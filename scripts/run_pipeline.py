"""전체 파이프라인 실행 (크론잡용).

Discovery → 자막 추출 → 스크립트 생성 → Notion 저장 → CSV 백업

콘셉트 모드:
  - talking: 기존 말하기 스크립트 (tutorial, tips, celebrity)
  - numbered: 자막+음악 스타일 (numbered_tips, numbered_lessons)
  - all: 양쪽 모두 생성 (주 10개)
"""

import argparse
import logging
from datetime import datetime

from config.keywords import get_all_keywords, get_categories, get_keywords_by_category
from config.settings import LOG_DIR
from src.youtube_discovery import search_videos
from src.transcript_extractor import extract_transcript
from src.script_generator import generate_reels_script
from src.notion_writer import save_video
from src.csv_backup import save_to_csv

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

# 콘셉트 그룹 정의
TALKING_CONCEPTS = ["tutorial", "tips", "celebrity"]
NUMBERED_CONCEPTS = ["numbered_tips", "numbered_lessons"]
ALL_CONCEPTS = TALKING_CONCEPTS + NUMBERED_CONCEPTS


def _process_videos(videos, concept, max_videos):
    """영상 목록에 대해 자막 추출 + 스크립트 생성 + 저장."""
    processed = []
    for video in videos[:max_videos]:
        logger.info(f"[{concept}] 처리 중: {video['title'][:60]}")

        transcript = extract_transcript(video["video_id"])
        if not transcript:
            logger.warning(f"자막 없음, 건너뜀: {video['video_id']}")
            continue

        script = generate_reels_script(
            transcript=transcript,
            video_title=video["title"],
            video_url=video["url"],
            concept=concept,
        )

        page_id = save_video(video, script=script)
        video["notion_page_id"] = page_id
        video["has_script"] = script is not None
        video["concept"] = concept
        processed.append(video)

    return processed


def main():
    parser = argparse.ArgumentParser(description="전체 파이프라인")
    parser.add_argument("--category", "-c", help="특정 카테고리만 실행")
    parser.add_argument("--max-videos", "-n", type=int, default=5,
                        help="콘셉트당 최대 처리 영상 수")
    parser.add_argument("--concept", default="tutorial",
                        choices=ALL_CONCEPTS)
    parser.add_argument("--mode", default="single",
                        choices=["single", "talking", "numbered", "all"],
                        help="single: --concept 하나만 / talking: 말하기 5개 / "
                             "numbered: 자막 5개 / all: 양쪽 10개")
    parser.add_argument("--dry-run", action="store_true",
                        help="발굴만 하고 스크립트/저장 건너뜀")
    args = parser.parse_args()

    logger.info("=== 파이프라인 시작 ===")

    # 콘셉트 목록 결정
    if args.mode == "single":
        concepts = [args.concept]
    elif args.mode == "talking":
        concepts = TALKING_CONCEPTS
    elif args.mode == "numbered":
        concepts = NUMBERED_CONCEPTS
    elif args.mode == "all":
        concepts = ALL_CONCEPTS

    # 1. 키워드 선택 (카테고리 로테이션)
    if args.category:
        keywords = get_keywords_by_category(args.category)
    else:
        categories = get_categories()
        if categories:
            day_index = datetime.now().weekday() % len(categories)
            category = categories[day_index]
            keywords = get_keywords_by_category(category)
            logger.info(f"오늘의 카테고리: {category}")
        else:
            keywords = get_all_keywords()

    if not keywords:
        logger.error("키워드 없음. run_keyword_refresh.py를 먼저 실행하세요.")
        return

    # 2. Discovery
    all_videos = []
    for kw in keywords[:3]:
        videos = search_videos(kw, max_results=args.max_videos)
        all_videos.extend(videos)

    logger.info(f"발굴 영상: {len(all_videos)}개")

    if args.dry_run:
        save_to_csv(all_videos, prefix="dryrun")
        logger.info("Dry run 완료")
        return

    # 3. 콘셉트별 스크립트 생성
    all_processed = []
    for concept in concepts:
        logger.info(f"--- 콘셉트: {concept} ---")
        processed = _process_videos(all_videos, concept, args.max_videos)
        all_processed.extend(processed)

    # 4. CSV 백업
    save_to_csv(all_videos, prefix="discovery")
    if all_processed:
        save_to_csv(all_processed, prefix="processed")

    talking_count = sum(1 for p in all_processed if p.get("concept") in TALKING_CONCEPTS)
    numbered_count = sum(1 for p in all_processed if p.get("concept") in NUMBERED_CONCEPTS)
    logger.info(
        f"=== 파이프라인 완료: 발굴 {len(all_videos)}개, "
        f"처리 {len(all_processed)}개 (말하기 {talking_count} + 자막 {numbered_count}) ==="
    )


if __name__ == "__main__":
    main()
