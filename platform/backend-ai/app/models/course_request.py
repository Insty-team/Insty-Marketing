from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ARRAY
from sqlalchemy.sql import func
from app.core.db import Base


class CourseRequest(Base):
    __tablename__ = "course_requests"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    requests_status = Column(String(20), nullable=False, server_default="PROCESSING")
    recommendation_status = Column(String(20), nullable=False, server_default="NOT_RECOMMENDED")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CourseRequestFormField(Base):
    __tablename__ = "course_request_form_fields"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    field_key = Column(String(50), nullable=False, unique=True)
    field_label = Column(String(255), nullable=False)
    field_type = Column(String(20), nullable=False)  # radio, checkbox, input_text, text_area
    is_required = Column(Boolean, nullable=False, server_default="true")
    order_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CourseRequestFormFieldOption(Base):
    __tablename__ = "course_request_form_field_options"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, nullable=False)   
    option_label = Column(String(255), nullable=False)
    order_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CourseRequestFormAnswer(Base):
    __tablename__ = "course_request_form_answers"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, nullable=False)   
    field_id = Column(Integer, nullable=False)   
    answer_text = Column(Text, nullable=True)
    answer_options = Column(ARRAY(String), nullable=True)  # PostgreSQL 배열
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    
class CourseRequestPackageStatus(Base):
    __tablename__ = "course_request_package_status"
    __table_args__ = {"schema": "ai_service"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, nullable=False, unique=True)
    summary_status = Column(String(20), nullable=False, server_default="PENDING")       
    section_plan_status = Column(String(20), nullable=False, server_default="PENDING")  
    script_status = Column(String(20), nullable=False, server_default="PENDING")
    references_status = Column(String(20), nullable=False, server_default="PENDING")
    checklist_status = Column(String(20), nullable=False, server_default="PENDING")
    vector_index_status = Column(String(20), nullable=False, server_default="PENDING")
    s3_key = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)