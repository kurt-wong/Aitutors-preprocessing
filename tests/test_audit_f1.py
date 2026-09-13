# -*- coding: utf-8 -*-
"""R54:F1 Structural Consistency Check(audit_f1_consistency.py)CI 契约测试。

F1 定位(用户 R53 裁决):Audit invariant only——比较 source_version_sha /
start_line / end_line / span hash 四项结构一致性,不是 Gate、不是
Resolver admission rule、不检查语义。

  f1_t1 干净产物 → 全部单元 MATCH(控制组语义)
  f1_t2 manifest span 漂移(不重编译)→ annotated 对账 DRIFT
  f1_t3 仅切片被改 → slice 对账 DRIFT
  f1_t4 源文件 span 内内容漂移(行数不变)→ span hash DRIFT
  f1_t5 确定性:两轮输出字节级一致
  f1_t6 C-OUT 纪律:输出只落 --out
  f1_t7 IR cross-check:生成 IR 后对账 MATCH;改源(行数不变)→
       source_version 不一致 → IR 对账 DRIFT,而 annotated/slice 仍 MATCH
       (精确隔离 source_version_sha 这一项检查)
  f1_t8 R-ACC-14 答案消费不变量检查器:answers∩unresolved 交集违规被咬
  f1_t9 R-ACC-14:unresolved 遗漏(未解题号既不在 answers 也不在
       unresolved)被咬
  f1_t10 R-ACC-14:空串/None 哨兵答案值被咬(下游默认值误变 admitted 面)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_f1_consistency as f1  # noqa: E402
import resolver_reference as rr  # noqa: E402
from conftest import make_repo  # noqa: E402


def _rows(report):
    return [r for f in report["files"] for r in f["units"]]


def test_f1_t1_clean_repo_all_match(workdir):
    src, _, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    report = f1.run([md], workdir / "o")
    assert report["summary"]["files_match"] == {
        "numerator": 1, "denominator": 1,
        "proof": "per-file status = MATCH iff no unit DRIFT and no "
                 "structural note"}
    rows = _rows(report)
    assert len(rows) == 3
    assert all(r["status"] == "MATCH" for r in rows)
    q1 = next(r for r in rows if r["question_id"] == "Q1")
    # 用户裁定的四项字段齐备
    assert q1["source_version_sha"] and len(q1["source_version_sha"]) == 64
    st = q1["annotated"]["stem"]
    assert st["manifest_lines"] == st["annotated_lines"] == [5, 9]
    assert st["resolver_span_hash"] == st["qc_span_hash"]
    assert st["status"] == "MATCH"


def test_f1_t2_manifest_span_drift_flagged(workdir):
    _, mf, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    man = json.loads(mf.read_text(encoding="utf-8"))
    man["units"][0]["stem_lines"] = [6, 9]  # 改 manifest 不重编译(F1 态)
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                  encoding="utf-8", newline="")
    report = f1.run([md], workdir / "o")
    q1 = next(r for r in _rows(report) if r["question_id"] == "Q1")
    assert q1["status"] == "DRIFT"
    assert q1["annotated"]["stem"]["status"] == "DRIFT"
    assert q1["annotated"]["stem"]["manifest_lines"] == [6, 9]
    assert q1["annotated"]["stem"]["annotated_lines"] == [5, 9]


def test_f1_t3_slice_only_edit_flagged(workdir):
    _, _, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    txt = md.read_text(encoding="utf-8")
    md.write_text(txt.replace("A. 甲", "A. 甲改", 1),
                  encoding="utf-8", newline="")
    report = f1.run([md], workdir / "o")
    q1 = next(r for r in _rows(report) if r["question_id"] == "Q1")
    assert q1["status"] == "DRIFT"
    assert q1["slice"]["stem_zone"]["status"] == "DRIFT"


def test_f1_t4_source_content_drift_same_lines(workdir):
    src, _, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    lines = src.read_text(encoding="utf-8").splitlines()
    lines[8] = "B. 乙漂移"  # L9,行数不变 → STALE 信号不可见,hash 必须咬
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    report = f1.run([md], workdir / "o")
    q1 = next(r for r in _rows(report) if r["question_id"] == "Q1")
    assert q1["status"] == "DRIFT"
    st = q1["annotated"]["stem"]
    assert st["manifest_lines"] == st["annotated_lines"]  # 行号一致
    assert st["resolver_span_hash"] != st["qc_span_hash"]  # 内容漂移被咬


def test_f1_t5_deterministic(workdir):
    _, _, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    f1.run([md], workdir / "o1")
    f1.run([md], workdir / "o2")
    for name in ("f1_report.json", "f1_summary.json"):
        assert ((workdir / "o1" / name).read_bytes()
                == (workdir / "o2" / name).read_bytes())


def test_f1_t6_outputs_confined(workdir):
    _, _, out_dir = make_repo(workdir)
    md = out_dir / "synthetic.md"
    o = workdir / "o"
    f1.run([md], o)
    assert sorted(p.name for p in o.iterdir()) == \
        ["f1_report.json", "f1_summary.json"]
    # summary 引用全量报告 sha(R52 摘要引用纪律)
    import hashlib
    s = json.loads((o / "f1_summary.json").read_text(encoding="utf-8"))
    assert s["full_report"]["sha256"] == hashlib.sha256(
        (o / "f1_report.json").read_bytes()).hexdigest()


def test_f1_t7_ir_crosscheck_source_version(workdir):
    import copy
    import question_identity as qi
    from conftest import SYNTH_LINES, SYNTH_MAN
    man = copy.deepcopy(SYNTH_MAN)
    qi.assign_identity(man, list(SYNTH_LINES))
    for u in man["units"]:
        u["basis"] = "printed_as_is"
        u["printed_provenance"] = "source_line"
        u["printed_number"] = list(u["question_numbers"])
    src, _, out_dir = make_repo(workdir, man=man)
    md = out_dir / "synthetic.md"
    rr.run([md], workdir / "ir")
    report = f1.run([md], workdir / "o",
                    ir_path=workdir / "ir" / "resolver_ir.json")
    rows = _rows(report)
    assert all(r["status"] == "MATCH" for r in rows)
    assert all(r["ir"]["status"] == "MATCH" for r in rows)
    # 改源首行标题(span 外,行数不变):IR source_version 必须失配,
    # 而 annotated/slice span 对账不受影响(检查项精确隔离)
    lines = src.read_text(encoding="utf-8").splitlines()
    lines[0] = "# 2024 合成测试卷(改标题)"
    src.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    report2 = f1.run([md], workdir / "o2",
                     ir_path=workdir / "ir" / "resolver_ir.json")
    rows2 = _rows(report2)
    assert all(r["ir"]["status"] == "DRIFT" for r in rows2)
    assert all(r["ir"]["source_version_match"] is False for r in rows2)
    assert all(r["ir"]["source_lines_match"] is True for r in rows2)
    assert all(r["annotated"]["stem"]["status"] == "MATCH"
               for r in rows2 if "stem" in r["annotated"])


def _table(ans_map, unresolved, cells=None):
    """真实 IR 形状(R54 实测):unit["answers"] =
    {cells, method, answers, unresolved} 表对象。"""
    return {"cells": cells or [], "method": "td_positional",
            "answers": ans_map, "unresolved": unresolved}


def _unit(tbl, qnums):
    return {"unit_id": "X", "question_numbers": qnums, "answers": tbl}


def _ir(units):
    return {"ir_version": "resolver-ir-0.1", "files": [
        {"file": "x.md", "disposition": "ADMITTED",
         "ir": {"units": units}}]}


def test_f1_t8_answer_unresolved_overlap_flagged():
    doc = _ir([_unit(_table({"1": "1. A"}, [1, 2]), [1, 2])])
    findings = f1.audit_ir_answers(doc)
    assert any("overlap" in x for x in findings)


def test_f1_t9_unresolved_missing_flagged():
    # 题 2 既不在 answers 也不在 unresolved → 会被下游静默丢弃
    doc = _ir([_unit(_table({"1": "1. A"}, []), [1, 2])])
    findings = f1.audit_ir_answers(doc)
    assert any("missing_from_unresolved" in x for x in findings)


def test_f1_t10_sentinel_answer_values_flagged():
    for bad in ("", None):
        doc = _ir([_unit(_table({"1": bad}, [2]), [1, 2])])
        findings = f1.audit_ir_answers(doc)
        assert any("sentinel" in x for x in findings), bad
    # 干净态零 findings(检查器非恒报)
    doc = _ir([_unit(_table({"1": "1. A"}, [2]), [1, 2])])
    assert f1.audit_ir_answers(doc) == []


def test_f1_t11_table_shape_violation_flagged():
    # 表对象缺内层 answers/unresolved 键(schema 漂移)必须显式报,
    # 不得静默按空处理(R54 首版检查器 schema 误读的防回归)
    doc = _ir([_unit({"cells": ["1. A"]}, [1])])
    findings = f1.audit_ir_answers(doc)
    assert any("shape" in x for x in findings)
