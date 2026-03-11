# 진행 상황
> 진행 중인 기능/작업 추적. git에 포함되어 멀티 머신 동기화.

## 현재 상태
- **프로젝트 단계**: Phase 1 — 파이프라인 대행 서비스
- **마지막 업데이트**: 2026-03-09

## 활성 작업

### Phase 1: AI 세일즈 파이프라인 구축 서비스
- **상태**: 계획 완료, 내일(3/10) 실행 시작
- **시작일**: 2026-03-10
- **목표**: 4주 안에 첫 매출 발생 (서버비 충당)
- **관련 파일**:
  - `pipeline/strategy/phase1-plan.md` — 전체 전략
  - `pipeline/team-sales/playbook.md` — 세일즈 플레이북
  - `pipeline/team-content/playbook.md` — 콘텐츠 플레이북
  - `pipeline/team-research/playbook.md` — 리서치 플레이북
  - `pipeline/team-delivery/playbook.md` — 딜리버리 플레이북
- **내일(3/10) 할 일**:
  - [ ] 오퍼 원페이지 작성
  - [ ] ICP 리서치 실행
  - [ ] DM 템플릿 3종 작성
  - [ ] 빌드인퍼블릭 첫 포스트
  - [ ] 타겟 리스트 작성 시작

### 콘텐츠 실험 파이프라인 (브랜치: feat/content-experiment-pipeline)
- **상태**: 코드 구현 완료, Notion DB 생성 + .env 설정 필요
- **시작일**: 2026-03-10
- **목표**: 매일 아침 자동으로 고성과 쇼츠 분석 → 촬영 가이드 3개 Notion에 생성
- **관련 파일**:
  - `config/experiment_config.py` — 실험 파이프라인 설정
  - `src/shorts_discovery.py` — YouTube Shorts 고성과 레퍼런스 발견
  - `src/reference_analyzer.py` — 레퍼런스 구조 분석 (Gemini)
  - `src/production_guide_generator.py` — 촬영/편집 가이드 생성
  - `src/notion_experiment_writer.py` — Notion DB 연동 (레퍼런스 + 가이드)
  - `src/performance_tracker.py` — 성과 추적 + 패턴 분석
  - `src/ig_reference_collector.py` — IG 수동 수집 + Graph API
  - `scripts/run_experiment_pipeline.py` — 일일 자동 파이프라인
  - `scripts/run_reference.py` — 수동 URL 분석
  - `scripts/run_performance_check.py` — 성과 체크
- **남은 작업**:
  - [ ] Notion에 References DB, Production Guides DB 생성
  - [ ] `.env`에 `NOTION_REFERENCE_DB_ID`, `NOTION_GUIDE_DB_ID` 추가
  - [ ] (선택) `.env`에 `IG_ACCESS_TOKEN`, `IG_USER_ID` 추가
  - [ ] dry-run 테스트 후 PR 머지

## 완료된 작업
- [x] 프로젝트 `.claude/settings.json` 생성 (파일/웹/git 자동 허용)
- [x] Playwright MCP 글로벌 설정 추가
- [x] 메모리 시스템 구축
- [x] Insty BM v2.1 knowledge 저장 (`docs/what_is_insty.md`)
- [x] 프로젝트 지식을 `docs/`로 이전 (git 동기화)

<!-- 템플릿:
### [기능명] (브랜치: feat/xxx)
- **상태**: 진행 중 / 리뷰 중 / 블로킹
- **시작일**: YYYY-MM-DD
- **관련 파일**:
- **남은 작업**:
-->
