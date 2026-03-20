from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.creator_recommendation import (
    CreatorRecommendationFormAnswer,
    CreatorRecommendationFormField,
    CreatorRecommendationFormFieldOption,
    CourseRequestRecommendationResult,
    CourseRequestRecommendationUsedAnswer,
)

from app.schemas.community import CreatorInterestAnswer


class CreatorRecommendationFormRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_creator_fields_flat_from_instances(
        self,
        answers: List[CreatorRecommendationFormAnswer]
    ) -> Dict[str, str]:

        CREATOR_OTHER_OPTION_MAPPING = {
            1: 4,
            2: 10,
        }

        result: Dict[str, str] = {}

        for answer in answers:
            field = (
                self.db.query(CreatorRecommendationFormField)
                .filter(CreatorRecommendationFormField.id == answer.field_id)
                .first()
            )

            if not field:
                continue

            key = field.field_key
            parts = []

            other_option_id = CREATOR_OTHER_OPTION_MAPPING.get(answer.field_id)
            selected_option_ids = list(map(int, answer.answer_options or []))
            regular_option_ids = [oid for oid in selected_option_ids if oid != other_option_id]
            is_other_selected = other_option_id in selected_option_ids

            if regular_option_ids:
                options = (
                    self.db.query(CreatorRecommendationFormFieldOption)
                    .filter(
                        CreatorRecommendationFormFieldOption.field_id == answer.field_id,
                        CreatorRecommendationFormFieldOption.id.in_(regular_option_ids)
                    ).all()
                )
                option_labels = [opt.option_label for opt in options]
                parts.extend(option_labels)

            if is_other_selected and answer.answer_text:
                parts.append(answer.answer_text.strip())

            if not regular_option_ids and not is_other_selected and answer.answer_text:
                parts.append(answer.answer_text.strip())

            if parts:
                result[key] = ", ".join(parts)

        return result

    def create_answers_with_new_form_id(
        self, answers: List[CreatorInterestAnswer]
    ) -> Tuple[int, List[CreatorRecommendationFormAnswer]]:
        form_id = self.db.execute(text("SELECT nextval('ai_service.creator_form_id_seq')")).scalar()

        answer_objs = [
            CreatorRecommendationFormAnswer(
                form_id=form_id,
                field_id=ans.field_id,
                answer_text=ans.answer_text,
                answer_options=ans.answer_option_ids
            )
            for ans in answers
        ]
        self.db.add_all(answer_objs)
        return form_id, answer_objs
    
    def get_latest_answers_by_creator(self, creator_id: int) -> List[CreatorRecommendationFormAnswer]:
        latest_result_subq = (
            self.db.query(CourseRequestRecommendationResult.id)
            .filter(CourseRequestRecommendationResult.receiver_id == creator_id)
            .order_by(CourseRequestRecommendationResult.id.desc())
            .limit(1)
            .subquery()
        )

        latest_form_subq = (
            self.db.query(CourseRequestRecommendationUsedAnswer.form_id)
            .filter(CourseRequestRecommendationUsedAnswer.recommendation_result_id == latest_result_subq.c.id)
            .subquery()
        )

        answers = (
            self.db.query(CreatorRecommendationFormAnswer)
            .filter(CreatorRecommendationFormAnswer.form_id == latest_form_subq.c.form_id)
            .all()
        )

        return answers