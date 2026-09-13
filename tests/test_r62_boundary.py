# -*- coding: utf-8 -*-
"""R62:BUG-31 修复边界回归钉(R61 结果对抗审查的固化)。
R63 转正:BUG-32/33 获批修复后 t4/t5 由 strict-xfail 翻为正式钉,
并新增 t6-t9 批处理隔离钉。

  r62_t1  source_file = null/""/空白/不存在路径/已存在目录 → 三层
          fail-closed(resolver MISSING + 理由串 / QC FAIL 含 C15 /
          F1 DRIFT,禁崩、禁降级 ADMITTED)
  r62_t2  源文件含非法 UTF-8 字节 → 三组件禁崩(errors="replace" 契约;
          resolver 如实消费 QC 裁决 REJECTED_QC_FAIL)
  r62_t3  BUG-33a 源拒读(OSError)→ resolver 兜底层活体证明
  r62_t4  BUG-32 修复钉:int/dict/list/bool source_file → 三层显式失败
  r62_t5  BUG-33 修复钉:源拒读 → QC FAIL(C15)/F1 DRIFT,禁崩
  r62_t6  BUG-32 批处理隔离:good + 坏类型 + good → 批不崩
  r62_t7  批处理隔离通用层:坏 JSON manifest → REJECTED_UNCOMPUTABLE
  r62_t8  QC 批入口隔离:坏 manifest → 显式 FAIL 行,整批不崩
  r62_t9  F1 批入口隔离 + 汇总算术完整性(n_units 快捷返回键)
"""
import ctypes
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import r60_fact_drift_attack as r60  # noqa: E402
import reslice_qc as qc              # noqa: E402

WIN32 = sys.platform == "win32"


def _stage(workdir, name):
    return r60.stage_repo(workdir / name)


def _fail_closed_assert(obs):
    assert obs["resolver"] == "MISSING", obs
    assert "source_file missing or not a file" in obs["resolver_reason_head"]
    assert obs["qc"] == "FAIL" and "qc_exc" not in obs
    assert obs["f1"] == "DRIFT" and "f1_exc" not in obs


def _no_crash(obs):
    for k in ("resolver", "qc", "f1"):
        assert obs.get(k) != "CRASH", f"{k} 崩溃: {obs.get(k + '_exc')}"


@pytest.mark.parametrize("case", ["null", "empty", "whitespace",
                                  "nonexistent", "directory"])
def test_r62_t1_provenance_value_families_fail_closed(workdir, case):
    repo = _stage(workdir, f"r62t1_{case}")
    def mutate(m):
        if case == "null":
            m.update(source_file=None)
        elif case == "empty":
            m.update(source_file="")
        elif case == "whitespace":
            m.update(source_file="   ")
        elif case == "nonexistent":
            m.update(source_file="nope.md")
        else:
            m.update(source_file=str(repo["out_dir"]))  # 已存在目录
    r60._man_edit(repo, mutate)
    obs = r60.observe(repo)
    _fail_closed_assert(obs)
    q = qc.check(repo["md"])
    assert q["verdict"] == "FAIL"
    # 消息级钉(R63):必须是 C15"缺失/非文件"家族,不得被 OSError
    # 守卫的"不可读"消息顶替——否则 is_file 守卫回退变异成为等价变异
    # (R63 实测教训,分辨率恢复后 M5/M6 重新咬合)。
    assert any("C15" in i and "非文件" in i for i in q["issues"])
    import audit_f1_consistency as af1
    f = af1.check_file(repo["md"])
    assert f["status"] == "DRIFT"
    assert "missing or not a file" in f["note"]


def test_r62_t2_invalid_utf8_source_no_crash(workdir):
    repo = _stage(workdir, "r62t2")
    repo["src"].write_bytes(repo["src"].read_bytes() + b"\x8c\x8d\xfe\xff g\n")
    obs = r60.observe(repo)
    _no_crash(obs)
    # resolver 如实消费 QC 裁决(篡改使 C8 保真失败),不是静默放行
    assert obs["resolver"] == "REJECTED_QC_FAIL"
    assert obs["qc"] == "FAIL"
    assert obs["f1"] in ("MATCH", "DRIFT")  # 区级不变量如实,禁崩为本钉主张


@pytest.mark.skipif(not WIN32, reason="独占句柄拒读为 Windows 共享语义")
def test_r62_t3_unreadable_source_resolver_backstop_live(workdir):
    """BUG-33 半边:resolver 的 except OSError 兜底层活体证明(R61 新增层)。"""
    repo = _stage(workdir, "r62t3")
    src = repo["src"]
    GENERIC_READ, OPEN_EXISTING = 0x80000000, 3
    handle = ctypes.windll.kernel32.CreateFileW(
        str(src), GENERIC_READ, 0, None, OPEN_EXISTING, 0, None)
    try:
        assert handle != -1
        with pytest.raises(OSError):
            src.read_text(encoding="utf-8")  # 条件先实证
        obs = r60.observe(repo)
        assert obs["resolver"] == "MISSING"
        assert "source unreadable" in obs["resolver_reason_head"]
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


@pytest.mark.parametrize("case,raw", [("int", 123), ("dict", {"a": 1}),
                                      ("list", ["x"]), ("bool", True)])
def test_r62_t4_non_string_source_file_fail_closed(workdir, case, raw):
    """BUG-32 修复钉(原 strict-xfail 转正):非字符串 source_file 必须
    三层显式失败(resolver MISSING / QC FAIL 含 C15 / F1 DRIFT),
    禁崩、禁 str() 强转、禁降级 ADMITTED。"""
    repo = _stage(workdir, f"r62t4_{case}")
    r60._man_edit(repo, lambda m: m.update(source_file=raw))
    obs = r60.observe(repo)
    _no_crash(obs)
    assert obs["resolver"] == "MISSING", obs
    assert "not a string" in obs["resolver_reason_head"]
    assert obs["qc"] == "FAIL" and "qc_exc" not in obs
    q = qc.check(repo["md"])
    assert any("C15" in i and "非字符串" in i for i in q["issues"])
    assert obs["f1"] == "DRIFT" and "f1_exc" not in obs


