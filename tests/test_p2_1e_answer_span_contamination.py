# -*- coding: utf-8 -*-
r"""P2.1-e 答案区间污染修复最小钉(charter §10:prompt v2.5 边界语义 + 确定性校验)。

实测污染三形态(71/71 人工标注):
  整表污染   101地理:整张答案表单行 HTML 圈进每个单元
  相邻串题   综合英语/通州地理:连写答案行 "21\. B 22\. C" 含他题答案
  题干混入   交大英语:题区内联答案块并入 questions_lines;丰台历史:answer_lines 吞入复述题干
"""

import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RP = _load("rp_p21e", os.path.join(ROOT, "scripts", "reslice_pipeline.py"))
PC = _load("pc_p21e", os.path.join(ROOT, "scripts", "prereview_check.py"))


def test_t1_parse_inline_answers():
    # 综合能力测试英语 L395 实测形态(markdown 转义点)
    m = PC.parse_inline_answers(r"21\. B 22\. C 23\. A 24\. B 25\. C 26\. A 27\. D")
    assert m == {21: "B", 22: "C", 23: "A", 24: "B", 25: "C", 26: "A", 27: "D"}
    # 通州地理 L335 实测形态(普通点)
    m2 = PC.parse_inline_answers("1. A 2. D 3. D 4. B 5. C")
    assert m2 == {1: "A", 2: "D", 3: "D", 4: "B", 5: "C"}
    # 孤对不认(防句中 "1. A 项" 误报);句子型答案不认(交大英语翻译答案)
    assert PC.parse_inline_answers("故本题选 1. A 项即可") == {}
    assert PC.parse_inline_answers("【答案】60. While browsing the website") == {}
    # 完形填空词形答案("16. in 17. struck")不是字母答案,不认
    assert PC.parse_inline_answers("16. in 17. struck 18. fewer 19. themselves") == {}


def test_t2_c_a1_stem_contaminated_by_inline_answer():
    """交大英语形态:题区内联答案块并入 questions_lines → C-A1 issue。"""
    lines = [
        "翻译下列句子",            # L1
        "60. 中文题干一",          # L2
        "61. 中文题干二",          # L3
        "【答案】60. En one",      # L4 题区内联答案
        "",
        "【答案】61. En two",      # L6
        "## 参考答案",             # L7
        "【答案】60. En one",      # L8 卷末副本
        "",
        "【答案】61. En two",      # L10
    ]
    unit = {"unit_id": "U60-61", "unit_type": "composite_question",
            "question_numbers": [60, 61], "original_question_type": "short_answer",
            "material_lines": None, "questions_lines": [1, 6],
            "answer_lines": [8, 10], "explanation_lines": None}
    issues, _ = RP.validate_manifest({"units": [unit]}, len(lines), lines)
    assert any("题干区 L4 混入未圈定的【答案】行" in i for i in issues), issues
    # 修复后形态:questions 止于题干,answer_lines 圈题区内联答案,卷末副本降 warning
    unit2 = dict(unit, questions_lines=[1, 3], answer_lines=[4, 6])
    issues2, summary2 = RP.validate_manifest({"units": [unit2]}, len(lines), lines)
    assert not any("混入未圈定的【答案】行" in i for i in issues2), issues2
    assert not any("【答案】行未被任何单元区间覆盖" in i for i in issues2), issues2
    assert any("重复答案块" in w for w in summary2["warnings"]), summary2["warnings"]


def test_t3_c_a2_answer_swallowing_stem_heading():
    """丰台历史形态:answer_lines 吞入答案区里复述的题干标题行 → C-A2 issue。"""
    lines = [
        "### 28. 党章的演变",      # L1 答案区复述的题干
        "材料表格行",              # L2
        "依据材料解读历程。",       # L3
        "## 【答案】示例",         # L4
        "五四运动中……",            # L5
    ]
    unit = {"unit_id": "U28", "unit_type": "composite_question",
            "question_numbers": [28], "original_question_type": "short_answer",
            "material_lines": [2, 2], "questions_lines": [1, 3],
            "answer_lines": [1, 5], "explanation_lines": None}
    issues, _ = RP.validate_manifest({"units": [unit]}, len(lines), lines)
    assert any("答案区 L1 含本题题干标题行" in i for i in issues), issues
    unit2 = dict(unit, answer_lines=[4, 5])
    issues2, _ = RP.validate_manifest({"units": [unit2]}, len(lines), lines)
    assert not any("含本题题干标题行" in i for i in issues2), issues2


