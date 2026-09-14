# -*- coding: utf-8 -*-
r"""
p2_1_measure.py — Phase P2.1 批量切分结果度量(最小闭环版)

输入:抽样清单 JSON + reslice 输出目录。
输出:逐卷指标 + 汇总(解析成功率 / 题目数 / 答案齐全率 / 题号覆盖 / 错误分桶)。

指标口径(用户两周验收的可自动化子集):
  - 成功解析试卷比例 = manifest 存在且 validation_issues 为空 的卷数 / 批卷数
  - 答案齐全率 = answer_lines 非空的问题单元 / 全部问题单元
  - 题号覆盖 = question_numbers 并集跨度与缺号列表(供人工复核)
  - 错误分桶 = 无 manifest(调用失败)/ validation_issues / warnings

用法:
  python scripts/p2_1_measure.py --batch data/p2_1_batch1.json \
      --out Ocr-markdown/reslice-p2-b1 --result data/p2_1_b1_measure.json
"""

import argparse
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Ocr-markdown"
Q_TYPES = ("standalone_question", "composite_question")


def manifest_path_for(out_root: Path, src: str) -> Path:
    p = Path(src)
    try:
        rel = p.relative_to(SRC)
    except ValueError:
        rel = Path(p.name)
    return out_root / rel.parent / f"{p.stem}.manifest.json"


def measure_paper(out_root: Path, entry: dict) -> dict:
    src = entry["file"]
    mp = manifest_path_for(out_root, src)
    rec = {"file": src, "subject": entry.get("subject"),
           "manifest_exists": mp.exists()}
    if not mp.exists():
        rec["status"] = "NO_MANIFEST"
        return rec
    man = json.loads(mp.read_text(encoding="utf-8"))
    units = man.get("units") or []
    qs = [u for u in units if u.get("unit_type") in Q_TYPES]
    answered = [u for u in qs if u.get("answer_lines")]
    nums = sorted({n for u in qs for n in (u.get("question_numbers") or [])})
    meta = man.get("annotation_meta") or {}
    rec.update({
        "status": "OK" if not meta.get("validation_issues") else "VALIDATION_ISSUES",
        "units": len(units),
        "questions": len(qs),
        "answered": len(answered),
        "answer_rate": round(len(answered) / len(qs), 4) if qs else None,
        "qnum_min": nums[0] if nums else None,
        "qnum_max": nums[-1] if nums else None,
        "qnum_missing": [n for n in range(nums[0], nums[-1] + 1)
                         if n not in nums] if nums else [],
        "validation_issues": meta.get("validation_issues") or [],
        "warnings": len(meta.get("warnings") or []),
    })
    return rec


def main():
    global SRC
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=str(ROOT / "data/p2_1_batch1.json"))
    ap.add_argument("--out", default=str(SRC / "reslice-p2-b1"))
    ap.add_argument("--result", default=str(ROOT / "data/p2_1_b1_measure.json"))
    ap.add_argument("--src", default=str(SRC), help="源语料根(默认 Ocr-markdown)")
    args = ap.parse_args()

    SRC = Path(args.src)

    entries = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    out_root = Path(args.out)
    papers = [measure_paper(out_root, e) for e in entries]

    total = len(papers)
    ok = sum(1 for p in papers if p["status"] == "OK")
    no_man = sum(1 for p in papers if p["status"] == "NO_MANIFEST")
    vi = sum(1 for p in papers if p["status"] == "VALIDATION_ISSUES")
    tq = sum(p.get("questions") or 0 for p in papers)
    ta = sum(p.get("answered") or 0 for p in papers)
    by_subject = {}
    for p in papers:
        s = by_subject.setdefault(p["subject"], {"papers": 0, "ok": 0, "questions": 0})
        s["papers"] += 1
        s["ok"] += (p["status"] == "OK")
        s["questions"] += p.get("questions") or 0

    report = {
        "schema_version": 1,
        "batch": os.path.abspath(args.batch),
        "out": os.path.abspath(args.out),
        "totals": {
            "papers": total, "ok": ok,
            "validation_issues": vi, "no_manifest": no_man,
            "parse_success_rate": round(ok / total, 4) if total else None,
            "questions": tq, "answered": ta,
            "answer_rate": round(ta / tq, 4) if tq else None,
        },
        "by_subject": by_subject,
        "papers": papers,
    }
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    with io.open(args.result, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
        f.write("\n")
    t = report["totals"]
    print("papers={papers} ok={ok} vi={validation_issues} no_manifest={no_manifest} "
          "parse_success={parse_success_rate} questions={questions} "
          "answer_rate={answer_rate}".format(**t))
    print("result: " + args.result)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
