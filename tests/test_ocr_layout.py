# -*- coding: utf-8 -*-
"""QCORE-OCR-EXTRACTION-FIDELITY-01: layout evidence regression.

These tests use synthetic OCR-JSONL batches. They pin the deterministic
contract only: block bbox/label/order + markdown.images are consumed; source
Markdown is never rewritten; risks are explicit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import ocr_layout  # noqa: E402


def _write_jsonl(tmp_path: Path, page_blocks: list[dict], images: dict[str, str]) -> Path:
    rec = {
        "logId": "test",
        "result": {
            "layoutParsingResults": [{
                "prunedResult": {
                    "width": 1000,
                    "height": 1600,
                    "parsing_res_list": page_blocks,
                },
                "markdown": {"text": "", "images": images},
            }]
        },
    }
    p = tmp_path / "sample.ocr_raw.jsonl"
    p.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def _block(bid: int, label: str, bbox: list[int], content: str = "") -> dict:
    return {
        "block_id": bid,
        "block_order": None,
        "block_label": label,
        "block_bbox": bbox,
        "block_content": content,
        "group_id": 0,
    }


def test_inline_image_after_text_and_math_echo(tmp_path):
    md = "\n".join([
        r"16. CuSiF6 与 $ \left( \begin{array}{c} \text{N} \\ \text{N} \end{array} \right) $（L）通过配位键形成框架。",
        '<div><img src="imgs/img_in_image_box_300_100_360_160.jpg" alt="Image" /></div>',
    ])
    images = {"imgs/img_in_image_box_300_100_360_160.jpg": "https://example.invalid/img.jpg"}
    jl = _write_jsonl(
        tmp_path,
        [
            _block(0, "text", [100, 100, 900, 160], "16. CuSiF6 与 $ \\left( \\begin{array}{c} \\text{N} \\\\ \\text{N} \\end{array} \\right) $（L）通过配位键形成框架。"),
            _block(1, "image", [300, 100, 360, 160], ""),
        ],
        images,
    )
    layout = ocr_layout.build_layout_evidence(md, jl)
    assert layout["summary"]["images"] == 1
    p = layout["placements"][0]
    assert p["relation"] == "inline"
    assert p["text_line"] == 1
    assert p["md_line"] == 2
    assert p["echo"] is True
    assert "inline_image_after_text_in_md" in p["risks"]
    assert "math_echo_adjacent_image" in p["risks"]
    annotated = ocr_layout.annotate_layout_evidence(md, layout)
    assert "rel=inline" in annotated
    assert "math_echo_adjacent_image" in annotated


def test_math_echo_without_image_is_explicit_risk(tmp_path):
    md = r"I. $\left\langle\begin{array}{c}Z \\ Z^{\prime}\end{array}\right\rangle + RBr$"
    jl = _write_jsonl(
        tmp_path,
        [_block(0, "text", [100, 100, 900, 180], r"I. $\left\langle\begin{array}{c}Z \\ Z^{\prime}\end{array}\right\rangle + RBr$")],
        {},
    )
    layout = ocr_layout.build_layout_evidence(md, jl)
    assert layout["summary"]["images"] == 0
    assert any(r["kind"] == "math_echo_without_image" for r in layout["risks"])


def test_multi_image_row_groups_are_evidence_only(tmp_path):
    md = "\n".join([
        '<img src="imgs/img_in_image_box_100_500_160_560.jpg" />',
        '<img src="imgs/img_in_image_box_200_500_260_560.jpg" />',
        '<img src="imgs/img_in_image_box_300_500_360_560.jpg" />',
    ])
    images = {f"imgs/img_in_image_box_{x}_500_{x+60}_560.jpg": "https://example.invalid/i.jpg"
              for x in (100, 200, 300)}
    jl = _write_jsonl(
        tmp_path,
        [_block(i, "image", [x, 500, x + 60, 560], "")
         for i, x in enumerate((100, 200, 300))],
        images,
    )
    layout = ocr_layout.build_layout_evidence(md, jl)
    assert layout["summary"]["multi_image_groups"] == 1
    assert layout["multi_image_groups"][0]["lines"] == [1, 2, 3]
    # evidence only: source md unchanged
    assert md.splitlines()[0].startswith('<img src="imgs/')


def test_md_image_without_json_block_is_flagged(tmp_path):
    md = '<img src="imgs/img_in_image_box_100_100_160_160.jpg" />'
    jl = _write_jsonl(tmp_path, [], {})
    layout = ocr_layout.build_layout_evidence(md, jl)
    assert any(r["kind"] == "md_image_without_json_image_block" for r in layout["risks"])


def test_prompt_declares_layout_evidence_boundary():
    import reslice_pipeline as rp
    text = rp.PROMPT_HEAD
    assert "8c." in text
    assert "math_echo_without_image" in text
    assert "不得据此生成或合成结构图" in text
    assert "不得把 bbox 重叠直接当作 Unit 归属的充分证据" in text
    assert "multi_image_groups" in text

