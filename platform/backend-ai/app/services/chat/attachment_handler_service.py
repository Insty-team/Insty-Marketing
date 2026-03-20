import tempfile
from uuid import uuid4
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import filetype
from app.utils.s3_utils import upload_file_to_s3
from app.models.chat import CourseChatMessageAttachment
from app.repositories.chat.course_chat_attachment_repository import CourseChatMessageAttachmentRepository
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.core.config import get_settings

settings = get_settings()

ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class AttachmentHandlerService:
    def __init__(self, repo: CourseChatMessageAttachmentRepository):
        self.repo = repo

    def handle_attachment(
        self,
        file: UploadFile,
        session_id: int,
        course_id: int,
        user_id: int,
        message_id: int
    ) -> tuple[CourseChatMessageAttachment, str]:
        try:
            filename = file.filename
            ext = Path(filename).suffix.lower()
            expected_type = ALLOWED_IMAGE_TYPES.get(ext)

            if expected_type is None:
                raise APIException(
                    ErrorCode.BAD_REQUEST_BODY,
                    details=[f"허용되지 않은 확장자입니다: {ext}"]
                )

            file_bytes = file.file.read()
            file.file.seek(0)

            kind = filetype.guess(file_bytes)
            if kind is None or kind.mime != expected_type:
                raise APIException(
                    ErrorCode.BAD_REQUEST_BODY,
                    details=[f"파일 형식이 일치하지 않습니다. 예상: {expected_type}, 실제: {kind.mime if kind else 'unknown'}"]
                )

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            unique = uuid4().hex
            s3_key = f"chat-attachments/session_{session_id}/message_{message_id}_{unique}{ext}"

            if settings.ENVIRONMENT == "prod":
                bucket_name = "insty-prod-encoding"
            else:
                bucket_name = "insty-dev-encoding"

            file_url = upload_file_to_s3(
                tmp_path,
                s3_key,
                content_type=kind.mime,
                bucket_name=bucket_name
            )

            attachment = self.repo.create(
                message_id=message_id,
                session_id=session_id,
                course_id=course_id,
                user_id=user_id,
                file_url=file_url,
                file_type=kind.mime,
                file_size=len(file_bytes),
                file_name=filename
            )

            return attachment, tmp_path

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        
    def get_attachments_by_message_id(self, message_id: int) -> list[CourseChatMessageAttachment]:
        return self.repo.get_by_message_id(message_id)
