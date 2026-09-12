# -*- coding: utf-8 -*-
"""PAC OCR 漂移对比:新鲜 OCR 产物 vs 历史 OCR md 基线(逐样本量化)。

回答 Gate D6 的第一批问题:
1. 同一源 PDF,PaddleOCR-VL 现在重跑,与历史产物差多少?
2. 已知 hazard 形态(行融合/转义点)在新鲜产物中是否复现?

输出 data/pac_ocr_drift.json:逐样本 行数/字符数/标题数/图片数/页分隔数 +
difflib 相似度(粗粒度)+ hazard 形态复现检查(转义点序号头/融合头)。

用法:python scripts/pac_ocr_drift.py
"""

import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HEAD = re.compile(r"^#{1,6}\s*")
ESC_DOT = re.compile(r"^#{1,6}\s*\d{1,3}\s*\\+\s*[.、．]")          # BUG-25 家族形态
FUSE = re.compile(r"^#{1,6}\s*.*【答案】")                          # 标题行内含【答案】= 融合形态


def stats(text: str) -> dict:
    lines = text.splitlines()
    return {
        "lines": len(lines),
        "chars": len(text),
        "headings": sum(1 for l in lines if HEAD.match(l)),
        "images": text.count("<img"),
        "page_breaks": sum(1 for l in lines if l.strip() == "---"),
        "esc_dot_lines": sum(1 for l in lines if ESC_DOT.match(l)),
        "fuse_lines": sum(1 for l in lines if FUSE.match(l)),
    }


def main():
    sel = json.loads((ROOT / "data/pac_selection.json").read_text(encoding="utf-8"))
    track = json.loads((ROOT / "data/pac_track_ocr.json").read_text(encoding="utf-8"))
    rows = []
    for s in sel["samples"]:
        sid = s["sample_id"]
        fresh = Path(track[sid]["output_md_path"]).read_text(encoding="utf-8")
        base = Path(s["md_baseline"]["path"]).read_text(encoding="utf-8", errors="replace")
        fs, bs = stats(fresh), stats(base)
        ratio = round(difflib.SequenceMatcher(None, base, fresh).ratio(), 4)
        rows.append({
            "sample_id": sid,
            "category": s["category"],
            "baseline_sha256_equal": s["md_baseline"]["sha256"] == track[sid]["output_md_sha256"],
            "similarity": ratio,
            "baseline": bs,
            "fresh": fs,
            "delta_lines": fs["lines"] - bs["lines"],
        })
        print(f"{sid}: sim={ratio:.3f} lines {bs['lines']}→{fs['lines']} "
              f"esc_dot {bs['esc_dot_lines']}→{fs['esc_dot_lines']} "
              f"fuse {bs['fuse_lines']}→{fs['fuse_lines']}")

    out = {
        "note": "PAC OCR 漂移对比(D6 真实 OCR 服务链证据):fresh=本轮直调 API 产物,"
                "baseline=历史守护队列产物(同模型 PaddleOCR-VL-1.6,时间差数月)",
        "n": len(rows),
        "identical": sum(1 for r in rows if r["baseline_sha256_equal"]),
        "rows": rows,
    }
    p = ROOT / "data/pac_ocr_drift.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                 encoding="utf-8", newline="")
    print(f"\n留档 {p}:完全一致 {out['identical']}/{out['n']}")


if __name__ == "__main__":
    main()
