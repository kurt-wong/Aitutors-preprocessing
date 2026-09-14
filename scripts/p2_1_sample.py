# -*- coding: utf-8 -*-
r"""
p2_1_sample.py — Phase P2.1 首批真实试卷确定性抽样(用户 2026-09-14 口径)

配额:语文/数学/英语/物理/化学/生物 各 5 份,历史/地理/政治 各 3 份(共 39)。
来源:Ocr-markdown\{高一,高二,高三}\{subject}\*.md(校内单卷,排除汇编巨卷)。
方法:按路径排序后等距取样(跨学段/年份铺开),纯确定性,可复跑复现。

用法:python scripts/p2_1_sample.py --out data/p2_1_batch1.json
"""

import argparse
import glob
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Ocr-markdown"
GRADES = ["高一", "高二", "高三"]
QUOTA = {"语文": 5, "数学": 5, "英语": 5, "物理": 5, "化学": 5, "生物": 5,
         "历史": 3, "地理": 3, "政治": 3}
SIZE_MIN, SIZE_MAX = 5_000, 300_000  # 排除碎片与汇编巨卷


def sample():
    picks = []
    for subject, n in QUOTA.items():
        pool = []
        for g in GRADES:
            pattern = str(SRC / g / subject / "*.md")
            for p in sorted(glob.glob(pattern)):
                try:
                    sz = os.path.getsize(p)
                except OSError:
                    continue
                if SIZE_MIN <= sz <= SIZE_MAX:
                    pool.append(p)
        pool.sort()
        if len(pool) < n:
            raise SystemExit(f"[FATAL] {subject} 池不足: {len(pool)} < {n}")
        # 等距取样:铺开学段/年份
        step = len(pool) / n
        chosen = [pool[int(i * step)] for i in range(n)]
        for p in chosen:
            picks.append({"file": p, "subject": subject, "tier": "P2-b1"})
    return picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data/p2_1_batch1.json"))
    args = ap.parse_args()
    picks = sample()
    with io.open(args.out, "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=1)
        f.write("\n")
    by_subject = {}
    for p in picks:
        by_subject[p["subject"]] = by_subject.get(p["subject"], 0) + 1
    print(f"picked={len(picks)} by_subject={by_subject}")
    print(f"out: {args.out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
