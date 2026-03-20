from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
from app.core.config import get_settings

settings = get_settings()

# PostgreSQL 연결 URL 구성
database_url = (
    f"postgresql+psycopg://{settings.db.user}:{settings.db.password}"
    f"@{settings.db.host}:{settings.db.port}/{settings.db.database}"
)

# SQLAlchemy 엔진 생성 (커넥션 풀 설정 포함)
engine = create_engine(
    database_url,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_timeout=settings.db.pool_timeout,
    pool_recycle=settings.db.pool_recycle,
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base 선언
Base = declarative_base()

# FastAPI 의존성 주입용 DB 세션
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Celery/스크립트용 직접 세션
def get_db_session() -> Session:
    return SessionLocal()
