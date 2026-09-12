# -*- coding: utf-8 -*-
r"""
make_review_sample.py — 从 auto-annotated-v6 分层抽样生成人工审核清单

策略:
  1. 全量统计 1,433 份 v6 标注的质量基线(题目/答案/解析计数、标记配对、
     题答数量是否匹配等), 作为审核参照。
  2. 按 年级 x 科目 分层, 按比例分配 + 每层至少 2 份, 总样本 N(默认100)。
  3. 层内一半随机抽、一半"高风险优先"(题答数量不匹配 / 标记不配对 /
     无答案标记的文件优先入样), 提高审核发现问题的概率。
  4. 固定随机种子, 结果可复现。

输出:
  Ocr-markdown\auto-annotated-v6\review_sample.json
  Ocr-markdown\auto-annotated-v6\review_checklist_2026-09-09.md
"""

import glob
import io
import json
import os
import random
import re
import sys
import time
from collections import Counter

ROOT = r"D:\Project\Papers\Ocr-markdown\auto-annotated-v6"
OUT_JSON = os.path.join(ROOT, "review_sample.json")
OUT_MD = os.path.join(ROOT, "review_checklist_2026-09-09.md")
SEED = 20260909
N_TOTAL = 100

RE_Q = re.compile(r"META:question:start")
RE_A = re.compile(r"META:answer:start")
RE_E = re.compile(r"META:explanation:start")
RE_QEND = re.compile(r"META:question:end")
RE_AEND = re.compile(r"META:answer:end")
RE_IMG = re.compile(r"<img\s+src=")
RE_QTYPE = re.compile(r"META:question:start:\d+,(\w+)")
RE_DOC = re.compile(r"META:doc:(.*)-->")


def file_stats(path):
    t = io.open(path, encoding="utf-8").read()
    q, a, e = len(RE_Q.findall(t)), len(RE_A.findall(t)), len(RE_E.findall(t))
    flags = []
    if q == 0:
        flags.append("无题目标记")
    if a == 0:
        flags.append("无答案标记")
    if q and a and abs(q - a) > max(2, q * 0.2):
        flags.append(f"题答数量差异大({q}题/{a}答)")
    elif q and a and q != a:
        flags.append(f"题答数量不等({q}题/{a}答)")
    if len(RE_Q.findall(t)) != len(RE_QEND.findall(t)):
        flags.append("题目标记不配对")
    if len(RE_A.findall(t)) != len(RE_AEND.findall(t)):
        flags.append("答案标记不配对")
    doc = RE_DOC.search(t)
    return {
        "file": path,
        "questions": q,
        "answers": a,
        "explanations": e,
        "images": len(RE_IMG.findall(t)),
        "types": dict(Counter(RE_QTYPE.findall(t))),
        "doc_meta": doc.group(1).strip() if doc else "",
        "chars": len(t),
        "flags": flags,
        "risk": len(flags),
    }


