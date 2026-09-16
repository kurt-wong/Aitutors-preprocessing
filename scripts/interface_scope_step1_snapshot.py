r"""Step 1 接口快照冻结(DEC-026 执行令;五步序 Step 1)。

冻结 v2 接口面(字段口径 `identity_version == 2` = 87 份)的接口快照:
  - 文件清单(manifest / 切片 md / source_file locator);
  - `source_content_sha256` = SHA256(source md 原始字节)(DEC-025 FC-1 定义);
  - R50 关联关系(是否 R50 基线成员 + R50 记录的 sha + 是否一致);
  - IR 关联(有无 IR 记录 / disposition / `ir.source_sha256` + 是否一致)。

血统(Dependency Map E2 配对再冻结):本快照 + `interface_scope_prebackfill`
audit 记录在 Step 2 回填前冻结;回填必致 R50 DRIFT(87/87 manifest 为 R50
成员),此后接口面的完整性基线角色由 pre/post 双快照承接。

fail-closed 纪律:
  - source_file 缺失/非文件 → 抛错(身份输入不可达,禁静默跳过);
  - manifest 已含任何 `*sha*`/`*hash*` 键 → 抛错(回填前 0/166 硬事实被破坏);
  - scope 数 != 87 → 抛错(接口面口径漂移,须先裁决再执行)。

确定性:输出无时间戳、键排序稳定,同输入集字节级可复现。
用法:python scripts/interface_scope_step1_snapshot.py
输出:data/interface_scope_snapshot_step1.json
     data/audit_snapshot_interface_scope_prebackfill.json
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_integrity as ai  # noqa: E402

V2_DIRS = ("Ocr-markdown/reslice-batch-C",
           "Ocr-markdown/reslice-pac-annotated",
           "Ocr-markdown/resliced-pilot")
SCOPE_N = 87
R50_BASELINE = "data/audit_snapshot_R50_input_baseline.json"
IR_ARTIFACT = "data/resolver_ref_r52/resolver_ir.json"
SNAPSHOT_OUT = "data/interface_scope_snapshot_step1.json"
AUDIT_ID = "interface_scope_prebackfill"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def enumerate_scope(root: Path = ROOT):
    """字段口径 v2 面:identity_version == 2(兼容字符串 "2")。"""
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
    mans = enumerate_scope(root)
    if len(mans) != SCOPE_N:
        raise RuntimeError(f"interface scope drift: expected {SCOPE_N} "
                           f"v2 manifests, found {len(mans)}")

    r50 = json.loads((root / R50_BASELINE).read_text(encoding="utf-8"))
    r50_files = r50["files"]
    ir_doc = json.loads((root / IR_ARTIFACT).read_text(encoding="utf-8"))
    ir_by_manifest = {}
    for rec in ir_doc["files"]:
        mf = (rec.get("ir") or {}).get("manifest_file")
        if not mf:
            # 拒收记录无 ir 对象;以切片 md 兄弟件路径推导
            mf = str(Path(rec["file"]).with_suffix(".manifest.json"))
        ir_by_manifest[str(Path(mf))] = {
            "disposition": rec["disposition"],
            "ir_source_sha256": (rec.get("ir") or {}).get("source_sha256"),
        }

    rows = []
    for m, j in mans:
        rel = ai.rel_key(m, root)
        bad = [k for k in j.keys()
               if "sha" in k.lower() or "hash" in k.lower()]
        if bad:
            raise RuntimeError(
                f"pre-backfill invariant broken (manifest already carries "
                f"sha/hash keys): {rel} keys={bad}")
        src = Path(j.get("source_file") or "")
        if not src.is_file():
            raise RuntimeError(f"source_file missing or not a file: "
                               f"{rel} -> {src!s}")
        sha = sha256_file(src)
        man_sha = sha256_file(m)
        man_r50 = r50_files.get(rel)
        src_r50 = r50_files.get(ai.rel_key(src, root))
        ir = ir_by_manifest.get(str(Path(m).resolve()))
        if ir is not None:
            ir = dict(ir)
            ir["sha256_match"] = (ir.get("ir_source_sha256") == sha) \
                if ir.get("ir_source_sha256") is not None else None
        rows.append({
            "manifest": rel,
            "source_file": str(src),
            "source_content_sha256": sha,
            "r50": {
                "manifest_member": man_r50 is not None,
                "manifest_recorded_sha256": man_r50,
                "manifest_sha256_match": (man_r50 == man_sha)
                if man_r50 else None,
                "source_member": src_r50 is not None,
                "source_recorded_sha256": src_r50,
                "source_sha256_match": (src_r50 == sha) if src_r50
                else None,
            },
            "ir": ir,
        })

    summary = {
        "n_rows": len(rows),
        "r50_manifest_members": sum(1 for r in rows
                                    if r["r50"]["manifest_member"]),
        "r50_manifest_sha_match": sum(1 for r in rows
                                      if r["r50"]["manifest_sha256_match"]),
        "r50_source_members": sum(1 for r in rows
                                  if r["r50"]["source_member"]),
        "r50_source_sha_match": sum(1 for r in rows
                                    if r["r50"]["source_sha256_match"]),
        "ir_records": sum(1 for r in rows if r["ir"] is not None),
        "ir_admitted": sum(1 for r in rows
                           if (r["ir"] or {}).get("disposition") == "ADMITTED"),
        "ir_admitted_sha_match": sum(
            1 for r in rows
            if (r["ir"] or {}).get("disposition") == "ADMITTED"
            and (r["ir"] or {}).get("sha256_match")),
        "ir_rejected_qc_fail": sum(
            1 for r in rows
            if (r["ir"] or {}).get("disposition") == "REJECTED_QC_FAIL"),
        "ir_absent": sum(1 for r in rows if r["ir"] is None),
    }
    snap = {
        "snapshot_id": "interface_scope_step1_prebackfill",
        "scope_rule": ("manifest identity_version == 2 under "
                       + " / ".join(V2_DIRS) + " (field criterion, n=87)"),
        "identity_field": "source_content_sha256",
        "identity_definition": "SHA256(original source bytes), 64 lowercase hex",
        "lineage": ("R50_input_baseline is member-superset (87/87); this "
                    "snapshot becomes the paired re-freeze baseline for the "
                    "interface face across Step 2 backfill (DEC-021 D4 / E2)"),
        "summary": summary,
        "rows": rows,
    }
    out = root / SNAPSHOT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="")

    # audit 快照:回填前冻结输入面(87 manifest + 87 source + IR + R50 基线)
    paths = [root / r["manifest"] for r in rows] + \
            [Path(r["source_file"]) for r in rows] + \
            [root / IR_ARTIFACT, root / R50_BASELINE, out]
    rec = ai.record(AUDIT_ID, paths, metrics={
        "n_interface_files": summary["n_rows"],
        "n_ir_admitted": summary["ir_admitted"],
        "n_ir_admitted_sha_match": summary["ir_admitted_sha_match"],
        "n_r50_manifest_members": summary["r50_manifest_members"],
    })
    ai.write_record(rec)
    print(json.dumps(summary, ensure_ascii=False))
    print(f"snapshot: {out}")
    print(f"audit: data/audit_snapshot_{AUDIT_ID}.json "
          f"corpus_sha256={rec['corpus_sha256']}")


if __name__ == "__main__":
    main()
