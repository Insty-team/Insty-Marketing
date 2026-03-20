"""콘텐츠 실험 파이프라인 설정."""

import os
from config.settings import PROJECT_ROOT

# === Notion DB IDs (실험 파이프라인 전용) ===
NOTION_REFERENCE_DB_ID = os.getenv("NOTION_REFERENCE_DB_ID", "")
NOTION_GUIDE_DB_ID = os.getenv("NOTION_GUIDE_DB_ID", "")

# === YouTube Shorts 검색 필터 ===
SHORTS_FILTERS = {
    "max_duration_seconds": 60,
    "min_views": 5_000,  # 니치 faceless 쇼츠도 포함
    "max_age_days": 30,  # 최근 1개월 (트렌드 반영)
    "max_results_per_keyword": 15,
    "language": "en",
}

# === Shorts 스코어링 가중치 ===
# 쇼츠는 engagement ratio가 raw views보다 중요
SHORTS_SCORING_WEIGHTS = {
    "engagement_ratio": 0.4,  # (likes + comments) / views
    "views": 0.3,
    "recency": 0.2,
    "comment_ratio": 0.1,  # comments / views (토론 유발)
}

# === 레퍼런스 검색 키워드 (쇼츠 전용) ===
# Faceless 쇼츠 포맷 우선 — 촬영 없이 편집만으로 제작 가능한 레퍼런스
REFERENCE_KEYWORDS = [
    # Faceless 포맷 (촬영 없이 제작)
    "AI tools faceless shorts",
    "faceless youtube shorts AI",
    "AI tips text overlay shorts",
    "make money AI no face",
    "AI automation tips shorts",
    # 편집 중심 교육 쇼츠
    "AI tutorial screen recording shorts",
    "ChatGPT hack shorts",
    "AI business tips shorts",
    "solopreneur AI shorts",
    # 잘 터지는 포맷 벤치마크
    "viral AI shorts 2026",
    "AI tool demo shorts",
    "side hustle AI shorts",
]

# === 일일 파이프라인 설정 ===
DAILY_REFERENCE_TARGET = 10  # 일일 분석할 레퍼런스 수
DAILY_GUIDE_TARGET = 3  # 일일 생성할 프로덕션 가이드 수
KEYWORDS_PER_DAY = 5  # 일일 검색 키워드 수 (로테이션)

# === 성과 추적 ===
TRACKING_INTERVALS_HOURS = [24, 48, 168]  # 24h, 48h, 7d

# === 출력 경로 ===
EXPERIMENT_OUTPUT_DIR = PROJECT_ROOT / "output" / "experiment"
EXPERIMENT_LOG_DIR = PROJECT_ROOT / "output" / "logs"
