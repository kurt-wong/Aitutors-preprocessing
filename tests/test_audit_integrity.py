# -*- coding: utf-8 -*-
"""R50:审计治理机制(Input Integrity Gate + Audit Snapshot Manifest)契约测试。

  t1 gate 放行:输入集未变 → 通过;
  t2 gate 变异注入:执行期间改写输入 → RuntimeError 且指出漂移文件;
  t3 gate 输入缺失 → RuntimeError;
  t4 record→verify 回路:快照与当前一致 → ok;
  t5 快照后改写/删除文件 → verify 报 drift/missing(变异注入);
  t6 record 字节确定性:同一输入集两次快照 JSON 字节全等(无时间戳);
  t7 inputs_from_preflight 推导完整输入面(md/manifest/annotated/源)且去重;
  t8 record 输入缺失 → FileNotFoundError(fail-closed,不静默跳过)。

注:DSH 沙箱下系统 temp 不可写,pytest 内建 tmp_path 不可用,
用 conftest.workdir(仓库内 .pytest_work 自管目录)。
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_integrity as ai  # noqa: E402


def _mk_inputs(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    a = d / "a.md"
    b = d / "sub_b.md"
    a.write_text("alpha\nbeta\n", encoding="utf-8", newline="")
    b.write_text("gamma\n", encoding="utf-8", newline="")
    return [a, b]


def test_gate_passes_when_unchanged(workdir):
    paths = _mk_inputs(workdir)
    before = ai.gate_snapshot(paths, root=workdir)
    assert ai.gate_assert_unchanged(before, paths, "t1", root=workdir)


def test_gate_detects_input_mutation(workdir):
    paths = _mk_inputs(workdir)
    before = ai.gate_snapshot(paths, root=workdir)
    paths[0].write_text("alpha\nBETA-MUTATED\n", encoding="utf-8",
                        newline="")
    with pytest.raises(RuntimeError, match="a.md"):
        ai.gate_assert_unchanged(before, paths, "t2", root=workdir)


def test_gate_detects_missing_input(workdir):
    paths = _mk_inputs(workdir)
    before = ai.gate_snapshot(paths, root=workdir)
    paths[1].unlink()
    with pytest.raises(RuntimeError, match="missing"):
        ai.gate_assert_unchanged(before, paths, "t3", root=workdir)


def test_record_verify_roundtrip(workdir):
    paths = _mk_inputs(workdir)
    rec = ai.record("t4", paths, metrics={"units": 2}, root=workdir)
    assert rec["n_files"] == 2 and rec["metrics"]["units"] == 2
    out = ai.write_record(rec, root=workdir)
    assert out.exists()
    loaded = ai.load_record("t4", root=workdir)
    assert ai.verify(loaded, root=workdir)["ok"]


def test_verify_detects_drift_and_missing(workdir):
    paths = _mk_inputs(workdir)
    rec = ai.record("t5", paths, root=workdir)
    paths[0].write_text("drifted\n", encoding="utf-8", newline="")
    paths[1].unlink()
    res = ai.verify(rec, root=workdir)
    assert not res["ok"]
    assert res["drift"] == ["a.md"] and res["missing"] == ["sub_b.md"]


def test_record_is_byte_deterministic(workdir):
    paths = _mk_inputs(workdir)
    r1 = ai.record("t6a", paths, metrics={"k": 1}, root=workdir)
    r2 = ai.record("t6b", paths, metrics={"k": 1}, root=workdir)
    r1.pop("audit_id"), r2.pop("audit_id")
    assert (json.dumps(r1, ensure_ascii=False, indent=1)
            == json.dumps(r2, ensure_ascii=False, indent=1))
    assert len(r1["corpus_sha256"]) == 64


def test_inputs_from_preflight_full_surface(workdir):
    d = workdir / "corpus"
    d.mkdir(parents=True)
    src = d / "src.md"
    src.write_text("1. stem\n", encoding="utf-8", newline="")
    md = d / "doc.md"
    md.write_text("slice\n", encoding="utf-8", newline="")
    md.with_suffix(".annotated.md").write_text(
        "ann\n", encoding="utf-8", newline="")
    man = {"source_file": str(src), "units": []}
    md.with_suffix(".manifest.json").write_text(
        json.dumps(man), encoding="utf-8", newline="")
    pf = workdir / "pf.json"
    pf.write_text(json.dumps({"rows": [{"file": "corpus/doc.md"}]}),
                  encoding="utf-8", newline="")
    paths = ai.inputs_from_preflight(pf, root=workdir)
    names = sorted(p.name for p in paths)
    assert names == ["doc.annotated.md", "doc.manifest.json", "doc.md",
                     "pf.json", "src.md"]
    assert len(paths) == len(set(paths))  # 去重


def test_record_fails_closed_on_missing_input(workdir):
    paths = _mk_inputs(workdir)
    paths.append(workdir / "ghost.md")
    with pytest.raises(FileNotFoundError):
        ai.record("t8", paths, root=workdir)
