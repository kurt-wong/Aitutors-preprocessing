# -*- coding: utf-8 -*-
"""r67_apply_gate.py — R67 apply 前置闸门第二道:bootstrap 输出↔审计源双向一致性复核

依据:用户 R67 裁决 §四-A(apply 前必须 698/698 双向逐项复核)。
对象:bootstrap 规划(plan)产出的条目;期望值由本武器**独立重推**——
独立实现枚举/净化/年级科目/路径归一/哈希/日志解析(不复用 bootstrap 的推导,
G-AUDTB-1 精神:审计工具不复用被审对象的推导逻辑)。

四字段逐项:
  PDF path   : 条目 source_rel 的 runner 期望输出(独立重算)== 审计 from_rel
  output path: 条目 output_rel == 独立重算的 审计 to 相对 OUTPUT_ROOT
  sha256     : 条目 source_sha256/source_size == 独立 hashlib 重算
  pages      : 条目 pages == 独立日志重推(无唯一 OK 证据时必须为 null)

双向:
  forward(审计→条目):每条审计行必须恰有 1 条 provenance=r63-audit-bootstrap 条目
  backward(条目→审计):每条审计条目必须指向合法审计行且 to 一致;
    provenance=ocr-log-archaeology 条目无审计行,单独核日志证据。

输出 data/r67_apply_gate_report.json(确定性);一致才 exit 0。
用法:python scripts/r67_apply_gate.py
"""
import hashlib
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
import r67_manifest_bootstrap as BOOT  # noqa: E402  被审对象(仅取 plan 输出)

BASE = _ROOT
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")
AUDIT_FILE = os.path.join(BASE, "data", "reclassify_audit.jsonl")
OCR_LOG_FILE = os.path.join(BASE, "logs", "ocr_batch_log.txt")
MANIFEST_FILE = os.path.join(BASE, "data", "ocr_output_manifest.jsonl")
REPORT_FILE = os.path.join(BASE, "data", "r67_apply_gate_report.json")

_SUBJECTS = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
_BAD = re.compile(r'[<>:"/\\|?*]')


def _norm(p):
    return str(p).replace("\\", "/")


def _gate_sanitize(fn):
    return _BAD.sub("_", os.path.splitext(fn)[0])


def _gate_egs(fn):
    g = "未分类"
    if re.search(r"高一|高1", fn):
        g = "高一"
    elif re.search(r"高二|高2", fn):
        g = "高二"
    elif re.search(r"高三|高3", fn):
        g = "高三"
    s = next((x for x in _SUBJECTS if x in fn), "未分类")
    return g, s


def gate_expected_outputs(pdf_root):
    """独立重推:source_rel → runner 期望输出 rel(与 bootstrap 各自实现,互为对照)。"""
    out = {}
    for dirpath, _dirs, files in os.walk(pdf_root):
        rel_dir = os.path.relpath(dirpath, pdf_root)
        for fn in files:
            if not fn.lower().endswith(".pdf"):
                continue
            if rel_dir == ".":
                g, s = _gate_egs(fn)
            else:
                parts = rel_dir.split(os.sep)
                g, s = parts[0], (parts[1] if len(parts) > 1 else "未分类")
            src = _norm(os.path.relpath(os.path.join(dirpath, fn), pdf_root))
            out[src] = {"out_rel": f"{g}/{s}/{_gate_sanitize(fn)}.md",
                        "fragment": f"{g}/{s}/{fn[:50]}", "pdf": os.path.join(dirpath, fn)}
    return out


def gate_log_pages(log_file, fragments, candidate_counts):
    """独立日志重推:fragment → 最近一次 [OK] 页数。

    歧义判定 = 候选侧两个以上 PDF 共享同一 fragment(与 bootstrap 同语义、独立实现);
    日志行多次出现是跑步机双次处理的正常证据,不构成归属歧义(取最近一次 [OK])。
    """
    name_re = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[\d+/\d+\] (.*)\.\.\.$")
    ok_re = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]   \[OK\] (\d+) pages$")
    wanted = set(fragments)
    pages = {}
    if not os.path.exists(log_file):
        return pages
    lines = open(log_file, encoding="utf-8", errors="strict").read().splitlines()
    for i, line in enumerate(lines):
        m = name_re.match(line)
        if not m or m.group(1) not in wanted:
            continue
        frag = m.group(1)
        if candidate_counts.get(frag, 0) > 1:
            pages.pop(frag, None)  # 候选侧歧义 → 不可归属
            continue
        for j in (i + 1, i + 2):
            if j < len(lines):
                mo = ok_re.match(lines[j])
                if mo:
                    pages[frag] = int(mo.group(1))  # 最近一次 OK 覆盖
                    break
    return pages


