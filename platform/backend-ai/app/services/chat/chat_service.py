from app.tasks.chat.summary_tasks import run_maybe_summarize
import os
import asyncio
from typing import Optional
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.repositories.chat.course_chat_attachment_repository import CourseChatMessageAttachmentRepository
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.services.chat.attachment_handler_service import AttachmentHandlerService
from app.common.vision.vision_ocr_service import VisionOCRService
from app.services.chat.summary_service import SummarySegmentService
from app.common.vector_store.video.vector_search_service import VectorSearchService
from app.models.chat import CourseChatMessage
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from openai import OpenAI
from app.core.config import get_settings
from app.utils.prompt_loader import load_prompt
from app.utils.clean_gpt_text import enforce_html_breaks

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)

class ChatService:
    def __init__(
        self,
        message_repo: CourseChatMessageRepository,
        attachment_repo: CourseChatMessageAttachmentRepository,
        summary_repo: CourseChatSummarySegmentRepository,
        video_course_repo: VideoCourseRepository
    ):
        self.message_repo = message_repo  # 메시지 DB 저장소
        self.attachment_service = AttachmentHandlerService(attachment_repo)  # 첨부파일 처리기
        self.ocr_service = VisionOCRService()  # 이미지 텍스트 추출기
        self.summary_service = SummarySegmentService(summary_repo, message_repo)  # 요약 처리기
        self.vector_search_service = VectorSearchService(video_course_repo)  # 유사 강의 검색기

    def handle_chat(
        self,
        session_id: int,
        course_id: int,
        user_id: int,
        message_text: str,
        file: Optional[UploadFile] = None
    ) -> tuple[CourseChatMessage, CourseChatMessage]:
        try:
            user_message = self.message_repo.create(  # 사용자 메시지 저장
                session_id=session_id,
                course_id=course_id,
                user_id=user_id,
                sender_type="user",
                message_text=message_text,
                is_attachment=bool(file)
            )

            ocr_result = ""  # 이미지 OCR 결과 초기화
            if file:  # 이미지가 첨부된 경우
                try:
                    _, tmp_path = self.attachment_service.handle_attachment(  #언팩해서 사용
                        file=file,
                        session_id=session_id,
                        course_id=course_id,
                        user_id=user_id,
                        message_id=user_message.id
                    )
                    ocr_result = self.ocr_service.extract_text_from_image(tmp_path)  # OCR 실행
                finally:
                    delete_tmp_file.delay(tmp_path)  # 사용 후 임시 파일 경로 삭제 -> 백그라운드 테스크로 분리

            summaries = self.summary_service.get_all_segments_for_prompt(session_id, course_id)  # 요약 정보 가져오기
            vector_chunks = self.vector_search_service.search_similar_chunks(course_id, message_text)  # 유사 강의 검색 TODO: 성능 이슈시, 캐싱 고려
            recent_messages = self.message_repo.get_recent_messages_by_session_and_course(session_id, course_id, limit=10)  # 최근 대화 불러오기

            # 공통 응답 규칙 3종 결합
            system_base = (
                load_prompt("base/common_rules.j2", {}) + "\n" +
                load_prompt("base/meta_guidelines.j2", {}) + "\n" +
                load_prompt("base/safety_filters.j2", {})
            )

            # 기능 템플릿 + 컨텍스트(요약/벡터/OCR)
            user_prompt = load_prompt("chat_completion_prompt.j2", {
                "summaries": summaries,
                "vector_chunks": vector_chunks,
                "ocr_texts": [ocr_result] if ocr_result.strip() else []
            })

            # 메시지 구성 (최근 대화는 그대로 추가, OCR은 별도 섹션으로만 전달)
            chat_messages = [
                {"role": "system", "content": system_base},
                {"role": "user", "content": user_prompt},
            ]
            chat_messages.extend([
                {"role": m.sender_type, "content": m.message_text}
                for m in recent_messages
            ])

            response = client.chat.completions.create(  # GPT 호출
                model="gpt-4o",
                messages=chat_messages,
                max_tokens=1024,
            )
            assistant_reply_raw = response.choices[0].message.content.strip()  # GPT 응답 원본
            assistant_reply = enforce_html_breaks(assistant_reply_raw)  # 응답 HTML 렌더링 최적화

            assistant_message = self.message_repo.create(  # 어시스턴트 메시지 저장
                session_id=session_id,
                course_id=course_id,
                user_id=user_id,
                sender_type="assistant",
                message_text=assistant_reply,
                is_attachment=False
            )

            self.summary_service.maybe_summarize(  # 요약 업데이트 시도 TODO: 백그라운드 테스크로 분리
                session_id=session_id,
                course_id=course_id,
                user_id=user_id
            )

            return user_message, assistant_message

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        
    async def stream_message_response(
        self,
        session_id: int,
        course_id: int,
        user_id: int,
        message_text: str,
        file: Optional[UploadFile] = None
    ):
        # 1. 사용자 메시지 저장
        user_message = self.message_repo.create(
            session_id=session_id,
            course_id=course_id,
            user_id=user_id,
            sender_type="user",
            message_text=message_text,
            is_attachment=bool(file)
        )

        # 2. 이미지가 있는 경우 처리
        ocr_result = ""
        if file:
            try:
                _, tmp_path = self.attachment_service.handle_attachment(
                    file=file,
                    session_id=session_id,
                    course_id=course_id,
                    user_id=user_id,
                    message_id=user_message.id
                )
                ocr_result = self.ocr_service.extract_text_from_image(tmp_path)
            finally:
                os.remove(tmp_path)

        # 3. 컨텍스트 구성
        summaries = self.summary_service.get_all_segments_for_prompt(session_id, course_id)
        vector_chunks = self.vector_search_service.search_similar_chunks(course_id, message_text)
        recent_messages = self.message_repo.get_recent_messages_by_session_and_course(session_id, course_id, limit=10)

        # 공통 응답 규칙 3종 결합
        system_base = (
            load_prompt("base/common_rules.j2", {}) + "\n" +
            load_prompt("base/meta_guidelines.j2", {}) + "\n" +
            load_prompt("base/safety_filters.j2", {})
        )

        # 기능 템플릿 + 컨텍스트(요약/벡터/OCR)
        user_prompt = load_prompt("chat_completion_prompt.j2", {
            "summaries": summaries,
            "vector_chunks": vector_chunks,
            "ocr_texts": [ocr_result] if ocr_result.strip() else []
        })

        # 메시지 구성
        chat_messages = [
            {"role": "system", "content": system_base},
            {"role": "user", "content": user_prompt},
        ]
        chat_messages.extend([
            {"role": m.sender_type, "content": m.message_text}
            for m in recent_messages
        ])

        # 4. GPT 스트리밍 요청
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_messages,
            max_tokens=1024,
            stream=True
        )

        async def event_stream():
            full_content = ""
            try:
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content_piece = delta.content
                        full_content += content_piece
                        yield f"data: {content_piece}\n\n"
                        await asyncio.sleep(0)

                yield "data: [END]\n\n"

                # 응답 메시지 저장
                # 실시간 응답도 줄바꿈 규칙을 일관적으로 처리
                full_content = enforce_html_breaks(full_content)
                self.message_repo.create(
                    session_id=session_id,
                    course_id=course_id,
                    user_id=user_id,
                    sender_type="assistant",
                    message_text=full_content,
                    is_attachment=False
                )
                run_maybe_summarize.delay(session_id, course_id, user_id) #요약 저장 celery 비동기로 분리


            except Exception as e:
                yield f"data: [ERROR]: {str(e)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")