from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.community import (
    FormCheckResponse,
    CreatorInterestForm,
    CreatorInterestAnswer
)
from app.models.creator_recommendation import CreatorRecommendationFormAnswer
from app.repositories.course.creator_recommendation_repository import CreatorRecommendationRepository
from app.repositories.course.creator_recommendation_form_repository import CreatorRecommendationFormRepository


class CreatorRecommendationFormService:
    def __init__(self, db: Session):
        self.repo = CreatorRecommendationRepository(db)
        self.form_repo = CreatorRecommendationFormRepository(db)

    def get_form(self):
        fields = self.repo.get_all_fields()

        result = []
        for field in fields:
            options = self.repo.get_options_by_field_id(field.id)

            result.append({
                "id": field.id,
                "field_key": field.field_key,
                "label": field.field_label,
                "type": field.field_type,
                "is_required": field.is_required,
                "order_no": field.order_no,
                "options": [
                    {
                        "id": opt.id,
                        "label": opt.option_label,
                        "order_no": opt.order_no,
                    }
                    for opt in options
                ],
            })

        return {"form": result}
    
    
    def get_last_submitted_form(self, creator_id: int) -> FormCheckResponse:
        last_answers: List[CreatorRecommendationFormAnswer] = (
            self.form_repo.get_latest_answers_by_creator(creator_id)
        )

        if not last_answers:
            return FormCheckResponse(exists=False)

        answers = [
            CreatorInterestAnswer(
                field_id=ans.field_id,
                answer_text=ans.answer_text,
                answer_option_ids=ans.answer_options
            )
            for ans in last_answers
        ]

        return FormCheckResponse(
            exists=True,
            form=CreatorInterestForm(answers=answers)
        )
