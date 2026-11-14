"""DSH EB-008 Implementation Adversarial Review — 攻击测试基座（V3 冻结件）。

【本文件已隔离，不可执行】QCORE-GENERIC-EXECUTION-CHAIN-01 · 2026-11-14（V3 残留隔离）。

历史行为（隔离前，仅存档说明）：
- sys.path 注入 V3 backend（原 `D:\\Project\\AITutors-v3\\backend`，已归档 `ARCHIVE\\AITutors-v3`，原路径不存在）；
- 默认 DATABASE_URL = `postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors`（**共享库**）；
- 依赖 V3 `app.db.session` / 旧 Gate 模块；每测试 rollback 隔离；
- 复跑命令（历史）：`python -m pytest attacks --asyncio-mode=auto`。

隔离理由（DSH 复核 + Owner 裁决）：
1. V3 已正式废弃——旧测试不得作为当前生产代码的测试依赖；
2. 默认共享库连接有误执行风险（aitutors）；
3. V3 backend 路径已失效（归档），运行必然 ImportError。

隔离方式：**import 级 fail-closed 硬阻断**——任何收集/执行尝试立即报错中止。
历史证据保全：`test_eb008_impl_attack.py`（32KB 攻击用例）原样保留，本文件仅替换基座；
本目录不参与默认测试发现（pytest.ini testpaths=tests + norecursedirs=attacks）。
"""

import pytest

raise pytest.UsageError(
    "FROZEN V3 SUITE (EB-008 adversarial) — execution blocked by "
    "QCORE-GENERIC-EXECUTION-CHAIN-01 V3-residue isolation. "
    "Targets deprecated V3 backend + shared aitutors database; "
    "preserved as historical evidence only "
    "(test_eb008_impl_attack.py untouched). "
    "See V3_RESIDUE_ISOLATION_REPORT.md."
)
