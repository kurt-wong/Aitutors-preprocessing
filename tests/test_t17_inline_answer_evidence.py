# -*- coding: utf-8 -*-
"""T17: inline answer marker → v2.7 answer_evidence (Producer deterministic fallback)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reslice_pipeline import _normalize_inline_answer_evidence, _unique_choice_marker  # noqa: E402


def _unit(uid="Q1", al=None, ae=None, et=None, qtype="single_choice"):
    u = {
        "unit_id": uid,
        "unit_type": "standalone_question",
        "question_numbers": [1],
        "original_question_type": qtype,
        "answer_lines": al,
    }
    if ae is not None:
        u["answer_evidence"] = ae
    if et is not None:
        u["explanation_lines"] = et
    return u


def test_unique_marker_detects_gu_xuan_and_da_an():
    assert _unique_choice_marker("故选：D.") == "D"
    assert _unique_choice_marker("故选C.") == "C"
    assert _unique_choice_marker("答案：B") == "B"
    assert _unique_choice_marker("故答案为：A.") == "A"


def test_unique_marker_rejects_ambiguous_or_missing():
    assert _unique_choice_marker("【解答】没有标记") is None
    assert _unique_choice_marker("故选：A 故选：B") is None
    assert _unique_choice_marker("") is None
    assert _unique_choice_marker("答案：A 答案：C") is None


def test_normalize_emits_inline_ae_for_unique_marker():
    lines = [
        "1.",
        "【考点】代数",
        "【分析】略",
        "【解答】过程",
        "故选：A.",
        "【点评】基础题",
    ]
    man = {"units": [_unit(al=[1, 6])]}
    notes = _normalize_inline_answer_evidence(man, lines)
    u = man["units"][0]
    assert u["answer_evidence"] == {
        "type": "inline_in_explanation",
        "lines": [5, 5],
        "value": "A",
        "shared": False,
    }
    assert u["answer_lines"] is None
    assert u["explanation_lines"] == [1, 6]
    assert notes and "A" in notes[0]


def test_normalize_keeps_existing_explanation_lines():
    lines = ["x", "故选：B.", "y"]
    man = {"units": [_unit(al=[1, 3], et=[1, 3])]}
    _normalize_inline_answer_evidence(man, lines)
    u = man["units"][0]
    assert u["explanation_lines"] == [1, 3]
    assert u["answer_evidence"]["value"] == "B"


def test_normalize_skips_existing_ae_value():
    lines = ["故选：D."]
    man = {
        "units": [
            _unit(
                al=[1, 1],
                ae={"type": "answer_lines", "lines": [1, 1], "value": "D", "shared": False},
            )
        ]
    }
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_normalize_skips_absent_ae():
    lines = ["故选：D."]
    man = {
        "units": [
            _unit(
                al=[1, 1],
                ae={"type": "absent", "lines": None, "value": None, "shared": False},
            )
        ]
    }
    before = copy.deepcopy(man)
    _normalize_inline_answer_evidence(man, lines)
    assert man == before


def test_normalize_skips_no_marker():
    lines = ["【解答】过程很长", "没有结论"]
    man = {"units": [_unit(al=[1, 2])]}
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_normalize_skips_conflicting_markers():
    lines = ["故选：A.", "故选：B."]
    man = {"units": [_unit(al=[1, 2])]}
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_normalize_skips_shared_answer_table_without_per_unit_marker():
    # 合格考形态：多题共享答案表行，无本单元唯一结论标记
    lines = ["<table>1.A 2.B 3.C 4.D</table>"]
    man = {
        "units": [
            _unit(uid="Q1", al=[1, 1]),
            _unit(uid="Q2", al=[1, 1]),
        ]
    }
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_normalize_ignores_body_letters_not_answer_markers():
    # 解析正文讨论 A/B/C/D，但唯一答案标记是 故选：C
    lines = [
        "对于 A，错误。对于 B，错误。对于 D，错误。",
        "故选：C.",
    ]
    man = {"units": [_unit(al=[1, 2])]}
    _normalize_inline_answer_evidence(man, lines)
    assert man["units"][0]["answer_evidence"]["value"] == "C"
    assert man["units"][0]["answer_evidence"]["lines"] == [2, 2]


def test_normalize_requires_valid_range():
    lines = ["故选：A."]
    man = {"units": [_unit(al=[5, 9])]}  # out of range
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []
