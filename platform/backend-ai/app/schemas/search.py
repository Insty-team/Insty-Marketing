from datetime import datetime
from typing import List, Optional, Literal, Union
from pydantic import BaseModel

class CourseRecommendationRequest(BaseModel):
    query: str


class RecommendedCourse(BaseModel):
    course_id: str
    course_title: str
    thumbnail_url: Optional[str] = None


class CourseRecommendationResponse(BaseModel):
    message: str
    courses: List[RecommendedCourse]


class UserMessageItem(BaseModel):
    message_id: int
    sender: Literal["user"]
    content: str
    created_at: datetime


class AssistantMessageItem(BaseModel):
    message_id: int
    sender: Literal["assistant"]
    content: str
    created_at: datetime
    courses: Optional[List[RecommendedCourse]] = []


MessageHistoryItem = Union[UserMessageItem, AssistantMessageItem]


class RecommendationHistoryResponse(BaseModel):
    messages: List[MessageHistoryItem]


class ExternalAIService(BaseModel):
    title: str
    url: str
    description: str
    type: Literal["external_service"]
    courses: List[RecommendedCourse]


class AIServiceRecommendationRequest(BaseModel):
    query: str


class AIServiceRecommendationResponse(BaseModel):
    message: str
    services: List[ExternalAIService]