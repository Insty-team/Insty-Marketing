# Insty Marketing Pipeline

YouTube 콘텐츠 발굴 → Instagram Reels 스크립트 자동 생성 파이프라인.

Insty 타겟 페르소나(AI-powered solopreneur)에 맞는 YouTube 영상을 자동으로 찾고,
자막을 추출한 뒤, AI로 Reels 스크립트를 생성하여 Notion DB에 저장합니다.

## 파이프라인 흐름

```
키워드 생성 (페르소나 → Gemini)
  → YouTube 검색 (Data API v3)
  → 필터링 + 스코어링
  → 자막 추출 (youtube-transcript-api)
  → Reels 스크립트 생성 (Gemini)
  → Notion DB 저장 + CSV 백업
```

## 빠른 시작

### 1. 환경 설정

```bash
# 클론
git clone https://github.com/Insty-team/Insty-Marketing.git
cd Insty-Marketing

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력 (아래 참조)
```

### 2. API 키 발급

| 키 | 발급 위치 | 용도 |
|---|---|---|
| `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) → YouTube Data API v3 사용 설정 → 사용자 인증 정보 → API 키 | YouTube 영상 검색 |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) → API 키 만들기 | AI 스크립트 생성 |
| `NOTION_TOKEN` | [Notion Integrations](https://www.notion.so/my-integrations) → 새 통합 만들기 | Notion DB 저장 |

### 3. 실행

```bash
# 키워드 생성 (최초 1회 또는 월 1회)
python3 -m scripts.run_keyword_refresh

# 영상 발굴만
python3 -m scripts.run_discovery

# 특정 영상 스크립트 생성
python3 -m scripts.run_script_gen "https://www.youtube.com/watch?v=VIDEO_ID"

# 전체 파이프라인 (발굴 → 자막 → 스크립트 → 저장)
python3 -m scripts.run_pipeline
```

### 4. Docker로 실행

```bash
# .env 파일 준비 후
docker compose up -d          # 크론 모드 (주 3회 자동 실행)
docker compose run pipeline manual     # 수동 전체 실행
docker compose run pipeline discovery  # 발굴만
docker compose run pipeline keywords   # 키워드 갱신
```

## 프로젝트 구조

```
config/
  settings.py       — 환경변수, 필터 설정, 스코어링 가중치
  keywords.py       — 검증된 검색 키워드 (카테고리별)
src/
  youtube_discovery.py    — YouTube API 검색 + 필터링 + 스코어링
  transcript_extractor.py — 자막 추출 (타임스탬프 포함)
  keyword_generator.py    — 페르소나 기반 키워드 자동 생성 (Gemini)
  keyword_validator.py    — 키워드 YouTube 검증 (검색 결과 수, 평균 조회수)
  script_generator.py     — Reels 스크립트 생성 (Gemini)
  notion_writer.py        — Notion DB 저장 + 중복 체크
  csv_backup.py           — CSV 백업
scripts/
  run_pipeline.py         — 전체 파이프라인 (크론잡용)
  run_discovery.py        — 영상 발굴 단독 실행
  run_script_gen.py       — 스크립트 생성 단독 실행
  run_keyword_refresh.py  — 키워드 갱신
prompts/
  reels_tutorial.txt      — 튜토리얼 콘셉트 프롬프트
  reels_tips.txt          — 팁 리스트 콘셉트 프롬프트
  reels_celebrity.txt     — 유명인 레슨 콘셉트 프롬프트
output/
  csv/                    — CSV 백업 (gitignore)
  logs/                   — 실행 로그 (gitignore)
docs/                     — 프로젝트 지식 (BM, 의사결정 기록 등)
tests/                    — 테스트
```

## 스크립트 콘셉트

| 콘셉트 | 프롬프트 | 구조 | 적합한 영상 |
|---|---|---|---|
| `tutorial` | `reels_tutorial.txt` | Hook → Why → How → Summary → CTA | 도구 튜토리얼, 가이드 |
| `tips` | `reels_tips.txt` | Hook → Why → Tip1 → Tip2 → Tip3 → CTA | 팁 모음, 비교 영상 |
| `celebrity` | `reels_celebrity.txt` | Hook → Why → Lesson → Application → CTA | 인터뷰, 강연 |

## 필터링 기준

- 조회수 ≥ 5,000
- 영상 길이 4~40분
- 최근 6개월 이내
- 스코어링: 조회수 40% + 좋아요 30% + 댓글 20% + 최신성 10%

## 비용

| 항목 | 비용 |
|---|---|
| YouTube Data API | $0 (일 10,000 units 무료) |
| youtube-transcript-api | $0 |
| Gemini API | $0 (무료 tier) |
| Notion API | $0 |
| **합계** | **$0/월** |

## 테스트

```bash
python3 -m pytest tests/ -v
```
