# -*- coding: utf-8 -*-
"""P2.1-c 答案证据契约最小钉(prompt v2.4 answer_evidence + 校验 + 度量)。"""

import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RP = _load("rp_p21c", os.path.join(ROOT, "scripts", "reslice_pipeline.py"))
M = _load("m_p21c", os.path.join(ROOT, "scripts", "p2_1_measure.py"))


def _unit(**kw):
    u = {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "original_question_type": "single_choice",
         "stem_lines": [1, 1], "options_lines": None,
         "answer_lines": None, "explanation_lines": [3, 3]}
    u.update(kw)
    return u


LINES = ["1. 题干", "A. 选项", "【解析】", "【详解】故选 D。"]


def test_t1_inline_evidence_replaces_answer_lines_issue():
    man = {"units": [_unit(answer_evidence={
        "type": "inline_in_explanation", "lines": [4, 4], "value": "D"})]}
    issues, _ = RP.validate_manifest(man, len(LINES), LINES)
    assert not any("无 answer_lines" in i for i in issues), issues


def test_t2_absent_and_missing_evidence_still_issue():
    man = {"units": [_unit(answer_evidence={
        "type": "absent", "lines": None, "value": None})]}
    issues, _ = RP.validate_manifest(man, len(LINES), LINES)
    assert any("无 answer_lines" in i for i in issues)
    man2 = {"units": [_unit()]}                    # v2.3 遗留形态,无证据字段
    issues2, _ = RP.validate_manifest(man2, len(LINES), LINES)
    assert any("无 answer_lines" in i for i in issues2)


def test_t3_evidence_schema_violations():
    bad_type = {"units": [_unit(answer_evidence={"type": "guess", "lines": [4, 4]})]}
    issues, _ = RP.validate_manifest(bad_type, len(LINES), LINES)
    assert any("answer_evidence.type 非法" in i for i in issues)
    absent_with_lines = {"units": [_unit(answer_evidence={
        "type": "absent", "lines": [4, 4], "value": None})]}
    issues2, _ = RP.validate_manifest(absent_with_lines, len(LINES), LINES)
    assert any("absent 时 lines/value 必须为 null" in i for i in issues2)
    no_lines = {"units": [_unit(answer_evidence={"type": "inline_in_explanation"})]}
    issues3, _ = RP.validate_manifest(no_lines, len(LINES), LINES)
    assert any("缺合法 lines" in i for i in issues3)
    not_dict = {"units": [_unit(answer_evidence="D")]}
    issues4, _ = RP.validate_manifest(not_dict, len(LINES), LINES)
    assert any("answer_evidence 非对象" in i for i in issues4)


def test_t4_uncovered_answer_marker_line():
    lines = ["1. 题干", "【答案】D", "2. 题干", "【答案】A"]
    man = {"units": [
        _unit(unit_id="Q1", stem_lines=[1, 1], answer_lines=[2, 2],
              explanation_lines=None),
        _unit(unit_id="Q2", question_numbers=[2], stem_lines=[3, 3],
              answer_lines=None, explanation_lines=None,
              answer_evidence={"type": "absent", "lines": None, "value": None})]}
    issues, _ = RP.validate_manifest(man, len(lines), lines)
    assert any("L4: 【答案】行未被任何单元区间覆盖" in i for i in issues), issues
    assert not any("L2: 【答案】行未被任何单元" in i for i in issues)


def test_t5_compile_slices_renders_evidence_not_content():
    man = {"units": [_unit(answer_evidence={
        "type": "inline_in_explanation", "lines": [4, 4], "value": "D"})]}
    md, _ = RP.compile_slices(LINES, man, "x.md", "x.md")
    assert "答案证据 type=inline_in_explanation L0004-L0004 值=D" in md
    # absent 不渲染证据注释
    man2 = {"units": [_unit(answer_evidence={
        "type": "absent", "lines": None, "value": None})]}
    md2, _ = RP.compile_slices(LINES, man2, "x.md", "x.md")
    assert "答案证据" not in md2


def test_t6_prompt_version_provenance_not_washed():
    """重编译旧 v2.3 卷:manifest 版本戳保留,不得洗成当前版本。"""
    man = {"units": [_unit(answer_lines=[2, 2], explanation_lines=None)],
           "annotation_meta": {"prompt_version": "reslice-pilot-v2.3"}}
    anchor = RP.compile_anchor(LINES, man, "x.md", "x.md")
    assert "prompt=reslice-pilot-v2.3" in anchor
    import inspect
    src = inspect.getsource(RP.write_outputs)
    assert 'get("prompt_version")' in src


