# -*- coding: utf-8 -*-
"""G2-A 方案 A：确定性 MD 行 ↔ OCR-JSON 块证据映射。

Owner 裁决约束（2026-11-15）：
- 只读本轮 OCR 产物（*.md 与 *.ocr_raw.jsonl）；不重新 OCR、不重写 Markdown；
- 按现有 JSON 契约解析实际字段（page/blocks/lines/text/coords）；
- 程序化建立 MD 行 → JSON 块映射，允许一对多/多对一；
- 无法确定的映射保留显式 unmapped 状态，不强行匹配、不由 LLM 猜测；
- 输出仅为证据引用（页码/块号/坐标），不在注解中复制 OCR 原文。

页界约定：MD 以独立 ``---`` 行分页（与 reslice_pipeline.annotate_img_boxes
同一规则，保证与现有页码计数自洽）。

匹配策略（确定性，两遍）：
  1. exact    —— NFKC + 去 HTML 标签 + 去全部空白后子串匹配；
  2. folded   —— 对 MD 侧再折叠 Markdown 结构字符（# * ` |）后重试；
  3. 其余保留 unmapped_block / line_unmapped，不做模糊猜测。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

__all__ = [
    "load_ocr_pages",
    "split_md_pages",
    "build_line_evidence",
    "annotate_json_evidence",
    "evidence_digest",
]

_HTML_RE = re.compile(r"<(?:/?[a-zA-Z!][^<>]*)>")  # M-4/K-3：只认真标签，勿吞公式比较符（同 json_struct_verify 口径）
_MD_DECOR_RE = re.compile(r"[#*`|]")
_MD_DECOR_LINE_RE = re.compile(r"^\s{0,3}(#{1,6}\s+|>\s?|[-*+]\s+|\d+\.\s+)")


def normalize_text(s: str) -> str:
    """有限规范化（与 json_struct_verify._normalize_text 同口径）：
    Unicode NFKC + 去 HTML 标签 + 去全部空白。"""
    s = unicodedata.normalize("NFKC", s or "")
    s = _HTML_RE.sub("", s)
    s = re.sub(r"\s+", "", s)
    return s


def _fold_md_decor(s: str) -> str:
    """折叠 Markdown 结构字符（仅用于匹配，不改源文本）：# * ` | 与列表前缀。"""
    s = _MD_DECOR_LINE_RE.sub("", s)
    s = _MD_DECOR_RE.sub("", s)
    return s


def _parse_bbox(raw) -> list[int] | None:
    """block_bbox/block_polygon_points 在原始返回中是字符串化的列表。"""
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        vals = raw
    else:
        try:
            vals = json.loads(str(raw))
        except Exception:
            return None
    if isinstance(vals, list) and len(vals) >= 4 and all(isinstance(x, (int, float)) for x in vals[:4]):
        return [int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3])]
    if isinstance(vals, list) and vals and isinstance(vals[0], (list, tuple)):
        xs = [p[0] for p in vals]
        ys = [p[1] for p in vals]
        return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
    return None


