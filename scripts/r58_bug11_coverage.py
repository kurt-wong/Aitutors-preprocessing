# -*- coding: utf-8 -*-
"""
r58_bug11_coverage.py — BUG-11 修复的全库覆盖度证据(只读,不写任何语料)。

背景:recover_images.py 旧 SCAN_DIRS 硬编码四个目录,重归类后的六个源目录
(高考真题/合格考/会考/竞赛自招/其他汇编/学业水平考试)对图片恢复完全不可见。
本脚本按"旧白名单口径 vs 修复后口径"两套视野,实测:
  - 每个源顶层目录的 md 总数
  - 含悬空 imgs/*.jpg 引用(未重写)的文件数与引用总数
  - 其中 basename 在源 PDF 索引内(可恢复)的候选数
输出 data/r58_bug11_coverage.json + 控制台汇总。零写入语料。

用法: python scripts/r58_bug11_coverage.py
"""
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recover_images as ri  # noqa: E402

OLD_DIRS = ["高一", "高二", "高三", "未分类"]
OUT = os.path.join(ri.BASE, "data", "r58_bug11_coverage.json")


def main():
    pdf_index = ri.build_pdf_index()
    scanned = ri.scan_md_files()  # 修复后口径(排除派生目录)
    old_set = {p for p in scanned
               if os.path.relpath(p, ri.OCR_ROOT).split(os.sep)[0] in OLD_DIRS}

    per_dir = {}
    for p in scanned:
        d = os.path.relpath(p, ri.OCR_ROOT).split(os.sep)[0]
        st = per_dir.setdefault(d, {"md_total": 0, "with_dangling_refs": 0,
                                    "dangling_ref_total": 0, "already_marked": 0,
                                    "recover_candidate": 0, "pdf_miss": 0})
        st["md_total"] += 1
        try:
            text = io.open(p, encoding="utf-8").read()
        except Exception:
            continue
        base = os.path.splitext(os.path.basename(p))[0]
        refs = ri.REF.findall(text)
        marked = f"_imgs/{base}/" in text
        if marked:
            st["already_marked"] += 1
        if refs:
            st["with_dangling_refs"] += 1
            st["dangling_ref_total"] += len(set(refs))
            if not marked:
                if base in pdf_index:
                    st["recover_candidate"] += 1
                else:
                    st["pdf_miss"] += 1

    report = {
        "round": "R58 BUG-11",
        "scanned_total_new_scope": len(scanned),
        "scanned_total_old_scope": len(old_set),
        "newly_visible": len(scanned) - len(old_set),
        "pdf_index_size": len(pdf_index),
        "per_dir": dict(sorted(per_dir.items())),
    }
    tot = Counter()
    for st in per_dir.values():
        tot.update(st)
    report["totals_new_scope"] = dict(tot)
    old_tot = Counter()
    for d, st in per_dir.items():
        if d in OLD_DIRS:
            old_tot.update(st)
    report["totals_old_scope"] = dict(old_tot)
    report["delta_recover_candidates"] = (
        report["totals_new_scope"].get("recover_candidate", 0)
        - report["totals_old_scope"].get("recover_candidate", 0))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "per_dir"},
                     ensure_ascii=False, indent=1))
    for d, st in report["per_dir"].items():
        print(f"  {d}: {st}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
