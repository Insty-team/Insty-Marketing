<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/capstone/hr-agent -->

# HR팀 에이전트

HR팀 에이전트는 **채용, 온보딩, 성과관리, 조직문화** 관련 작업을 처리합니다. 반복적인 HR 업무를 자동화하면서 사람 중심의 따뜻한 문화를 유지합니다.

## HR 에이전트 구현

```typescript
// src/agents/hr.ts
import { query } from "@anthropic-ai/claude-agent-sdk";
import { AgentResponse } from "../shared/types";
import { extractText, log } from "../shared/utils";

const HR_SYSTEM_PROMPT = `당신은 People & Culture 전문가입니다.
데이터 기반 HR 의사결정을 지지하며, 직원 경험(EX)을 최우선으로 생각합니다.
다양성과 포용성(D&I)을 모든 HR 프로세스에 반영합니다.
개인 정보와 민감한 데이터를 철저히 보호합니다.`;

export async function runHRAgent(task: string): Promise<AgentResponse> {
  log("HR", `작업 시작: ${task.slice(0, 40)}...`);
  const response = await query({
    prompt: `${HR_SYSTEM_PROMPT}\n\n---\n\n${task}`,
    options: {
      maxTurns: 10,
      allowedTools: ["Read", "Write"]
    }
  });
  const result = extractText(response);
  log("HR", "작업 완료");
  return {
    department: "hr",
    result,
    confidence: "high",
    actionItems: [],
    escalationNeeded: result.toLowerCase().includes("법적") ||
      result.toLowerCase().includes("징계")
  };
}
```

## 주요 HR 워크플로우

### 1. 채용 공고 작성

직무 설명, 자격요건, 우대사항을 포함한 채용 공고를 생성합니다.

### 2. 온보딩 프로그램 설계

30-60-90일 구조의 체계적 온보딩 프로그램을 설계합니다:
- Day 1: 첫날 경험 (환영, 장비 설정, 팀 소개)
- Week 1: 회사/제품/문화 이해
- 30일: 역할 핵심 역량 기초
- 60일: 독립적 업무 수행
- 90일: 성과 첫 평가 및 목표 설정

### 3. 성과 리뷰 템플릿 생성

역량 평가, SMART 목표 설정, 건설적 피드백을 포함한 리뷰를 작성합니다.

### 4. 직원 만족도 설문 분석

강점 영역, 개선 필요 영역, 부서별 특이사항, 즉시 실행 가능한 개선안을 도출합니다.

## HR 에이전트 특화 설정

```typescript
const HR_SENSITIVE_KEYWORDS = [
  "급여", "연봉", "징계", "해고", "소송",
  "차별", "성희롱", "개인정보"];

export async function runHRAgentSafe(task: string): Promise<AgentResponse> {
  const isSensitive = HR_SENSITIVE_KEYWORDS.some(kw =>
    task.toLowerCase().includes(kw)
  );
  if (isSensitive) {
    log("HR", "민감한 사안 감지 → HR 담당자 검토 필요 표시");
  }
  const result = await runHRAgent(task);
  return {
    ...result,
    escalationNeeded: isSensitive || result.escalationNeeded
  };
}
```

## HR 에이전트 사용 주의사항

- 급여, 징계, 해고 관련 결정은 반드시 HR 담당자가 최종 검토
- 개인 식별 정보(이름, 사번)는 프롬프트에 최소화
- 법적 효력이 있는 문서(계약서, 경고장)는 법무팀 에이전트와 연계

---

**최종 수정:** 2026년 2월 28일
