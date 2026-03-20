from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.db import Base

class File(Base):
    __tablename__ = "files"
    __table_args__ = {"schema": "web_service"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    container_id = Column(BigInteger, nullable=False)
    container_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=True)
    original_name = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    size = Column(BigInteger, nullable=False)