def main():
    random.seed(SEED)
    strata = {}
    for g in ["高一", "高二", "高三"]:
        for s in sorted(os.listdir(os.path.join(ROOT, g))):
            d = os.path.join(ROOT, g, s)
            if not os.path.isdir(d):
                continue
            for f in sorted(glob.glob(os.path.join(d, "*.md"))):
                strata.setdefault(f"{g}/{s}", []).append(f)

    print(f"分层数: {len(strata)}")
    all_stats = []
    strata_stats = {}
    for k, files in strata.items():
        lst = [file_stats(f) for f in files]
        strata_stats[k] = lst
        all_stats.extend(lst)

    # ---- 全量质量基线 ----
    baseline = {
        "总文件数": len(all_stats),
        "标注题目总数": sum(x["questions"] for x in all_stats),
        "标注答案总数": sum(x["answers"] for x in all_stats),
        "标注解析总数": sum(x["explanations"] for x in all_stats),
        "含图片引用文件数": sum(1 for x in all_stats if x["images"]),
        "无答案标记文件数": sum(1 for x in all_stats if "无答案标记" in x["flags"]),
        "无题目标记文件数": sum(1 for x in all_stats if "无题目标记" in x["flags"]),
        "题答数量不等文件数": sum(1 for x in all_stats if any("题答" in f for f in x["flags"])),
        "标记不配对文件数": sum(1 for x in all_stats if any("不配对" in f for f in x["flags"])),
    }
    print(json.dumps(baseline, ensure_ascii=False, indent=2))

    # ---- 分层配额 ----
    total_files = len(all_stats)
    quota = {}
    remaining = N_TOTAL
    keys = sorted(strata_stats.keys())
    for k in keys:
        n = len(strata_stats[k])
        q = max(2, round(N_TOTAL * n / total_files))
        quota[k] = min(q, n)
        remaining -= quota[k]
    # 调整到总数接近 N_TOTAL
    while remaining < 0:
        big = max(quota, key=lambda k: quota[k])
        if quota[big] > 2:
            quota[big] -= 1
            remaining += 1
        else:
            break

    # ---- 层内抽样: 一半随机 + 一半高风险 ----
    sample = []
    for k in keys:
        pool = strata_stats[k]
        n = min(quota[k], len(pool))
        risky = sorted([x for x in pool if x["risk"] > 0], key=lambda x: -x["risk"])
        safe = [x for x in pool if x["risk"] == 0]
        random.shuffle(risky)
        random.shuffle(safe)
        n_risk = min(len(risky), (n + 1) // 2)
        picked = risky[:n_risk] + safe[: n - n_risk]
        for x in picked:
            x = dict(x)
            x["stratum"] = k
            sample.append(x)

    # ---- 输出 JSON ----
    with io.open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "n_total": N_TOTAL, "quota": quota,
                   "baseline": baseline, "sample": sample},
                  f, ensure_ascii=False, indent=1)

    # ---- 输出审核清单 Markdown ----
    lines = []
    lines.append("# 人工审核清单 (auto-annotated-v6 抽样)")
    lines.append("")
    lines.append(f"- 生成时间: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 抽样方式: 按 年级×科目 分层, 层内一半随机 + 一半高风险优先, 随机种子 {SEED}")
    lines.append(f"- 样本量: **{len(sample)} / {total_files}**")
    lines.append("")
    lines.append("## 全量质量基线 (审核参照)")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---|")
    for k, v in baseline.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## 审核要点")
    lines.append("")
    lines.append("1. **题目边界**: 题号识别是否正确, 起止位置是否准确, 有无多题合并/误拆")
    lines.append("2. **答案对应**: 答案标记是否与题目一一对应, 有无漏标/错位")
    lines.append("3. **解析标记**: 【解析】【详解】是否被正确识别为 explanation")
    lines.append("4. **图片引用**: 图片是否归属正确题目, 路径是否可解析")
    lines.append("5. **元数据**: subject/grade/year 是否与文件内容一致")
    lines.append("")
    lines.append("每份审核后请在结论处标注: ✅ 合格 / ⚠️ 小问题(记录) / ❌ 需重做(记录)")
    lines.append("")

    by_stratum = {}
    for x in sample:
        by_stratum.setdefault(x["stratum"], []).append(x)

    for k in keys:
        if k not in by_stratum:
            continue
        lines.append(f"## {k} ({len(by_stratum[k])} 份)")
        lines.append("")
        for i, x in enumerate(sorted(by_stratum[k], key=lambda z: -z["risk"]), 1):
            rel = os.path.relpath(x["file"], ROOT).replace("\\", "/")
            flag_txt = ("；".join(x["flags"])) if x["flags"] else "无"
            lines.append(f"### {k} #{i} {os.path.basename(x['file'])}")
            lines.append("")
            lines.append(f"- 路径: `{rel}`")
            lines.append(f"- 统计: 题目 {x['questions']} / 答案 {x['answers']} / 解析 {x['explanations']} / 图片 {x['images']}")
            lines.append(f"- 元数据: `{x['doc_meta']}`")
            lines.append(f"- 风险标记: {flag_txt}")
            lines.append("- 审核: 题目边界 [ ]  答案对应 [ ]  解析标记 [ ]  图片引用 [ ]  元数据 [ ]")
            lines.append("- 结论: __________")
            lines.append("")

    with io.open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"样本: {len(sample)} 份 | 配额: {json.dumps(quota, ensure_ascii=False)}")
    print(f"输出: {OUT_MD}")
    print(f"输出: {OUT_JSON}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
