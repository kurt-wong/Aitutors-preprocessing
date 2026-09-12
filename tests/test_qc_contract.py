# -*- coding: utf-8 -*-
"""write_outputs 产物与 QC check 的契约:
合成试卷 → 真实 write_outputs → 真实 QC → 必须全绿(不含网络)。
同时锁定 QC C12 的三种场景语义(固化 R24-B1)。"""
import json

import reslice_qc as qc
from conftest import SYNTH_LINES, make_repo


def _qc(manifest_path):
    # QC 的 check() 接收切片 md(非 annotated);manifest/annotated 均由 stem 派生
    md = manifest_path.parent / (manifest_path.name.replace(".manifest.json", ".md"))
    return qc.check(md)


def test_synth_repo_passes_qc(synth_repo):
    src, mf, out_dir = synth_repo
    r = _qc(mf)
    assert r["verdict"] == "PASS", r["issues"]


def test_c12_intersection_without_nesting_reported(workdir):
    """material 与 questions 相交但不嵌套(修复链引入过的真实形状)→ 必须报。"""
    lines = list(SYNTH_LINES)
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    u = man["units"][2]
    u["material_lines"] = [16, 20]      # 与 questions[19,22] 相交但越出
    u["questions_lines"] = [19, 22]
    _, mf, _ = make_repo(workdir, lines=lines, man=man)
    assert any(i.startswith("C12") for i in _qc(mf)["issues"])


def test_c12_separated_listening_structure_allowed(workdir):
    """听力式分离(material 全在 questions 之外)→ 不报 C12(合法结构)。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    u = man["units"][2]
    u["material_lines"] = [1, 3]        # 与 questions[19,22] 完全不相交
    u["questions_lines"] = [19, 22]
    _, mf, _ = make_repo(workdir, man=man)
    assert not any(i.startswith("C12") for i in _qc(mf)["issues"])


def test_c13_duplicate_question_numbers_reported(workdir):
    """R30 实测缺陷形状:大题内编号被当全卷题号(无 section 字段)→ 按全卷题号判定必须报 C13。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    # U3-4 的题号撞上 Q3(模拟选择题 Q3 + 非选择题大题内编号"3.")
    man["units"].append(
        {"unit_id": "N3", "unit_type": "standalone_question",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None})
    _, mf, _ = make_repo(workdir, man=man)
    assert any(i.startswith("C13") for i in _qc(mf)["issues"])


def test_c13_same_section_duplicate_reported(workdir):
    """R31 审查升级:有 section 字段时身份键=(section,题号);同分节重复仍必须报。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    for u in man["units"]:
        u["section"] = "一、选择题"
    man["units"].append(
        {"unit_id": "N3", "unit_type": "standalone_question", "section": "一、选择题",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None})
    _, mf, _ = make_repo(workdir, man=man)
    assert any(i.startswith("C13") for i in _qc(mf)["issues"])


def test_c13_cross_section_duplicate_allowed(workdir):
    """v1 存量语义(R31 scoped,无 identity_version 的历史产物口径):
    不同 section 同号不报 C13。⚠ 该语义已被 R33 证伪为无守卫(BUG-23),
    仅保用于未回填的 v1 产物;v2 语义(非 keep 全卷唯一+keep 证据豁免)
    见 test_question_identity_phase2.py,新产物一律走 v2。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    for u in man["units"]:
        u["section"] = "一、选择题"
    # 模拟"任选一个模块"的选考模块:模块二内编号 3 与选择题 3 同号但分节不同
    man["units"].append(
        {"unit_id": "M2-3", "unit_type": "standalone_question", "section": "《有机化学基础》模块试题",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None})
    _, mf, _ = make_repo(workdir, man=man)
    assert not any(i.startswith("C13") for i in _qc(mf)["issues"])


def test_c13_scoped_identity_passes_qc(workdir):
    """v1 存量语义:带 section 的分节重编号经 write_outputs 产物 QC PASS
    (历史口径;v2 口径需 keep+证据,见 test_question_identity_phase2)。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    for u in man["units"]:
        u["section"] = "一、选择题"
    man["units"].append(
        {"unit_id": "M2-3", "unit_type": "standalone_question", "section": "《有机化学基础》模块试题",
         "question_numbers": [3], "original_question_type": "fill_in",
         "stem_lines": [19, 19], "options_lines": None,
         "answer_lines": [31, 31], "explanation_lines": None})
    _, mf, _ = make_repo(workdir, man=man)
    r = _qc(mf)
    assert r["verdict"] == "PASS", r["issues"]


def test_c12_proper_nesting_allowed(workdir):
    """material ⊆ questions → 不报。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    u = man["units"][2]
    u["material_lines"] = [19, 20]
    u["questions_lines"] = [19, 22]
    _, mf, _ = make_repo(workdir, man=man)
    assert not any(i.startswith("C12") for i in _qc(mf)["issues"])
