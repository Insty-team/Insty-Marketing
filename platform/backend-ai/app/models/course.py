from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.db import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {"schema": "web_service"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=True)
    is_show = Column(Boolean, nullable=False)
    like_count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    target_audience = Column(String(100), nullable=True)
    thumbnail_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    view_count = Column(Integer, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    is_deleted = Column(Boolean, nullable=False)
    
    
class PurchaseAssistantUsage(Base):
    __tablename__ = "purchase_assistant_usage"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(BigInteger, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
