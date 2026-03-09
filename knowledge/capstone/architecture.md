<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/capstone/architecture -->

# 아키텍처 설계

캡스톤 프로젝트에서 구축할 기업 AI 팀은 **CEO 오케스트레이터 + 7개 부서 에이전트**로 구성됩니다. 이 챕터에서는 전체 시스템 아키텍처와 에이전트 간 통신 방식을 설계합니다.

## 전체 아키텍처

```
                    [사용자 / 경영진]
                          ↓
              [CEO 오케스트레이터 에이전트]
                 작업 분석 → 라우팅 → 통합
                          ↓
    ┌─────────────────────────────────────────────────┐
    │                                                 │
  [마케팅]  [HR]  [개발]  [재무]  [영업]  [법무]  [CS] │
    │                                                 │
    └─────────────────────────────────────────────────┘
                          ↓
                  [결과 통합 & 보고서]
```

## 에이전트 역할 정의

| 에이전트 | 핵심 역할 | 주요 도구 |
|---------|---------|---------|
| CEO 오케스트레이터 | 작업 분석, 부서 라우팅, 결과 통합 | 모든 도구 |
| 마케팅 | 콘텐츠 생성, 캠페인 분석, SEO | Read, Write |
| HR | 채용, 온보딩, 성과 관리 | Read, Write |
| 개발 | 코드 리뷰, 기술부채, PR 분석 | Read, Grep, Bash |
| 재무 | 예산 분석, 지출 보고, 예측 | Read, Bash |
| 영업 | CRM 업데이트, 제안서, 파이프라인 | Read, Write |
| 법무 | 계약 검토, 컴플라이언스 | Read |
| CS | 티켓 처리, FAQ, 에스컬레이션 | Read, Write |

## 프로젝트 구조

```
enterprise-ai-team/
├── src/
│   ├── orchestrator/
│   │   ├── ceo.ts          — CEO 오케스트레이터
│   │   └── router.ts       — 부서 라우팅 로직
│   ├── agents/
│   │   ├── marketing.ts
│   │   ├── hr.ts
│   │   ├── dev.ts
│   │   ├── finance.ts
│   │   ├── sales.ts
│   │   ├── legal.ts
│   │   └── cs.ts
│   ├── shared/
│   │   ├── types.ts        — 공통 타입 정의
│   │   ├── utils.ts        — extractText 등 유틸
│   │   └── config.ts       — 에이전트 설정
│   └── index.ts            — 진입점
├── prompts/
│   ├── ceo-system.md
│   └── ...                 — 각 에이전트 시스템 프롬프트
├── package.json
└── .env
```

## 공통 타입 정의

```typescript
// src/shared/types.ts
export type Department =
  | "marketing" | "hr" | "dev"
  | "finance" | "sales" | "legal" | "cs";

export interface AgentRequest {
  task: string;
  context?: string;
  priority?: "urgent" | "normal" | "low";
  requestedBy?: string;
}

export interface AgentResponse {
  department: Department;
  result: string;
  confidence: "high" | "medium" | "low";
  actionItems?: string[];
  escalationNeeded?: boolean;
}

export interface OrchestratorResult {
  summary: string;
  departmentResults: AgentResponse[];
  actionItems: string[];
  executiveReport: string;
}
```

## 공통 유틸리티

```typescript
// src/shared/utils.ts
import { SDKMessage } from "@anthropic-ai/claude-agent-sdk";

export function extractText(messages: SDKMessage[]): string {
  return messages
    .filter(m => m.type === "assistant")
    .flatMap(m => m.content)
    .filter(c => c.type === "text")
    .map(c => c.text)
    .join("\n");
}

export function parseJSON<T>(text: string, fallback: T): T {
  try {
    const match = text.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    return match ? JSON.parse(match[0]) : fallback;
  } catch {
    return fallback;
  }
}

export function log(agent: string, message: string) {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] [${agent.toUpperCase()}] ${message}`);
}
```

## 에이전트 기본 설정

```typescript
// src/shared/config.ts
import { Department } from "./types";

export interface AgentConfig {
  systemPrompt: string;
  maxTurns: number;
  allowedTools: string[];
}

export const AGENT_CONFIGS: Record<Department, AgentConfig> = {
  marketing: {
    systemPrompt: `당신은 마케팅 전략가이자 콘텐츠 크리에이터입니다.
      데이터 기반으로 마케팅 전략을 수립하고 고품질 콘텐츠를 생산합니다.`,
    maxTurns: 12,
    allowedTools: ["Read", "Write", "Glob"]
  },
  hr: {
    systemPrompt: `당신은 HR 전문가입니다.
      채용, 온보딩, 성과관리, 조직문화 강화에 전문성을 보유합니다.`,
    maxTurns: 10,
    allowedTools: ["Read", "Write"]
  },
  dev: {
    systemPrompt: `당신은 시니어 소프트웨어 엔지니어입니다.
      코드 품질, 아키텍처, 보안, 성능을 전문으로 검토합니다.`,
    maxTurns: 15,
    allowedTools: ["Read", "Glob", "Grep", "Bash"]
  },
  finance: {
    systemPrompt: `당신은 재무 분석가입니다.
      예산 계획, 비용 분석, 재무 예측을 수행합니다.`,
    maxTurns: 8,
    allowedTools: ["Read", "Bash"]
  },
  sales: {
    systemPrompt: `당신은 영업 전략가입니다.
      CRM 관리, 제안서 작성, 파이프라인 최적화를 전문으로 합니다.`,
    maxTurns: 10,
    allowedTools: ["Read", "Write"]
  },
  legal: {
    systemPrompt: `당신은 기업 법무 전문가입니다.
      계약 검토, 리스크 분석, 컴플라이언스 확인을 수행합니다.
      법적 자문은 참고용이며 실제 법률 결정은 변호사 확인이 필요합니다.`,
    maxTurns: 10,
    allowedTools: ["Read"]
  },
  cs: {
    systemPrompt: `당신은 고객 성공 전문가입니다.
      고객 문제를 신속하고 친절하게 해결하며 고객 만족도를 높입니다.`,
    maxTurns: 8,
    allowedTools: ["Read", "Write"]
  }
};
```

## 데이터 흐름

```
1. 사용자 요청 입력
   ↓
2. CEO 오케스트레이터가 요청 분석
   → 어떤 부서가 필요한가?
   → 순차 처리인가 병렬 처리인가?
   ↓
3. 해당 부서 에이전트 실행
   → 단일 부서: 직접 실행
   → 복수 부서: Promise.all() 병렬 실행
   ↓
4. CEO가 결과 통합
   → 부서별 결과 요약
   → 액션 아이템 추출
   → 경영진 보고서 작성
   ↓
5. 최종 결과 반환
```

## 아키텍처 설계 원칙

- **단일 진입점**: 사용자는 CEO 에이전트만 상대하면 됨
- **느슨한 결합**: 각 부서 에이전트는 독립적으로 교체/업그레이드 가능
- **실패 격리**: 한 부서 실패가 전체 시스템에 영향을 주지 않음
- **확장성**: 새 부서 에이전트를 쉽게 추가 가능

---

**최종 수정**: 2026년 2월 28일
