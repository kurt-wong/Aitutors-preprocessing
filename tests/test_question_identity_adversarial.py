# -*- coding: utf-8 -*-
"""R33 对抗审查固化 + R34 守卫修复验证:BUG-22 回归突变的守卫行为。

R33 真实测量(scripts/phase2_adversarial_probe.py A3):R31 scoped C13 对
BUG-22 跨分节回归形态漏放 6/7(guard soundness failure,BUG-23)。
R34 修复(QuestionIdentity v2:非 keep 全卷唯一 + keep 个体豁免带证据)后,
同一突变在真实 batch-C 产物上 7/7 全拦(data/phase2_adversarial_review_r34.json)。
本文件用合成件锁定修复后的语义:回归形态必须 FAIL(修复义务已从 xfail 转正)。
"""
import json

import reslice_qc as qc
from conftest import SYNTH_MAN, make_repo

SECTIONS = [
    {"id": "S1", "title": "一、选择题", "ordinal": 1, "start_line": 3, "end_line": 14},
    {"id": "S2", "title": "二、非选择题", "ordinal": 2, "start_line": 15, "end_line": 32},
]


def _qc(manifest_path):
    md = manifest_path.parent / (manifest_path.name.replace(".manifest.json", ".md"))
    return qc.check(md)


def _bug22_regressed_manifest():
    """BUG-22 原始形态:选择题 3 与非选择题大题内编号"3."同号、跨分节、均非 keep。"""
    man = json.loads(json.dumps(SYNTH_MAN))
    man["identity_version"] = 2
    man["sections"] = SECTIONS
    for u in man["units"]:
        u["section"] = "一、选择题"
        u["section_ref"] = "S1"
        u["basis"] = "printed_as_is"
    man["units"].append(
        {"unit_id": "N3", "unit_type": "standalone_question",
         "section": "二、非选择题", "section_ref": "S2",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None,
         "basis": "shift", "basis_evidence": "大题内编号顺延(R31 迁移前形态)"})
    return man


def test_bug22_cross_section_regression_is_flagged(workdir):
    """BUG-23 修复验证:跨分节重号、无 keep 依据 → 必须 FAIL。"""
    _, mf, _ = make_repo(workdir, man=_bug22_regressed_manifest())
    r = _qc(mf)
    assert r["verdict"] == "FAIL"
    assert any(i.startswith("C13") for i in r["issues"])


def test_section_fields_are_not_sole_discriminant_anymore(workdir):
    """R33 时这是分叉点(section 在/不在行为不同);v2 修复后两条路径都必须拦:
    无 section_ref 时同 scope 重号 FAIL + C14 identity_scope_missing 复核项。"""
    man = _bug22_regressed_manifest()
    for u in man["units"]:
        u.pop("section", None)
        u.pop("section_ref", None)
    _, mf, _ = make_repo(workdir, man=man)
    r = _qc(mf)
    assert any(i.startswith("C13") for i in r["issues"])
    assert any("identity_scope_missing" in n for n in r["review_notes"])
