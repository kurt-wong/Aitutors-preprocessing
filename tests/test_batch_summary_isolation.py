# -*- coding: utf-8 -*-
"""BUG-28 回归:batch summary 路径必须随 --out 隔离,不得冲掉生产 batch-C 证据工件。

Gate 首攻面(PAC)批注前实测发现:derive_run_paths 已隔离 log/result,
但 batch summary 硬编码写 data/reslice_batch_c_summary.json——任何带
--out 的独立批量跑都会静默覆盖生产 batch-C 的证据工件(C-01 家族)。

测试:
1. 默认(不带 --out)行为保持:summary 仍写 batch-C 路径(生产口径不变);
2. --out 时 summary 按输出目录名派生;
3. 集成级变异敏感:模拟带 --out 的 batch 跑,summary 必须落在派生路径,
   batch-C 路径必须不存在——调用点若回退硬编码,本条必失败。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import reslice_pipeline as rp  # noqa: E402


def test_summary_path_default_untouched():
    assert rp.derive_summary_path(None) == ROOT / "data/reslice_batch_c_summary.json"


def test_summary_path_out_isolated():
    p = rp.derive_summary_path(r"D:\x\reslice-pac")
    # 命名约定与 derive_run_paths 一致:reslice_{目录名}
    assert p.name == "reslice_reslice-pac_summary.json"
    assert p != rp.derive_summary_path(None)


def test_batch_run_with_out_never_touches_batch_c_summary(workdir, monkeypatch):
    monkeypatch.setattr(rp, "ROOT", workdir)           # 账目全部落工作目录
    monkeypatch.setattr(rp, "OUT_ROOT", rp.OUT_ROOT)   # 登记原值,teardown 还原
    out_dir = workdir / "reslice-pac"
    batch = workdir / "batch.json"
    batch.write_text(json.dumps([{"file": str(workdir / "a.md"), "tier": "C1"}]),
                     encoding="utf-8")
    monkeypatch.setattr(rp, "process_file",
                        lambda f, log: {"file": str(f), "prompt_tokens": 1,
                                        "completion_tokens": 1, "elapsed_s": 0.1,
                                        "units": 0, "issues": []})
    monkeypatch.setattr(sys, "argv",
                        ["reslice_pipeline.py", "--batch", str(batch),
                         "--out", str(out_dir)])
    rp.main()
    assert (workdir / "data/reslice_reslice-pac_summary.json").exists(), \
        "--out 批量跑的 summary 必须落在派生路径"
    assert not (workdir / "data/reslice_batch_c_summary.json").exists(), \
        "BUG-28 回归:--out 批量跑不得写默认 batch-C summary"
