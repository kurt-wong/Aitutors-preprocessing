# -*- coding: utf-8 -*-
"""Prompt v4 契约测试（QC0RE-PHASE3-G3-B · B2-1）。

锁住 Prompt v4 的判据面（DSH B2 盯防主线①的可测部分）：
- 根本规则 2 以金标准 A/B/D 取代「共享同一段材料才算」门槛（P-01 根因）；
- 结构输出解禁：sub_questions 树 + grouping_statements 必须输出（结构标注非拆题）；
- triage 三值 + tie-break（共用前提+点名范围 → explicit_grouping）；
- answers[].sub_ref 显式绑定；uncertainty 如实标注；
- 既有 P2.2/P2.1-e/P0 保真锚点不丢（回归不放水）。
真实 LLM 行为由 12 卷验证与 g3_expected_structure.json 对账检验。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reslice_pipeline as rp  # noqa: E402


class TestPromptV4Judgment:
    def test_version(self):
        assert rp.PROMPT_VERSION == "v4-g3-structure-20261116"

    def test_basis_abd_replaces_material_gate(self):
        h = rp.PROMPT_HEAD
        # P-01 根因规则已替换
        assert '共享"同一段"材料才算' not in h
        assert "不要输出 sub_questions" not in h
        # A/B/D 判据落地
        assert "basis ∈ {A, B, D}" in h
        assert "material_lines 是否存在不是综合题的必要或排除条件" in h
        assert "single printed number" in h
        assert "A 共享前提与材料依赖" in h
        assert "B 明确的共同题目任务单元" in h
        assert "D 印刷原子性" in h

    def test_gs2_three_semantics_and_listening(self):
        h = rp.PROMPT_HEAD
        assert "同措辞三语义" in h
        assert "完形填空 N 空 = 1 题" in h
        assert "N 道独立题" in h
        assert "听力成组" in h
        assert "单题音频" in h

    def test_structure_output_required(self):
        h = rp.PROMPT_HEAD
        assert "结构标注不是拆题" in h
        assert "4g. 【结构标注 sub_questions[]】" in h
        assert "4h. 【判据与声明的完整表达】" in h
        assert "parent_sub_id" in h
        assert "label_kind" in h

    def test_triage_tiebreak_and_gt_conflict(self):
        h = rp.PROMPT_HEAD
        assert "explicit_grouping" in h
        assert "shared_dependency" in h
        assert "section_count_only" in h
        assert "tie-break" in h
        assert "不是** triage 取值" in h or "不是** triage" in h or "不是**triage" in h or \
            "**不是** triage 取值" in h

    def test_sub_ref_and_uncertainty(self):
        h = rp.PROMPT_HEAD
        assert '"sub_ref"' in h or "sub_ref" in h
        assert "答案归属靠它显式绑定" in h
        assert "绝不伪装确定" in h
        assert "uncertainty" in h


class TestPromptV4NoRegressionAnchors:
    """既有锚点保留（P0 保真 / P2.1-e / P2.2 / 4d 答案契约）。"""

    def test_fidelity_and_answer_anchors(self):
        h = rp.PROMPT_HEAD
        assert '"shared": true 或 false' in h
        assert "绝不为了\"只圈自己的\"把共享答案表切碎" in h
        assert "由 answer_lines 圈定" in h
        assert "answer_completeness" in h
        assert "answer_conflicts" in h
        assert "PDF 是唯一事实源" in h

    def test_image_semantic_reference_anchors(self):
        h = rp.PROMPT_HEAD
        assert "语义引用规则" in h
        assert "必须包含在本题的行区间内" in h
        assert "绝不因为图片离本题近就纳入" in h
        assert "不要为此建立任何新的图片归属结构" in h
        assert "选项配图版式" in h
        assert "延伸覆盖到末选项的配图行" in h

    def test_identity_and_paper_line_anchors(self):
        h = rp.PROMPT_HEAD
        assert "printed_number" in h
        assert "question_numbers" in h
        assert "入库的是 question，不是 paper" in h

    def test_build_prompt_embeds_version(self):
        p = rp.build_prompt("", "L0001 x")
        assert p.startswith("[prompt_version=v4-g3-structure-20261116]")
        assert "【试卷内容】" in p
