from celery import shared_task
from app.services.chat.summary_service import SummarySegmentService
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.core.db import get_db

@shared_task
def run_maybe_summarize(session_id: int, course_id: int, user_id: int):
    db = next(get_db())
    try:
        summary_service = SummarySegmentService(
            CourseChatSummarySegmentRepository(db),
            CourseChatMessageRepository(db),
        )
        summary_service.maybe_summarize(session_id, course_id, user_id)
    finally:
        db.close()
