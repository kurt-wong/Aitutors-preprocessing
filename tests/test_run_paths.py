# -*- coding: utf-8 -*-
"""BUG-21 回归:调试/独立输出跑绝不许覆盖正式账目。

两层锁定:
  ① 纯函数 derive_run_paths 的路径选择契约;
  ② 真实子进程集成——RESLICE_ROOT 指空目录(无配置,LLM 必失败),
     跑 `--file <src> --out <dir>`,断言账目落在派生路径、
     且 data/reslice_pilot_result.json 根本不被创建。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import reslice_pipeline as rp

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_out_run_never_touches_pilot_accounting():
    log_p, res_p = rp.derive_run_paths(out="reslice-h01-smoke")
    assert "reslice-h01-smoke" in res_p.name
    assert res_p != rp.derive_run_paths()[1]          # ≠ pilot 账目
    assert log_p != rp.derive_run_paths()[0]          # ≠ pilot 日志


def test_batch_out_derivation_unchanged():
    """batch+--out 的既有派生契约不回归(R23 账目隔离)。"""
    log_p, res_p = rp.derive_run_paths(out="some/reslice-stress10", batch=True)
    assert res_p.name == "reslice_reslice-stress10_result.json"
    assert log_p.name == "reslice_reslice-stress10_log.txt"


def test_default_paths_untouched():
    """正式跑(无 --out)仍写正式账目:pilot / batch-C 各归各。"""
    assert rp.derive_run_paths()[1].name == "reslice_pilot_result.json"
    assert rp.derive_run_paths(batch=True)[1].name == "reslice_batch_c_result.json"


def test_file_mode_with_out_end_to_end(workdir):
    """集成:无配置环境跑 --file --out(链路必失败),账目隔离必须成立。"""
    src = workdir / "t.md"
    src.write_text("1. 题干\n", encoding="utf-8", newline="")
    out = workdir / "out-x"
    env = dict(os.environ, RESLICE_ROOT=str(workdir), PYTHONPATH=str(SCRIPTS))
    # encoding 显式 utf-8:禁依赖宿主区域设置(R62 F-r62-2,同 test_no_config_import)
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "reslice_pipeline.py"),
         "--file", str(src), "--out", str(out)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(workdir), timeout=180)
    assert r.returncode == 0, r.stderr                     # 单文件失败不炸进程
    derived = workdir / "data" / "reslice_out-x_result.json"
    assert derived.exists(), "派生账目缺失:BUG-21 未修复"
    entries = json.loads(derived.read_text(encoding="utf-8"))
    assert entries and entries[0].get("error")             # LLM 缺配置,如实记错误
    assert not (workdir / "data" / "reslice_pilot_result.json").exists(), \
        "pilot 账目被调试跑创建——BUG-21 复发"
    assert not (workdir / "logs" / "reslice_pilot_log.txt").exists(), \
        "pilot 日志被调试跑创建——BUG-21 复发"
