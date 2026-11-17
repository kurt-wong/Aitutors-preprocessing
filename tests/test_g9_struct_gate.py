# -*- coding: utf-8 -*-
"""G9-STRUCT 定向测试（QC0RE-PHASE3-G3-B · B1，B1-6 测试清单）。

B1-6 清单（重建自实施计划 §7.2/§10.1 + DSH B1 放行条件①②，如与指令原文
有出入以指令为准）：
  T1  absent 态：旧 v3.2 结构（含 12 卷真实 manifest）→ G9 记 na，不 FAIL
  T2  present 合法：新字段完整自洽 → G9 pass
  T3  区间倒置/越界 → FAIL（禁 clamp：不静默修正）
  T4  父子包含破坏（子⊄父 / 小问越出单元）→ FAIL
  T5  引用解析断裂 + §8 文本保真（悬空 parent/材料/答案/图表/covered、
      缺 evidence_locator、basis_text 改写）→ FAIL
  T6  区间交叉 → FAIL；兄弟包含/重合未声明父子 → soft（reliable=false，不 FAIL）
  T7  N-2 枚举锁：basis∋printed_atomicity → FAIL；triage=gt_conflict → FAIL
  T8  uncertainty 原样保留（不改写）→ soft/reliable=false；畸形 uncertainty → FAIL
  T9  禁 clamp：clamp_intervals 不触碰新字段；validate_manifest 新字段 issues
      与 G9 同源（G9-STRUCT 前缀）
  T10 真实阻断案例（DSH 放行条件②）：G2A 真实 manifest 副本注入一处结构缺陷
      → G9 FAIL → 整卷 FAIL → E-1 未写盘；原文件 SHA 不变；合法注入 → 通过。
"""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import reslice_pipeline as rp  # noqa: E402
from json_struct_verify import check_struct_integrity  # noqa: E402

G2A_ROOT = Path(r"D:\Project\AITutors\runs\qcore_phase3_g2a\g2a-20261115-093538")
G2A_MD = G2A_ROOT / "ocr" / "语文" / "2026全国I高考真题语文（教师版）(1).md"
G2A_JSONL = G2A_ROOT / "ocr" / "语文" / "2026全国I高考真题语文（教师版）(1).ocr_raw.jsonl"
G2A_MANIFEST = (G2A_ROOT / "preprocessing" / "语文"
                / "2026全国I高考真题语文（教师版）(1).manifest.json")
EVID_DIR = (Path(r"D:\Project\AITutors\runs\qcore_phase3_g3\manifest_semantics_01")
            / "_dsh" / "b1_g9_evidence")

N_LINES = 40


def _lines():
    ls = [""] * N_LINES
    ls[15] = "阅读下列材料，回答第 3—4 题。"
    ls[16] = "材料内容甲乙丙。"
    ls[18] = "3. 依据材料，下列正确的是（ ）"
    ls[19] = "A. ①"
    ls[20] = "4. 依据材料，错误的是（ ）"
    ls[21] = "A. 甲"
    ls[30] = "3.【答案】C"
    ls[31] = "4.【答案】D"
    return ls


def _unit_ok(uid="U1"):
    """结构完整自洽的 G3 新结构单元（供变异注入）。"""
    return {
        "unit_id": uid,
        "unit_type": "composite_question",
        "question_numbers": [3, 4],
        "material_lines": [16, 17],
        "questions_lines": [19, 22],
        "answer_lines": [31, 32],
        "classification": {"unit_type": "composite", "basis": ["A", "D"]},
        "materials": [{"material_id": "M01", "label": "材料一",
                       "line_start": 16, "line_end": 17}],
        "sub_questions": [
            {"sub_id": "S1", "label": "3.", "label_kind": "printed_number",
             "parent_sub_id": None, "order": 1, "line_start": 19, "line_end": 20,
             "materials_used": ["M01"], "answer_refs": ["A1"], "figure_refs": [],
             "answer_entry_count": 1},
            {"sub_id": "S2", "label": "4.", "label_kind": "printed_number",
             "parent_sub_id": None, "order": 2, "line_start": 21, "line_end": 22,
             "materials_used": ["M01"], "answer_refs": ["A2"], "figure_refs": [],
             "answer_entry_count": 1},
        ],
        "answers": [
            {"slot_id": "A1", "sub_ref": "S1", "evidence_lines": [31, 31],
             "value_text": "C"},
            {"slot_id": "A2", "sub_ref": "S2", "evidence_lines": [32, 32],
             "value_text": "D"},
        ],
        "figures": [{"figure_id": "F1",
                     "evidence": {"line_start": 16, "line_end": 16},
                     "applies_to": ["S1"]}],
        "grouping_statements": [{
            "statement_id": "GS1",
            "basis_text": "阅读下列材料，回答第 3—4 题。",
            "evidence_locator": {"line_start": 16, "line_end": 16},
            "covered_range": "3—4", "covered_sub_ids": ["S1", "S2"],
            "triage": "explicit_grouping", "gt_conflict": False,
        }],
    }


