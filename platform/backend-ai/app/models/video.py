from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base

class VideoSpeechTextTable(Base):
    __tablename__ = "video_speech_texts"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    video_id = Column(Integer, nullable=False)
    speech_text_url = Column(String(1000), nullable=False)
    model_version = Column(String(100), nullable=False)
    language_code = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, nullable=False, server_default='false')


class VideoCourse(Base):
    __tablename__ = "video_courses"
    __table_args__ = {"schema": "web_service"},

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    analysis_at = Column(DateTime(timezone=True), nullable=True)
    analysis_status = Column(String(100), nullable=False)
    duration = Column(Integer, nullable=False)
    encoding_at = Column(DateTime(timezone=True), nullable=True)
    encoding_status = Column(String(100), nullable=False)
    extension = Column(String(10), nullable=False)
    is_deleted = Column(Boolean, nullable=False)
    original_file_name = Column(String(150), nullable=False)
    s3key = Column(String(255), nullable=False)              
    video_uuid = Column(UUID(as_uuid=True), nullable=False, unique=True)
    course_id = Column(BigInteger, nullable=True)
    user_id = Column(BigInteger, nullable=False)      