def load_ocr_pages(jsonl_path: str | Path) -> list[dict]:
    """解析 ocr_raw.jsonl → 页序列（顺序=batch_convert 拼接 all_md 的顺序）。

    契约：每行 = 一次 OCR 响应 record {logId,result,errorCode,errorMsg}；
    result.layoutParsingResults[] 逐页；页内 prunedResult.parsing_res_list[]
    为块：{block_label, block_content, block_bbox, block_id, block_order,
    group_id, block_polygon_points}。
    """
    pages: list[dict] = []
    for line in Path(jsonl_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("errorCode") not in (0, "0", None):
            raise ValueError(f"OCR record errorCode={rec.get('errorCode')}: {rec.get('errorMsg')}")
        for lpr in (rec.get("result") or {}).get("layoutParsingResults") or []:
            pr = lpr.get("prunedResult") or {}
            blocks = []
            for b in pr.get("parsing_res_list") or []:
                blocks.append({
                    "block_id": b.get("block_id"),
                    "block_order": b.get("block_order"),
                    "group_id": b.get("group_id"),
                    "block_label": b.get("block_label"),
                    "bbox": _parse_bbox(b.get("block_bbox")),
                    "content": b.get("block_content") or "",
                })
            pages.append({
                "page_no": len(pages) + 1,
                "width": pr.get("width"),
                "height": pr.get("height"),
                "blocks": blocks,
                # OCR-JSON 的 markdown.images 是页内图片引用 → URL 的原始映射；
                # 供布局/内联图证据使用，不进入文本行映射。
                "images": (lpr.get("markdown") or {}).get("images") or {},
            })
    return pages


def split_md_pages(text: str) -> list[dict]:
    """按独立 ``---`` 行切页（与 annotate_img_boxes 同规则）。

    返回 [{page_no, start_line, end_line, text}]，行号为全文 1-based。
    """
    lines = text.splitlines()
    segs: list[dict] = []
    cur: list[tuple[int, str]] = []
    page_no = 1

    def _flush():
        nonlocal cur, page_no
        if cur:
            segs.append({
                "page_no": page_no,
                "start_line": cur[0][0],
                "end_line": cur[-1][0],
                "lines": [t for _, t in cur],
            })
            page_no += 1
            cur = []

    for i, ln in enumerate(lines, 1):
        if ln.strip() == "---":
            _flush()
            continue
        cur.append((i, ln))
    _flush()
    return segs


def _match_block_in_page(page_norm: str, char_to_line: list[tuple[int, int, int]],
                         block_norm: str) -> tuple[str, list[int]] | None:
    """在页规范化文本中定位块 → (状态, 行号列表)。找不到返回 None。"""
    if not block_norm:
        return None
    idx = page_norm.find(block_norm)
    if idx < 0:
        return None
    end = idx + len(block_norm)
    line_nos = sorted({ln for cs, ce, ln in char_to_line if cs < end and ce > idx})
    return ("mapped_exact", line_nos) if line_nos else None


def build_line_evidence(text: str, jsonl_path: str | Path) -> dict:
    """建立 MD 行 → JSON 块映射。行号为 text.splitlines() 的 1-based（number_lines 之前）。

    输出（纯证据引用，不复制原文）：
      {
        "lines": {lineno: {"page": int, "block_ids": [...], "bbox": [x0,y0,x1,y1]|None, "status": ...}},
        "unmapped_blocks": [{page_no, block_id, block_label}],
        "unmapped_lines": [lineno, ...],
        "page_count_md": int, "page_count_json": int,
        "page_split_consistent": bool,
        "match_counts": {exact: n, folded: n, unmapped_blocks: n, unmapped_lines: n},
      }
    """
    pages = load_ocr_pages(jsonl_path)
    segs = split_md_pages(text)
    consistent = len(segs) == len(pages)

    lines_out: dict[int, dict] = {}
    unmapped_blocks: list[dict] = []
    skipped_blocks: list[dict] = []
    used_lines: set[int] = set()
    counts = {"mapped_exact": 0, "mapped_folded": 0}

    # 页界一致 → 逐页匹配；不一致 → 整卷单页对待（不强行切页）
    pairs = list(zip(segs, pages)) if consistent else []
    if not consistent:
        # 全卷模式：全部 MD 行 ↔ 全部块（顺序不假设）
        segs2 = [{"page_no": 0, "start_line": 1, "end_line": len(text.splitlines()),
                  "lines": text.splitlines()}]
        all_blocks = [b for p in pages for b in p["blocks"]]
        block_page = {id(b): p["page_no"] for p in pages for b in p["blocks"]}
        pairs = [(segs2[0], {"page_no": 0, "blocks": all_blocks, "_page_of": block_page})]

    for seg, pg in pairs:
        seg_lines: list[str] = seg["lines"]
        base = seg["start_line"] - 1
        # 字符→行 映射（规范化后无缝拼接）
        page_norm_parts: list[str] = []
        char_to_line: list[tuple[int, int, int]] = []
        pos = 0
        for k, ln in enumerate(seg_lines):
            n = normalize_text(ln)
            if n:
                char_to_line.append((pos, pos + len(n), base + k + 1))
                page_norm_parts.append(n)
                pos += len(n)
        page_norm = "".join(page_norm_parts)
        # 第二遍：MD 折叠版
        fold_parts: list[str] = []
        fold_char_to_line: list[tuple[int, int, int]] = []
        pos = 0
        for k, ln in enumerate(seg_lines):
            n = normalize_text(_fold_md_decor(ln))
            if n:
                fold_char_to_line.append((pos, pos + len(n), base + k + 1))
                fold_parts.append(n)
                pos += len(n)
        fold_norm = "".join(fold_parts)

        blocks = pg["blocks"] if pg else []
        page_of = pg.get("_page_of") if pg else {}
        for b in sorted(blocks, key=lambda x: (x.get("block_order") is None, x.get("block_order"))):
            bn = normalize_text(b.get("content"))
            if not bn:
                # 空文本块/纯结构性块：预期无文本可映射，单列不计未映射（3.2）
                skipped_blocks.append({
                    "page_no": pg["page_no"] if pg else None,
                    "block_id": b.get("block_id"),
                    "block_label": b.get("block_label"),
                    "class": "empty_or_structural",
                })
                continue
            hit = _match_block_in_page(page_norm, char_to_line, bn)
            status = "mapped_exact"
            if hit is None:
                hit = _match_block_in_page(fold_norm, fold_char_to_line, bn)
                status = "mapped_folded"
            real_page = page_of.get(id(b), pg["page_no"] if pg and pg.get("page_no") else None) \
                if pg and pg.get("_page_of") else (pg["page_no"] if pg else None)
            if hit is None:
                unmapped_blocks.append({
                    "page_no": real_page,
                    "block_id": b.get("block_id"),
                    "block_label": b.get("block_label"),
                })
                continue
            counts[status] += 1
            for ln_no in hit[1]:
                used_lines.add(ln_no)
                rec = lines_out.setdefault(ln_no, {
                    "page": real_page, "block_ids": [], "bbox": None, "status": status,
                })
                if b.get("block_id") is not None and b["block_id"] not in rec["block_ids"]:
                    rec["block_ids"].append(b["block_id"])
                if b.get("bbox"):
                    bb = b["bbox"]
                    rec["bbox"] = bb if rec["bbox"] is None else [
                        min(rec["bbox"][0], bb[0]), min(rec["bbox"][1], bb[1]),
                        max(rec["bbox"][2], bb[2]), max(rec["bbox"][3], bb[3]),
                    ]

    total_lines = len(text.splitlines())
    unmapped_lines = [i for i in range(1, total_lines + 1) if i not in used_lines]
    return {
        "lines": lines_out,
        "unmapped_blocks": unmapped_blocks,
        "skipped_blocks": skipped_blocks,
        "unmapped_lines": unmapped_lines,
        "page_count_md": len(segs),
        "page_count_json": len(pages),
        "page_split_consistent": consistent,
        "match_counts": {
            "mapped_exact": counts["mapped_exact"],
            "mapped_folded": counts["mapped_folded"],
            "unmapped_blocks": len(unmapped_blocks),
            "skipped_blocks": len(skipped_blocks),
            "unmapped_lines": len(unmapped_lines),
        },
    }


def annotate_json_evidence(text: str, evidence: dict, only_mapped: bool = True) -> str:
    """把证据标注注入行尾（内存操作，不改盘上 Markdown）。

    形如 `` 〔j p3 b7,b8 box 1,2-3,4〕``；与 annotate_img_boxes 的
    ``〔p… box …〕`` 同风格。only_mapped 时跳过未映射行（其保持显式空标注）。
    """
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        rec = evidence.get("lines", {}).get(i)
        if rec:
            ids = ",".join(str(x) for x in rec["block_ids"]) if rec["block_ids"] else "-"
            box = ""
            if rec.get("bbox"):
                x0, y0, x1, y1 = rec["bbox"]
                box = f" box {x0},{y0}-{x1},{y1}"
            ln = f"{ln} 〔j p{rec['page']} b{ids}{box}〕"
        elif not only_mapped:
            ln = f"{ln} 〔j unmapped〕"
        out.append(ln)
    return "\n".join(out)


def evidence_digest(evidence: dict) -> str:
    """映射结果指纹（annotation_meta 留痕 + 门禁复算比对用）。"""
    canon = json.dumps(
        {k: evidence[k] for k in (
            "lines", "unmapped_blocks", "skipped_blocks", "unmapped_lines",
            "page_count_md", "page_count_json", "page_split_consistent")},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def unit_evidence_pointers(evidence: dict, units: list[dict]) -> dict:
    """单元级证据指针（只记来源定位，不复制原文）。

    units 为 manifest units（含 *_lines 行区间字段）；输出
    {unit_id: {"pages": [...], "block_ids": [...], "line_span": [s,e]}}。
    """
    out: dict[str, dict] = {}
    for u in units or []:
        uid = u.get("unit_id")
        spans = [u.get(r) for r in (
            "stem_lines", "options_lines", "answer_lines", "explanation_lines",
            "extra_lines", "material_lines", "questions_lines")]
        lns: set[int] = set()
        for sp in spans:
            if isinstance(sp, list) and len(sp) == 2 and all(isinstance(x, int) for x in sp):
                lns.update(range(max(1, sp[0]), sp[1] + 1))
        pages: set[int] = set()
        blocks: set[int] = set()
        for n in lns:
            rec = evidence.get("lines", {}).get(n)
            if not rec:
                continue
            if rec.get("page") is not None:
                pages.add(rec["page"])
            blocks.update(rec.get("block_ids") or [])
        out[str(uid)] = {
            "pages": sorted(pages),
            "block_ids": sorted(blocks),
            "line_span": [min(lns), max(lns)] if lns else None,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="确定性 MD 行 ↔ OCR-JSON 块证据映射")
    ap.add_argument("--md", required=True)
    ap.add_argument("--json", required=True, dest="jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--annotate-out", help="注入证据标注后的文本输出（可选，仅验证用）")
    args = ap.parse_args()
    text = Path(args.md).read_text(encoding="utf-8", errors="replace")
    ev = build_line_evidence(text, args.jsonl)
    ev["md_sha256"] = hashlib.sha256(Path(args.md).read_bytes()).hexdigest()
    ev["json_sha256"] = hashlib.sha256(Path(args.jsonl).read_bytes()).hexdigest()
    ev["map_sha256"] = evidence_digest(ev)
    Path(args.out).write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.annotate_out:
        Path(args.annotate_out).write_text(annotate_json_evidence(text, ev), encoding="utf-8")
    mc = ev["match_counts"]
    print(f"pages md={ev['page_count_md']} json={ev['page_count_json']} "
          f"consistent={ev['page_split_consistent']} | exact={mc['mapped_exact']} "
          f"folded={mc['mapped_folded']} unmapped_blocks={mc['unmapped_blocks']} "
          f"unmapped_lines={mc['unmapped_lines']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
