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


def _write_src(env, rel, lines):
    p = env["src"] / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")


def test_t5_v3_metrics_admission_credibility_integrity_image(env):
    """用户 §7.2 口径:admission_ready / 答案可信度分桶 / 小问完整 / 图片依赖。"""
    lines = []
    lines += ["1. 题干一"]                                   # 1   Q1 stem
    lines += ["答案：A"]                                     # 2   Q1 answer
    lines += ["2. 题干二"]                                   # 3   Q2 stem(无答案)
    lines += ["12. 大题干"]                                  # 4   C1 stem head
    lines += ["（1）小问一"]                                  # 5
    lines += ["（2）<img src=\"a.jpg\" /> 小问二"]            # 6
    lines += ["（1）答一"]                                   # 7   C1 answer(缺(2)→partial)
    lines += ["13. 无小问组合"]                               # 8   C2 stem(拍平嫌疑)
    lines += ["（1）答"]                                     # 9   C2 answer
    _write_src(env, "高一/物理/x.md", lines)
    env["put"]("高一/物理/x.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question", "question_numbers": [1],
         "original_question_type": "choice", "stem_lines": [1, 1], "answer_lines": [2, 2]},
        {"unit_id": "Q2", "unit_type": "standalone_question", "question_numbers": [2],
         "original_question_type": "choice", "stem_lines": [3, 3], "answer_lines": None},
        {"unit_id": "C1", "unit_type": "composite_question", "question_numbers": [12],
         "original_question_type": "solve", "stem_lines": [4, 6], "answer_lines": [7, 7]},
        {"unit_id": "C2", "unit_type": "composite_question", "question_numbers": [13],
         "original_question_type": "solve", "stem_lines": [8, 8], "answer_lines": [9, 9]},
    ])
    rec = M.measure_paper(env["out"], {
        "file": str(env["src"] / "高一" / "物理" / "x.md"), "subject": "物理"})
    assert rec["source_readable"] is True
    # Q1 exact-ready;Q2 缺答案;C1 答案缺(2)=partial;C2 stem 无小问=suspect
    # admission 口径(§7.2)不含小问完整性:C1/C2 仍满足 stem/answer/anchor/题型
    assert rec["admission_ready"] == 3 and rec["questions"] == 4
    assert rec["admission_ready_rate"] == 0.75
    assert rec["answer_credibility"] == {"exact": 1, "missing": 1,
                                         "partial": 1, "suspect": 1}
    assert rec["composite_total"] == 2 and rec["composite_intact"] == 1
    assert rec["sub_question_integrity"] == 0.5
    assert rec["image_dependent_questions"] == 1   # C1 stem 含 <img>


def test_t6_human_sample_deterministic(env, workdir):
    env["put"]("高一/数学/a.manifest.json", [
        {"unit_id": f"Q{i}", "unit_type": "standalone_question",
         "question_numbers": [i], "answer_lines": [1, 1]} for i in range(1, 16)])
    entry = {"file": str(env["src"] / "高一" / "数学" / "a.md"), "subject": "数学"}
    s1 = M.build_human_sample(env["out"], [entry])
    s2 = M.build_human_sample(env["out"], [entry])
    assert s1 == s2, "抽检清单必须确定性可复现"
    assert s1["questions"] == 10 and s1["papers"] == 1
    assert len({i["unit_id"] for i in s1["items"]}) == 10


def test_t7_aggregate_v3_totals(env, workdir):
    _write_src(env, "高一/数学/a.md", ["1. 题干", "答案：B"])
    env["put"]("高一/数学/a.manifest.json", [
        {"unit_id": "Q1", "unit_type": "standalone_question", "question_numbers": [1],
         "original_question_type": "choice", "stem_lines": [1, 1], "answer_lines": [2, 2]}])
    batch = workdir / "batch2.json"
    batch.write_text(json.dumps([
        {"file": str(env["src"] / "高一" / "数学" / "a.md"), "subject": "数学"}],
        ensure_ascii=False), encoding="utf-8")
    result = workdir / "measure2.json"
    import subprocess
    p = subprocess.run([sys.executable,
                        os.path.join(ROOT, "scripts", "p2_1_measure.py"),
                        "--batch", str(batch), "--out", str(env["out"]),
                        "--src", str(env["src"]),
                        "--result", str(result),
                        "--human-sample", str(workdir / "hs.json")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    assert p.returncode == 0, p.stderr
    rep = json.loads(result.read_text(encoding="utf-8"))
    t = rep["totals"]
    assert t["admission_ready"] == 1 and t["admission_ready_rate"] == 1.0
    assert t["answer_credibility"] == {"exact": 1}
    assert t["image_dependent_questions"] == 0
    hs = json.loads((workdir / "hs.json").read_text(encoding="utf-8"))
    assert hs["questions"] == 1 and hs["items"][0]["unit_id"] == "Q1"
