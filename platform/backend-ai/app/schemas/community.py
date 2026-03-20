from typing import Optional, List, Literal
from datetime import datetime
from fastapi import Form
from pydantic import BaseModel, Field


class CourseRequestAnswer(BaseModel):
    field_id: int
    answer_text: Optional[str] = None
    answer_option_ids: Optional[List[int]] = None


class CourseRequest(BaseModel):
    title: str
    description: str
    answers: List[CourseRequestAnswer] 


class CreatorInterestAnswer(BaseModel):
    field_id: int
    answer_text: Optional[str] = None
    answer_option_ids: Optional[List[int]] = None


class CreatorInterestForm(BaseModel):
    answers: List[CreatorInterestAnswer]


class CourseResponse(BaseModel):
    request_id: int
    title: str
    description: str
    requests_status: str
    action_status: Optional[str] = None  
    action_at: Optional[datetime] = None  
    created_at: datetime


class CourseFormOption(BaseModel):
    id: int
    label: str
    order_no: int


class CourseFormField(BaseModel):
    id: int
    field_key: str
    label: str
    type: Literal['radio', 'checkbox', 'input_text', 'text_area']
    is_required: bool
    order_no: int
    options: List[CourseFormOption] = []


class CourseFormResponse(BaseModel):
    form: List[CourseFormField]


class CreatorRecommendationFormOption(BaseModel):
    id: int
    label: str
    order_no: int


class CreatorRecommendationFormField(BaseModel):
    id: int
    field_key: str
    label: str
    type: Literal['radio', 'checkbox', 'input_text', 'text_area']
    is_required: bool
    order_no: int
    options: List[CreatorRecommendationFormOption] = []


class CreatorRecommendationFormResponse(BaseModel):
    form: List[CreatorRecommendationFormField]


class SelectedFieldItem(BaseModel):
    field_key: str     
    answer_text: str     


class CourseRequestRecommendationItem(BaseModel):
    request_id: int
    title: str
    description: str
    selected_fields: List[SelectedFieldItem] = Field(default_factory=list)
    reason: str  


class CourseRequestRecommendationResponse(BaseModel):
    recommendations: List[CourseRequestRecommendationItem]


class CourseRequestSuggestion(BaseModel):
    problem_context: str
    goal: str
    current_attempt: str
    ai_usage_level: str
    desired_output: str
    extra_context: Optional[str] = None
    

class CourseResponseSuggestion(BaseModel):
    title: str
    description: str
    
    
class FormCheckResponse(BaseModel):
    exists: bool
    form: Optional[CreatorInterestForm] = None


class DraftRequest(BaseModel):
    course_id: int
    query: str
    has_attachment: Optional[bool] = False

    @classmethod
    def as_form(
        cls,
        course_id: int = Form(...),
        query: str = Form(...),
        has_attachment: Optional[bool] = Form(False)
    ):
        return cls(
            course_id=course_id,
            query=query,
            has_attachment=has_attachment
        )


class DraftAttachment(BaseModel):
    file_url: str
    file_type: str
    file_size: int
    file_name: str


class AnswerDraftResponse(BaseModel):
    answer_content: str
    has_attachment: bool = Field(...)

    class Config:
        exclude_none = True


class QuestionDraftResponse(BaseModel):
    question_title: str
    question_content: str
    has_attachment: bool = Field(...)

    class Config:
        exclude_none = True


class ThoughtDraftResponse(BaseModel):
    post_title: str
    post_content: str
    has_attachment: bool = Field(...)

    class Config:
        exclude_none = True


class CourseRequestStatusUpdateRequest(BaseModel):
    action_status: Literal['ACCEPTED', 'DECLINED', 'IGNORED', 'COMPLETED']


class CourseRequestStatusUpdateResponse(BaseModel):
    request_id: int
    action_status: str
    action_at: datetime


class CourseRequestAvailabilityResponse(BaseModel):
    available: bool
    status: Literal["IGNORED", "DECLINED", "ACCEPTED", "COMPLETED", "NOT_RECOMMENDED", "UNKNOWN"]