def run_gate(*, pdf_root=PDF_ROOT, output_root=OUTPUT_ROOT, audit_file=AUDIT_FILE,
             log_file=OCR_LOG_FILE, manifest_file=MANIFEST_FILE,
             report_file=REPORT_FILE, written_at="gate-probe"):
    expected = gate_expected_outputs(pdf_root)
    audit_rows = []
    with open(audit_file, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if line.strip():
                audit_rows.append((lineno, json.loads(line)))
    plan_out = BOOT.plan(pdf_root=pdf_root, output_root=output_root,
                         audit_file=audit_file, log_file=log_file,
                         manifest_file=manifest_file, written_at=written_at)
    entries = plan_out["entries"]
    audit_entries = [e for e in entries if e["provenance"] == "r63-audit-bootstrap"]
    log_entries = [e for e in entries if e["provenance"] == "ocr-log-archaeology"]

    frags = {v["fragment"] for v in expected.values()}
    candidate_counts = {}
    for v in expected.values():
        candidate_counts[v["fragment"]] = candidate_counts.get(v["fragment"], 0) + 1
    log_pages = gate_log_pages(log_file, frags, candidate_counts)

    mismatches = []
    by_line = {}
    for e in audit_entries:
        by_line.setdefault(e.get("audit_line"), []).append(e)

    # forward:审计 → 条目(逐行恰一条)
    forward_missing, forward_dup = [], []
    for lineno, row in audit_rows:
        got = by_line.get(lineno, [])
        if not got:
            forward_missing.append(lineno)
        elif len(got) > 1:
            forward_dup.append(lineno)

    # backward + 四字段逐项
    valid_lines = {ln for ln, _ in audit_rows}
    for e in audit_entries:
        ln = e.get("audit_line")
        if ln not in valid_lines:
            mismatches.append({"kind": "BACKWARD_ORPHAN", "source_rel": e["source_rel"]})
            continue
        row = dict(audit_rows)[ln]
        exp = expected.get(e["source_rel"])
        if exp is None:
            mismatches.append({"kind": "PDF_PATH_UNKNOWN", "source_rel": e["source_rel"],
                               "audit_line": ln})
            continue
        from_rel = _norm(os.path.relpath(row["from"], output_root))
        to_rel = _norm(os.path.relpath(row["to"], output_root))
        if exp["out_rel"] != from_rel:
            mismatches.append({"kind": "PDF_PATH", "audit_line": ln,
                               "entry_source": e["source_rel"],
                               "entry_expected_out": exp["out_rel"], "audit_from": from_rel})
        if e["output_rel"] != to_rel:
            mismatches.append({"kind": "OUTPUT_PATH", "audit_line": ln,
                               "entry_output_rel": e["output_rel"], "audit_to": to_rel})
        blob = open(exp["pdf"], "rb").read()
        if (e["source_sha256"] != hashlib.sha256(blob).hexdigest()
                or e["source_size"] != len(blob)):
            mismatches.append({"kind": "SHA256", "audit_line": ln,
                               "source_rel": e["source_rel"]})
        derived = log_pages.get(exp["fragment"])
        if e["pages"] != derived:
            mismatches.append({"kind": "PAGES", "audit_line": ln,
                               "entry_pages": e["pages"], "derived_pages": derived})

    # log-archaeology 条目:独立核日志页数(无审计行,单列)
    for e in log_entries:
        exp = expected.get(e["source_rel"])
        derived = log_pages.get(exp["fragment"]) if exp else None
        if exp is None or e["pages"] != derived or derived is None:
            mismatches.append({"kind": "LOG_ENTRY_UNVERIFIED",
                               "source_rel": e["source_rel"]})

    report = {
        "purpose": "R67 apply gate: bidirectional consistency (independent re-derivation)",
        "audit_rows": len(audit_rows),
        "entries_total": len(entries),
        "audit_entries": len(audit_entries),
        "log_entries": len(log_entries),
        "forward_missing": forward_missing,
        "forward_dup": forward_dup,
        "backward_mismatches": mismatches,
        "consistent": (not forward_missing and not forward_dup and not mismatches
                       and len(audit_rows) == len(audit_entries)),
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report


def main():
    rep = run_gate()
    print(f"audit_rows={rep['audit_rows']} audit_entries={rep['audit_entries']} "
          f"log_entries={rep['log_entries']}")
    print(f"forward_missing={len(rep['forward_missing'])} "
          f"forward_dup={len(rep['forward_dup'])} "
          f"mismatches={len(rep['backward_mismatches'])}")
    print(f"consistent={rep['consistent']}")
    print(f"-> {REPORT_FILE}")
    sys.exit(0 if rep["consistent"] else 1)


if __name__ == "__main__":
    main()
