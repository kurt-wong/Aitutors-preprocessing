# -*- coding: utf-8 -*-
"""R52:参考 Resolver(resolver_reference.py)的 CI 契约测试(合成语料)。

逐条对应冻结契约验收标准(R-ACC)的 CI 可离线部分:
  t1  PASS v2 → ADMITTED;身份字段与 manifest 逐字段相等(R-ACC-3,
      C-IN-4/5 只读不重塑);provenance 一等公民字段齐全(R-ACC-11,
      C-OUT-2);材料去重引用(shared material 不复制);
  t2  v1 输入 → REJECTED_V1 fail-closed(R-ACC-1,C-IN-1);
  t3  QC FAIL → REJECTED_QC_FAIL,不产生 IR(R-ACC-2,C-IN-2/3);
  t4  PENDING_REVIEW → ADMITTED_PENDING_REVIEW,永不自动 PASS
      (R-ACC-2,C-FAIL-2,Admission 通道);
  t5  STALE(源被截断,span 越界)→ REJECTED_STALE(R-ACC-11,C-FAIL-1);
  t6  MISSING(源缺失)→ MISSING(R-ACC-11,C-FAIL-1);
  t7  答案表 td:键位形态按题号取 / 位置形态按序对齐 / 推不出标
      unresolved 不猜(C-IN-7,R-ACC-6 的 CI 级);
  t8  answer 区题号与本单元无关 → answer_number_mismatch flag,
      不重绑不崩(C-IN-6,R-ACC-5);
  t9  跨节重号(非 keep)→ QC FAIL 拒收,basis 不被重解释
      (R-ACC-9,C-IN-5);
  t10 C-OUT-1:输出只落在 --out 目录(恰好 2 个文件);
  t11 确定性:两次 run 输出字节级一致;
  t12 R-ACC-4 import 面:resolver 不含任何身份推断逻辑(不 import
      question_identity/check_identity,身份唯一来源 = manifest 字段)。
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import question_identity as qi  # noqa: E402
import resolver_reference as rr  # noqa: E402
from conftest import make_repo, SYNTH_LINES, SYNTH_MAN  # noqa: E402

IDENTITY_KEYS = ("question_numbers", "printed_number", "printed_provenance",
                 "basis", "basis_evidence", "section_ref", "unit_id",
                 "unit_type")


def _v2_man():
    man = copy.deepcopy(SYNTH_MAN)
    qi.assign_identity(man, list(SYNTH_LINES))
    for u in man["units"]:
        u["basis"] = "printed_as_is"
        u["printed_provenance"] = "source_line"
        u["printed_number"] = list(u["question_numbers"])
    return man


def _repo(workdir, man=None):
    src, _, out_dir = make_repo(workdir, lines=list(SYNTH_LINES),
                                man=man if man is not None else _v2_man())
    return out_dir / "synthetic.md"


def test_t1_admitted_identity_readonly_and_provenance(workdir):
    md = _repo(workdir)
    man = json.loads(md.with_suffix(".manifest.json").read_text(
        encoding="utf-8"))
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "ADMITTED" and rec["qc_verdict"] == "PASS"
    ir = rec["ir"]
    assert ir["qc_verdict"] == "PASS"
    by_id = {u["unit_id"]: u for u in ir["units"]}
    assert len(ir["units"]) == len(man["units"])
    for mu in man["units"]:  # R-ACC-3:身份字段逐字段只读搬运
        iu = by_id[mu["unit_id"]]
        for k in IDENTITY_KEYS:
            assert iu[k] == mu.get(k), f"{mu['unit_id']}.{k} 被重塑"
        prov = iu["provenance"]  # R-ACC-11 / C-OUT-2 一等公民 provenance
        for k in ("source_file", "source_version", "source_lines",
                  "manifest_file", "qc_verdict", "extraction_method",
                  "confidence_state"):
            assert k in prov and prov[k] is not None
        assert prov["confidence_state"].startswith("structural_only")
    # 共享材料去重:综合题 material 一条,两个子题不复制
    mats = ir["materials"]
    assert len(mats) == 1
    (entry,) = mats.values()
    assert entry["text"] == SYNTH_LINES[15:17]
    comp = by_id["U3-4"]
    assert comp["material_ref"] in mats
    assert by_id["Q1"]["material_ref"] is None
    # 行号锚定:内容 = 源行切片(C-IN-8)
    assert by_id["Q1"]["content"]["answer_lines"] == ["1.【答案】A"]


def test_t2_v1_rejected(workdir):
    md = _repo(workdir, man=copy.deepcopy(SYNTH_MAN))  # 无 identity 字段 = v1
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "REJECTED_V1" and rec["ir"] is None


def test_t3_qc_fail_rejected(workdir):
    man = _v2_man()
    man["units"][0]["answer_lines"] = None  # C3 缺答案区 → QC FAIL
    md = _repo(workdir, man=man)
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "REJECTED_QC_FAIL"
    assert rec["ir"] is None and rec["reasons"]


def test_t4_pending_review_admission_channel(workdir):
    man = _v2_man()
    man["units"][0].pop("section_ref")  # C14 → PENDING_REVIEW(R41 B-03 形态)
    md = _repo(workdir, man=man)
    rec = rr.resolve_file(md)
    assert rec["qc_verdict"] == "PENDING_REVIEW"
    assert rec["disposition"] == "ADMITTED_PENDING_REVIEW"
    assert rec["disposition"] != "ADMITTED"  # 永不自动转 PASS


def test_t5_stale_rejected(workdir):
    md = _repo(workdir)
    src = Path(json.loads(md.with_suffix(".manifest.json").read_text(
        encoding="utf-8"))["source_file"])
    lines = src.read_text(encoding="utf-8").splitlines()
    src.write_text("\n".join(lines[:10]) + "\n", encoding="utf-8",
                   newline="")  # 截断源 → span 越界
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "REJECTED_STALE" and rec["ir"] is None


def test_t6_missing_source(workdir):
    md = _repo(workdir)
    src = Path(json.loads(md.with_suffix(".manifest.json").read_text(
        encoding="utf-8"))["source_file"])
    src.unlink()
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "MISSING" and rec["ir"] is None


def test_t7_answer_table_td_by_question_number():
    line = '<table><tr><td>1. A</td><td>2. B</td></tr></table>'
    keyed = rr.parse_answer_table(line, [1, 2])
    assert keyed["method"] == "td_by_question_number"
    assert keyed["answers"] == {"1": "1. A", "2": "2. B"}
    assert keyed["unresolved"] == []
    # 键位缺题 → 该题 unresolved,不猜
    partial = rr.parse_answer_table(line, [1, 5])
    assert partial["answers"] == {"1": "1. A"} and partial["unresolved"] == [5]
    # 纯位置形态 → 按序对齐;数量不符 → 全 unresolved
    pos = rr.parse_answer_table("<table><tr><td>A</td><td>B</td></tr></table>",
                                [3, 4])
    assert pos["method"] == "td_positional"
    assert pos["answers"] == {"3": "A", "4": "B"}
    bad = rr.parse_answer_table("<table><tr><td>A</td></tr></table>", [3, 4])
    assert bad["answers"] == {} and bad["unresolved"] == [3, 4]


def test_t8_answer_number_mismatch_flag_no_rebind():
    flags = rr._answer_flags(["10.【答案】A"], [20])
    assert flags == ["answer_number_mismatch"]
    assert rr._answer_flags(["20.【答案】A"], [20]) == []
    assert rr._answer_flags(None, [20]) == []


def test_t9_cross_section_dup_fail_closed_basis_untouched(workdir):
    man = _v2_man()
    man["units"][1]["question_numbers"] = [1]  # 与 unit0 重号(非 keep)
    md = _repo(workdir, man=man)
    rec = rr.resolve_file(md)
    assert rec["disposition"] == "REJECTED_QC_FAIL" and rec["ir"] is None
    # basis 不被 resolver 重解释:manifest 原值保持
    saved = json.loads(md.with_suffix(".manifest.json").read_text(
        encoding="utf-8"))
    assert saved["units"][1]["basis"] == "printed_as_is"


def test_t10_c_out_1_outputs_confined(workdir):
    md = _repo(workdir)
    out_dir = workdir / "ir_out"
    _, report = rr.run([md], out_dir)
    assert sorted(p.name for p in out_dir.iterdir()) == \
        ["resolver_ir.json", "resolver_report.json"]
    assert report["files"] == {
        "numerator": 1, "denominator": 1,
        "proof": "qc.check verdict==PASS via reslice_qc.check"}
    assert report["dispositions"] == {"ADMITTED": 1}
    assert report["units_in_ir"]["numerator"] == 3


def test_t11_run_deterministic(workdir):
    md = _repo(workdir)
    rr.run([md], workdir / "o1")
    rr.run([md], workdir / "o2")
    for name in ("resolver_ir.json", "resolver_report.json"):
        b1 = (workdir / "o1" / name).read_bytes()
        b2 = (workdir / "o2" / name).read_bytes()
        assert b1 == b2, f"{name} 非确定性"


def test_t12_import_surface_no_identity_inference():
    src = (ROOT / "scripts/resolver_reference.py").read_text(
        encoding="utf-8")
    assert "import question_identity" not in src
    assert "check_identity" not in src
    assert "import reslice_qc" in src  # 唯一裁决来源 = 生产共用 QC
