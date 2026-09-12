# -*- coding: utf-8 -*-
"""PAC OCR runner(R43 Gate 首攻面):对 data/pac_selection.json 的 22 份源 PDF
直调 PaddleOCR-VL API 单跑,不经守护队列(用户裁定),独立输出与逐样本记账。

链路(与生产 ocr_service/batch_convert_pdf.py 同款 API 协议):
    POST https://paddleocr.aistudio-app.com/api/v2/ocr/jobs (multipart PDF)
    -> 轮询 state -> done 后下载 jsonl -> layoutParsingResults[].markdown.text
    -> 页间 "\n\n---\n\n" 合并 -> Ocr-markdown/reslice-pac/ocr/{sample_id}.md

记账(诚实分账):
    - data/pac_track_ocr.json     逐样本 stage 轨迹(job_id/页数/耗时/sha256/状态)
    - data/ocr_page_usage.json    全局页额度台账(与守护进程同源,防额度双花)
    - data/pac_ocr_usage.json     PAC 专项页账目(独立对账)

失败纪律:任一样本 FAIL 如实记入轨迹,不重试超过 3 次,不静默跳过;
重跑本脚本自带断点续跑(已成功样本跳过)。

用法:python scripts/pac_ocr_runner.py [--only pac-c02-01]
"""

import argparse
import hashlib
import json
import sys
import time
import urllib3
from pathlib import Path

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "data" / "pac_selection.json"
OCR_OUT = ROOT / "Ocr-markdown" / "reslice-pac" / "ocr"
TRACK = ROOT / "data" / "pac_track_ocr.json"
PAC_USAGE = ROOT / "data" / "pac_ocr_usage.json"
GLOBAL_USAGE = ROOT / "data" / "ocr_page_usage.json"

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MODEL = "PaddleOCR-VL-1.6"
DAILY_PAGE_LIMIT = 20000

OPTIONAL_PAYLOAD = {
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useChartRecognition": False,
}


def load_token() -> str:
    t = None
    import os
    t = os.environ.get("OCR_API_TOKEN")
    if t:
        return t.strip()
    cfg = ROOT / "data" / ".ocr_config"
    for line in cfg.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            if k.strip() == "token":
                return v.strip()
    sys.exit("缺少 OCR API token")


