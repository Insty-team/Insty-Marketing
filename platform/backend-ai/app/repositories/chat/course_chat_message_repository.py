from sqlalchemy.orm import Session
from app.models.chat import (
    CourseChatMessage, 
    CourseChatMessageAttachment
    )


class CourseChatMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        session_id: int,
        course_id: int,
        user_id: int,
        sender_type: str,
        message_text: str,
        is_attachment: bool = False
    ) -> CourseChatMessage:
        new_message = CourseChatMessage(
            session_id=session_id,
            course_id=course_id,
            user_id=user_id,
            sender_type=sender_type,
            message_text=message_text,
            is_attachment=is_attachment
        )
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        return new_message

    def get_messages_by_session_and_course(self, session_id: int, course_id: int) -> list[CourseChatMessage]:
        return (
            self.db.query(CourseChatMessage)
            .filter(
                CourseChatMessage.session_id == session_id,
                CourseChatMessage.course_id == course_id
            )
            .order_by(CourseChatMessage.created_at.asc())
            .all()
        )
        
    def get_recent_messages_by_session_and_course(
        self,
        session_id: int,
        course_id: int,
        limit: int = 10
    ) -> list[CourseChatMessage]:
        return (
            self.db.query(CourseChatMessage)
            .filter(
                CourseChatMessage.session_id == session_id,
                CourseChatMessage.course_id == course_id
            )
            .order_by(CourseChatMessage.created_at.desc())
            .limit(limit)
            .all()[::-1]  # 최신순으로 가져온 뒤 → 시간 순으로 역정렬
        )
        
    def get_messages_with_attachments_by_session(self, session_id: int) -> tuple[list[CourseChatMessage], list[CourseChatMessageAttachment]]:
        messages = (
            self.db.query(CourseChatMessage)
            .filter(CourseChatMessage.session_id == session_id)
            .order_by(CourseChatMessage.created_at.asc())
            .all()
        )

        message_ids = [m.id for m in messages]
        attachments = (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.message_id.in_(message_ids))
            .all()
        )

        return messages, attachments

    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(CourseChatMessage)
            .filter(CourseChatMessage.user_id == user_id)
            .delete(synchronize_session=False)
        )
    
    def delete_by_course_id(self, course_id: int) -> int:
        return (
            self.db.query(CourseChatMessage)
            .filter(CourseChatMessage.course_id == course_id)
            .delete(synchronize_session=False)
        )