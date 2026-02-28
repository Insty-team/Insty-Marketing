"""환경변수 로드 및 프로젝트 설정."""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")

# AI Backend: "gemini" (크론잡 자동) | "claude" (수동 실행)
AI_BACKEND = os.getenv("AI_BACKEND", "gemini")

# YouTube 검색 필터
YOUTUBE_FILTERS = {
    "min_views": 5_000,
    "min_duration_minutes": 4,
    "max_duration_minutes": 40,
    "max_age_days": 180,  # 최근 6개월
    "max_results_per_keyword": 10,
    "language": "en",
}

# 스코어링 가중치
SCORING_WEIGHTS = {
    "views": 0.4,
    "likes": 0.3,
    "comments": 0.2,
    "recency": 0.1,
}

# 키워드 검증 기준
KEYWORD_VALIDATION = {
    "min_results": 5,
    "min_avg_views": 3_000,
    "top_n_for_avg": 5,
}

# 출력 경로
OUTPUT_DIR = PROJECT_ROOT / "output"
CSV_DIR = OUTPUT_DIR / "csv"
LOG_DIR = OUTPUT_DIR / "logs"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
