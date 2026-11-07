# -*- coding: utf-8 -*-
"""T20-BF: Producer answer_completeness declaration tests."""
import sys

sys.path.insert(0, r"D:\Project\Papers\scripts")
sys.stdout.reconfigure(encoding="utf-8")

from reslice_pipeline import (  # noqa: E402
    _answer_completeness_from_evidence,
    _answer_value_placeholder_class,
    _assign_answer_completeness,
    _looks_incomplete_multipart,
)


def test_full_when_value_and_span_not_multipart():
    lines = ["1. 题干", "【答案】", "故答案为：1464"]
    u = {
        "unit_id": "Q1",
        "answer_evidence": {"type": "inline_in_explanation", "lines": [3, 3], "value": "1464"},
        "answer_lines": None,
    }
    assert _answer_completeness_from_evidence(u, lines) == "full"


def test_partial_when_multipart_single_value():
    lines = [
        "28. 题干",
        "（Ⅰ）r=___",
        "（Ⅱ）求 r",
        "28.",
        "【解答】（Ⅰ）……（Ⅱ）……",
        "故答案为： $ \\frac{\\sqrt{2}}{2} $。",
    ]
    u = {
        "unit_id": "Q28",
        "answer_evidence": {
            "type": "inline_in_explanation",
            "lines": [6, 6],
            "value": "$ \\frac{\\sqrt{2}}{2} $",
        },
        "answer_lines": [4, 6],
    }
    # multipart block + short single value → partial
    assert _answer_completeness_from_evidence(u, lines) == "partial"


def test_unknown_when_range_only():
    lines = ["26.", "【解答】（Ⅰ）……（Ⅱ）……"]
    u = {"unit_id": "Q26", "answer_evidence": None, "answer_lines": [1, 2]}
    assert _answer_completeness_from_evidence(u, lines) == "unknown"


def test_unknown_when_multipart_guard_without_value():
    lines = ["28.", "（Ⅰ）（Ⅱ）答案块"]
    u = {"unit_id": "Q28", "answer_evidence": None, "answer_lines": [1, 2]}
    assert _looks_incomplete_multipart("\n".join(lines))
    assert _answer_completeness_from_evidence(u, lines) == "unknown"


def test_partial_when_truncated():
    lines = ["26.", "解：tan θ = - $ \\frac{"]
    u = {"unit_id": "Q26", "answer_evidence": None, "answer_lines": [1, 2]}
    assert _answer_completeness_from_evidence(u, lines) == "partial"


def test_missing_field_not_full():
    lines = ["1. 题", "答案"]
    u = {"unit_id": "Q1"}  # no evidence at all
    assert _answer_completeness_from_evidence(u, lines) == "unknown"


def test_assign_writes_all_units():
    man = {
        "units": [
            {"unit_id": "Q1", "answer_evidence": {"lines": [1, 1], "value": "A"}},
            {"unit_id": "Q2", "answer_lines": [1, 1]},
        ]
    }
    lines = ["故答案为：A"]
    notes = _assign_answer_completeness(man, lines)
    assert man["units"][0]["answer_completeness"] == "full"
    assert man["units"][1]["answer_completeness"] in ("unknown", "full", "partial")
    assert notes


# ---- T81 非答案占位语不得声明 full（DSH：math_2021 Q18 / eng_2020 Q67）----


def test_placeholder_class_pure_and_partial():
    assert _answer_value_placeholder_class("答案见解析") == "pure"
    assert _answer_value_placeholder_class("无答案") == "pure"
    assert _answer_value_placeholder_class("略") == "pure"
    assert _answer_value_placeholder_class("（1）答案见解析（2）证明见解析") == "pure"
    assert _answer_value_placeholder_class("（1）见解析；（2）$B_{1}D=\\frac{1}{2}$") == "partial"
    assert _answer_value_placeholder_class("（1）图像见解析；（2）$a \\geq \\frac{11}{2}$") == "partial"
    assert _answer_value_placeholder_class("1464") == "none"
    assert _answer_value_placeholder_class("A") == "none"
    assert _answer_value_placeholder_class("故选：D。") == "none"
    assert _answer_value_placeholder_class("$B_{1}D=\\frac{1}{2}$") == "none"


def test_counterexample_math2021_q18_not_full():
    """math_2021 Q18：源行 18.【答案】答案见解析 → 不得 full。"""
    lines = ["18.【答案】答案见解析", "【解析】……"]
    u = {
        "unit_id": "Q18",
        "answer_evidence": {"type": "inline_in_explanation", "lines": [1, 1], "value": "答案见解析"},
        "answer_lines": [1, 1],
    }
    assert _answer_completeness_from_evidence(u, lines) == "unknown"


