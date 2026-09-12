# -*- coding: utf-8 -*-
"""clamp_intervals 行号兜底契约(固化 R24-A3/A4 + R25-R7 边界)。"""
import reslice_pipeline as rp


def _man(v):
    return {"units": [{"unit_id": "Q1", "answer_lines": list(v)}]}


def test_normal_untouched():
    m = _man([10, 20])
    assert rp.clamp_intervals(m, 100) == []
    assert m["units"][0]["answer_lines"] == [10, 20]


def test_tail_overflow_clamped():
    m = _man([616, 642])          # R24-A4:首师大化学真实案例形状(源 641 行)
    notes = rp.clamp_intervals(m, 641)
    assert m["units"][0]["answer_lines"] == [616, 641]
    assert len(notes) == 1


def test_inverted_swapped():
    m = _man([500, 400])          # R24-A3:倒置 → 锚点 end 先于 start 的协议破坏源
    rp.clamp_intervals(m, 600)
    assert m["units"][0]["answer_lines"] == [400, 500]


def test_head_underflow_clamped():
    m = _man([0, 5])
    rp.clamp_intervals(m, 100)
    assert m["units"][0]["answer_lines"] == [1, 5]


def test_negative_clamped():
    m = _man([-5, -1])
    rp.clamp_intervals(m, 100)
    assert m["units"][0]["answer_lines"] == [1, 1]


def test_both_overflow_collapses():
    m = _man([150, 200])
    rp.clamp_intervals(m, 100)
    assert m["units"][0]["answer_lines"] == [100, 100]


def test_non_list_ignored():
    m = {"units": [{"unit_id": "Q1", "answer_lines": None,
                    "stem_lines": "bogus", "options_lines": [1]}]}
    assert rp.clamp_intervals(m, 100) == []
    assert m["units"][0]["answer_lines"] is None


def test_all_roles_clamped():
    u = {"unit_id": "Q1", "stem_lines": [300, 400]}
    m = {"units": [u]}
    rp.clamp_intervals(m, 50)
    assert u["stem_lines"] == [50, 50]
