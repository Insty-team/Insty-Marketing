"""콘텐츠 실험 파이프라인 (일일 자동 실행).

매일 아침 자동 실행되어 Notion에 "오늘 찍을 콘텐츠" 가이드를 생성한다.

Flow:
  1. [구조 레퍼런스] YouTube Shorts 고성과 영상 발견 → 포맷/구성 분석
  2. [내용 소싱] 인기 긴 영상 발견 (기존 파이프라인 활용) → 핵심 내용 추출
  3. [결합] 좋은 내용 + 검증된 구조 = 프로덕션 가이드 생성
  4. Notion DB 저장

Usage:
  python -m scripts.run_experiment_pipeline                  # 전체 파이프라인
  python -m scripts.run_experiment_pipeline --discover-only   # 레퍼런스 발견만
  python -m scripts.run_experiment_pipeline --track-only      # 성과 추적만
  python -m scripts.run_experiment_pipeline --dry-run         # 저장 없이 테스트
"""

import argparse
import json
import logging
import time
from datetime import datetime

from config.experiment_config import (
    DAILY_GUIDE_TARGET,
    DAILY_REFERENCE_TARGET,
    EXPERIMENT_LOG_DIR,
    EXPERIMENT_OUTPUT_DIR,
    KEYWORDS_PER_DAY,
    REFERENCE_KEYWORDS,
)
from config.keywords import get_categories, get_keywords_by_category
from src.shorts_discovery import search_shorts
from src.youtube_discovery import search_videos
from src.transcript_extractor import extract_transcript
from src.reference_analyzer import analyze_reference
from src.production_guide_generator import generate_production_guide
from src.notion_experiment_writer import save_reference, save_production_guide

EXPERIMENT_LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            EXPERIMENT_LOG_DIR / f"experiment_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


def _select_ref_keywords() -> list[str]:
    """쇼츠 레퍼런스용 키워드 로테이션."""
    day_index = datetime.now().timetuple().tm_yday
    n = len(REFERENCE_KEYWORDS)
    start = (day_index * KEYWORDS_PER_DAY) % n
    return [REFERENCE_KEYWORDS[(start + i) % n] for i in range(KEYWORDS_PER_DAY)]


def _select_content_keywords() -> list[str]:
    """콘텐츠 소싱용 키워드 (기존 keywords.py에서 카테고리 로테이션)."""
    categories = get_categories()
    if not categories:
        return []
    day_index = datetime.now().timetuple().tm_yday % len(categories)
    category = categories[day_index]
    keywords = get_keywords_by_category(category)
    logger.info(f"콘텐츠 소싱 카테고리: {category}")
    return keywords[:3]


# ============================================================
# Step 1: 구조 레퍼런스 발견 + 분석
# ============================================================

def step_discover_references(keywords: list[str]) -> list[dict]:
    """고성과 쇼츠를 찾아서 구조를 분석한다."""
    logger.info(f"=== Step 1: 구조 레퍼런스 발견 (키워드 {len(keywords)}개) ===")

    all_shorts = []
    for kw in keywords:
        shorts = search_shorts(kw)
        all_shorts.extend(shorts)
        logger.info(f"  [Shorts:{kw}] → {len(shorts)}개")

    # 중복 제거 + 상위 선정
    seen = set()
    unique = []
    for s in all_shorts:
        if s["video_id"] not in seen:
            seen.add(s["video_id"])
            unique.append(s)
    unique.sort(key=lambda x: x["score"], reverse=True)
    top = unique[:DAILY_REFERENCE_TARGET]

    logger.info(f"총 {len(all_shorts)}개 → 중복 제거 {len(unique)}개 → 상위 {len(top)}개")
    return top


