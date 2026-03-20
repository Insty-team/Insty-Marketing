"""Instagram Reels 레퍼런스 수집 (수동 + Graph API own account).

Instagram Graph API 제한:
- 다른 계정의 Reels 검색/발견 불가
- 자기 계정 미디어의 성과(insights)만 조회 가능
- Business/Creator 계정 + Facebook Page 연동 필요

따라서:
1. 레퍼런스 수집은 수동 URL 입력 방식
2. 자기 계정 성과 추적은 Graph API 사용
"""

import logging
import os
import re
from typing import Optional

import requests

from config.settings import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Instagram Graph API
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def create_manual_reference(
    url: str,
    title: str = "",
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    duration_seconds: int = 0,
    notes: str = "",
) -> dict:
    """수동으로 IG Reel 레퍼런스 생성.

    Args:
        url: Instagram Reel URL
        title: 콘텐츠 제목/설명
        views, likes, comments: 대략적 수치 (IG에서 보고 수동 입력)
        duration_seconds: 영상 길이
        notes: 참고 사항

    Returns:
        레퍼런스 딕셔너리 (Notion 저장용)
    """
    reel_id = _parse_reel_id(url)

    return {
        "video_id": reel_id or url,
        "title": title or f"IG Reel {reel_id or 'unknown'}",
        "channel": "",
        "channel_id": "",
        "description": notes,
        "published_at": "",
        "url": url,
        "views": views,
        "likes": likes,
        "comments": comments,
        "duration_seconds": duration_seconds,
        "keyword": "manual_ig",
        "platform": "instagram_reels",
        "score": 0,
    }


def fetch_own_reels_metrics() -> list[dict]:
    """자기 IG 계정의 Reels 성과 조회 (Graph API).

    Returns:
        [{"media_id": str, "views": int, "likes": int, "comments": int,
          "saves": int, "shares": int, "url": str}, ...]
    """
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        logger.warning("IG_ACCESS_TOKEN 또는 IG_USER_ID 미설정")
        return []

    try:
        # 최근 미디어 조회
        media_url = f"{_GRAPH_API_BASE}/{IG_USER_ID}/media"
        resp = requests.get(media_url, params={
            "fields": "id,caption,media_type,permalink,timestamp",
            "access_token": IG_ACCESS_TOKEN,
            "limit": 25,
        })
        resp.raise_for_status()
        media_list = resp.json().get("data", [])

        results = []
        for media in media_list:
            if media.get("media_type") != "VIDEO":
                continue

            media_id = media["id"]
            metrics = _fetch_media_insights(media_id)
            if metrics:
                metrics["media_id"] = media_id
                metrics["url"] = media.get("permalink", "")
                metrics["caption"] = media.get("caption", "")[:200]
                metrics["timestamp"] = media.get("timestamp", "")
                results.append(metrics)

        logger.info(f"IG Reels 성과 조회: {len(results)}개")
        return results

    except requests.RequestException as e:
        logger.error(f"IG 미디어 조회 실패: {e}")
        return []


def _fetch_media_insights(media_id: str) -> Optional[dict]:
    """개별 미디어의 인사이트 조회."""
    try:
        insights_url = f"{_GRAPH_API_BASE}/{media_id}/insights"
        resp = requests.get(insights_url, params={
            "metric": "plays,likes,comments,saves,shares",
            "access_token": IG_ACCESS_TOKEN,
        })
        resp.raise_for_status()

        data = resp.json().get("data", [])
        metrics = {}
        for item in data:
            name = item.get("name", "")
            value = item.get("values", [{}])[0].get("value", 0)
            metrics[name] = value

        return {
            "views": metrics.get("plays", 0),
            "likes": metrics.get("likes", 0),
            "comments": metrics.get("comments", 0),
            "saves": metrics.get("saves", 0),
            "shares": metrics.get("shares", 0),
        }
    except requests.RequestException as e:
        logger.error(f"IG 인사이트 조회 실패 [{media_id}]: {e}")
        return None


def _parse_reel_id(url: str) -> Optional[str]:
    """URL에서 Instagram Reel ID 추출."""
    match = re.search(r"instagram\.com/reel/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None
