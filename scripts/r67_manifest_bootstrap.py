# -*- coding: utf-8 -*-
"""r67_manifest_bootstrap.py — manifest 审计级/日志级引导(BUG-14-DATA D5-A bootstrap)

治理依据:governance/rule_registry.md §7 R-OHM-1 + R67 扩展(用户 2026-09-13 五项裁决)。
设计:reports/r67_manifest_bootstrap_design.md(§十 用户裁决冻结)。

证据来源(仅两种,其余永不入账):
  1. R63 reclassify 审计(data/reclassify_audit.jsonl,698 条 from→to):
     from 路径 == 某唯一 PDF 的 runner 期望输出路径(完整路径等值,禁 stem)
     且 to 在位 >100B → 该 PDF 历史上已成功 OCR(输出只可能由 OCR 产生)。
  2. OCR 批量日志(logs/ocr_batch_log.txt):
     runner 格式行 `[ts] [i/total] grade/subject/{filename[:50]}...` 后随
     `[OK] N pages` → 该 PDF 成功处理过(F-r65-2 教训:必须按截断规则构造期望串)。
     仅用于「首扫受害者候选」(期望输出落空 + 语料存在同名 md,重 OCR = 制造重复);
     无同名 md 者(输出真丢)不 seed——其首扫重跑是有价值的数据恢复,如实放行。

分桶(用户裁决 ③):
  A 类:日志可证(或审计可证)→ 写入 bootstrap 记录
  B 类:仅有弱证据(同名 md 存在)→ PENDING_REVIEW,只入报告,不入 manifest
  C 类:无任何证据 → 不入 manifest(= 正常存量,daemon 本职)

铁律(用户裁决 ④⑤ + R-OHM-1):
  - 默认 dry-run;--apply 显式落盘;报告先于写入供人工批准。
  - **禁止覆盖/修改任何已有 manifest 条目**:source_rel 已在册 → 跳过并计数。
  - 幂等:二次 apply 追加 0 条。
  - fail-closed:审计坏行 / 期望输出歧义 / to 缺失 / 既有清单损坏 → 显式处置,
    绝不静默降级。
  - pages 未知 = null + provenance(禁 -1 哨兵、禁假 0);
    processed_at: null(OCR 时刻不可知);written_at = 记录写入时刻(recorded_at 语义)。

用法:
  python scripts/r67_manifest_bootstrap.py            # dry-run(只写报告)
  python scripts/r67_manifest_bootstrap.py --apply    # 落盘(先 dry-run 审查!)
"""
import argparse
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "ocr_service"))
from output_manifest import (ManifestError, append_entry,  # noqa: E402
                             file_sha256, load_manifest,
                             normalize_rel, validate_entry)

BASE = _ROOT
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")
AUDIT_FILE = os.path.join(BASE, "data", "reclassify_audit.jsonl")
OCR_LOG_FILE = os.path.join(BASE, "logs", "ocr_batch_log.txt")
MANIFEST_FILE = os.path.join(BASE, "data", "ocr_output_manifest.jsonl")
REPORT_FILE = os.path.join(BASE, "data", "r67_bootstrap_report.json")

EXCLUDE_TOP_PREFIXES = ("reslice-", "resliced-")

LOG_NAME_RE = re.compile(
    r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[\d+/\d+\] (.*)\.\.\.$")
LOG_OK_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]   \[OK\] (\d+) pages$")


class BootstrapError(RuntimeError):
    """引导前置条件损坏(fail-closed:显式中止,禁部分静默)。"""


def sanitize_stem(name):
    return re.sub(r'[<>:"/\\|?*]', "_", os.path.splitext(name)[0])


def extract_grade_subject(filename):
    grade = "未分类"
    if re.search(r"高一|高1", filename):
        grade = "高一"
    elif re.search(r"高二|高2", filename):
        grade = "高二"
    elif re.search(r"高三|高3", filename):
        grade = "高三"
    subject = "未分类"
    for s in ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]:
        if s in filename:
            subject = s
            break
    return grade, subject


def enumerate_pdfs(pdf_root):
    """与 runner main() 相同的枚举与 output_dir 决策(路径正斜杠归一)。"""
    out = []
    for filename in sorted(os.listdir(pdf_root)):
        if filename.lower().endswith(".pdf"):
            grade, subject = extract_grade_subject(filename)
            out.append((os.path.join(pdf_root, filename), grade, subject, filename))
    for grade in ["高一", "高二", "高三"]:
        grade_path = os.path.join(pdf_root, grade)
        if not os.path.isdir(grade_path):
            continue
        for subject in sorted(os.listdir(grade_path)):
            subject_path = os.path.join(grade_path, subject)
            if not os.path.isdir(subject_path):
                continue
            for filename in sorted(os.listdir(subject_path)):
                if filename.lower().endswith(".pdf"):
                    out.append((os.path.join(subject_path, filename),
                                grade, subject, filename))
    return out


