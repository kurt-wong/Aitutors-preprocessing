# -*- coding: utf-8 -*-
"""P2.1 度量脚本最小钉(Phase P2 先闭环纪律:度量必须可信,但不企业化)。"""

import importlib.util
import io
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


M = _load("p2_1_measure", os.path.join(ROOT, "scripts", "p2_1_measure.py"))


@pytest.fixture
def env(workdir):
    """假 SRC 根 + 输出根,返回 helper。"""
    src = workdir / "src"
    out = workdir / "out"
    src.mkdir(), out.mkdir()
    M.SRC = src

    def put(stem_rel, units, issues=None, warnings=None):
        man = {"source_file": "x.md", "model": "m",
               "annotation_meta": {"prompt_version": "v",
                                   "validation_issues": issues or [],
                                   "warnings": warnings or []},
               "units": units}
        p = out / stem_rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")

    return {"src": src, "out": out, "put": put}


def test_t1_ok_paper_metrics(env):
    env["put"]("高一/数学/a.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "answer_lines": [100, 100]},
        {"unit_id": "Q2", "unit_type": "standalone_question",
         "question_numbers": [2], "answer_lines": None},
        {"unit_id": "C1", "unit_type": "composite_question",
         "question_numbers": [3, 4], "answer_lines": [200, 210]},
    ])
    rec = M.measure_paper(env["out"], {
        "file": str(env["src"] / "高一" / "数学" / "a.md"), "subject": "数学"})
    assert rec["status"] == "OK" and rec["questions"] == 3
    assert rec["answered"] == 2 and rec["answer_rate"] == round(2 / 3, 4)
    assert rec["qnum_min"] == 1 and rec["qnum_max"] == 4 and rec["qnum_missing"] == []


def test_t2_no_manifest_and_validation_issues(env):
    rec = M.measure_paper(env["out"], {
        "file": str(env["src"] / "高一" / "数学" / "none.md"), "subject": "数学"})
    assert rec["status"] == "NO_MANIFEST" and rec["manifest_exists"] is False
    env["put"]("高一/数学/b.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "answer_lines": [1, 1]}], issues=["BAD"])
    rec2 = M.measure_paper(env["out"], {
        "file": str(env["src"] / "高一" / "数学" / "b.md"), "subject": "数学"})
    assert rec2["status"] == "VALIDATION_ISSUES"
    assert rec2["validation_issues"] == ["BAD"]


def test_t3_qnum_gap_detection(env):
    env["put"]("高二/物理/c.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "answer_lines": [1, 1]},
        {"unit_id": "Q3", "unit_type": "standalone_question",
         "question_numbers": [3], "answer_lines": [2, 2]},
    ])
    rec = M.measure_paper(env["out"], {
        "file": str(env["src"] / "高二" / "物理" / "c.md"), "subject": "物理"})
    assert rec["qnum_missing"] == [2]


def test_t4_batch_aggregation(env, workdir):
    env["put"]("高一/数学/a.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question",
         "question_numbers": [1], "answer_lines": [1, 1]}])
    batch = workdir / "batch.json"
    batch.write_text(json.dumps([
        {"file": str(env["src"] / "高一" / "数学" / "a.md"), "subject": "数学"},
        {"file": str(env["src"] / "高一" / "数学" / "none.md"), "subject": "数学"},
    ], ensure_ascii=False), encoding="utf-8")
    result = workdir / "measure.json"
    import subprocess
    p = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "p2_1_measure.py"),
                        "--batch", str(batch), "--out", str(env["out"]),
                        "--src", str(env["src"]),
                        "--result", str(result)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    assert p.returncode == 0, p.stderr
    rep = json.loads(result.read_text(encoding="utf-8"))
    t = rep["totals"]
    assert t["papers"] == 2 and t["ok"] == 1 and t["no_manifest"] == 1
    assert t["parse_success_rate"] == 0.5 and t["questions"] == 1
    assert rep["by_subject"]["数学"]["papers"] == 2
