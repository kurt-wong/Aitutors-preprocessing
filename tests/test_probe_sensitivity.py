# -*- coding: utf-8 -*-
"""语义探针(P13/P14/P15)灵敏度回归(R46 对抗审查固化)。

R46 在真实产物上验证了双向灵敏度(注入必报 + 已知无害形态必不报);
本文件用合成语料把双向契约钉进 CI。探针报警≠缺陷的分诊纪律不变,
这里只锁"测量仪还能不能测到"。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import semantic_probe as sp  # noqa: E402
from conftest import make_repo  # noqa: E402


def _probe(mf):
    return sp.probe_file(mf)["flags"]


def _load(mf):
    return json.loads(mf.read_text(encoding="utf-8"))


def _save(mf, man):
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="")


def _files(out_dir, stem="synthetic"):
    return out_dir / f"{stem}.manifest.json"


def test_control_synth_zero_flags(workdir):
    _, _, out_dir = make_repo(workdir)
    assert _probe(_files(out_dir)) == []


def test_p14_stem_eats_next_question_fires(workdir):
    """stem 区间吞入下一题题号行 → P14 必报。"""
    _, _, out_dir = make_repo(workdir)
    mf = _files(out_dir)
    man = _load(mf)
    man["units"][0]["stem_lines"] = [5, 11]  # 覆盖到 L11 "2. 第二题题干"
    _save(mf, man)
    flags = _probe(mf)
    assert any(f["check"] == "P14" and f["unit"] == "Q1" for f in flags), flags


def test_p15_answer_points_other_question_fires(workdir):
    """answer 区间含别题题号+答案行 → P15 必报。"""
    _, _, out_dir = make_repo(workdir)
    mf = _files(out_dir)
    man = _load(mf)
    man["units"][0]["answer_lines"] = [25, 28]  # 含 L28 "2.【答案】B"
    _save(mf, man)
    flags = _probe(mf)
    assert any(f["check"] == "P15" and f["unit"] == "Q1" for f in flags), flags


def test_p13_answer_without_answer_form_fires(workdir):
    """answer 指向纯散文行 → P13 必报(答案虚指)。"""
    _, _, out_dir = make_repo(workdir)
    mf = _files(out_dir)
    man = _load(mf)
    man["units"][0]["answer_lines"] = [17, 17]  # "材料内容甲乙丙。"
    _save(mf, man)
    flags = _probe(mf)
    assert any(f["check"] == "P13" and f["unit"] == "Q1" for f in flags), flags


def test_negative_step_number_not_qnum(workdir):
    """解答步骤编号行("1、目的基因的获取:")不构成 P14(阴性对照)。"""
    src, _, out_dir = make_repo(workdir)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write("\n1、目的基因的获取：PCR扩增\n")
    mf = _files(out_dir)
    man = _load(mf)
    n = len(src.read_text(encoding="utf-8").splitlines())
    man["units"][0]["stem_lines"] = [n, n]
    _save(mf, man)
    assert _probe(mf) == []


def test_negative_range_answer_not_p13(workdir):
    """区间连写答案("1-2 AB")不算答案虚指(阴性对照)。"""
    src, _, out_dir = make_repo(workdir)
    with open(src, "a", encoding="utf-8", newline="") as f:
        f.write("\n1-2 AB\n")
    mf = _files(out_dir)
    man = _load(mf)
    n = len(src.read_text(encoding="utf-8").splitlines())
    man["units"][0]["answer_lines"] = [n, n]
    _save(mf, man)
    assert _probe(mf) == []
