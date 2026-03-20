import os
import json
import uuid
import shutil
from typing import Literal, Optional, List

from fastapi import UploadFile
from sqlalchemy.orm import Session
from openai import OpenAI

from app.common.vector_store.video.vector_search_service import VectorSearchService
from app.common.vision.vision_ocr_service import VisionOCRService
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.utils.clean_gpt_text import enforce_html_breaks
from app.utils.prompt_loader import load_prompt

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


ALLOWED_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class CommunityAnswerDraftService:
    def __init__(self, video_course_repo: VideoCourseRepository):
        self.vector_search_service = VectorSearchService(video_course_repo)
        self.ocr_service = VisionOCRService()

    @staticmethod
    def from_db(db: Session) -> "CommunityAnswerDraftService":
        return CommunityAnswerDraftService(
            video_course_repo=VideoCourseRepository(db)
        )

    def generate_draft_response(
        self,
        course_id: int,
        text: str,
        draft_type: Literal["question", "answer", "thought"],
        attachment_files: Optional[List[UploadFile]] = None
    ) -> dict:
        try:
            # 1. 백터 검색 (thought 타입은 제외)
            vector_chunks = []
            if draft_type != "thought":
                vector_chunks = self.vector_search_service.search_similar_chunks(course_id, text)

            # 2. OCR 처리
            ocr_texts = []
            if attachment_files:
                file_paths = self._save_files_locally(attachment_files)
                for path in file_paths:
                    ocr_result = self.ocr_service.extract_text_from_image(path)
                    ocr_texts.append(ocr_result)

            # 3. 프롬프트 파일 결정
            if draft_type == "question":
                prompt_template = "community_question_draft_prompt.j2"
                key_prefix = "question"
            elif draft_type == "answer":
                prompt_template = "community_answer_draft_prompt.j2"
                key_prefix = "answer"
            elif draft_type == "thought":
                prompt_template = "community_thought_draft_prompt.j2"
                key_prefix = "thought"
            else:
                raise APIException(ErrorCode.INVALID_TYPE_PARAMETER, details=["Invalid draft_type"])

            # 4. 프롬프트 구성
            system_prompt = load_prompt(prompt_template, {
                key_prefix: text,
                "vector_chunks": vector_chunks,
                "ocr_texts": ocr_texts
            })

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]

            # 5. GPT 호출
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=messages,
                max_tokens=800
            )

            raw_content = response.choices[0].message.content.strip()

            # 6. JSON 응답 파싱
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError:
                raise APIException(
                    ErrorCode.INVALID_TYPE_PARAMETER,
                    details=["AI 응답이 올바른 JSON이 아닙니다.", raw_content]
                )

            # 7. 필수 키 검사
            if draft_type == "question":
                if "question_title" not in parsed or "question_content" not in parsed:
                    raise APIException(
                        ErrorCode.INVALID_TYPE_PARAMETER,
                        details=["질문 생성 응답 형식 오류", parsed]
                    )
                parsed["question_title"] = enforce_html_breaks(parsed["question_title"])
                parsed["question_content"] = enforce_html_breaks(parsed["question_content"])

            elif draft_type == "answer":
                if "answer_content" not in parsed:
                    raise APIException(
                        ErrorCode.INVALID_TYPE_PARAMETER,
                        details=["답변 생성 응답 형식 오류", parsed]
                    )
                parsed["answer_content"] = enforce_html_breaks(parsed["answer_content"])

            elif draft_type == "thought":
                if "post_title" not in parsed or "post_content" not in parsed:
                    raise APIException(
                        ErrorCode.INVALID_TYPE_PARAMETER,
                        details=["생각 정리 생성 응답 형식 오류", parsed]
                    )
                parsed["post_title"] = enforce_html_breaks(parsed["post_title"])
                parsed["post_content"] = enforce_html_breaks(parsed["post_content"])

            return parsed

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _save_files_locally(self, files: List[UploadFile]) -> List[str]:
        file_paths = []
        os.makedirs("/tmp/draft_uploads", exist_ok=True)

        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()

            # 확장자 검증
            if ext not in ALLOWED_IMAGE_TYPES:
                raise APIException(
                    ErrorCode.INVALID_TYPE_PARAMETER,
                    details=[f"지원하지 않는 이미지 확장자입니다: {file.filename}"]
                )

            file_id = str(uuid.uuid4())
            path = f"/tmp/draft_uploads/{file_id}{ext}"

            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            file_paths.append(path)

        return file_paths