def test_t7_measure_evidence_locates_admission(workdir):
    src = workdir / "src"
    out = workdir / "out"
    (src / "高一" / "数学").mkdir(parents=True)
    out.mkdir()
    (src / "高一" / "数学" / "a.md").write_text("\n".join(LINES), encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v2.4",
                               "validation_issues": [], "warnings": []},
           "units": [
               _unit(answer_evidence={"type": "inline_in_explanation",
                                      "lines": [4, 4], "value": "D"}),
               _unit(unit_id="Q2", question_numbers=[2],
                     answer_evidence={"type": "absent", "lines": None, "value": None}),
           ]}
    (out / "高一" / "数学").mkdir(parents=True, exist_ok=True)
    (out / "高一" / "数学" / "a.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M.SRC = src
    rec = M.measure_paper(out, {"file": str(src / "高一" / "数学" / "a.md"),
                                "subject": "数学"})
    assert rec["answered"] == 1                      # evidence 定位计入
    assert rec["admission_ready"] == 1
    assert rec["answer_evidence_types"] == {"inline_in_explanation": 1, "absent": 1}


def test_t8_measure_legacy_v23_unchanged(workdir):
    src = workdir / "src2"
    out = workdir / "out2"
    (src / "高一" / "数学").mkdir(parents=True)
    out.mkdir()
    (src / "高一" / "数学" / "b.md").write_text("1. 题干\n答案：B", encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v2.3",
                               "validation_issues": [], "warnings": []},
           "units": [_unit(stem_lines=[1, 1], answer_lines=[2, 2],
                           explanation_lines=None)]}
    (out / "高一" / "数学").mkdir(parents=True, exist_ok=True)
    (out / "高一" / "数学" / "b.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M.SRC = src
    rec = M.measure_paper(out, {"file": str(src / "高一" / "数学" / "b.md"),
                                "subject": "数学"})
    assert rec["answered"] == 1 and rec["answer_evidence_types"] == {}


def test_t9_suspect_sample_labels(workdir):
    src = workdir / "src3"
    out = workdir / "out3"
    (src / "高一" / "历史").mkdir(parents=True)
    out.mkdir()
    (src / "高一" / "历史" / "c.md").write_text(
        "材料一……\n12. 无小问组合题", encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v", "validation_issues": [],
                               "warnings": []},
           "units": [{"unit_id": "C1", "unit_type": "composite_question",
                      "question_numbers": [12], "original_question_type": "solve",
                      "material_lines": [1, 1], "questions_lines": [1, 2],
                      "answer_lines": None,
                      "answer_evidence": {"type": "absent", "lines": None,
                                          "value": None}}]}
    (out / "高一" / "历史").mkdir(parents=True, exist_ok=True)
    (out / "高一" / "历史" / "c.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M.SRC = src
    ss = M.build_suspect_sample(out, [{"file": str(src / "高一" / "历史" / "c.md"),
                                       "subject": "历史"}])
    assert ss["questions"] == 1 and ss["items"][0]["label"] is None
    assert ss["label_vocabulary"] == ["KEEP", "SPLIT", "LOST", "UNCERTAIN"]


def test_t10_credibility_counts_evidence_value(workdir):
    """无答案区但 evidence.value 为源文明文 → exact;仅定位无值 → missing。"""
    src = workdir / "src4"
    out = workdir / "out4"
    (src / "高一" / "数学").mkdir(parents=True)
    out.mkdir()
    (src / "高一" / "数学" / "d.md").write_text("\n".join(LINES), encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v2.4",
                               "validation_issues": [], "warnings": []},
           "units": [
               _unit(unit_id="Q1", question_numbers=[1],
                     answer_evidence={"type": "inline_in_explanation",
                                      "lines": [4, 4], "value": "D"}),
               _unit(unit_id="Q2", question_numbers=[2],
                     answer_evidence={"type": "inline_in_explanation",
                                      "lines": [4, 4], "value": None}),
           ]}
    (out / "高一" / "数学").mkdir(parents=True, exist_ok=True)
    (out / "高一" / "数学" / "d.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M.SRC = src
    rec = M.measure_paper(out, {"file": str(src / "高一" / "数学" / "d.md"),
                                "subject": "数学"})
    assert rec["answer_credibility"] == {"exact": 1, "missing": 1}
