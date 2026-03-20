"""게시 콘텐츠 성과 추적 (수동 실행 또는 실험 파이프라인에서 호출).

Usage:
  python -m scripts.run_performance_check --video-id <youtube_id> --snapshot 24h
  python -m scripts.run_performance_check --ig-check  # IG 자기 계정 체크
"""

import argparse
import json
import logging
from datetime import datetime

from config.experiment_config import EXPERIMENT_LOG_DIR, EXPERIMENT_OUTPUT_DIR
from src.performance_tracker import (
    track_youtube_metrics,
    compare_with_benchmark,
    identify_winning_patterns,
)
from src.ig_reference_collector import fetch_own_reels_metrics

EXPERIMENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def check_youtube(video_id: str, snapshot: str = "24h"):
    """YouTube 영상 성과 체크."""
    logger.info(f"YouTube 성과 체크: {video_id} ({snapshot})")

    metrics = track_youtube_metrics(video_id)
    if not metrics:
        logger.error("성과 조회 실패")
        return

    logger.info(f"  조회수: {metrics['views']:,}")
    logger.info(f"  좋아요: {metrics['likes']:,}")
    logger.info(f"  댓글: {metrics['comments']:,}")

    engagement = (metrics["likes"] + metrics["comments"]) / max(metrics["views"], 1) * 100
    logger.info(f"  Engagement Rate: {engagement:.2f}%")


def check_instagram():
    """IG 자기 계정 Reels 성과 체크."""
    logger.info("Instagram Reels 성과 체크")

    results = fetch_own_reels_metrics()
    if not results:
        logger.info("조회 가능한 Reels 없음 (IG_ACCESS_TOKEN / IG_USER_ID 확인)")
        return

    for r in results:
        logger.info(f"\n[{r.get('caption', 'N/A')[:50]}]")
        logger.info(f"  Views: {r.get('views', 0):,}")
        logger.info(f"  Likes: {r.get('likes', 0):,}")
        logger.info(f"  Comments: {r.get('comments', 0):,}")
        logger.info(f"  Saves: {r.get('saves', 0):,}")
        logger.info(f"  Shares: {r.get('shares', 0):,}")

    # 로컬 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPERIMENT_OUTPUT_DIR / f"ig_metrics_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"\n성과 데이터 저장: {path}")


def main():
    parser = argparse.ArgumentParser(description="성과 추적")
    parser.add_argument("--video-id", help="YouTube video ID")
    parser.add_argument("--snapshot", default="24h", choices=["24h", "48h", "7d"])
    parser.add_argument("--ig-check", action="store_true", help="IG 자기 계정 체크")
    args = parser.parse_args()

    if args.ig_check:
        check_instagram()
    elif args.video_id:
        check_youtube(args.video_id, args.snapshot)
    else:
        logger.info("--video-id 또는 --ig-check 중 하나를 지정하세요.")


if __name__ == "__main__":
    main()
