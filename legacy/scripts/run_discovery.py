"""Phase 1: YouTube 영상 발굴 단독 실행."""

import argparse
import logging
import sys

from config.keywords import get_all_keywords, get_keywords_by_category, get_categories
from src.youtube_discovery import search_videos
from src.csv_backup import save_to_csv
from src.notion_writer import save_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="YouTube 영상 발굴")
    parser.add_argument("--keyword", "-k", help="특정 키워드로 검색")
    parser.add_argument("--category", "-c", help="특정 카테고리 키워드로 검색")
    parser.add_argument("--max-results", "-n", type=int, default=10)
    parser.add_argument("--no-notion", action="store_true", help="Notion 저장 건너뜀")
    parser.add_argument("--no-csv", action="store_true", help="CSV 저장 건너뜀")
    args = parser.parse_args()

    # 키워드 결정
    if args.keyword:
        keywords = [args.keyword]
    elif args.category:
        keywords = get_keywords_by_category(args.category)
        if not keywords:
            logger.error(f"카테고리 '{args.category}' 없음. 가능: {get_categories()}")
            sys.exit(1)
    else:
        keywords = get_all_keywords()
        if not keywords:
            logger.error("키워드가 없습니다. scripts/run_keyword_refresh.py를 먼저 실행하세요.")
            sys.exit(1)

    logger.info(f"검색 키워드 {len(keywords)}개: {keywords[:5]}{'...' if len(keywords) > 5 else ''}")

    all_videos = []
    for kw in keywords:
        videos = search_videos(kw, max_results=args.max_results)
        all_videos.extend(videos)

    logger.info(f"총 발굴 영상: {len(all_videos)}개")

    # Notion 저장
    if not args.no_notion and all_videos:
        saved = 0
        for video in all_videos:
            if save_video(video):
                saved += 1
        logger.info(f"Notion 저장: {saved}개")

    # CSV 백업
    if not args.no_csv and all_videos:
        save_to_csv(all_videos, prefix="discovery")

    return all_videos


if __name__ == "__main__":
    main()
