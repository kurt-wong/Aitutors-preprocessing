# -*- coding: utf-8 -*-
"""R33 Phase 2 对抗性审查固化:BUG-22 回归突变的守卫行为。

真实测量(scripts/phase2_adversarial_probe.py A3):把 R31 迁移的 7 份产物题号
全部回退到 old 值(BUG-22 原始形态:选择题与非选择题各自从 1 编号)后:
  - 保留 section 字段 → 生产 C13 只拦住 1/7(博雅语文是回退后恰成同分节重复)
  - 删除 section 字段(全卷口径)→ 7/7 全部拦住
结论:scoped C13 一旦有 section 就对 BUG-22 的跨分节重号形态失去守卫能力
(登记 BUG-23)。本文件用合成件复现该分叉,xfail 锁定"应拦未拦"的修复义务。
"""
import json

import pytest

import reslice_qc as qc
from conftest import SYNTH_MAN, make_repo


def _qc(manifest_path):
    md = manifest_path.parent / (manifest_path.name.replace(".manifest.json", ".md"))
    return qc.check(md)


def _bug22_regressed_manifest():
    """BUG-22 原始形态:选择题 3 与非选择题大题内编号"3."同号、跨分节、均非 keep。"""
    man = json.loads(json.dumps(SYNTH_MAN))
    for u in man["units"]:
        u["section"] = "一、选择题"
    man["units"].append(
        {"unit_id": "N3", "unit_type": "standalone_question", "section": "二、非选择题",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None})
    return man


@pytest.mark.xfail(
    strict=True,
    reason="BUG-23: scoped C13 对跨分节 canonical 重号(BUG-22 回归形态)无守卫,"
           "真实产物回迁突变 6/7 漏放;修复需 canonical 全卷唯一 + keep/basis 豁免模型"
           "(question_identity_design.md R33 修订),Phase 2 实施后转绿。")
def test_bug22_cross_section_regression_must_be_flagged(workdir):
    man = _bug22_regressed_manifest()
    _, mf, _ = make_repo(workdir, man=man)
    assert any(i.startswith("C13") for i in _qc(mf)["issues"]), \
        "BUG-22 回归形态(跨分节重号、无 keep 依据)必须被拦截"


def test_section_field_is_sole_discriminant_for_bug22(workdir):
    """同一回归形态:无 section 必拦(全卷口径)——证明 section 字段是唯一分叉点。"""
    man = _bug22_regressed_manifest()
    for u in man["units"]:
        u.pop("section", None)
    _, mf, _ = make_repo(workdir, man=man)
    assert any(i.startswith("C13") for i in _qc(mf)["issues"])
