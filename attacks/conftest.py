"""DSH EB-008 Implementation Adversarial Review — 攻击测试基座。

只读使用 V3 backend 代码(sys.path 指向 D:\\Project\\AITutors-v3\\backend),
不修改 V3 仓库任何文件。DB = V3 测试库(localhost aitutors),每测试 rollback 隔离。

复跑命令(DEC-045 自审 S-2 落字;历史报告曾称"见套件文件头"但缺失,以本行为准):
    python -m pytest attacks --asyncio-mode=auto
说明:本套件用例为裸 async def 无 marker,pytest-asyncio 1.x strict 模式下必须
显式 --asyncio-mode=auto;另勿与 tests/ 合并收集(tests/ 内 `from conftest import …`
会解析到本文件 = 顶层模块名冲突,S-1 known issue)。依赖 aitutor-postgres(5432),
容器未启动时全部 ConnectionRefused = 环境性,非代码回归。
"""

import os
import sys

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)
# 攻击运行自带合法长度 secret(与 V3 conftest 同语义;B-5 攻击单独 monkeypatch 置空)
os.environ.setdefault("APP_SECRET", "dsh-attack-secret-32-bytes-minimum!!!")

V3_BACKEND = r"D:\Project\AITutors-v3\backend"
if V3_BACKEND not in sys.path:
    sys.path.insert(0, V3_BACKEND)

import pytest_asyncio  # noqa: E402


@pytest_asyncio.fixture
async def session():
    from app.db.session import async_session_maker

    async with async_session_maker() as s:
        yield s
        await s.rollback()
