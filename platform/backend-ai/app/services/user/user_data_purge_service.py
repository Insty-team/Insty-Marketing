from sqlalchemy.orm import Session

from app.repositories.chat.course_chat_attachment_repository import CourseChatMessageAttachmentRepository
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.repositories.chat.course_chat_session_repository import CourseChatSessionRepository
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository
from app.repositories.course.purchase_assistant_usage_repository import PurchaseAssistantUsageRepository
from app.repositories.search.search_chat_message_repository import SearchCourseMessageRepository
from app.repositories.search.search_course_result_log_repository import SearchCourseResultLogRepository
from app.repositories.video.video_speech_text_repository import VideoSpeechTextRepository
from app.common.vector_store.video.vector_delete_service import VectorDeleteService
from app.utils.s3_utils import delete_file_from_s3
from app.common.vector_store.video.vector_storage_service import index


class UserDataPurgeService:
    def __init__(self, db: Session):
        self.db = db

        self.attachment_repo = CourseChatMessageAttachmentRepository(db)
        self.chat_message_repo = CourseChatMessageRepository(db)
        self.chat_session_repo = CourseChatSessionRepository(db)
        self.summary_repo = CourseChatSummarySegmentRepository(db)

        self.purchase_usage_repo = PurchaseAssistantUsageRepository(db)

        self.search_message_repo = SearchCourseMessageRepository(db)
        self.search_result_log_repo = SearchCourseResultLogRepository(db)

        self.speech_text_repo = VideoSpeechTextRepository(db)
        self.vector_delete_service = VectorDeleteService(index)

    def delete_all_ai_data_for_user(self, user_id: int) -> dict:
        deleted_counts = {
            "attachments": 0,
            "messages": 0,
            "sessions": 0,
            "summaries": 0,
            "purchase_usages": 0,
            "search_messages": 0,
            "search_result_logs": 0,
            "speech_texts": 0,
            "vectors_deleted": 0,
            "s3_files_deleted": 0,
        }

        try:
            deleted_counts["attachments"] = self.attachment_repo.delete_by_user_id(user_id)
            deleted_counts["messages"] = self.chat_message_repo.delete_by_user_id(user_id)
            deleted_counts["sessions"] = self.chat_session_repo.delete_by_user_id(user_id)
            deleted_counts["summaries"] = self.summary_repo.delete_by_user_id(user_id)

            deleted_counts["purchase_usages"] = self.purchase_usage_repo.delete_by_user_id(user_id)

            deleted_counts["search_messages"] = self.search_message_repo.delete_by_user_id(user_id)
            deleted_counts["search_result_logs"] = self.search_result_log_repo.delete_by_user_id(user_id)

            video_ids, deleted_count = self.speech_text_repo.delete_by_user_id(user_id)
            deleted_counts["speech_texts"] = deleted_count

            s3_deleted_count = 0
            for video_id in video_ids:
                speech_texts = self.speech_text_repo.get_by_video_id(video_id)
                for speech in speech_texts:
                    if speech.speech_text_url:
                        try:
                            delete_file_from_s3(speech.speech_text_url)
                            s3_deleted_count += 1
                        except Exception as e:
                            print(f"[WARN] S3 삭제 실패: {speech.speech_text_url} / {str(e)}")

            deleted_counts["s3_files_deleted"] = s3_deleted_count

            deleted_counts["vectors_deleted"] = self.vector_delete_service.delete_by_video_ids(video_ids)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e

        return deleted_counts