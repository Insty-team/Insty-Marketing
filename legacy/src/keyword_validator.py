"""YouTube API로 키워드 검증 (실제 검색 결과 수 + 평균 조회수)."""

import logging
from pathlib import Path
from typing import Optional

from config.settings import KEYWORD_VALIDATION, PROJECT_ROOT
from src.youtube_discovery import get_youtube_client

logger = logging.getLogger(__name__)

KEYWORDS_FILE = PROJECT_ROOT / "config" / "keywords.py"


def validate_keyword(keyword: str) -> Optional[dict]:
    """키워드의 YouTube 검색 성과를 검증.

    Returns:
        {"keyword": str, "result_count": int, "avg_views": float} or None (실패 시)
    """
    youtube = get_youtube_client()
    top_n = KEYWORD_VALIDATION["top_n_for_avg"]

    try:
        # search.list
        search_resp = youtube.search().list(
            q=keyword,
            part="id",
            type="video",
            order="relevance",
            maxResults=top_n,
        ).execute()

        items = search_resp.get("items", [])
        result_count = search_resp.get("pageInfo", {}).get("totalResults", 0)
        video_ids = [item["id"]["videoId"] for item in items if item["id"].get("videoId")]

        if not video_ids:
            return {"keyword": keyword, "result_count": 0, "avg_views": 0}

        # videos.list — 조회수 확인
        videos_resp = youtube.videos().list(
            id=",".join(video_ids),
            part="statistics",
        ).execute()

        views = [
            int(v.get("statistics", {}).get("viewCount", 0))
            for v in videos_resp.get("items", [])
        ]
        avg_views = sum(views) / len(views) if views else 0

        return {
            "keyword": keyword,
            "result_count": result_count,
            "avg_views": avg_views,
        }

    except Exception as e:
        logger.error(f"키워드 검증 실패 [{keyword}]: {e}")
        return None


def validate_keywords(keywords: dict[str, list[str]]) -> dict[str, list[str]]:
    """카테고리별 키워드를 검증하고 통과한 것만 반환.

    Args:
        keywords: {"category": ["kw1", "kw2", ...]}

    Returns:
        검증 통과한 키워드만 포함된 딕셔너리
    """
    min_results = KEYWORD_VALIDATION["min_results"]
    min_avg_views = KEYWORD_VALIDATION["min_avg_views"]

    validated = {}
    total_checked = 0
    total_passed = 0

    for category, kw_list in keywords.items():
        passed = []
        for kw in kw_list:
            total_checked += 1
            result = validate_keyword(kw)
            if result is None:
                continue
            if result["result_count"] >= min_results and result["avg_views"] >= min_avg_views:
                passed.append(kw)
                total_passed += 1
                logger.info(
                    f"  PASS [{category}] '{kw}' — "
                    f"결과 {result['result_count']}, 평균 조회수 {result['avg_views']:,.0f}"
                )
            else:
                logger.debug(
                    f"  FAIL [{category}] '{kw}' — "
                    f"결과 {result['result_count']}, 평균 조회수 {result['avg_views']:,.0f}"
                )
        if passed:
            validated[category] = passed

    logger.info(f"키워드 검증 완료: {total_checked}개 중 {total_passed}개 통과")
    return validated


def save_keywords(keywords: dict[str, list[str]]) -> None:
    """검증된 키워드를 config/keywords.py에 저장."""
    lines = [
        '"""검색 키워드 목록.',
        "",
        "키워드는 src/keyword_generator.py로 페르소나 기반 자동 생성 후",
        "src/keyword_validator.py로 YouTube 검증을 거쳐 여기 저장됨.",
        "scripts/run_keyword_refresh.py로 갱신 (월 1회 수동 실행 권장).",
        '"""',
        "",
        "# 검증 완료된 키워드 (카테고리별)",
        '# 형식: {"카테고리": ["keyword1", "keyword2", ...]}',
        "KEYWORDS: dict[str, list[str]] = {",
    ]

    for category, kw_list in sorted(keywords.items()):
        lines.append(f'    "{category}": [')
        for kw in kw_list:
            lines.append(f'        "{kw}",')
        lines.append("    ],")

    lines.extend([
        "}",
        "",
        "",
        "def get_all_keywords() -> list[str]:",
        '    """모든 카테고리의 키워드를 하나의 리스트로 반환."""',
        "    return [kw for keywords in KEYWORDS.values() for kw in keywords]",
        "",
        "",
        "def get_keywords_by_category(category: str) -> list[str]:",
        '    """특정 카테고리의 키워드만 반환."""',
        "    return KEYWORDS.get(category, [])",
        "",
        "",
        "def get_categories() -> list[str]:",
        '    """모든 카테고리 이름 반환."""',
        "    return list(KEYWORDS.keys())",
        "",
    ])

    KEYWORDS_FILE.write_text("\n".join(lines), encoding="utf-8")
    total = sum(len(v) for v in keywords.values())
    logger.info(f"keywords.py 저장 완료: {total}개 키워드, {len(keywords)} 카테고리")
