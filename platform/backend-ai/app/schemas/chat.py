from datetime import datetime, date
from typing import Literal, Optional, List

from fastapi import Form
from pydantic import BaseModel, Field

class ChatSessionInitRequest(BaseModel):
    course_id: int


class ChatSessionInitResponse(BaseModel):
    session_id: int
    course_id: int
    status: Literal['active', 'ended', 'expired']
    created_at: datetime
    is_new: bool


class ChatSessionListResponse(BaseModel):
    session_id: int
    course_id: int
    status: Literal['active', 'ended', 'expired']
    created_at: datetime
    ended_at: Optional[datetime] = None
    is_installed: bool


class ChatMessageRequest(BaseModel):
    course_id: int
    message_text: str
    has_attachment: Optional[bool] = False

    @classmethod
    def as_form(
        cls,
        course_id: int = Form(...),
        message_text: str = Form(...),
        has_attachment: Optional[bool] = Form(False)
    ):
        return cls(
            course_id=course_id,
            message_text=message_text,
            has_attachment=has_attachment
        )


class ChatMessageAttachment(BaseModel):
    file_url: str
    file_type: str
    file_size: int
    file_name: str


class ChatMessageResponse(BaseModel):
    message_id: int
    sender: Literal['user', 'assistant', 'system']
    content: str
    created_at: datetime
    attachments: List[ChatMessageAttachment] = Field(default_factory=list)

    class Config:
        exclude_none = True


class ChatSessionInstallRequest(BaseModel):
    is_installed: bool
   
    
class ChatSessionInstallResponse(BaseModel):
    session_id: int
    is_installed: bool
    

class ChatSessionMessage(BaseModel):
    message_id: int
    sender: Literal['user', 'assistant', 'system']
    content: str
    created_at: datetime
    attachments: List[ChatMessageAttachment] = Field(default_factory=list)

    class Config:
        exclude_none = True


class ChatSessionMessagesResponse(BaseModel):
    session_id: int
    course_id: int
    messages: List[ChatSessionMessage]


class QuestionHistoryItem(BaseModel):
    session_id: int
    course_title: str
    message_id: int
    question_text: str


class QuestionHistoryByDate(BaseModel):
    date: date
    questions: List[QuestionHistoryItem]


class QuestionHistoryGroupedResponse(BaseModel):
    question_history_by_date: List[QuestionHistoryByDate]