def parse_audit(audit_file):
    """审计 JSONL → [{from,to,...}];坏行/缺键 → BootstrapError(含行号)。"""
    if not os.path.exists(audit_file):
        raise BootstrapError(f"审计文件不存在: {audit_file}")
    records = []
    with open(audit_file, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError as e:
                raise BootstrapError(f"{audit_file}:{lineno}: 非法 JSON: {e}")
            if not isinstance(rec, dict) or not rec.get("from") or not rec.get("to"):
                raise BootstrapError(f"{audit_file}:{lineno}: 缺 from/to: {rec!r}")
            records.append({"from": rec["from"], "to": rec["to"], "line": lineno})
    return records


def build_log_index(log_file, fragments):
    """单遍扫描 OCR 日志,收集候选 fragment 的处理证据。

    返回 {fragment: {"ok_pages": 最近一次 [OK] 页数, "occurrences": 出现次数,
                     "ok_lines": [行号], "name_lines": [行号]}}
    仅记录 fragment ∈ fragments 的行;名行后 2 行内出现 [OK] 才算成功处理。
    """
    index = {fr: {"ok_pages": None, "occurrences": 0,
                  "ok_lines": [], "name_lines": []} for fr in fragments}
    if not os.path.exists(log_file):
        return index
    with open(log_file, encoding="utf-8", errors="strict") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        m = LOG_NAME_RE.match(line)
        if not m:
            continue
        frag = m.group(1)
        if frag not in index:
            continue
        rec = index[frag]
        rec["occurrences"] += 1
        rec["name_lines"].append(i + 1)
        for j in (i + 1, i + 2):
            if j < len(lines):
                mo = LOG_OK_RE.match(lines[j])
                if mo:
                    rec["ok_pages"] = int(mo.group(1))
                    rec["ok_lines"].append(j + 1)
                    break
    return index


def md_stem_index(output_root):
    """Ocr-markdown 全树 md stem → [相对路径](排除 reslice*/resliced* 试验目录)。"""
    idx = {}
    for dirpath, _dirs, files in os.walk(output_root):
        rel_dir = normalize_rel(os.path.relpath(dirpath, output_root))
        top = rel_dir.split("/")[0] if rel_dir != "." else ""
        if top.startswith(EXCLUDE_TOP_PREFIXES):
            continue
        for fn in files:
            if fn.lower().endswith(".md"):
                idx.setdefault(fn[:-3], []).append(
                    normalize_rel(os.path.join(rel_dir, fn) if rel_dir != "." else fn))
    return idx


def _make_entry(source_pdf, source_rel, output_rel, pages, provenance,
                written_at, extra=None):
    entry = {
        "source_rel": source_rel,
        "source_size": os.path.getsize(source_pdf),
        "source_sha256": file_sha256(source_pdf),
        "output_rel": output_rel,
        "written_at": written_at,
        "pages": pages,
        "provenance": provenance,
        "processed_at": None,  # OCR 时刻不可知(本轮未从日志提取时间戳),不用 written_at 冒充
    }
    if extra:
        entry.update(extra)
    validate_entry(entry)
    return entry


def plan(*, pdf_root, output_root, audit_file, log_file, manifest_file,
         written_at):
    """只读规划:计算 bootstrap 记录 + 分桶 + 排除清单。不写任何文件。"""
    existing = load_manifest(manifest_file)  # 损坏即 ManifestError(fail-closed)

    pdfs = enumerate_pdfs(pdf_root)
    expected = {}  # output_rel -> [pdf 记录]
    for path, grade, subject, filename in pdfs:
        rel = normalize_rel(os.path.relpath(path, pdf_root))
        out_rel = f"{grade}/{subject}/{sanitize_stem(filename)}.md"
        expected.setdefault(out_rel, []).append(
            {"pdf": path, "source_rel": rel, "out_rel": out_rel,
             "filename": filename, "grade": grade, "subject": subject,
             "fragment": f"{grade}/{subject}/{filename[:50]}"})

    # --- 证据源 1:审计(from == 唯一 PDF 期望输出 且 to 在位)
    entries, excluded, audit_sources = [], [], {}
    for rec in parse_audit(audit_file):
        from_rel = normalize_rel(os.path.relpath(rec["from"], output_root))
        owners = expected.get(from_rel, [])
        if len(owners) != 1:
            excluded.append({"reason": ("AUDIT_FROM_UNMATCHED" if not owners
                                        else "AUDIT_FROM_AMBIGUOUS"),
                             "audit_line": rec["line"], "from_rel": from_rel,
                             "owner_count": len(owners)})
            continue
        if not (os.path.exists(rec["to"]) and os.path.getsize(rec["to"]) > 100):
            excluded.append({"reason": "AUDIT_TO_MISSING", "audit_line": rec["line"],
                             "from_rel": from_rel})
            continue
        audit_sources[owners[0]["source_rel"]] = {
            "audit_line": rec["line"],
            "output_rel": normalize_rel(os.path.relpath(rec["to"], output_root)),
            "pdf": owners[0]}

    # --- 证据源 2:日志考古(仅面向首扫受害者候选)
    victims = []
    for out_rel, owners in expected.items():
        out_abs = os.path.join(output_root, *out_rel.split("/"))
        if os.path.exists(out_abs) and os.path.getsize(out_abs) > 100:
            continue  # EXISTS skip,无需引导
        for o in owners:
            victims.append(o)
    md_idx = md_stem_index(output_root)
    victims = [v for v in victims
               if md_idx.get(sanitize_stem(v["filename"]))]  # 同名 md 存在 = 受害者候选

    # 全量 fragment 统计与日志索引(歧义判定与页数富化覆盖所有 PDF,含审计源)
    frag_counts = {}
    for owners in expected.values():
        for o in owners:
            frag_counts[o["fragment"]] = frag_counts.get(o["fragment"], 0) + 1
    log_index = build_log_index(log_file, set(frag_counts))

    # 审计条目的日志富化:日志可证时补真实页数(审计证明处理事实,日志补页数事实)
    for a in audit_sources.values():
        frag = a["pdf"]["fragment"]
        li = log_index.get(frag, {})
        if li.get("ok_pages") is not None and frag_counts[frag] == 1:
            a["log_pages"] = li["ok_pages"]
            a["log_lines"] = li["ok_lines"]

    buckets = {"A_seeded": [], "B_pending_review": [], "C_not_seeded_note": []}
    for v in sorted(victims, key=lambda x: x["source_rel"]):
        src = v["source_rel"]
        if src in audit_sources:
            continue  # 审计条目稍后统一构造(证据更强)
        li = log_index.get(v["fragment"], {})
        ambiguous_frag = frag_counts[v["fragment"]] > 1
        if li.get("ok_pages") is not None and not ambiguous_frag:
            audit_sources[src] = {
                "audit_line": None,
                "output_rel": v["out_rel"],
                "pdf": v,
                "log_pages": li["ok_pages"],
                "log_lines": li["ok_lines"]}
        else:
            buckets["B_pending_review"].append({
                "source_rel": src,
                "reason": ("LOG_FRAGMENT_AMBIGUOUS" if ambiguous_frag
                           else ("LOG_NAME_ONLY_NO_OK" if li.get("name_lines")
                                 else "NO_LOG_EVIDENCE")),
                "same_stem_md": sorted(md_idx.get(sanitize_stem(v["filename"]), [])),
                "log_name_lines": li.get("name_lines", [])})

    # --- 统一构造条目(禁覆盖:已在册者跳过)
    skipped_present = []
    for src in sorted(audit_sources):
        if src in existing:
            skipped_present.append({"source_rel": src,
                                    "reason": "ALREADY_IN_MANIFEST"})
            continue
        a = audit_sources[src]
        v = a["pdf"]
        pages = a.get("log_pages")
        prov = ("r63-audit-bootstrap" if a["audit_line"] is not None
                else "ocr-log-archaeology")
        extra = {"processed_at": None}
        if a["audit_line"] is not None:
            extra["audit_line"] = a["audit_line"]
        if a.get("log_lines"):
            extra["log_ok_lines"] = a["log_lines"]
        entry = _make_entry(v["pdf"], src, a["output_rel"], pages, prov,
                            written_at, extra=extra)
        entries.append(entry)
        buckets["A_seeded"].append({
            "source_rel": src, "provenance": prov, "pages": pages,
            "audit_line": a["audit_line"], "log_ok_lines": a.get("log_lines", [])})

    return {"entries": entries, "buckets": buckets, "excluded": excluded,
            "skipped_already_present": skipped_present,
            "existing_count": len(existing),
            "victim_candidates": len(victims)}


def run(apply=False, *, pdf_root=PDF_ROOT, output_root=OUTPUT_ROOT,
        audit_file=AUDIT_FILE, log_file=OCR_LOG_FILE,
        manifest_file=MANIFEST_FILE, report_file=REPORT_FILE,
        written_at=None):
    if written_at is None:
        import time
        written_at = time.strftime("%Y-%m-%d %H:%M:%S")
    plan_out = plan(pdf_root=pdf_root, output_root=output_root,
                    audit_file=audit_file, log_file=log_file,
                    manifest_file=manifest_file, written_at=written_at)
    report = {
        "purpose": "R67 manifest bootstrap (dry-run unless apply)",
        "applied": bool(apply),
        "existing_count": plan_out["existing_count"],
        "victim_candidates": plan_out["victim_candidates"],
        "planned_entries": len(plan_out["entries"]),
        "skipped_already_present": plan_out["skipped_already_present"],
        "excluded": plan_out["excluded"],
        "buckets": plan_out["buckets"],
        "entries": plan_out["entries"],
    }
    if apply:
        appended = 0
        for entry in plan_out["entries"]:
            append_entry(manifest_file, entry)  # 先校验后写 + fsync
            appended += 1
        report["appended"] = appended
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rep = run(apply=args.apply)
    print(f"planned_entries={rep['planned_entries']} "
          f"(A={len(rep['buckets']['A_seeded'])} "
          f"B_pending={len(rep['buckets']['B_pending_review'])} "
          f"excluded={len(rep['excluded'])} "
          f"already_in_manifest={len(rep['skipped_already_present'])})")
    print(f"applied={rep['applied']} appended={rep.get('appended', 0)}")
    print(f"-> {REPORT_FILE}")


if __name__ == "__main__":
    main()
