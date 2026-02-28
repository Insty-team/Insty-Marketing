"""키워드 갱신: 페르소나 기반 생성 → YouTube 검증 → 저장."""

import argparse
import logging

from src.keyword_generator import generate_keywords
from src.keyword_validator import validate_keywords, save_keywords

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="키워드 갱신 (월 1회 수동 실행 권장)")
    parser.add_argument("--count", "-n", type=int, default=100,
                        help="생성할 키워드 후보 수")
    parser.add_argument("--skip-validation", action="store_true",
                        help="YouTube 검증 건너뜀 (API quota 절약)")
    args = parser.parse_args()

    # 1. 키워드 후보 생성
    logger.info(f"키워드 {args.count}개 후보 생성 중...")
    candidates = generate_keywords(count=args.count)

    if not candidates:
        logger.error("키워드 생성 실패")
        return

    total = sum(len(v) for v in candidates.values())
    logger.info(f"후보 {total}개 생성 완료")

    # 2. YouTube 검증
    if args.skip_validation:
        logger.info("YouTube 검증 건너뜀 (--skip-validation)")
        validated = candidates
    else:
        logger.info("YouTube 검증 시작...")
        validated = validate_keywords(candidates)

    if not validated:
        logger.error("검증 통과 키워드 없음")
        return

    # 3. 저장
    save_keywords(validated)
    total_validated = sum(len(v) for v in validated.values())
    logger.info(f"완료: {total_validated}개 키워드 저장됨")


if __name__ == "__main__":
    main()
