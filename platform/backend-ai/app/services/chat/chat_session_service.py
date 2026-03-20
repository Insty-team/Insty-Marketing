from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from collections import defaultdict
from app.models.chat import CourseChatSession
from app.repositories.chat.course_chat_session_repository import CourseChatSessionRepository
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.schemas.chat import (
    ChatSessionInitResponse, 
    ChatSessionListResponse, 
    ChatSessionInstallResponse,
    ChatSessionMessagesResponse,
    ChatSessionMessage,
    ChatMessageAttachment,
    QuestionHistoryItem,
    QuestionHistoryByDate,
    QuestionHistoryGroupedResponse
    )
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.utils.s3_to_cloudfront_url import convert_s3_to_cloudfront_url
from app.utils.date_range import get_start_date_by_relative


class ChatSessionService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = CourseChatSessionRepository(db)

    def init_session(self, user_id: int, course_id: int) -> ChatSessionInitResponse:
        try:
            existing_sessions = self.session_repo.get_by_user(user_id)
            for session in existing_sessions:
                if session.course_id == course_id and session.status == "active":
                    return ChatSessionInitResponse(
                        session_id=session.id,
                        course_id=session.course_id,
                        user_id=session.user_id,
                        status=session.status,
                        created_at=session.created_at,
                        is_new=False
                    )

            new_session = self.session_repo.create(
                course_id=course_id,
                user_id=user_id,
                status="active",
                is_installed=False
            )

            return ChatSessionInitResponse(
                session_id=new_session.id,
                course_id=new_session.course_id,
                user_id=new_session.user_id,
                status=new_session.status,
                created_at=new_session.created_at,
                is_new=True
            )

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        
    def list_sessions(self, user_id: int) -> list[ChatSessionListResponse]:
        try:
            sessions = self.session_repo.get_by_user(user_id)
            return [
                ChatSessionListResponse(
                    session_id=session.id,
                    course_id=session.course_id,
                    status=session.status,
                    created_at=session.created_at,
                    ended_at=session.ended_at,
                    is_installed=session.is_installed
                )
                for session in sessions
            ]
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        
    def mark_installed(self, session_id: int, user_id: int, is_installed: bool = True) -> ChatSessionInstallResponse:
        try:
            session = self.db.query(CourseChatSession).filter_by(id=session_id, user_id=user_id).first()
            if not session:
                raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["세션을 찾을 수 없습니다."])

            self.session_repo.set_installed_status(session_id, is_installed)

            return ChatSessionInstallResponse(
                session_id=session_id,
                is_installed=is_installed
            )
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        
    def get_session_messages(self, session_id: int, user_id: int) -> ChatSessionMessagesResponse:
        session = self.db.query(CourseChatSession).filter_by(id=session_id, user_id=user_id).first()
        if not session:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["세션을 찾을 수 없습니다."])

        message_repo = CourseChatMessageRepository(self.db)
        messages, attachments = message_repo.get_messages_with_attachments_by_session(session_id)

        attachment_map = defaultdict(list)
        for att in attachments:
            attachment_map[att.message_id].append(ChatMessageAttachment(
                file_url=convert_s3_to_cloudfront_url(att.file_url),
                file_type=att.file_type,
                file_size=att.file_size,
                file_name=att.file_name
            ))

        message_list = []
        for m in messages:
            msg_data = {
                "message_id": m.id,
                "sender": m.sender_type,
                "content": m.message_text,
                "created_at": m.created_at,
                "attachments": attachment_map.get(m.id, [])  # (없으면 빈 리스트)
            }

            message_list.append(ChatSessionMessage(**msg_data))

        return ChatSessionMessagesResponse(
            session_id=session.id,
            course_id=session.course_id,
            messages=message_list
        )
        
    def get_question_history_grouped_by_date(
        self,
        user_id: int,
        target_date: Optional[date] = None,
        relative_date: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> QuestionHistoryGroupedResponse:
        try:
            if target_date and relative_date:
                raise APIException(
                    ErrorCode.INVALID_TYPE_PARAMETER,
                    details=["date와 relativeDate는 동시에 사용할 수 없습니다."]
                )

            relative_start_date = None
            if relative_date:
                try:
                    relative_start_date = get_start_date_by_relative(relative_date)
                except ValueError:
                    raise APIException(
                        ErrorCode.INVALID_TYPE_PARAMETER,
                        details=[f"지원하지 않는 relativeDate 값입니다: {relative_date}"]
                    )

            raw_data = self.session_repo.get_user_question_history_grouped_by_date(
                user_id=user_id,
                target_date=target_date,
                relative_start_date=relative_start_date,
                keyword=keyword
            )

            response = [
                QuestionHistoryByDate(
                    date=group["date"],
                    questions=[
                        QuestionHistoryItem(**question)
                        for question in group["questions"]
                    ]
                )
                for group in raw_data
            ]

            return QuestionHistoryGroupedResponse(question_history_by_date=response)

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
