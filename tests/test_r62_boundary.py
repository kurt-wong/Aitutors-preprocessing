# -*- coding: utf-8 -*-
"""R62:BUG-31 修复边界回归钉(R61 结果对抗审查的固化)。

  r62_t1  source_file = null/""/空白/不存在路径/已存在目录 → 三层
          fail-closed(resolver MISSING + 理由串 / QC FAIL 含 C15 /
          F1 DRIFT,禁崩、禁降级 ADMITTED)
  r62_t2  源文件含非法 UTF-8 字节 → 三组件禁崩(errors="replace" 契约;
          resolver 如实消费 QC 裁决 REJECTED_QC_FAIL)
  r62_t3  BUG-33a 源拒读(OSError)→ resolver 兜底层活体证明(现即通过)
  r62_t4  BUG-32 义务钉(strict xfail):非字符串 source_file 必须
          fail-closed,现状三组件 TypeError 崩 → 修复转正时强制翻绿
  r62_t5  BUG-33 义务钉(strict xfail):源拒读时 QC/F1 必须显式失败态,
          现状 CRASH → 修复转正时强制翻绿
"""
import ctypes
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
    assert any("C15" in i for i in q["issues"])


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


@pytest.mark.xfail(
    strict=True,
    reason="BUG-32 修复义务钉:非字符串 source_file 必须 fail-closed,"
           "现状三组件 TypeError 崩且批处理整批死(R62 K7-K10/K13)")
def test_r62_t4_non_string_source_file_must_fail_closed(workdir):
    repo = _stage(workdir, "r62t4")
    r60._man_edit(repo, lambda m: m.update(source_file=123))
    obs = r60.observe(repo)
    _no_crash(obs)
    assert obs["resolver"] != "ADMITTED"  # 缺事实禁降级


@pytest.mark.skipif(not WIN32, reason="独占句柄拒读为 Windows 共享语义")
@pytest.mark.xfail(
    strict=True,
    reason="BUG-33 修复义务钉:源拒读时 QC/F1 必须显式失败态,现状 CRASH"
           "(resolver 已兜底;r62_t3 单独钉其正确性)")
def test_r62_t5_unreadable_source_qc_f1_must_fail_closed(workdir):
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
        assert obs["qc"] != "CRASH" and "qc_exc" not in obs
        assert obs["f1"] != "CRASH" and "f1_exc" not in obs
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)
