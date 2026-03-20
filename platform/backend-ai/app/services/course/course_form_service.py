from sqlalchemy.orm import Session
from app.repositories.course.course_form_repository import CourseFormRepository

FIELD_KEY_TO_API_FIELD_TYPE = {
    "problem_context": "text_area",
    "goal": "input_text",
    "current_attempt": "text_area",
    "ai_usage_level": "radio",
    "desired_output": "input_text",
    "extra_context": "text_area",
}

class CourseFormService:
    def __init__(self, db: Session):
        self.repo = CourseFormRepository(db)

    def get_form(self):
        fields = self.repo.get_all_fields()
        result = []

        for field in fields:
            options = self.repo.get_options_by_field_id(field.id)

            result.append({
                "id": field.id,
                "field_key": field.field_key,
                "label": field.field_label,
                "type": self._resolve_api_field_type(field.field_key),
                "is_required": field.is_required,
                "order_no": field.order_no,
                "options": [
                    {"id": opt.id, "label": opt.option_label, "order_no": opt.order_no}
                    for opt in options
                ],
            })

        return {"form": result}

    def _resolve_api_field_type(self, field_key: str) -> str:
        resolved_type = FIELD_KEY_TO_API_FIELD_TYPE.get(field_key)
        if not resolved_type:
            raise ValueError(f"field_key 타입 매핑이 없습니다. field_key={field_key}")
        return resolved_type
