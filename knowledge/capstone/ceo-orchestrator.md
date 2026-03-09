<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/capstone/ceo-orchestrator -->

# CEO 오케스트레이터

CEO 오케스트레이터는 기업 AI 팀의 **두뇌이자 조율자**입니다. 사용자 요청을 분석해 어떤 부서가 필요한지 판단하고, 해당 에이전트에게 위임한 후 결과를 통합해 보고합니다.

## CEO의 책임

1. **요청 분석**: 입력된 작업이 어떤 부서 역량이 필요한지 판단
2. **라우팅**: 단일 또는 복수 부서 에이전트로 작업 위임
3. **병렬 조율**: 독립적인 부서 작업은 동시에 실행
4. **결과 통합**: 각 부서 결과를 종합해 의미 있는 보고서 작성
5. **에스컬레이션**: 복잡한 사안을 감지하고 인간에게 전달

## CEO 라우터 구현

```typescript
// src/orchestrator/router.ts
import { query } from "@anthropic-ai/claude-agent-sdk";
import { Department, AgentRequest } from "../shared/types";
import { extractText, parseJSON, log } from "../shared/utils";

interface RoutingDecision {
  departments: Department[];
  parallel: boolean;
  reasoning: string;
}

export async function routeRequest(
  request: AgentRequest): Promise<RoutingDecision> {
  const routingResponse = await query({
    prompt: `기업 AI 팀의 라우터로서 다음 요청을 분석해줘.
    요청: ${request.task}
    ${request.context ? `컨텍스트: ${request.context}` : ""}
    사용 가능한 부서:
    - marketing: 마케팅, 콘텐츠, 브랜딩, SEO, 캠페인
    - hr: 채용, 인사, 교육훈련, 성과관리, 조직문화
    - dev: 코드, 개발, 기술, 시스템, 인프라
    - finance: 재무, 예산, 회계, 비용, 투자
    - sales: 영업, 고객 확보, 제안서, CRM, 파이프라인
    - legal: 계약, 법무, 컴플라이언스, 규정, 특허
    - cs: 고객지원, 불만처리, 만족도, 피드백
    다음 JSON만 출력해줘:
    {
      "departments": ["부서1", "부서2"],
      "parallel": true,
      "reasoning": "이유 설명"
    }`,
    options: { maxTurns: 3 }
  });

  const text = extractText(routingResponse);
  return parseJSON<RoutingDecision>(text, {
    departments: ["cs"],
    parallel: false,
    reasoning: "기본 CS 라우팅"
  });
}
```

## CEO 오케스트레이터 메인 구현