def _man_with(unit):
    return {"units": [unit]}


def _old_unit():
    return {"unit_id": "U1", "unit_type": "composite_question",
            "question_numbers": [3, 4], "material_lines": [16, 17],
            "questions_lines": [19, 22], "answer_lines": [31, 32]}


class TestT1Absent:
    def test_old_unit_is_absent_not_fail(self):
        r = check_struct_integrity(_man_with(_old_unit()), N_LINES)
        assert r["structure_contract"] == "absent"
        assert r["status"] == "na"
        assert r["issues"] == []

    @pytest.mark.skipif(not G2A_ROOT.is_dir(), reason="G2A 产物不可用")
    def test_real_12_manifests_all_absent(self):
        seen = []
        for p in sorted(G2A_ROOT.glob("preprocessing/*/*.manifest.json")):
            man = json.loads(p.read_text(encoding="utf-8"))
            r = check_struct_integrity(man, 10**6)
            assert r["structure_contract"] == "absent", f"{p.name} 不应有新字段"
            assert r["status"] == "na" and r["issues"] == []
            seen.append(p.name)
        assert len(seen) == 12, f"预期 12 卷真实 manifest，实得 {len(seen)}"


class TestT2ValidPass:
    def test_valid_new_struct_pass(self):
        r = check_struct_integrity(_man_with(_unit_ok()), N_LINES, lines=_lines())
        assert r["structure_contract"] == "present"
        assert r["status"] == "pass", r["issues"]
        assert r["soft"] == [], r["soft"]
        assert r["uncertain_units"] == []


class TestT3IntervalIllegal:
    def test_inverted_interval_fails_and_not_clamped(self):
        u = _unit_ok()
        u["sub_questions"][0]["line_start"], u["sub_questions"][0]["line_end"] = 22, 19
        man = _man_with(u)
        before = copy.deepcopy(man)
        r = check_struct_integrity(man, N_LINES)
        assert r["status"] == "fail"
        assert any("倒置" in m for m in r["issues"]), r["issues"]
        # 禁 clamp：检查器只读，倒置区间不得被改写
        assert man == before, "G9 检查器不得修改 man（禁 clamp/禁改写）"

    def test_out_of_bounds_fails(self):
        u = _unit_ok()
        u["sub_questions"][1]["line_end"] = 9999
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("越界" in m for m in r["issues"]), r["issues"]

    def test_material_interval_inverted_fails(self):
        u = _unit_ok()
        u["materials"][0]["line_start"], u["materials"][0]["line_end"] = 17, 16
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("倒置" in m for m in r["issues"])


class TestT4Containment:
    def test_sub_out_of_unit_hull_fails(self):
        u = _unit_ok()
        u["sub_questions"][0]["line_start"], u["sub_questions"][0]["line_end"] = 2, 5
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("越出单元区间" in m for m in r["issues"]), r["issues"]

    def test_child_not_in_parent_fails(self):
        u = _unit_ok()
        u["sub_questions"][1]["parent_sub_id"] = "S1"
        u["sub_questions"][1]["line_start"], u["sub_questions"][1]["line_end"] = 21, 22
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("未包含于父小问" in m for m in r["issues"]), r["issues"]

    def test_parent_cycle_fails(self):
        u = _unit_ok()
        u["sub_questions"][0]["parent_sub_id"] = "S2"
        u["sub_questions"][1]["parent_sub_id"] = "S1"
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("成环" in m for m in r["issues"]), r["issues"]


