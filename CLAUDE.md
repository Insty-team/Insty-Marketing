# Insty Marketing - Claude Code 프로젝트 가이드

## 프로젝트 개요
- **Insty**: AI powered solo preneur를 위한 정보 공유 플랫폼 & 커뮤니티
- **슬로건**: "Solve your problem with the right AI service."
- **상세 BM**: `docs/what_is_insty.md` 참조

## 프로젝트 지식 (docs/)
> 새 세션 시작 시 필요한 문서를 `docs/`에서 Read로 로드할 것.
> 프로젝트 지식은 반드시 `docs/`에 저장 (git 동기화 대상).

- `docs/what_is_insty.md` — BM v2.1 핵심 (수익 모델, 가설, 전략)
- `docs/decisions.md` — 기술 결정 기록 (ADR 스타일)
- `docs/debugging.md` — 반복 문제와 해결책
- `docs/progress.md` — 진행 중 작업 / 브랜치 상태
- `docs/mcp-setup.md` — MCP 서버 설정 가이드 (머신 세팅 시 참조)

## 해야 할 것 (Do)
- 한국어 응답 (코드/기술 용어는 영어)
- Conventional Commits 사용 (feat/fix/test/chore/docs)
- main 직접 커밋 금지 → 브랜치 생성 후 PR
- 서브 에이전트 사용 전 반드시 TodoWrite로 계획
- 코드 변경 시 테스트 실행
- 프로젝트 지식 추가/변경 시 `docs/`에 기록

## 하면 안 되는 것 (Don't)
- 테스트 없이 PR 생성 금지
- 유저 확인 없이 파일 삭제 금지

## 서브 에이전트 규칙
- **Explore**: 코드베이스 탐색에만 사용
- **Plan**: 3개 이상 파일 수정 시 먼저 사용
- **general-purpose**: 웹 리서치에만 사용

## 컨텍스트 유지 전략 (Auto-Compact 대응)

> 대화가 길어지면 auto-compact가 발생하여 이전 맥락이 압축된다.
> 아래 규칙을 따라 기억상실을 방지할 것.

### 작업 중 (Compact 전)
1. **TodoWrite 항상 최신 유지** — 현재 진행 중인 작업이 Todo에 반영되어야 함
2. **중요한 결정/발견 즉시 기록** — `docs/decisions.md` 또는 `docs/debugging.md`에 저장
3. **작업 진행 상황 기록** — 큰 작업 완료 시 `docs/progress.md` 업데이트

### Compact 발생 후 (맥락이 불확실할 때)
compact 후 맥락이 불분명하면 **반드시 아래 순서로 복구**:
1. `docs/progress.md` Read → 현재 무슨 작업 중이었는지 파악
2. `git status` + `git diff` → 변경된 파일 확인
3. `git log --oneline -10` → 최근 커밋 히스토리 확인
4. TodoWrite 확인 → 남은 작업 파악
5. 필요시 `docs/` 내 관련 문서 Read

### PreCompact Hook (자동)
- `.claude/hooks/pre-compact.sh`가 compact 직전에 핸드오버 문서를 자동 생성
- 저장 위치: `~/.claude/projects/.../memory/handovers/`
- SessionStart Hook이 다음 세션에서 자동 로드

### 절대 하지 말 것
- compact 후 이전 맥락을 **추측하지 말 것** — 반드시 파일에서 확인
- 진행 중이던 작업을 **처음부터 다시 시작하지 말 것** — 기존 변경사항 먼저 확인
- 유저에게 "이전 대화 내용을 기억하지 못합니다" 같은 말 하지 말 것 — 위 복구 절차를 조용히 수행

## 기술 스택
- Python 3.10+
- YouTube Data API v3 (`google-api-python-client`)
- `youtube-transcript-api` (자막 추출, 무료)
- Gemini API (`google-generativeai`) — 크론잡 무료 tier
- Notion SDK (`notion-client`) — DB 저장
- Docker — 컨테이너화 실행

## 디렉토리 구조
```
config/         — 설정 (settings.py, keywords.py)
src/            — 핵심 모듈 (discovery, transcript, script_gen, notion, csv)
prompts/        — Reels 스크립트 프롬프트 (tutorial, tips, celebrity)
scripts/        — 실행 스크립트 (run_pipeline, run_discovery, run_script_gen)
output/csv/     — CSV 백업 (gitignore)
output/logs/    — 실행 로그 (gitignore)
tests/          — 테스트
docs/           — 프로젝트 지식 (git 동기화)
.claude/        — Claude Code 설정 (hooks, settings)
```

## Docker 실행 방법
```bash
# 빌드 + 크론 모드 (백그라운드)
docker compose up -d

# 수동 파이프라인 실행
docker compose run pipeline manual

# 개별 단계 실행
docker compose run pipeline discovery
docker compose run pipeline script
docker compose run pipeline keywords
```
