# -*- coding: utf-8 -*-
"""Deterministic OCR layout evidence from Markdown + OCR-JSONL.

Owner task QCORE-OCR-EXTRACTION-FIDELITY-01: use the structured OCR JSON
(block bbox / label / order / markdown.images) together with the OCR
Markdown, instead of relying on Markdown line order alone.

This module is read-only: it does not rewrite the source Markdown, OCR JSONL,
Manifest, images or Question revisions.  It produces placement evidence and
explicit risks.  The Producer may attach the evidence to the prompt/Manifest;
a risk is never silently "fixed" here.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from json_evidence_map import load_ocr_pages, split_md_pages, build_line_evidence

__all__ = [
    "build_layout_evidence",
    "annotate_layout_evidence",
    "layout_digest",
]

_IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"')
_BBOX_RE = re.compile(r"_box_(\d+)_(\d+)_(\d+)_(\d+)")
_ECHO_RE = re.compile(
    r"\\left\s*(?:\\langle|\(|\[)\s*\\begin\{array\}\{c\}"
    r"[^$]{0,120}\\end\{array\}"
)


def _bbox_of_ref(ref: str) -> list[int] | None:
    m = _BBOX_RE.search(ref.replace("\\", "/"))
    if not m:
        return None
    return [int(g) for g in m.groups()]


def _overlap(a0: int, a1: int, b0: int, b1: int) -> float:
    inter = max(0, min(a1, b1) - max(a0, b0))
    denom = min(max(1, a1 - a0), max(1, b1 - b0))
    return inter / denom


def _page_line_map(text: str) -> dict[int, int]:
    """line -> page_no for Markdown lines (same split rule as Producer)."""
    out: dict[int, int] = {}
    for seg in split_md_pages(text):
        for n in range(seg["start_line"], seg["end_line"] + 1):
            out[n] = seg["page_no"]
    return out


def _line_images(text: str) -> list[dict]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for ref in _IMG_RE.findall(line):
            if ref.startswith(("http://", "https://", "data:")):
                continue
            out.append({"line": n, "ref": ref, "bbox": _bbox_of_ref(ref)})
    return out


def _text_blocks(pages: list[dict]) -> list[dict]:
    out = []
    for page in pages:
        for b in page["blocks"]:
            if b.get("block_label") in ("text", "paragraph_title", "figure_title") and b.get("bbox"):
                out.append({
                    "page": page["page_no"],
                    "block_id": b.get("block_id"),
                    "block_label": b.get("block_label"),
                    "block_order": b.get("block_order"),
                    "bbox": b["bbox"],
                    "content": b.get("content") or "",
                })
    return out


def build_layout_evidence(md_text: str, jsonl_path: str | Path) -> dict:
    """Return page/image placements + explicit risks.

    Relations:
      inline          image vertically inside/overlaps a text block and its
                      horizontal span intersects that block;
      block_before    image is above the nearest text block;
      block_after     image is below the nearest text block;
      block_unmapped  no text block candidate.
    """
    pages = load_ocr_pages(jsonl_path)
    line_page = _page_line_map(md_text)
    md_images = _line_images(md_text)
    # Evidence line mapping gives block_id -> MD line for text blocks.
    ev = build_line_evidence(md_text, jsonl_path)
    block_line: dict[tuple[int, int], int] = {}
    for ln, rec in ev.get("lines", {}).items():
        for bid in rec.get("block_ids") or []:
            block_line[(rec.get("page"), bid)] = ln

    # page-level MD images
    md_by_page: dict[int, list[dict]] = {}
    for im in md_images:
        pg = line_page.get(im["line"])
        if pg is not None:
            md_by_page.setdefault(pg, []).append(im)

    placements: list[dict] = []
    risks: list[dict] = []
    used_md_lines: set[int] = set()
    text_blocks = _text_blocks(pages)

    for page in pages:
        pno = page["page_no"]
        # JSON image blocks: label=image, with bbox (order may be None).
        blocks = [b for b in page["blocks"] if b.get("block_label") == "image" and b.get("bbox")]
        page_md = md_by_page.get(pno, [])
        for b in blocks:
            bbox = b["bbox"]
            # Match MD ref by exact bbox first, then nearest bbox (same page).
            cand = [im for im in page_md if im.get("bbox") == bbox]
            if not cand:
                cand = sorted(
                    (im for im in page_md if im.get("bbox")),
                    key=lambda im: sum(abs(x - y) for x, y in zip(im["bbox"], bbox)),
                )
                cand = cand[:1] if cand else []
            md = cand[0] if cand else None
            if md:
                used_md_lines.add(md["line"])
            # nearest text block by vertical overlap, then distance.
            best = None
            for t in (x for x in text_blocks if x["page"] == pno):
                tb = t["bbox"]
                vo = _overlap(bbox[1], bbox[3], tb[1], tb[3])
                # Require some vertical intersection; same-row images need > 0.5.
                if vo <= 0:
                    continue
                h_over = _overlap(bbox[0], bbox[2], tb[0], tb[2])
                score = (vo, h_over)
                if best is None or score > best[0]:
                    best = (score, t)
            relation = "block_unmapped"
            text = None
            text_line = None
            if best:
                t = best[1]
                tb = t["bbox"]
                vo = _overlap(bbox[1], bbox[3], tb[1], tb[3])
                inside_x = bbox[0] >= tb[0] - 8 and bbox[2] <= tb[2] + 8
                if vo >= 0.5 and inside_x:
                    relation = "inline"
                elif bbox[1] < tb[1]:
                    relation = "block_before"
                else:
                    relation = "block_after"
                text = t
                text_line = block_line.get((pno, t["block_id"]))
            item = {
                "page": pno,
                "block_id": b.get("block_id"),
                "block_order": b.get("block_order"),
                "bbox": bbox,
                "md_line": md["line"] if md else None,
                "ref": md["ref"] if md else None,
                "relation": relation,
                "text_block_id": text.get("block_id") if text else None,
                "text_line": text_line,
                "echo": bool(_ECHO_RE.search(text.get("content") or "")) if text else False,
                "risks": [],
            }
            if not md:
                item["risks"].append("json_image_missing_in_md")
            if relation == "inline" and md and text_line and md["line"] > text_line:
                item["risks"].append("inline_image_after_text_in_md")
            if item["echo"]:
                item["risks"].append("math_echo_adjacent_image")
            placements.append(item)
            for r in item["risks"]:
                risks.append({"kind": r, "page": pno, "block_id": b.get("block_id"),
                              "md_line": md["line"] if md else None, "text_line": text_line})

    # MD images with no JSON image block: explicit (do not silently drop).
    json_bboxes = {
        (p["page_no"], tuple(b["bbox"]))
        for p in pages for b in p["blocks"]
        if b.get("block_label") == "image" and b.get("bbox")
    }
    for im in md_images:
        pg = line_page.get(im["line"])
        key = (pg, tuple(im["bbox"])) if im.get("bbox") and pg else None
        if key is not None and key in json_bboxes:
            continue
        # exact bbox may be absent because OCR filename uses footer_image etc.;
        # only flag when JSON has no image with that bbox at all.
        if key not in json_bboxes:
            risks.append({"kind": "md_image_without_json_image_block",
                          "page": pg, "md_line": im["line"], "ref": im["ref"]})

    # Text math echo with no adjacent image: Q18 known-I style.
    for p in pages:
        pno = p["page_no"]
        page_placements = [x for x in placements if x["page"] == pno]
        for b in p["blocks"]:
            c = b.get("content") or ""
            if not c or not _ECHO_RE.search(c) or not b.get("bbox"):
                continue
            # already covered by a placement with echo?
            covered = any(x.get("text_block_id") == b.get("block_id") for x in page_placements)
            if not covered:
                risks.append({"kind": "math_echo_without_image",
                              "page": pno, "block_id": b.get("block_id"),
                              "bbox": b["bbox"]})

    # Deterministic grouping hint for multi-image rows (Q5): same page and
    # vertical band, with figure_title blocks; not a fix, just evidence.
    groups: list[dict] = []
    by_page: dict[int, list[dict]] = {}
    for im in md_images:
        pg = line_page.get(im["line"])
        if pg is not None:
            by_page.setdefault(pg, []).append(im)
    for pg, ims in by_page.items():
        if len(ims) < 2:
            continue
        for im in ims:
            if not im.get("bbox"):
                continue
            y0, y1 = im["bbox"][1], im["bbox"][3]
            same = [x for x in ims if x.get("bbox") and abs(x["bbox"][1] - y0) <= 100]
            if len(same) >= 2:
                groups.append({"page": pg, "lines": sorted({x["line"] for x in same}),
                               "y_band": [min(x["bbox"][1] for x in same),
                                          max(x["bbox"][3] for x in same)]})
                by_page[pg] = [x for x in ims if x not in same]  # avoid duplicates
                break

    summary = {
        "pages": len(pages),
        "images": len(placements),
        "inline": sum(1 for x in placements if x["relation"] == "inline"),
        "risks": len(risks),
        "multi_image_groups": len(groups),
    }
    return {
        "pages": len(pages),
        "placements": placements,
        "risks": risks,
        "multi_image_groups": groups,
        "summary": summary,
        "line_page": line_page,
    }


def annotate_layout_evidence(text: str, layout: dict) -> str:
    """Append compact layout evidence to Markdown-visible lines (prompt only)."""
    by_line: dict[int, list[dict]] = {}
    for p in layout.get("placements", []):
        if p.get("md_line"):
            by_line.setdefault(p["md_line"], []).append(p)
    risk_by_line: dict[int, list[str]] = {}
    for r in layout.get("risks", []):
        if r.get("md_line"):
            risk_by_line.setdefault(r["md_line"], []).append(r["kind"])
    out = []
    for n, ln in enumerate(text.splitlines(), 1):
        if n in by_line:
            tags = []
            for p in by_line[n]:
                tags.append(f"L p{p['page']} b{p['block_id']} rel={p['relation']}"
                            f" textL={p['text_line']} bbox={p['bbox']}")
            ln = ln + "  〔" + " | ".join(tags) + "〕"
        if n in risk_by_line:
            ln = ln + "  〔RISK " + ",".join(sorted(set(risk_by_line[n]))) + "〕"
        out.append(ln)
    return "\n".join(out)


def layout_digest(layout: dict) -> str:
    canon = json.dumps(
        {"placements": layout.get("placements"), "risks": layout.get("risks"),
         "multi_image_groups": layout.get("multi_image_groups")},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
