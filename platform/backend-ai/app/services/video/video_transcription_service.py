import logging

logger = logging.getLogger(__name__)

from app.tasks.video.video_transcription_tasks import transcribe_video_task

class VideoTranscriptionService:
    def transcribe_from_url_async(self, file_url: str, video_id: int):
        logger.info(f"Celery task 호출: transcribe_video_task.delay(video_id={video_id})")
        transcribe_video_task.delay(file_url, video_id)