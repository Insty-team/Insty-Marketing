# Insty AI 에이전트 팀 시스템

> CEO 오케스트레이터 + 4개 팀 에이전트로 구성된 1인 사업자용 AI 팀
> 캡스톤 아키텍처(`knowledge/capstone/`)를 1인 사업자 규모로 최적화

## 아키텍처

```
                    [사장 (나)]
                        ↓
              [CEO 오케스트레이터]
            작업 분석 → 라우팅 → 통합
                        ↓
    ┌───────────────────────────────────┐
    │                                   │
  [마케팅]  [영업]  [리서치]  [딜리버리] │
    │                                   │
    └───────────────────────────────────┘
                        ↓
                [결과 보고 + 실행]
```

## 기업 vs 1인 사업자 차이

| 구분 | 기업 캡스톤 (7팀) | 우리 시스템 (4팀) |
|------|-----------------|-----------------|
| 에이전트 | CEO + 마케팅/HR/개발/재무/영업/법무/CS | CEO + 마케팅/영업/리서치/딜리버리 |
| 인프라 | Agent SDK + TypeScript | Claude Code 서브에이전트 + 프롬프트 |
| 비용 | API 과금 (월 $100~500) | Claude Pro/Max 구독 내 |
| 난이도 | 개발자 필요 | 프롬프트만으로 운영 |

## 파일 구조

```
agents/
├── README.md                — 이 파일
├── prompts/                 — 각 에이전트 시스템 프롬프트
│   ├── ceo-orchestrator.md  — CEO 오케스트레이터
│   ├── marketing.md         — 마케팅 에이전트
│   ├── sales.md             — 영업 에이전트
│   ├── research.md          — 리서치 에이전트
│   └── delivery.md          — 딜리버리 에이전트
├── workflows/               — 자주 쓰는 워크플로우 (복사해서 실행)
│   ├── daily-morning.md     — 매일 아침 루틴
│   ├── lead-pipeline.md     — 리드 발굴 → 전환 파이프라인
│   ├── content-weekly.md    — 주간 콘텐츠 생산
│   └── client-onboarding.md — 신규 고객 온보딩
└── for-clients/             — 고객에게 납품하는 에이전트 템플릿
    ├── README.md            — 고객용 가이드
    └── templates/           — 업종별 템플릿
```

## 사용법

### 1. CEO에게 업무 지시 (일반적인 사용)
```
> @agents/prompts/ceo-orchestrator.md
> "이번 주 리드 10명 발굴하고, 콘텐츠 3개 만들고, 기존 리드 팔로업해줘"
```

### 2. 특정 팀에 직접 지시
```
> @agents/prompts/marketing.md
> "오늘의 빌드인퍼블릭 X 쓰레드 작성해줘. 주제: AI 에이전트로 1인 기업 운영하기"
```

### 3. 워크플로우 실행
```
> @agents/workflows/daily-morning.md
```
