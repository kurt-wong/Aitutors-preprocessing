r"""Contract v0.2 Freeze Evidence 最终一致性检查(Owner 冻结收口令 Task 2)。

只读复核:不信任何先前报告的结论,全部判定从当前磁盘字节重新推导,
并与 Step 1 快照 / Step 2 报告 / R50 基线 / pre+post audit 快照交叉对账。

检查项(fail-closed,任何一项不通过即整体 BLOCKED,不做修复):
  C1  接口面 87(字段口径 identity_version == 2,独立重新枚举);
  C2  87/87 manifest 携 `source_content_sha256`(且该面内无其它 *sha*/*hash* 键);
  C3  87/87 值 == SHA256(当前 source bytes),64 位小写 hex;
  C4  87/87 source bytes == Step 1 快照记录值 == R50 基线记录值(零漂移);
  C5  IR 对账:ADMITTED 71/71 且 ir.source_sha256 == manifest.source_content_sha256;
  C6  16/16 Semantic Pending(REJECTED_QC_FAIL):身份自足(字节可达 + sha 一致);
  C7  R50 血统:87 manifest + 87 source 双成员;R50 DRIFT 恰为 87 manifest、
      missing 0;post-backfill audit 快照 verify ok;pre audit 漂移集 ⊆ scope;
  C8  仅追加一键再证:剥去新键重序列化 sha == R50 基线记录 manifest sha 87/87;
  C9  path 非身份:locator(source_file)与 Step 1 快照一致 87/87;
      身份唯一性只按 hash 判定(重复 hash 单独列出,不参与通过判据)。

用法:python scripts/freeze_evidence_final_check.py
输出:data/freeze_evidence_final_check.json
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_integrity as ai  # noqa: E402

FIELD = "source_content_sha256"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCOPE_N, ADMITTED_N, PENDING_N = 87, 71, 16
V2_DIRS = ("Ocr-markdown/reslice-batch-C",
           "Ocr-markdown/reslice-pac-annotated",
           "Ocr-markdown/resliced-pilot")
SNAPSHOT_IN = "data/interface_scope_snapshot_step1.json"
STEP2_REPORT = "data/interface_scope_step2_backfill_report.json"
IR_ARTIFACT = "data/resolver_ref_r52/resolver_ir.json"
R50_BASELINE = "data/audit_snapshot_R50_input_baseline.json"
OUT = "data/freeze_evidence_final_check.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def enumerate_scope(root: Path):
    mans = []
    for d in V2_DIRS:
        for m in sorted((root / d).rglob("*.manifest.json")):
            j = json.loads(m.read_text(encoding="utf-8"))
            if j.get("identity_version") in (2, "2"):
                mans.append((m, j))
    mans.sort(key=lambda t: ai.rel_key(t[0], root))
    return mans


def main():
    root = ROOT
    checks = {}

    def add(cid, desc, ok, evidence):
        checks[cid] = {"id": cid, "desc": desc,
                       "status": "PASS" if ok else "FAIL",
                       "evidence": evidence}
        print(f"{cid}: {'PASS' if ok else 'FAIL'} — {desc}")

    snap = json.loads((root / SNAPSHOT_IN).read_text(encoding="utf-8"))
    snap_by_manifest = {r["manifest"]: r for r in snap["rows"]}
    step2 = json.loads((root / STEP2_REPORT).read_text(encoding="utf-8"))
    r50 = ai.load_record("R50_input_baseline")
    r50_files = r50["files"]

    # IR 索引(manifest 路径 -> 讲座记录)
    ir_doc = json.loads((root / IR_ARTIFACT).read_text(encoding="utf-8"))
    ir_by_manifest = {}
    for rec in ir_doc["files"]:
        mf = (rec.get("ir") or {}).get("manifest_file")
        if not mf:
            mf = str(Path(rec["file"]).with_suffix(".manifest.json"))
        ir_by_manifest[str(Path(mf))] = {
            "disposition": rec["disposition"],
            "ir_source_sha256": (rec.get("ir") or {}).get("source_sha256"),
        }

    # C1 独立重新枚举接口面
    mans = enumerate_scope(root)
    add("C1", f"interface scope == {SCOPE_N} (identity_version==2)",
        len(mans) == SCOPE_N, {"n_found": len(mans),
                               "dirs": list(V2_DIRS)})

    rows, field_ok, bytes_ok, snap_ok, r50_src_ok, locator_ok = \
        [], 0, 0, 0, 0, 0
    stripped_ok, hex_ok = 0, 0
    for m, j in mans:
        rel = ai.rel_key(m, root)
        srow = snap_by_manifest.get(rel)
        val = j.get(FIELD)
        src = Path(j.get("source_file") or "")
        cur_sha = sha256_bytes(src.read_bytes()) if src.is_file() else None
        # C2:唯一身份键在位
        sha_keys = [k for k in j if "sha" in k.lower() or "hash" in k.lower()]
        field_ok += (sha_keys == [FIELD])
        # C3:值 == 当前字节 sha,格式 64 小写 hex
        hex_ok += bool(val) and bool(HEX64.match(val))
        bytes_ok += (val is not None and val == cur_sha)
        # C4:字节自 Step 1 起零漂移,且 == R50 记录
        if srow is not None:
            snap_ok += (cur_sha == srow["source_content_sha256"])
            locator_ok += (str(src) == srow["source_file"])
        r50_src_ok += (r50_files.get(ai.rel_key(src, root)) == cur_sha)
        # C8:剥键重序列化 == R50 基线记录的回填前 manifest sha
        stripped = {k: v for k, v in j.items() if k != FIELD}
        s_sha = sha256_bytes(
            json.dumps(stripped, ensure_ascii=False, indent=1)
            .encode("utf-8"))
        stripped_ok += (r50_files.get(rel) == s_sha)
        # C5/C6:IR 对账
        ir = ir_by_manifest.get(str(Path(m).resolve()))
        rows.append({
            "manifest": rel,
            "source_content_sha256": val,
            "source_file": str(src),
            "ir_disposition": (ir or {}).get("disposition"),
            "ir_sha_match": ((ir or {}).get("ir_source_sha256") == val)
            if ir else None,
        })

    add("C2", f"{SCOPE_N}/{SCOPE_N} manifest carry {FIELD} as sole sha/hash key",
        field_ok == SCOPE_N, {"n_ok": field_ok})
    add("C3", f"{SCOPE_N}/{SCOPE_N} value == SHA256(current source bytes), "
              "64 lowercase hex",
        bytes_ok == SCOPE_N == hex_ok,
        {"n_bytes_match": bytes_ok, "n_hex64_format": hex_ok})
    add("C4", f"{SCOPE_N}/{SCOPE_N} source bytes unchanged since Step 1 "
              "snapshot and == R50 recorded",
        snap_ok == SCOPE_N and r50_src_ok == SCOPE_N,
        {"n_match_step1_snapshot": snap_ok, "n_match_r50": r50_src_ok})

    adm = [r for r in rows if r["ir_disposition"] == "ADMITTED"]
    adm_match = [r for r in adm if r["ir_sha_match"]]
    add("C5", f"IR ADMITTED {ADMITTED_N}/{ADMITTED_N} "
              "ir.source_sha256 == manifest.source_content_sha256",
        len(adm) == ADMITTED_N and len(adm_match) == ADMITTED_N,
        {"n_admitted": len(adm), "n_sha_match": len(adm_match)})

    pending = [r for r in rows if r["ir_disposition"] == "REJECTED_QC_FAIL"]
    pending_self = [r for r in pending if HEX64.match(r["source_content_sha256"] or "")]
    add("C6", f"Semantic Pending {PENDING_N}/{PENDING_N} "
              "(REJECTED_QC_FAIL, identity self-sufficient)",
        len(pending) == PENDING_N and len(pending_self) == PENDING_N,
        {"n_pending": len(pending),
         "n_identity_available": len(pending_self),
         "manifests": sorted(r["manifest"] for r in pending)})

    # C7 R50 血统 + audit 快照对账
    scope_set = {r["manifest"] for r in rows}
    man_members = sum(1 for rel in scope_set if rel in r50_files)
    src_members = sum(1 for r in rows
                      if ai.rel_key(Path(r["source_file"]), root) in r50_files)
    r50_res = ai.verify(r50)
    drift_is_exactly_scope = (sorted(r50_res["drift"]) == sorted(scope_set)
                              and not r50_res["missing"])
    post_rec = ai.load_record("interface_scope_postbackfill")
    post_res = ai.verify(post_rec)
    pre_rec = ai.load_record("interface_scope_prebackfill")
    pre_res = ai.verify(pre_rec)
    pre_drift_subset = (not pre_res["missing"]
                        and set(pre_res["drift"]) <= scope_set)
    # pre/post corpus 与 Step 2 报告记录一致
    corpus_match = (pre_rec["corpus_sha256"] ==
                    step2["summary"]["pre_audit_corpus_sha256"]
                    and post_rec["corpus_sha256"] ==
                    step2["summary"]["post_audit_corpus_sha256"])
    add("C7", "R50 lineage: 87+87 members; DRIFT == exactly 87 manifests, "
              "missing 0; post-backfill audit verify ok; pre drift subset",
        man_members == SCOPE_N and src_members == SCOPE_N
        and drift_is_exactly_scope and post_res["ok"]
        and pre_drift_subset and corpus_match,
        {"r50_manifest_members": man_members,
         "r50_source_members": src_members,
         "r50_drift_n": len(r50_res["drift"]),
         "r50_missing_n": len(r50_res["missing"]),
         "post_audit_ok": post_res["ok"],
         "post_corpus_sha256": post_rec["corpus_sha256"],
         "pre_corpus_sha256": pre_rec["corpus_sha256"],
         "pre_drift_subset_of_scope": pre_drift_subset,
         "corpus_match_step2_report": corpus_match})

    add("C8", f"stripped-key re-serialization == R50 baseline manifest sha "
              f"{SCOPE_N}/{SCOPE_N} (only the one key added)",
        stripped_ok == SCOPE_N, {"n_match": stripped_ok})

    add("C9", f"path non-identity: locator unchanged vs Step 1 snapshot "
              f"{SCOPE_N}/{SCOPE_N}; identity judged by content hash only",
        locator_ok == SCOPE_N,
        {"n_locator_unchanged": locator_ok,
         "n_unique_identities": len({r["source_content_sha256"]
                                     for r in rows}),
         "duplicate_identities": sorted(
             h for h in {r["source_content_sha256"] for r in rows}
             if sum(1 for r in rows
                    if r["source_content_sha256"] == h) > 1),
         "note": ("identity = SHA256(source bytes); source_file is a "
                  "locator only and takes no part in identity/uniqueness/"
                  "version/hash judgement")})

    overall = all(c["status"] == "PASS" for c in checks.values())
    report = {
        "report_id": "contract_v02_freeze_evidence_final_check",
        "identity_field": FIELD,
        "identity_definition": ("SHA256(original source bytes), "
                                "64 lowercase hex; path is locator only"),
        "checks": checks,
        "overall": "VERIFIED" if overall else "BLOCKED",
        "rows": rows,
    }
    (root / OUT).write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")
    print(f"overall: {report['overall']}")
    print(f"report: {root / OUT}")
    if not overall:
        sys.exit(1)


if __name__ == "__main__":
    main()
