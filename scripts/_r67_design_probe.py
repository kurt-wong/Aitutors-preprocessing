# -*- coding: utf-8 -*-
"""R67 设计输入探针(只读):审计 698 条 from→to 与 runner 期望输出路径的可匹配性。"""
import json
import os
import re

BASE = r"D:\Project\Papers"
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUT_ROOT = os.path.join(BASE, "Ocr-markdown")


def san(n):
    return re.sub(r'[<>:"/\\|?*]', "_", os.path.splitext(n)[0])


def egs(fn):
    g = "未分类"
    if re.search(r"高一|高1", fn):
        g = "高一"
    elif re.search(r"高二|高2", fn):
        g = "高二"
    elif re.search(r"高三|高3", fn):
        g = "高三"
    s = "未分类"
    for x in ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]:
        if x in fn:
            s = x
            break
    return g, s


exp = {}
for dirpath, _dirnames, filenames in os.walk(PDF_ROOT):
    rel_dir = os.path.relpath(dirpath, PDF_ROOT)
    for fn in filenames:
        if not fn.lower().endswith(".pdf"):
            continue
        if rel_dir == ".":
            g, s = egs(fn)
        else:
            parts = rel_dir.split(os.sep)
            g, s = parts[0], (parts[1] if len(parts) > 1 else "未分类")
        exp.setdefault(f"{g}/{s}/{san(fn)}.md", []).append(fn)

audit = [json.loads(l) for l in
         open(os.path.join(BASE, "data", "reclassify_audit.jsonl"), encoding="utf-8")
         if l.strip()]

matched, to_missing, unmatched = [], 0, []
for a in audit:
    fr = os.path.relpath(a["from"], OUT_ROOT).replace("\\", "/")
    if fr in exp:
        if os.path.exists(a["to"]):
            matched.append(fr)
        else:
            to_missing += 1
    else:
        unmatched.append(fr)

multi = sum(1 for fr in matched if len(exp[fr]) > 1)
print(f"audit_total={len(audit)}")
print(f"matched(from==某PDF期望输出 且 to 仍在位)={len(matched)}")
print(f"to_missing={to_missing} unmatched_from={len(unmatched)}")
print(f"matched 中期望输出路径被多个 PDF 共享的={multi}")
print("unmatched 样例:")
for u in unmatched[:8]:
    print("  ", u)
# 反向:victim 625 交集
vic = json.load(open(os.path.join(BASE, "data", "r66_1_victim_split.json"), encoding="utf-8"))
audit_froms = {os.path.relpath(a["from"], OUT_ROOT).replace("\\", "/") for a in audit}
hit = 0
for v in vic["victims"]:
    stem = v["stem"]
    for p in v["existing_md_core"] + v["existing_md_excluded"]:
        pass
    # victim 的期望输出 rel:
    rel = v["expected_output_rel"].replace("Ocr-markdown/", "")
    if rel in audit_froms:
        hit += 1
        break
print(f"victim 625 中期望输出在审计 from 集合内的={hit}")
