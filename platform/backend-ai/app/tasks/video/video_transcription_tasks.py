from celery import shared_task
import os
import tempfile

from app.common.whisper.whisper_service import WhisperService
from app.utils.s3_utils import download_file_from_s3, upload_file_to_s3, delete_file_from_s3
from app.utils.progress_notifier import publish_video_task_status
from app.repositories.video.video_speech_text_repository import VideoSpeechTextRepository
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.core.db import get_db_session
from app.utils.video_duration import validate_video_length, VideoDurationError
from app.core.config import get_settings

settings = get_settings()

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def transcribe_video_task(self, file_url: str, video_id: int):
    db = get_db_session()
    repo = VideoSpeechTextRepository(db)
    course_repo = VideoCourseRepository(db)
    whisper = WhisperService()
    speech_text_url = None
    temp_path = None

    # Whisper 진행 콜백도 내부적으로 publish_video_task_status만 사용
    def progress_cb(step: str, percent: int):
        publish_video_task_status(video_id, step=step, progress=percent)

    try:
        course_repo.update_analysis_status_by_video_id(video_id, "PROCESSING")
        publish_video_task_status(video_id, step="영상 다운로드 중", progress=10)
        course_repo.initialize_analysis_time_by_video_id(video_id)

        if repo.get_by_video_id(video_id):
            publish_video_task_status(video_id, step="이미 전사된 영상", progress=100)
            raise APIException(ErrorCode.CONFLICT)

        temp_path = download_file_from_s3(file_url)  

        max_seconds = 900 if settings.ENVIRONMENT == "prod" else 1800

        try:
            is_ok, seconds = validate_video_length(temp_path, max_seconds=max_seconds) 
        except VideoDurationError as ve:
            raise Exception(f"영상 길이 확인 실패: {ve}")

        if not is_ok:
            reason = f"영상 길이 초과 (재생 시간: {seconds:.1f}초 / 제한: {max_seconds}초)"
            course_repo.update_analysis_status_by_video_id(video_id, "FAILED")
            publish_video_task_status(
                video_id,
                step="실패",
                progress=100,
                status="FAILED_INVALID_VIDEO_LENGTH",
                reason=reason
            )
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return

        publish_video_task_status(video_id, step="Whisper 전사 시작", progress=20)

        transcription = whisper.transcribe_video(temp_path, progress_callback=progress_cb)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(transcription["text"].encode("utf-8"))
            tmp_path = tmp.name

        s3_key = f"vod-transcripts/{video_id}/speech.txt"
        speech_text_url = upload_file_to_s3(tmp_path, s3_key)
        os.remove(tmp_path)
        publish_video_task_status(video_id, step="전사 텍스트 S3 업로드 완료", progress=98)

        repo.create(
            video_id=video_id,
            speech_text_url=speech_text_url,
            model_version=transcription["model_version"],
            language_code=transcription["language_code"]
        )

        course_repo.update_analysis_status_by_video_id(video_id, "COMPLETED")
        publish_video_task_status(video_id, step="완료", progress=100)
        publish_video_task_status(video_id, step="완료", progress=100, status="COMPLETED")

    except APIException as ae:
        course_repo.update_analysis_status_by_video_id(video_id, "FAILED")
        publish_video_task_status(video_id, step="실패", progress=100)

        reason = ae.error.message
        if ae.details:
            print(f"[DEBUG] Whisper 실패: {ae.error.code} | details: {ae.details}")

        publish_video_task_status(
            video_id,
            step="실패",
            progress=100,
            status="FAILED",
            reason=reason
        )

        if speech_text_url:
            try:
                delete_file_from_s3(speech_text_url)
            except:
                pass

        if ae.error == ErrorCode.AUDIO_NO_SPEECH_DETECTED:
            return

        raise self.retry(exc=ae)

    except Exception as e:
        course_repo.update_analysis_status_by_video_id(video_id, "FAILED")
        publish_video_task_status(video_id, step="실패", progress=100)

        print(f"[DEBUG] 알 수 없는 예외 발생: {str(e)}")

        publish_video_task_status(
            video_id,
            step="실패",
            progress=100,
            status="FAILED",
            reason="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )

        if speech_text_url:
            try:
                delete_file_from_s3(speech_text_url)
            except:
                pass

        raise self.retry(exc=e)

    finally:
        db.close()
        if 'temp_path' in locals() and temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
