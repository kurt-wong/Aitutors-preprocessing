# -*- coding: utf-8 -*-
r"""
r65_r64_review.py — R64 全部结论的独立对抗性复证武器(只读)。

原则:不复用 R64 武器的判定逻辑得出结论——所有聚合、分桶、指纹、时序
均从冻结 JSON 与文件系统**独立重算**后与 R64 记录值比对;任何不一致
如实入账为 FINDING,不修正 R64 数据、不解释、不圆场。

审查面:
  A  三 JSON 交叉一致性 + bucket 逐行独立重判 + dup_twin/后缀独立重算
  B  文件系统全量重哈希 vs 冻结清单(MATCH/MODIFIED/NEW/MISSING)——
     既是"冻结忠实性"证据,也是"零修改生产数据"证据
  C  跑步机机制日志级直接物证(ocr_batch_log.txt 时间戳 vs 回流份 mtime)
     + 审计 from/to 路径与碰撞成员逐组交叉核对
  D  PDF 唯一性独立重算(每碰撞 stem 的 PDF 数分布)
  E  提交武器可重现性:现跑产物 vs 提交 JSON(逐 record 等值)
  F  (脚本外)变异复跑 / 套件重跑 / CI 日志 skip 枚举

输出: data/r65_r64_review.json(确定性,fail-closed)
用法: python scripts/r65_r64_review.py
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

BASE = Path(r"D:\Project\Papers")
OCR_ROOT = BASE / "Ocr-markdown"
PDF_ROOT = BASE / "maintainess" / "PDF"
DATA = BASE / "data"
AUDIT_JSONL = DATA / "reclassify_audit.jsonl"
OCR_LOG = BASE / "logs" / "ocr_batch_log.txt"
OUT = DATA / "r65_r64_review.json"

SOURCE_DIRS = [
    "高一", "高二", "高三", "高考真题", "未分类",
    "合格考", "会考", "竞赛自招", "其他汇编", "学业水平考试",
]
DUP_SUFFIX_RE = re.compile(r"\(\d+\)$")
SANITIZE_RE = re.compile(r'[<>:"/\\|?*]')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_sha(path):
    with io.open(path, encoding="utf-8", errors="strict") as f:
        text = f.read()
    norm = unicodedata.normalize("NFC", text)
    norm = norm.replace("\r\n", "\n").replace("\r", "\n")
    norm = "\n".join(x.rstrip() for x in norm.split("\n")).strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# A — 交叉一致性与独立重算
# ---------------------------------------------------------------------------
def review_cross_consistency(inv, buck, coll):
    records = inv["records"]
    rows = buck["d1"]["rows"]
    groups = coll["d2_d3"]["groups"]
    findings = []

    by_rel = {r["rel_path"]: r for r in records}
    # A1 桶成员集合 = 清单事实(main=未分类/**, stray=高三/未分类/**)
    want_main = sorted(r["rel_path"] for r in records
                       if r["tree"] == "source" and r["top_dir"] == "未分类")
    want_stray = sorted(r["rel_path"] for r in records
                        if r["tree"] == "source" and r["rel_path"].startswith("高三/未分类/"))
    got_main = sorted(r["rel_path"] for r in rows if r["scope"] == "main")
    got_stray = sorted(r["rel_path"] for r in rows if r["scope"] == "stray")
    if want_main != got_main:
        findings.append("A1_MAIN_SET_MISMATCH")
    if want_stray != got_stray:
        findings.append("A1_STRAY_SET_MISMATCH")

    # A2 bucket 逐行独立重判(用记录的原始谓词值,规则独立重述)
    rejudged = {}
    for r in rows:
        p = r["predicates"]
        if "error" in p:
            b = "UNREADABLE"
        elif p.get("runner_grade") != "未分类":
            b = "PLACEMENT_MISMATCH"
        elif p.get("reclassify_name") is not None:
            b = "NAME_RULE_COVERED"
        elif p.get("reclassify_with_text") != "其他汇编":
            b = "CONTENT_RULE_COVERED"
        else:
            b = "UNDETERMINED"
        rejudged[r["rel_path"]] = b
        if b != r["bucket"]:
            findings.append(f"A2_BUCKET_MISMATCH:{r['rel_path']}:{r['bucket']}->{b}")

    # A3 汇总独立重算
    agg = {}
    for r in rows:
        k = f"{r['scope']}:{rejudged[r['rel_path']]}"
        agg[k] = agg.get(k, 0) + 1
    if agg != buck["d1"]["summary"]:
        findings.append(f"A3_SUMMARY_MISMATCH:{agg} vs {buck['d1']['summary']}")

    # A4 dup_twin / 下载后缀 独立重算(仅源树 basename 分组,规则与 R64 声明一致)
    groups_by_base = {}
    for r in records:
        if r["tree"] == "source":
            groups_by_base.setdefault(r["basename"], []).append(r["rel_path"])
    twin_counts = {"main_with_twin": 0, "main_without_twin": 0, "stray_with_twin": 0}
    dup_suffix = 0
    for r in rows:
        base = r["basename"]
        twins = sorted(p for p in groups_by_base.get(base, [])
                       if not p.startswith("未分类/"))
        if twins != sorted(r["predicates"].get("dup_twins_outside_unknown", [])):
            findings.append(f"A4_TWINS_MISMATCH:{r['rel_path']}")
        if r["scope"] == "main":
            twin_counts["main_with_twin" if twins else "main_without_twin"] += 1
        elif twins:
            twin_counts["stray_with_twin"] += 1
        if DUP_SUFFIX_RE.search(Path(base).stem):
            dup_suffix += 1

    # A5 碰撞组独立重算(源树 basename n>=2)
    want_groups = {b: sorted(p) for b, p in groups_by_base.items() if len(p) >= 2}
    got_groups = {g["basename"]: sorted(m["rel_path"] for m in g["members"]) for g in groups}
    if want_groups != got_groups:
        only_want = sorted(set(want_groups) - set(got_groups))
        only_got = sorted(set(got_groups) - set(want_groups))
        findings.append(f"A5_GROUP_SET_MISMATCH:missing={only_want[:3]} extra={only_got[:3]}")

    # A6 组内指纹标记独立重算 + 成员 sha 与清单一致
    for g in groups:
        shas, nshas = [], []
        for m in g["members"]:
            rec = by_rel.get(m["rel_path"])
            if rec is None:
                findings.append(f"A6_MEMBER_NOT_IN_INVENTORY:{m['rel_path']}")
                continue
            if rec["sha256"] != m["sha256"] or rec["norm_sha256"] != m["norm_sha256"]:
                findings.append(f"A6_SHA_MISMATCH:{m['rel_path']}")
            shas.append(m["sha256"])
            nshas.append(m["norm_sha256"])
        if (len(set(shas)) == 1) != g["byte_identical"]:
            findings.append(f"A6_BYTE_FLAG:{g['basename']}")
        if (len(set(nshas)) == 1) != g["norm_identical"]:
            findings.append(f"A6_NORM_FLAG:{g['basename']}")

    # A7 组数/文件数与 R64 D0 计数闭合
    if len(groups) != 73 or sum(g["n_files"] for g in groups) != 146:
        findings.append("A7_COUNT_DRIFT")

    return {
        "findings": findings,
        "rejudged_buckets": agg,
        "twin_counts": twin_counts,
        "dup_suffix_rows": dup_suffix,
        "n_main": len(got_main),
        "n_stray": len(got_stray),
    }


# ---------------------------------------------------------------------------
# B — 文件系统全量重哈希 vs 冻结清单
# ---------------------------------------------------------------------------
def review_fs_resha(inv):
    records = {r["rel_path"]: r for r in inv["records"]}
    seen = set()
    mismatch, modified, unreadable = [], [], []
    for dirpath, _d, filenames in os.walk(OCR_ROOT):
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            full = Path(dirpath) / fn
            rel = full.relative_to(OCR_ROOT).as_posix()
            seen.add(rel)
            rec = records.get(rel)
            try:
                sha = sha256_file(full)
            except OSError as e:
                unreadable.append(f"{rel}: {e!r}")
                continue
            if rec is None:
                modified.append(("NEW", rel))
                continue
            if rec["sha256"] != sha:
                modified.append(("SHA_CHANGED", rel))
            elif rec["mtime"] != full.stat().st_mtime:
                modified.append(("MTIME_CHANGED", rel))
    missing = sorted(set(records) - seen)
    return {
        "frozen_total": len(records),
        "seen_total": len(seen),
        "missing_from_fs": missing[:20],
        "n_missing": len(missing),
        "changes": modified[:40],
        "n_changes": len(modified),
        "unreadable": unreadable,
    }


# ---------------------------------------------------------------------------
# C — 跑步机日志级直接物证 + 审计交叉核对
# ---------------------------------------------------------------------------
LOG_LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[\d+/\d+\] (.+?)\.\.\.$")


def parse_ocr_log():
    """解析 ocr_batch_log.txt。

    日志行格式(batch_convert_pdf.main):"[ts] [i/total] {grade}/{subject}/{filename[:50]}..."
    —— 文件名被**截断至 50 字符**。故以完整 logged 路径串为键(不含尾部 "..."),
    供 review_treadmill 用 rel_dir + basename[:50] 精确构造期望串。
    """
    entries = {}
    if not OCR_LOG.is_file():
        return entries, "LOG_ABSENT"
    with io.open(OCR_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_LINE_RE.match(line.rstrip("\n"))
            if not m:
                continue
            ts_s, path = m.group(1), m.group(2)
            ts = time.mktime(time.strptime(ts_s, "%Y-%m-%d %H:%M:%S"))
            entries.setdefault(path, []).append(ts)
    for k in entries:
        entries[k].sort()
    return entries, None


def review_treadmill(coll, buck_audit_index_from_inv=None):
    log_entries, log_err = parse_ocr_log()
    findings = []
    per_group = []
    n_direct = n_entry_other = n_no_entry = n_out_of_window = 0
    for g in coll["d2_d3"]["groups"]:
        name = g["basename"]
        stem = os.path.splitext(name)[0]
        # 回流份 = mtime 序最后的成员
        ordered = g["mtime_order"]
        later_rel = ordered[-1] if ordered else None
        later = next((m for m in g["members"] if m["rel_path"] == later_rel), None)
        rec = {"basename": name, "later_rel": later_rel}
        if later is None or later["mtime"] is None:
            rec["log_evidence"] = "NO_MTIME"
            n_no_entry += 1
        else:
            rec["later_mtime"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(later["mtime"]))
            # 期望 logged 串:回流份落位目录 + 截断文件名(R65 首版误用全名
            # stem 匹配,长名漏配 —— 见 F-r65-2;此处按日志截断规则精确构造)
            rel = later["rel_path"]
            rel_dir = rel.rsplit("/", 1)[0] if "/" in rel else ""
            fname = rel.rsplit("/", 1)[-1]
            # 日志记录的是**源 PDF 文件名**(runner 的 original_filename),
            # 且截断 [:50] 施加于 PDF 名 —— 先换扩展名再截断。
            pdf_name = fname[:-2] + "pdf" if fname.lower().endswith(".md") else fname
            expected = (rel_dir + "/" if rel_dir else "") + pdf_name[:50]
            ts_list = log_entries.get(expected, [])
            near = [t for t in ts_list if abs(t - later["mtime"]) <= 6 * 3600]
            if near:
                rec["log_evidence"] = "DIRECT(±6h)"
                rec["log_ts"] = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)) for t in near]
                rec["expected_log_path"] = expected
                n_direct += 1
            elif ts_list:
                rec["log_evidence"] = "ENTRY_OTHER_TIME"
                rec["expected_log_path"] = expected
                n_entry_other += 1
            else:
                rec["log_evidence"] = "NO_ENTRY(log covers 09-06..09-10 only)"
                rec["expected_log_path"] = expected
                n_no_entry += 1
        # 审计 from/to 与成员路径交叉核对
        audit_moves = g.get("audit_moves", [])
        member_rels = {m["rel_path"] for m in g["members"]}
        ok_move = False
        for mv in audit_moves:
            frm = mv["from"].replace("\\", "/")
            to = mv["to"].replace("\\", "/")
            if any(frm.endswith(r) for r in member_rels) and any(to.endswith(r) for r in member_rels):
                ok_move = True
                break
        rec["audit_paths_match_members"] = ok_move
        if not ok_move:
            findings.append(f"C_AUDIT_PATH_MISMATCH:{name}")
        per_group.append(rec)
    return {
        "log_file": str(OCR_LOG),
        "log_parse_error": log_err,
        "log_stems_indexed": len(log_entries),
        "groups_direct_log_evidence": n_direct,
        "groups_entry_other_time": n_entry_other,
        "groups_no_entry": n_no_entry,
        "per_group": per_group,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# D — PDF 唯一性独立重算
# ---------------------------------------------------------------------------
def review_pdf_uniqueness(coll):
    index = {}
    total = 0
    for dirpath, _d, filenames in os.walk(PDF_ROOT):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                total += 1
                stem = SANITIZE_RE.sub("_", os.path.splitext(fn)[0])
                index.setdefault(stem, []).append(fn)
    dist = {}
    for g in coll["d2_d3"]["groups"]:
        stem = SANITIZE_RE.sub("_", os.path.splitext(g["basename"])[0])
        n = len(index.get(stem, []))
        dist[n] = dist.get(n, 0) + 1
    return {"pdf_total": total, "exact_count_distribution": dist}


# ---------------------------------------------------------------------------
# E — 提交武器可重现性
# ---------------------------------------------------------------------------
def review_reproducibility(inv):
    import tempfile
    tmp = DATA.parent / ".pytest_work" / ("r65_repro_" + os.urandom(4).hex())
    tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ,
               R64_DATA_DIR=str(tmp),
               R64_AUDIT=str(AUDIT_JSONL))
    try:
        r = subprocess.run(
            [sys.executable, str(BASE / "scripts" / "r64_data_inventory.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, cwd=str(BASE), timeout=1200)
        if r.returncode != 0:
            return {"verdict": "WEAPON_RUN_FAILED", "tail": (r.stderr or "")[-400:]}
        rerun = json.loads((tmp / "r64_corpus_inventory.json").read_text(encoding="utf-8"))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    committed = {rec["rel_path"]: rec for rec in inv["records"]}
    fresh = {rec["rel_path"]: rec for rec in rerun["records"]}
    changed = [rel for rel in committed
               if rel not in fresh or fresh[rel] != committed[rel]]
    new = sorted(set(fresh) - set(committed))
    return {
        "verdict": "REPRODUCIBLE" if not changed else "DIVERGED",
        "n_changed": len(changed),
        "changed_sample": changed[:10],
        "n_new_since_freeze": len(new),
        "new_sample": new[:10],
    }


# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    inv = json.loads((DATA / "r64_corpus_inventory.json").read_text(encoding="utf-8"))
    buck = json.loads((DATA / "r64_unknown_buckets.json").read_text(encoding="utf-8"))
    coll = json.loads((DATA / "r64_collision_fingerprint.json").read_text(encoding="utf-8"))

    a = review_cross_consistency(inv, buck, coll)
    b = review_fs_resha(inv)
    c = review_treadmill(coll)
    d = review_pdf_uniqueness(coll)
    e = review_reproducibility(inv)

    all_findings = a["findings"] + b["unreadable"] + c["findings"]
    if b["n_missing"]:
        all_findings.append(f"B_MISSING:{b['n_missing']}")
    if b["n_changes"]:
        all_findings.append(f"B_CHANGES:{b['n_changes']}")
    if e.get("verdict") != "REPRODUCIBLE":
        all_findings.append(f"E:{e.get('verdict')}")

    out = {
        "meta": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "weapon": "scripts/r65_r64_review.py",
            "elapsed_sec": round(time.time() - t0, 1),
        },
        "A_cross_consistency": a,
        "B_fs_resha": b,
        "C_treadmill_log_evidence": {k: v for k, v in c.items() if k != "per_group"},
        "C_per_group": c["per_group"],
        "D_pdf_uniqueness": d,
        "E_reproducibility": e,
        "findings": all_findings,
        "verdict": "PASS(无 finding)" if not all_findings else f"FINDINGS:{len(all_findings)}",
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps({k: out[k] for k in ("verdict", "findings")}, ensure_ascii=False))
    print("A:", json.dumps(a, ensure_ascii=False)[:400])
    print("B:", json.dumps({k: b[k] for k in ("frozen_total", "seen_total", "n_missing", "n_changes")}, ensure_ascii=False))
    print("C:", json.dumps({k: c[k] for k in ("groups_direct_log_evidence", "groups_entry_other_time", "groups_no_entry", "log_stems_indexed")}, ensure_ascii=False))
    print("D:", json.dumps(d, ensure_ascii=False))
    print("E:", json.dumps(e, ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
