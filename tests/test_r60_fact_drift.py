# -*- coding: utf-8 -*-
"""R60:Source → Resolver → IR 事实漂移攻击的回归钉(CI 离线,合成语料)。

用户 R59 裁定的四攻击面,逐面钉住实测边界(不粉饰:凡 resolver 层静默的
如实钉"静默 + F1 捕获",凡防线在 QC 层的如实钉防线身份):

  t1  A1 界内字节篡改 → 非 STALE,由 C8(整文件锚点保真)拦,REJECTED_QC_FAIL
  t2  A2 span 外字节篡改 → C8 拦;F1 如实 MATCH(F1 是区级不变量,
      看不见 span 外漂移——C8 与 F1 互补,谁都不是全集)
  t3  A3 旧 IR + 篡改源 → F1 ir 对账 source_version_match=False → DRIFT
  t4  B1 start-1 界内平移 → **resolver 静默 ADMITTED(已裁定边界)**,
      F1 捕获 DRIFT;IR 题干内容实测被平移(事实漂移坐实)
  t5  B2 end+1 越界 → REJECTED_STALE(结构信号)
  t6  B3 answer end+1 界内 → 同 B1 家族:ADMITTED + F1 捕获
  t7  C1 manifest 缺 source_file → BUG-31 修复后(R61)三层 fail-closed:
      resolver MISSING / QC FAIL(C15)/ F1 DRIFT,禁崩;并验证批处理
      记录原因后继续处理其它单元(t7b)
  t8  C2 source_file 重定向诱饵 → C8 拦 + F1 全区 DRIFT
  t9  C3 IR provenance.source_version 删除 → F1 ir DRIFT
  t10 D1 只改 manifest 不重编译 → resolver+QC 双绿而答案归属已错位,
      F1 必须 DRIFT(QC 看到 A、Resolver 看到 B 的分叉证明)
  t11 D2 对照组未变异 → 全绿(阴性对照)
  t12 攻击报告确定性:两次运行字节级一致
  t13 语料冒烟(skipif 无语料 → CI SKIPPED):88 份真实控制组 F1 复核
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import r60_fact_drift_attack as r60  # noqa: E402

CORPUS = ROOT / "data/resolver_contract_preflight.json"


def _fresh(workdir, name):
    d = workdir / name
    return d


# ------------------------------------------------------------------ A 面

def test_t1_a1_in_span_byte_edit_caught_by_c8(workdir):
    obs = r60.attack_A(_fresh(workdir, "t1"))["A1_stem_byte_edit"]
    # 不是 STALE(行数不变,span 界内)——防线身份如实:C8 整文件锚点保真
    assert obs["resolver"] == "REJECTED_QC_FAIL"
    assert "C8" in obs["resolver_reason_head"]
    assert obs["qc"] == "FAIL"
    assert obs["f1"] == "DRIFT"


def test_t2_a2_out_of_span_edit_c8_catches_f1_zone_scoped(workdir):
    obs = r60.attack_A(_fresh(workdir, "t2"))["A2_outside_span_edit"]
    assert obs["resolver"] == "REJECTED_QC_FAIL"
    assert "C8" in obs["resolver_reason_head"]
    # F1 是区级不变量:span 外漂移如实 MATCH——与 C8 互补,不得互相冒充
    assert obs["f1"] == "MATCH"
    assert obs["f1_drift_zones"] == []


def test_t3_a3_stale_ir_vs_edited_source_drift(workdir):
    obs = r60.attack_A(_fresh(workdir, "t3"))["A3_stale_ir_then_edit"]
    assert obs["f1"] == "DRIFT"
    assert obs["f1_ir_zone"]["source_version_match"] is False
    assert obs["f1_ir_zone"]["status"] == "DRIFT"


# ------------------------------------------------------------------ B 面

def test_t4_b1_start_minus_1_silent_at_resolver_caught_by_f1(workdir):
    obs = r60.attack_B(_fresh(workdir, "t4"))["B1_start_minus_1_in_bounds"]
    # 边界事实(resolver 结构性 STALE 语义,R53 用户裁定不扩大):
    # 界内平移 resolver 静默放行且内容实测被平移
    assert obs["resolver"] == "ADMITTED"
    assert obs["resolver_content_q1_stem"][0] == ""  # 多吸入 L4 空行
    assert obs["qc"] == "PASS"
    # 捕获层 = F1(annotated 锚点 vs manifest 行号漂移)
    assert obs["f1"] == "DRIFT"
    assert "DRIFT:stem" in obs["f1_drift_zones"]


def test_t5_b2_end_plus_1_oob_rejected_stale(workdir):
    obs = r60.attack_B(_fresh(workdir, "t5"))["B2_end_plus_1_oob"]
    assert obs["resolver"] == "REJECTED_STALE"
    assert "STALE" in obs["resolver_reason_head"]
    assert obs["f1"] == "DRIFT"


def test_t6_b3_answer_end_plus_1_in_bounds_same_family(workdir):
    obs = r60.attack_B(_fresh(workdir, "t6"))[
        "B3_answer_end_plus_1_in_bounds"]
    assert obs["resolver"] == "ADMITTED"
    assert obs["qc"] == "PASS"
    assert obs["f1"] == "DRIFT"
    assert "DRIFT:answer" in obs["f1_drift_zones"]


# ------------------------------------------------------------------ C 面

def test_t7_c1_missing_source_file_fails_closed(workdir):
    """BUG-31 修复转正(R61):缺 source_file → 三层全部显式失败态,禁崩。"""
    obs = r60.attack_C(_fresh(workdir, "t7"))["C1_manifest_no_source_file"]
    assert obs["resolver"] == "MISSING", (
        f"resolver 非 fail-closed:{obs['resolver']} ({obs.get('resolver_exc')})")
    assert "source_file missing or not a file" in obs["resolver_reason_head"]
    assert obs["qc"] == "FAIL" and "qc_exc" not in obs
    assert obs["f1"] == "DRIFT" and "f1_exc" not in obs
    # QC 显式理由含 C15(独立直查,不依赖 observe 采样字段)
    r = r60.stage_repo(workdir / "t7b")
    r60._man_edit(r, lambda m: m.pop("source_file"))
    import reslice_qc as _qc
    q = _qc.check(r["md"])
    assert q["verdict"] == "FAIL"
    assert any("C15" in i for i in q["issues"])


def test_t7b_batch_continues_after_provenance_break(workdir):
    """用户裁定要求:记录原因 + 继续处理其它单元(一份坏 manifest 不杀整批)。"""
    import resolver_reference as rr
    good = r60.stage_repo(workdir / "t7c" / "good")
    bad = r60.stage_repo(workdir / "t7c" / "bad")
    r60._man_edit(bad, lambda m: m.pop("source_file"))
    _, report = rr.run([good["md"], bad["md"]], workdir / "t7c" / "ir_out")
    assert report["dispositions"] == {"ADMITTED": 1, "MISSING": 1}
    assert report["files"]["numerator"] == 1
    assert report["files"]["denominator"] == 2


def test_t8_c2_source_retarget_decoy_caught(workdir):
    obs = r60.attack_C(_fresh(workdir, "t8"))["C2_source_retarget_decoy"]
    assert obs["resolver"] == "REJECTED_QC_FAIL"
    assert "C8" in obs["resolver_reason_head"]
    assert obs["qc"] == "FAIL"
    assert obs["f1"] == "DRIFT"
    assert len(obs["f1_drift_zones"]) >= 6  # 全区漂移


def test_t9_c3_ir_provenance_deleted_drift(workdir):
    obs = r60.attack_C(_fresh(workdir, "t9"))["C3_ir_provenance_deleted"]
    assert obs["f1"] == "DRIFT"
    assert obs["f1_ir_zone"]["source_version_match"] is False


# ------------------------------------------------------------------ D 面

def test_t10_d1_recut_no_recompile_both_green_f1_must_drift(workdir):
    obs = r60.attack_D(_fresh(workdir, "t10"))["D1_recut_no_recompile"]
    # 分叉坐实:QC 看切片(旧)、Resolver 看 manifest(新),双方各自"正确"
    assert obs["resolver"] == "ADMITTED"
    assert obs["qc"] == "PASS"
    # 系统级唯一防线:F1 必须报 DRIFT(答案归属漂移坐实见 t10b)
    assert obs["f1"] == "DRIFT"
    assert "DRIFT:answer" in obs["f1_drift_zones"]


def test_t10b_d1_ir_answer_misattribution_realized(workdir):
    res = r60.attack_D(_fresh(workdir, "t10b"))
    assert res["D1_ir_q1_answer"] == ["2.【答案】B"]


def test_t11_d2_control_all_green(workdir):
    obs = r60.attack_D(_fresh(workdir, "t11"))["D2_control_untouched"]
    assert obs["resolver"] == "ADMITTED"
    assert obs["qc"] == "PASS"
    assert obs["f1"] == "MATCH"
    assert obs["f1_drift_zones"] == []


# ------------------------------------------------------------------ 工具性质

def test_t12_report_deterministic(workdir):
    r1 = r60.run_attacks(_fresh(workdir, "d1"))
    r2 = r60.run_attacks(_fresh(workdir, "d2"))
    b1 = json.dumps(r1, ensure_ascii=False, sort_keys=True).encode("utf-8")
    b2 = json.dumps(r2, ensure_ascii=False, sort_keys=True).encode("utf-8")
    assert b1 == b2, "攻击报告非确定性(含路径/时间戳泄漏)"


@pytest.mark.skipif(
    not CORPUS.exists(), reason="corpus preflight absent (CI)")
def test_t13_corpus_control_group_f1_recheck(workdir):
    rep = r60.corpus_recheck()
    if rep.get("status") == "SKIPPED":
        pytest.skip("corpus files absent (CI)")
    assert rep["files"]["numerator"] == rep["files"]["denominator"] > 0
    assert rep["units"]["numerator"] == rep["units"]["denominator"] > 0
    assert rep["units_drift"] == 0