def step_analyze_references(
    references: list[dict], dry_run: bool = False
) -> list[dict]:
    """레퍼런스 쇼츠의 구조를 분석한다."""
    logger.info(f"=== Step 1b: 구조 분석 ({len(references)}개) ===")

    analyzed = []
    for ref in references:
        transcript = extract_transcript(ref["video_id"])
        if not transcript:
            logger.warning(f"자막 없음: {ref['video_id']} — {ref['title'][:40]}")
            continue

        analysis = analyze_reference(transcript, ref)
        if not analysis:
            logger.warning(f"분석 실패: {ref['video_id']}")
            continue

        ref["transcript"] = transcript
        ref["analysis"] = analysis

        if not dry_run:
            page_id = save_reference(ref, analysis)
            ref["notion_page_id"] = page_id

        analyzed.append(ref)
        logger.info(
            f"  레퍼런스: {ref['title'][:40]} "
            f"(hook={analysis.get('hook_type')}, format={analysis.get('video_format')})"
        )
        time.sleep(4)

    logger.info(f"구조 분석 완료: {len(analyzed)}/{len(references)}개")
    return analyzed


# ============================================================
# Step 2: 콘텐츠 소싱 (인기 긴 영상에서 내용 추출)
# ============================================================

def step_discover_content(keywords: list[str], max_videos: int = 5) -> list[dict]:
    """기존 파이프라인을 활용해 인기 긴 영상을 발견하고 자막을 추출한다."""
    logger.info(f"=== Step 2: 콘텐츠 소싱 (키워드 {len(keywords)}개) ===")

    all_videos = []
    for kw in keywords:
        videos = search_videos(kw, max_results=max_videos)
        all_videos.extend(videos)
        logger.info(f"  [Content:{kw}] → {len(videos)}개")

    # 중복 제거 + 스코어 정렬
    seen = set()
    unique = []
    for v in all_videos:
        if v["video_id"] not in seen:
            seen.add(v["video_id"])
            unique.append(v)
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 자막 추출
    with_transcript = []
    for video in unique[:max_videos]:
        transcript = extract_transcript(video["video_id"])
        if transcript:
            video["transcript"] = transcript
            with_transcript.append(video)
            logger.info(f"  자막 추출: {video['title'][:50]}")
        else:
            logger.warning(f"  자막 없음: {video['title'][:50]}")

    logger.info(f"콘텐츠 소싱 완료: {len(with_transcript)}개 (자막 있음)")
    return with_transcript


# ============================================================
# Step 3: 구조 + 내용 결합 → 프로덕션 가이드
# ============================================================

def step_generate_guides(
    analyzed_refs: list[dict],
    content_sources: list[dict],
    dry_run: bool = False,
    max_guides: int = DAILY_GUIDE_TARGET,
) -> list[dict]:
    """레퍼런스 구조 + 소스 콘텐츠를 결합하여 가이드를 생성한다.

    레퍼런스와 소스를 1:1 매칭하여 가이드를 만든다.
    replicability_score 높은 레퍼런스 순으로 사용.
    """
    logger.info(f"=== Step 3: 가이드 생성 (목표 {max_guides}개) ===")

    # replicability_score 높은 순 정렬
    sorted_refs = sorted(
        analyzed_refs,
        key=lambda x: x.get("analysis", {}).get("replicability_score", 0),
        reverse=True,
    )

    guides = []
    for i, ref in enumerate(sorted_refs):
        if len(guides) >= max_guides:
            break
        if i >= len(content_sources):
            break

        source = content_sources[i]
        analysis = ref.get("analysis", {})

        logger.info(
            f"  결합: [구조] {ref['title'][:30]} + [내용] {source['title'][:30]}"
        )

        guide = generate_production_guide(
            source_transcript=source["transcript"],
            source_metadata=source,
            reference_analysis=analysis,
        )

        if not guide:
            logger.warning(f"  가이드 생성 실패")
            continue

        guide["reference_url"] = ref.get("url", "")
        guide["reference_title"] = ref.get("title", "")
        guide["source_url"] = source.get("url", "")
        guide["source_title"] = source.get("title", "")

        if not dry_run:
            page_id = save_production_guide(guide, source, ref)
            guide["notion_page_id"] = page_id

        guides.append(guide)
        logger.info(f"  → 가이드: {guide.get('title_en', '?')}")
        time.sleep(4)

    logger.info(f"가이드 생성 완료: {len(guides)}개")
    return guides


