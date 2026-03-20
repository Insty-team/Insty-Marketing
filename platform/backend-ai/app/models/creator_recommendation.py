from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ARRAY
from sqlalchemy.sql import func
from app.core.db import Base


class CreatorRecommendationFormField(Base):
    __tablename__ = "creator_recommendation_form_fields"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    field_key = Column(String(50), nullable=False, unique=True)
    field_label = Column(String(255), nullable=False)
    field_type = Column(String(20), nullable=False)  # 'input_text', 'text_area', 'radio', 'checkbox'
    is_required = Column(Boolean, nullable=False, server_default="true")
    order_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CreatorRecommendationFormFieldOption(Base):
    __tablename__ = "creator_recommendation_form_field_options"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)
    option_label = Column(String(255), nullable=False)
    order_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CreatorRecommendationFormAnswer(Base):
    __tablename__ = "creator_recommendation_form_answers"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, nullable=False)
    field_id = Column(Integer, nullable=False)
    answer_text = Column(Text, nullable=True)
    answer_options = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    

class CourseRequestRecommendationResult(Base):
    __tablename__ = "course_request_recommendation_results"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    course_request_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    matched_by_form = Column(Boolean, nullable=False, server_default="true")
    rank = Column(Integer, nullable=False)
    action_status = Column(String(20), nullable=False, server_default="IGNORED")
    action_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CourseRequestRecommendationUsedAnswer(Base):
    __tablename__ = "course_request_recommendation_used_answers"
    __table_args__ = {"schema": "ai_service"}

    recommendation_result_id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, primary_key=True, index=True)


