import os
from uuid import UUID
from sqlalchemy.orm import Session

from app.schemas.video import TitleSuggestionResponse
from app.utils.s3_utils import download_file_from_s3
from app.utils.prompt_loader import load_prompt
from app.utils.clean_gpt_text import clean_gpt_text
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.repositories.video.video_course_repository import VideoCourseRepository
from botocore.exceptions import ClientError
from openai import OpenAI

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class VideoTitleSuggestionService:
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoCourseRepository(db)

    def suggest_title(self, video_uuid: UUID, original_title: str) -> TitleSuggestionResponse:
        video = self.video_repo.get_active_video_by_uuid(str(video_uuid))
        if not video:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["해당 video_uuid의 강의가 존재하지 않습니다."])
        video_id = video.id
        
        if video.analysis_status == "PROCESSING":
            raise APIException(ErrorCode.ANALYSIS_NOT_READY, details=["영상 분석이 아직 완료되지 않았습니다."])
        if video.analysis_status == "FAILED":
            raise APIException(ErrorCode.ANALYSIS_FAILED, details=["영상 분석에 실패한 상태입니다."])

        try:
            transcript_text = self._get_transcript_from_s3(video_id)
        except APIException:
            raise
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"S3 처리 중 오류: {str(e)}"])

        try:
            prompt = load_prompt("title_suggestion_prompt.j2", {
                "transcript": transcript_text.strip(),
                "original_title": original_title.strip()
            })
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"프롬프트 로딩 실패: {str(e)}"])

        title = self._generate_with_gpt(prompt)
        return TitleSuggestionResponse(title=title)

    def _get_transcript_from_s3(self, video_id: int) -> str:
        s3_key = f"vod-transcripts/{video_id}/speech.txt"
        s3_url = f"https://{settings.aws.bucket_name}.s3.{settings.aws.region_name}.amazonaws.com/{s3_key}"

        try:
            local_path = download_file_from_s3(s3_url)
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read()

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise APIException(
                    ErrorCode.FAILED_NOT_FOUND_VOICE,
                    details=[f"음성 텍스트 파일이 존재하지 않습니다. (video_id={video_id})"]
                )
            raise APIException(
                ErrorCode.INTERNAL_ERROR,
                details=[f"S3 ClientError 발생: {error_code}", str(e)]
            )

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"S3 예외 발생: {str(e)}"])

        finally:
            if 'local_path' in locals() and os.path.exists(local_path):
                os.remove(local_path)

    def _generate_with_gpt(self, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()
            return clean_gpt_text(raw)

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"GPT 호출 실패: {str(e)}"])
