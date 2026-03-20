from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "insty_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.autodiscover_tasks([
    "app.tasks",
])

# 직접 태스크 모듈 import하여 등록 보장
import app.tasks.video.video_transcription_tasks
import app.tasks.video.vector_tasks
import app.tasks.chat.summary_tasks

import app.tasks.course_request.vector_tasks
import app.tasks.course_request.general_llm_tasks
import app.tasks.course_request.references_generation_tasks
import app.tasks.course_request.finalize_task