TOKEN = load_token()
SESSION = requests.Session()
SESSION.verify = False
SESSION.proxies = {"http": "http://127.0.0.1:55219", "https": "http://127.0.0.1:55219"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(p: Path, default):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def save_json(p: Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                 encoding="utf-8", newline="")  # BUG-16:禁 CRLF 翻转


def bill_pages(pages: int):
    """页账目:全局台账(与守护进程同源)+ PAC 专项台账。"""
    today = time.strftime("%Y-%m-%d")
    g = load_json(GLOBAL_USAGE, {"date": today, "used": 0})
    if g.get("date") != today:
        g = {"date": today, "used": 0}
    g["used"] = g.get("used", 0) + pages
    save_json(GLOBAL_USAGE, g)

    p = load_json(PAC_USAGE, {"date": today, "used": 0, "files": 0})
    if p.get("date") != today:
        p = {"date": today, "used": 0, "files": 0}
    p["used"] += pages
    p["files"] += 1
    save_json(PAC_USAGE, p)
    return g["used"]


def ocr_one(pdf: Path) -> dict:
    """单份 PDF -> 合并 markdown。返回 {status, pages, md_text, job_id, attempts, duration_s}。"""
    headers = {"Authorization": f"bearer {TOKEN}"}
    t0 = time.time()
    last_err = "unknown"
    for attempt in range(1, 4):
        try:
            with open(pdf, "rb") as f:
                r = SESSION.post(JOB_URL, headers=headers,
                                 data={"model": MODEL,
                                       "optionalPayload": json.dumps(OPTIONAL_PAYLOAD)},
                                 files={"file": f}, timeout=180)
            if r.status_code != 200:
                last_err = f"submit HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(5)
                continue
            job_id = r.json()["data"]["jobId"]
            jsonl_url = ""
            for _ in range(240):  # 最长等 20 分钟
                q = SESSION.get(f"{JOB_URL}/{job_id}", headers=headers, timeout=60)
                if q.status_code != 200:
                    last_err = f"poll HTTP {q.status_code}"
                    break
                state = q.json()["data"]["state"]
                if state == "done":
                    jsonl_url = q.json()["data"]["resultUrl"]["jsonUrl"]
                    break
                if state == "failed":
                    last_err = "job state=failed"
                    break
                time.sleep(5)
            if not jsonl_url:
                time.sleep(5)
                continue
            dl = SESSION.get(jsonl_url, timeout=120)
            if dl.status_code != 200:
                last_err = f"download HTTP {dl.status_code}"
                time.sleep(5)
                continue
            pages_md, page_count = [], 0
            for line in dl.text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    for res in json.loads(line)["result"]["layoutParsingResults"]:
                        pages_md.append(res["markdown"]["text"])
                        page_count += 1
                except Exception:
                    pass
            if pages_md:
                return {"status": "OK", "pages": page_count,
                        "md_text": "\n\n---\n\n".join(pages_md),
                        "job_id": job_id, "attempts": attempt,
                        "duration_s": round(time.time() - t0, 1)}
            last_err = "empty layoutParsingResults"
        except Exception as e:
            last_err = f"exception: {e}"
        time.sleep(5)
    return {"status": "FAIL", "error": last_err, "attempts": attempt,
            "duration_s": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只跑指定 sample_id")
    args = ap.parse_args()

    sel = load_json(SELECTION, None)
    if not sel:
        sys.exit("缺 data/pac_selection.json,先跑 scripts/pac_select.py")
    OCR_OUT.mkdir(parents=True, exist_ok=True)
    track = load_json(TRACK, {})

    samples = [s for s in sel["samples"]
               if not args.only or s["sample_id"] == args.only]
    print(f"PAC OCR: {len(samples)} 份,输出 {OCR_OUT}", flush=True)
    for s in samples:
        sid = s["sample_id"]
        prev = track.get(sid, {})
        if prev.get("status") == "OK" and (OCR_OUT / f"{sid}.md").exists():
            print(f"[skip] {sid} 已成功", flush=True)
            continue
        pdf = Path(s["pdf"]["path"])
        print(f"[run ] {sid} {pdf.name} ({s['pdf']['pages']}p)...", flush=True)
        res = ocr_one(pdf)
        rec = {"sample_id": sid, "stage": "ocr",
               "input_pdf_sha256": s["pdf"]["sha256"],
               "input_pages_measured": s["pdf"]["pages"],
               "model": MODEL, "attempts": res.get("attempts"),
               "duration_s": res.get("duration_s"), "status": res["status"]}
        if res["status"] == "OK":
            md_bytes = res["md_text"].encode("utf-8")
            outp = OCR_OUT / f"{sid}.md"
            outp.write_text(res["md_text"], encoding="utf-8", newline="")
            rec.update({"job_id": res["job_id"], "pages_billed": res["pages"],
                        "output_md_sha256": sha256_bytes(md_bytes),
                        "output_md_path": str(outp)})
            used = bill_pages(res["pages"])
            print(f"  [OK] {res['pages']}p {res['duration_s']}s "
                  f"(全局额度累计 {used}/{DAILY_PAGE_LIMIT})", flush=True)
        else:
            rec["error"] = res.get("error")
            print(f"  [FAIL] {res.get('error')}", flush=True)
        track[sid] = rec
        save_json(TRACK, track)

    ok = sum(1 for r in track.values() if r.get("status") == "OK")
    fail = sum(1 for r in track.values() if r.get("status") == "FAIL")
    print(f"\n===== OCR 完成:OK {ok} / FAIL {fail} / 计 {len(track)} =====", flush=True)


if __name__ == "__main__":
    main()
