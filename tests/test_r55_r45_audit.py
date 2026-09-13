# -*- coding: utf-8 -*-
"""R55:R45 声明对抗性审查工具(r55_r45_audit.py)CI 契约测试。

钉住本轮抓获并修复的两处审计工具自身缺陷(F-r55-4)与核心判据函数:
  r55_t1  M1 printed/canonical 错位族:P14 亦须触发(首版错误限定 P15)
  r55_t2  OCR 转义点行首(`1\\.`)必须可解析(首版正则漏检)
  r55_t3  M2 括号答案键连写(P13,≥2 括号题号)
  r55_t4  M3 子问编号行首(`1）`/`1)`)
  r55_t5  M4 写作提示/评分细则关键词
  r55_t6  M5 P13 格式盲区(答案内容在)
  r55_t7  残差分诊桶:略/解析/紧凑/字母超A-D/essay 单元/printed=None/
          题干内编号 逐桶命中 + 干净行走末桶
  r55_t8  coverage_check:完美卷 / 缺号 / 重号
  r55_t9  md_of 路径派生(pac-x.manifest.json → pac-x.md;回归
          with_suffix 只剥 .json 的陷阱——本轮 M-b 实际踩坑)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from r55_r45_audit import (classify_alarm, coverage_check, md_of,  # noqa: E402
                           residual_bucket)


def _row(check, sample, unit="Q1", detail="", file="x.manifest.json"):
    return {"check": check, "sample": sample, "unit": unit,
            "detail": detail, "file": file}


def test_r55_t1_m1_fires_on_p14_printed_mismatch():
    row = _row("P14", "2. （3分）选择装置，完成实验。", unit="Q27")
    label, ev = classify_alarm(row, [2], [27])
    assert label == "M1" and ev["sample_num"] == 2
    # 反例:号 ∈ canon → 不得进 M1
    row2 = _row("P14", "27. （3分）选择装置。", unit="Q27")
    assert classify_alarm(row2, [2], [27])[0] != "M1"


def test_r55_t2_escaped_dot_prefix():
    row = _row("P14", r"1\. （3分）补齐物质及其用途的连线。", unit="Q26")
    label, ev = classify_alarm(row, [1], [26])
    assert label == "M1" and ev["sample_num"] == 1


def test_r55_t3_m2_paren_answer_keys():
    row = _row("P13", r"(21)  $ [0,+\infty) $. (22)  $ \underline{2} $",
               unit="Q21")
    assert classify_alarm(row, [], [21])[0] == "M2"


def test_r55_t4_m3_subquestion_prefix():
    row = _row("P14", "1）当小球的角速度为 10rad/s 时，细线拉力大小；",
               unit="Q24")
    assert classify_alarm(row, [24], [24])[0] == "M3"


def test_r55_t5_m4_essay_rubric():
    row = _row("P15", "2. 语言准确性：包括语法、用词、拼写等要素。",
               unit="U-Essay-44")
    assert classify_alarm(row, [], [44])[0] == "M4"


def test_r55_t6_m5_p13_format_blindspot():
    row = _row("P13", "9.1 10.-1 11.(0,2) 12.1 13.a<0 14.①②⑤",
               unit="Q9")
    assert classify_alarm(row, [], [9])[0] == "M5"


def test_r55_t7_residual_buckets():
    cases = [
        (("P13", "## （27） 略"), "略式答案"),
        (("P13", "24. （6分）【解析】"), "散文式解析答案"),
        (("P13", "9.1 10.-1 11.(0,2)"), "紧凑答案行"),
        (("P13", "35-39 DEFGB"), "答案键字母超A-D"),
        (("P13", "7. （5分）（1）Na（2）H2O"), "括号子问答案连写"),
        (("P14", "2. 不能参加的原因："), "写作提示/评分细则"),  # essay 单元
        (("P14", "1. 补齐连线。"), "printed=None题号族"),
        (("P14", "1. 削弱了帝国主义和殖民主义力量"), "题干/材料内编号"),
    ]
    for (chk, sample), want in cases:
        unit = "U-Essay-44" if want == "写作提示/评分细则" else "Q1"
        printed = [] if want in ("写作提示/评分细则",
                                 "printed=None题号族") else [1]
        got, ev = residual_bucket(_row(chk, sample, unit=unit), printed)
        assert got == want, (sample, got, want, ev)


def test_r55_t8_coverage_check():
    man = {"units": [
        {"unit_id": "A", "question_numbers": [1, 2]},
        {"unit_id": "B", "question_numbers": [3]}]}
    assert coverage_check(man)["ok"] is True
    man2 = {"units": [{"unit_id": "A", "question_numbers": [1, 3]}]}
    c2 = coverage_check(man2)
    assert c2["ok"] is False and c2["missing"] == [2]
    man3 = {"units": [
        {"unit_id": "A", "question_numbers": [1]},
        {"unit_id": "B", "question_numbers": [1]}]}
    c3 = coverage_check(man3)
    assert c3["ok"] is False and "1" in c3["dups"]


def test_r55_t9_md_of_no_suffix_trap():
    p = Path("Ocr-markdown/reslice-pac-annotated/reslice-pac/ocr/"
             "pac-c01-01.manifest.json")
    assert md_of(p).name == "pac-c01-01.md"
    # with_suffix 陷阱回归:若实现回退为 with_suffix('.md') 会得到
    # pac-c01-01.manifest.md —— 本断言即钉死正确行为
    assert md_of(p).name != "pac-c01-01.manifest.md"
