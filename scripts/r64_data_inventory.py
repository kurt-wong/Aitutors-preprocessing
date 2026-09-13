# -*- coding: utf-8 -*-
r"""
r64_data_inventory.py — BUG-14-DATA D0~D3 实测武器(只读,零修改生产数据)

用户裁定的攻击顺序(R64):
  D0 Corpus inventory freeze   — 冻结全库 md 清单(path/basename/suffix/size/SHA-256/
                                 所属目录/是否 derived/当前 runner 分类/provenance)
  D1 未分类逐类归因             — 145 份逐文件机器可复现 reason bucket
  D2 basename collision 指纹    — 73 组:group → SHA-256 set → byte-identical/different
  D3 duplicate source 真实性    — 仅字节/归一化/PDF 侧机器证据;logical source 语义
                                 判定一律不猜,输出 PENDING_REVIEW 供用户裁定

铁律落实:
  - 只读 corpus;不移动、不改名、不删除、不自动归并任何生产数据。
  - fail-closed:单文件不可读/非法 UTF-8 → 显式错误记录,批继续,绝不静默跳过。
  - 无 fallback / 无猜测 / 无自动修正。
  - runner 与 reclassify 的判定逻辑为"副本实现(replica)",由测试锚定源码原文
    (ocr_service/batch_convert_pdf.py L93-106 / scripts/reclassify_unknown.py)
    防漂移;副本与源码不一致时以源码为准。

输出(确定性排序,可重跑复现):
  data/r64_corpus_inventory.json    D0 全库清单
  data/r64_unknown_buckets.json     D1 未分类归因
  data/r64_collision_fingerprint.json D2+D3 碰撞指纹与重复真实性

用法: python scripts/r64_data_inventory.py
"""

import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

BASE = Path(r"D:\Project\Papers")
# 环境变量覆写仅用于测试(合成夹具);生产行为不变。
OCR_ROOT = Path(os.environ.get("R64_OCR_ROOT") or BASE / "Ocr-markdown")
PDF_ROOT = Path(os.environ.get("R64_PDF_ROOT") or BASE / "maintainess" / "PDF")
DATA_DIR = Path(os.environ.get("R64_DATA_DIR") or BASE / "data")
AUDIT_JSONL = Path(os.environ.get("R64_AUDIT") or BASE / "data" / "reclassify_audit.jsonl")

OUT_INVENTORY = DATA_DIR / "r64_corpus_inventory.json"
OUT_BUCKETS = DATA_DIR / "r64_unknown_buckets.json"
OUT_COLLISION = DATA_DIR / "r64_collision_fingerprint.json"

SOURCE_DIRS = [
    "高一", "高二", "高三", "高考真题", "未分类",
    "合格考", "会考", "竞赛自招", "其他汇编", "学业水平考试",
]
DERIVED_PREFIXES = ("auto-annotated", "reslice")
NON_MD_TOP_DIRS = {".cache", "_imgs"}  # 已知非语料目录

# D1 主口径 = 顶层 未分类/**;D1 附录口径 = 散落(如 高三/未分类/**,reclassify EXTRA_DIRS)
UNKNOWN_TOP = "未分类"
STRAY_DIRS = [("高三", "未分类")]

NORM_ALGO = "sha256(NFC(text); CRLF/CR->LF; per-line rstrip; whole strip)"

# ---------------------------------------------------------------------------
# runner 逻辑副本 —— 锚定 ocr_service/batch_convert_pdf.py L93-106
# (源码以 if/elif 链实现;此处逐条等价复制,测试锚定源码原文防漂移)
# ---------------------------------------------------------------------------
GRADE_RULES = [
    (re.compile(r"高一|高1"), "高一"),
    (re.compile(r"高二|高2"), "高二"),
    (re.compile(r"高三|高3"), "高三"),
]
SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
SANITIZE_RE = re.compile(r'[<>:"/\\|?*]')


