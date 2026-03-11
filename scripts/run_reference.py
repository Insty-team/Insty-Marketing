"""수동 URL 레퍼런스 분석.

특정 YouTube Shorts 또는 Instagram Reel URL을 분석하여
레퍼런스 카드 + 프로덕션 가이드를 생성한다.

Usage:
  python -m scripts.run_reference --url https://www.youtube.com/shorts/xxxxx
  python -m scripts.run_reference --url https://www.instagram.com/reel/xxxxx
  python -m scripts.run_reference --url https://youtu.be/xxxxx
"""

import argparse
import json
import logging
import re
from datetime import datetime
from typing import Optional

from config.experiment_config import EXPERIMENT_LOG_DIR, EXPERIMENT_OUTPUT_DIR
from src.transcript_extractor import extract_transcript
from src.reference_analyzer import analyze_reference
from src.production_guide_generator import generate_production_guide
from src.notion_experiment_writer import save_reference, save_production_guide

EXPERIMENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _parse_youtube_id(url: str) -> Optional[str]:
    """URL에서 YouTube video ID 추출."""
    patterns = [
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _parse_instagram_id(url: str) -> Optional[str]:
    """URL에서 Instagram Reel ID 추출."""
    match = re.search(r"instagram\.com/reel/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def _fetch_youtube_metadata(video_id: str) -> Optional[dict]:
    """YouTube API로 영상 메타데이터 조회."""
    from src.youtube_discovery import get_youtube_client
    from src.shorts_discovery import _iso_duration_to_seconds

    try:
        youtube = get_youtube_client()
        response = youtube.videos().list(
            id=video_id,
            part="snippet,statistics,contentDetails",
        ).execute()

        items = response.get("items", [])
        if not items:
            logger.error(f"영상을 찾을 수 없음: {video_id}")
            return None

        video = items[0]
        snippet = video["snippet"]
        stats = video.get("statistics", {})
        content = video.get("contentDetails", {})

        return {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "url": f"https://www.youtube.com/shorts/{video_id}",
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "duration_seconds": _iso_duration_to_seconds(content.get("duration", "")),
            "keyword": "manual",
            "platform": "youtube_shorts",
            "score": 0,
        }
    except Exception as e:
        logger.error(f"메타데이터 조회 실패: {e}")
        return None


def process_youtube_url(url: str, generate_guide: bool = True, dry_run: bool = False):
    """YouTube URL을 분석하여 레퍼런스 카드 + 가이드 생성."""
    video_id = _parse_youtube_id(url)
    if not video_id:
        logger.error(f"YouTube video ID를 추출할 수 없음: {url}")
        return

    logger.info(f"YouTube 분석 시작: {video_id}")

    # 메타데이터 조회
    metadata = _fetch_youtube_metadata(video_id)
    if not metadata:
        return

    logger.info(f"제목: {metadata['title']}")
    logger.info(f"조회수: {metadata['views']:,} / 좋아요: {metadata['likes']:,}")

    # 자막 추출
    transcript = extract_transcript(video_id)
    if not transcript:
        logger.error("자막을 추출할 수 없습니다.")
        return

    # 레퍼런스 분석
    logger.info("구조 분석 중...")
    analysis = analyze_reference(transcript, metadata)
    if not analysis:
        logger.error("구조 분석 실패")
        return

    logger.info(f"Hook: {analysis.get('hook_type')} | Format: {analysis.get('video_format')}")
    logger.info(f"Framework: {analysis.get('content_framework')}")
    logger.info(f"재현성: {analysis.get('replicability_score')}/10")

    # Notion 저장
    if not dry_run:
        ref_page = save_reference(metadata, analysis)
        if ref_page:
            logger.info(f"레퍼런스 Notion 저장: {ref_page}")

    # 프로덕션 가이드 생성
    if generate_guide:
        logger.info("프로덕션 가이드 생성 중...")
        guide = generate_production_guide(
            source_transcript=transcript,
            source_metadata=metadata,
            reference_analysis=analysis,
        )
        if guide:
            guide["reference_url"] = metadata.get("url", "")
            guide["reference_title"] = metadata.get("title", "")

            if not dry_run:
                guide_page = save_production_guide(guide, metadata, metadata)
                if guide_page:
                    logger.info(f"가이드 Notion 저장: {guide_page}")

            # 로컬 백업
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = EXPERIMENT_OUTPUT_DIR / f"manual_guide_{ts}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(guide, f, ensure_ascii=False, indent=2)
            logger.info(f"가이드 로컬 저장: {path}")
        else:
            logger.error("프로덕션 가이드 생성 실패")


def process_instagram_url(url: str):
    """Instagram Reel URL (수동 메타데이터 입력)."""
    reel_id = _parse_instagram_id(url)
    if not reel_id:
        logger.error(f"Instagram Reel ID를 추출할 수 없음: {url}")
        return

    logger.info(f"Instagram Reel: {reel_id}")
    logger.info("IG API 제한으로 자동 분석이 불가합니다.")
    logger.info("레퍼런스로 저장하려면 아래 정보를 수동 입력하세요:")
    logger.info("  --title, --views, --likes, --comments, --duration")
    logger.info("또는 Notion에서 직접 레퍼런스 카드를 생성하세요.")


def main():
    parser = argparse.ArgumentParser(description="수동 URL 레퍼런스 분석")
    parser.add_argument("--url", required=True, help="YouTube Shorts 또는 IG Reel URL")
    parser.add_argument("--no-guide", action="store_true",
                        help="프로덕션 가이드 생성 안 함 (분석만)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Notion 저장 없이 테스트")
    args = parser.parse_args()

    url = args.url.strip()

    if "youtube.com" in url or "youtu.be" in url:
        process_youtube_url(url, generate_guide=not args.no_guide, dry_run=args.dry_run)
    elif "instagram.com" in url:
        process_instagram_url(url)
    else:
        logger.error(f"지원하지 않는 URL: {url}")
        logger.info("지원 플랫폼: YouTube Shorts, Instagram Reels")


if __name__ == "__main__":
    main()
