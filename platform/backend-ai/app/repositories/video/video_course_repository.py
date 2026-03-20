from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.video import VideoCourse


class VideoCourseRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_by_id(self, video_id: int) -> VideoCourse | None:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.id == video_id, VideoCourse.is_deleted == False)
            .first()
        )

    def get_by_course_id(self, course_id: int) -> VideoCourse | None:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.course_id == course_id, VideoCourse.is_deleted == False)
            .first()
        )
        
    def get_by_course_ids(self, course_ids: list[int]) -> list[VideoCourse]:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.course_id.in_(course_ids), VideoCourse.is_deleted == False)
            .all()
        )
        
    def get_by_video_ids(self, video_ids: list[int]) -> list[VideoCourse]:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.id.in_(video_ids), VideoCourse.is_deleted == False)
            .all()
        )
        
    def get_analysis_status_by_video_id(self, video_id: int) -> str | None:
        result = (
            self.db.query(VideoCourse.analysis_status)
            .filter(VideoCourse.id == video_id, VideoCourse.is_deleted == False)
            .scalar()
        )
        return result

    def initialize_analysis_time_by_video_id(self, video_id: int) -> bool:
        video_course = (
            self.db.query(VideoCourse)
            .filter(VideoCourse.id == video_id, VideoCourse.is_deleted == False)
            .first()
        )
        if video_course and video_course.analysis_at is None:
            video_course.analysis_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False


    def update_analysis_status_by_video_id(self, video_id: int, new_status: str) -> bool:
        video_course = (
            self.db.query(VideoCourse)
            .filter(VideoCourse.id == video_id, VideoCourse.is_deleted == False)
            .first()
        )
        if video_course:
            video_course.analysis_status = new_status
            self.db.commit()
            return True
        return False
    
    def get_by_s3key(self, s3key: str) -> VideoCourse | None:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.s3key == s3key, VideoCourse.is_deleted == False)
            .first()
        )
        
    def get_active_video_by_uuid(self, video_uuid: UUID) -> VideoCourse | None:
        return (
            self.db.query(VideoCourse)
            .filter(
                VideoCourse.video_uuid == video_uuid,
                VideoCourse.is_deleted == False
            )
            .first()
        )
        
    def get_video_by_uuid(self, video_uuid: UUID) -> VideoCourse | None:
        return (
            self.db.query(VideoCourse)
            .filter(VideoCourse.video_uuid == video_uuid)
            .first()
        )
        
    def get_uploaded_video_ids(self, user_id: int) -> list[int]:
        rows = (
            self.db.query(VideoCourse.id)
            .filter(
                VideoCourse.user_id == user_id,
                VideoCourse.is_deleted == False
            )
            .all()
        )
        return [row.id for row in rows]
