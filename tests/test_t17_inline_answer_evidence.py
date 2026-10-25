# -*- coding: utf-8 -*-
"""T17/T18: inline answer marker → v2.7 answer_evidence (Producer fallback).

T18 extends to fill_in/short_answer 明文值（故答案为：X）并钉死冲突边界。
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reslice_pipeline import (  # noqa: E402
    _looks_incomplete_multipart,
    _normalize_inline_answer_evidence,
    _unique_answer_conclusion,
    _unique_choice_marker,
    verify_fill_in_form,
)


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


def test_unique_marker_rejects_ambiguous_or_missing():
    assert _unique_choice_marker("【解答】没有标记") is None
    assert _unique_choice_marker("故选：A 故选：B") is None
    assert _unique_choice_marker("") is None
    assert _unique_choice_marker("答案：A 答案：C") is None


def test_fill_in_values_extracted():
    assert _unique_answer_conclusion("故答案为：x = -1。") == "x = -1"
    assert _unique_answer_conclusion("故答案为： $ 2\\sqrt{2} $") == "$ 2\\sqrt{2} $"
    assert _unique_answer_conclusion("故答案为1或2.") == "1或2"
    assert _unique_answer_conclusion("故答案为：1464.") == "1464"


def test_narrative_answer_word_not_a_conclusion():
    assert _unique_answer_conclusion("即可得到答案.") is None
    assert _unique_answer_conclusion("故选项A正确：") is None
    assert _unique_answer_conclusion("利用定义求解即可得到答案；") is None


def test_same_line_conflict_not_migrated():
    """T18 冲突边界：同行冲突标记不得只挑一个干净标记。"""
    lines = ["故答案为：A 故答案为：B", "【点评】略"]
    man = {"units": [_unit(al=[1, 2])]}
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_same_line_letter_and_value_conflict():
    lines = ["故选：A 故答案为：1464"]
    man = {"units": [_unit(al=[1, 1])]}
    before = copy.deepcopy(man)
    _normalize_inline_answer_evidence(man, lines)
    assert man == before


def test_cross_line_conflict_not_migrated():
    lines = ["故答案为：1464", "故选：B."]
    man = {"units": [_unit(al=[1, 2])]}
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_same_line_two_identical_markers_still_conflict():
    # 同行两个标记（即使值相同）也 fail-closed，不挑一个
    assert _unique_answer_conclusion("故选：A. 故选：A.") is None


def test_normalize_emits_inline_ae_for_unique_marker():
    lines = ["1.", "【考点】代数", "【分析】略", "【解答】过程", "故选：A.", "【点评】基础题"]
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


def test_normalize_emits_fill_in_value():
    lines = ["11.【分析】略", "【解答】过程", "故答案为：x = -1。", "【点评】略"]
    man = {"units": [_unit(uid="Q11", al=[1, 4], qtype="fill_in")]}
    _normalize_inline_answer_evidence(man, lines)
    u = man["units"][0]
    assert u["answer_evidence"]["value"] == "x = -1"
    assert u["answer_evidence"]["lines"] == [3, 3]
    assert u["answer_lines"] is None
    assert u["explanation_lines"] == [1, 4]


def test_normalize_keeps_existing_explanation_lines():
    lines = ["x", "故选：B.", "y"]
    man = {"units": [_unit(al=[1, 3], et=[1, 3])]}
    _normalize_inline_answer_evidence(man, lines)
    assert man["units"][0]["explanation_lines"] == [1, 3]


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
    assert _normalize_inline_answer_evidence(man, lines) == []
    assert man == before


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
    assert _normalize_inline_answer_evidence(man, lines) == []
    assert man == before


def test_normalize_skips_shared_answer_table_without_per_unit_marker():
    lines = ["<table>1.A 2.B 3.C 4.D</table>"]
    man = {"units": [_unit(uid="Q1", al=[1, 1]), _unit(uid="Q2", al=[1, 1])]}
    before = copy.deepcopy(man)
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man == before
    assert notes == []


def test_normalize_ignores_body_letters_not_answer_markers():
    lines = ["对于 A，错误。对于 B，错误。对于 D，错误。", "故选：C."]
    man = {"units": [_unit(al=[1, 2])]}
    _normalize_inline_answer_evidence(man, lines)
    assert man["units"][0]["answer_evidence"]["value"] == "C"


def test_normalize_requires_valid_range():
    lines = ["故选：A."]
    man = {"units": [_unit(al=[5, 9])]}
    before = copy.deepcopy(man)
    assert _normalize_inline_answer_evidence(man, lines) == []
    assert man == before


# ---- T19: fill_in 形态 + 多问不完整保护 ----


def test_fill_in_five_validated_forms():
    d = "$"
    assert verify_fill_in_form("x = -1") is True
    assert verify_fill_in_form(f"{d} 2\\sqrt{{2}} {d}") is True
    assert verify_fill_in_form(f"{d} (-1,0) {d}") is True
    assert verify_fill_in_form("1或2") is True
    assert verify_fill_in_form("1464") is True


def test_fill_in_form_fail_closed_out_of_scope():
    assert verify_fill_in_form("") is False
    assert verify_fill_in_form("【解答】很长的过程") is False
    assert verify_fill_in_form("这是一个自然语言长答案" * 5) is False
    assert verify_fill_in_form("故选：A") is False


def test_multipart_block_detected():
    assert _looks_incomplete_multipart("（Ⅰ）foo（Ⅱ）bar 故答案为：x") is True
    assert _looks_incomplete_multipart("（1）第一问\n（2）第二问") is True
    assert _looks_incomplete_multipart("（Ⅰ）a\n（Ⅱ）b\n（Ⅲ）c") is True


def test_statement_circled_numbers_not_multipart():
    """①②③④ 是命题序号，不是小问（T19 Q16/17/22）。"""
    assert _looks_incomplete_multipart("判断①正确；判断②错误 故选：D.") is False
    assert _looks_incomplete_multipart("①a正确 ②b错误 ③c正确 ④d错误") is False


def test_math_f1gx_not_multipart():
    """f(1)/g(x)/(1) 出现在公式中时不得误判为多问（T19 Q6/Q8）。"""
    assert _looks_incomplete_multipart("g(1)=3 f(1)=1 g(-1)=-f(1)+2") is False
    assert _looks_incomplete_multipart("f(x) 在区间 [1,5] 上 f (1) = 2-1 =1") is False


def test_single_part_not_blocked():
    assert _looks_incomplete_multipart("故答案为：x = -1。") is False
    assert _looks_incomplete_multipart("11.【分析】略 故答案为：1464.") is False


def test_multipart_unit_does_not_extract_single_value():
    """T16 Q28 形态：（Ⅰ）（Ⅱ）+ 文末一个故答案为 → 不得抽成单值整题答案。"""
    d = "$"
    lines = [
        "28.",
        "（Ⅰ）第一问结论",
        "（Ⅱ）第二问结论",
        f"故答案为： {d}\\frac{{\\sqrt{{2}}}}{{2}} {d}。",
    ]
    man = {"units": [_unit(uid="Q28", al=[1, 4], qtype="short_answer")]}
    notes = _normalize_inline_answer_evidence(man, lines)
    assert man["units"][0].get("answer_evidence") is None
    assert any("multi-part" in n for n in notes)
