"""프로덕션 가이드 생성 (레퍼런스 구조 + 소스 콘텐츠 결합).

레퍼런스 분석 결과의 구조를 템플릿으로, 소스 콘텐츠의 내용을
한국 1인 AI 사업자 타겟으로 적응시켜 촬영/편집 가이드를 생성한다.
"""

import json
import logging
import time
from typing import Optional

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, PROMPTS_DIR

logger = logging.getLogger(__name__)

_PROMPT_FILE = PROMPTS_DIR / "production_guide.txt"


def generate_production_guide(
    source_transcript: str,
    source_metadata: dict,
    reference_analysis: dict,
) -> Optional[dict]:
    """프로덕션 가이드 생성.

    Args:
        source_transcript: 소스 영상 자막
        source_metadata: 소스 영상 메타데이터 (title, url 등)
        reference_analysis: reference_analyzer.analyze_reference()의 출력

    Returns:
        프로덕션 가이드 JSON 또는 None
    """
    if not _PROMPT_FILE.exists():
        logger.error(f"프롬프트 파일 없음: {_PROMPT_FILE}")
        return None

    # structure_breakdown을 읽기 좋은 텍스트로 변환
    breakdown_text = _format_structure_breakdown(
        reference_analysis.get("structure_breakdown", [])
    )

    prompt_template = _PROMPT_FILE.read_text(encoding="utf-8")
    full_prompt = prompt_template.format(
        source_title=source_metadata.get("title", ""),
        source_transcript=source_transcript[:6000],
        ref_hook_type=reference_analysis.get("hook_type", "unknown"),
        ref_video_format=reference_analysis.get("video_format", "unknown"),
        ref_content_framework=reference_analysis.get("content_framework", "unknown"),
        ref_cut_frequency=reference_analysis.get("cut_frequency", "medium_4s"),
        ref_caption_style=reference_analysis.get("caption_style", "auto_captions"),
        ref_cta_type=reference_analysis.get("cta_type", "follow"),
        ref_structure_breakdown=breakdown_text,
        ref_key_patterns=", ".join(reference_analysis.get("key_patterns", [])),
    )

    return _generate_with_gemini(full_prompt)


def _format_structure_breakdown(breakdown: list) -> str:
    """structure_breakdown 리스트를 프롬프트용 텍스트로 변환."""
    if not breakdown or not isinstance(breakdown, list):
        return "No breakdown available"

    lines = []
    for segment in breakdown:
        if isinstance(segment, dict):
            ts = segment.get("timestamp", "?")
            element = segment.get("element", "?")
            content = segment.get("content_ko", segment.get("content", ""))
            visual = segment.get("visual_type", "")
            lines.append(f"  [{ts}] {element}: {content} (visual: {visual})")
        else:
            lines.append(f"  {segment}")
    return "\n".join(lines)


def _generate_with_gemini(prompt: str) -> Optional[dict]:
    """Gemini API로 프로덕션 가이드 생성."""
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

            guide = json.loads(text)

            # 필수 필드 검증
            required = ["title_ko", "script_ko", "shot_breakdown", "editing_guide"]
            missing = [f for f in required if f not in guide]
            if missing:
                logger.warning(f"가이드 누락 필드: {missing}")

            logger.info(f"프로덕션 가이드 생성 완료: {guide.get('title_ko', '?')}")
            return guide

        except json.JSONDecodeError as e:
            logger.error(f"가이드 JSON 파싱 실패: {e}\n응답: {text[:500]}")
            return None
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < 2:
                wait = 25 * (attempt + 1)
                logger.warning(f"Gemini rate limit, {wait}초 대기 ({attempt + 1}/3)")
                time.sleep(wait)
                continue
            logger.error(f"프로덕션 가이드 생성 실패: {e}")
            return None

    return None
