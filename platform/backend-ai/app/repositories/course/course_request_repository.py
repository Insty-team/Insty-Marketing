from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict
from typing import Union, Optional

from app.models.course_request import (
    CourseRequest, 
    CourseRequestFormAnswer,  
    CourseRequestFormField, 
    CourseRequestFormFieldOption,
    CourseRequestPackageStatus
) 


class CourseRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, requester_id: int, title: str, description: str) -> CourseRequest:
        new_request = CourseRequest(
            requester_id=requester_id,
            title=title,
            description=description,
            requests_status="PENDING",
            recommendation_status="NOT_RECOMMENDED"
        )
        self.db.add(new_request)
        self.db.flush()
        return new_request
    
    def init_package_status(self, request_id: int) -> CourseRequestPackageStatus:
        package_status = CourseRequestPackageStatus(
            request_id=request_id,
            summary_status="PENDING",
            section_plan_status="PENDING",
            script_status="PENDING",
            references_status="PENDING",
            checklist_status="PENDING",
            vector_index_status="PENDING"
        )
        self.db.add(package_status)
        self.db.flush()
        return package_status
    
    def update_package_task_status(self, package_status_id: int, task_column: str, new_status: str) -> None:
        
        VALID_COLUMNS = {
            "summary_status",
            "section_plan_status",
            "script_status",
            "references_status",
            "checklist_status",
            "vector_index_status"
        }

        VALID_STATUSES = {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}

        if task_column not in VALID_COLUMNS:
            raise ValueError(f"'{task_column}'은 유효한 상태 컬럼이 아닙니다.")

        if new_status not in VALID_STATUSES:
            raise ValueError(f"'{new_status}'은 유효한 상태값이 아닙니다. 허용값: {VALID_STATUSES}")

        self.db.query(CourseRequestPackageStatus).filter_by(id=package_status_id).update(
            {
                task_column: new_status,
                "update_at": datetime.now(timezone.utc)
            },
            synchronize_session=False
        )
        self.db.flush()

    def update_request_status(self, request_id: int, status: str):
        request = self.db.query(CourseRequest).filter_by(id=request_id).first()
        if request:
            request.requests_status = status
            self.db.flush()

    def update_recommendation_status(self, course_request_ids: list[int], new_status: str) -> None:
        if not course_request_ids:
            return

        self.db.query(CourseRequest).filter(
            CourseRequest.id.in_(course_request_ids),
            # CourseRequest.recommendation_status == "NOT_RECOMMENDED"
        ).update(
            {
                CourseRequest.recommendation_status: new_status
            },
            synchronize_session=False
        )

    def create_answers(self, request_id: int, answers: List[dict]) -> List[CourseRequestFormAnswer]:
        new_answers = []
        now = datetime.utcnow()

        for answer in answers:
            new_answer = CourseRequestFormAnswer(
                request_id=request_id,
                field_id=answer["field_id"],
                answer_text=answer.get("answer_text"),
                answer_options=answer.get("answer_option_ids"),
                created_at=now,
                update_at=now
            )
            self.db.add(new_answer)
            new_answers.append(new_answer)

        return new_answers

    def get_request_fields_flat_from_instances(
        self,
        request: CourseRequest,
        answers: List[CourseRequestFormAnswer]
    ) -> Dict[str, str]:
        result = {
            "title": request.title,
            "description": request.description,
        }

        OTHER_OPTION_MAPPING = {
            1: 4,
            2: 10,
        }

        for answer in answers:
            field = (
                self.db.query(CourseRequestFormField)
                .filter(CourseRequestFormField.id == answer.field_id)
                .first()
            )

            if not field:
                continue

            key = field.field_key
            parts = []

            other_option_id = OTHER_OPTION_MAPPING.get(answer.field_id)
            selected_option_ids = list(map(int, answer.answer_options or []))
            regular_option_ids = [opt_id for opt_id in selected_option_ids if opt_id != other_option_id]
            is_other_selected = other_option_id in selected_option_ids

            if regular_option_ids:
                options = (
                    self.db.query(CourseRequestFormFieldOption)
                    .filter(
                        CourseRequestFormFieldOption.field_id == answer.field_id,
                        CourseRequestFormFieldOption.id.in_(regular_option_ids)
                    ).all()
                )
                option_labels = [opt.option_label for opt in options]
                parts.extend(option_labels)

            if is_other_selected and answer.answer_text:
                parts.append(answer.answer_text)

            if not regular_option_ids and not is_other_selected and answer.answer_text:
                parts.append(answer.answer_text)

            if parts:
                result[key] = ", ".join(parts)

        return result
    
    def get_request_with_answers(
        self, request_ids: Union[int, List[int]]
    ) -> Optional[Union[Dict, Dict[int, Dict]]]:

        if isinstance(request_ids, int):
            ids = [request_ids]
            single = True
        else:
            ids = request_ids
            single = False

        if not ids:
            return {} if not single else None

        answers = (
            self.db.query(
                CourseRequest.id.label("request_id"),
                CourseRequest.title,
                CourseRequest.description,
                CourseRequestFormField.field_key,
                CourseRequestFormAnswer.answer_text,
                CourseRequestFormAnswer.answer_options,
                CourseRequestFormField.id.label("field_id")
            )
            .join(CourseRequestFormAnswer, CourseRequest.id == CourseRequestFormAnswer.request_id)
            .join(CourseRequestFormField, CourseRequestFormField.id == CourseRequestFormAnswer.field_id)
            .filter(
                CourseRequest.id.in_(ids),
                CourseRequest.recommendation_status.notin_(["ACCEPTED", "COMPLETED"])
            )
            .all()
        )

        result: Dict[int, Dict] = {}
        for row in answers:
            req = result.setdefault(row.request_id, {
                "title": row.title,
                "description": row.description,
                "answers": []
            })

            selected_labels = []
            if row.answer_options:
                options = (
                    self.db.query(CourseRequestFormFieldOption)
                    .filter(
                        CourseRequestFormFieldOption.field_id == row.field_id,
                        CourseRequestFormFieldOption.id.in_(list(map(int, row.answer_options)))
                    ).all()
                )
                selected_labels = [opt.option_label for opt in options]

            parts = []
            if selected_labels:
                parts.extend(selected_labels)
            if row.answer_text:
                parts.append(row.answer_text)

            req["answers"].append({
                "field_key": row.field_key,
                "answer_text": ", ".join(parts)
            })

        if single:
            return result.get(ids[0])
        return result

    def get_requests_by_user_id(self, user_id: int) -> List[CourseRequest]:
        return (
            self.db.query(CourseRequest)
            .filter(CourseRequest.requester_id == user_id)
            .order_by(CourseRequest.created_at.desc())
            .all()
        )
        
    def get_excludable_requests(self, user_id: int) -> List[CourseRequest]:
        return (
            self.db.query(CourseRequest)
            .filter(
                CourseRequest.requester_id == user_id,
                CourseRequest.recommendation_status.in_(["ACCEPTED", "COMPLETED"])
            )
            .order_by(CourseRequest.created_at.desc())
            .all()
        )

    def get_request_by_id(self, request_id: int) -> Optional[CourseRequest]:
        return self.db.query(CourseRequest).filter(CourseRequest.id == request_id).first()

    def delete_request(self, request: CourseRequest):
        self.db.query(CourseRequestFormAnswer).filter(
            CourseRequestFormAnswer.request_id == request.id
        ).delete(synchronize_session=False)

        self.db.delete(request)
        self.db.flush()
        
    def delete_request_cascade(self, request_id: int) -> None:
        # 1. Answer 먼저 삭제
        self.db.query(CourseRequestFormAnswer).filter_by(request_id=request_id).delete()

        # 2. PackageStatus 삭제
        self.db.query(CourseRequestPackageStatus).filter_by(request_id=request_id).delete()

        # 3. CourseRequest 삭제
        self.db.query(CourseRequest).filter_by(id=request_id).delete()

        self.db.flush()

    def exists_by_id(self, request_id: int) -> bool:
        return (
            self.db.query(CourseRequest.id)
            .filter(CourseRequest.id == request_id)
            .first()
            is not None
        )

    def get_package_status_by_request_id(self, request_id: int) -> CourseRequestPackageStatus:
        return (
            self.db.query(CourseRequestPackageStatus)
            .filter(CourseRequestPackageStatus.request_id == request_id)
            .first()
        )        