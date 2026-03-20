"""Phase 2: 자막 추출 + Reels 스크립트 생성."""

import argparse
import json
import logging

from src.transcript_extractor import extract_transcript
from src.script_generator import generate_reels_script
from src.notion_writer import save_video, update_status
from src.csv_backup import save_to_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def process_video(
    video_url: str,
    concept: str = "tutorial",
    backend: str = None,
    save_notion: bool = True,
) -> dict | None:
    """단일 영상에 대해 자막 추출 → 스크립트 생성.

    Args:
        video_url: YouTube 영상 URL 또는 video_id
        concept: tutorial | tips | celebrity
        backend: gemini | claude
        save_notion: Notion 저장 여부
    """
    # video_id 추출
    video_id = video_url
    if "youtube.com" in video_url or "youtu.be" in video_url:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]

    logger.info(f"처리 시작: {video_id} (콘셉트: {concept})")

    # 1. 자막 추출
    transcript = extract_transcript(video_id)
    if not transcript:
        logger.error(f"자막 추출 실패: {video_id}")
        return None

    logger.info(f"자막 추출 완료: {len(transcript)}자")

    # 2. 스크립트 생성
    script = generate_reels_script(
        transcript=transcript,
        video_title=video_id,  # TODO: 실제 제목 가져오기
        video_url=f"https://www.youtube.com/watch?v={video_id}",
        concept=concept,
        backend=backend,
    )

    if script:
        logger.info("스크립트 생성 완료:")
        logger.info(json.dumps(script, ensure_ascii=False, indent=2))

    return script


def main():
    parser = argparse.ArgumentParser(description="자막 추출 + Reels 스크립트 생성")
    parser.add_argument("video_url", help="YouTube 영상 URL 또는 video_id")
    parser.add_argument("--concept", "-c", default="tutorial",
                        choices=["tutorial", "tips", "celebrity"])
    parser.add_argument("--backend", "-b", choices=["gemini", "claude"])
    parser.add_argument("--no-notion", action="store_true")
    args = parser.parse_args()

    result = process_video(
        video_url=args.video_url,
        concept=args.concept,
        backend=args.backend,
        save_notion=not args.no_notion,
    )

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
