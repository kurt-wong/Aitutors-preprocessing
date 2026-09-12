# -*- coding: utf-8 -*-
r"""fix_orphan_imgs.py — 无主配图的确定性归属并入(BUG-18)。

背景(R19 抽审):
  PDF 版式"图排在题号前"及详解段间配图,LLM 行区间从题号/文字段起算,
  紧邻的 <img> 行被漏在区间外 → 源文件完整但入库按区间提取会丢图。
  立体几何 123 张、全批 204 张(8 份)。

规则(确定性,保守):
  对每张无主 img 行 ln,在全部 unit 区间中找最近区间 [s,e]（按角色优先
  stem > explanation > answer > options > extra）：
  R-pre  ln < s 且 s-ln≤6 且中间行全为空行/分隔线/图行 → stem 起点前移至 ln
  R-post ln > e 且 ln-e≤6 且中间行全为空行/分隔线/图行 → 该区间终点后移至 ln
  不满足 → 留档 keep(人工/后续),不动。
  冲突取距离更近者;并列取 unit 序号小者。

用法:
  python fix_orphan_imgs.py           # dry-run
  python fix_orphan_imgs.py --apply
"""
import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\Papers")
BATCH = ROOT / "Ocr-markdown/reslice-batch-C"
LOG = ROOT / "data/bug18_orphan_img_fix_log.json"

IMG = re.compile(r"<img\s|!\[[^\]]*\]\(")
FILLER = re.compile(r"^\s*$|^\s*---\s*$|^\s*<div[^>]*>\s*$|^\s*</div>\s*$")
ROLE_RANK = {"stem_lines": 0, "explanation_lines": 1, "answer_lines": 2,
             "options_lines": 3, "extra_lines": 4, "material_lines": 5,
             "questions_lines": 6}   # question_numbers 是题号,不是行区间,排除
GAP_MAX = 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    records = []
    n_merge = n_keep = 0
    for mf in sorted(BATCH.rglob("*.manifest.json")):
        with io.open(str(mf), encoding="utf-8", newline="") as f:
            man = json.load(f)
        src = Path(man["source_file"])
        if not src.exists():
            continue
        with io.open(str(src), encoding="utf-8", newline="") as f:
            lines = f.read().splitlines()

        used = set()
        ranges = []  # (start, end, unit_idx, role)
        for ui, u in enumerate(man["units"]):
            for role, v in u.items():
                if role in ROLE_RANK and isinstance(v, list) and len(v) == 2 \
                        and all(isinstance(x, int) for x in v):
                    used.update(range(v[0], v[1] + 1))
                    ranges.append((v[0], v[1], ui, role))

        orph = [i + 1 for i, l in enumerate(lines)
                if IMG.search(l) and (i + 1) not in used]
        if not orph:
            continue

        changed = False
        for ln in orph:
            # 找候选:(距离, role_rank, unit_idx, 角色, s, e)
            cands = []
            for s, e, ui, role in ranges:
                if ln < s:
                    gap = s - ln
                    mid = range(ln + 1, s)
                    rule = "R-pre"
                elif ln > e:
                    gap = ln - e
                    mid = range(e + 1, ln)
                    rule = "R-post"
                else:
                    continue
                if gap <= GAP_MAX and all(FILLER.match(lines[m - 1]) for m in mid):
                    cands.append((gap, ROLE_RANK[role], ui, role, s, e, rule))
            if not cands:
                records.append({"manifest": str(mf), "line": ln,
                                "action": "keep", "preview": lines[ln - 1][:70]})
                n_keep += 1
                continue
            cands.sort()
            gap, _, ui, role, s, e, rule = cands[0]
            u = man["units"][ui]
            before = list(u[role])
            if rule == "R-pre":
                u[role] = [ln, e]
            else:
                u[role] = [s, ln]
            # 嵌套不变量联动（B1 审查）：material ⊆ questions，扩展 material 时 questions 端点跟随
            if role == "material_lines" and isinstance(u.get("questions_lines"), list):
                q = u["questions_lines"]
                u["questions_lines"] = [min(q[0], u[role][0]), max(q[1], u[role][1])]
            records.append({
                "manifest": str(mf), "line": ln, "action": "merge",
                "unit_id": u.get("unit_id"), "role": role, "rule": rule,
                "gap": gap, "before": before, "after": list(u[role]),
                "preview": lines[ln - 1][:70],
            })
            changed = True
            n_merge += 1

        if changed and args.apply:
            with io.open(str(mf), "w", encoding="utf-8", newline="") as f:
                f.write(json.dumps(man, ensure_ascii=False, indent=1))

    summary = {"merge": n_merge, "keep": n_keep,
               "mode": "apply" if args.apply else "dry-run"}
    LOG.write_text(json.dumps({"summary": summary, "records": records},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{summary['mode']}] merge={n_merge} keep={n_keep} → {LOG}")


if __name__ == "__main__":
    main()
