# -*- coding: utf-8 -*-
r"""fix_explanation_prefix.py — 方案A:详解区"原题复述"起点收缩(确定性清洗)。

问题(R18 人工抽审发现,BUG-17):
  教师版详解区(卷末答案区)自带完整原题复述(题号+题干+选项),LLM 忠实划行后
  explanation_lines 起点落在题干复述行上 → 切片展示"题干重复出现在详解区"。

修复:
  explanation_lines=[s,e] 且源行 lines[s-1] 以题号开头时,
  起点收缩到区间内第一个【分析】/【解答】标记行;无标记 → 保持原样并留档。
  其他字段不动;before/after 逐条记入审计 JSON。

用法:
  python fix_explanation_prefix.py           # dry-run,只报告
  python fix_explanation_prefix.py --apply   # 应用(写 manifest)
"""
import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
BATCH = ROOT / "Ocr-markdown/reslice-batch-C"
LOG = ROOT / "data/bug17_explanation_fix_log.json"

QNUM = re.compile(r"^\s*\d+[.．、]")           # 题号开头 = 原题复述
MARK = re.compile(r"【(?:分析|解答)】")         # 解析正文起点标记


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", help="切片目录(默认 reslice-batch-C)")
    ap.add_argument("--log", help="审计日志路径(默认 data/bug17_explanation_fix_log.json)")
    args = ap.parse_args()
    if args.log:
        global LOG
        LOG = Path(args.log)

    records = []
    n_fix = n_keep = n_skip_mark = 0
    batch = Path(args.out) if args.out else BATCH
    for mf in sorted(batch.rglob("*.manifest.json")):
        with io.open(str(mf), encoding="utf-8", newline="") as f:
            man = json.load(f)
        src = Path(man["source_file"])
        if not src.exists():
            records.append({"manifest": str(mf), "action": "skip_no_src"})
            continue
        with io.open(str(src), encoding="utf-8", newline="") as f:
            lines = f.read().splitlines()
        changed = False
        for u in man["units"]:
            e = u.get("explanation_lines")
            if not (isinstance(e, list) and len(e) == 2 and 0 < e[0] <= len(lines)):
                continue
            if not QNUM.match(lines[e[0] - 1]):
                continue
            # 在 [e0, e1] 内找第一个标记行
            new_start = None
            for i in range(e[0] - 1, min(e[1], len(lines))):
                if MARK.search(lines[i]):
                    new_start = i + 1
                    break
            if new_start and new_start > e[0]:
                records.append({
                    "manifest": str(mf), "unit_id": u.get("unit_id"),
                    "question_numbers": u.get("question_numbers"),
                    "action": "fix", "before": list(e),
                    "after": [new_start, e[1]],
                    "cut_head_preview": lines[e[0] - 1][:60],
                })
                u["explanation_lines"] = [new_start, e[1]]
                changed = True
                n_fix += 1
            else:
                records.append({
                    "manifest": str(mf), "unit_id": u.get("unit_id"),
                    "action": "keep_no_mark", "lines": list(e),
                })
                n_skip_mark += 1
        if changed and args.apply:
            with io.open(str(mf), "w", encoding="utf-8", newline="") as f:
                f.write(json.dumps(man, ensure_ascii=False, indent=1))

    summary = {
        "fix": n_fix, "keep_no_mark": n_skip_mark,
        "mode": "apply" if args.apply else "dry-run",
    }
    LOG.write_text(json.dumps({"summary": summary, "records": records},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{summary['mode']}] fix={n_fix} keep_no_mark={n_skip_mark} → {LOG}")


if __name__ == "__main__":
    main()
