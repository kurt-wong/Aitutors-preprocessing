# -*- coding: utf-8 -*-
"""r67_apply_verify.py — R67.1 Gate A:manifest 落盘正确性独立验证

依据:用户 R67 apply 裁定 §三-Gate A(append_count / duplicate / entries_sha256 /
written_at / processed_at / provenance 六项)+ 证据链重验(PDF sha256/size 重算、
输出文件存在性与重哈希)。

独立性(G-AUDTB-1 精神):不 import bootstrap/gate,自读 preview、manifest、
审计文件与语料,全部证据现场重算。

输出 data/r67_apply_verify_report.json(确定性,不含 698 个明细 sha 逐条冗余,
以聚合计数 + 组合指纹呈现);全部通过才 exit 0。
用法:python scripts/r67_apply_verify.py
"""
import hashlib
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_ROOT = os.path.join(BASE, "maintainess", "PDF")
OUTPUT_ROOT = os.path.join(BASE, "Ocr-markdown")
MANIFEST_FILE = os.path.join(BASE, "data", "ocr_output_manifest.jsonl")
PREVIEW_FILE = os.path.join(BASE, "data", "r67_manifest_apply_preview.json")
AUDIT_FILE = os.path.join(BASE, "data", "reclassify_audit.jsonl")
REPORT_FILE = os.path.join(BASE, "data", "r67_apply_verify_report.json")


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_verify(*, manifest_file=MANIFEST_FILE, preview_file=PREVIEW_FILE,
               pdf_root=PDF_ROOT, output_root=OUTPUT_ROOT,
               audit_file=AUDIT_FILE, report_file=REPORT_FILE):
    with open(preview_file, encoding="utf-8") as f:
        preview = json.load(f)

    entries = []
    with open(manifest_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    checks = {}

    # 1) append_count:manifest 现存条目数 == preview 冻结数
    checks["append_count"] = (len(entries) == preview["append_count"],
                              len(entries), preview["append_count"])

    # 2) duplicate:source_rel / output_rel 均不得重复
    dup_src = len(entries) - len({e["source_rel"] for e in entries})
    dup_out = len(entries) - len({e["output_rel"] for e in entries})
    checks["duplicate_zero"] = (dup_src == 0 and dup_out == 0, dup_src, dup_out)

    # 3) entries_sha256:manifest 全体条目 canonical 指纹 == preview
    blob = json.dumps(entries, ensure_ascii=False, sort_keys=True)
    got_sha = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    checks["entries_sha256"] = (got_sha == preview["entries_sha256"],
                                got_sha, preview["entries_sha256"])

    # 4) written_at:唯一值 == preview 冻结值(bootstrap 引入时间,非 OCR 时间)
    wts = {e["written_at"] for e in entries}
    checks["written_at_frozen"] = (wts == {preview["written_at"]},
                                   sorted(wts), preview["written_at"])

    # 5) processed_at:全部 null(OCR 真实时间未知,禁止伪造)
    bad_pa = [e["source_rel"] for e in entries if e["processed_at"] is not None]
    checks["processed_at_all_null"] = (not bad_pa, len(bad_pa))

    # 6) provenance:全部 r63-audit-bootstrap
    bad_pv = sorted({e["provenance"] for e in entries} - {"r63-audit-bootstrap"})
    checks["provenance_uniform"] = (not bad_pv, bad_pv)

    # 7) pages:int(≥1)或 null-with-provenance;bootstrap 批次应全为 int
    bad_pages = [e["source_rel"] for e in entries
                 if not (isinstance(e["pages"], int) and e["pages"] >= 1)]
    checks["pages_int"] = (not bad_pages, len(bad_pages))

    # 8) PDF 重哈希:source_sha256/source_size 与磁盘事实一致
    pdf_bad = []
    for e in entries:
        p = os.path.join(pdf_root, e["source_rel"])
        if not os.path.exists(p):
            pdf_bad.append({"source_rel": e["source_rel"], "kind": "PDF_MISSING"})
            continue
        size = os.path.getsize(p)
        if size != e["source_size"] or _sha_file(p) != e["source_sha256"]:
            pdf_bad.append({"source_rel": e["source_rel"], "kind": "PDF_DRIFT"})
    checks["pdf_rehash"] = (not pdf_bad, len(pdf_bad))

    # 9) 输出重哈希:698 个 output 存在且 >100B;组合指纹(排序对)留证
    out_bad = []
    pairs = []
    for e in entries:
        p = os.path.join(output_root, e["output_rel"])
        if not os.path.exists(p):
            out_bad.append({"output_rel": e["output_rel"], "kind": "OUT_MISSING"})
            continue
        size = os.path.getsize(p)
        if size <= 100:
            out_bad.append({"output_rel": e["output_rel"], "kind": "OUT_TOO_SMALL",
                            "size": size})
            continue
        pairs.append((e["output_rel"], _sha_file(p)))
    checks["output_rehash"] = (not out_bad, len(out_bad))
    combo = hashlib.sha256(
        json.dumps(sorted(pairs), ensure_ascii=False).encode("utf-8")).hexdigest()

    # 10) 审计源文件本身未在 apply 前后被改(698 行仍在)
    with open(audit_file, encoding="utf-8") as f:
        audit_rows = sum(1 for line in f if line.strip())
    checks["audit_rows_intact"] = (audit_rows == preview["append_count"],
                                   audit_rows, preview["append_count"])

    consistent = all(ok for ok, *_ in checks.values())
    report = {
        "purpose": "R67.1 Gate A: manifest write correctness (independent)",
        "consistent": consistent,
        "manifest_sha256": _sha_file(manifest_file),
        "outputs_combo_sha256": combo,
        "checks": {k: {"ok": ok, "detail": list(rest)}
                   for k, (ok, *rest) in checks.items()},
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report


def main():
    rep = run_verify()
    for k, v in rep["checks"].items():
        print(f"{'PASS' if v['ok'] else 'FAIL'}  {k}  {v['detail']}")
    print(f"manifest_sha256={rep['manifest_sha256']}")
    print(f"outputs_combo_sha256={rep['outputs_combo_sha256']}")
    print(f"consistent={rep['consistent']}")
    print(f"-> {REPORT_FILE}")
    sys.exit(0 if rep["consistent"] else 1)


if __name__ == "__main__":
    main()