```typescript
// src/orchestrator/ceo.ts
import { query } from "@anthropic-ai/claude-agent-sdk";
import { routeRequest } from "./router";
import { runMarketingAgent } from "../agents/marketing";
import { runHRAgent } from "../agents/hr";
import { runDevAgent } from "../agents/dev";
import { runFinanceAgent } from "../agents/finance";
import { runSalesAgent } from "../agents/sales";
import { runLegalAgent } from "../agents/legal";
import { runCSAgent } from "../agents/cs";
import {
  Department, AgentRequest, AgentResponse, OrchestratorResult
} from "../shared/types";
import { extractText, log } from "../shared/utils";

const AGENT_RUNNERS: Record<
  Department,
  (task: string) => Promise<AgentResponse>> = {
  marketing: runMarketingAgent,
  hr: runHRAgent,
  dev: runDevAgent,
  finance: runFinanceAgent,
  sales: runSalesAgent,
  legal: runLegalAgent,
  cs: runCSAgent
};

export async function runCEO(
  request: AgentRequest): Promise<OrchestratorResult> {
  log("CEO", `요청 접수: ${request.task.slice(0, 50)}...`);

  // 1단계: 라우팅 결정
  const routing = await routeRequest(request);
  log("CEO", `라우팅: ${routing.departments.join(", ")} (${routing.parallel ? "병렬" : "순차"})`);

  // 2단계: 부서 에이전트 실행
  let departmentResults: AgentResponse[];

  if (routing.parallel) {
    const results = await Promise.allSettled(
      routing.departments.map(dept => {
        log("CEO", `${dept} 에이전트 시작`);
        return AGENT_RUNNERS[dept](request.task);
      })
    );

    departmentResults = results
      .filter(r => r.status === "fulfilled")
      .map(r => (r as PromiseFulfilledResult<AgentResponse>).value);

    const failedCount = results.filter(r => r.status === "rejected").length;
    if (failedCount > 0) log("CEO", `경고: ${failedCount}개 부서 실행 실패`);
  } else {
    departmentResults = [];
    for (const dept of routing.departments) {
      log("CEO", `${dept} 에이전트 실행 중...`);

      const prevContext = departmentResults
        .map(r => `[${r.department}]: ${r.result.slice(0, 200)}`)
        .join("\n");

      const taskWithContext = prevContext
        ? `${request.task}\n\n이전 부서 결과:\n${prevContext}`
        : request.task;

      const result = await AGENT_RUNNERS[dept](taskWithContext);
      departmentResults.push(result);
    }
  }

  // 3단계: 결과 통합 및 경영진 보고서
  log("CEO", "결과 통합 중...");

  const summaryResponse = await query({
    prompt: `CEO로서 다음 부서 보고를 종합해서 경영진 보고서를 작성해줘.
    원래 요청: ${request.task}

    부서별 결과:
    ${departmentResults.map(r =>
      `## ${r.department.toUpperCase()} 팀\n${r.result}`
    ).join("\n\n")}

    보고서 형식:
    1. 핵심 요약 (3줄 이내)
    2. 부서별 주요 발견사항
    3. 즉시 실행 가능한 액션 아이템
    4. 리스크 및 주의사항`,
    options: { maxTurns: 5 }
  });

  const executiveReport = extractText(summaryResponse);

  const actionItems = departmentResults
    .flatMap(r => r.actionItems || [])
    .filter(Boolean);

  log("CEO", "완료");

  return {
    summary: executiveReport.slice(0, 500),
    departmentResults,
    actionItems,
    executiveReport
  };
}
```

## 진입점

```typescript
// src/index.ts
import { runCEO } from "./orchestrator/ceo";

async function main() {
  const result = await runCEO({
    task: "Q1 마케팅 캠페인 계획을 수립하고, 예산을 분석하고, 필요한 개발 리소스를 파악해줘",
    priority: "urgent",
    requestedBy: "CFO"
  });

  console.log("\n===== 경영진 보고서 =====");
  console.log(result.executiveReport);

  console.log("\n===== 액션 아이템 =====");
  result.actionItems.forEach((item, i) => {
    console.log(`${i + 1}. ${item}`);
  });
}

main().catch(console.error);
```

## 실행 예시

**입력**: "신규 SaaS 제품 런칭을 위한 전사 준비 상황 점검"

**→ CEO 라우팅**: marketing, dev, sales, legal (병렬)

**경영진 보고서**:
"마케팅팀은 SNS 캠페인 준비 완료. 개발팀은 베타 배포 준비 중이며 보안 이슈 2건 해결 필요. 영업팀은 파이프라인 50건 확보. 법무팀은 개인정보처리방침 수정 권고 1건 발생."

**액션 아이템**:
1. 개발팀: 보안 이슈 패치 즉시 적용
2. 법무팀: 개인정보처리방침 3항 수정
3. 마케팅팀: 런칭 D-7 SNS 예약 발행 확인

## CEO 에이전트 최적화

- 라우팅 판단에는 저비용 모델(Haiku) 사용으로 비용 절감
- 독립적인 부서 작업은 항상 병렬 실행
- 경영진 보고서는 1페이지 분량으로 제한해 가독성 확보

---

**최종 수정**: 2026년 2월 28일
