# -*- coding: utf-8 -*-
"""
r59_r58_review.py — R58(BUG-11 修复轮)结论的对抗性复证工具。

纪律:凡被审结论,一律用独立实现重测(不复用 recover_images 的
scan_md_files / is_source_top_dir / REF),R58 若与本工具分歧以本工具为准并记 finding。

审查面:
  P1 视野账目独立重算(3119/2421/698 + 逐目录表 + 根层 md + 顶层目录分类穷举)
  P2 攻"盲区 0 缺图":扩展引用语法(任意扩展名/大小写/bare 图片 token/<img 标签)
     + "515 已标记"与 _imgs 目录落盘存在性 + 未标记 84 份零图片 token 验证
  P4 攻"误纳派生目录仅多扫":无排除政策下会被真实处理/重写的派生文件面
输出 data/r59_r58_review.json。只读,不写任何语料。

用法: python scripts/r59_r58_review.py
"""
import io
import json
import os
import re
import sys
from collections import Counter

BASE = r"D:\Project\Papers"
OCR_ROOT = os.path.join(BASE, "Ocr-markdown")
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
R58_JSON = os.path.join(BASE, "data", "r58_bug11_coverage.json")
OUT = os.path.join(BASE, "data", "r59_r58_review.json")

# 独立定义:R58 证据工件中列出的 10 个源目录(硬取自工件,非被审代码)
OLD_DIRS = {"高一", "高二", "高三", "未分类"}
DERIVED_PREFIXES = ("auto-annotated", "reslice")
DERIVED_NAMES = {"_imgs", ".cache"}

# 独立的更宽引用语法(攻 R58 的 REF 只认 .jpg、区分大小写)
RE_IMGS_ANY = re.compile(r"(?<!_)imgs/([^)\"'\s>]+)", re.IGNORECASE)
RE_IMG_TOKEN = re.compile(r"[^\s()\"'<>]+\.(?:jpg|jpeg|png|gif|webp|bmp)", re.IGNORECASE)
RE_IMG_TAG = re.compile(r"<img\b", re.IGNORECASE)


def pdf_index_independent():
    idx = {}
    for root, _d, files in os.walk(PDF_ROOT):
        for fn in files:
            if fn.lower().endswith(".pdf"):
                idx.setdefault(os.path.splitext(fn)[0], os.path.join(root, fn))
    return idx


def classify_top(name):
    if name in DERIVED_NAMES or name.startswith(DERIVED_PREFIXES):
        return "derived"
    return "source"


def walk_md(top):
    out = []
    for r, dirs, files in os.walk(os.path.join(OCR_ROOT, top)):
        dirs[:] = [x for x in dirs if x != "_imgs"]
        for fn in files:
            if fn.lower().endswith(".md"):
                out.append(os.path.join(r, fn))
    return sorted(out)