def test_counterexample_eng2020_q67_not_full():
    """eng_2020 Q67：源行 ## 【答案】无答案 → 不得 full。"""
    lines = ["## 【答案】无答案", "【解析】书面表达，略。"]
    u = {
        "unit_id": "Q67",
        "answer_evidence": {"type": "inline_in_explanation", "lines": [1, 1], "value": "无答案"},
        "answer_lines": [1, 1],
    }
    assert _answer_completeness_from_evidence(u, lines) == "unknown"


def test_mixed_placeholder_value_is_partial_not_full():
    lines = ["19.【答案】（1）见解析；（2） $ B_{1}D=\\frac{1}{2} $"]
    u = {
        "unit_id": "Q19",
        "answer_evidence": {
            "type": "inline_in_explanation",
            "lines": [1, 1],
            "value": "（1）见解析；（2）$B_{1}D=\\frac{1}{2}$",
        },
        "answer_lines": [1, 1],
    }
    assert _answer_completeness_from_evidence(u, lines) == "partial"


def test_normal_answer_still_full():
    """正常答案仍可通过（不把占位符修复扩大成全面拒发）。"""
    lines = ["1. 题干", "【答案】", "故答案为：1464"]
    u = {
        "unit_id": "Q1",
        "answer_evidence": {"type": "inline_in_explanation", "lines": [3, 3], "value": "1464"},
        "answer_lines": [3, 3],
    }
    assert _answer_completeness_from_evidence(u, lines) == "full"
    u2 = {
        "unit_id": "Q2",
        "answer_evidence": {"type": "answer_table", "lines": [1, 1], "value": "A"},
        "answer_lines": [1, 1],
    }
    lines2 = ["故选：A"]
    assert _answer_completeness_from_evidence(u2, lines2) == "full"


# ==================== TASK-QCC-ANSWER-SEMANTICS-1：语义/证据两轴分离 ====================


def test_snapshot_captures_llm_semantic_before_fixers():
    """轴S：LLM 语义声明在 fixer 触碰前快照，不被推导值静默覆盖。"""
    from reslice_pipeline import _snapshot_llm_semantic_completeness

    man = {
        "units": [
            {"unit_id": "Q7", "answer_evidence": {"lines": [1, 1], "value": "见解析"},
             "answer_completeness": "full"},   # LLM 声明（prompt 4c）
            {"unit_id": "Q8"},                  # LLM 未声明
        ]
    }
    assert _snapshot_llm_semantic_completeness(man) == 1
    u7, u8 = man["units"]
    assert u7["answer_completeness_semantic"] == "full"
    assert u7["answer_completeness_semantic_source"] == "llm_declared"
    assert "answer_completeness_semantic" not in u8


def test_assign_only_writes_evidence_axis():
    """轴E：_assign 只写推导值；轴S 字段不被其改写。"""
    from reslice_pipeline import _snapshot_llm_semantic_completeness

    man = {
        "units": [
            {"unit_id": "Q7", "answer_evidence": {"lines": [1, 1], "value": "见解析"},
             "answer_completeness": "full"}
        ]
    }
    _snapshot_llm_semantic_completeness(man)
    _assign_answer_completeness(man, ["见解析"])
    u = man["units"][0]
    assert u["answer_completeness"] == "unknown"           # 轴E 推导值
    assert u["answer_completeness_semantic"] == "full"      # 轴S 不被覆盖
    assert u["answer_completeness_semantic_source"] == "llm_declared"


def test_axes_agree_still_keeps_semantic_field():
    """两轴一致也保留语义字段（轴S 需独立表达）。"""
    from reslice_pipeline import _snapshot_llm_semantic_completeness

    man = {
        "units": [
            {"unit_id": "Q1", "answer_evidence": {"lines": [1, 1], "value": "1464"},
             "answer_completeness": "full"}
        ]
    }
    _snapshot_llm_semantic_completeness(man)
    _assign_answer_completeness(man, ["故答案为：1464"])
    u = man["units"][0]
    assert u["answer_completeness"] == "full"
    assert u["answer_completeness_semantic"] == "full"


def test_assign_note_still_records_overwrite():
    """审计 warning 保留（(was …) 痕迹不删除）。"""
    man = {
        "units": [
            {"unit_id": "Q17", "answer_evidence": {"lines": [1, 1], "value": "见解析"},
             "answer_completeness": "full"}
        ]
    }
    notes = _assign_answer_completeness(man, ["见解析"])
    assert any("(was 'full')" in n for n in notes)


if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for f in fns:
        try:
            f()
            print("PASS", f.__name__)
            ok += 1
        except Exception:
            print("FAIL", f.__name__)
            traceback.print_exc()
    print(f"{ok}/{len(fns)} passed")
    raise SystemExit(0 if ok == len(fns) else 1)
