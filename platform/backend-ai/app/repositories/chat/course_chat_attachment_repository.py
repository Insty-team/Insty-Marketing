from sqlalchemy.orm import Session
from app.models.chat import CourseChatMessageAttachment


class CourseChatMessageAttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        message_id: int,
        session_id: int,
        course_id: int,
        user_id: int,
        file_url: str,
        file_type: str,
        file_size: int,
        file_name: str
    ) -> CourseChatMessageAttachment:
        attachment = CourseChatMessageAttachment(
            message_id=message_id,
            session_id=session_id,
            course_id=course_id,
            user_id=user_id,
            file_url=file_url,
            file_type=file_type,
            file_size=file_size,
            file_name=file_name
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def get_attachments_by_session(self, session_id: int) -> list[CourseChatMessageAttachment]:
        return (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.session_id == session_id)
            .order_by(CourseChatMessageAttachment.created_at.asc())
            .all()
        )

    def get_by_message_id(self, message_id: int) -> list[CourseChatMessageAttachment]:
        return (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.message_id == message_id)
            .all()
        )

    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.user_id == user_id)
            .delete(synchronize_session=False)
        )
        
    def list_by_course_id(self, course_id: int) -> list[CourseChatMessageAttachment]:
        return (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.course_id == course_id)
            .all()
        )

    def delete_by_course_id(self, course_id: int) -> int:
        return (
            self.db.query(CourseChatMessageAttachment)
            .filter(CourseChatMessageAttachment.course_id == course_id)
            .delete(synchronize_session=False)
        )