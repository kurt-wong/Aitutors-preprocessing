# -*- coding: utf-8 -*-
"""R-02 答案源文绑定单测（全部合成用例，零真实试卷内容）。

覆盖 Owner 工单 §12 正/负例 + DSH V-1/V-2/V-3 返修点：
  正例：verbatim 全等/空白归一、compressed 源锚、combined 多源、descriptive、
        composite 归属与 slot 不受影响。
  负例：verbatim 失配/全卷无/错 locator、无 locator、越界、模型纠错/改数字/
        改化学式标记/凭空生成、宽松归一不得掩盖语义变化。
  V-1：区域级候选（R-LABELED-LINE / R-WHOLE / 标签未命中回退）禁止恢复；
       恢复仅限条目绑定候选（标签命中）；同单元重复值守卫。
  V-2：source_value_sha256 = 实写 value_text 哈希。
  V-3：无 locator → value_text=None（与越界同处置）。
红线守卫：模块内不得出现任何模型/网络调用。
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import answer_binding as ab  # noqa: E402


def _sha16(s) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def _unit(**kw):
    u = {"unit_id": kw.get("unit_id", "Q1"), "unit_type": "standalone_question",
         "question_numbers": kw.get("qnums", [1]), "printed_number": kw.get("printed", "1"),
         "answer_evidence": kw.get("ev", {"type": "answer_lines", "lines": [1, 2]}),
         "answers": [], "answer_conflicts": []}
    return u


def _entry(**kw):
    e = {"sub_label": kw.get("sub_label"), "slot_id": kw.get("slot_id"),
         "value_text": kw.get("value"), "asset_ref": kw.get("asset_ref"),
         "form": kw.get("form", "verbatim"), "source_region": kw.get("region", "answer_area"),
         "evidence_lines": kw.get("lines", [1, 2]), "status": kw.get("status", "resolved"),
         "missing_reason": None, "note": None}
    return e


def _bind(lines, unit, entries):
    man = {"units": [unit]}
    unit["answers"] = entries if isinstance(entries, list) else [entries]
    notes = ab.bind_answers(man, lines)
    return unit["answers"], notes


# ---------------- 正例 ----------------

def test_verbatim_exact_candidate_pass():
    lines = ["1. A 2. B 3. C", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}, qnums=[2]),
                    _entry(value="B", lines=[1, 1]))
    b = e["value_binding"]
    assert b["tier"] == "rule_candidate" and b["mismatch_class"] is None
    assert e["value_text"] == "B"
    assert e["model_value_text"] == "B"


def test_verbatim_whitespace_normalized_pass():
    lines = ["【答案】  1464  ", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="1464", lines=[1, 1]))
    assert e["value_binding"]["tier"] in ("rule_candidate", "source_substring")
    assert e["value_text"] == "1464"


def test_compressed_with_source_evidence_pass_keeps_value():
    lines = ["21. B 22. C 23. A", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="21.B 22.C 23.A", form="compressed", lines=[1, 1]))
    b = e["value_binding"]
    assert b["mismatch_class"] is None
    assert e["value_text"] == "21.B 22.C 23.A"
    assert b["tier"] in ("rule_candidate", "source_substring", "compressed_strong")


def test_combined_multi_region_pass():
    lines = ["故选 D。", "", "21.B 22.C", ""]
    u = _unit(ev={"type": "inline_in_explanation", "lines": [1, 3]})
    e1 = _entry(value="故选 D。", form="combined", lines=[1, 1])
    e2 = _entry(value="21.B 22.C", form="combined", lines=[3, 3])
    (a, b), _ = _bind(lines, u, [e1, e2])
    assert a["value_binding"]["mismatch_class"] is None
    assert b["value_binding"]["mismatch_class"] is None


def test_descriptive_with_locator_kept():
    lines = ["参考范文：示例文本内容甲乙丙。", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="示例文本内容甲乙丙。", form="descriptive", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is None
    assert e["value_text"] == "示例文本内容甲乙丙。"


def test_composite_subquestion_attribution_unaffected():
    lines = ["（1）甲答案X", "（2）乙答案Y", ""]
    u = _unit(unit_id="U2", unit_type="composite_question", qnums=[2],
              ev={"type": "answer_lines", "lines": [1, 2]})
    e1 = _entry(value="甲答案X", lines=[1, 1], sub_label="（1）", slot_id="(1)#1")
    e2 = _entry(value="乙答案Y", lines=[2, 2], sub_label="（2）", slot_id="(2)#1")
    (a, b), _ = _bind(lines, u, [e1, e2])
    assert a["value_text"] == "甲答案X" and a["value_binding"]["mismatch_class"] is None
    assert b["value_text"] == "乙答案Y" and b["value_binding"]["mismatch_class"] is None
    assert a["slot_id"] == "(1)#1" and b["slot_id"] == "(2)#1"


# ---------------- 负例（失锚一律不采用模型值） ----------------

def test_verbatim_mismatch_not_adopted():
    lines = ["30. Zn", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}, qnums=[30]),
                    _entry(value="Nn", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "Nn"
    assert e["model_value_text"] == "Nn"


def test_verbatim_absent_from_doc_withheld():
    lines = ["【答案】 苯甲酸", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="乙酸乙酯", lines=[1, 1]))
    b = e["value_binding"]
    assert b["mismatch_class"] in ("absent_from_doc", "in_region_edit", "outside_region")
    assert e["value_text"] != "乙酸乙酯"


def test_verbatim_wrong_locator_flagged():
    lines = ["他题答案 A", "本题答案 B", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="B", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] == "outside_region"
    assert e["value_text"] != "B"


def test_value_without_locator_fail_closed():
    """V-3：无 locator → value_text=None（与越界同处置），不保留模型值冒充源文。"""
    lines = ["无关行", ""]
    u = _unit(ev={"type": "answer_lines", "lines": None})
    u["answer_lines"] = None
    (e,), _ = _bind(lines, u, _entry(value="孤值", lines=None))
    b = e["value_binding"]
    assert b["mismatch_class"] == "no_locator"
    assert e["value_text"] is None
    assert e["status"] == "missing"
    assert e["model_value_text"] == "孤值"


def test_locator_out_of_bounds_fail_closed():
    lines = ["仅一行", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="越界值", lines=[5, 9]))
    assert e["value_binding"]["mismatch_class"] == "locator_invalid"
    assert e["value_text"] is None
    assert e["status"] == "missing"


def test_model_typo_correction_is_mismatch():
    lines = ["32. D South Afria", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}, qnums=[32]),
                    _entry(value="South Africa", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "South Africa"


def test_model_digit_change_is_mismatch():
    lines = ["【答案】 0.110", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="0.100", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "0.100"


def test_model_fabricated_answer_not_source_fact():
    lines = ["【答案】 见解析", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="苯乙烯", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "苯乙烯"


def test_normalization_must_not_mask_semantic_change():
    lines = ["【答案】 增大压强", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="增大压力", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "增大压力"


def test_fabricated_compressed_also_blocked():
    lines = ["21. B 22. C", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="21.A 22.D 23.E", form="compressed", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is not None
    assert e["value_text"] != "21.A 22.D 23.E"


# ---------------- V-1 恢复粒度 ----------------

def test_label_hit_recovery_is_granular():
    """R-SHARED-LABEL 标签命中 → 可恢复，且恢复值=段候选（非整行/整块）。"""
    lines = [r"(1). A \rightleftharpoons B (2). C", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="A ⇌ B", lines=[1, 1], sub_label="（1）"))
    b = e["value_binding"]
    assert b["tier"] == "mismatch_recovered"
    assert b["bind_source"] == ab.ENTRY_BOUND
    assert e["value_text"] != lines[0].strip()          # 不是整行
    assert "rightleftharpoons" in e["value_text"]        # 标记原文忠实（Owner 口径）
    assert e.get("display_value")                        # 另存可读形态


def test_labeled_line_never_recovers():
    """V-1：R-LABELED-LINE 失锚一律 withheld（区域文本≠槽位答案）。"""
    lines = ["【答案】 甲乙丙丁戊己庚辛壬癸", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="错误值XYZ", lines=[1, 1]))
    b = e["value_binding"]
    assert b["rule_id"] == "R-LABELED-LINE"
    assert b["tier"] == "mismatch_withheld"
    assert e["value_text"] is None
    assert e["value_text"] != lines[0].strip()


def test_rwhole_never_recovers():
    lines = ["这是一段没有标签的答案区域文本内容", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="完全不同的声明", lines=[1, 1], form="compressed"))
    b = e["value_binding"]
    assert b["rule_id"] == "R-WHOLE"
    assert b["tier"] == "mismatch_withheld"
    assert e["value_text"] is None


def test_label_miss_fallback_never_recovers():
    """R-SHARED-LABEL 标签未命中（回退单段）→ 区域级，禁止恢复。"""
    lines = ["(7). 值甲 (8). 值乙", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="不存在的值", lines=[1, 1], sub_label="（3）"))
    b = e["value_binding"]
    assert b["tier"] == "mismatch_withheld"
    assert e["value_text"] is None


def test_duplicate_guard_withholds_colliding_recovery():
    """V-1 重复值守卫：恢复值与兄弟槽位重合 → 本槽位 withheld。"""
    lines = ["(1). 相同答案K (2). 其他", ""]
    u = _unit(ev={"type": "answer_lines", "lines": [1, 1]})
    e1 = _entry(value="相同答案K", lines=[1, 1], sub_label="（1）", slot_id="(1)#1")
    e2 = _entry(value="模型乱写", lines=[1, 1], sub_label="（1）", slot_id="(1)#2")
    (a, b), notes = _bind(lines, u, [e1, e2])
    assert a["value_text"] == "相同答案K"                # 原合法条目不动
    bb = b["value_binding"]
    assert bb["tier"] == "mismatch_withheld"            # 恢复撞兄弟 → withheld
    assert bb.get("duplicate_guard") is True
    assert b["value_text"] is None


# ---------------- V-2 哈希一致性 ----------------

def test_source_value_sha_matches_written_value():
    lines = ["【答案】 12345", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="99999", lines=[1, 1]))
    b = e["value_binding"]
    assert e["value_text"] is None                       # R-LABELED-LINE withheld
    assert b["source_value_sha256"] is None
    lines2 = ["(1). 答案甲乙 (2). x", ""]
    (e2,), _ = _bind(lines2, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                     _entry(value="错误", lines=[1, 1], sub_label="（1）"))
    b2 = e2["value_binding"]
    assert b2["tier"] == "mismatch_recovered"
    assert b2["source_value_sha256"] == _sha16(e2["value_text"])
    assert b2["candidate_sha256"] == _sha16(e2["value_text"])


# ---------------- 红线守卫 ----------------

def test_module_has_no_model_or_network_calls():
    src = Path(ab.__file__).read_text(encoding="utf-8")
    for banned in ("urllib", "requests", "httpx", "openai", "anthropic",
                   "chat/completions", "subprocess", "eval(", "exec("):
        assert banned not in src, f"answer_binding 不得包含 {banned}"


def test_display_value_never_used_for_equality():
    lines = [r"$ \alpha $ 甲", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value=r"$ \alpha $ 甲", lines=[1, 1]))
    assert e["value_binding"]["mismatch_class"] is None
    assert e["value_text"] == r"$ \alpha $ 甲"
    assert e.get("display_value") not in (None, r"$ \alpha $ 甲")

# ---------------- 返修补充（V-1 收紧 + 小数剥除缺陷） ----------------

def test_decimal_answer_not_mangled_by_marker_strip():
    """"0.975" 不得被题号前缀剥除吃掉小数点变成 "975"。"""
    lines = ["(1). 甲 (2). 0.975", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="错误声明", lines=[1, 1], sub_label="（2）"))
    b = e["value_binding"]
    assert b["tier"] == "mismatch_recovered"
    assert e["value_text"] == "0.975"


def test_compressed_label_hit_never_recovers():
    """压缩形态是组织形态，机械不可重建——即使标签命中，失锚一律 withheld。"""
    lines = ["(1). 完整源文答案段落内容示例甲乙丙", ""]
    (e,), _ = _bind(lines, _unit(ev={"type": "answer_lines", "lines": [1, 1]}),
                    _entry(value="压缩声明", lines=[1, 1], sub_label="（1）", form="compressed"))
    b = e["value_binding"]
    assert b["tier"] == "mismatch_withheld"
    assert e["value_text"] is None


def test_mutual_collision_all_withheld():
    """同单元多个槽位恢复出同一值 → 全组 withheld（快照语义，不许留最后一个）。"""
    lines = ["(5). 段落答案内容XYZ", ""]
    u = _unit(ev={"type": "answer_lines", "lines": [1, 1]})
    es = [_entry(value=f"错值{i}", lines=[1, 1], sub_label="（5）", slot_id=f"(5)#{i+1}")
          for i in range(3)]
    out, _ = _bind(lines, u, es)
    for e in out:
        assert e["value_binding"]["tier"] == "mismatch_withheld"
        assert e["value_text"] is None
