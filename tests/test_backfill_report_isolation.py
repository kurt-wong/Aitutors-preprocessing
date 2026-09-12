# -*- coding: utf-8 -*-
"""BUG-29 回归:phase2_identity_backfill 的报告路径必须尊重 --report。

BUG-28 有 test_batch_summary_isolation 钉住;BUG-29(同族第二例)修复后一直
只有人工实测(R46 dry-run),没有 CI 回归——本文件补齐。测试跑真实 main()
(合成语料),断言:① --report 指到哪写到哪;② 默认报告工件
data/phase2_identity_backfill_report.json 内容不被触动。
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import phase2_identity_backfill as bf  # noqa: E402
from conftest import make_repo  # noqa: E402

DEFAULT_REPORT = ROOT / "data/phase2_identity_backfill_report.json"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_report_arg_respected_and_default_untouched(workdir, monkeypatch):
    _, _, out_dir = make_repo(workdir)
    custom = workdir / "custom_report.json"
    before = _sha(DEFAULT_REPORT)
    snapshot = DEFAULT_REPORT.read_bytes()  # 变异自审防护:复发变异会写穿真工件
    try:
        monkeypatch.setattr(sys, "argv",
                            ["phase2_identity_backfill.py",
                             "--out", str(out_dir),
                             "--report", str(custom)])
        bf.main()
        assert custom.exists(), "--report 指定路径未写入"
        rep = json.loads(custom.read_text(encoding="utf-8"))
        assert rep["applied"] is False and len(rep["files"]) == 1, rep
        assert _sha(DEFAULT_REPORT) == before, \
            "BUG-29 复发:独立跑冲掉了默认报告工件"
    finally:
        # 无论测试成败(含 BUG-29 复发变异故意打穿的场合),恢复真实工件
        DEFAULT_REPORT.write_bytes(snapshot)
