# -*- coding: utf-8 -*-
"""答案表解析器与选项标签检测单测（主线定向修复）。

覆盖：分页 / 全角字母 / 多题号 / 无表 / 伪标签；
以及 Q2/Q17 伪选项标签、Q20 续行合并。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reslice_pipeline as rp  # noqa: E402


# ---------- _parse_labeled_answer_table ----------

def test_no_table_returns_empty():
    assert rp._parse_labeled_answer_table("没有表格，只有正文答案 B") == {}
    assert rp._parse_labeled_answer_table("") == {}


def test_fake_labels_not_parsed():
    # 首列不是「题号/答案」标签对，或行不成对 → 不产出映射
    block = (
        "<table><tr><td>名称</td><td>甲</td><td>乙</td></tr>"
        "<tr><td>能量</td><td>1</td><td>2</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {}


def test_basic_labeled_table():
    block = (
        "<table><tr><td>题号</td><td>1</td><td>2</td><td>3</td></tr>"
        "<tr><td>答案</td><td>B</td><td>A</td><td>D</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {1: "B", 2: "A", 3: "D"}


def test_fullwidth_letters_kept_in_parser():
    # 解析层保留全角；归一化层负责折叠
    block = (
        "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
        "<tr><td>答案</td><td>Ａ</td><td>Ｂ</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {1: "Ａ", 2: "Ｂ"}


def test_multi_question_number_label_skipped():
    # 「9-11」不是纯数字题号 → 不产出该列；纯数字列仍可解析
    block = (
        "<table><tr><td>题号</td><td>9-11</td><td>12</td></tr>"
        "<tr><td>答案</td><td>D</td><td>A</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {12: "A"}


def test_pagination_multiple_tables_merged():
    # 分页：两段表各自成表，映射应合并
    block = (
        "第2页\n"
        "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
        "<tr><td>答案</td><td>B</td><td>C</td></tr></table>\n"
        "第3页\n"
        "<table><tr><td>题号</td><td>3</td><td>4</td></tr>"
        "<tr><td>答案</td><td>D</td><td>A</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {
        1: "B", 2: "C", 3: "D", 4: "A",
    }


def test_score_row_ignored():
    block = (
        "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
        "<tr><td>答案</td><td>B</td><td>A</td></tr>"
        "<tr><td>分数</td><td>1</td><td>1</td></tr></table>"
    )
    assert rp._parse_labeled_answer_table(block) == {1: "B", 2: "A"}


# ---------- _normalize_answer_table_evidence ----------

def _man_unit(**kw):
    u = {
        "unit_id": "Q1",
        "question_numbers": [1],
        "answer_lines": [1, 1],
        "answer_evidence": None,
    }
    u.update(kw)
    return u


def test_normalize_writes_answer_table_evidence():
    line = (
        "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
        "<tr><td>答案</td><td>D</td><td>B</td></tr></table>"
    )
    man = {"units": [_man_unit()]}
    notes = rp._normalize_answer_table_evidence(man, [line])
    ae = man["units"][0]["answer_evidence"]
    assert ae["type"] == "answer_table"
    assert ae["value"] == "D"
    assert ae["shared"] is True
    assert notes


def test_normalize_fullwidth_folded_to_ascii():
    line = (
        "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
        "<tr><td>答案</td><td>Ｂ</td><td>Ａ</td></tr></table>"
    )
    man = {"units": [_man_unit()]}
    rp._normalize_answer_table_evidence(man, [line])
    assert man["units"][0]["answer_evidence"]["value"] == "B"


def test_normalize_multi_qn_stays_unknown():
    line = (
        "<table><tr><td>题号</td><td>9</td><td>10</td><td>11</td></tr>"
        "<tr><td>答案</td><td>D</td><td>C</td><td>A</td></tr></table>"
    )
    man = {"units": [_man_unit(question_numbers=[9, 10, 11], unit_id="U-9-11")]}
    rp._normalize_answer_table_evidence(man, [line])
    assert man["units"][0]["answer_evidence"] in (None, {})


def test_normalize_no_table_untouched():
    man = {"units": [_man_unit()]}
    rp._normalize_answer_table_evidence(man, ["答案：D"])
    assert not man["units"][0].get("answer_evidence")


def test_normalize_existing_value_untouched():
    man = {"units": [_man_unit(answer_evidence={"type": "inline", "value": "C"})]}
    rp._normalize_answer_table_evidence(
        man, ["<table><tr><td>题号</td><td>1</td></tr><tr><td>答案</td><td>D</td></tr></table>"]
    )
    assert man["units"][0]["answer_evidence"]["value"] == "C"


# ---------- _detect_option_labels：伪标签 / 续行 ----------

def test_q2_element_symbol_F_not_label():
    # `C. F、Mg` — F 是选项内容（氟），不得成为选项标签
    lines = ["2. 下列各组元素中，属于同一周期的是",
             "A. Na、P B. N、Cl C. F、Mg D. O、S"]
    labs = [x[0] for x in rp._detect_option_labels(lines, 2, 2)]
    assert labs == ["A", "B", "C", "D"], labs


def test_q17_electron_dot_H_not_label():
    # `B. H: O: H` — H 是电子式内容，不得成为选项标签
    lines = [
        "17. 下列物质的电子式书写正确的是",
        "A. Cl: Cl",
        "B. H: O: H",
        "C. Na: Cl:",
        "D. H: N: H",
    ]
    labs = [x[0] for x in rp._detect_option_labels(lines, 2, 5)]
    assert labs == ["A", "B", "C", "D"], labs


def test_q20_continuation_merged_into_D():
    # 「还原反应」是 D「涉及了氧」的续行，不得成为选项 E
    lines = [
        "20. 硫在自然界的循环过程如右图所示",
        "A. 火山喷发、森林火灾会产生SO $ _{2} $",
        "B. 氢、氧两种元素没有参与硫的",
        "C. 工厂产生的烟气应经脱硫处理后再排放",
        "D. 硫在自然界的循环过程中，涉及了氧",
        "还原反应",
    ]
    spans = rp._detect_option_labels(lines, 2, 6)
    labs = [x[0] for x in spans]
    assert labs == ["A", "B", "C", "D"], labs
    d = next(x for x in spans if x[0] == "D")
    assert d[2] == 6, d  # 续行并入 D


def test_rule_a_still_recovers_missing_D():
    # 少于 4 个标签时，尾部无标签内容仍可补 D（Q23 形态）
    lines = [
        "23. 下列反应的离子方程式书写不正确的是",
        "A．金属钠与水",
        "B．氯化钠溶液与硝酸银溶液：",
        "C．稀盐酸与碳酸钙",
        " $  \\mathrm{H}^{+} + \\mathrm{SO}_{4}^{2-} $",
    ]
    labs = [x[0] for x in rp._detect_option_labels(lines, 2, 5)]
    assert labs == ["A", "B", "C", "D"], labs


def test_image_letter_option_spans():
    lines = [
        "16. 图 8 中正确反映 U 和 Q 关系的图像是",
        '<div><img src="a.jpg" /></div>',
        "<div>A</div>",
        '<div><img src="b.jpg" /></div>',
        "<div>B</div>",
        '<div><img src="c.jpg" /></div>',
        "<div>C</div>",
        '<div><img src="d.jpg" /></div>',
        "<div>D</div>",
    ]
    man = {"units": [{
        "unit_id": "Q16",
        "original_question_type": "single_choice",
        "stem_lines": [1, 9],
        "options": None,
        "options_lines": None,
        "question_numbers": [16],
    }]}
    notes = rp._expand_image_letter_option_spans(man, lines)
    u = man["units"][0]
    assert [o["label"] for o in u["options"]] == ["A", "B", "C", "D"]
    assert u["stem_lines"] == [1, 1]
    assert notes


def test_prune_phantom_labels_F_and_H():
    # LLM 错把 F/H 声明成选项；源文检测只认 A-D 时应剪掉
    lines = [
        "x",
        "A. Na、P B. N、Cl C. F、Mg D. O、S",
    ]
    man = {"units": [{
        "unit_id": "Q2",
        "options_lines": [2, 2],
        "options": [
            {"label": "A", "start_line": 2, "end_line": 2},
            {"label": "B", "start_line": 2, "end_line": 2},
            {"label": "C", "start_line": 2, "end_line": 2},
            {"label": "F", "start_line": 2, "end_line": 2},
            {"label": "D", "start_line": 2, "end_line": 2},
        ],
    }]}
    notes = rp._expand_option_spans(man, lines)
    labs = [o["label"] for o in man["units"][0]["options"]]
    assert labs == ["A", "B", "C", "D"], labs
    assert any("pruned" in n for n in notes)


def test_prune_phantom_E_merges_continuation():
    lines = [
        "x",
        "A. aaa",
        "B. bbb",
        "C. ccc",
        "D. 涉及了氧",
        "还原反应",
    ]
    man = {"units": [{
        "unit_id": "Q20",
        "options_lines": [2, 6],
        "options": [
            {"label": "A", "start_line": 2, "end_line": 2},
            {"label": "B", "start_line": 3, "end_line": 3},
            {"label": "C", "start_line": 4, "end_line": 4},
            {"label": "D", "start_line": 5, "end_line": 5},
            {"label": "E", "start_line": 6, "end_line": 6},
        ],
    }]}
    rp._expand_option_spans(man, lines)
    u = man["units"][0]
    labs = [o["label"] for o in u["options"]]
    assert labs == ["A", "B", "C", "D"], labs
    d = next(o for o in u["options"] if o["label"] == "D")
    assert d["end_line"] == 6, d


def test_no_prune_when_detection_misses_real_label():
    # 检测只到 A-C 时，不得剪掉已声明的 D
    lines = ["x", "A. aaa", "B. bbb", "C. ccc"]
    man = {"units": [{
        "unit_id": "Q1",
        "options_lines": [2, 4],
        "options": [
            {"label": "A", "start_line": 2, "end_line": 2},
            {"label": "B", "start_line": 3, "end_line": 3},
            {"label": "C", "start_line": 4, "end_line": 4},
            {"label": "D", "start_line": 4, "end_line": 4},
        ],
    }]}
    rp._expand_option_spans(man, lines)
    labs = [o["label"] for o in man["units"][0]["options"]]
    assert "D" in labs, labs