def extract_grade_subject(filename):
    """batch_convert_pdf.extract_grade_subject 副本(逐条等价)。"""
    grade = "未分类"
    subject = "未分类"
    for pat, g in GRADE_RULES:
        if pat.search(filename):
            grade = g
            break
    for s in SUBJECTS:
        if s in filename:
            subject = s
            break
    return grade, subject


def sanitize_stem(stem):
    """batch_convert_pdf L115 的输出名净化副本。"""
    return SANITIZE_RE.sub("_", stem)


# ---------------------------------------------------------------------------
# reclassify 逻辑副本 —— 锚定 scripts/reclassify_unknown.py TYPE_RULES/GAOKAO_RE
# ---------------------------------------------------------------------------
GAOKAO_RE = re.compile(r"高考[^，。；]{0,6}真题|真题汇编")
TYPE_RULES = [
    ("高考真题", ["高考真题", "真题汇编"]),
    ("合格考", ["合格考", "合格性考试", "合性试"]),
    ("会考", ["会考"]),
    ("学业水平考试", ["学业水平", "学考", "水平考试"]),
    ("等级考", ["等级考"]),
    ("竞赛自招", ["竞赛", "博雅", "强基", "自主招生", "领军", "筑梦"]),
]


def reclassify_name_only(name):
    """仅用文件名跑 reclassify.classify 的规则(不做内容嗅探)。"""
    if GAOKAO_RE.search(name):
        return "高考真题"
    for cat, kws in TYPE_RULES:
        if any(k in name for k in kws):
            return cat
    return None


def reclassify_with_text(name, text):
    """reclassify.classify 副本(hay = name + 前 3000 字)。"""
    hay = name + "\n" + text
    if GAOKAO_RE.search(name):
        return "高考真题"
    for cat, kws in TYPE_RULES:
        if any(k in hay for k in kws):
            return cat
    return "其他汇编"  # reclassify 的兜底(非 None);D1 用 None 表示"未判定"


# ---------------------------------------------------------------------------
# 工具(全部 fail-closed:错误入记录,不抛出杀批)
# ---------------------------------------------------------------------------
def sha256_file(path):
    """流式 SHA-256。返回 (hex, None) 或 (None, error_str)。"""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest(), None
    except OSError as e:
        return None, f"OSError: {e!r}"


def normalized_text_sha256(path):
    """归一化文本哈希。非法 UTF-8 → (None, "invalid-utf8") 亦不崩溃。"""
    try:
        with io.open(path, encoding="utf-8", errors="strict") as f:
            text = f.read()
    except UnicodeDecodeError:
        return None, "invalid-utf8"
    except OSError as e:
        return None, f"OSError: {e!r}"
    norm = unicodedata.normalize("NFC", text)
    norm = norm.replace("\r\n", "\n").replace("\r", "\n")
    norm = "\n".join(line.rstrip() for line in norm.split("\n")).strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest(), None


def sniff_text(path, n=3000):
    try:
        with io.open(path, encoding="utf-8", errors="strict") as f:
            return f.read(n)
    except (OSError, UnicodeDecodeError):
        return ""  # 与 reclassify.sniff_text 同语义:嗅探失败=空串(分类层会自然落空)


def is_derived_top(name):
    return name.startswith(DERIVED_PREFIXES)


DUP_SUFFIX_RE = re.compile(r"\(\d+\)$")


def build_pdf_index():
    r"""maintainess\PDF 全树 stem 索引(净化后 stem → 相对路径列表)。"""
    exact = {}
    casefold = {}
    stripped = {}  # 去下载重复后缀 X(1) → X 的 stem 索引
    total = 0
    if not PDF_ROOT.is_dir():
        return exact, casefold, stripped, total
    for dirpath, _dirnames, filenames in os.walk(PDF_ROOT):
        for fn in filenames:
            if not fn.lower().endswith(".pdf"):
                continue
            total += 1
            stem = sanitize_stem(os.path.splitext(fn)[0])
            rel = os.path.relpath(os.path.join(dirpath, fn), PDF_ROOT).replace("\\", "/")
            exact.setdefault(stem, []).append(rel)
            casefold.setdefault(stem.casefold(), []).append(rel)
            base = DUP_SUFFIX_RE.sub("", stem)
            if base != stem:
                stripped.setdefault(base, []).append(rel)
    for d in (exact, casefold, stripped):
        for k in d:
            d[k].sort()
    return exact, casefold, stripped, total


