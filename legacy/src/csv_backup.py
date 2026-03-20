"""CSV 백업 — 날짜별 파일로 저장."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import CSV_DIR

logger = logging.getLogger(__name__)


def save_to_csv(
    videos: list[dict],
    prefix: str = "discovery",
    extra_fields: Optional[dict] = None,
) -> Path:
    """영상 리스트를 CSV로 백업.

    Args:
        videos: 영상 딕셔너리 리스트
        prefix: 파일명 접두어
        extra_fields: 각 영상에 추가할 필드

    Returns:
        저장된 파일 경로
    """
    if not videos:
        logger.info("저장할 영상 없음 — CSV 건너뜀")
        return CSV_DIR

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = CSV_DIR / f"{prefix}_{date_str}.csv"

    # 필드명 수집
    fieldnames = list(videos[0].keys())
    if extra_fields:
        fieldnames.extend(k for k in extra_fields if k not in fieldnames)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for video in videos:
            row = {**video}
            if extra_fields:
                row.update(extra_fields)
            writer.writerow(row)

    logger.info(f"CSV 저장: {filepath} ({len(videos)}건)")
    return filepath