@pytest.mark.skipif(not WIN32, reason="独占句柄拒读为 Windows 共享语义")
def test_r62_t5_unreadable_source_qc_f1_fail_closed(workdir):
    """BUG-33 修复钉(原 strict-xfail 转正):源拒读时 QC/F1 必须显式
    失败态(C15 FAIL / DRIFT),与 resolver MISSING 同族,禁崩。"""
    repo = _stage(workdir, "r62t5")
    src = repo["src"]
    GENERIC_READ, OPEN_EXISTING = 0x80000000, 3
    handle = ctypes.windll.kernel32.CreateFileW(
        str(src), GENERIC_READ, 0, None, OPEN_EXISTING, 0, None)
    try:
        assert handle != -1
        with pytest.raises(OSError):
            src.read_text(encoding="utf-8")  # 条件先实证
        obs = r60.observe(repo)
        assert obs["qc"] == "FAIL" and "qc_exc" not in obs
        q = qc.check(repo["md"])
        assert any("C15" in i and "不可读" in i for i in q["issues"])
        assert obs["f1"] == "DRIFT" and "f1_exc" not in obs
        assert obs["resolver"] == "MISSING"
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def test_r62_t6_resolver_batch_isolation_bad_type(workdir):
    """BUG-32 批处理隔离(good + source_file=123 bad + good):
    批不崩、坏件显式拒收、好件正常通过。"""
    import resolver_reference as rr
    g1 = _stage(workdir, "r62t6_g1")
    bad = _stage(workdir, "r62t6_bad")
    r60._man_edit(bad, lambda m: m.update(source_file=123))
    g2 = _stage(workdir, "r62t6_g2")
    ir, rep = rr.run([g1["md"], bad["md"], g2["md"]], workdir / "r62t6_ir")
    disp = [f["disposition"] for f in ir["files"]]
    assert disp[0] == "ADMITTED", disp
    assert disp[1] == "MISSING", disp
    assert disp[2] == "ADMITTED", disp
    assert rep["dispositions"] == {"ADMITTED": 2, "MISSING": 1}


def test_r62_t7_resolver_batch_isolation_malformed_manifest(workdir):
    """批处理隔离(通用兜底层):坏 JSON manifest → REJECTED_UNCOMPUTABLE,
    不杀整批;好件不受影响。"""
    import resolver_reference as rr
    g1 = _stage(workdir, "r62t7_g1")
    bad = _stage(workdir, "r62t7_bad")
    bad["man"].write_text("{not valid json", encoding="utf-8")
    g2 = _stage(workdir, "r62t7_g2")
    ir, rep = rr.run([g1["md"], bad["md"], g2["md"]], workdir / "r62t7_ir")
    disp = [f["disposition"] for f in ir["files"]]
    assert disp == ["ADMITTED", "REJECTED_UNCOMPUTABLE", "ADMITTED"], disp


def test_r62_t8_qc_main_batch_isolation(workdir, monkeypatch, capsys):
    """QC 批入口隔离:坏 JSON manifest 单件 → 显式 FAIL 行,整批不崩。"""
    import shutil
    root = workdir / "root"
    g = _stage(workdir, "r62t8_g")
    bad = _stage(workdir, "r62t8_bad")
    bad["man"].write_text("{not valid json", encoding="utf-8")
    (root / "g").mkdir(parents=True)
    (root / "bad").mkdir()
    shutil.copytree(g["out_dir"], root / "g" / "out")     # 只搬切片目录,
    shutil.copytree(bad["out_dir"], root / "bad" / "out")  # 源不进扫描面
    monkeypatch.setattr(sys, "argv",
                        ["reslice_qc.py", "--out", str(root),
                         "--result", str(workdir / "qc_result.json")])
    qc.main()
    results = json.loads((workdir / "qc_result.json").read_text(
        encoding="utf-8"))
    by_name = {Path(r["file"]).parent.parent.name: r for r in results}
    assert by_name["g"]["verdict"] in ("PASS", "PENDING_REVIEW")
    assert by_name["bad"]["verdict"] == "FAIL"
    assert any("QC exception contained" in i
               for i in by_name["bad"]["issues"])


def test_r62_t9_f1_run_batch_isolation_and_arithmetic(workdir):
    """F1 批入口:坏 JSON manifest 单件 → 显式 DRIFT 行;汇总算术
    (n_units 键)不因快捷返回缺失而 KeyError(R63 顺带修复面)。"""
    import audit_f1_consistency as af1
    g = _stage(workdir, "r62t9_g")
    bad = _stage(workdir, "r62t9_bad")
    bad["man"].write_text("{not valid json", encoding="utf-8")
    miss = _stage(workdir, "r62t9_miss")  # source 缺失 → 快捷 DRIFT 返回
    r60._man_edit(miss, lambda m: m.update(source_file=None))
    rep = af1.run([g["md"], bad["md"], miss["md"]], workdir / "r62t9_f1")
    st = [f["status"] for f in rep["files"]]  # 行序 = 入参序
    assert st == ["MATCH", "DRIFT", "DRIFT"], st
    assert "exception contained" in rep["files"][1]["note"]
    assert "missing or not a file" in rep["files"][2]["note"]
    assert rep["summary"]["units_match"]["denominator"] > 0
