from uuid import UUID
from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.video import VideoCourse

class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, course_id: int) -> Course | None:
        return (
            self.db.query(Course)
            .filter(Course.id == course_id, Course.is_deleted == False)
            .first()
        )
        
    def get_by_ids(self, course_ids: list[int]) -> list[Course]:
        return (
            self.db.query(Course)
            .filter(Course.id.in_(course_ids), Course.is_deleted == False)
            .all()
        )

    def get_thumbnail_status(self, course_id: int) -> tuple[str, UUID | None]:
        course = (
            self.db.query(Course)
            .filter(Course.id == course_id, Course.is_deleted == False)
            .first()
        )

        if not course:
            return "not_found", None

        if course.thumbnail_id is not None:
            return "custom", None

        video_course = (
            self.db.query(VideoCourse)
            .filter(VideoCourse.course_id == course_id, VideoCourse.is_deleted == False)
            .first()
        )

        if not video_course:
            return "not_found", None

        return "default", video_course.video_uuid
