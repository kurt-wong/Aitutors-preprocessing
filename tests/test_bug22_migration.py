# -*- coding: utf-8 -*-
"""BUG-22 迁移工具的确定性算法契约(R31 审查 Phase 3:语义腐蚀防回归)。

锁定三条证据驱动规则:
  shift(分节顺延递推) / answer_key(答案区键位) / keep(分节重编号保持印刷号)。
并锁定 scoped 身份断言:同分节重复必须拒绝,跨分节同号必须放行。
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fix_bug22_renumber as mig  # noqa: E402


def _man(*units):
    return {"units": [dict(u) for u in units]}


def _u(uid, nums, start):
    return {"unit_id": uid, "unit_type": "standalone_question",
            "question_numbers": list(nums), "stem_lines": [start, start],
            "options_lines": None, "answer_lines": None, "explanation_lines": None}


def test_shift_running_max_sequencing():
    """分节重编号(英语试卷形态:听力 1-25 + 笔试又从 1 编)→ 顺延 +25。"""
    man = _man(_u("L1", [1], 10), _u("L25", [25], 20),
               _u("W1", [1], 30), _u("W2-3", [2, 3], 40))
    ops = [{"units": ["W1", "W2-3"], "mode": "shift", "evidence": "t"}]
    ch = mig.apply_ops(man, [""] * 50, ops, None)
    assert man["units"][2]["question_numbers"] == [26]
    assert man["units"][3]["question_numbers"] == [27, 28]
    assert {c["unit_id"] for c in ch} == {"W1", "W2-3"}


def test_shift_no_collision_means_no_change():
    """后分节题号不与前文冲突(天然全卷连续)→ 不动。"""
    man = _man(_u("A1", [1], 10), _u("A2", [2], 20))
    ops = [{"units": ["A1", "A2"], "mode": "shift", "evidence": "t"}]
    mig.apply_ops(man, [""] * 30, ops, None)
    assert man["units"][0]["question_numbers"] == [1]
    assert man["units"][1]["question_numbers"] == [2]


def test_answer_key_from_answer_line():
    """答案区键位(化学合格考形态:N1 印刷 1 但答案区是 '26.【答案】')→ 采用键位。"""
    lines = [""] * 100
    lines[60] = "26. 【答案】(1). 甲 (2). 乙"
    man = _man(_u("N1", [1], 30))
    man["units"][0]["answer_lines"] = [61, 61]
    ops = [{"units": ["N1"], "mode": "answer_key", "evidence": "t"}]
    mig.apply_ops(man, lines, ops, None)
    assert man["units"][0]["question_numbers"] == [26]


def test_keep_preserves_printed_numbers():
    """选考模块/汇编(合法分节重编号)→ 印刷号原样保留。"""
    man = _man(_u("M1-1", [1], 10), _u("M2-1", [1], 50))
    ops = [{"units": ["M1-1", "M2-1"], "mode": "keep", "evidence": "t"}]
    ch = mig.apply_ops(man, [""] * 60, ops, None)
    assert ch == []
    assert man["units"][0]["question_numbers"] == [1]
    assert man["units"][1]["question_numbers"] == [1]


def test_scoped_assertion_rejects_same_section_dup():
    man = _man(_u("Q3", [3], 10), _u("N3", [3], 20))
    for u in man["units"]:
        u["section"] = "一、选择题"
    with pytest.raises(AssertionError):
        mig.assert_scoped_unique(man)


def test_scoped_assertion_allows_cross_section_dup():
    """选考模块形态:两个模块都有印刷题号 1,分节不同 → 合法。"""
    man = _man(_u("M1-1", [1], 10), _u("M2-1", [1], 50))
    man["units"][0]["section"] = "《化学与生活》模块试题"
    man["units"][1]["section"] = "《有机化学基础》模块试题"
    mig.assert_scoped_unique(man)   # 不抛即通过


def test_section_dedup_by_heading_occurrence():
    """同名分节标题(汇编多块'针对训练')按出现次序消歧,块内同号不再冲突。"""
    lines = ["## 针对训练", "1. 甲", "2. 乙", "", "## 针对训练", "1. 丙", "2. 丁"]
    units = [_u("a1", [1], 2), _u("a2", [2], 3), _u("b1", [1], 6), _u("b2", [2], 7)]
    secs = mig.derive_sections(lines, units)
    assert secs[0] == "针对训练#1"
    assert secs[2] == "针对训练#2"
