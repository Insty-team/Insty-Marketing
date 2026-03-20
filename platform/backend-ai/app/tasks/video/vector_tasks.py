from celery import shared_task
from uuid import UUID
import os

from app.core.db import get_db_session
from app.common.vector_store.video.vector_storage_service import VectorStorageService
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.repositories.video.video_speech_text_repository import VideoSpeechTextRepository
from app.utils.s3_utils import download_file_from_s3
from app.utils.progress_notifier import publish_video_task_status
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_vector_upsert_task(self, video_uuid: str):
    db = get_db_session()
    local_path = None
    video = None

    try:
        # UUID로 video 조회
        course_repo = VideoCourseRepository(db)
        speech_repo = VideoSpeechTextRepository(db)

        video = course_repo.get_active_video_by_uuid(UUID(video_uuid))
        if not video:
            raise ValueError(f"UUID({video_uuid})로 비디오를 찾을 수 없습니다.")

        # TODO : BE 쪽에서 문제 없이 지속적으로 course_id를 채우게 된다면 삭제 가능
        # 현재 문제 체크 및 차후 디버깅을 위해 임의로 추가했음
        if getattr(video, "course_id", None) is None:
            # 예외 던저서 retry하지 않고, 실패 처리(BE 쪽 실패로 인한 전역 처리)
            publish_video_task_status(
                video.id,
                step="course_id가 없어 벡터 임베딩을 건너뜁니다.",
                progress=100,
                status="FAILED",
                prefix="vector",
            )
            return

        speech_list = speech_repo.get_by_video_id(video.id)
        if not speech_list or not speech_list[0].speech_text_url:
            raise APIException(ErrorCode.FAILED_NOT_FOUND_VOICE, details=["변환된 텍스트를 찾을 수 없습니다."])

        # 최신 전사 텍스트
        speech_url = speech_list[0].speech_text_url

        def progress(step: str, percent: int):
            publish_video_task_status(video.id, step=step, progress=percent, status="PROCESSING", prefix="vector")

        progress("변환된 텍스트 다운로드 중", 0)

        # S3에서 텍스트 파일 다운로드
        local_path = download_file_from_s3(speech_url)
        with open(local_path, "r", encoding="utf-8") as f:
            text = f.read()

        progress("벡터 임베딩 시작", 5)

        # 벡터 임베딩 업서트
        vector_service = VectorStorageService()
        vector_service.upsert_text(video.id, text, progress_callback=progress)
        
        # 임베딩 완료 상태 알림 추가
        publish_video_task_status(video.id, step="벡터 임베딩 완료", progress=100, status="COMPLETED", prefix="vector")

    except Exception as e:
        publish_video_task_status(video.id, step="실패", progress=100, status="FAILED", prefix="vector")
        raise self.retry(exc=e)

    finally:
        db.close()
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
