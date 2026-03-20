import json
import os
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.repositories.course.purchase_assistant_usage_repository import PurchaseAssistantUsageRepository
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.utils.prompt_loader import load_prompt
from app.utils.s3_utils import download_file_from_s3
from app.schemas.course import (
    PurchaseAssistantRequest, 
    PurchaseAssistantResponse, 
    PurchaseAssistantUsageInfo
    )

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class PurchaseAssistantService:
    def __init__(self, db: Session):
        self.db = db
        self.usage_repo = PurchaseAssistantUsageRepository(db)
        self.video_repo = VideoCourseRepository(db)

    def assist_user(self, user_id: int, req: PurchaseAssistantRequest) -> PurchaseAssistantResponse:
        # 1. VideoCourse 조회
        video = self.video_repo.get_by_course_id(req.course_id)
        if not video:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["해당 course_id의 영상이 존재하지 않습니다."])
        video_id = video.id

        # 2. transcript 가져오기
        transcript = self._get_transcript_from_s3(video_id)

        # 3. 사용 기록 조회 또는 초기화
        usage = self.usage_repo.get_by_user_and_course(user_id, req.course_id)
        if not usage:
            usage = self.usage_repo.create(user_id, req.course_id)

        # 4. 사용 가능 횟수 초과 시 고정 응답
        if usage.usage_count >= 2:
            return PurchaseAssistantResponse(
                recommendation="챗봇 무료 사용 가능 횟수를 모두 사용하셨습니다. 자세한 상담은 고객지원으로 문의해주세요.",
                judgment="판단 불가",
                reasons=["무료 사용 횟수를 초과하여 AI 진단이 제공되지 않았습니다."],
                usage_count=usage.usage_count
            )

        # 5. 프롬프트 로딩
        try:
            prompt = load_prompt("purchase_assistant_prompt.j2", {
                "transcript": transcript.strip(),
                "user_message": req.query.strip()
            })
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"프롬프트 로딩 실패: {str(e)}"])

        # 6. GPT 호출
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": req.query}
                ],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"GPT 처리 실패: {str(e)}"])

        # 7. 사용 횟수 증가
        usage = self.usage_repo.increment_usage(user_id, req.course_id)

        # 8. 안전한 응답 파싱
        allowed_judgments = {"적합", "다소 부족", "너무 고급", "보통"}
        judgment = parsed.get("judgment", "판단 불가")
        if judgment not in allowed_judgments:
            judgment = "판단 불가"

        recommendation = parsed.get("recommendation", "AI가 해당 영상의 적합성을 명확히 판단하지 못했습니다.")
        reasons = parsed.get("reasons", ["AI가 응답 형식에 맞춰 판단을 내리지 못했습니다."])

        return PurchaseAssistantResponse(
            recommendation=recommendation,
            judgment=judgment,
            reasons=reasons,
            usage_count=usage.usage_count
        )

    def _get_transcript_from_s3(self, video_id: int) -> str:
        s3_key = f"vod-transcripts/{video_id}/speech.txt"
        s3_url = f"https://{settings.aws.bucket_name}.s3.{settings.aws.region_name}.amazonaws.com/{s3_key}"

        try:
            local_path = download_file_from_s3(s3_url)
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
        finally:
            if 'local_path' in locals() and os.path.exists(local_path):
                os.remove(local_path)

    def get_usage_info(self, user_id: int, course_id: int) -> PurchaseAssistantUsageInfo:
        usage = self.usage_repo.get_by_user_and_course(user_id, course_id)
        used = usage.usage_count if usage else 0
        remaining = max(2 - used, 0)
        return PurchaseAssistantUsageInfo(usage_count=used, remaining=remaining)