from celery import shared_task
from app.core.db import get_db_session
from app.repositories.course.course_request_repository import CourseRequestRepository
from app.models.course_request import CourseRequestPackageStatus
from app.utils.s3_utils import upload_file_to_s3
from app.core.config import get_settings

import json
import tempfile
from uuid import uuid4

settings = get_settings()


@shared_task
def finalize_request_task(results, request_id: int, package_status_id: int):
    db = get_db_session()
    try:
        repo = CourseRequestRepository(db)
        package_status = (
            db.query(CourseRequestPackageStatus)
            .filter_by(id=package_status_id)
            .first()
        )

        if not package_status:
            return

        unified_result = {
            "request_id": request_id,
            "package_status_id": package_status_id,
            "results": []
        }

        for i, result in enumerate(results):
            if isinstance(result, (list, tuple)) and len(result) == 2:
                _, task_result = result
            else:
                task_result = result

            if i == 0 and task_result is None:
                continue

            if not isinstance(task_result, dict):
                raise ValueError(f"Unexpected task result at index {i}: {task_result}")

            task_entry = {
                "task": task_result.get("task"),
                "status": task_result.get("status"),
                "output": task_result.get("output"),
            }

            if task_result.get("status") == "FAILED":
                task_entry["error"] = task_result.get("error")

            unified_result["results"].append(task_entry)

        # 결과 JSON을 S3에 업로드
        try:
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
                json.dump(unified_result, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name

            uuid_str = uuid4().hex
            s3_key = f"course-request/task-results/{uuid_str}.json"

            if settings.ENVIRONMENT == "prod":
                bucket_name = "insty-prod-encoding"
            else:
                bucket_name = "insty-dev-encoding"

            upload_file_to_s3(
                local_path=tmp_path,
                s3_key=s3_key,
                content_type="application/json",
                bucket_name=bucket_name,
            )

            package_status.s3_key = s3_key

        except Exception as e:
            print(f"결과 JSON 업로드 실패: {e}")

        # 모든 상태 체크
        all_completed = all(
            getattr(package_status, col) == "COMPLETED"
            for col in [
                "summary_status",
                "section_plan_status",
                "script_status",
                "references_status",
                "checklist_status",
                "vector_index_status",
            ]
        )
        any_failed = any(
            getattr(package_status, col) == "FAILED"
            for col in [
                "summary_status",
                "section_plan_status",
                "script_status",
                "references_status",
                "checklist_status",
                "vector_index_status",
            ]
        )

        if all_completed:
            repo.update_request_status(request_id, "COMPLETED")
        elif any_failed:
            from app.services.course.course_request_service import CourseRequestService
            service = CourseRequestService(db)
            request = repo.get_request_by_id(request_id)
            if request:
                service.delete_request(request_id=request_id, user_id=request.requester_id)
                repo.update_request_status(request_id, "FAILED")
        else:
            repo.update_request_status(request_id, "PROCESSING")

        db.commit()

    finally:
        db.close()
