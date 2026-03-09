# Knowledge 적용 가이드

> Claude Code 플레이북(`knowledge/`)을 프로젝트에 반영한 내용 정리.
> 작성: 2026-03-09

## 이미 반영한 개선 사항

### 1. CLAUDE.md 강화
- **Phase 1 컨텍스트 추가**: 현재 진행 중인 파이프라인 서비스 정보를 CLAUDE.md에 포함
- **knowledge/ 참조 추가**: 에이전트가 필요 시 플레이북 참고할 수 있도록 경로 안내
- **비용 최적화 습관 추가**: `/clear` 습관, 모델 선택, 범위 지정 등
- **디렉토리 구조 업데이트**: `knowledge/`, `pipeline/` 추가 반영
- 📖 참고: `knowledge/level-2/claude-md.md`

### 2. 모듈화된 규칙 파일 (`.claude/rules/`)
- **`pipeline-rules.md`**: Phase 1 팀별 에이전트 프롬프팅 패턴 (역할 부여, CoT, 검증 기준)
- **`cost-rules.md`**: 모델 선택 기준, 컨텍스트 관리, 서브에이전트 비용 절감
- 📖 참고: `knowledge/level-2/claude-md.md` (`.claude/rules/` 패턴)

### 3. 프롬프팅 전략 → 팀 플레이북에 적용
기존 팀 플레이북의 프롬프트들에 다음 기법이 이미 적용됨:
- **역할 부여**: 각 팀별 전문가 역할 설정
- **제약 조건 명시**: "하지 말 것" 포함
- **예시 기반 요청**: DM 템플릿, 콘텐츠 예시 제공
- 📖 참고: `knowledge/level-3/prompting-strategy.md`

## 추가 적용 가능한 영역 (유저 판단 필요)

### A. Headless 모드로 반복 작업 자동화 (중요도: 높음)
매일 반복되는 작업 (콘텐츠 초안, 리드 리서치)을 headless 모드로 자동화 가능:
```bash
# 예: 매일 아침 콘텐츠 초안 자동 생성
claude -p "오늘의 빌드인퍼블릭 포스트 초안 작성" --output-format json
```
- 📖 참고: `knowledge/level-4/headless-mode.md`

### B. Skills로 반복 프롬프트 분리 (중요도: 중간)
자주 쓰는 작업을 Skill로 만들면 `/generate-dm`, `/daily-content` 등으로 호출 가능:
```
# .claude/skills/generate-dm.md
---
description: "DM 메시지 생성"
---
pipeline/team-sales/dm-templates-kr.md를 참고해서 ...
```
- 📖 참고: `knowledge/level-4/skills.md`

### C. Agent Teams로 병렬 실행 (중요도: 낮음 → Phase 2)
4개 팀을 동시에 실행하는 멀티 에이전트 구조. 현재는 순차 실행으로 충분하지만,
고객이 3명 이상이면 고려할 가치 있음.
- 📖 참고: `knowledge/level-5/multi-agent-cowork.md`

### D. CRM 연동 자동화 (중요도: 중간 → 첫 고객 확보 후)
Notion CRM에 딜 정보 자동 업데이트, AI 추천 액션 생성.
- 📖 참고: `knowledge/capstone/sales-agent.md`

### E. CI/CD 파이프라인 (중요도: 낮음 → 코드 성장 후)
코드가 복잡해지면 PR 자동 검증, 테스트 자동화 적용.
- 📖 참고: `knowledge/level-3/cicd-integration.md`

## 추천 읽기 순서

### 지금 바로 읽어볼 것 (Phase 1 실행에 도움)
1. `knowledge/level-3/prompting-strategy.md` — 에이전트한테 일 시키는 8가지 기법
2. `knowledge/level-3/cost-optimization.md` — 토큰 비용 줄이는 7가지 전략
3. `knowledge/capstone/sales-agent.md` — 영업 에이전트 워크플로우 (제안서, CRM)
4. `knowledge/level-4/skills.md` — 반복 작업을 슬래시 커맨드로 만들기

### 나중에 읽어볼 것 (규모 확장 시)
5. `knowledge/level-4/headless-mode.md` — 자동 실행 파이프라인
6. `knowledge/level-5/multi-agent-cowork.md` — 멀티 에이전트 협업
7. `knowledge/level-4/subagent-patterns.md` — 서브에이전트 아키텍처

### 참고용 (필요할 때)
8. `knowledge/level-2/claude-md.md` — CLAUDE.md 고급 작성법
9. `knowledge/level-3/hooks.md` — 자동화 훅 패턴
10. `knowledge/appendix/prompt-cookbook.md` — 프롬프트 레시피 모음