class TestT5RefsAndFidelity:
    def test_dangling_refs_fail(self):
        u = _unit_ok()
        u["sub_questions"][0]["parent_sub_id"] = "SX"
        u["sub_questions"][0]["materials_used"] = ["MX"]
        u["answers"][0]["sub_ref"] = "SX"
        u["figures"][0]["applies_to"] = ["SX"]
        u["grouping_statements"][0]["covered_sub_ids"] = ["SX"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        joined = " ".join(r["issues"])
        for frag in ("parent_sub_id", "materials_used", "sub_ref",
                     "applies_to", "covered_sub_ids"):
            assert frag in joined, (frag, r["issues"])
        assert joined.count("无法解析") >= 5

    def test_missing_locator_fails(self):
        u = _unit_ok()
        del u["grouping_statements"][0]["evidence_locator"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("缺 evidence_locator" in m for m in r["issues"])

    def test_basis_text_rewritten_fails(self):
        u = _unit_ok()
        u["grouping_statements"][0]["basis_text"] = "这段声明文字被改写了"
        r = check_struct_integrity(_man_with(u), N_LINES, lines=_lines())
        assert r["status"] == "fail"
        assert any("basis_text" in m and "改写" in m for m in r["issues"]), r["issues"]

    def test_label_rewritten_fails(self):
        u = _unit_ok()
        u["sub_questions"][0]["label"] = "第3小问"
        r = check_struct_integrity(_man_with(u), N_LINES, lines=_lines())
        assert r["status"] == "fail"
        assert any("label" in m and "改写" in m for m in r["issues"])


class TestT6Overlap:
    def test_crossing_siblings_fail(self):
        u = _unit_ok()
        u["sub_questions"][0]["line_start"], u["sub_questions"][0]["line_end"] = 19, 21
        u["sub_questions"][1]["line_start"], u["sub_questions"][1]["line_end"] = 20, 22
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("交叉" in m for m in r["issues"]), r["issues"]

    def test_undeclared_nesting_is_soft_not_fail(self):
        u = _unit_ok()
        # S2 ⊂ S1 但未声明父子 → 层级错误族：reliable=false（soft），非 G9 FAIL
        u["sub_questions"][1]["line_start"], u["sub_questions"][1]["line_end"] = 19, 19
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass", r["issues"]
        assert any("未声明父子" in m for m in r["soft"]), r["soft"]
        # 观察项②：soft 归因走 soft_units（uid→msgs），不从文案反解
        assert "U1" in r["soft_units"] and r["soft_units"]["U1"], r["soft_units"]

    def test_equal_interval_siblings_are_note_not_soft(self):
        # 同区间多空位（一行多空/选词填空格子）：完全重合非冲突，只记 note；
        # 槽位身份对/entry_count 一致性另行检查（12 卷 S02/S05/S06 实证形态）
        u = _unit_ok()
        u["sub_questions"][1]["line_start"] = u["sub_questions"][0]["line_start"]
        u["sub_questions"][1]["line_end"] = u["sub_questions"][0]["line_end"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass", r["issues"]
        assert r["soft"] == [], r["soft"]
        assert any("同区间多空位" in n for n in r["notes"]), r["notes"]


class TestG9F1RealLayout:
    """G9-F1 回归（DSH G9 专项）：S01 U1 真实版式——题面 [21,105]、答案 [402,432]、
    中缝 [106,401] 是他单元内容，n_lines=594。hull=[21,432] 含答案区，
    旧包含校验会被架空；现以题面区为界 + 答案/解析相交独立规则。"""

    N = 594

    def _u1(self):
        return {"unit_id": "U1", "unit_type": "composite_question",
                "question_numbers": [1],
                "material_lines": [21, 65], "questions_lines": [21, 105],
                "options_lines": [69, 100], "answer_lines": [402, 432]}

    def _with_sub(self, end):
        u = self._u1()
        u["sub_questions"] = [
            {"sub_id": "S1", "label": None, "label_kind": "unlabeled",
             "parent_sub_id": None, "order": 1,
             "line_start": 21, "line_end": end}]
        return u

    def test_probe_end_105_pass(self):
        r = check_struct_integrity(_man_with(self._with_sub(105)), self.N)
        assert r["status"] == "pass", r["issues"]

    def test_probe_end_300_fails_face_region(self):
        # 溢出题面区 195 行（落进他单元区）→ 必须拦
        r = check_struct_integrity(_man_with(self._with_sub(300)), self.N)
        assert r["status"] == "fail"
        assert any("越出题面区" in m for m in r["issues"]), r["issues"]

    def test_probe_end_432_fails_answer_intersection(self):
        # 一路吃到答案区末尾 → 题面区 + 相交规则双拦
        r = check_struct_integrity(_man_with(self._with_sub(432)), self.N)
        assert r["status"] == "fail"
        joined = " ".join(r["issues"])
        assert "越出题面区" in joined, r["issues"]
        assert "相交" in joined, r["issues"]

    def test_probe_end_433_fails(self):
        r = check_struct_integrity(_man_with(self._with_sub(433)), self.N)
        assert r["status"] == "fail"

    def test_answer_intersection_rule_independent(self):
        # 无题面角色（face=None）时，相交规则独立生效
        u = {"unit_id": "U9", "unit_type": "standalone_question",
             "question_numbers": [9], "answer_lines": [31, 32],
             "sub_questions": [
                 {"sub_id": "S1", "label": None, "label_kind": "unlabeled",
                  "parent_sub_id": None, "order": 1,
                  "line_start": 31, "line_end": 32}]}
        r = check_struct_integrity(_man_with(u), self.N)
        assert r["status"] == "fail"
        assert any("相交" in m for m in r["issues"]), r["issues"]
        assert not any("越出题面区" in m for m in r["issues"]), r["issues"]


class TestT7EnumLockN2:
    def test_printed_atomicity_not_basis_value(self):
        u = _unit_ok()
        u["classification"]["basis"] = ["printed_atomicity"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("printed_atomicity" in m for m in r["issues"])

    def test_gt_conflict_not_triage_value(self):
        u = _unit_ok()
        u["grouping_statements"][0]["triage"] = "gt_conflict"
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("triage" in m for m in r["issues"])
        assert any("gt_conflict" in m for m in r["issues"])

    def test_classification_unit_type_mismatch_fails(self):
        u = _unit_ok()
        u["classification"]["unit_type"] = "standalone"
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("不一致" in m for m in r["issues"])


class TestT8Uncertainty:
    def test_uncertainty_preserved_and_soft(self):
        u = _unit_ok()
        u["uncertainty"] = {"object": "小问边界", "reason": "印刷不清",
                            "affects": ["S1"], "note": "原样保留"}
        man = _man_with(u)
        before = copy.deepcopy(man)
        r = check_struct_integrity(man, N_LINES)
        assert man == before, "uncertainty 不得被改写"
        assert r["status"] == "pass"
        assert r["uncertain_units"] == ["U1"]

    def test_malformed_uncertainty_fails_but_untouched(self):
        u = _unit_ok()
        u["uncertainty"] = ["not-a-dict"]
        man = _man_with(u)
        before = copy.deepcopy(man)
        r = check_struct_integrity(man, N_LINES)
        assert r["status"] == "fail"
        assert man == before

    def test_uncertainty_locator_inverted_fails(self):
        u = _unit_ok()
        u["uncertainty"] = {"object": "区间", "evidence_locator": {"line_start": 9,
                                                                  "line_end": 3}}
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("倒置" in m for m in r["issues"])


class TestT9NoClampSharedChecker:
    def test_clamp_intervals_does_not_touch_new_fields(self):
        u = _unit_ok()
        u["sub_questions"][0]["line_start"], u["sub_questions"][0]["line_end"] = 22, 19
        u["materials"][0]["line_start"], u["materials"][0]["line_end"] = 99, 120
        u["stem_lines"] = [50, 60]  # 旧行为字段：照旧 clamp
        man = _man_with(u)
        notes = rp.clamp_intervals(man, N_LINES)
        assert man["units"][0]["sub_questions"][0]["line_start"] == 22
        assert man["units"][0]["sub_questions"][0]["line_end"] == 19
        assert man["units"][0]["materials"][0]["line_start"] == 99
        assert man["units"][0]["stem_lines"] == [40, 40], notes

    def test_validate_manifest_issues_carry_g9_prefix(self):
        u = _unit_ok()
        u["sub_questions"][1]["line_end"] = 9999
        issues, summary = rp.validate_manifest(_man_with(u), N_LINES, _lines())
        g9_msgs = [i for i in issues if i.startswith("G9-STRUCT:")]
        assert g9_msgs, issues
        assert any("越界" in m for m in g9_msgs)
        assert summary["g9_struct"]["structure_contract"] == "present"
        assert summary["g9_struct"]["status"] == "fail"

    def test_validate_manifest_absent_has_no_g9_issues(self):
        issues, summary = rp.validate_manifest(_man_with(_old_unit()), N_LINES,
                                               _lines())
        assert not [i for i in issues if i.startswith("G9-STRUCT:")]
        assert summary["g9_struct"]["structure_contract"] == "absent"


@pytest.mark.skipif(not G2A_MANIFEST.is_file(), reason="G2A 产物不可用")
class TestG9AnswerBindingRules:
    """12 卷冒烟暴露的规则口径（G3-B 阶段四修正）：
    一问多空 = 同一 sub_ref 多条 answers（常态，非冲突）；同名 slot 跨小问合法
    （槽位身份 = (sub_ref, slot_id) 对）；父小问 answer_entry_count=0 合法；
    答案关联冲突 = 同对重复登记 / sub_ref 与 sub_label 归属矛盾。"""

    def test_entry_count_zero_and_multi_answer_one_sub(self):
        u = {
            "unit_id": "U1", "unit_type": "composite_question",
            "question_numbers": [1],
            "material_lines": [16, 17], "questions_lines": [19, 22],
            "answer_lines": [31, 32],
            "classification": {"unit_type": "composite", "basis": ["A"]},
            "sub_questions": [
                {"sub_id": "S0", "label": None, "label_kind": "unlabeled",
                 "parent_sub_id": None, "order": 1,
                 "line_start": 19, "line_end": 22, "answer_entry_count": 0},
                {"sub_id": "S1", "label": None, "label_kind": "unlabeled",
                 "parent_sub_id": "S0", "order": 2,
                 "line_start": 21, "line_end": 22, "answer_entry_count": 2},
            ],
            "answers": [
                {"slot_id": "A1", "sub_ref": "S1", "evidence_lines": [31, 31]},
                {"slot_id": "A2", "sub_ref": "S1", "evidence_lines": [32, 32]},
            ],
        }
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass", r["issues"]
        assert r["soft"] == [], r["soft"]

    def test_cross_sub_same_slot_id_is_legal(self):
        # 不同小问同名空位（ans#1 型）= 各自小问的第 1 空，槽位身份不同，非冲突
        u = _unit_ok()
        u["answers"][0]["slot_id"] = "X"
        u["answers"][1]["slot_id"] = "X"
        u["sub_questions"][0]["answer_refs"] = ["X"]
        u["sub_questions"][1]["answer_refs"] = ["X"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass", r["issues"]
        assert r["soft"] == [], r["soft"]

    def test_duplicate_slot_pair_is_conflict(self):
        u = _unit_ok()
        u["answers"][1]["sub_ref"] = "S1"
        u["answers"][1]["slot_id"] = u["answers"][0]["slot_id"]  # (S1,A1) 重复登记
        u["sub_questions"][1]["answer_refs"] = ["A1"]
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass", r["issues"]
        assert any("重复登记" in m for m in r["soft"]), r["soft"]

    def test_sub_ref_vs_sub_label_contradiction(self):
        u = _unit_ok()
        # 标签照抄源行（4. 出现在 L21）；sub_label 指 S2 的标签而 sub_ref 指 S1 → 矛盾
        u["answers"][0]["sub_ref"] = "S1"
        u["answers"][0]["sub_label"] = "4."
        r = check_struct_integrity(_man_with(u), N_LINES, lines=_lines())
        assert r["status"] == "pass", r["issues"]
        assert any("矛盾" in m for m in r["soft"]), r["soft"]

    def test_negative_entry_count_fails(self):
        u = _unit_ok()
        u["sub_questions"][0]["answer_entry_count"] = -1
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "fail"
        assert any("answer_entry_count" in m for m in r["issues"])

    def test_entry_count_mismatch_still_soft(self):
        u = _unit_ok()
        u["sub_questions"][0]["answer_entry_count"] = 3  # 实绑 1 条
        r = check_struct_integrity(_man_with(u), N_LINES)
        assert r["status"] == "pass"
        assert any("不一致" in m for m in r["soft"]), r["soft"]

    def test_verbatim_folds_md_escape(self):
        from json_struct_verify import _g9_verbatim_ok
        assert _g9_verbatim_ok("1.", "1\\. 下列对材料相关内容的理解……")
        assert _g9_verbatim_ok("1.", "1. 下列对材料相关内容的理解……")
        assert _g9_verbatim_ok("（1）", "（1）渔为得也……")
        assert not _g9_verbatim_ok("第 3 小问", "3. 依据材料……")


class TestT10RealInjectionBlocking:
    """DSH B1 放行条件②：G2A 真实 manifest 副本注入一处结构缺陷。

    真实源文（ocr md + jsonl）+ 真实 manifest 内容回放；两例注入同构新结构
    （全部 composite_question 单元带 sub_questions），**只差一处缺陷**（倒置区间）：
    缺陷例 G9 FAIL → 整卷 FAIL → E-1 未写盘；合法例 G9 pass → 正式 Manifest 写出。
    G2A 原文件 SHA 前后必须不变。
    """

    def _sha(self):
        return hashlib.sha256(G2A_MANIFEST.read_bytes()).hexdigest()

    def _prepare(self, tmp_path):
        md = tmp_path / G2A_MD.name
        jl = tmp_path / G2A_JSONL.name
        md.write_bytes(G2A_MD.read_bytes())
        jl.write_bytes(G2A_JSONL.read_bytes())
        man = json.loads(G2A_MANIFEST.read_text(encoding="utf-8"))
        return md, jl, man

    @staticmethod
    def _inject(man, defect=None):
        """给全部 composite 单元补同构新结构；defect='inverted' 时只改一处区间。"""
        man = copy.deepcopy(man)
        for u in man["units"]:
            if u.get("unit_type") != "composite_question":
                continue
            u["classification"] = {"unit_type": "composite", "basis": ["A"]}
            q = u.get("questions_lines") or u.get("stem_lines") or u.get("material_lines")
            assert q, f"{u.get('unit_id')} 无可拆区间"
            mid = (q[0] + q[1]) // 2
            u["sub_questions"] = [
                {"sub_id": f"{u.get('unit_id')}-S1", "label": None,
                 "label_kind": "unlabeled", "parent_sub_id": None, "order": 1,
                 "line_start": q[0], "line_end": max(q[0], mid)},
                {"sub_id": f"{u.get('unit_id')}-S2", "label": None,
                 "label_kind": "unlabeled", "parent_sub_id": None, "order": 2,
                 "line_start": min(q[1], mid + 1), "line_end": q[1]},
            ]
        if defect == "inverted":
            u0 = man["units"][0]
            u0["sub_questions"][0]["line_start"] = u0["sub_questions"][0]["line_end"]
            u0["sub_questions"][0]["line_end"] = u0["sub_questions"][0]["line_start"] - 5
        return man

    def test_injected_defect_blocks_and_source_sha_unchanged(self, tmp_path,
                                                             monkeypatch):
        sha_before = self._sha()
        md, _jl, man = self._prepare(tmp_path)
        injected = self._inject(man, defect="inverted")  # ← 唯一缺陷（倒置区间）
        reply = json.dumps(injected, ensure_ascii=False)
        monkeypatch.setattr(
            rp, "call_llm",
            lambda prompt, **kw: (reply, {"prompt_tokens": 1,
                                          "completion_tokens": 1}))
        out = tmp_path / "out"
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        with pytest.raises(rp.GenerationGateError):
            rp.process_file(md, lambda s: None)
        assert not list(out.rglob("*.manifest.json")), "FAIL 卷不得写出正式 Manifest"
        diag = out / f"{md.stem}.gate.json"
        assert diag.is_file(), "须留下失败标记"
        rec = json.loads(diag.read_text(encoding="utf-8"))
        assert rec["verdict"] == "FAIL"
        g9_checks = [c for c in (rec.get("gate", {}).get("checks") or [])
                     if c["id"] == "G9_struct_integrity"]
        assert g9_checks and g9_checks[0]["status"] == "fail", g9_checks
        assert "倒置" in g9_checks[0]["detail"], g9_checks[0]["detail"]
        sha_after = self._sha()
        assert sha_after == sha_before, "G2A 原 manifest 不得被改动"
        # G9-F2：证据写产物绝对路径与内容——gate.json 全文、run 目录清单、
        # 「正式 manifest 不存在」的目录清单；gate.json 本体另存 EVID_DIR 可回放。
        self._write_evidence("injected_defect_blocking", sha_before, sha_after,
                             rec["run_id"], g9_checks[0]["detail"], artifacts={
                                 "out_dir": str(out.resolve()),
                                 "gate_json_path": str(diag.resolve()),
                                 "gate_json": rec,
                                 "out_dir_listing": sorted(
                                     str(x.resolve()) for x in out.rglob("*")),
                                 "formal_manifests_written": sorted(
                                     str(x.resolve())
                                     for x in out.rglob("*.manifest.json")),
                             })
        durable = EVID_DIR / "g9_b1_injected_defect_blocking.gate.json"
        durable.write_bytes(diag.read_bytes())

    def test_injected_valid_struct_passes_and_writes(self, tmp_path, monkeypatch):
        sha_before = self._sha()
        md, _jl, man = self._prepare(tmp_path)
        injected = self._inject(man, defect=None)  # 与缺陷例同构，仅无那处倒置
        reply = json.dumps(injected, ensure_ascii=False)
        monkeypatch.setattr(
            rp, "call_llm",
            lambda prompt, **kw: (reply, {"prompt_tokens": 1,
                                          "completion_tokens": 1}))
        out = tmp_path / "out"
        monkeypatch.setattr(rp, "OUT_ROOT", out)
        rp.process_file(md, lambda s: None)
        written = list(out.rglob("*.manifest.json"))
        assert written, "合法结构必须写出正式 Manifest"
        man_out = json.loads(written[0].read_text(encoding="utf-8"))
        gate = man_out["annotation_meta"]["json_struct_verification"]
        assert gate["verdict"] != "FAIL"
        g9 = [c for c in gate["checks"] if c["id"] == "G9_struct_integrity"]
        assert g9 and g9[0]["status"] == "pass", g9
        sha_after = self._sha()
        assert sha_after == sha_before
        self._write_evidence("injected_valid_pass", sha_before, sha_after,
                             "n/a", g9[0]["detail"], artifacts={
                                 "out_dir": str(out.resolve()),
                                 "formal_manifests_written": sorted(
                                     str(x.resolve())
                                     for x in out.rglob("*.manifest.json")),
                                 "out_dir_listing": sorted(
                                     str(x.resolve()) for x in out.rglob("*")),
                                 "gate_verdict": gate["verdict"],
                             })

    @staticmethod
    def _write_evidence(case, sha_before, sha_after, run_id, detail,
                        artifacts=None):
        EVID_DIR.mkdir(parents=True, exist_ok=True)
        p = EVID_DIR / f"g9_b1_{case}.json"
        p.write_text(json.dumps({
            "case": case,
            "source_manifest": str(G2A_MANIFEST),
            "source_sha256_before": sha_before,
            "source_sha256_after": sha_after,
            "sha_unchanged": sha_before == sha_after,
            "run_id": run_id,
            "g9_detail": detail,
            "evidence_json_path": str(p.resolve()),
            "artifacts": artifacts or {},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
