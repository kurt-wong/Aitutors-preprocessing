# -*- coding: utf-8 -*-
"""R66.1-B/C 受控激活验证驱动(真实 runner、真实 OCR API、沙箱目录)

原则:
- 不修改任何生产代码;import 真实 batch_convert_pdf 模块,仅在驱动进程内重定向
  PDF_ROOT / OUTPUT_ROOT / MANIFEST_FILE / LOG_FILE 到沙箱(等价于测试 Harness,
  但走真实 API、真实清单写入)。
- PAGE_USAGE_FILE 保持生产路径:真实消耗页数必须诚实入账。
- 语料零触碰:source 为沙箱副本;Ocr-markdown 不写入。

阶段(全部真实执行):
  P1 首跑   : OCR -> output + manifest append(预期 success=1)
  P2 复扫   : output 在位 -> EXISTS 静默 skip,manifest 字节不变,零 OCR
  P3 搬移复扫: 移走 output(模拟 reclassify)-> MANIFEST_DONE,零 OCR,不回流
  P4 归位   : output 移回,manifest 不变
证据: 每阶段 manifest sha256/行数 + run.log 中 [DECIDE:*]/[OK] 行。
输出 data/r66_1_activation_evidence.json(确定性,除时间戳见证字段)。
"""
import hashlib
import json
import os
import shutil
import sys
import time

BASE = r"D:\Project\Papers"
SB = os.path.join(BASE, ".pytest_work", "r66_1_activation")
SRC_PDF = os.path.join(BASE, "maintainess", "PDF", "2022北京西城高二（下）期末地理参考答案(1).pdf")
EVIDENCE = os.path.join(BASE, "data", "r66_1_activation_evidence.json")

sys.path.insert(0, os.path.join(BASE, "ocr_service"))
import batch_convert_pdf as B  # noqa: E402  真实模块(token/session/常量)

B.PDF_ROOT = os.path.join(SB, "pdf")
B.OUTPUT_ROOT = os.path.join(SB, "out")
B.MANIFEST_FILE = os.path.join(SB, "manifest.jsonl")
B.LOG_FILE = os.path.join(SB, "run.log")


def sha(p):
    if not os.path.exists(p):
        return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def manifest_state():
    p = B.MANIFEST_FILE
    if not os.path.exists(p):
        return {"lines": 0, "sha256": None}
    data = open(p, "rb").read()
    return {"lines": len([l for l in data.decode("utf-8").splitlines() if l.strip()]),
            "sha256": hashlib.sha256(data).hexdigest()}


def log_tail(n=40):
    if not os.path.exists(B.LOG_FILE):
        return []
    lines = open(B.LOG_FILE, encoding="utf-8", errors="replace").read().splitlines()
    return lines[-n:]


def main():
    # 沙箱重建
    if os.path.exists(SB):
        shutil.rmtree(SB)
    os.makedirs(os.path.join(SB, "pdf"), exist_ok=True)
    shutil.copy2(SRC_PDF, os.path.join(SB, "pdf", os.path.basename(SRC_PDF)))

    out_md = os.path.join(SB, "out", "高二", "地理",
                          os.path.splitext(os.path.basename(SRC_PDF))[0] + ".md")
    ev = {"source_pdf_bytes": os.path.getsize(SRC_PDF),
          "source_pdf_sha256": sha(SRC_PDF),
          "phases": []}

    def record(phase, before, extra=None):
        after = manifest_state()
        entry = {"phase": phase, "manifest_before": before, "manifest_after": after,
                 "output_exists": os.path.exists(out_md),
                 "output_sha256": sha(out_md)}
        if extra:
            entry.update(extra)
        ev["phases"].append(entry)
        print(f"[DRIVER] {phase}: manifest {before['lines']}->{after['lines']} "
              f"output_exists={entry['output_exists']}")

    # P1 首跑(真实 OCR)
    before = manifest_state()
    print("[DRIVER] P1 first run (real OCR) ...", flush=True)
    B.main()
    record("P1_first_run", before, {"log_tail": log_tail(15)})

    # P2 复扫(output 在位)
    before = manifest_state()
    print("[DRIVER] P2 rescan (output in place) ...", flush=True)
    B.main()
    record("P2_rescan_in_place", before, {"log_tail": log_tail(6)})

    # P3 搬移 output 后复扫(模拟 reclassify)
    moved = os.path.join(SB, "moved_output.md")
    os.replace(out_md, moved)
    before = manifest_state()
    print("[DRIVER] P3 rescan after move (treadmill reproduction) ...", flush=True)
    B.main()
    record("P3_rescan_after_move", before, {"log_tail": log_tail(6)})

    # P4 归位
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    os.replace(moved, out_md)
    before = manifest_state()
    record("P4_restore", before)

    # 判定
    p1, p2, p3, p4 = ev["phases"]
    ev["verdict"] = {
        "P1_output_written_and_manifested":
            p1["output_exists"] and p1["manifest_after"]["lines"] == 1,
        "P2_zero_ocr_manifest_unchanged":
            p2["manifest_before"] == p2["manifest_after"],
        "P3_manifedone_zero_ocr_no_reflow":
            (not p3["output_exists"]) and p3["manifest_before"] == p3["manifest_after"],
        "P4_output_restored": p4["output_exists"],
        "manifest_content": open(B.MANIFEST_FILE, encoding="utf-8").read().splitlines()
        if os.path.exists(B.MANIFEST_FILE) else [],
    }
    with open(EVIDENCE, "w", encoding="utf-8") as f:
        json.dump(ev, f, ensure_ascii=False, indent=1)
    print("[DRIVER] verdict:")
    print(json.dumps({k: v for k, v in ev["verdict"].items() if k != "manifest_content"},
                     ensure_ascii=False, indent=1))
    print(f"[DRIVER] manifest entries: {ev['verdict']['manifest_content']}")
    print(f"[DRIVER] -> {EVIDENCE}")


if __name__ == "__main__":
    main()
