# -*- coding: utf-8 -*-
"""Phase C #1 回归：印刷题号抽取覆盖 OCR 转义点 `\\.`（O2 根因）。

冻结验收：
- 7 个历史 NULL 单元 stem（`1\\.`…`19\\.`）可解析出印刷题号；
- 全角 `．` / 半角 `.` / 顿号仍工作；
- provenance=source_line；identity 字段分离不被破坏。
"""
import re

import pytest

import question_identity as qi
from phase2_identity_backfill import printed_from_stem

# 实测来自 chem-2018 包 paper.md 的 7 个 NULL 单元首行
ESCAPED_STEMS = [
    (r"1\. 2017年，我国科学家实现了二氧化碳高稳定性加氢合成甲醇", 1),
    (r"9\. 丝绸之路贸易中的下列商品，主要成分属于合金的是", 9),
    (r"13\. 下列营养物质中，不能发生水解反应的是", 13),
    (r"14\. 下列属于取代反应的是", 14),
    (r"15\. 下列方法能用来鉴别甲烷和乙烯的是", 15),
    (r"18\. 下列事实不能用元素周期律知识解释的是", 18),
    (r"19\. 控制变量是科学研究的重要方法。", 19),
]

PLAIN_STEMS = [
    ("2．下列各组元素中，属于同一周期的是", 2),
    ("8．下列物质中，含有离子键的是", 8),
    ("10. 羰基硫（COS）可用于合成除草剂和杀虫剂", 10),
    ("1. （4分）农历九月初九是重阳节", 1),
    ("1、顿号形式", 1),
    ("26．答案区标题", 26),
]


@pytest.mark.parametrize("line,expect", ESCAPED_STEMS + PLAIN_STEMS)
def test_printed_line_extracts_number(line, expect):
    m = qi.PRINTED_LINE.match(line)
    assert m is not None, f"failed to match: {line!r}"
    assert int(m.group(1)) == expect


def test_printed_line_rejects_non_number():
    assert qi.PRINTED_LINE.match("no number here") is None
    assert qi.PRINTED_LINE.match("甲、乙、丙") is None


@pytest.mark.parametrize("line,expect", ESCAPED_STEMS)
def test_printed_from_stem_escaped_dot_source_line(line, expect):
    u = {"stem_lines": [1, 1], "question_numbers": [expect]}
    pn, prov = printed_from_stem(u, [line])
    assert prov == "source_line"
    assert pn == [expect]


def test_printed_from_stem_unknown_when_no_prefix():
    u = {"stem_lines": [1, 1], "question_numbers": [5]}
    pn, prov = printed_from_stem(u, ["没有题号前缀的题干"])
    assert pn is None
    assert prov == "unknown"


def test_identity_fields_stay_separate():
    """全局题号 / 印刷题号 / unit_id 是不同字段，不得混用。"""
    u = {
        "unit_id": "U-req1",
        "question_numbers": [26],  # 全局
        "stem_lines": [1, 1],
    }
    pn, prov = printed_from_stem(u, [r"1\. （3分）中国首款完全自主知识产权"])
    assert pn == [1]  # 印刷
    assert prov == "source_line"
    assert u["question_numbers"] == [26]  # 全局不变
    assert u["unit_id"] == "U-req1"
