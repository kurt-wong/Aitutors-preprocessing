# -*- coding: utf-8 -*-
"""Composite options evidence transport (授权：只修 transport，不拆子题)。

已证实缺口：Producer composite 分支对 choice 单元不声明 options，导致
V3 `required_for_choice` 失败（options missing for choice type）。
本文件锁定 `_expand_composite_option_spans` 的确定性行为。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402


GEO_LIKE = [
    "第一部分选择题（共50分）",                     # 1
    "“卡西尼号”太空探测器…据此完成1-2题。",          # 2 material
    "1\\. 与 “卡西尼号” 探测的天体系统级别相同的是",  # 3
    "",                                              # 4
    "A. 地月系 B. 太阳系 C. 银河系 D. 总星系",        # 5 Q1 options
    "",                                              # 6
    "2. 为推断土星卫星上是否存在生命，需要寻找的最关键证据是该卫星",  # 7
    "",                                              # 8
    "A. 体积适当 B. 质量适中 C. 有大气层 D. 有液态水",  # 9 Q2 options
]


def _comp(uid="U1-2", qns=(1, 2), qtype="single_choice", **kw):
    u = {
        "unit_id": uid,
        "unit_type": "composite_question",
        "question_numbers": list(qns),
        "original_question_type": qtype,
        "material_lines": [2, 2],
        "questions_lines": [2, 9],
        "answer_lines": [1, 1],
    }
    u.update(kw)
    return u


class TestCompositeOptionExpansion:
    def test_choice_composite_declares_options_from_questions_lines(self):
        man = {"units": [_comp()]}
        notes = rp._expand_composite_option_spans(man, GEO_LIKE)
        opts = man["units"][0]["options"]
        assert [o["label"] for o in opts] == ["A", "B", "C", "D"]
        # first-occurrence: Q1 options sit on L5
        assert all(o["start_line"] == 5 and o["end_line"] == 5 for o in opts)
        assert any("U1-2" in n for n in notes)

    def test_non_choice_composite_untouched(self):
        man = {"units": [_comp(uid="U-P2-1", qns=(51,), qtype="short_answer")]}
        rp._expand_composite_option_spans(man, GEO_LIKE)
        assert "options" not in man["units"][0]

    def test_existing_options_not_overwritten(self):
        u = _comp()
        u["options"] = [{"label": "X", "start_line": 5, "end_line": 5}]
        man = {"units": [u]}
        rp._expand_composite_option_spans(man, GEO_LIKE)
        assert man["units"][0]["options"][0]["label"] == "X"

    def test_options_lines_short_circuit(self):
        u = _comp(options_lines=[5, 5])
        man = {"units": [u]}
        rp._expand_composite_option_spans(man, GEO_LIKE)
        # options_lines present → this helper leaves it to _expand_option_spans
        assert "options" not in man["units"][0]

    def test_no_markers_no_declaration(self):
        lines = ["材料", "1. 题干", "没有选项字母"]
        man = {"units": [_comp(questions_lines=[1, 3], material_lines=[1, 1])]}
        rp._expand_composite_option_spans(man, lines)
        assert "options" not in man["units"][0]

    def test_multi_choice_and_true_false_also_covered(self):
        for qt in ("multiple_choice", "true_false"):
            man = {"units": [_comp(qtype=qt)]}
            rp._expand_composite_option_spans(man, GEO_LIKE)
            assert [o["label"] for o in man["units"][0]["options"]] == ["A", "B", "C", "D"]

    def test_standalone_unit_not_touched(self):
        u = {
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_numbers": [1], "original_question_type": "single_choice",
            "stem_lines": [3, 3], "questions_lines": [3, 5],
        }
        man = {"units": [u]}
        rp._expand_composite_option_spans(man, GEO_LIKE)
        assert "options" not in u

    def test_tight_packed_labels_on_one_line(self):
        # 版式 A.①②B.①④C.②③D.③④（地理实测）
        lines = ["材料", "4. 题干", "A.①②B. ①④C. ②③D. ③④"]
        man = {"units": [_comp(qns=(4,), material_lines=[1, 1], questions_lines=[1, 3])]}
        rp._expand_composite_option_spans(man, lines)
        opts = man["units"][0]["options"]
        assert [o["label"] for o in opts] == ["A", "B", "C", "D"]
        assert all(o["start_line"] == 3 for o in opts)

    def test_cross_line_options(self):
        lines = ["材料", "1. 题干", "A. 软流层 B. 岩石圈", "C．下地幔 D．外地核"]
        man = {"units": [_comp(qns=(1,), material_lines=[1, 1], questions_lines=[1, 4])]}
        rp._expand_composite_option_spans(man, lines)
        opts = {o["label"]: o["start_line"] for o in man["units"][0]["options"]}
        assert opts == {"A": 3, "B": 3, "C": 4, "D": 4}

    def test_pipeline_hook_invoked(self):
        """process_file 路径必须调用 composite expansion（与 standalone 扩展并列）。"""
        import inspect
        src = inspect.getsource(rp.process_file)
        assert "_expand_composite_option_spans" in src
