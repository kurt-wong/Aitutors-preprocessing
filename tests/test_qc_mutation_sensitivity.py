# -*- coding: utf-8 -*-
"""QC 变异灵敏度回归(R46 对抗审查固化)。

R46 在真实 PAC 产物上做了 17 条变异(全部命中),但那些脚本依赖被 gitignore
的语料,CI 跑不到。本文件用合成语料把"注入缺陷必须被对应检查码咬住"钉进
CI:任何未来让某检查族失敏的改动都会在这里红。

纪律:每条测试=一个变异→断言一个检查码;不测"应该干净"的反向断言
(那是 test_qc_contract 的职责)。
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_identity as qi  # noqa: E402
import reslice_qc  # noqa: E402
from conftest import SYNTH_LINES, SYNTH_MAN, make_repo  # noqa: E402


def _qc(md_path):
    return reslice_qc.check(md_path)


def _files(out_dir, stem="synthetic"):
    md = out_dir / f"{stem}.md"
    ann = out_dir / f"{stem}.annotated.md"
    mf = out_dir / f"{stem}.manifest.json"
    return md, ann, mf


def _load(mf):
    return json.loads(mf.read_text(encoding="utf-8"))


def _save(mf, man):
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="")


def _has(res, code):
    return any(i.startswith(code) for i in res["issues"]) or \
           any(i.startswith(code) for i in res.get("review_notes") or [])


def test_control_synth_passes(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, _ = _files(out_dir)
    res = _qc(md)
    assert res["verdict"] == "PASS", res["issues"]


def test_c1_marker_broken_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, _ = _files(out_dir)
    md.write_text(md.read_text(encoding="utf-8").replace("“题干区结束”", "", 1),
                  encoding="utf-8", newline="")
    res = _qc(md)
    assert _has(res, "C1") and res["verdict"] == "FAIL"


def test_c2_question_number_lost_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, mf = _files(out_dir)
    man = _load(mf)
    man["units"][0]["question_numbers"] = [99]
    _save(mf, man)
    res = _qc(md)
    assert _has(res, "C2") and res["verdict"] == "FAIL"


def test_c3_empty_answer_zone_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, _ = _files(out_dir)
    t = md.read_text(encoding="utf-8")
    i = t.index("“答案区开始”") + len("“答案区开始”")
    j = t.index("“答案区结束”", i)
    md.write_text(t[:i] + "\n" + t[j:], encoding="utf-8", newline="")
    res = _qc(md)
    assert _has(res, "C3") and res["verdict"] == "FAIL"


def test_c5_image_line_lost_fails(workdir):
    src, _, out_dir = make_repo(workdir)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write('\n<img src="mutation_injected.jpg">\n')
    md, _, _ = _files(out_dir)
    res = _qc(md)
    assert _has(res, "C5") and res["verdict"] == "FAIL"


def test_c7_boilerplate_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, _ = _files(out_dir)
    md.write_text(md.read_text(encoding="utf-8") + "\n考试时间 90 分钟\n",
                  encoding="utf-8", newline="")
    res = _qc(md)
    assert _has(res, "C7") and res["verdict"] == "FAIL"


def test_c8_anchor_drift_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    _, ann, _ = _files(out_dir)
    ann.write_text(ann.read_text(encoding="utf-8") + "\n变异行\n",
                   encoding="utf-8", newline="")
    res = _qc(out_dir / "synthetic.md")
    assert _has(res, "C8") and res["verdict"] == "FAIL"


def test_c10_anchor_unpaired_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    _, ann, _ = _files(out_dir)
    t = ann.read_text(encoding="utf-8")
    t2 = re.sub(r"<!--\s*META:\w+:end[^>]*-->\n?", "", t, count=1)
    assert t2 != t, "合成 annotated 无 META:end 行"
    ann.write_text(t2, encoding="utf-8", newline="")
    res = _qc(out_dir / "synthetic.md")
    assert _has(res, "C10") and res["verdict"] == "FAIL"


def test_c11_restate_stem_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, mf = _files(out_dir)
    man = _load(mf)
    u = man["units"][0]
    u["explanation_lines"] = [u["stem_lines"][0], u["stem_lines"][0]]
    _save(mf, man)
    res = _qc(md)
    assert _has(res, "C11") and res["verdict"] == "FAIL"


def test_c13_duplicate_canonical_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, mf = _files(out_dir)
    man = _load(mf)
    dup = dict(man["units"][0])
    dup["unit_id"] = "Q1-DUP"
    man["units"].append(dup)
    _save(mf, man)
    res = _qc(md)
    assert _has(res, "C13") and res["verdict"] == "FAIL"


def _make_repo_v2(workdir):
    """identity v2 版合成产物(sections 由真实 assign_identity 构建)。"""
    man = json.loads(json.dumps(SYNTH_MAN))
    qi.assign_identity(man, SYNTH_LINES)
    return make_repo(workdir, man=man)


def test_c14_missing_section_ref_pending_review(workdir):
    """v2 缺 section_ref 不得静默 PASS:必须 PENDING_REVIEW。"""
    _, _, out_dir = _make_repo_v2(workdir)
    md, _, mf = _files(out_dir)
    man = _load(mf)
    man["units"][0]["section_ref"] = None
    _save(mf, man)
    res = _qc(md)
    assert _has(res, "C14")
    assert res["verdict"] == "PENDING_REVIEW", res


def test_c12_intersection_without_nesting_fails(workdir):
    _, _, out_dir = make_repo(workdir)
    md, _, mf = _files(out_dir)
    man = _load(mf)
    comp = next(u for u in man["units"]
                if u["unit_type"] == "composite_question")
    comp["material_lines"] = [16, 20]   # 与 questions [19,22] 相交但未嵌套
    _save(mf, man)
    res = _qc(md)
    assert _has(res, "C12") and res["verdict"] == "FAIL"