# ---------------------------------------------------------------------------
# D0 — 全库清单
# ---------------------------------------------------------------------------
def md_role(stem, top_dir):
    if top_dir not in SOURCE_DIRS:
        if stem.endswith(".annotated"):
            return "annotated"
        return "resliced"
    return "source-md"


def collect_inventory():
    records = []
    errors = []
    if not OCR_ROOT.is_dir():
        raise SystemExit(f"Input Integrity Gate: OCR_ROOT 不存在: {OCR_ROOT}")
    for top in sorted(os.listdir(OCR_ROOT)):
        top_path = OCR_ROOT / top
        if not top_path.is_dir():
            continue
        if top in NON_MD_TOP_DIRS:
            continue
        in_source = top in SOURCE_DIRS
        if not in_source and not is_derived_top(top):
            # 未知前缀的顶层目录 = admission 异常,如实记录,不猜测
            errors.append(f"UNKNOWN_TOP_DIR: {top}")
        for dirpath, _dirnames, filenames in os.walk(top_path):
            for fn in sorted(filenames):
                if not fn.lower().endswith(".md"):
                    continue
                full = Path(dirpath) / fn
                rel = full.relative_to(OCR_ROOT).as_posix()
                stem, suffix = os.path.splitext(fn)
                try:
                    st = full.stat()
                    size, mtime = st.st_size, st.st_mtime
                    stat_err = None
                except OSError as e:
                    size, mtime, stat_err = None, None, f"OSError: {e!r}"
                sha, sha_err = sha256_file(full)
                nsha, nsha_err = normalized_text_sha256(full)
                # colocated manifest 证据(源树应为零;derived 为 {stem}.manifest.json)
                manifest_path = Path(dirpath) / (stem + ".manifest.json")
                if manifest_path.is_file():
                    msha, _ = sha256_file(manifest_path)
                    mf_status = "present"
                else:
                    msha, mf_status = None, "absent"
                grade, subject = extract_grade_subject(fn)
                rec = {
                    "rel_path": rel,
                    "basename": fn,
                    "stem": stem,
                    "suffix": suffix,
                    "size": size,
                    "sha256": sha,
                    "norm_sha256": nsha,
                    "mtime": mtime,
                    "top_dir": top,
                    "parent_dir": Path(dirpath).relative_to(OCR_ROOT).as_posix(),
                    "tree": "source" if in_source else "derived",
                    "role": md_role(stem, top),
                    "runner_grade": grade,
                    "runner_subject": subject,
                    "manifest_status": mf_status,
                    "manifest_sha256": msha,
                }
                if stat_err or sha_err or nsha_err:
                    rec["errors"] = [e for e in (stat_err, sha_err, nsha_err) if e]
                    errors.append(f"{rel}: {rec['errors']}")
                records.append(rec)
    records.sort(key=lambda r: r["rel_path"])
    return records, errors


