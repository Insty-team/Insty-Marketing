import json
from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.schemas.community import CourseRequestSuggestion, CourseResponseSuggestion
from app.utils.prompt_loader import load_prompt

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class CourseRequestSuggestionService:
    def suggest(self, request: CourseRequestSuggestion) -> CourseResponseSuggestion:
        try:
            prompt = load_prompt(
                "course_request_prompt.j2",
                {
                    "problem_context": request.problem_context,
                    "goal": request.goal,
                    "current_attempt": request.current_attempt,
                    "ai_usage_level": request.ai_usage_level,
                    "desired_output": request.desired_output,
                    "extra_context": request.extra_context,
                },
            )
        except Exception as e:
            raise APIException(
                ErrorCode.INTERNAL_ERROR,
                details=[f"프롬프트 로딩 실패: {str(e)}"],
            )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "너는 반드시 JSON 객체만 응답해야 한다. "
                            '형식: { "title": string, "description": string } '
                            "코드블록/주석/추가 텍스트 금지. "
                            "description은 5~7문장 이상으로 작성하고, "
                            "강의 제작 요청 배경, 겪고 있는 어려움, 구체적인 강의 주제, "
                            "세션 구성 예시, 최신 트렌드 키워드, 추가 조언까지 포함할 것."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception as e:
            raise APIException(
                ErrorCode.INTERNAL_ERROR,
                details=[f"GPT 호출 실패: {str(e)}"],
            )

        try:
            content = response.choices[0].message.content
            data = json.loads(content) if isinstance(content, str) else content

            title = (data.get("title") or "").strip()
            description = (data.get("description") or "").strip()

            if not title or not description:
                raise ValueError("응답 스키마 누락(title/description)")

            return CourseResponseSuggestion(title=title, description=description)

        except Exception as e:
            raise APIException(
                ErrorCode.INTERNAL_ERROR,
                details=[f"응답 파싱 실패: {str(e)}"],
            )
