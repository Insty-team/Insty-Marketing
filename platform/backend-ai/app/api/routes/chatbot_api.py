from fastapi import Query, Form, Request
from typing import List, Optional, cast
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import get_db
from app.core.auth import get_current_user
from app.schemas.user import User
from app.schemas.chat import (
    ChatSessionInitRequest,
    ChatSessionInitResponse,
    ChatSessionListResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionInstallRequest,
    ChatSessionInstallResponse,
    ChatSessionMessagesResponse,
    QuestionHistoryGroupedResponse
)
from app.docs.deco import op
from app.schemas.common import ResponseModel
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.repositories.chat.course_chat_attachment_repository import CourseChatMessageAttachmentRepository
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.services.chat.chat_session_service import ChatSessionService
from app.services.chat.chat_service import ChatService
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.component.events import (
    CHATBOT_USED,
    COURSE_INSTALLATION_COMPLETED
)
from app.integrations.mixpanel.run_service_method_in_threadpool import run_with_service_in_threadpool

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@op("ai_chatbot_init_session", tags=["chatbot"])
@router.post("/sessions", response_model=ResponseModel[ChatSessionInitResponse])
async def init_chat_session(
    request: ChatSessionInitRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatSessionService(db)
    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=CHATBOT_USED,
        base_event_fields={"course_id": request.course_id},
        business_operation=lambda: run_with_service_in_threadpool(
            ChatSessionService,
            lambda service: service.init_session(
                user_id=current_user.id,
                course_id=request.course_id,
            ),
        ),
    )
    return ResponseModel(success=True, data=result)


@op("ai_chatbot_list_user_sessions", tags=["chatbot"])
@router.get("/sessions", response_model=List[ChatSessionListResponse])
def list_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ChatSessionService(db)
    return service.list_sessions(user_id=current_user.id)


@op("ai_chatbot_post_message", tags=["chatbot"])
@router.post("/sessions/{session_id}/messages", response_model=ResponseModel[ChatMessageResponse])
def post_message_to_session(
    session_id: int,
    request: ChatMessageRequest = Depends(ChatMessageRequest.as_form),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat_service = ChatService(
        message_repo=CourseChatMessageRepository(db),
        attachment_repo=CourseChatMessageAttachmentRepository(db),
        summary_repo=CourseChatSummarySegmentRepository(db),
        video_course_repo=VideoCourseRepository(db)
    )

    result = chat_service.send_message_with_response(
        session_id=session_id,
        course_id=request.course_id,
        user_id=current_user.id,
        message_text=request.message_text,
        file=file
    )

    return ResponseModel(success=True, data=result)

@op("ai_chatbot_post_message_stream", tags=["chatbot"])
@router.post("/sessions/{session_id}/messages/stream")
async def post_message_stream_to_session(
    session_id: int,
    course_id: int = Form(...),
    message_text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat_service = ChatService(
        message_repo=CourseChatMessageRepository(db),
        attachment_repo=CourseChatMessageAttachmentRepository(db),
        summary_repo=CourseChatSummarySegmentRepository(db),
        video_course_repo=VideoCourseRepository(db)
    )

    return await chat_service.stream_message_response(
        session_id=session_id,
        course_id=course_id,
        user_id=current_user.id,
        message_text=message_text,
        file=file
    )


@op("ai_chatbot_get_session_messages", tags=["chatbot"])
@router.get("/sessions/{session_id}/messages", response_model=ResponseModel[ChatSessionMessagesResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ChatSessionService(db)
    result = service.get_session_messages(session_id=session_id, user_id=current_user.id)
    return ResponseModel(success=True, data=result)


@op("ai_chatbot_mark_session_installed", tags=["chatbot"])
@router.patch("/sessions/{session_id}/mark-installed", response_model=ResponseModel[ChatSessionInstallResponse])
async def mark_session_installed(
    session_id: int,
    request: ChatSessionInstallRequest,
    http_request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChatSessionService(db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COURSE_INSTALLATION_COMPLETED, 
        base_event_fields={
            "session_id": session_id,
            "is_installed": bool(request.is_installed),
        },
        business_operation=lambda: run_with_service_in_threadpool(
            ChatSessionService,
            lambda service: service.mark_installed(
                session_id=session_id,
                user_id=current_user.id,
                is_installed=request.is_installed,
            ),
        ),
    )
    return ResponseModel(success=True, data=result)


@op("ai_chatbot_get_question_history_grouped", tags=["chatbot"])
@router.get("/question-history", response_model=ResponseModel[QuestionHistoryGroupedResponse])
def get_question_history_grouped_by_date(
    target_date: Optional[date] = Query(None, alias="date"),
    relative_date: Optional[str] = Query(None, alias="relativeDate"),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ChatSessionService(db)
    result = service.get_question_history_grouped_by_date(
        user_id=current_user.id,
        target_date=target_date,
        relative_date=relative_date,
        keyword=keyword
    )
    return ResponseModel(success=True, data=result)