# ---------------------------------------------------------------------------
# D1 — 未分类归因(逐文件机器可复现 bucket)
# ---------------------------------------------------------------------------
def classify_unknown_file(rec, path, basename_index):
    """
    返回 (bucket, predicates)。bucket 取值(优先级从上到下):
      UNREADABLE            无法读取 → PENDING_REVIEW(fail-closed)
      PLACEMENT_MISMATCH    文件名含年级关键词却落位未分类 → 目录/来源异常
      NAME_RULE_COVERED     文件名即可被 reclassify 规则覆盖 → 分类规则缺口/回流
      CONTENT_RULE_COVERED  仅正文嗅探可覆盖 → 内容可判(文件名无信号)
      UNDETERMINED          名+正文均无信号 → 真正孤儿候选 PENDING_REVIEW
    附加 flags(不改变 bucket):dup_twin / download_dup_suffix / non_nfc / derived_artifact
    """
    preds = {}
    if rec.get("errors"):
        return "UNREADABLE", {"error": rec["errors"]}
    grade, subject = extract_grade_subject(basename_index)
    preds["runner_grade"] = grade
    preds["runner_subject"] = subject
    name_cat = reclassify_name_only(basename_index)
    preds["reclassify_name"] = name_cat
    text = sniff_text(path)
    preds["reclassify_with_text"] = reclassify_with_text(basename_index, text)
    # 碰撞孪生:同名文件在源树其他类型目录也存在
    twins = [
        p for p in DUPLICATE_BASENAME_INDEX.get(basename_index, [])
        if not p.startswith(UNKNOWN_TOP + "/")
    ]
    preds["dup_twins_outside_unknown"] = sorted(twins)
    flags = []
    if twins:
        flags.append("dup_twin")
    if DUP_SUFFIX_RE.search(Path(basename_index).stem):
        flags.append("download_dup_suffix")
    if unicodedata.normalize("NFC", basename_index) != basename_index:
        flags.append("non_nfc")
    # 派生物误入源树:同目录存在 .manifest.json / .annotated.md
    stem = os.path.splitext(basename_index)[0]
    sib = Path(path).parent
    if (sib / (stem + ".manifest.json")).is_file() or (sib / (stem + ".annotated.md")).is_file():
        flags.append("derived_artifact")
    preds["flags"] = flags
    if grade != "未分类":
        return "PLACEMENT_MISMATCH", preds
    if name_cat is not None:
        return "NAME_RULE_COVERED", preds
    if preds["reclassify_with_text"] != "其他汇编":
        return "CONTENT_RULE_COVERED", preds
    return "UNDETERMINED", preds


BUCKET_MEANINGS = {
    "UNREADABLE": "无法读取,归因不可判定(fail-closed)→ PENDING_REVIEW",
    "PLACEMENT_MISMATCH": "文件名含年级关键词但落位未分类 → 目录/来源异常(真实落位 bug 候选)",
    "NAME_RULE_COVERED": "文件名即可被 reclassify 类型规则覆盖 → 正常但重归类未跑/跑步机回流(规则缺口)",
    "CONTENT_RULE_COVERED": "仅正文内容可判类型 → 文件名无信号,需内容推断",
    "UNDETERMINED": "文件名+正文均无信号 → 真正孤儿候选 → PENDING_REVIEW(不自动归类)",
}


# 全局(在 main 中构建):basename → 源树 rel_path 列表
DUPLICATE_BASENAME_INDEX = {}


def build_unknown_analysis(records, pdf_exact, pdf_casefold):
    by_rel = {r["rel_path"]: r for r in records}
    rows = []
    # 主口径
    main_rels = sorted(r["rel_path"] for r in records
                       if r["tree"] == "source" and r["top_dir"] == UNKNOWN_TOP)
    # 附录口径(散落)
    stray_rels = sorted(
        r["rel_path"] for r in records
        if r["tree"] == "source" and any(
            r["rel_path"].startswith(f"{a}/{b}/") or r["rel_path"] == f"{a}/{b}"
            for a, b in STRAY_DIRS))
    for scope, rels in (("main", main_rels), ("stray", stray_rels)):
        for rel in rels:
            rec = by_rel[rel]
            bucket, preds = classify_unknown_file(rec, OCR_ROOT / rel, rec["basename"])
            stem = sanitize_stem(rec["stem"])
            pdf_hits = pdf_exact.get(stem, [])
            pdf_hits_cf = [p for p in pdf_casefold.get(stem.casefold(), []) if p not in pdf_hits]
            rows.append({
                "scope": scope,
                "rel_path": rel,
                "basename": rec["basename"],
                "bucket": bucket,
                "predicates": preds,
                "pdf_exact_matches": pdf_hits[:5],
                "pdf_exact_match_count": len(pdf_hits),
                "pdf_casefold_extra_matches": pdf_hits_cf[:5],
            })
    summary = {}
    for row in rows:
        key = f"{row['scope']}:{row['bucket']}"
        summary[key] = summary.get(key, 0) + 1
    return {"rows": rows, "summary": summary, "bucket_meanings": BUCKET_MEANINGS}


