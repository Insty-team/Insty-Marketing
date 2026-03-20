import logging
from typing import List, Optional
from app.repositories.chat.course_chat_summary_segment_repository import CourseChatSummarySegmentRepository
from app.repositories.chat.course_chat_message_repository import CourseChatMessageRepository
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.utils.prompt_loader import load_prompt
from openai import OpenAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)  # 로거 선언

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class SummarySegmentService:
    def __init__(
        self,
        segment_repo: CourseChatSummarySegmentRepository,
        message_repo: CourseChatMessageRepository,
    ):
        self.segment_repo = segment_repo
        self.message_repo = message_repo

    def maybe_summarize(
        self,
        session_id: int,
        course_id: int,
        user_id: int
    ) -> Optional[str]:
        try:
            messages = self.message_repo.get_messages_by_session_and_course(session_id, course_id)
            if len(messages) <= 10:
                return None

            latest_segment = self.segment_repo.get_latest_segment(session_id)
            last_end_id = latest_segment.end_message_id if latest_segment else None

            start_index = 0
            if last_end_id:
                for i, msg in enumerate(messages):
                    if msg.id == last_end_id:
                        start_index = i + 1
                        break

            messages_to_summarize = messages[start_index:-10]
            if len(messages_to_summarize) < 10:
                return None

            chunk = messages_to_summarize[:10]

            prompt = load_prompt("chat_summary_prompt.j2", {
                "previous_summary": "",
                "new_messages": [
                    {"sender_type": msg.sender_type, "message_text": msg.message_text}
                    for msg in chunk
                ]
            })

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=1024,
            )

            summary_text = response.choices[0].message.content.strip()
            token_estimate = len(summary_text.split())

            self.segment_repo.create_segment(
                session_id=session_id,
                course_id=course_id,
                user_id=user_id,
                start_message_id=chunk[0].id,
                end_message_id=chunk[-1].id,
                summary_text=summary_text,
                summary_tokens=token_estimate
            )

            logger.info(
                f"[요약 수행됨] session_id={session_id}, course_id={course_id}, "
                f"messages summarized=[{chunk[0].id}~{chunk[-1].id}], token_estimate={token_estimate}"
            )

            return summary_text

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def get_all_segments_for_prompt(self, session_id: int, course_id: int) -> List[str]:
        segments = self.segment_repo.get_segments_by_session_and_course(session_id, course_id)
        return [s.summary_text for s in segments]
