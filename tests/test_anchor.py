# -*- coding: utf-8 -*-
"""锚点顺序/嵌套/分离契约(固化 R24-A3 + R24-B1)。"""
import re

import pytest

import reslice_pipeline as rp


def _anchor_order(man, n_lines=600):
    lines = [f"line{i}" for i in range(1, n_lines + 1)]
    out = rp.compile_anchor(lines, man, "fake.md", None)
    return [m.group(1) for m in
            re.finditer(r"<!-- META:answer:(start|end):1 -->", out)]


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷形状(R24-B2/T-02):compile_anchor 不自防御倒置区间,"
           "生产路径靠 clamp_intervals 前置归一化。此测试语义是"
           "'当前仍然是错的'——若哪天 compile_anchor 内建兜底,strict xfail 会失败,"
           "提醒把本测试翻转为正向断言。")
def test_inverted_produces_end_before_start():
    """R24-A3 实测复现:未兜底的倒置区间,end 先于 start 输出(协议破坏)。

    不作为正向 PASS 条件(ChatGPT 二轮 T-02):这是负向回归文档,
    锁的是"缺陷仍在"而不是"缺陷是对的"。
    """
    man = {"units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_numbers": [1], "stem_lines": [10, 20],
                      "answer_lines": [500, 400]}]}
    order = _anchor_order(man)
    assert order == ["start", "end"]   # 断言正确形状;当前实现给不出 → xfail


def test_clamped_inverted_produces_start_before_end():
    """兜底后:锚点恢复 start→end。"""
    man = {"units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_numbers": [1], "stem_lines": [10, 20],
                      "answer_lines": [500, 400]}]}
    rp.clamp_intervals(man, 600)
    assert _anchor_order(man) == ["start", "end"]


def test_out_of_range_never_emitted():
    """R24-A4:越界行号(源 100 行报 150)兜底后,end 锚点落在文件内。"""
    lines = [f"L{i}" for i in range(1, 101)]
    man = {"units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_numbers": [1], "stem_lines": [10, 20],
                      "answer_lines": [95, 150]}]}
    rp.clamp_intervals(man, len(lines))
    assert man["units"][0]["answer_lines"] == [95, 100]
    # compile_anchor 能正常产出(不因越界崩溃)
    out = rp.compile_anchor(lines, man, "fake.md", None)
    assert "META:answer:start:1" in out
    assert "META:answer:end:1" in out


def test_composite_nested_anchor_ordering():
    """material ⊂ questions:锚点应 material 先开后关(合法嵌套)。"""
    lines = [f"L{i}" for i in range(1, 21)]
    man = {"units": [{"unit_id": "U1", "unit_type": "composite_question",
                      "question_numbers": [1, 2],
                      "material_lines": [5, 8], "questions_lines": [3, 12]}]}
    out = rp.compile_anchor(lines, man, "fake.md", None)
    mat_open = out.index("META:material:start:1,2")
    q_open = out.index("META:questions:start:1,2")
    q_close = out.index("META:questions:end:1,2")
    mat_close = out.index("META:material:end:1,2")
    # 语义嵌套(按 DEPTH 排序):questions(L3开)先于 material(L5开)开启,
    # 但 material(L8闭)先于 questions(L12闭)闭合——即锚点序列交叉开启、
    # material 在 questions 区间内部闭合,构成合法嵌套。
    assert q_open < mat_open < mat_close < q_close


def test_separated_material_no_crossing():
    """R24-B1:听力式分离结构(material 在卷末、questions 在开头)锚点不交叉。"""
    lines = [f"L{i}" for i in range(1, 21)]
    man = {"units": [{"unit_id": "U1", "unit_type": "composite_question",
                      "question_numbers": [1],
                      "material_lines": [15, 18], "questions_lines": [3, 6]}]}
    out = rp.compile_anchor(lines, man, "fake.md", None)
    q_close = out.index("META:questions:end:1")
    mat_open = out.index("META:material:start:1")
    assert q_close < mat_open            # questions 全部闭合后 material 才开启
