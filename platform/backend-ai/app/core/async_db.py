## 현재는 쓰이지 않고 있으나 점진적으로 사용 예정

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

_settings = get_settings()

_ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{_settings.db.user}:{_settings.db.password}"
    f"@{_settings.db.host}:{_settings.db.port}/{_settings.db.database}"
)

# SQLAlchemy 엔진 생성 (커넥션 풀 설정 포함)
_async_engine = create_async_engine(
    _ASYNC_DATABASE_URL,
    pool_size=_settings.db.pool_size,
    max_overflow=_settings.db.max_overflow,
    pool_timeout=_settings.db.pool_timeout,
    pool_recycle=_settings.db.pool_recycle,
    echo=getattr(_settings.db, "echo", False),
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_async_engine,
    autoflush=False,
    expire_on_commit=False,
)

# Base 선언은 db.py에서 이미 하고 있으므로 필요 없음

# 사용 가능 함수
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    요청-단위 비동기 세션 제공. 기본적으로는 이걸 사용하면 됨.
    """
    async with AsyncSessionLocal() as session:
        yield session