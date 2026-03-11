"""게시된 콘텐츠 성과 추적 및 패턴 분석.

YouTube Shorts와 Instagram Reels의 성과를 추적하고,
레퍼런스 벤치마크와 비교하여 승리 패턴을 식별한다.
"""

import logging
from typing import Optional

from googleapiclient.errors import HttpError

from src.youtube_discovery import get_youtube_client
from src.notion_experiment_writer import update_guide_performance
from src.shorts_discovery import _iso_duration_to_seconds

logger = logging.getLogger(__name__)


def track_youtube_metrics(video_id: str) -> Optional[dict]:
    """YouTube 영상의 현재 성과 지표 조회.

    Args:
        video_id: YouTube video ID

    Returns:
        {"views": int, "likes": int, "comments": int} 또는 None
    """
    try:
        youtube = get_youtube_client()
        response = youtube.videos().list(
            id=video_id,
            part="statistics",
        ).execute()

        items = response.get("items", [])
        if not items:
            logger.warning(f"영상을 찾을 수 없음: {video_id}")
            return None

        stats = items[0].get("statistics", {})
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
        }
    except HttpError as e:
        logger.error(f"YouTube 성과 조회 실패 [{video_id}]: {e}")
        return None


def compare_with_benchmark(
    actual_metrics: dict,
    reference_metrics: dict,
) -> dict:
    """실제 성과를 레퍼런스 벤치마크와 비교.

    Args:
        actual_metrics: 실제 성과 {"views": int, "likes": int, "comments": int}
        reference_metrics: 레퍼런스 성과 (같은 형식)

    Returns:
        비교 결과 딕셔너리
    """
    ref_views = max(reference_metrics.get("views", 1), 1)
    actual_views = max(actual_metrics.get("views", 0), 1)

    # 성과 비율 (1.0 = 레퍼런스와 동일)
    view_ratio = actual_views / ref_views

    # Engagement rate 비교
    ref_engagement = (
        (reference_metrics.get("likes", 0) + reference_metrics.get("comments", 0))
        / ref_views
    )
    actual_engagement = (
        (actual_metrics.get("likes", 0) + actual_metrics.get("comments", 0))
        / actual_views
    )

    return {
        "view_ratio": round(view_ratio, 3),
        "view_percent_of_ref": round(view_ratio * 100, 1),
        "ref_engagement_rate": round(ref_engagement * 100, 2),
        "actual_engagement_rate": round(actual_engagement * 100, 2),
        "engagement_better": actual_engagement >= ref_engagement,
        "verdict": _get_verdict(view_ratio, actual_engagement, ref_engagement),
    }


def _get_verdict(view_ratio: float, actual_eng: float, ref_eng: float) -> str:
    """성과 판정."""
    if view_ratio >= 0.5 and actual_eng >= ref_eng:
        return "STRONG - 포맷 유지, 확대 적용"
    elif view_ratio >= 0.2 and actual_eng >= ref_eng * 0.8:
        return "GOOD - 포맷 유지, Hook 개선 시도"
    elif view_ratio >= 0.1:
        return "AVERAGE - Hook 또는 포맷 변경 필요"
    else:
        return "WEAK - 다른 레퍼런스 구조 시도"


def identify_winning_patterns(performance_history: list[dict]) -> dict:
    """성과 히스토리에서 승리 패턴 추출.

    Args:
        performance_history: [
            {"hook_type": str, "video_format": str, "framework": str,
             "views": int, "engagement_rate": float, ...},
            ...
        ]

    Returns:
        패턴별 평균 성과 및 추천
    """
    if not performance_history:
        return {"message": "성과 데이터가 부족합니다"}

    # 패턴별 집계
    by_hook = {}
    by_format = {}
    by_framework = {}

    for entry in performance_history:
        views = entry.get("views", 0)
        eng = entry.get("engagement_rate", 0)

        hook = entry.get("hook_type", "unknown")
        fmt = entry.get("video_format", "unknown")
        fw = entry.get("framework", "unknown")

        by_hook.setdefault(hook, []).append({"views": views, "engagement": eng})
        by_format.setdefault(fmt, []).append({"views": views, "engagement": eng})
        by_framework.setdefault(fw, []).append({"views": views, "engagement": eng})

    def _avg(items):
        if not items:
            return {"avg_views": 0, "avg_engagement": 0, "count": 0}
        return {
            "avg_views": round(sum(i["views"] for i in items) / len(items)),
            "avg_engagement": round(
                sum(i["engagement"] for i in items) / len(items), 2
            ),
            "count": len(items),
        }

    return {
        "by_hook_type": {k: _avg(v) for k, v in by_hook.items()},
        "by_video_format": {k: _avg(v) for k, v in by_format.items()},
        "by_framework": {k: _avg(v) for k, v in by_framework.items()},
        "recommendation": _recommend(by_hook, by_format, by_framework),
    }


def _recommend(by_hook: dict, by_format: dict, by_framework: dict) -> str:
    """가장 성과 좋은 패턴 조합 추천."""

    def _best(group):
        if not group:
            return "unknown"
        return max(
            group.keys(),
            key=lambda k: sum(i["views"] for i in group[k]) / len(group[k]),
        )

    best_hook = _best(by_hook)
    best_format = _best(by_format)
    best_fw = _best(by_framework)

    return (
        f"최적 조합: Hook={best_hook}, "
        f"Format={best_format}, "
        f"Framework={best_fw}"
    )
