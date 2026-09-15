# -*- coding: utf-8 -*-
"""dq_data_quality_scan.py — preprocessing 内部数据卫生四重点只读测量(一次性武器)。

Owner 2026 指令四重点:
  1. unit_type 值域(全语料 manifest + 真实 IR)
  2. figure 引用形态(源树全量 md,排除派生目录,沿用 recover_images 排除政策)
  3. unresolved flags 值域(真实 IR)
  4. manifest/source 输出稳定性(manifest 是否钉 sha / OCR 输出清单 sha 对账 / R50 基线复核)

纪律:只读,零语料写入;确定性(无时间戳进结论字段);G-AUDTB-1——不复用生产
parser 做判定,排除政策复用 recover_images 常量(单一来源,非判定逻辑)。
用法: python scripts/dq_data_quality_scan.py   → data/preprocessing_data_quality_scan.json
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "preprocessing_data_quality_scan.json"
OCR = ROOT / "Ocr-markdown"
IR_PATH = ROOT / "data" / "resolver_ref_r52" / "resolver_ir.json"
OCR_MANIFEST = ROOT / "data" / "ocr_output_manifest.jsonl"

# 排除政策单一来源(与 scripts/recover_images.py 相同语义;若漂移由测试钉住)
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from recover_images import EXCLUDED_TOP_NAMES, EXCLUDED_TOP_PREFIXES  # noqa: E402
except Exception:  # fail-closed:政策取不到就不做全树扫描,如实报告
    EXCLUDED_TOP_NAMES, EXCLUDED_TOP_PREFIXES = None, None

CANON_UNIT_TYPES = {"standalone_question", "composite_question"}
IMG_HTML = re.compile(r"<img[^>]*\ssrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
IMG_MD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_unit_type() -> dict:
    """重点 1:全语料 manifest + 真实 IR 的 unit_type 值域。"""
    files = sorted(OCR.rglob("*.manifest.json"))
    per_value_files = {}
    value_counter = Counter()
    anomalies = []  # (manifest, unit_id, value)
    identity_versions = Counter()
    for m in files:
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
        except Exception as e:
            anomalies.append({"manifest": str(m.relative_to(ROOT)), "error": repr(e)})
            continue
        identity_versions[str(data.get("identity_version"))] += 1
        for u in data.get("units", []):
            v = u.get("unit_type")
            value_counter[v] += 1
            per_value_files.setdefault(v, set()).add(str(m.relative_to(ROOT)))
            if v not in CANON_UNIT_TYPES:
                anomalies.append({
                    "manifest": str(m.relative_to(ROOT)),
                    "unit_id": u.get("unit_id"),
                    "unit_type": v,
                })
    ir_counter = Counter()
    ir_anomalies = []
    if IR_PATH.is_file():
        ir = json.loads(IR_PATH.read_text(encoding="utf-8"))
        for f in ir.get("files", []):
            for u in (f.get("ir") or {}).get("units", []) or []:
                v = u.get("unit_type")
                ir_counter[v] += 1
                if v not in CANON_UNIT_TYPES:
                    ir_anomalies.append({
                        "source_file": (f.get("file") or "").split("\\")[-1],
                        "unit_id": u.get("unit_id"),
                        "unit_type": v,
                    })
    return {
        "manifests_scanned": len(files),
        "identity_version_distribution": dict(identity_versions),
        "manifest_value_counts": {str(k): v for k, v in value_counter.items()},
        "manifest_non_canonical": anomalies,
        "manifest_value_files": {str(k): sorted(v) for k, v in per_value_files.items()},
        "ir_value_counts": {str(k): v for k, v in ir_counter.items()},
        "ir_non_canonical": ir_anomalies,
    }


def scan_figures() -> dict:
    """重点 2:源树全量 md 的图片引用形态 + 悬空检查。"""
    if EXCLUDED_TOP_NAMES is None:
        return {"error": "exclusion policy unavailable — scan skipped (fail-closed)"}
    total_refs = 0
    total_files_with_refs = 0
    forms = Counter()  # html_local / md_local / http / data_uri / other
    dangling = []
    external_samples = []
    scanned = 0
    for top in sorted(p for p in OCR.iterdir() if p.is_dir()):
        if top.name in EXCLUDED_TOP_NAMES or top.name.startswith(EXCLUDED_TOP_PREFIXES):
            continue
        for md in sorted(top.rglob("*.md")):
            scanned += 1
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                dangling.append({"file": str(md.relative_to(ROOT)), "error": repr(e)})
                continue
            refs = [("html", r) for r in IMG_HTML.findall(text)] + \
                   [("md", r) for r in IMG_MD.findall(text)]
            if refs:
                total_files_with_refs += 1
            for syntax, ref in refs:
                total_refs += 1
                r = ref.strip()
                if r.startswith(("http://", "https://")):
                    forms["external_http"] += 1
                    if len(external_samples) < 5:
                        external_samples.append({"file": str(md.relative_to(ROOT)), "ref": r})
                elif r.startswith("data:"):
                    forms["data_uri"] += 1
                elif re.match(r"^[a-zA-Z]:", r) or r.startswith("\\\\"):
                    forms["absolute_path"] += 1
                    target = Path(r)
                    if not target.exists():
                        dangling.append({"file": str(md.relative_to(ROOT)), "ref": r})
                else:
                    forms[f"{syntax}_local_relative"] += 1
                    target = (md.parent / r).resolve()
                    if not target.exists():
                        # 悬空归因:bare imgs/(原始 OCR 形态)vs 已改写 _imgs/ 形态
                        if r.startswith("imgs/") or r.startswith("./imgs/"):
                            stem_dir = OCR / "_imgs" / md.stem
                            recovered = (stem_dir / r) if stem_dir.is_dir() else None
                            alt = stem_dir / "imgs" / Path(r).name
                            if (recovered is not None and recovered.exists()) or alt.exists():
                                kind = "bare_imgs_asset_in__imgs_ref_not_rewritten"
                            else:
                                kind = "bare_imgs_no_asset_anywhere"
                        elif "_imgs/" in r:
                            kind = "rewritten__imgs_target_missing"
                        else:
                            kind = "other_relative_missing"
                        dangling.append({"file": str(md.relative_to(ROOT)), "ref": r, "kind": kind})
    kind_counts = Counter(d.get("kind", "read_error") for d in dangling)
    dangling_files = Counter(d["file"] for d in dangling if "file" in d)
    return {
        "source_md_scanned": scanned,
        "files_with_refs": total_files_with_refs,
        "total_refs": total_refs,
        "form_counts": dict(forms),
        "dangling_count": len(dangling),
        "dangling_kind_counts": dict(kind_counts),
        "dangling_files_count": len(dangling_files),
        "dangling_top_files": dangling_files.most_common(20),
        "dangling_samples": dangling[:30],
        "external_samples": external_samples,
    }


def scan_flags() -> dict:
    """重点 3:IR flags 值域(含 unresolved 槽位量化)。"""
    if not IR_PATH.is_file():
        return {"error": "IR missing"}
    ir = json.loads(IR_PATH.read_text(encoding="utf-8"))
    flag_counter = Counter()
    units = 0
    unresolved_slots = 0
    answers_table_units = 0
    dispositions = Counter()
    for f in ir.get("files", []):
        dispositions[f.get("disposition")] += 1
        fir = f.get("ir") or {}
        for u in fir.get("units", []) or []:
            units += 1
            for fl in u.get("flags", []) or []:
                flag_counter[fl] += 1
            ans = u.get("answers")
            if isinstance(ans, dict):
                answers_table_units += 1
                unresolved_slots += len(ans.get("unresolved") or [])
    return {
        "ir_version": ir.get("ir_version"),
        "files": len(ir.get("files", [])),
        "dispositions": dict(dispositions),
        "units": units,
        "flag_value_counts": dict(flag_counter),
        "answers_table_units": answers_table_units,
        "unresolved_slots": unresolved_slots,
    }


def scan_stability() -> dict:
    """重点 4:manifest 是否钉源 sha / OCR 输出清单 sha 对账 / IR sha 对账。"""
    # 4a. manifest 是否携带任何 sha 字段(精确键名,防 "shared" 类子串误命中)
    manifests = sorted(OCR.rglob("*.manifest.json"))
    with_sha_key = []
    sha_key_names = Counter()

    def _walk_keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and ("sha256" in k.lower() or k.lower() in ("sha", "hash", "source_sha")):
                    sha_key_names[k] += 1
                    yield k
                yield from _walk_keys(v)
        elif isinstance(obj, list):
            for x in obj:
                yield from _walk_keys(x)

    for m in manifests:
        data = json.loads(m.read_text(encoding="utf-8"))
        if any(True for _ in _walk_keys(data)):
            with_sha_key.append(str(m.relative_to(ROOT)))
    # 4b. OCR 输出清单(ocr_output_manifest.jsonl):条目数 + 抽样 sha 对账
    om_entries = 0
    om_bad = []
    om_checked = 0
    om_missing_output = 0
    if OCR_MANIFEST.is_file():
        lines = [l for l in OCR_MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
        om_entries = len(lines)
        idxs = sorted({0, om_entries // 3, 2 * om_entries // 3, om_entries - 1})
        for i in idxs:
            e = json.loads(lines[i])
            out = OCR / e["output_rel"]
            if not out.is_file():
                om_missing_output += 1
                continue
            actual = _sha256(out)
            om_checked += 1
            # 清单钉的是 PDF 源 sha;输出侧无 sha 字段 → 如实记录 schema
    # 4c. IR provenance.source_sha256 与当前源文件 sha 对账——
    #     对账对象 = ir.source_file(源树路径),不是顶层 file(annotated 路径);
    #     首版武器曾误用顶层 file 得 10/10 假 mismatch,已修正(如实入账)。
    ir = json.loads(IR_PATH.read_text(encoding="utf-8")) if IR_PATH.is_file() else {"files": []}
    ir_mismatch = []
    ir_checked = 0
    ir_missing = 0
    for f in ir.get("files", []):
        fir = f.get("ir")
        if not fir:
            continue
        src = Path(fir["source_file"])
        if not src.is_file():
            ir_missing += 1
            ir_mismatch.append({"source_file": fir["source_file"], "reason": "missing"})
            continue
        ir_checked += 1
        if _sha256(src) != fir.get("source_sha256"):
            ir_mismatch.append({"source_file": fir["source_file"], "reason": "sha_mismatch"})
    # 4d. OCR 输出清单条目的 PDF 源 sha 抽样对账(清单 ↔ 源 PDF;PDF 在 original/ 树内按文件名检索)
    pdf_checked = pdf_bad = pdf_missing = 0
    if OCR_MANIFEST.is_file():
        lines = [l for l in OCR_MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
        idxs = sorted({0, len(lines) // 2, len(lines) - 1})
        for i in idxs:
            e = json.loads(lines[i])
            cand = (ROOT / "original" / e["source_rel"])
            if not cand.is_file():
                hits = list((ROOT / "original").rglob(Path(e["source_rel"]).name))
                cand = hits[0] if len(hits) == 1 else None
            if cand is None or not cand.is_file():
                pdf_missing += 1
                continue
            pdf_checked += 1
            if _sha256(cand) != e["source_sha256"]:
                pdf_bad += 1
    return {
        "manifest_total": len(manifests),
        "manifest_with_sha_key": len(with_sha_key),
        "sha_key_names": dict(sha_key_names),
        "ocr_output_manifest_entries": om_entries,
        "ocr_output_manifest_sample_checked": om_checked,
        "ocr_output_manifest_sample_missing": om_missing_output,
        "ocr_output_manifest_entry_schema_pins": ["source_sha256(PDF)", "source_size", "pages", "written_at", "output_rel"],
        "ir_sha_checked_all": ir_checked,
        "ir_sha_missing": ir_missing,
        "ir_sha_mismatches": ir_mismatch,
        "pdf_sha_sample_checked": pdf_checked,
        "pdf_sha_sample_missing": pdf_missing,
        "pdf_sha_mismatches": pdf_bad,
    }


def main() -> None:
    result = {
        "weapon": "dq-data-quality-scan-1",
        "scope": "read-only; Ocr-markdown source tree + 166 manifests + resolver_ref_r52 IR + ocr_output_manifest.jsonl",
        "unit_type": scan_unit_type(),
        "figures": scan_figures(),
        "flags": scan_flags(),
        "stability": scan_stability(),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: (v if k != "unit_type" else {kk: vv for kk, vv in v.items() if kk != "manifest_value_files"})
                      for k, v in result.items()}, ensure_ascii=False, indent=1)[:4000])
    print(f"\n[written] {OUT}")


if __name__ == "__main__":
    main()
