# -*- coding: utf-8 -*-
"""T20-BF: Producer answer_completeness declaration tests."""
import sys

sys.path.insert(0, r"D:\Project\Papers\scripts")
sys.stdout.reconfigure(encoding="utf-8")

from reslice_pipeline import (  # noqa: E402
    _answer_completeness_from_evidence,
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
