from sqlalchemy.orm import Session
from app.models.course_request import (
    CourseRequestFormField,
    CourseRequestFormFieldOption,
)


class CourseFormRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_fields(self):
        return (
            self.db.query(CourseRequestFormField)
            .order_by(CourseRequestFormField.order_no)
            .all()
        )

    def get_options_by_field_id(self, field_id: int):
        return (
            self.db.query(CourseRequestFormFieldOption)
            .filter(CourseRequestFormFieldOption.field_id == field_id)
            .order_by(CourseRequestFormFieldOption.order_no)
            .all()
        )
