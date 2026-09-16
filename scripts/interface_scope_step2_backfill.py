r"""Step 2 Manifest 字段补齐(DEC-026 执行令;五步序 Step 2)。

对 Step 1 冻结的 v2 接口面(87 份)逐份回填:
    source_content_sha256 = SHA256(source md 原始字节)(DEC-025 FC-1)

纪律(fail-closed,全程可重入):
  - 范围只读 Step 1 快照,不重新发明口径;scope 数 != 87 → 抛错;
  - manifest 已携 `source_content_sha256`:
      值一致 → 视为已回填(幂等通过);值不一致 → 抛错(禁覆盖);
  - 写回仅追加一个键(键序保持,json.dumps ensure_ascii=False indent=1
    无尾换行,与在库格式字节级同风格);原子替换(temp + os.replace);
  - 逐份回读验证:新 JSON == 原 JSON + {source_content_sha256: sha},
    其余键零改动;
  - 语义零触碰:只加身份键,不动 units/sections/任何既有键(禁改 IR 语义
    内容 / 原始文件 / Question 数据);
  - source 字节不变断言:回填后 87 份 source md sha == Step 1 记录值,
    任何漂移即抛错。

验证(报告落 data/interface_scope_step2_backfill_report.json):
  - 71 份 ADMITTED:manifest.source_content_sha256 == ir.source_sha256;
  - 16 份 Semantic Pending(QC_FAIL):身份自足,无 IR 可比;
  - R50 DRIFT 对账:回填后 R50 基线 drift 集合应恰为 87 份 manifest
    (E2 已预期,配对基线 = pre/post 双快照);
  - 冻结 post-backfill audit 快照(interface_scope_postbackfill)。

用法:python scripts/interface_scope_step2_backfill.py
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_integrity as ai  # noqa: E402

SCOPE_N = 87
SNAPSHOT_IN = "data/interface_scope_snapshot_step1.json"
PRE_AUDIT_ID = "interface_scope_prebackfill"
POST_AUDIT_ID = "interface_scope_postbackfill"
REPORT_OUT = "data/interface_scope_step2_backfill_report.json"
FIELD = "source_content_sha256"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def atomic_write(p: Path, text: str):
    tmp = p.with_suffix(p.suffix + ".step2tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, p)


def backfill_one(man_path: Path, expected_sha: str):
    """单份回填。返回 (status, before_keys, after_keys)。"""
    raw = man_path.read_text(encoding="utf-8")
    j = json.loads(raw)
    if FIELD in j:
        if j[FIELD] == expected_sha:
            return "already_backfilled", list(j.keys()), list(j.keys())
        raise RuntimeError(
            f"{FIELD} already present with different value on "
            f"{man_path}: {j[FIELD]} != {expected_sha} (refuse to overwrite)")
    new_j = dict(j)
    new_j[FIELD] = expected_sha
    atomic_write(man_path,
                 json.dumps(new_j, ensure_ascii=False, indent=1))
    # 回读验证:内容 = 原 JSON + 新键;键序 = 原键序 + 新键在尾
    rt = json.loads(man_path.read_text(encoding="utf-8"))
    if rt != new_j or list(rt.keys()) != list(j.keys()) + [FIELD]:
        raise RuntimeError(f"round-trip verification failed: {man_path}")
    return "backfilled", list(j.keys()), list(rt.keys())


def main():
    root = ROOT
    snap = json.loads((root / SNAPSHOT_IN).read_text(encoding="utf-8"))
    rows = snap["rows"]
    if len(rows) != SCOPE_N:
        raise RuntimeError(f"scope drift: Step 1 snapshot has {len(rows)} "
                           f"rows, expected {SCOPE_N}")

    # Step 1 audit 快照在回填前应零漂移;重入容忍:若漂移集恰为 87 份
    # manifest 且全部已正确携键(幂等重跑场景),放行并继续验证链。
    pre_rec = ai.load_record(PRE_AUDIT_ID)
    pre_res = ai.verify(pre_rec)
    if not pre_res["ok"]:
        drifted = set(pre_res["drift"])
        scope_set = {r["manifest"] for r in rows}
        if pre_res["missing"] or not drifted <= scope_set:
            raise RuntimeError(f"pre-backfill audit drift: {pre_res}")

    results, n_done, n_idem = [], 0, 0
    for r in rows:
        man = root / r["manifest"]
        sha = r["source_content_sha256"]
        # source 字节自 Step 1 冻结起必须未变(内容 hash 决定身份)
        cur = sha256_file(Path(r["source_file"]))
        if cur != sha:
            raise RuntimeError(
                f"source bytes drifted since Step 1 snapshot: "
                f"{r['source_file']} {cur} != {sha}")
        status, before_keys, after_keys = backfill_one(man, sha)
        n_done += status == "backfilled"
        n_idem += status == "already_backfilled"
        results.append({
            "manifest": r["manifest"],
            "status": status,
            "source_content_sha256": sha,
            "ir_disposition": (r["ir"] or {}).get("disposition"),
            "ir_sha256_match": (r["ir"] or {}).get("sha256_match"),
            "n_keys_before": len(before_keys),
            "n_keys_after": len(after_keys),
            "key_appended": after_keys[-1] if after_keys != before_keys
                            else None,
        })

    # 交叉验证 1:71 份 ADMITTED —— manifest hash == IR hash(有 IR 者)
    adm = [x for x in results if x["ir_disposition"] == "ADMITTED"]
    adm_match = [x for x in adm if x["ir_sha256_match"]]
    if len(adm) != 71 or len(adm_match) != 71:
        raise RuntimeError(
            f"IR cross-check failed: ADMITTED={len(adm)} "
            f"sha_match={len(adm_match)} (expected 71/71)")
    # 逐份再验一次回填后的磁盘值(不信中间态)
    for x in adm:
        j = json.loads((root / x["manifest"]).read_text(encoding="utf-8"))
        if j[FIELD] != x["source_content_sha256"]:
            raise RuntimeError(f"post-write field mismatch: {x['manifest']}")

    pending = [x for x in results
               if x["ir_disposition"] == "REJECTED_QC_FAIL"]
    absent = [x for x in results if x["ir_disposition"] is None]

    # 交叉验证 2:R50 DRIFT 对账(E2 预期:恰 87 份 manifest 漂移)
    r50 = ai.load_record("R50_input_baseline")
    r50_res = ai.verify(r50)
    expected_drift = sorted(r["manifest"] for r in rows)
    if sorted(r50_res["drift"]) != expected_drift:
        raise RuntimeError(
            f"R50 drift set mismatch: got {len(r50_res['drift'])} "
            f"entries, expected the 87 backfilled manifests")
    if r50_res["missing"]:
        raise RuntimeError(f"R50 missing files: {r50_res['missing']}")

    # post-backfill 冻结:输入面与 pre 快照同集(manifest 已含新键)
    paths = [root / r["manifest"] for r in rows] + \
            [Path(r["source_file"]) for r in rows] + \
            [root / "data/resolver_ref_r52/resolver_ir.json",
             root / "data/audit_snapshot_R50_input_baseline.json",
             root / SNAPSHOT_IN]
    post_rec = ai.record(POST_AUDIT_ID, paths, metrics={
        "n_interface_files": SCOPE_N,
        "n_backfilled": n_done,
        "n_already_backfilled": n_idem,
        "n_ir_admitted_sha_match": len(adm_match),
    })
    ai.write_record(post_rec)
    if not ai.verify(post_rec)["ok"]:
        raise RuntimeError("post-backfill audit snapshot self-verify failed")

    report = {
        "report_id": "interface_scope_step2_backfill",
        "field": FIELD,
        "definition": "SHA256(original source bytes), 64 lowercase hex",
        "scope": snap["scope_rule"],
        "summary": {
            "n_scope": SCOPE_N,
            "n_backfilled": n_done,
            "n_already_backfilled": n_idem,
            "n_ir_admitted": len(adm),
            "n_ir_admitted_sha_match": len(adm_match),
            "n_semantic_pending_qc_fail": len(pending),
            "n_ir_absent": len(absent),
            "source_bytes_unchanged": True,
            "r50_drift_expected_87": True,
            "pre_audit_corpus_sha256": pre_rec["corpus_sha256"],
            "post_audit_corpus_sha256": post_rec["corpus_sha256"],
        },
        "semantic_pending": sorted(x["manifest"] for x in pending),
        "ir_absent": sorted(x["manifest"] for x in absent),
        "files": results,
    }
    (root / REPORT_OUT).write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
