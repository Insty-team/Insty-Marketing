"""YouTube Shorts 고성과 레퍼런스 발견.

기존 youtube_discovery.py의 클라이언트를 재사용하되,
Shorts 전용 필터링(< 60초)과 engagement ratio 기반 스코어링을 적용한다.
"""

import logging
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.errors import HttpError

from config.experiment_config import SHORTS_FILTERS, SHORTS_SCORING_WEIGHTS
from src.youtube_discovery import get_youtube_client

logger = logging.getLogger(__name__)


def search_shorts(
    keyword: str,
    max_results: int = SHORTS_FILTERS["max_results_per_keyword"],
    published_after: Optional[datetime] = None,
) -> list[dict]:
    """YouTube Shorts(< 60초) 고성과 영상 검색.

    Args:
        keyword: 검색 키워드
        max_results: 최대 결과 수
        published_after: 이 날짜 이후만 검색

    Returns:
        Shorts 영상 리스트 (engagement score 내림차순)
    """
    youtube = get_youtube_client()

    if published_after is None:
        published_after = datetime.now(timezone.utc) - timedelta(
            days=SHORTS_FILTERS["max_age_days"]
        )

    # Step 1: search.list — videoDuration=short (< 4분), #Shorts 힌트 추가
    search_query = f"{keyword} #Shorts"
    try:
        search_response = youtube.search().list(
            q=search_query,
            part="id,snippet",
            type="video",
            videoDuration="short",  # < 4분 필터 (API 레벨)
            order="viewCount",
            publishedAfter=published_after.isoformat(),
            relevanceLanguage=SHORTS_FILTERS["language"],
            maxResults=max_results,
        ).execute()
    except HttpError as e:
        logger.error(f"Shorts 검색 실패 [{keyword}]: {e}")
        return []

    video_ids = [
        item["id"]["videoId"]
        for item in search_response.get("items", [])
        if item["id"].get("videoId")
    ]

    if not video_ids:
        logger.info(f"Shorts 검색 결과 없음: {keyword}")
        return []

    # Step 2: videos.list — 상세 정보 (배치, 1 unit)
    try:
        videos_response = youtube.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics,contentDetails",
        ).execute()
    except HttpError as e:
        logger.error(f"Shorts 상세 조회 실패: {e}")
        return []

    # Step 3: Shorts 필터 + 스코어링
    results = []
    for video in videos_response.get("items", []):
        parsed = _parse_shorts_video(video, keyword)
        if parsed and _passes_shorts_filter(parsed):
            parsed["score"] = _calculate_shorts_score(parsed)
            results.append(parsed)

    results.sort(key=lambda x: x["score"], reverse=True)
    logger.info(
        f"[Shorts:{keyword}] 검색 {len(video_ids)}개 → Shorts 필터 통과 {len(results)}개"
    )
    return results


def _parse_shorts_video(video: dict, keyword: str) -> Optional[dict]:
    """YouTube API 응답을 Shorts 내부 형식으로 변환."""
    try:
        snippet = video["snippet"]
        stats = video.get("statistics", {})
        content = video.get("contentDetails", {})

        duration_seconds = _iso_duration_to_seconds(content.get("duration", ""))

        return {
            "video_id": video["id"],
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "url": f"https://www.youtube.com/shorts/{video['id']}",
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "duration_seconds": duration_seconds,
            "duration_iso": content.get("duration", ""),
            "keyword": keyword,
            "platform": "youtube_shorts",
        }
    except (KeyError, ValueError) as e:
        logger.warning(f"Shorts 영상 파싱 실패: {e}")
        return None


def _passes_shorts_filter(video: dict) -> bool:
    """Shorts 전용 필터 (< 60초, min views)."""
    if video["duration_seconds"] > SHORTS_FILTERS["max_duration_seconds"]:
        return False
    if video["duration_seconds"] < 5:  # 너무 짧은 건 제외
        return False
    if video["views"] < SHORTS_FILTERS["min_views"]:
        return False
    return True


def _calculate_shorts_score(video: dict) -> float:
    """Shorts engagement 기반 스코어 (0~100).

    일반 영상과 달리 engagement ratio를 가장 높게 가중한다.
    """
    w = SHORTS_SCORING_WEIGHTS
    views = max(video["views"], 1)

    # Engagement ratio (likes + comments) / views
    engagement = (video["likes"] + video["comments"]) / views
    engagement_score = min(100, engagement * 1000)  # 10% ratio = 100점

    # 조회수 (log scale, 10K=0, 10M=100)
    view_score = min(100, max(0, (math.log10(views) - 4) * 33))

    # 최신성
    try:
        pub_date = datetime.fromisoformat(video["published_at"].replace("Z", "+00:00"))
        days_ago = (datetime.now(timezone.utc) - pub_date).days
        recency_score = max(0, 100 - days_ago * 3)  # 30일 기준
    except (ValueError, TypeError):
        recency_score = 50

    # 댓글 비율 (토론 유발력)
    comment_ratio = video["comments"] / views
    comment_score = min(100, comment_ratio * 10000)

    return (
        w["engagement_ratio"] * engagement_score
        + w["views"] * view_score
        + w["recency"] * recency_score
        + w["comment_ratio"] * comment_score
    )


def _iso_duration_to_seconds(duration: str) -> int:
    """ISO 8601 duration을 초로 변환. 예: PT45S → 45, PT1M30S → 90"""
    if not duration:
        return 0
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
