from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.core.db import Base

class CourseChatSession(Base):
    __tablename__ = "course_chat_sessions"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_installed = Column(Boolean, server_default="false", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseChatMessage(Base):
    __tablename__ = "course_chat_messages"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    sender_type = Column(String(10), nullable=False)
    message_text = Column(Text, nullable=False)
    is_attachment = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseChatSummarySegment(Base):
    __tablename__ = "course_chat_summary_segments"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    start_message_id = Column(Integer, nullable=False)
    end_message_id = Column(Integer, nullable=False)
    summary_text = Column(Text, nullable=False)
    summary_tokens = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseChatMessageAttachment(Base):
    __tablename__ = "course_chat_message_attachments"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, nullable=False)
    session_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)