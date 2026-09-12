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


def test_c12_proper_nesting_allowed(workdir):
    """material ⊆ questions → 不报。"""
    from conftest import SYNTH_MAN
    man = json.loads(json.dumps(SYNTH_MAN))
    u = man["units"][2]
    u["material_lines"] = [19, 20]
    u["questions_lines"] = [19, 22]
    _, mf, _ = make_repo(workdir, man=man)
    assert not any(i.startswith("C12") for i in _qc(mf)["issues"])