def build_audit_index():
    """reclassify_audit.jsonl 搬移审计索引(basename → [{from,to}] 预览)。
    fail-closed:文件缺失/坏行 → 显式记录,不崩溃。"""
    by_base = {}
    errors = []
    if not AUDIT_JSONL.is_file():
        return by_base, [f"AUDIT_ABSENT: {AUDIT_JSONL}"], 0
    n = 0
    try:
        with io.open(AUDIT_JSONL, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError as e:
                    errors.append(f"AUDIT_BAD_LINE {i}: {e!r}")
                    continue
                if not isinstance(rec, dict):
                    errors.append(f"AUDIT_BAD_RECORD {i}: not an object")
                    continue
                src, dst = rec.get("from"), rec.get("to")
                if not isinstance(src, str) or not isinstance(dst, str):
                    errors.append(f"AUDIT_BAD_RECORD {i}: from/to not str")
                    continue
                n += 1
                # 审计由 Windows 写入(反斜杠路径);跨平台索引须双分隔符归一
                # (F-r64-1:CI ubuntu 上 os.path.basename 不切 '\' → 键错位)
                by_base.setdefault(os.path.basename(src.replace("\\", "/")), []).append(
                    {"from": src, "to": dst})
    except OSError as e:
        errors.append(f"AUDIT_UNREADABLE: {e!r}")
    for k in by_base:
        by_base[k].sort(key=lambda r: (r["from"], r["to"]))
    return by_base, errors, n


# ---------------------------------------------------------------------------
# D2 + D3 — 碰撞指纹与重复真实性
# ---------------------------------------------------------------------------
def build_collisions(records, pdf_exact, pdf_stripped, audit_index):
    source = [r for r in records if r["tree"] == "source"]
    groups = {}
    for r in source:
        groups.setdefault(r["basename"], []).append(r)
    out = []
    for name in sorted(groups):
        members = groups[name]
        if len(members) < 2:
            continue
        members = sorted(members, key=lambda r: r["rel_path"])
        shas = [m["sha256"] for m in members]
        nshas = [m["norm_sha256"] for m in members]
        byte_identical = len(set(shas)) == 1
        norm_identical = len(set(nshas)) == 1
        unreadable = any(m.get("errors") for m in members)
        top_dirs = sorted({m["top_dir"] for m in members})
        stem = os.path.splitext(name)[0]
        pdf_hits = pdf_exact.get(sanitize_stem(stem), [])
        stripped_hits = pdf_stripped.get(sanitize_stem(stem), [])
        # mtime 序(事实记录,不做因果判定)
        with_mt = [m for m in members if m["mtime"] is not None]
        ordered = sorted(with_mt, key=lambda m: m["mtime"])
        out.append({
            "basename": name,
            "n_files": len(members),
            "top_dirs": top_dirs,
            "byte_identical": byte_identical,
            "norm_identical": norm_identical,
            "unreadable": unreadable,
            "members": [{
                "rel_path": m["rel_path"],
                "top_dir": m["top_dir"],
                "size": m["size"],
                "sha256": m["sha256"],
                "norm_sha256": m["norm_sha256"],
                "mtime": m["mtime"],
            } for m in members],
            "mtime_order": [m["rel_path"] for m in ordered],
            "pdf_exact_match_count": len(pdf_hits),
            "pdf_exact_matches": pdf_hits[:5],
            "pdf_stripped_match_count": len(stripped_hits),
            "pdf_stripped_matches": stripped_hits[:5],
            "in_reclassify_audit": name in audit_index,
            "audit_moves": audit_index.get(name, [])[:3],
        })
    summary = {
        "n_groups": len(out),
        "n_files_in_groups": sum(g["n_files"] for g in out),
        "byte_identical_groups": sum(1 for g in out if g["byte_identical"]),
        "norm_identical_groups": sum(1 for g in out if g["norm_identical"]),
        "byte_different_groups": sum(1 for g in out if not g["byte_identical"] and not g["unreadable"]),
        "unreadable_groups": sum(1 for g in out if g["unreadable"]),
        "pdf_exact_hit_groups": sum(1 for g in out if g["pdf_exact_match_count"] > 0),
        "pdf_only_stripped_hit_groups": sum(
            1 for g in out if g["pdf_exact_match_count"] == 0 and g["pdf_stripped_match_count"] > 0),
        "pdf_no_hit_groups": sum(
            1 for g in out if g["pdf_exact_match_count"] == 0 and g["pdf_stripped_match_count"] == 0),
        "audit_hit_groups": sum(1 for g in out if g["in_reclassify_audit"]),
        "top_dir_pair_kinds": {},
    }
    for g in out:
        key = "+".join(g["top_dirs"])
        summary["top_dir_pair_kinds"][key] = summary["top_dir_pair_kinds"].get(key, 0) + 1
    verdict = (
        "D3 裁决域外:本武器只提供机器证据层(basename → SHA-256 → 归一化文本 → PDF 侧同源)。"
        "'是否同一 logical source'属业务语义层,一律 PENDING_REVIEW,禁止自动归并。"
    )
    return {"groups": out, "summary": summary, "d3_verdict": verdict}


# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    records, inv_errors = collect_inventory()

    global DUPLICATE_BASENAME_INDEX
    DUPLICATE_BASENAME_INDEX = {}
    for r in records:
        if r["tree"] == "source":
            DUPLICATE_BASENAME_INDEX.setdefault(r["basename"], []).append(r["rel_path"])
    for k in DUPLICATE_BASENAME_INDEX:
        DUPLICATE_BASENAME_INDEX[k].sort()

    pdf_exact, pdf_casefold, pdf_stripped, pdf_total = build_pdf_index()
    audit_index, audit_errors, audit_n = build_audit_index()

    unknown = build_unknown_analysis(records, pdf_exact, pdf_casefold)
    collisions = build_collisions(records, pdf_exact, pdf_stripped, audit_index)

    src_recs = [r for r in records if r["tree"] == "source"]
    der_recs = [r for r in records if r["tree"] == "derived"]
    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "weapon": "scripts/r64_data_inventory.py",
        "read_only": True,
        "norm_algo": NORM_ALGO,
        "source_dirs": SOURCE_DIRS,
        "counts": {
            "md_total": len(records),
            "md_source": len(src_recs),
            "md_derived": len(der_recs),
            "pdf_total_indexed": pdf_total,
            "unknown_main": sum(1 for r in unknown["rows"] if r["scope"] == "main"),
            "unknown_stray": sum(1 for r in unknown["rows"] if r["scope"] == "stray"),
            "collision_groups": collisions["summary"]["n_groups"],
            "collision_files": collisions["summary"]["n_files_in_groups"],
            "audit_moves_indexed": audit_n,
        },
        "inventory_errors": inv_errors,
        "audit_errors": audit_errors,
        "elapsed_sec": round(time.time() - t0, 1),
    }

    for path, payload in (
        (OUT_INVENTORY, {"meta": meta, "records": records}),
        (OUT_BUCKETS, {"meta": meta, "d1": unknown}),
        (OUT_COLLISION, {"meta": meta, "d2_d3": collisions}),
    ):
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=False)
            f.write("\n")

    print(json.dumps(meta["counts"], ensure_ascii=False, indent=1))
    print("D1 buckets:", json.dumps(unknown["summary"], ensure_ascii=False))
    print("D2/D3:", json.dumps(collisions["summary"], ensure_ascii=False)[:800])
    if inv_errors:
        print(f"[WARN] inventory errors: {len(inv_errors)} (evidence preserved in JSON)")
    print(f"outputs: {OUT_INVENTORY.name} / {OUT_BUCKETS.name} / {OUT_COLLISION.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