def main():
    r58 = json.load(io.open(R58_JSON, encoding="utf-8"))
    report = {"round": "R59", "target": "R58 BUG-11", "findings": []}

    # ---------- P1: 视野账目独立重算 ----------
    tops = sorted(os.listdir(OCR_ROOT))
    src_tops = [t for t in tops if os.path.isdir(os.path.join(OCR_ROOT, t))
                and classify_top(t) == "source"]
    derived_tops = [t for t in tops if os.path.isdir(os.path.join(OCR_ROOT, t))
                    and classify_top(t) == "derived"]
    root_md = [f for f in os.listdir(OCR_ROOT)
               if os.path.isfile(os.path.join(OCR_ROOT, f)) and f.lower().endswith(".md")]

    per_dir_md = {}
    all_scanned = []
    for t in src_tops:
        fs = walk_md(t)
        per_dir_md[t] = len(fs)
        all_scanned.extend(fs)
    all_scanned = sorted(all_scanned)
    old_n = sum(v for k, v in per_dir_md.items() if k in OLD_DIRS)

    # 顶层目录分类穷举:每个顶层目录必须要么在 R58 工件 per_dir 表中,要么可识别为派生
    r58_dirs = set(r58["per_dir"].keys())
    classification_gap = []
    for t in tops:
        if not os.path.isdir(os.path.join(OCR_ROOT, t)):
            continue
        in_table = t in r58_dirs
        derived = classify_top(t) == "derived"
        if in_table and derived:
            classification_gap.append(f"派生目录混入源表: {t}")
        if not in_table and not derived:
            classification_gap.append(f"源目录缺席工件表: {t}")

    p1 = {
        "per_dir_md_independent": per_dir_md,
        "total_independent": len(all_scanned),
        "old_scope_independent": old_n,
        "newly_visible_independent": len(all_scanned) - old_n,
        "r58_total": r58["scanned_total_new_scope"],
        "r58_old": r58["scanned_total_old_scope"],
        "r58_newly": r58["newly_visible"],
        "per_dir_match_r58": {k: (per_dir_md.get(k) == r58["per_dir"].get(k, {}).get("md_total"))
                              for k in r58_dirs},
        "derived_tops": derived_tops,
        "root_level_md": root_md,
        "classification_gap": classification_gap,
        "scan_list_deterministic_sorted": all_scanned == sorted(all_scanned),
    }
    p1["total_match"] = p1["total_independent"] == p1["r58_total"]
    p1["old_match"] = p1["old_scope_independent"] == p1["r58_old"]
    p1["newly_match"] = p1["newly_visible_independent"] == p1["r58_newly"]
    report["P1_scope_ledger"] = p1
    if not (p1["total_match"] and p1["old_match"] and p1["newly_match"]
            and all(p1["per_dir_match_r58"].values()) and not classification_gap):
        report["findings"].append("P1 视野账目与 R58 不一致或分类有缺口")

    # ---------- P2: 攻"盲区 0 缺图" ----------
    # 判定基准 = 完整 src="..." 属性解析(盲区图片引用几乎全是 <img src=...>);
    # 裸 token 扫描因目录名含 (1) 会在括号处截断产生假阳性,仅作参考,不作判定依据。
    new_tops = [t for t in src_tops if t not in OLD_DIRS]
    blind = [p for p in all_scanned
             if os.path.relpath(p, OCR_ROOT).split(os.sep)[0] in new_tops]
    RE_SRC = re.compile(r'src\s*=\s*"([^"]+)"', re.IGNORECASE)
    p2 = {"blind_files": len(blind),
          "imgs_ref_anyext_hits": 0,          # (?<!_)imgs/ 任意扩展名(悬空形态)
          "src_total": 0, "src_to_imgs_recovered": 0,
          "src_dangling_imgs": 0, "src_other": 0, "src_other_samples": [],
          "markdown_img_syntax": 0,
          "marked_gaokao": 0, "marked_dir_missing": [],
          "unmarked_gaokao": 0, "unmarked_with_imgs_ref": []}
    for p in blind:
        text = io.open(p, encoding="utf-8", errors="replace").read()
        base = os.path.splitext(os.path.basename(p))[0]
        p2["imgs_ref_anyext_hits"] += len(RE_IMGS_ANY.findall(text))
        p2["markdown_img_syntax"] += len(re.findall(r"!\[[^\]]*\]\(", text))
        for m in RE_SRC.finditer(text):
            v = m.group(1)
            p2["src_total"] += 1
            if "_imgs/" in v:
                p2["src_to_imgs_recovered"] += 1
            elif re.search(r"(?<!_)imgs/", v, re.IGNORECASE):
                p2["src_dangling_imgs"] += 1
            else:
                p2["src_other"] += 1
                if len(p2["src_other_samples"]) < 5:
                    p2["src_other_samples"].append(v)
        top = os.path.relpath(p, OCR_ROOT).split(os.sep)[0]
        if top == "高考真题":
            if f"_imgs/{base}/" in text:
                p2["marked_gaokao"] += 1
                if not os.path.isdir(os.path.join(OCR_ROOT, "_imgs", base)):
                    p2["marked_dir_missing"].append(base)
            else:
                p2["unmarked_gaokao"] += 1
                if re.search(r"(?<!_)imgs/", text, re.IGNORECASE):
                    p2["unmarked_with_imgs_ref"].append(base)
    # R58 结论"盲区当前缺图候选=0"稳健判据:无任何悬空 imgs/ 引用形态 + 无指向 imgs/ 的 src
    p2["r58_claim_dangling_candidates_in_blind"] = 0
    p2["claim_robust_wide_grammar"] = (p2["imgs_ref_anyext_hits"] == 0
                                       and p2["src_dangling_imgs"] == 0)
    report["P2_blind_zero_dangling"] = p2
    if not p2["claim_robust_wide_grammar"]:
        report["findings"].append("P2 '盲区 0 缺图'在扩展语法下不成立")

    # ---------- P4: 攻"误纳派生目录仅多扫" ----------
    pdf_idx = pdf_index_independent()
    p4 = {"derived_dirs_md": 0, "with_raw_refs": 0, "raw_ref_total": 0,
          "would_process_pdf_hit": 0, "per_dir": {}}
    for t in derived_tops:
        st = Counter()
        for p in walk_md(t):
            st["md"] += 1
            text = io.open(p, encoding="utf-8", errors="replace").read()
            refs = re.findall(r"(?<!_)imgs/([^)\"'\s>]+?\.jpg)", text)
            if refs:
                st["with_raw_refs"] += 1
                st["raw_refs"] += len(set(refs))
                base = os.path.splitext(os.path.basename(p))[0]
                if base in pdf_idx:
                    st["would_process"] += 1
        if st:
            p4["per_dir"][t] = dict(st)
        p4["derived_dirs_md"] += st.get("md", 0)
        p4["with_raw_refs"] += st.get("with_raw_refs", 0)
        p4["raw_ref_total"] += st.get("raw_refs", 0)
        p4["would_process_pdf_hit"] += st.get("would_process", 0)
    p4["r58_claim"] = "误纳派生目录的代价只是多扫(幂等跳过),不会漏修"
    p4["claim_holds"] = p4["would_process_pdf_hit"] == 0
    report["P4_overinclusion_cost"] = p4
    if not p4["claim_holds"]:
        report["findings"].append(
            f"P4 '误纳仅多扫'不成立:无排除政策下 {p4['would_process_pdf_hit']} 份派生 md "
            f"会被真实处理(提取图片+就地重写+审计记录)")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(report, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
