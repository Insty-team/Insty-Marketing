"""페르소나 기반 키워드 자동 생성."""

import json
import logging
from pathlib import Path

import google.generativeai as genai

from config.settings import GEMINI_API_KEY, PROJECT_ROOT

logger = logging.getLogger(__name__)

PERSONA_DOC = PROJECT_ROOT / "docs" / "what_is_insty.md"

KEYWORD_GEN_PROMPT = """You are a YouTube keyword strategist.

Based on the following business persona document, generate YouTube search keywords
that would help find tutorial/educational content relevant to this audience.

## Persona Document:
{persona}

## Requirements:
- Generate exactly {count} keywords grouped into categories
- Target audience: AI-powered solopreneurs, freelancers, small team leaders
- Focus on: AI tools, automation, productivity, solo business
- Keywords should be in English (YouTube global audience)
- Each keyword should be 2-5 words, searchable on YouTube
- Mix of: tool tutorials, how-to guides, comparison videos, tips

## Output Format (JSON):
{{
  "ai_tools": ["keyword1", "keyword2", ...],
  "automation": ["keyword1", "keyword2", ...],
  "solopreneur": ["keyword1", "keyword2", ...],
  "productivity": ["keyword1", "keyword2", ...],
  "business_strategy": ["keyword1", "keyword2", ...]
}}

Return ONLY valid JSON, no markdown fences.
"""


def generate_keywords(count: int = 100) -> dict[str, list[str]]:
    """페르소나 문서 기반으로 키워드 후보 생성.

    Args:
        count: 생성할 총 키워드 수

    Returns:
        카테고리별 키워드 딕셔너리
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    persona_text = PERSONA_DOC.read_text(encoding="utf-8")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = KEYWORD_GEN_PROMPT.format(persona=persona_text, count=count)

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # JSON 파싱 (마크다운 코드블록 제거)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        keywords = json.loads(text)
        total = sum(len(v) for v in keywords.values())
        logger.info(f"키워드 {total}개 생성 완료 ({len(keywords)} 카테고리)")
        return keywords

    except json.JSONDecodeError as e:
        logger.error(f"키워드 JSON 파싱 실패: {e}\n응답: {text[:500]}")
        return {}
    except Exception as e:
        logger.error(f"키워드 생성 실패: {e}")
        return {}
