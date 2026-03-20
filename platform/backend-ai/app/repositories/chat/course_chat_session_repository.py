from collections import defaultdict
from datetime import date
from typing import Optional, List, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.chat import CourseChatSession, CourseChatMessage
from app.models.course import Course


class CourseChatSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        course_id: int,
        user_id: int,
        status: str,
        is_installed: bool = False
    ) -> CourseChatSession:
        new_session = CourseChatSession(
            course_id=course_id,
            user_id=user_id,
            status=status,
            is_installed=is_installed
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

    def get_by_user(self, user_id: int) -> list[CourseChatSession]:
        return (
            self.db.query(CourseChatSession)
            .filter(CourseChatSession.user_id == user_id)
            .order_by(CourseChatSession.created_at.desc())
            .all()
        )

    def update_status(self, session_id: int, status: str) -> None:
        self.db.query(CourseChatSession).filter_by(id=session_id).update(
            {"status": status}
        )
        self.db.commit()
        
    def set_installed_status(self, session_id: int, is_installed: bool) -> None:
        self.db.query(CourseChatSession).filter_by(id=session_id).update(
            {"is_installed": is_installed}
        )
        self.db.commit()
        
    def get_user_question_history_grouped_by_date(
        self,
        user_id: int,
        target_date: Optional[date] = None,
        relative_start_date: Optional[date] = None,
        keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        Message = CourseChatMessage
        SessionModel = CourseChatSession
        CourseModel = Course

        query = (
            self.db.query(
                func.date(Message.created_at).label("grouped_date"),
                Message.session_id,
                CourseModel.title.label("course_title"),
                Message.id.label("message_id"),
                Message.message_text.label("question_text"),
            )
            .join(SessionModel, Message.session_id == SessionModel.id)
            .join(CourseModel, SessionModel.course_id == CourseModel.id)
            .filter(
                Message.user_id == user_id,
                Message.sender_type == "user"
            )
        )

        if target_date:
            query = query.filter(func.date(Message.created_at) == target_date)

        if relative_start_date:
            query = query.filter(Message.created_at >= relative_start_date)

        if keyword:
            query = query.filter(Message.message_text.ilike(f"%{keyword}%"))

        rows = query.order_by(
            func.date(Message.created_at).desc(),
            Message.created_at.desc()
        ).all()

        grouped: Dict[date, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row.grouped_date].append({
                "session_id": row.session_id,
                "course_title": row.course_title,
                "message_id": row.message_id,
                "question_text": row.question_text,
            })

        return [
            {
                "date": group_date,
                "questions": questions
            }
            for group_date, questions in grouped.items()
        ]
        
    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(CourseChatSession)
            .filter(CourseChatSession.user_id == user_id)
            .delete(synchronize_session=False)
        )

    def list_by_course_id(self, course_id: int) -> list[CourseChatSession]:
        return (
            self.db.query(CourseChatSession)
            .filter(CourseChatSession.course_id == course_id)
            .all()
        )

    def delete_by_course_id(self, course_id: int) -> int:
        return (
            self.db.query(CourseChatSession)
            .filter(CourseChatSession.course_id == course_id)
            .delete(synchronize_session=False)
        )