def test_t4_c_a3_shared_answer_must_be_declared():
    """综合英语形态:连写答案行含他题答案 → 必须 shared=true + 逐题 value。"""
    lines = ["21. 题干", "22. 题干", "23. 题干",
             r"21\. B 22\. C 23\. A 24\. B 25\. C"]
    base = {"unit_id": "U21-23", "unit_type": "composite_question",
            "question_numbers": [21, 22, 23], "original_question_type": "reading",
            "material_lines": [1, 1], "questions_lines": [1, 3],
            "answer_lines": [4, 4], "explanation_lines": None}
    # 未标 shared → issue
    issues, _ = RP.validate_manifest({"units": [dict(base)]}, len(lines), lines)
    assert any("但未标 answer_evidence.shared" in i for i in issues), issues
    # shared=true 但缺 value → issue(逐题定位要求)
    u2 = dict(base, answer_evidence={"type": "range_string", "lines": [4, 4],
                                     "value": None, "shared": True})
    issues2, _ = RP.validate_manifest({"units": [u2]}, len(lines), lines)
    assert any("shared 答案区必须给本题明文 value" in i for i in issues2), issues2
    # shared=true 且逐题明文 value → 零污染 issue
    u3 = dict(base, answer_evidence={"type": "range_string", "lines": [4, 4],
                                     "value": "21.B 22.C 23.A", "shared": True})
    issues3, _ = RP.validate_manifest({"units": [u3]}, len(lines), lines)
    assert not any("shared" in i for i in issues3), issues3
    # shared 非布尔 → issue
    u4 = dict(base, answer_evidence={"type": "range_string", "lines": [4, 4],
                                     "value": "21.B 22.C 23.A", "shared": "yes"})
    issues4, _ = RP.validate_manifest({"units": [u4]}, len(lines), lines)
    assert any("answer_evidence.shared 非布尔" in i for i in issues4), issues4


def test_t5_c_a3_answer_table_shared():
    """101地理形态:整张答案表单行 HTML 圈进每个单元 → 同一 C-A3 口径。"""
    table = ('<table border=1><tr><td>2</td><td>3</td><td>4</td></tr>'
             '<tr><td>B</td><td>C</td><td>D</td></tr></table>')
    lines = ["2. 题干", "3. 题干", table]
    u = {"unit_id": "U2-3", "unit_type": "composite_question",
         "question_numbers": [2, 3], "original_question_type": "short_answer",
         "material_lines": [1, 1], "questions_lines": [1, 2],
         "answer_lines": [3, 3],
         "answer_evidence": {"type": "answer_table", "lines": [3, 3],
                             "value": "2.B 3.C", "shared": True},
         "explanation_lines": None}
    issues, _ = RP.validate_manifest({"units": [u]}, len(lines), lines)
    assert not any("shared" in i for i in issues), issues
    u2 = dict(u, answer_evidence={"type": "answer_table", "lines": [3, 3],
                                  "value": "B", "shared": False})
    issues2, _ = RP.validate_manifest({"units": [u2]}, len(lines), lines)
    assert any("但未标 answer_evidence.shared" in i for i in issues2), issues2


