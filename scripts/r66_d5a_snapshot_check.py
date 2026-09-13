# -*- coding: utf-8 -*-
r"""
r66_d5a_snapshot_check.py — BUG-14-DATA D5-A 修复前/后冻结快照对账武器(只读)

用途(R66,用户 R65 裁定 D5-A:只修跑步机机制,先冻结修复前快照):
  以 R64 D0 冻结清单(data/r64_corpus_inventory.json,R65 已独立复证)为 baseline,
  对当前 OCR_ROOT 全部 md(源树 + derived + 根级)重新哈希,逐条对账:
    changed / missing / new 三态清单 + corpus_digest(整体指纹)。
  本武器输出无时间戳、确定性排序 —— 修复前后各跑一次,两次输出应字节一致,
  git diff 即"修复未触碰语料"的机器证据。

身份口径(有意为之,如实在册):
  - 内容身份 = (rel_path, size, sha256, norm_sha256);**mtime 不入身份**
    (进程重写同内容文件只会变 mtime,不算内容变化;但任何字节变化必入 changed)。
  - norm_sha256 = sha256(NFC(text); CRLF/CR->LF; per-line rstrip; whole strip)
    (复用 r64_data_inventory 同一实现,不另立副本)。
  - baseline 不含 OCR_ROOT 根级 md(F-r65-1);本武器单独点名根级 md 及其 sha。

铁律:零写入生产数据;只输出 data/r66_d5a_snapshot_check.json。
用法: python scripts/r66_d5a_snapshot_check.py
"""

import hashlib
import io
import json
import os
import sys
from pathlib import Path

BASE = Path(r"D:\Project\Papers")
sys.path.insert(0, str(BASE / "scripts"))

import r64_data_inventory as inv  # noqa: E402  复用同一采集/哈希实现(不复制)

OUT = Path(os.environ.get("R66_OUT") or BASE / "data" / "r66_d5a_snapshot_check.json")
BASELINE = Path(os.environ.get("R66_BASELINE") or BASE / "data" / "r64_corpus_inventory.json")
AUDIT_JSONL = Path(os.environ.get("R66_AUDIT") or BASE / "data" / "reclassify_audit.jsonl")

IDENTITY_FIELDS = ("rel_path", "size", "sha256", "norm_sha256")


def corpus_digest(records):
    h = hashlib.sha256()
    for r in sorted(records, key=lambda x: x["rel_path"]):
        h.update(f"{r['rel_path']}\t{r['sha256']}\n".encode("utf-8"))
    return h.hexdigest()


def root_level_md():
    """OCR_ROOT 根级 md(F-r65-1 口径:不入语料账,单独点名披露)。"""
    rows = []
    if not inv.OCR_ROOT.is_dir():
        return rows
    for fn in sorted(os.listdir(inv.OCR_ROOT)):
        full = inv.OCR_ROOT / fn
        if full.is_file() and fn.lower().endswith(".md"):
            sha, err = inv.sha256_file(full)
            rows.append({"rel_path": fn, "sha256": sha,
                         "errors": [err] if err else []})
    return rows


def main():
    with io.open(BASELINE, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    base_recs = baseline["records"]
    cur_recs, cur_errors = inv.collect_inventory()

    base_by = {r["rel_path"]: r for r in base_recs}
    cur_by = {r["rel_path"]: r for r in cur_recs}

    changed, missing = [], []
    for rel in sorted(base_by):
        b, c = base_by[rel], cur_by.get(rel)
        if c is None:
            missing.append(rel)
            continue
        if any(b.get(k) != c.get(k) for k in IDENTITY_FIELDS):
            changed.append({
                "rel_path": rel,
                "baseline": {k: b.get(k) for k in IDENTITY_FIELDS},
                "current": {k: c.get(k) for k in IDENTITY_FIELDS},
            })
    new = sorted(set(cur_by) - set(base_by))

    audit_sha = None
    if AUDIT_JSONL.is_file():
        audit_sha, _ = inv.sha256_file(AUDIT_JSONL)

    payload = {
        "meta": {
            "weapon": "r66_d5a_snapshot_check",
            "purpose": "D5-A 跑步机修复前后冻结快照对账(修复不得触碰语料)",
            "baseline": "data/r64_corpus_inventory.json (R64 D0 冻结;R65 独立复证 0 漂移)",
            "identity_fields": list(IDENTITY_FIELDS),
            "mtime_excluded_note": "mtime 不入内容身份(如实声明);任何字节变化必入 changed",
            "scope_note": "OCR_ROOT 源树+derived 全部 md(baseline 口径);根级 md 单独点名",
            "root_level_md": root_level_md(),
            "collect_errors": cur_errors,
        },
        "counts": {
            "baseline_records": len(base_recs),
            "current_records": len(cur_recs),
            "changed": len(changed),
            "missing": len(missing),
            "new": len(new),
        },
        "changed": changed,
        "missing": missing,
        "new": new,
        "corpus_digest": corpus_digest(cur_recs),
        "audit_jsonl_sha256": audit_sha,
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1))
    print(f"baseline={len(base_recs)} current={len(cur_recs)} "
          f"changed={len(changed)} missing={len(missing)} new={len(new)}")
    print(f"corpus_digest={payload['corpus_digest']}")


if __name__ == "__main__":
    main()