# ============================================================
# 백업 + 메인
# ============================================================

def _save_local_backup(references: list[dict], sources: list[dict], guides: list[dict]):
    """로컬 JSON 백업."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    ref_data = [{k: v for k, v in r.items() if k != "transcript"} for r in references]
    ref_path = EXPERIMENT_OUTPUT_DIR / f"references_{ts}.json"
    with open(ref_path, "w", encoding="utf-8") as f:
        json.dump(ref_data, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"레퍼런스 백업: {ref_path} ({len(ref_data)}건)")

    if guides:
        guide_path = EXPERIMENT_OUTPUT_DIR / f"guides_{ts}.json"
        with open(guide_path, "w", encoding="utf-8") as f:
            json.dump(guides, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"가이드 백업: {guide_path} ({len(guides)}건)")


def main():
    parser = argparse.ArgumentParser(description="콘텐츠 실험 파이프라인")
    parser.add_argument("--discover-only", action="store_true",
                        help="레퍼런스 발견만 실행")
    parser.add_argument("--track-only", action="store_true",
                        help="성과 추적만 실행")
    parser.add_argument("--dry-run", action="store_true",
                        help="Notion 저장 없이 테스트")
    parser.add_argument("--ref-keywords", nargs="+",
                        help="레퍼런스 검색 키워드 직접 지정")
    parser.add_argument("--content-keywords", nargs="+",
                        help="콘텐츠 소싱 키워드 직접 지정")
    parser.add_argument("--max-refs", type=int, default=DAILY_REFERENCE_TARGET,
                        help="분석할 레퍼런스 최대 수")
    parser.add_argument("--max-guides", type=int, default=DAILY_GUIDE_TARGET,
                        help="생성할 가이드 최대 수")
    args = parser.parse_args()

    logger.info("=== 콘텐츠 실험 파이프라인 시작 ===")

    if args.track_only:
        logger.info("성과 추적 모드 (Phase F에서 구현 예정)")
        return

    # Step 1: 구조 레퍼런스 발견 + 분석
    ref_keywords = args.ref_keywords or _select_ref_keywords()
    logger.info(f"레퍼런스 키워드: {ref_keywords}")

    references = step_discover_references(ref_keywords)
    if not references:
        logger.warning("레퍼런스 발견 실패 — 파이프라인 종료")
        return

    if args.discover_only:
        _save_local_backup(references, [], [])
        logger.info("레퍼런스 발견 완료 (discover-only)")
        return

    analyzed_refs = step_analyze_references(
        references[:args.max_refs], dry_run=args.dry_run
    )
    if not analyzed_refs:
        logger.warning("분석 가능한 레퍼런스 없음 — 파이프라인 종료")
        _save_local_backup(references, [], [])
        return

    # Step 2: 콘텐츠 소싱 (인기 긴 영상에서)
    content_keywords = args.content_keywords or _select_content_keywords()
    logger.info(f"콘텐츠 키워드: {content_keywords}")

    content_sources = step_discover_content(
        content_keywords, max_videos=args.max_guides + 2
    )
    if not content_sources:
        logger.warning("콘텐츠 소싱 실패 — 파이프라인 종료")
        _save_local_backup(analyzed_refs, [], [])
        return

    # Step 3: 구조 + 내용 결합 → 가이드 생성
    guides = step_generate_guides(
        analyzed_refs, content_sources,
        dry_run=args.dry_run, max_guides=args.max_guides,
    )

    _save_local_backup(analyzed_refs, content_sources, guides)

    logger.info(
        f"=== 파이프라인 완료: "
        f"레퍼런스 {len(analyzed_refs)}개, "
        f"콘텐츠 {len(content_sources)}개, "
        f"가이드 {len(guides)}개 ==="
    )


if __name__ == "__main__":
    main()
