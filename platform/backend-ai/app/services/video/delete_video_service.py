from uuid import UUID
from typing import List, Set

from sqlalchemy.orm import Session

from app.repositories.video.video_course_repository import VideoCourseRepository
from app.repositories.video.video_speech_text_repository import VideoSpeechTextRepository
from app.common.vector_store.video.vector_delete_service import VectorDeleteService
from app.utils.s3_utils import delete_file_from_s3
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.core.db import get_db_session
from app.common.vector_store.video.vector_storage_service import index
from app.core.config import get_settings

from app.repositories.chat.course_chat_attachment_repository import CourseChatMessageAttachmentRepository
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.repositories.chat.course_chat_session_repository import CourseChatSessionRepository
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository

settings = get_settings()


class DeleteVideoService:
    
    def __init__(self):
        self.db: Session = get_db_session()
        self.course_repo = VideoCourseRepository(self.db)
        self.speech_repo = VideoSpeechTextRepository(self.db)
        self.vector_service = VectorDeleteService(index)

        self.attachment_repo = CourseChatMessageAttachmentRepository(self.db)
        self.chat_message_repo = CourseChatMessageRepository(self.db)
        self.chat_session_repo = CourseChatSessionRepository(self.db)
        self.summary_repo = CourseChatSummarySegmentRepository(self.db)

    def delete_video_by_uuid(self, video_uuid: UUID, secret: str):
        self._validate_secret(secret)
        video = self.course_repo.get_video_by_uuid(video_uuid)
        if not video:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["Video not found"])

        try:
            if video.course_id:
                self._delete_course_related_data(video.course_id)

            self._delete_video_by_id(video.id)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            self.db.close()

    def delete_videos_by_uuids(self, video_uuids: List[UUID], secret: str):
        self._validate_secret(secret)

        video_ids: List[int] = []
        course_ids: Set[int] = set()

        for video_uuid in video_uuids:
            video = self.course_repo.get_video_by_uuid(video_uuid)
            if video:
                video_ids.append(video.id)
                if video.course_id:
                    course_ids.add(video.course_id)

        try:
            for cid in course_ids:
                self._delete_course_related_data(cid)

            if video_ids:
                self.vector_service.delete_by_video_ids(video_ids)

            for video_id in video_ids:
                speech_texts = self.speech_repo.get_by_video_id(video_id)
                for speech in speech_texts:
                    if getattr(speech, "speech_text_url", None):
                        try:
                            delete_file_from_s3(speech.speech_text_url)
                        except Exception as e:
                            print(f"[WARN] S3 삭제 실패: {speech.speech_text_url} / {str(e)}")
                for speech in speech_texts:
                    speech.is_deleted = True

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            self.db.close()

    def _validate_secret(self, secret: str):
        if secret != settings.internal_api_secret:
            raise APIException(ErrorCode.UNAUTHORIZED)

    def _delete_video_by_id(self, video_id: int):
        self.vector_service.delete_by_video_id(video_id)
        speech_texts = self.speech_repo.get_by_video_id(video_id)
        for speech in speech_texts:
            if getattr(speech, "speech_text_url", None):
                try:
                    delete_file_from_s3(speech.speech_text_url)
                except Exception as e:
                    print(f"[WARN] S3 삭제 실패: {speech.speech_text_url} / {str(e)}")
        for speech in speech_texts:
            speech.is_deleted = True

    def _delete_course_related_data(self, course_id: int):
        self._delete_chat_attachments_by_course_id(course_id)
        self._delete_chat_summary_by_course_id(course_id)
        self._delete_chat_messages_by_course_id(course_id)
        self._delete_chat_sessions_by_course_id(course_id)

    def _delete_chat_attachments_by_course_id(self, course_id: int):
        attachments = []
        if hasattr(self.attachment_repo, "list_by_course_id"):
            attachments = self.attachment_repo.list_by_course_id(course_id)

        for att in attachments:
            file_url = getattr(att, "file_url", None)
            if file_url:
                try:
                    delete_file_from_s3(file_url)
                except Exception as e:
                    print(f"[WARN] 첨부 S3 삭제 실패: {file_url} / {str(e)}")

        if hasattr(self.attachment_repo, "delete_by_course_id"):
            self.attachment_repo.delete_by_course_id(course_id)

    def _delete_chat_summary_by_course_id(self, course_id: int):
        if hasattr(self.summary_repo, "delete_by_course_id"):
            self.summary_repo.delete_by_course_id(course_id)

    def _delete_chat_messages_by_course_id(self, course_id: int):
        if hasattr(self.chat_message_repo, "delete_by_course_id"):
            self.chat_message_repo.delete_by_course_id(course_id)

    def _delete_chat_sessions_by_course_id(self, course_id: int):
        if hasattr(self.chat_session_repo, "delete_by_course_id"):
            self.chat_session_repo.delete_by_course_id(course_id)
