from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.chat import CourseChatSummarySegment


class CourseChatSummarySegmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_segment(
        self,
        session_id: int,
        course_id: int,
        user_id: int,
        start_message_id: int,
        end_message_id: int,
        summary_text: str,
        summary_tokens: int
    ) -> CourseChatSummarySegment:
        segment = CourseChatSummarySegment(
            session_id=session_id,
            course_id=course_id,
            user_id=user_id,
            start_message_id=start_message_id,
            end_message_id=end_message_id,
            summary_text=summary_text,
            summary_tokens=summary_tokens
        )
        self.db.add(segment)
        self.db.commit()
        self.db.refresh(segment)
        return segment

    def get_segments_by_session_and_course(self, session_id: int, course_id: int) -> list[CourseChatSummarySegment]:
        return (
            self.db.query(CourseChatSummarySegment)
            .filter(
                CourseChatSummarySegment.session_id == session_id,
                CourseChatSummarySegment.course_id == course_id
            )
            .order_by(CourseChatSummarySegment.start_message_id.asc())
            .all()
        )

    def get_latest_segment(self, session_id: int) -> CourseChatSummarySegment | None:
        return (
            self.db.query(CourseChatSummarySegment)
            .filter(CourseChatSummarySegment.session_id == session_id)
            .order_by(desc(CourseChatSummarySegment.end_message_id))
            .first()
        )

    def delete_segments_by_session(self, session_id: int) -> int:
        deleted = (
            self.db.query(CourseChatSummarySegment)
            .filter(CourseChatSummarySegment.session_id == session_id)
            .delete()
        )
        self.db.commit()
        return deleted

    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(CourseChatSummarySegment)
            .filter(CourseChatSummarySegment.user_id == user_id)
            .delete(synchronize_session=False)
        )
        
    def delete_by_course_id(self, course_id: int) -> int:
        return (
            self.db.query(CourseChatSummarySegment)
            .filter(CourseChatSummarySegment.course_id == course_id)
            .delete(synchronize_session=False)
        )