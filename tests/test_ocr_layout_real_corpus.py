# -*- coding: utf-8 -*-
"""Real-corpus layout evidence checks for the PBA chemistry paper.

The artifacts are external run data; skip when this checkout lacks them. The
test pins the Q16 main-stem image relation and the Q18 known-I missing-image
risk without changing any source.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ocr_layout  # noqa: E402

BASE = ROOT.parent / "runs/qcore_prebulk_owner_acceptance_01/production/ocr"
MD = BASE / "化学/化学_2026山东高考真题化学（教师版）(1).md"
JL = BASE / "化学/化学_2026山东高考真题化学（教师版）(1).ocr_raw.jsonl"


@pytest.mark.skipif(not (MD.is_file() and JL.is_file()), reason="PBA OCR corpus absent")
def test_q16_main_stem_image_is_evidence_inline():
    layout = ocr_layout.build_layout_evidence(MD.read_text(encoding="utf-8"), JL)
    hit = [p for p in layout["placements"] if p.get("block_id") == 7 and p.get("page") == 5]
    assert hit, "Q16 main-stem image block not found"
    p = hit[0]
    assert p["relation"] == "inline"
    assert p["md_line"] == 266
    assert p["text_line"] == 264
    assert p["echo"] is True
    assert "inline_image_after_text_in_md" in p["risks"]
    assert "math_echo_adjacent_image" in p["risks"]


@pytest.mark.skipif(not (MD.is_file() and JL.is_file()), reason="PBA OCR corpus absent")
def test_q18_known_i_math_echo_is_missing_image_risk():
    layout = ocr_layout.build_layout_evidence(MD.read_text(encoding="utf-8"), JL)
    risks = [r for r in layout["risks"] if r["kind"] == "math_echo_without_image"]
    assert any(r.get("page") == 7 and r.get("block_id") == 12 for r in risks)
    # No JSON image block exists at the known-I row; extraction must not
    # silently synthesize one.
    assert not any(p.get("page") == 7 and p.get("text_block_id") == 12 for p in layout["placements"])
