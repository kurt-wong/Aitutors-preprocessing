# -*- coding: utf-8 -*-
"""R66.1 预检第二步(只读):把 would_ocr 10,282 拆成两类

A. treadmill-victim candidates:语料中存在同名 .md(任意目录,规范化 stem 匹配)
   -> 该 source 历史上已 OCR 过且输出被搬走;首扫重 OCR = 重复产出 + 浪费配额
B. never-processed:全语料无同名 md
   -> daemon 本职待办,重跑属正常业务

匹配规则:md 文件名(去 .md)与 sanitize_stem(pdf) 完全相等;
md 候选集 = Ocr-markdown 全树,排除 reslice-* / resliced-* 试验目录(单独计数披露)。
输出 data/r66_1_victim_split.json(确定性)。
"""
import json
import os
import re

BASE = r"D:\Project\Papers"
OUT_JSON = os.path.join(BASE, "data", "r66_1_preflight.json")
SPLIT_JSON = os.path.join(BASE, "data", "r66_1_victim_split.json")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")

EXCLUDE_PREFIXES = ("reslice-", "resliced-")


def sanitize_stem(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", os.path.splitext(name)[0])


def md_stem_index():
    core, excluded = {}, {}
    for dirpath, dirnames, filenames in os.walk(OUTPUT_ROOT):
        rel_dir = os.path.relpath(dirpath, OUTPUT_ROOT).replace("\\", "/")
        top = rel_dir.split("/")[0] if rel_dir != "." else ""
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            stem = fn[:-3]
            rec = {"path": os.path.relpath(os.path.join(dirpath, fn), BASE).replace("\\", "/")}
            bucket = excluded if top.startswith(EXCLUDE_PREFIXES) else core
            bucket.setdefault(stem, []).append(rec["path"])
    return core, excluded


def main():
    with open(OUT_JSON, encoding="utf-8") as f:
        pre = json.load(f)
    core, excluded = md_stem_index()

    victims, never = [], []
    for w in pre["would_ocr"]:
        stem = sanitize_stem(os.path.basename(w["source_rel"]))
        in_core = core.get(stem, [])
        in_excl = excluded.get(stem, [])
        if in_core or in_excl:
            victims.append({**w, "stem": stem,
                            "existing_md_core": sorted(in_core),
                            "existing_md_excluded": sorted(in_excl)})
        else:
            never.append({**w, "stem": stem})

    report = {
        "purpose": "split would_ocr into treadmill-victim candidates vs never-processed",
        "matching_rule": "md filename (minus .md) == sanitize_stem(pdf basename), exact",
        "excluded_dir_prefixes": list(EXCLUDE_PREFIXES),
        "md_core_stems": len(core),
        "md_excluded_stems": len(excluded),
        "victim_count": len(victims),
        "victim_source_bytes": sum(v["source_bytes"] or 0 for v in victims),
        "never_count": len(never),
        "never_source_bytes": sum(v["source_bytes"] or 0 for v in never),
        "victims": victims,
        "never": never,
    }
    with open(SPLIT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"md_core_stems={len(core)} md_excluded_stems={len(excluded)}")
    print(f"victim_count={report['victim_count']} bytes={report['victim_source_bytes']}")
    print(f"never_count={report['never_count']} bytes={report['never_source_bytes']}")
    print(f"-> {SPLIT_JSON}")


if __name__ == "__main__":
    main()
