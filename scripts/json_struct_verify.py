# -*- coding: utf-8 -*-
"""QCORE-DELIVERY-01-B-R1: OCR JSON 结构化检测层。

只读检测,不修改 Manifest 内容(units)、不修改 OCR 产物、不自动修复。
检测结果写入 annotation_meta.json_struct_verification。

四个功能:
  A. 双输入关联与校验(associate_inputs) — manifest_path 和 ocr_run_id 必填
  B. 答案证据匹配(match_answer_evidence) — 限定 answer_lines 区域,过短标 too_short
  C. 答案完整性与结构风险检测(detect_structural_risks) — 图片用 <img src> 定位
  D. 检测结果输出(build_verification_report) + CLI 入口

用法:
  python json_struct_verify.py \
    --pdf <path> --md <path> --json <path> --manifest <path> \
    --pdf-sha <sha256> --md-sha <sha256> --json-sha <sha256> \
    --run-id <ocr_run_id> \
    --manifest-out <output_manifest_with_annotation> \
    --report-out <detection_report_json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

CHUNK = 1 << 20


class VerificationError(RuntimeError):
    """输入关联或校验失败;调用方必须显式处理,禁止静默降级。"""


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ─── A. 双输入关联与校验 ───────────────────────────────────────────

def associate_inputs(
    *,
    pdf_path: str | Path,
    md_path: str | Path,
    json_path: str | Path,
    expected_pdf_sha256: str,
    expected_md_sha256: str,
    expected_json_sha256: str,
    ocr_run_id: str,
    manifest_path: str | Path,
    ocr_output_root: str | Path | None = None,
) -> dict:
    """双输入关联校验。manifest_path 和 ocr_run_id 必填。失败抛 VerificationError。"""
    result = {
        "associated": False,
        "pdf_sha256": None,
        "md_sha256": None,
        "json_sha256": None,
        "ocr_run_id": ocr_run_id,
        "manifest_entry": None,
        "manifest_source": str(manifest_path),
        "errors": [],
    }

    # 0. 必填参数检查
    if not ocr_run_id:
        raise VerificationError("ocr_run_id 必填,不允许为空")
    if not manifest_path or not os.path.isfile(manifest_path):
        raise VerificationError(f"manifest_path 必填且必须存在: {manifest_path}")

    # 1. 文件存在性
    for label, p in [("PDF", pdf_path), ("Markdown", md_path), ("JSON", json_path)]:
        if not os.path.isfile(p):
            result["errors"].append(f"{label} 文件不存在: {p}")
    if result["errors"]:
        raise VerificationError("; ".join(result["errors"]))

    # 2. 路径越界检查
    if ocr_output_root:
        root = Path(ocr_output_root).resolve()
        for label, p in [("Markdown", md_path), ("JSON", json_path)]:
            rp = Path(p).resolve()
            if not (rp == root or str(rp).startswith(str(root) + os.sep)):
                result["errors"].append(f"{label} 路径越界: {p} 不在 {root} 内")

    # 3. SHA-256 校验
    result["pdf_sha256"] = _sha256_file(pdf_path)
    result["md_sha256"] = _sha256_file(md_path)
    result["json_sha256"] = _sha256_file(json_path)

    if result["pdf_sha256"] != expected_pdf_sha256:
        result["errors"].append(f"PDF SHA-256 不匹配")
    if result["md_sha256"] != expected_md_sha256:
        result["errors"].append(f"MD SHA-256 不匹配")
    if result["json_sha256"] != expected_json_sha256:
        result["errors"].append(f"JSON SHA-256 不匹配")

    # 4. 台账关联:必须找到 ocr_run_id 匹配的记录
    entries = _load_manifest_entries(manifest_path)
    matched = None
    for e in entries:
        if (e.get("source_sha256") == expected_pdf_sha256
                and e.get("ocr_run_id") == ocr_run_id):
            if matched is not None:
                result["errors"].append(
                    f"OCR Run 歧义: source_sha256 + ocr_run_id 匹配到多条记录")
                break
            matched = e

    if matched is None:
        # check if there are entries with matching sha but different/no run_id
        sha_matches = [e for e in entries if e.get("source_sha256") == expected_pdf_sha256]
        if sha_matches:
            run_ids = [e.get("ocr_run_id") for e in sha_matches]
            result["errors"].append(
                f"未找到 ocr_run_id={ocr_run_id} 的台账记录; "
                f"同 PDF 的现有 run_id: {run_ids}")
        else:
            result["errors"].append(
                f"台账中无 source_sha256={expected_pdf_sha256[:16]}... 的记录")
        raise VerificationError("; ".join(result["errors"]))

    # 5. 台账字段完整性:R2 字段必须存在
    for field in ("output_rel", "output_md_sha256", "output_json_rel",
                  "output_json_sha256", "json_status"):
        if field not in matched or matched[field] is None:
            result["errors"].append(f"台账记录缺少必填字段: {field}")
    if result["errors"]:
        raise VerificationError("; ".join(result["errors"]))

    # 6. output_rel 与实际 md 路径全路径比对(正斜杠归一)
    actual_md_norm = str(md_path).replace("\\", "/")
    ledger_md_rel = matched["output_rel"].replace("\\", "/")
    # check if actual path ends with the ledger's relative path
    if not actual_md_norm.endswith(ledger_md_rel):
        result["errors"].append(
            f"台账 output_rel({ledger_md_rel})无法在实际 md 路径({actual_md_norm})中解析")
    # same for json
    actual_json_norm = str(json_path).replace("\\", "/")
    ledger_json_rel = matched.get("output_json_rel", "").replace("\\", "/")
    if ledger_json_rel and not actual_json_norm.endswith(ledger_json_rel):
        result["errors"].append(
            f"台账 output_json_rel({ledger_json_rel})无法在实际 json 路径({actual_json_norm})中解析")

    # 7. 台账哈希与实际文件哈希比对
    if matched.get("output_md_sha256") != result["md_sha256"]:
        result["errors"].append("台账 output_md_sha256 与实际 md 哈希不一致")
    if matched.get("output_json_sha256") != result["json_sha256"]:
        result["errors"].append("台账 output_json_sha256 与实际 json 哈希不一致")

    # 8. json_status 必须 complete
    if matched.get("json_status") != "complete":
        result["errors"].append(f"台账 json_status={matched.get('json_status')}, 不允许双输入检测")

    if result["errors"]:
        raise VerificationError("; ".join(result["errors"]))

    result["manifest_entry"] = {
        k: matched.get(k) for k in (
            "source_sha256", "ocr_run_id", "output_rel",
            "output_md_sha256", "output_json_rel", "output_json_sha256",
            "json_status", "json_page_check", "pdf_page_count",
        ) if k in matched
    }
    result["associated"] = True
    return result


def _load_manifest_entries(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
    return entries


# ─── JSON 结构解析 ─────────────────────────────────────────────

def parse_json_blocks(json_path: str | Path) -> list[dict]:
    """解析 ocr_raw.jsonl,返回全部块列表。"""
    blocks = []
    with open(json_path, encoding="utf-8") as f:
        page_idx = 0
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            for lpr in (obj.get("result") or {}).get("layoutParsingResults") or []:
                pr = lpr.get("prunedResult") or {}
                for b in pr.get("parsing_res_list") or []:
                    blocks.append({
                        "block_id": b.get("block_id"),
                        "label": b.get("block_label"),
                        "content": b.get("block_content") or "",
                        "bbox": b.get("block_bbox"),
                        "order": b.get("block_order"),
                        "group_id": b.get("group_id"),
                        "page_index": page_idx,
                    })
                page_idx += 1
    return blocks


def parse_json_markdown_images(json_path: str | Path) -> dict[int, dict[str, str]]:
    """提取每页的 markdown.images 映射 {page_idx: {img_src: url}}。"""
    result = {}
    with open(json_path, encoding="utf-8") as f:
        page_idx = 0
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            for lpr in (obj.get("result") or {}).get("layoutParsingResults") or []:
                md = lpr.get("markdown") or {}
                if isinstance(md, dict):
                    result[page_idx] = md.get("images") or {}
                page_idx += 1
    return result


# ─── B. 答案证据匹配 ───────────────────────────────────────────

MIN_LITERAL_LEN = 4


def _normalize_text(s: str) -> str:
    """有限规范化:Unicode NFKC + 去 HTML 标签 + 去全部空白。"""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def _get_answer_region_blocks(blocks: list[dict], al: list | None, md_lines: list[str]) -> list[dict]:
    """限定候选块在 answer_lines 覆盖范围内。"""
    if not isinstance(al, list) or len(al) != 2:
        return []
    s, e = max(1, al[0]), min(len(md_lines), al[1])
    region_text = "\n".join(md_lines[s - 1:e])
    region_norm = _normalize_text(region_text)
    candidates = []
    for b in blocks:
        c = b["content"]
        if not c or len(c) < 2:
            continue
        # block content must appear in answer region
        if _normalize_text(c) in region_norm:
            candidates.append(b)
    return candidates


def match_answer_evidence(man: dict, blocks: list[dict], md_lines: list[str]) -> list[dict]:
    """对每个 unit 的 answer_evidence.value 在 answer_lines 区域内做确定性匹配。

    结果: literal / normalized / unmatched / too_short。
    候选块限定在 answer_lines 覆盖范围内。
    """
    results = []
    for u in man.get("units", []):
        ae = u.get("answer_evidence") or {}
        val = ae.get("value")
        al = u.get("answer_lines")
        unit_result = {
            "unit_id": u.get("unit_id"),
            "question_numbers": u.get("question_numbers"),
            "value_is_empty": val is None or (isinstance(val, str) and not val.strip()),
            "match_status": "unmatched",
            "matched_block_ids": [],
            "matched_page_indices": [],
            "match_method": None,
            "diff_note": None,
        }

        if unit_result["value_is_empty"]:
            unit_result["diff_note"] = "answer_evidence.value 为空"
            results.append(unit_result)
            continue

        val_stripped = val.strip()
        val_norm = _normalize_text(val)

        # too_short: 值过短不做 literal 判定(先于候选块查询)
        if len(val_stripped) < MIN_LITERAL_LEN:
            unit_result["match_status"] = "too_short"
            unit_result["diff_note"] = f"值长度 {len(val_stripped)} < {MIN_LITERAL_LEN},不做 literal 判定"
            results.append(unit_result)
            continue

        # 候选块限定在 answer_lines 区域
        candidates = _get_answer_region_blocks(blocks, al, md_lines)
        if not candidates:
            unit_result["match_status"] = "unmatched_no_candidates"
            unit_result["diff_note"] = "answer_lines 区域内无可匹配的 JSON 文本块"
            results.append(unit_result)
            continue

        if not val_norm:
            unit_result["diff_note"] = "value 规范化后为空"
            results.append(unit_result)
            continue

        # 1. literal: verbatim substring in a single candidate block
        for b in candidates:
            if val_stripped in b["content"]:
                unit_result["match_status"] = "literal"
                unit_result["matched_block_ids"].append(b["block_id"])
                unit_result["matched_page_indices"].append(b["page_index"])
                unit_result["match_method"] = "verbatim_in_answer_region"
                results.append(unit_result)
                break
        else:
            # 2. normalized: normalized substring
            for b in candidates:
                b_norm = _normalize_text(b["content"])
                if val_norm in b_norm:
                    unit_result["match_status"] = "normalized"
                    unit_result["matched_block_ids"].append(b["block_id"])
                    unit_result["matched_page_indices"].append(b["page_index"])
                    unit_result["match_method"] = "normalized_in_answer_region"
                    results.append(unit_result)
                    break
            else:
                # 3. multi-block in answer region
                matched_parts = []
                remaining = val_norm
                for b in sorted(candidates, key=lambda x: len(_normalize_text(x["content"])), reverse=True):
                    b_norm = _normalize_text(b["content"])
                    if b_norm and b_norm in remaining:
                        matched_parts.append(b)
                        remaining = remaining.replace(b_norm, "", 1)
                if matched_parts and len(remaining) < len(val_norm) * 0.3:
                    unit_result["match_status"] = "normalized"
                    unit_result["matched_block_ids"] = [b["block_id"] for b in matched_parts]
                    unit_result["matched_page_indices"] = [b["page_index"] for b in matched_parts]
                    unit_result["match_method"] = "multi_block_in_answer_region"
                    unit_result["diff_note"] = f"拼接 {len(matched_parts)} 块,残余 {len(remaining)} 字符"
                else:
                    unit_result["match_status"] = "unmatched_text_mismatch"
                    unit_result["diff_note"] = (
                        f"文本不匹配: value 长度 {len(val_stripped)}, "
                        f"候选块 {len(candidates)}, 最佳残余 {len(remaining)} 字符")
                results.append(unit_result)

    return results


# ─── C. 答案完整性与结构风险检测 ─────────────────────────────────

_SUBQ_RE = re.compile(r"[（(]\s*(\d{1,2})\s*[)）]")
_IMG_SRC_RE = re.compile(r'<img[^>]*src="([^"]*)"')
_IMG_BBOX_RE = re.compile(r"_box_(\d+)_(\d+)_(\d+)_(\d+)\.\w+$")


def _extract_bbox_from_ref(ref: str) -> list[int] | None:
    """从图片文件名提取 bbox: img_in_*_box_{x0}_{y0}_{x1}_{y1}.ext"""
    m = _IMG_BBOX_RE.search(ref.replace("\\", "/"))
    if m:
        return [int(m.group(i)) for i in range(1, 5)]
    return None


def detect_structural_risks(
    man: dict,
    blocks: list[dict],
    md_lines: list[str],
    json_images: dict[int, dict[str, str]] | None = None,
) -> dict:
    """C1-C4:空答案值、子问标记覆盖、结构块盘点、结构/文本分离。

    图片归属:用 MD answer_lines 区域内 <img src> + JSON markdown.images 对应,
    不使用 group_id 猜测。无法归属记 unattributed。
    """
    out = {"units": [], "summary": {}}
    json_images = json_images or {}

    for u in man.get("units", []):
        uid = u.get("unit_id")
        ae = u.get("answer_evidence") or {}
        val = ae.get("value")
        al = u.get("answer_lines")
        unit_res = {
            "unit_id": uid,
            "question_numbers": u.get("question_numbers"),
            "c1_empty_value": None,
            "c2_sub_question_gap": None,
            "c3_structural_blocks": [],
            "c3_unattributed_images": [],
            "c4_notes": [],
        }

        val_empty = val is None or (isinstance(val, str) and not val.strip())

        # C1: 空答案值检测
        if val_empty:
            al_has_content = False
            if isinstance(al, list) and len(al) == 2:
                s, e = max(1, al[0]), min(len(md_lines), al[1])
                region = "\n".join(md_lines[s - 1:e]).strip()
                al_has_content = bool(region)
            unit_res["c1_empty_value"] = {
                "detected": True,
                "answer_lines_has_content": al_has_content,
                "answer_lines": al,
            }

        # C2: 子问标记覆盖检测
        if not val_empty and isinstance(val, str):
            val_subqs = set(_SUBQ_RE.findall(val))
            area_subqs = set()
            if isinstance(al, list) and len(al) == 2:
                s, e = max(1, al[0]), min(len(md_lines), al[1])
                region_text = "\n".join(md_lines[s - 1:e])
                region_norm = _normalize_text(region_text)
                for b in blocks:
                    if b["content"] and _normalize_text(b["content"]) in region_norm:
                        for sq in _SUBQ_RE.findall(b["content"]):
                            area_subqs.add(sq)
            missing = area_subqs - val_subqs
            if area_subqs and missing:
                unit_res["c2_sub_question_gap"] = {
                    "detected": True,
                    "area_sub_questions": sorted(area_subqs, key=int),
                    "value_sub_questions": sorted(val_subqs, key=int),
                    "missing_in_value": sorted(missing, key=int),
                }
            elif area_subqs:
                unit_res["c2_sub_question_gap"] = {
                    "detected": False,
                    "area_sub_questions": sorted(area_subqs, key=int),
                    "value_sub_questions": sorted(val_subqs, key=int),
                }
            else:
                unit_res["c2_sub_question_gap"] = {
                    "detected": None,
                    "note": "答案区域无可识别子问标记,无法判断",
                }

        # C3: 答案区域结构块盘点
        # 文本块:content 匹配 answer region
        # 图片块:MD answer region 内 <img src> → markdown.images → 图片块 bbox
        if isinstance(al, list) and len(al) == 2:
            s, e = max(1, al[0]), min(len(md_lines), al[1])
            region_text = "\n".join(md_lines[s - 1:e])
            region_norm = _normalize_text(region_text)

            # 图片归属:通过 <img src> 文件名中的 bbox 模式 (x0_y0_x1_y1) 与 block_bbox 匹配
            img_refs = _IMG_SRC_RE.findall(region_text)
            if img_refs and json_images:
                for ref in img_refs:
                    # 从 ref 提取 bbox: img_in_image_box_{x0}_{y0}_{x1}_{y1}.ext
                    ref_bbox = _extract_bbox_from_ref(ref)
                    matched_block = None
                    if ref_bbox:
                        for b in blocks:
                            if b["label"] == "image" and b["bbox"] and list(b["bbox"]) == ref_bbox:
                                matched_block = b
                                break
                    # fallback: 找该 ref 对应页面的 image 块(仅当 bbox 不可解析时)
                    if not matched_block and ref_bbox is None:
                        for page_idx, imgs in json_images.items():
                            if ref in imgs or any(ref in k for k in imgs):
                                for b in blocks:
                                    if b["label"] == "image" and b["page_index"] == page_idx and b["bbox"]:
                                        matched_block = b
                                        break
                                break
                    if matched_block:
                        unit_res["c3_structural_blocks"].append({
                            "page_index": matched_block["page_index"],
                            "block_id": matched_block["block_id"],
                            "block_order": matched_block["order"],
                            "block_label": matched_block["label"],
                            "bbox": matched_block["bbox"],
                            "img_ref": ref,
                        })
                    else:
                        unit_res["c3_unattributed_images"].append(ref)

            # 非图片结构块:table/formula 在 answer region
            for b in blocks:
                if b["label"] in ("table", "display_formula", "inline_formula", "chart"):
                    if b["content"] and _normalize_text(b["content"]) in region_norm:
                        unit_res["c3_structural_blocks"].append({
                            "page_index": b["page_index"],
                            "block_id": b["block_id"],
                            "block_order": b["order"],
                            "block_label": b["label"],
                            "bbox": b["bbox"],
                        })

        # C4 flags
        has_image = any(sb["block_label"] == "image" for sb in unit_res["c3_structural_blocks"])
        has_table = any(sb["block_label"] == "table" for sb in unit_res["c3_structural_blocks"])
        has_formula = any(sb["block_label"] in ("display_formula", "inline_formula")
                          for sb in unit_res["c3_structural_blocks"])
        if has_image:
            unit_res["c4_notes"].append("answer_has_image_evidence")
        if has_table:
            unit_res["c4_notes"].append("answer_has_table_evidence")
        if has_formula:
            unit_res["c4_notes"].append("answer_has_formula_evidence")
        if unit_res["c3_unattributed_images"]:
            unit_res["c4_notes"].append("unattributed_images_in_answer_region")

        out["units"].append(unit_res)

    # summary
    out["summary"] = {
        "total_units": len(out["units"]),
        "c1_empty_value_count": sum(1 for r in out["units"] if r["c1_empty_value"] and r["c1_empty_value"]["detected"]),
        "c2_gap_count": sum(1 for r in out["units"] if r["c2_sub_question_gap"] and r["c2_sub_question_gap"].get("detected")),
        "c3_units_with_image": sum(1 for r in out["units"] if "answer_has_image_evidence" in r["c4_notes"]),
        "c3_units_with_table": sum(1 for r in out["units"] if "answer_has_table_evidence" in r["c4_notes"]),
        "c3_units_with_formula": sum(1 for r in out["units"] if "answer_has_formula_evidence" in r["c4_notes"]),
        "c3_total_image_blocks": sum(
            sum(1 for sb in r["c3_structural_blocks"] if sb["block_label"] == "image")
            for r in out["units"]),
        "c3_total_table_blocks": sum(
            sum(1 for sb in r["c3_structural_blocks"] if sb["block_label"] == "table")
            for r in out["units"]),
        "c3_total_formula_blocks": sum(
            sum(1 for sb in r["c3_structural_blocks"] if sb["block_label"] in ("display_formula", "inline_formula"))
            for r in out["units"]),
    }
    return out


# ─── D. 检测结果输出 ───────────────────────────────────────────

def build_verification_report(
    *,
    association: dict,
    evidence_matches: list[dict],
    structural: dict,
    json_path: str | Path,
    md_path: str | Path,
    pdf_sha256: str,
    ocr_run_id: str,
) -> dict:
    """构建 annotation_meta.json_struct_verification 结果字典。"""
    blocks = parse_json_blocks(json_path)

    report = {
        "detection_version": "QCORE-DELIVERY-01-B-R1",
        "input": {
            "pdf_sha256": pdf_sha256,
            "ocr_run_id": ocr_run_id,
            "md_sha256": association.get("md_sha256"),
            "json_sha256": association.get("json_sha256"),
            "manifest_entry": association.get("manifest_entry"),
            "manifest_source": association.get("manifest_source"),
        },
        "json_block_stats": {
            "total_blocks": len(blocks),
            "by_label": {},
        },
        "answer_evidence_matching": evidence_matches,
        "structural_risks": structural,
        "summary": {
            "total_units": len(evidence_matches),
            "literal_count": sum(1 for m in evidence_matches if m["match_status"] == "literal"),
            "normalized_count": sum(1 for m in evidence_matches if m["match_status"] == "normalized"),
            "unmatched_no_candidates_count": sum(1 for m in evidence_matches if m["match_status"] == "unmatched_no_candidates"),
            "unmatched_text_mismatch_count": sum(1 for m in evidence_matches if m["match_status"] == "unmatched_text_mismatch"),
            "too_short_count": sum(1 for m in evidence_matches if m["match_status"] == "too_short"),
            "empty_value_count": sum(1 for m in evidence_matches if m["value_is_empty"]),
        },
    }

    for b in blocks:
        lab = b["label"] or "unknown"
        report["json_block_stats"]["by_label"][lab] = (
            report["json_block_stats"]["by_label"].get(lab, 0) + 1
        )

    return report


def write_annotation(manifest_path: str | Path, verification: dict,
                     output_path: str | Path) -> None:
    """将检测结果写入 manifest 的 annotation_meta.json_struct_verification(不动 units)。"""
    man = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if "annotation_meta" not in man:
        man["annotation_meta"] = {}
    man["annotation_meta"]["json_struct_verification"] = verification
    Path(output_path).write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── CLI 入口 ─────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="QCORE-DELIVERY-01-B-R1: OCR JSON 结构化检测层")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--manifest", required=True, help="OCR 输出台账路径")
    ap.add_argument("--pdf-sha", required=True)
    ap.add_argument("--md-sha", required=True)
    ap.add_argument("--json-sha", required=True)
    ap.add_argument("--run-id", required=True, help="OCR Run ID(台账中的 ocr_run_id)")
    ap.add_argument("--manifest-input", required=True, help="待检测的 Manifest JSON")
    ap.add_argument("--report-out", required=True, help="检测报告输出路径")
    ap.add_argument("--manifest-out", help="输出带 annotation 的 Manifest(可选)")
    ap.add_argument("--ocr-root", required=True, help="OCR 输出根目录(路径越界检查)")
    args = ap.parse_args()

    # A: 关联校验
    try:
        assoc = associate_inputs(
            pdf_path=args.pdf, md_path=args.md, json_path=args.json,
            expected_pdf_sha256=args.pdf_sha,
            expected_md_sha256=args.md_sha,
            expected_json_sha256=args.json_sha,
            ocr_run_id=args.run_id,
            manifest_path=args.manifest,
            ocr_output_root=args.ocr_root,
        )
        print(f"[A] associated OK: run_id={args.run_id}")
    except VerificationError as e:
        print(f"[A] FAILED: {e}", file=sys.stderr)
        sys.exit(1)

    # load manifest + md
    man = json.loads(Path(args.manifest_input).read_text(encoding="utf-8"))
    md_lines = Path(args.md).read_text(encoding="utf-8", errors="replace").splitlines()

    # parse JSON
    blocks = parse_json_blocks(args.json)
    json_images = parse_json_markdown_images(args.json)
    print(f"[JSON] {len(blocks)} blocks")

    # B: evidence matching
    matches = match_answer_evidence(man, blocks, md_lines)
    s = {k: sum(1 for m in matches if m["match_status"] == k)
         for k in ("literal", "normalized", "unmatched_no_candidates",
                   "unmatched_text_mismatch", "too_short")}
    print(f"[B] literal={s['literal']} normalized={s['normalized']} "
          f"unmatched_no_cand={s['unmatched_no_candidates']} "
          f"unmatched_text={s['unmatched_text_mismatch']} "
          f"too_short={s['too_short']}")

    # C: structural risks
    structural = detect_structural_risks(man, blocks, md_lines, json_images)
    ss = structural["summary"]
    print(f"[C] empty={ss['c1_empty_value_count']} gap={ss['c2_gap_count']} "
          f"img_units={ss['c3_units_with_image']} img_blocks={ss['c3_total_image_blocks']}")

    # D: report
    report = build_verification_report(
        association=assoc, evidence_matches=matches, structural=structural,
        json_path=args.json, md_path=args.md,
        pdf_sha256=args.pdf_sha, ocr_run_id=args.run_id,
    )
    Path(args.report_out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[D] report -> {args.report_out}")

    # optional: write annotation
    if args.manifest_out:
        write_annotation(args.manifest_input, report, args.manifest_out)
        print(f"[D] annotated manifest -> {args.manifest_out}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# G2-A 方案 A 强制门禁（Owner 2026-11-15 裁决 + DSH 预审判据）
#
# 纯校验、只读：本函数不修改 man（尤其不改 units）。返回验证结果字典，
# 由生成链调用方写入 annotation_meta["json_struct_verification"]。
# json_evidence 缺失判 FAIL（不是跳过）；反向场景（删 JSONL/篡改/错页/
# 跨 run 混用/删指针）由摘要比对与逐页消费证明捕获。
# ---------------------------------------------------------------------------

GATE_VERSION = "g2a-json-gate-v1"
_MARKER_RE = re.compile(r"〔j p(\d+) b([\d,\-]+)(?: box [\d,\-]+)?〕")


def run_generation_gate(
    *,
    man: dict,
    ev_map: dict,
    md_text: str,
    jsonl_path: str | Path,
    recorded: dict | None,
    prompt_text: str | None = None,
    prompt_sha256: str | None = None,
    mode: str = "generation",
) -> dict:
    """执行 G2-A 双源验证门禁。返回 {verdict, checks, unit_flags, ...}。

    mode="generation"：完整消费证明（prompt 证据列逐页/块溯源）。
    mode="recompile"：无新 prompt——指针/摘要照查，prompt 子项记
    not_applicable 并注明依赖原 run 记录（json_evidence 缺失仍 FAIL）。
    """
    import hashlib as _hashlib

    checks: list[dict] = []
    unit_flags: dict[str, dict] = {}

    def _check(cid, status, detail):
        checks.append({"id": cid, "status": status, "detail": detail})

    units = man.get("units") or []

    if ev_map is None:
        _check("G2_binding", "fail", "ev_map 不可构建（OCR-JSON 缺失或不可解析）")
        return {
            "verdict": "FAIL", "gate_version": GATE_VERSION, "checks": checks,
            "unit_flags": {}, "unreliable_units": [],
            "divergence_register": {}, "consumption_proof": {},
            "mode": mode,
        }

    # ---- G1 证据存在性：缺失即 FAIL（不是跳过）----
    if not recorded:
        _check("G1_evidence_presence", "fail",
               "annotation_meta.json_evidence 缺失——无法证明 JSON 参与生成（含 --recompile 旧产物）")
        return {
            "verdict": "FAIL", "gate_version": GATE_VERSION, "checks": checks,
            "unit_flags": {}, "unreliable_units": [],
            "divergence_register": {}, "consumption_proof": {},
        }
    _check("G1_evidence_presence", "pass", "json_evidence 存在")

    # ---- G2 绑定：记录哈希 vs 本轮实际文件/重算映射（篡改/跨 run 捕获）----
    binding_fail = []
    # md 字节哈希由调用方记录进 json_evidence（write_outputs 落盘源 md 同源）；
    # 此处校验 jsonl 字节与映射摘要。
    try:
        json_sha = _hashlib.sha256(Path(jsonl_path).read_bytes()).hexdigest()
    except Exception as e:
        json_sha = None
        binding_fail.append(f"jsonl 不可读: {e}")
    if recorded.get("json_sha256") and json_sha and recorded["json_sha256"] != json_sha:
        binding_fail.append("jsonl SHA 不符（篡改或跨 run 混用）")
    import json_evidence_map as _jem_mod
    recomputed = _jem_mod.evidence_digest(ev_map)
    if recorded.get("map_sha256") and recorded["map_sha256"] != recomputed:
        binding_fail.append("map_sha256 不符（映射输入被改动或记录被篡改）")
    _check("G2_binding", "fail" if binding_fail else "pass",
           "; ".join(binding_fail) if binding_fail else "jsonl/map 摘要一致")

    # ---- G3 双向映射完整性 ----
    # 分流（Owner E-2"不得误升级"）：文本行（规范化后非空）未映射=证据缺口；
    # 标记行（原始非空、规范化为空，如 <div><img/></div>）是结构性行，走 G5 配对；
    # 结构性块（image/chart/table/formula 标签）未文本映射属预期，不株连单元。
    _jem2 = _jem_mod
    raw_lines = md_text.splitlines()
    _STRUCTURAL_LABELS = {"image", "chart", "table", "formula"}
    _segments = _jem2.split_md_pages(md_text)
    _pages_inv = _jem2.load_ocr_pages(jsonl_path)

    def _is_markup_only(n):
        raw = raw_lines[n - 1] if 0 < n <= len(raw_lines) else ""
        return bool(raw.strip()) and not _normalize_text(raw)

    blank_lines = {i for i, ln in enumerate(raw_lines, 1) if not ln.strip()}
    # 分页符行（独立 ---，与 split_md_pages/annotate_img_boxes 同规则）是结构性行，
    # 不属文本内容，不计未映射。
    sep_lines = {i for i, ln in enumerate(raw_lines, 1) if ln.strip() == "---"}
    _raw_unmapped = [n for n in ev_map.get("unmapped_lines", [])
                     if n not in blank_lines and n not in sep_lines
                     and not _is_markup_only(n)]
    # 重复文本分流（E-2"不得误升级"）：行内容在 JSON 块中存在但因同文首匹配
    # 歧义未挂上 → 内容证据在，仅位置归属不唯一，不株连单元；内容完全缺失才算缺口。
    _block_norms = {_normalize_text(b.get("content"))
                    for p in _pages_inv for b in p["blocks"]}
    text_unmapped_lines = [n for n in _raw_unmapped
                           if _normalize_text(raw_lines[n - 1]) not in _block_norms]
    unmapped_duplicate_content = [n for n in _raw_unmapped
                                  if _normalize_text(raw_lines[n - 1]) in _block_norms]
    markup_lines = [n for n in range(1, len(raw_lines) + 1)
                    if _is_markup_only(n)]
    all_unmapped_blocks = ev_map.get("unmapped_blocks", [])
    structural_unmapped_blocks = [b for b in all_unmapped_blocks
                                 if b.get("block_label") in _STRUCTURAL_LABELS]
    content_unmapped_blocks = [b for b in all_unmapped_blocks
                               if b.get("block_label") not in _STRUCTURAL_LABELS]
    mc = ev_map.get("match_counts", {})
    _check("G3_bidirectional",
           "pass" if not (text_unmapped_lines or content_unmapped_blocks) else "warn",
           f"mapped_exact={mc.get('mapped_exact')} folded={mc.get('mapped_folded')} "
           f"text_unmapped_lines={len(text_unmapped_lines)} "
           f"dup_content_lines={len(unmapped_duplicate_content)} markup_lines={len(markup_lines)} "
           f"content_unmapped_blocks={len(content_unmapped_blocks)} "
           f"structural_unmapped_blocks={len(structural_unmapped_blocks)} skipped={mc.get('skipped_blocks')}")

    # ---- 单元可靠性标记（未映射落在哪个单元区间）----
    def _units_of_line(n):
        out = []
        for u in units:
            for role in ("stem_lines", "options_lines", "answer_lines", "explanation_lines",
                         "extra_lines", "material_lines", "questions_lines"):
                sp = u.get(role)
                if isinstance(sp, list) and len(sp) == 2 and all(isinstance(x, int) for x in sp):
                    if sp[0] <= n <= sp[1]:
                        out.append(u.get("unit_id"))
                        break
        return out

    for n in text_unmapped_lines:
        for uid in _units_of_line(n):
            unit_flags.setdefault(str(uid), {"reliable": True, "reasons": []})
            unit_flags[str(uid)]["reliable"] = False
            unit_flags[str(uid)]["reasons"].append(f"unmapped_line L{n}")
    for b in content_unmapped_blocks:
        for u in units:
            ptr = (recorded.get("units") or {}).get(str(u.get("unit_id"))) or {}
            if b.get("page_no") in (ptr.get("pages") or []):
                unit_flags.setdefault(str(u.get("unit_id")), {"reliable": True, "reasons": []})
                unit_flags[str(u.get("unit_id"))]["reliable"] = False
                unit_flags[str(u.get("unit_id"))]["reasons"].append(
                    f"unmapped_block p{b.get('page_no')} b{b.get('block_id')}")

    # ---- G4 跨页/页级证据覆盖：单元页必须有 JSON 证据 ----
    page_ev_lines: dict[int, int] = {}
    for n, rec in (ev_map.get("lines") or {}).items():
        pg = rec.get("page")
        if pg is not None:
            page_ev_lines[pg] = page_ev_lines.get(pg, 0) + 1
    page_missing = []
    for uid, ptr in (recorded.get("units") or {}).items():
        for pg in ptr.get("pages") or []:
            if page_ev_lines.get(pg, 0) == 0:
                page_missing.append(f"{uid}@p{pg}")
                unit_flags.setdefault(uid, {"reliable": True, "reasons": []})
                unit_flags[uid]["reliable"] = False
                unit_flags[uid]["reasons"].append(f"page {pg} 无 JSON 证据")
    _check("G4_cross_page_coverage", "fail" if page_missing else "pass",
           f"单元页证据缺口: {page_missing}" if page_missing else "全部单元页均有 JSON 证据")

    # ---- G5 图像/标记行归属证据（多路确定性配对，禁止语义认领）----
    # (a) 文本块映射；(b) 标记行 ↔ 同页结构块（image/chart/table/formula 或空内容块）
    # 结构配对；(c) 文件名内嵌 box / 〔pN box …〕 注解 ↔ 同页块坐标。
    import re as _re
    _BOX_FN_RE = _re.compile(r"(?:img_in_)?(?:image|chart|table|formula)?_?box_(\d+)_(\d+)_(\d+)_(\d+)")
    _BOX_ANN_RE = _re.compile(r"〔p(\d+) box (\d+),(\d+)-(\d+),(\d+)〕")

    def _page_blocks(pg):
        for pd in _pages_inv:
            if pd.get("page_no") == pg:
                return pd.get("blocks") or []
        return []

    def _attributable(n):
        rec = (ev_map.get("lines") or {}).get(n)
        if rec and rec.get("block_ids"):
            return "block_mapped"
        raw = raw_lines[n - 1] if 0 < n <= len(raw_lines) else ""
        pg = rec.get("page") if rec else None
        if pg is None:
            seg = next((s for s in _segments if s["start_line"] <= n <= s["end_line"]), None)
            pg = seg["page_no"] if seg else None
        blocks = _page_blocks(pg) if pg else []
        box = None
        m = _BOX_FN_RE.search(raw) or _BOX_ANN_RE.search(raw)
        if m:
            box = tuple(int(x) for x in m.groups()[-4:])
        if box and any(tuple(b.get("bbox") or []) == box for b in blocks):
            return "spatial_bbox_match"
        if _is_markup_only(n) and any(
                (b.get("block_label") in _STRUCTURAL_LABELS)
                or not _normalize_text(b.get("content"))
                for b in blocks):
            return "structural_pairing"
        return None

    img_unconfirmed = []
    for u in units:
        uid = str(u.get("unit_id"))
        for role in ("stem_lines", "options_lines", "material_lines", "questions_lines", "extra_lines"):
            sp = u.get(role)
            if not (isinstance(sp, list) and len(sp) == 2):
                continue
            for n in range(max(1, sp[0]), sp[1] + 1):
                raw = raw_lines[n - 1] if 0 < n <= len(raw_lines) else ""
                if not (_re.search(r"<img\s", raw) or _is_markup_only(n)):
                    continue
                if not _attributable(n):
                    img_unconfirmed.append(f"{uid}@L{n}")
                    unit_flags.setdefault(uid, {"reliable": True, "reasons": []})
                    unit_flags[uid]["reliable"] = False
                    unit_flags[uid]["reasons"].append(f"img/markup line L{n} 无可定位 JSON 证据")
    _check("G5_image_attribution", "warn" if img_unconfirmed else "pass",
           f"未确认图行: {img_unconfirmed}" if img_unconfirmed
           else "标记行均有块映射/结构配对/坐标证据")

    # ---- G6 差异登记（只记录不修正）----
    divergence = {
        "folded_matches": mc.get("mapped_folded", 0),
        "text_unmapped_lines": text_unmapped_lines,
        "unmapped_duplicate_content_lines": unmapped_duplicate_content,
        "markup_lines": markup_lines,
        "unmapped_blocks": content_unmapped_blocks,
        "structural_unmapped_blocks": structural_unmapped_blocks,
        "skipped_blocks": mc.get("skipped_blocks", 0),
        "page_split_consistent": ev_map.get("page_split_consistent"),
        "note": "仅描述证据差异，不修正源文件、不生成替代文本",
    }
    _check("G6_divergence_register", "pass",
           f"folded={mc.get('mapped_folded')} text_unmapped={len(text_unmapped_lines)} "
           f"content_unmapped_blocks={len(content_unmapped_blocks)} "
           f"structural_unmapped_blocks={len(structural_unmapped_blocks)}")

    # ---- G7 消费证明（逐页标记/标记溯源/指针一致/同 run 锚）----
    cons_fail = []
    proof = {"mode": mode}
    if mode == "recompile":
        # recompile 无新 prompt：prompt 证据列检查不适用（消费证明留原 run 记录）；
        # 仍查单元指针一致性与原 run 锚（prompt_sha256 记录）。
        import json_evidence_map as _jem_r
        recomputed_ptr_r = _jem_r.unit_evidence_pointers(ev_map, units)
        if recorded.get("units") != recomputed_ptr_r:
            cons_fail.append("单元证据指针与重算不一致（指针被删改或输入被换）")
        proof["unit_pointers_match"] = recorded.get("units") == recomputed_ptr_r
        proof["prompt_marker_check"] = "not_applicable_recompile"
        if not (prompt_sha256 or recorded.get("prompt_sha256")):
            cons_fail.append("无 prompt_sha256 同 run 锚")
        else:
            proof["prompt_sha256"] = prompt_sha256 or recorded.get("prompt_sha256")
    elif prompt_text is None:
        cons_fail.append("未提供 prompt_text，无法证明证据列进入生成")
    else:
        marked_pages = set()
        marker_blocks = set()
        for m in _MARKER_RE.finditer(prompt_text):
            marked_pages.add(int(m.group(1)))
            for tok in m.group(2).split(","):
                if tok.isdigit():
                    marker_blocks.add(int(tok))
        proof["marked_pages"] = sorted(marked_pages)
        pages_with_text = {s["page_no"] for s in _segments
                           if any(ln.strip() for ln in s["lines"])}
        missing_marks = sorted(pages_with_text - marked_pages)
        if missing_marks:
            cons_fail.append(f"页缺证据标记: {missing_marks}")
        known_blocks = {b.get("block_id") for p in _pages_inv for b in p["blocks"]}
        ghost = sorted(b for b in marker_blocks if b not in known_blocks)
        if ghost:
            cons_fail.append(f"标记引用了 JSONL 不存在的块: {ghost}")
        proof["marker_blocks_in_jsonl"] = not ghost
        recomputed_ptr = _jem2.unit_evidence_pointers(ev_map, units)
        if recorded.get("units") != recomputed_ptr:
            cons_fail.append("单元证据指针与重算不一致（指针被删改或输入被换）")
        proof["unit_pointers_match"] = recorded.get("units") == recomputed_ptr
    if prompt_sha256:
        proof["prompt_sha256"] = prompt_sha256
    elif recorded.get("prompt_sha256"):
        proof["prompt_sha256"] = recorded["prompt_sha256"]
    else:
        cons_fail.append("无 prompt_sha256 同 run 锚")
    _check("G7_consumption_proof", "fail" if cons_fail else "pass",
           "; ".join(cons_fail) if cons_fail else "逐页标记/块溯源/指针一致/同 run 锚成立")

    # E-2（Owner 2026-11-15 裁决）：任意 reliable=false 单元 → 整卷 FAIL，
    # 即使其他检查 PASS；普通 WARN 且全部单元可靠 → WARN（保留继续）；
    # 不得把无差别 WARN 升级为 FAIL。
    unreliable = {uid: fl for uid, fl in unit_flags.items() if not fl.get("reliable", True)}
    has_fail = any(c["status"] == "fail" for c in checks)
    has_warn = any(c["status"] == "warn" for c in checks)
    if unreliable:
        checks.append({
            "id": "G8_volume_reliability", "status": "fail",
            "detail": f"整卷阻断：{len(unreliable)} 个不可靠单元 {sorted(unreliable)}（全部列入 unit_flags）",
        })
        has_fail = True
    elif has_warn:
        checks.append({
            "id": "G8_volume_reliability", "status": "warn",
            "detail": "无不可靠单元；保留既有警告继续",
        })
    else:
        checks.append({"id": "G8_volume_reliability", "status": "pass",
                       "detail": "全部单元 reliable=true"})
    verdict = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")
    return {
        "verdict": verdict,
        "gate_version": GATE_VERSION,
        "mode": mode,
        "checks": checks,
        "unit_flags": unit_flags,
        "unreliable_units": sorted(unreliable),
        "divergence_register": divergence,
        "consumption_proof": proof,
    }