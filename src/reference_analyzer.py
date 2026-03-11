"""레퍼런스 쇼츠/릴스 구조 분석 (Gemini 기반).

고성과 쇼츠의 Hook 유형, 영상 포맷, 컷 빈도, 콘텐츠 프레임워크 등을
분석하여 JSON으로 반환한다.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, PROMPTS_DIR

logger = logging.getLogger(__name__)

_PROMPT_FILE = PROMPTS_DIR / "reference_analysis.txt"


def analyze_reference(
    transcript: str,
    video_metadata: dict,
) -> Optional[dict]:
    """레퍼런스 영상의 구조를 분석.

    Args:
        transcript: 타임스탬프 포함 자막 텍스트
        video_metadata: shorts_discovery에서 반환된 영상 딕셔너리
            필수 키: video_id, title, channel, views, likes, comments,
                     duration_seconds, url

    Returns:
        분석 결과 JSON 또는 None
    """
    if not _PROMPT_FILE.exists():
        logger.error(f"프롬프트 파일 없음: {_PROMPT_FILE}")
        return None

    prompt_template = _PROMPT_FILE.read_text(encoding="utf-8")
    full_prompt = prompt_template.format(
        video_title=video_metadata.get("title", ""),
        channel=video_metadata.get("channel", ""),
        views=video_metadata.get("views", 0),
        likes=video_metadata.get("likes", 0),
        comments=video_metadata.get("comments", 0),
        duration_seconds=video_metadata.get("duration_seconds", 0),
        video_url=video_metadata.get("url", ""),
        transcript=transcript[:6000],  # 토큰 절약
    )

    return _analyze_with_gemini(full_prompt)


def _analyze_with_gemini(prompt: str) -> Optional[dict]:
    """Gemini API로 레퍼런스 분석."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # JSON 추출 (마크다운 코드블록 제거)
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            analysis = json.loads(text)

            # 필수 필드 검증
            required = ["hook_type", "video_format", "content_framework", "structure_breakdown"]
            missing = [f for f in required if f not in analysis]
            if missing:
                logger.warning(f"분석 결과 누락 필드: {missing}")
                # 누락되어도 사용 가능한 부분은 반환
                for field in missing:
                    analysis[field] = "unknown"

            logger.info("레퍼런스 구조 분석 완료")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"분석 JSON 파싱 실패: {e}\n응답: {text[:500]}")
            return None
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < 2:
                wait = 25 * (attempt + 1)
                logger.warning(f"Gemini rate limit, {wait}초 대기 ({attempt + 1}/3)")
                time.sleep(wait)
                continue
            logger.error(f"레퍼런스 분석 실패: {e}")
            return None

    return None
