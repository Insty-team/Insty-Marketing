# Insty Marketing Pipeline

YouTube 콘텐츠 발굴 → Instagram Reels 스크립트 자동 생성 파이프라인.

타겟 페르소나(AI-powered solopreneur)에 맞는 YouTube 영상을 자동으로 찾고,
자막을 추출한 뒤, AI(Gemini)로 Reels 스크립트를 생성하여 Notion DB + CSV에 저장합니다.

```
키워드 생성 (페르소나 → Gemini)
  → YouTube 검색 (Data API v3)
  → 필터링 + 스코어링 (조회수/좋아요/댓글/최신성)
  → 자막 추출 (youtube-transcript-api)
  → Reels 스크립트 생성 (Gemini 2.5 Flash)
  → Notion DB 저장 + CSV 백업
```

---

## 사전 준비

### 1. Docker Desktop 설치

| OS | 설치 방법 |
|---|---|
| **Windows** | [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 다운로드 → 설치 → 재부팅 |
| **Ubuntu** | `sudo apt install docker.io docker-compose-v2` |
| **Mac** | [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) |

> **Windows 참고**: Docker Desktop 설치 시 WSL 2 백엔드를 사용합니다.
> 설치 과정에서 WSL 2 활성화를 안내하면 그대로 따라하세요.

설치 확인:
```bash
docker --version        # Docker version 2x.x.x
docker compose version  # Docker Compose version v2.x.x
```

### 2. 프로젝트 클론

```bash
git clone https://github.com/Insty-team/Insty-Marketing.git
cd Insty-Marketing
```

### 3. API 키 발급 (모두 무료)

#### YouTube Data API Key
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
3. **API 및 서비스 → 라이브러리** → "YouTube Data API v3" 검색 → **사용 설정**
4. **API 및 서비스 → 사용자 인증 정보** → **사용자 인증 정보 만들기 → API 키**
5. 생성된 키 복사

> 무료 할당량: 일 10,000 units. 파이프라인 1회 실행 ≈ 300 units.

#### Gemini API Key
1. [Google AI Studio](https://aistudio.google.com/apikey) 접속
2. **API 키 만들기** 클릭
3. 생성된 키 복사

> 무료 할당량: Gemini 2.5 Flash 기준 일 500 RPD.

#### Notion Integration Token
1. [Notion Integrations](https://www.notion.so/my-integrations) 접속
2. **새 통합 만들기** → 이름 입력 → 워크스페이스 선택 → **제출**
3. **내부 통합 시크릿** 복사
4. **(중요)** Notion에서 Content Pipeline DB 페이지 열기 → 우측 상단 `···` → **연결** → 만든 통합 추가

### 4. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Linux / Mac:**
```bash
cp .env.example .env
nano .env
```

`.env` 내용:
```env
YOUTUBE_API_KEY=발급받은_YouTube_API_키
GEMINI_API_KEY=발급받은_Gemini_API_키
NOTION_TOKEN=발급받은_Notion_Integration_Token
NOTION_DB_ID=Notion_DB_ID
AI_BACKEND=gemini
```

> `NOTION_DB_ID`는 Notion DB URL에서 추출합니다.
> `https://notion.so/xxxxx?v=...` → `xxxxx` 부분 (32자리 hex)

---

## 실행 방법 (Docker — Windows/Ubuntu/Mac 공통)

### 이미지 빌드 (최초 1회, 코드 변경 시)

```bash
docker compose build
```

### 수동 실행

```bash
# 전체 파이프라인 (발굴 → 자막 → 스크립트 → 저장)
docker compose run --rm pipeline manual

# 콘셉트 지정
docker compose run --rm pipeline manual --concept tutorial
docker compose run --rm pipeline manual --concept numbered_tips
docker compose run --rm pipeline manual --concept numbered_lessons

# 카테고리 지정 + 최대 영상 수
docker compose run --rm pipeline manual --category ai_tools --max-videos 3

# 주간 10개 모드 (talking head 5개 + numbered 5개)
docker compose run --rm pipeline weekly
```

### 단일 스텝 실행

```bash
docker compose run --rm pipeline discovery   # 영상 발굴만
docker compose run --rm pipeline keywords    # 키워드 갱신
```

### 자동 실행 (크론 모드 — 켜두면 자동으로 돌아감)

```bash
# 백그라운드 시작 (월/수/금 09:00 KST 자동 실행)
docker compose up -d

# 실행 상태 확인
docker compose ps

# 로그 실시간 확인
docker compose logs -f

# 중지
docker compose down
```

### 결과물 확인

실행 결과는 `output/` 폴더에 저장됩니다 (Docker 볼륨으로 호스트와 공유):

```
output/
  csv/    ← 발굴/처리 결과 CSV (날짜별)
  logs/   ← 실행 로그
```

Notion DB에도 자동 저장됩니다 (integration 연결 필수).

---

## 실행 방법 (로컬 Python — Docker 없이)

Docker 없이 Python으로 직접 실행할 수도 있습니다.

```bash
# Python 3.10+ 필요
pip install -r requirements.txt

# 키워드 생성 (최초 1회)
python -m scripts.run_keyword_refresh

# 전체 파이프라인
python -m scripts.run_pipeline

# 콘셉트 지정
python -m scripts.run_pipeline --concept numbered_tips

# 주간 10개 모드
python -m scripts.run_pipeline --mode all

# 영상 발굴만
python -m scripts.run_discovery

# 특정 영상 스크립트 생성
python -m scripts.run_script_gen "https://www.youtube.com/watch?v=VIDEO_ID"
```

> Windows에서는 `python3` 대신 `python`을 사용합니다.

---

## 스크립트 콘셉트

### Talking Head (직접 말하기)
| 콘셉트 | 구조 | 용도 |
|---|---|---|
| `tutorial` | Hook → Why → How → Summary → CTA | 도구 튜토리얼, 가이드 |
| `tips` | Hook → Why → Tip1 → Tip2 → Tip3 → CTA | 팁 모음, 비교 |
| `celebrity` | Hook → Why → Lesson → Application → CTA | 인터뷰, 강연 |

### Numbered (자막 + B-roll + 음악)
| 콘셉트 | 구조 | 용도 |
|---|---|---|
| `numbered_tips` | Hook → 4-7 numbered items → CTA | 도구 비교, 꿀팁 |
| `numbered_lessons` | Hook → 3-5 numbered lessons → CTA | 유명인 인사이트 |

> **Numbered 포맷**: 말하기 없이 텍스트 오버레이 + 작업/이동 B-roll + 배경 음악으로 제작.
> 촬영 시간 대폭 절약!

---

## 파이프라인 모드

| 모드 | Docker 명령 | 설명 |
|---|---|---|
| 단일 콘셉트 | `manual --concept tutorial` | 1개 콘셉트로만 생성 |
| talking | `manual --mode talking` | talking head 3종으로 생성 |
| numbered | `manual --mode numbered` | numbered 2종으로 생성 |
| 전체 (주간) | `weekly` | 5종 콘셉트 모두 (주 10개 목표) |

---

## 프로젝트 구조

```
config/
  settings.py                  — 환경변수, 필터 설정, 스코어링 가중치
  keywords.py                  — 검증된 검색 키워드 (카테고리별)
src/
  youtube_discovery.py         — YouTube API 검색 + 필터링 + 스코어링
  transcript_extractor.py      — 자막 추출 (타임스탬프 포함)
  keyword_generator.py         — 페르소나 기반 키워드 자동 생성 (Gemini)
  keyword_validator.py         — 키워드 YouTube 검증
  script_generator.py          — Reels 스크립트 생성 (Gemini)
  notion_writer.py             — Notion DB 저장 + 중복 체크
  csv_backup.py                — CSV 백업
scripts/
  run_pipeline.py              — 전체 파이프라인
  run_discovery.py             — 영상 발굴 단독 실행
  run_script_gen.py            — 스크립트 생성 단독 실행
  run_keyword_refresh.py       — 키워드 갱신
  entrypoint.sh                — Docker 엔트리포인트
prompts/
  reels_tutorial.txt           — 튜토리얼 (talking head)
  reels_tips.txt               — 팁 리스트 (talking head)
  reels_celebrity.txt          — 유명인 레슨 (talking head)
  reels_numbered_tips.txt      — 넘버링 팁 (자막 + 음악)
  reels_numbered_lessons.txt   — 넘버링 레슨 (자막 + 음악)
output/
  csv/                         — CSV 백업
  logs/                        — 실행 로그
```

## 필터링 기준

- 조회수 ≥ 5,000
- 영상 길이 4~40분
- 최근 6개월 이내
- 스코어링: 조회수 40% + 좋아요 30% + 댓글 20% + 최신성 10%

## 월 운영 비용

| 항목 | 비용 |
|---|---|
| YouTube Data API | $0 (일 10,000 units 무료) |
| youtube-transcript-api | $0 |
| Gemini API | $0 (무료 tier) |
| Notion API | $0 |
| **합계** | **$0/월** |

## 테스트

```bash
# Docker
docker compose run --rm pipeline pytest tests/ -v

# 로컬
python -m pytest tests/ -v
```

## 트러블슈팅

### Windows에서 `docker compose` 명령어가 안 됨
- Docker Desktop이 실행 중인지 확인 (시스템 트레이에 Docker 아이콘)
- PowerShell 또는 CMD를 **관리자 권한**으로 실행
- `docker compose` 대신 `docker-compose` (하이픈)도 시도

### Gemini rate limit (429 에러)
- 무료 tier 일일 한도 초과. 24시간 후 자동 리셋
- 파이프라인에 자동 재시도 로직 내장 (3회, 25초 간격)

### Notion 저장 실패 (404 에러)
- Notion DB를 integration에 공유했는지 확인
- DB 페이지 → 우측 상단 `···` → **연결** → 만든 통합 선택

### Windows에서 `python` 명령어가 안 됨 (로컬 실행 시)
- [Python 공식 사이트](https://www.python.org/downloads/)에서 3.10+ 설치
- 설치 시 **"Add Python to PATH"** 체크 필수
- PowerShell 재시작 후 `python --version` 확인
