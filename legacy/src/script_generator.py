"""AI를 이용한 Reels 스크립트 생성.

크론잡: Gemini 무료 tier
수동 실행: Claude Code (Max 구독)
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from config.settings import AI_BACKEND, GEMINI_API_KEY, PROMPTS_DIR

logger = logging.getLogger(__name__)


def generate_reels_script(
    transcript: str,
    video_title: str,
    video_url: str,
    concept: str = "tutorial",
    backend: Optional[str] = None,
) -> Optional[dict]:
    """자막에서 Reels 스크립트 생성.

    Args:
        transcript: 타임스탬프 포함 자막 텍스트
        video_title: 원본 영상 제목
        video_url: 원본 영상 URL
        concept: 스크립트 콘셉트 (tutorial, tips, celebrity, numbered_tips, numbered_lessons)
        backend: AI 백엔드 강제 지정 (None이면 설정값 사용)

    Returns:
        스크립트 JSON:
        {
            "hook": {"text": str, "duration": "0-5s", "source_timestamp": str},
            "why": {"text": str, "duration": "5-15s", "source_timestamp": str},
            "how": {"text": str, "duration": "15-35s", "source_timestamp": str},
            "summary": {"text": str, "duration": "35-45s", "source_timestamp": str},
            "cta": {"text": str, "duration": "45-60s"},
            "caption": str,
            "hashtags": list[str],
            "cta_keyword": str,
        }
    """
    active_backend = backend or AI_BACKEND

    prompt_file = PROMPTS_DIR / f"reels_{concept}.txt"
    if not prompt_file.exists():
        logger.error(f"프롬프트 파일 없음: {prompt_file}")
        return None

    prompt_template = prompt_file.read_text(encoding="utf-8")
    full_prompt = prompt_template.format(
        video_title=video_title,
        video_url=video_url,
        transcript=transcript[:8000],  # 토큰 제한
    )

    if active_backend == "gemini":
        return _generate_with_gemini(full_prompt)
    elif active_backend == "claude":
        # Claude Code에서 수동 실행 시 — 이 함수 대신 직접 프롬프트 사용
        logger.info("Claude 백엔드: Claude Code에서 직접 프롬프트를 실행하세요.")
        logger.info(f"프롬프트 파일: {prompt_file}")
        return None
    else:
        logger.error(f"알 수 없는 AI 백엔드: {active_backend}")
        return None


def _generate_with_gemini(prompt: str) -> Optional[dict]:
    """Gemini API로 스크립트 생성."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # JSON 추출
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            script = json.loads(text)
            logger.info("Reels 스크립트 생성 완료 (Gemini)")
            return script

        except json.JSONDecodeError as e:
            logger.error(f"스크립트 JSON 파싱 실패: {e}\n응답: {text[:500]}")
            return None
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < 2:
                wait = 25 * (attempt + 1)
                logger.warning(f"Gemini rate limit, {wait}초 대기 후 재시도 ({attempt + 1}/3)")
                time.sleep(wait)
                continue
            logger.error(f"Gemini 스크립트 생성 실패: {e}")
            return None
    return None
