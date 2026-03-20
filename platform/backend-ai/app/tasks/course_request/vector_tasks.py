import logging
from celery import shared_task
from fastapi import HTTPException
from app.repositories.course.course_request_repository import CourseRequestRepository
from app.common.vector_store.course_request.vector_storage_service import CourseRequestVectorStorageService
from app.core.db import get_db_session

logger = logging.getLogger(__name__)

OTHER_OPTION_MAPPING = {
    1: 4,   # 예: field_id 1의 기타 옵션 ID
    2: 10,  # 예: field_id 2의 기타 옵션 ID
}

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def run_answer_vector_task(self, request_id: int, package_status_id: int, field_values: dict):
    db = get_db_session()

    try:
        repo = CourseRequestRepository(db)
        vector_storage_service = CourseRequestVectorStorageService()

        # PROCESSING으로 상태 업데이트
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column="vector_index_status",
            new_status="PROCESSING"
        )

        # Pinecone에 vector upsert
        vector_storage_service.upsert_request_vectors(
            request_id=request_id,
            fields=field_values
        )

        # COMPLETED로 상태 업데이트
        repo.update_package_task_status(
            package_status_id=package_status_id,
            task_column="vector_index_status",
            new_status="COMPLETED"
        )

        db.commit()

    except Exception as e:
        # 실패한 경우 FAILED로 상태 업데이트
        try:
            repo.update_package_task_status(
                package_status_id=package_status_id,
                task_column="vector_index_status",
                new_status="FAILED"
            )
            db.commit()
        except Exception as inner_e:
            logger.error(f"[FAILED 상태 업데이트 중 오류] {inner_e}", exc_info=True)
            db.rollback()

        logger.error(f"[Vector task failed] {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()
