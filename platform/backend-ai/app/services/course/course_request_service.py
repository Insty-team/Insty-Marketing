import json
import os
from typing import List

from celery import chord, group
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.vector_store.course_request.vector_delete_service import CourseRequestVectorDeleteService
from app.common.vector_store.course_request.vector_storage_service import CourseRequestVectorStorageService
from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import APIException
from app.models.course_request import CourseRequest as CourseRequestModel
from app.models.course_request import CourseRequestPackageStatus
from app.models.creator_recommendation import CourseRequestRecommendationResult
from app.repositories.course.course_request_repository import CourseRequestRepository
from app.schemas.community import CourseRequest, CourseResponse
from app.tasks.course_request.vector_tasks import run_answer_vector_task
from app.tasks.course_request.general_llm_tasks import run_llm_generation_task
from app.tasks.course_request.references_generation_tasks import run_references_generation_task
from app.tasks.course_request.finalize_task import finalize_request_task
from app.utils.s3_utils import download_file_from_s3, delete_file_from_s3

settings = get_settings()

OTHER_OPTION_MAPPING = {
    1: 4,     # field_id 1에서 option_id 4는 "기타"
    2: 10     # field_id 2에서 option_id 10은 "기타"
}


class CourseRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRequestRepository(db)
        self.vector_storage_service = CourseRequestVectorStorageService()
        self.vector_delete_service = CourseRequestVectorDeleteService()


    def create_course_request(self, request: CourseRequest, user_id: int) -> CourseResponse:
        try:
            new_request = self.repo.create_request(
                requester_id=user_id,
                title=request.title,
                description=request.description
            )
            
            package_status = self.repo.init_package_status(new_request.id)

            answers_data = []

            for answer in request.answers:
                other_option_id = OTHER_OPTION_MAPPING.get(answer.field_id)

                if answer.answer_option_ids and other_option_id is not None:
                    if other_option_id in answer.answer_option_ids:
                        if not answer.answer_text or not answer.answer_text.strip():
                            raise HTTPException(
                                status_code=422,
                                detail=f"field_id {answer.field_id}에서 '기타' 옵션을 선택한 경우, answer_text는 필수입니다."
                            )

                answers_data.append({
                    "field_id": answer.field_id,
                    "answer_text": answer.answer_text,
                    "answer_option_ids": answer.answer_option_ids
                })

            created_answers = self.repo.create_answers(
                request_id=new_request.id,
                answers=answers_data
            )

            field_values = self.repo.get_request_fields_flat_from_instances(
                request=new_request,
                answers=created_answers
            )
            
            self.db.commit()
            
            # 태스크 그룹 실행
            task_group = group(
                # Pinecone 업서트
                run_answer_vector_task.s(
                    request_id=new_request.id,
                    package_status_id=package_status.id,
                    field_values=field_values,
                ),
                # 통합 태스크 사용
                run_llm_generation_task.s(
                    package_status_id=package_status.id,
                    field_values=field_values,
                    task_type="summary"
                ),
                run_llm_generation_task.s(
                    package_status_id=package_status.id,
                    field_values=field_values,
                    task_type="section_plan"
                ),
                run_llm_generation_task.s(
                    package_status_id=package_status.id,
                    field_values=field_values,
                    task_type="script"
                ),
                run_references_generation_task.s(
                    package_status_id=package_status.id,
                    field_values=field_values,
                ),
                run_llm_generation_task.s(
                    package_status_id=package_status.id,
                    field_values=field_values,
                    task_type="checklist"
                ),
            )

            # 모든 태스크 완료 후 집계 태스크 실행
            chord(task_group)(
                finalize_request_task.s(
                    request_id=new_request.id,
                    package_status_id=package_status.id,
                )
            )
            
            return CourseResponse(
                request_id=new_request.id,
                title=new_request.title,
                description=new_request.description,
                requests_status=new_request.requests_status,
                created_at=new_request.created_at
            )

        except HTTPException:
            self.db.rollback()
            raise
        except APIException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def get_request_with_answers(self, user_id: int) -> List[CourseResponse]:
        course_requests = (
            self.db.query(CourseRequestModel)
            .filter(CourseRequestModel.requester_id == user_id)
            .order_by(CourseRequestModel.created_at.desc())
            .all()
        )
        request_ids = [r.id for r in course_requests]
        if not request_ids:
            return []

        recommendation_results = (
            self.db.query(CourseRequestRecommendationResult)
            .filter(CourseRequestRecommendationResult.course_request_id.in_(request_ids))
            .all()
        )

        def get_priority(action_status: str) -> int:
            priorities = {
                "COMPLETED": 1,
                "ACCEPTED": 2,
                "DECLINED": 3,
                "IGNORED": 4,
            }
            return priorities.get(action_status, 999)

        result_map = {}
        for rec in recommendation_results:
            current = result_map.get(rec.course_request_id)
            if current is None or get_priority(rec.action_status) < get_priority(current[0]):
                result_map[rec.course_request_id] = (rec.action_status, rec.action_at)

        result: List[CourseResponse] = []
        for req in course_requests:
            if req.id in result_map:
                action_status, action_at = result_map[req.id]
            else:
                action_status = "NOT_RECOMMENDED"
                action_at = None

            response = CourseResponse(
                request_id=req.id,
                title=req.title,
                description=req.description,
                requests_status=req.requests_status,
                action_status=action_status,
                action_at=action_at,
                created_at=req.created_at,
            )
            result.append(response)

        return result

    def delete_request(self, request_id: int, user_id: int):
        request = self.repo.get_request_by_id(request_id)

        if not request:
            raise APIException(
                ErrorCode.RESOURCE_NOT_FOUND,
                details=[ErrorCode.RESOURCE_NOT_FOUND.message]
            )

        if request.requester_id != user_id:
            raise APIException(
                ErrorCode.FORBIDDEN,
                details=[ErrorCode.FORBIDDEN.message]
            )

        package_status = self.repo.get_package_status_by_request_id(request_id)
        if package_status and package_status.s3_key:
            if settings.ENVIRONMENT == "prod":
                bucket_name = "insty-prod-encoding"
            else:
                bucket_name = "insty-dev-encoding"

            s3_url = f"https://{bucket_name}.s3.{settings.aws.region_name}.amazonaws.com/{package_status.s3_key}"
            try:
                delete_file_from_s3(s3_url)
            except Exception as e:
                print(f"S3 파일 삭제 실패: {e}")
                self.db.rollback()
                raise APIException(
                    ErrorCode.INTERNAL_ERROR,
                    details=[f"S3 파일 삭제 실패: {e}"]
                )

        self.vector_delete_service.delete_request_vectors(request_id)
        self.repo.delete_request_cascade(request_id)
        self.db.commit()

    def get_finalized_result(self, request_id: int) -> dict:
        status_row = self.repo.get_package_status_by_request_id(request_id)
        if not status_row:
            raise APIException(
                ErrorCode.RESOURCE_NOT_FOUND,
                details=[ErrorCode.RESOURCE_NOT_FOUND.message]
            )

        required_fields = [
            "summary_status", "section_plan_status", "script_status",
            "references_status", "checklist_status", "vector_index_status"
        ]

        if not all(getattr(status_row, field) == "COMPLETED" for field in required_fields):
            raise APIException(
                ErrorCode.FINAL_RESULT_NOT_READY,
                details=[ErrorCode.FINAL_RESULT_NOT_READY.message]
            )

        if not status_row.s3_key:
            raise APIException(
                ErrorCode.RESOURCE_NOT_FOUND,
                details=["S3 키가 존재하지 않아 결과를 조회할 수 없습니다."]
            )

        if settings.ENVIRONMENT == "prod":
            bucket_name = "insty-prod-encoding"
        else:
            bucket_name = "insty-dev-encoding"

        s3_url = f"https://{bucket_name}.s3.{settings.aws.region_name}.amazonaws.com/{status_row.s3_key}"

        local_path = download_file_from_s3(s3_url)

        try:
            with open(local_path, "r", encoding="utf-8") as f:
                result_json = json.load(f)
        finally:
            os.remove(local_path)

        return result_json
