from sqlalchemy.orm import Session
from app.models.search import SearchCourseResultLog


class SearchCourseResultLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        message_id: int,
        user_id: int,
        course_id: int,
        rank: int
    ) -> SearchCourseResultLog:
        new_log = SearchCourseResultLog(
            message_id=message_id,
            user_id=user_id,
            course_id=course_id,
            rank=rank
        )
        self.db.add(new_log)
        self.db.commit()
        self.db.refresh(new_log)
        return new_log

    def get_by_message(self, message_id: int) -> list[SearchCourseResultLog]:
        return (
            self.db.query(SearchCourseResultLog)
            .filter(SearchCourseResultLog.message_id == message_id)
            .order_by(SearchCourseResultLog.rank.asc())
            .all()
        )

    def delete_by_user_id(self, user_id: int) -> int:
        return (
            self.db.query(SearchCourseResultLog)
            .filter(SearchCourseResultLog.user_id == user_id)
            .delete(synchronize_session=False)
        )