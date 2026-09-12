# -*- coding: utf-8 -*-
"""锚点顺序/嵌套/分离契约(固化 R24-A3 + R24-B1)。"""
import re

import reslice_pipeline as rp


def _anchor_order(man, n_lines=600):
    lines = [f"line{i}" for i in range(1, n_lines + 1)]
    out = rp.compile_anchor(lines, man, "fake.md", None)
    return [m.group(1) for m in
            re.finditer(r"<!-- META:answer:(start|end):1 -->", out)]


def test_inverted_produces_end_before_start():
    """R24-A3 实测复现:未兜底的倒置区间,end 先于 start 输出(协议破坏)。"""
    man = {"units": [{"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_numbers": [1], "stem_lines": [10, 20],
                      "answer_lines": [500, 400]}]}
    order = _anchor_order(man)
    assert order == ["end", "start"]          # 这是"bug 形状"的锁定测试


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
