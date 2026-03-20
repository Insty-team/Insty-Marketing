from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.creator_recommendation import (
    CreatorRecommendationFormField,
    CreatorRecommendationFormFieldOption,
    CourseRequestRecommendationResult,
    CourseRequestRecommendationUsedAnswer
)


class CreatorRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_fields(self):
        return (
            self.db.query(CreatorRecommendationFormField)
            .order_by(CreatorRecommendationFormField.order_no)
            .all()
        )

    def get_options_by_field_id(self, field_id: int):
        return (
            self.db.query(CreatorRecommendationFormFieldOption)
            .filter(CreatorRecommendationFormFieldOption.field_id == field_id)
            .order_by(CreatorRecommendationFormFieldOption.order_no)
            .all()
        )

    def save_recommendation_results(
        self,
        course_request_ids: list[int],
        receiver_id: int,
        matched_by_form: bool,
        return_ids: bool = False,
    ) -> list[int] | None:
        inserted_ids = [] 

        for rank, course_request_id in enumerate(course_request_ids, start=1):
            result = CourseRequestRecommendationResult(
                course_request_id=course_request_id,
                receiver_id=receiver_id,
                matched_by_form=matched_by_form,
                rank=rank,
                action_status="IGNORED",
            )
            self.db.add(result)
            if return_ids:
                self.db.flush() 
                inserted_ids.append(result.id)

        return inserted_ids if return_ids else None

    def get_recommendation_result_ids(
        self,
        creator_id: int,
        course_request_ids: Optional[List[int]] = None,
        matched_by_form: Optional[bool] = None
    ) -> List[int]:
        query = self.db.query(CourseRequestRecommendationResult.id).filter(
            CourseRequestRecommendationResult.receiver_id == creator_id
        )

        if course_request_ids:
            query = query.filter(
                CourseRequestRecommendationResult.course_request_id.in_(course_request_ids)
            )

        if matched_by_form is not None:
            query = query.filter(
                CourseRequestRecommendationResult.matched_by_form == matched_by_form
            )

        results = query.all()
        return [r.id for r in results]

    def link_form_answers_to_recommendation_results(
        self,
        recommendation_result_ids: List[int],
        form_id: int
    ) -> None:
        for rec_id in recommendation_result_ids:
            self.db.merge(
                CourseRequestRecommendationUsedAnswer(
                    recommendation_result_id=rec_id,
                    form_id=form_id
                )
            )
        self.db.flush()

    def update_action_status(
        self,
        receiver_id: int,
        course_request_id: int,
        new_status: str,
        action_at: datetime
    ) -> int:
        result = (
            self.db.query(CourseRequestRecommendationResult)
            .filter(
                CourseRequestRecommendationResult.receiver_id == receiver_id,
                CourseRequestRecommendationResult.course_request_id == course_request_id,
            )
            .update({
                CourseRequestRecommendationResult.action_status: new_status,
                CourseRequestRecommendationResult.action_at: action_at,
                CourseRequestRecommendationResult.update_at: action_at,
            }, synchronize_session=False)
        )
        self.db.flush()
        return result
    
    def get_recommendation_result_by_request_id(self, request_id: int) -> Optional[CourseRequestRecommendationResult]:
        return self.db.query(CourseRequestRecommendationResult).filter(
            CourseRequestRecommendationResult.course_request_id == request_id
        ).first()
        
    def get_action_statuses_by_request_id(self, request_id: int) -> List[str]:
        rows = (
            self.db.query(CourseRequestRecommendationResult.action_status)
            .filter(CourseRequestRecommendationResult.course_request_id == request_id)
            .all()
        )
        return [r[0] for r in rows]
    
    def exists_by_course_request_id(self, request_id: int) -> bool:
        return self.db.query(
            CourseRequestRecommendationResult.course_request_id
        ).filter(
            CourseRequestRecommendationResult.course_request_id == request_id
        ).first() is not None
