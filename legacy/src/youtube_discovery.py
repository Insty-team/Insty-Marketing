"""YouTube Data API v3를 이용한 콘텐츠 발굴."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import (
    YOUTUBE_API_KEY,
    YOUTUBE_FILTERS,
    SCORING_WEIGHTS,
)

logger = logging.getLogger(__name__)


def get_youtube_client():
    """YouTube Data API 클라이언트 생성."""
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def search_videos(
    keyword: str,
    max_results: int = YOUTUBE_FILTERS["max_results_per_keyword"],
    published_after: Optional[datetime] = None,
) -> list[dict]:
    """키워드로 YouTube 영상을 검색하고 상세 정보를 반환.

    Args:
        keyword: 검색 키워드
        max_results: 최대 결과 수
        published_after: 이 날짜 이후 영상만 검색

    Returns:
        필터링+스코어링된 영상 리스트 (점수 내림차순)
    """
    youtube = get_youtube_client()

    if published_after is None:
        published_after = datetime.now(timezone.utc) - timedelta(
            days=YOUTUBE_FILTERS["max_age_days"]
        )

    # Step 1: search.list (100 units/call)
    try:
        search_response = youtube.search().list(
            q=keyword,
            part="id,snippet",
            type="video",
            order="relevance",
            publishedAfter=published_after.isoformat(),
            relevanceLanguage=YOUTUBE_FILTERS["language"],
            maxResults=max_results,
        ).execute()
    except HttpError as e:
        logger.error(f"YouTube 검색 실패 [{keyword}]: {e}")
        return []

    video_ids = [
        item["id"]["videoId"]
        for item in search_response.get("items", [])
        if item["id"].get("videoId")
    ]

    if not video_ids:
        logger.info(f"검색 결과 없음: {keyword}")
        return []

    # Step 2: videos.list — 상세 정보 (1 unit/call)
    try:
        videos_response = youtube.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics,contentDetails",
        ).execute()
    except HttpError as e:
        logger.error(f"영상 상세 정보 조회 실패: {e}")
        return []

    # Step 3: 필터링 + 스코어링
    results = []
    for video in videos_response.get("items", []):
        parsed = _parse_video(video, keyword)
        if parsed and _passes_filter(parsed):
            parsed["score"] = _calculate_score(parsed)
            results.append(parsed)

    results.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"[{keyword}] 검색 {len(video_ids)}개 → 필터 통과 {len(results)}개")
    return results


def _parse_video(video: dict, keyword: str) -> Optional[dict]:
    """YouTube API 응답을 내부 형식으로 변환."""
    try:
        snippet = video["snippet"]
        stats = video.get("statistics", {})
        content = video.get("contentDetails", {})

        return {
            "video_id": video["id"],
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "duration_iso": content.get("duration", ""),
            "duration_minutes": _iso_duration_to_minutes(content.get("duration", "")),
            "keyword": keyword,
        }
    except (KeyError, ValueError) as e:
        logger.warning(f"영상 파싱 실패: {e}")
        return None


def _passes_filter(video: dict) -> bool:
    """필터 조건 통과 여부."""
    if video["views"] < YOUTUBE_FILTERS["min_views"]:
        return False
    if video["duration_minutes"] < YOUTUBE_FILTERS["min_duration_minutes"]:
        return False
    if video["duration_minutes"] > YOUTUBE_FILTERS["max_duration_minutes"]:
        return False
    return True


def _calculate_score(video: dict) -> float:
    """영상 스코어 계산 (0~100)."""
    w = SCORING_WEIGHTS

    # 조회수 점수 (log scale, 5k=0, 1M=100)
    import math
    view_score = min(100, max(0, (math.log10(max(video["views"], 1)) - 3.7) * 40))

    # 좋아요 비율 점수
    like_ratio = video["likes"] / max(video["views"], 1)
    like_score = min(100, like_ratio * 2000)

    # 댓글 점수
    comment_ratio = video["comments"] / max(video["views"], 1)
    comment_score = min(100, comment_ratio * 5000)

    # 최신성 점수
    try:
        pub_date = datetime.fromisoformat(video["published_at"].replace("Z", "+00:00"))
        days_ago = (datetime.now(timezone.utc) - pub_date).days
        recency_score = max(0, 100 - days_ago * 0.5)
    except (ValueError, TypeError):
        recency_score = 50

    return (
        w["views"] * view_score
        + w["likes"] * like_score
        + w["comments"] * comment_score
        + w["recency"] * recency_score
    )


def _iso_duration_to_minutes(duration: str) -> float:
    """ISO 8601 duration을 분으로 변환. 예: PT1H2M30S → 62.5"""
    if not duration:
        return 0
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 60 + minutes + seconds / 60
