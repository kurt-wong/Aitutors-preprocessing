# -*- coding: utf-8 -*-
r"""fix_heading_qnum.py — 题号行的 OCR 标题误标清洗(BUG-19)。

问题(R22 抽审):
  OCR 把题号行误转为 markdown 标题(`### 52. 题干`),渲染加粗。
  全批 20/50 份、158 行;其中 134 行在 unit 区间内(题干/答案内容,误标,
  应剥),24 行在区间外(教师用书小节标题等真结构,保留)。

修复:
  区间内的 ^#{1,6}\s*\d{1,3}[.．、] 行 → 剥 # 前缀,保留题号与内容。
  newline="" 读写(BUG-16),逐行 before/after 审计。

用法:
  python fix_heading_qnum.py           # dry-run
  python fix_heading_qnum.py --apply
"""
import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
BATCH = ROOT / "Ocr-markdown/reslice-batch-C"
LOG = ROOT / "data/bug19_heading_fix_log.json"

PAT = re.compile(r"^\s*#{1,6}\s*(\d{1,3}[.．、].*)$")
ROLE = {"stem_lines", "explanation_lines", "answer_lines", "options_lines",
        "extra_lines", "material_lines", "questions_lines"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", help="切片目录(默认 reslice-batch-C)")
    ap.add_argument("--log", help="审计日志路径(默认 data/bug19_heading_fix_log.json)")
    args = ap.parse_args()
    if args.log:
        global LOG
        LOG = Path(args.log)
    batch = Path(args.out) if args.out else BATCH

    records = []
    n_fix = n_keep = 0
    for mf in sorted(batch.rglob("*.manifest.json")):
        with io.open(str(mf), encoding="utf-8", newline="") as f:
            man = json.load(f)
        src = Path(man["source_file"])
        if not src.exists():
            continue
        with io.open(str(src), encoding="utf-8", newline="") as f:
            raw = f.read()
        lines = raw.splitlines(keepends=True)

        used = set()
        for u in man["units"]:
            for role, v in u.items():
                if role in ROLE and isinstance(v, list) and len(v) == 2 \
                        and all(isinstance(x, int) for x in v):
                    used.update(range(v[0], v[1] + 1))

        changed = False
        for i, l in enumerate(lines):
            body = l.rstrip("\r\n")
            eol = l[len(body):]
            m = PAT.match(body)
            if not m:
                continue
            if (i + 1) in used:
                records.append({"source": str(src), "line": i + 1,
                                "action": "strip",
                                "before": body[:70], "after": m.group(1)[:70]})
                lines[i] = m.group(1) + eol
                changed = True
                n_fix += 1
            else:
                records.append({"source": str(src), "line": i + 1,
                                "action": "keep_structure",
                                "preview": body[:70]})
                n_keep += 1
        if changed and args.apply:
            try:
                with io.open(str(src), "w", encoding="utf-8", newline="") as f:
                    f.write("".join(lines))
            except Exception as e:
                records.append({"source": str(src), "action": "write_error",
                                "error": f"{type(e).__name__}: {e}"})

    summary = {"strip": n_fix, "keep_structure": n_keep,
               "mode": "apply" if args.apply else "dry-run"}
    LOG.write_text(json.dumps({"summary": summary, "records": records},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{summary['mode']}] strip={n_fix} keep_structure={n_keep} → {LOG}")


if __name__ == "__main__":
    main()
