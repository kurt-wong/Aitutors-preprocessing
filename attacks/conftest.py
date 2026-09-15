"""DSH EB-008 Implementation Adversarial Review — 攻击测试基座。

只读使用 V3 backend 代码(sys.path 指向 D:\\Project\\AITutors-v3\\backend),
不修改 V3 仓库任何文件。DB = V3 测试库(localhost aitutors),每测试 rollback 隔离。
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
