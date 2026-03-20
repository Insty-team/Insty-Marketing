from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, Boolean
from sqlalchemy.sql import func
from app.core.db import Base


class SearchCourseResultLog(Base):
    __tablename__ = "search_course_result_logs"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    rank = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SearchCourseMessage(Base):
    __tablename__ = "search_course_messages"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False)
    sender_type = Column(String(10), nullable=False)
    message_text = Column(Text, nullable=False)
    has_recommendation = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