def test_t6_contamination_report_counts():
    lines = ["21. 题干", "22. 题干", "23. 题干",
             r"21\. B 22\. C 23\. A 24\. B"]
    u = {"unit_id": "U21-23", "unit_type": "composite_question",
         "question_numbers": [21, 22, 23], "original_question_type": "reading",
         "material_lines": [1, 1], "questions_lines": [1, 3],
         "answer_lines": [4, 4], "explanation_lines": None}
    rep = RP.contamination_report({"units": [u]}, lines)
    assert rep == {"stem_has_answer_line": 0, "answer_has_stem_heading": 0,
                   "shared_unmarked": 1, "shared_missing_value": 0, "total": 1}
    u2 = dict(u, answer_evidence={"type": "range_string", "lines": [4, 4],
                                  "value": "21.B 22.C 23.A", "shared": True})
    rep2 = RP.contamination_report({"units": [u2]}, lines)
    assert rep2["total"] == 0, rep2


def test_t7_compile_shared_inline_not_echoed():
    """连写共享行在切片展示视图:按题取值+行号引用,不整段回引他题答案。"""
    lines = ["21. 题干", "22. 题干", "23. 题干",
             r"21\. B 22\. C 23\. A 24\. B 25\. C"]
    man = {"units": [{"unit_id": "U21-23", "unit_type": "composite_question",
                      "question_numbers": [21, 22, 23],
                      "original_question_type": "reading",
                      "material_lines": [1, 1], "questions_lines": [1, 3],
                      "answer_lines": [4, 4],
                      "answer_evidence": {"type": "range_string", "lines": [4, 4],
                                          "value": "21.B 22.C 23.A", "shared": True},
                      "explanation_lines": None}]}
    md, _ = RP.compile_slices(lines, man, "x.md", "x.md")
    ans_zone = md.split("“答案区开始”")[1].split("“答案区结束”")[0]
    assert "21.B 22.C 23.A" in ans_zone
    assert "为多题共享" in ans_zone and "已按题号取值" in ans_zone
    assert r"24\. B" not in ans_zone        # 他题答案不整段回引


def test_t8_measure_answer_contamination(workdir):
    src = workdir / "src"
    out = workdir / "out"
    (src / "高三" / "英语").mkdir(parents=True)
    out.mkdir()
    lines = ["21. 题干", "22. 题干", "23. 题干",
             r"21\. B 22\. C 23\. A 24\. B 25\. C"]
    (src / "高三" / "英语" / "f.md").write_text("\n".join(lines), encoding="utf-8")
    man = {"source_file": "x", "model": "m",
           "annotation_meta": {"prompt_version": "v2.5",
                               "validation_issues": [], "warnings": []},
           "units": [{"unit_id": "U21-23", "unit_type": "composite_question",
                      "question_numbers": [21, 22, 23],
                      "original_question_type": "reading",
                      "material_lines": [1, 1], "questions_lines": [1, 3],
                      "answer_lines": [4, 4], "explanation_lines": None}]}
    (out / "高三" / "英语").mkdir(parents=True, exist_ok=True)
    (out / "高三" / "英语" / "f.manifest.json").write_text(
        json.dumps(man, ensure_ascii=False), encoding="utf-8")
    M = _load("m_p21e", os.path.join(ROOT, "scripts", "p2_1_measure.py"))
    M.SRC = src
    rec = M.measure_paper(out, {"file": str(src / "高三" / "英语" / "f.md"),
                                "subject": "英语"})
    assert rec["answer_contamination"]["shared_unmarked"] == 1
    assert rec["answer_contamination"]["total"] == 1


def test_t9_prompt_v25_boundary_semantics():
    """prompt v2.5:shared 字段 + 答案边界规则必须在 prompt 里。"""
    assert RP.PROMPT_VERSION == "reslice-pilot-v2.5"
    assert '"shared": true 或 false' in RP.PROMPT_HEAD
    assert "绝不为了\"只圈自己的\"把共享答案表切碎" in RP.PROMPT_HEAD
    assert "由 answer_lines 圈定" in RP.PROMPT_HEAD


def test_t10_answer_line_nums_formats():
    assert RP.answer_line_nums("【答案】60. While browsing") == {60}
    assert RP.answer_line_nums("2.【答案】D") == {2}
    assert RP.answer_line_nums("【答案】示例") == set()
