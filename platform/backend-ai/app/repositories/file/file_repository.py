from sqlalchemy.orm import Session
from app.models.file import File


class FileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_course_thumbnail_by_course_id(self, course_id: int) -> File | None:
        return (
            self.db.query(File)
            .filter(
                File.container_id == course_id,
                File.container_type == "COURSE_THUMBNAIL"
            )
            .first()
        )
