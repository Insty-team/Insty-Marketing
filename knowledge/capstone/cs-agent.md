<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/capstone/cs-agent -->

# CS팀 에이전트

CS(Customer Success)팀 에이전트는 **고객 문의 처리, FAQ 자동 생성, 고객 감정 분석, 에스컬레이션 판단**을 담당합니다. 빠르고 일관된 고객 응대로 CSAT(고객 만족도)를 높입니다.

## CS 에이전트 구현

```typescript
// src/agents/cs.ts
import { query } from "@anthropic-ai/claude-agent-sdk";
import { AgentResponse } from "../shared/types";
import { extractText, log } from "../shared/utils";

const CS_SYSTEM_PROMPT = `당신은 공감 능력이 뛰어난 고객 성공 전문가입니다.
고객의 감정을 먼저 인정하고, 명확하고 실행 가능한 해결책을 제시합니다.
기술적 내용도 비전문가가 이해할 수 있게 쉽게 설명합니다.
에스컬레이션이 필요한 경우 지체 없이 적절한 팀으로 연결합니다.
응답은 항상 친절하고 전문적으로, 과도한 사과 반복은 피합니다.`;

export async function runCSAgent(task: string): Promise<AgentResponse> {
  log("CS", `작업 시작: ${task.slice(0, 40)}...`);

  const sentiment = await analyzeSentiment(task);
  const needsEscalation = sentiment === "very_negative" ||
    task.includes("환불") ||
    task.includes("법적") ||
    task.includes("언론");

  const response = await query({
    prompt: `${CS_SYSTEM_PROMPT}
    고객 감정 상태: ${sentiment}
    에스컬레이션 필요: ${needsEscalation ? "예" : "아니요"}
    ---
    ${task}`,
    options: {
      maxTurns: 8,
      allowedTools: ["Read", "Write"]
    }
  });

  const result = extractText(response);
  log("CS", `작업 완료 (에스컬레이션: ${needsEscalation})`);

  return {
    department: "cs",
    result,
    confidence: needsEscalation ? "low" : "high",
    escalationNeeded: needsEscalation,
    actionItems: needsEscalation ? ["즉시 CS 매니저에게 연결"] : []
  };
}

async function analyzeSentiment(
  text: string
): Promise<"positive" | "neutral" | "negative" | "very_negative"> {
  const response = await query({
    prompt: `다음 고객 메시지의 감정 상태를 분석해줘.
    positive/neutral/negative/very_negative 중 하나만 출력해줘.
    메시지: ${text}`,
    options: { maxTurns: 2 }
  });

  const result = extractText(response).trim().toLowerCase();
  if (result.includes("very_negative")) return "very_negative";
  if (result.includes("negative")) return "negative";
  if (result.includes("positive")) return "positive";
  return "neutral";
}
```

## 주요 CS 워크플로우

### 1. 고객 문의 자동 응답

감정 분석 후 공감적 톤으로 단계별 해결책을 제시합니다.

### 2. FAQ 자동 생성

지원 티켓 히스토리에서 자주 묻는 질문을 추출해 카테고리별 FAQ 문서를 작성합니다.

### 3. 고객 VOC 분석

긍정/부정 피드백 테마, 기능 요청 빈도, 이탈 위험 신호, UX 개선점을 분석합니다.

### 4. 에스컬레이션 판단 로직

```typescript
const ESCALATION_RULES: EscalationRule[] = [
  {
    condition: (t) => t.includes("환불") || t.includes("취소"),
    target: "CS 매니저",
    priority: "high"
  },
  {
    condition: (t) => t.includes("법적") || t.includes("소송") || t.includes("변호사"),
    target: "법무팀",
    priority: "urgent"
  },
  {
    condition: (t) => t.includes("데이터 유출") || t.includes("개인정보"),
    target: "보안팀 + 법무팀",
    priority: "urgent"
  },
  {
    condition: (t) => t.includes("언론") || t.includes("기사"),
    target: "PR팀 + 임원",
    priority: "urgent"
  }
];
```

## CSAT 모니터링 자동화

매일 CSAT 데이터를 분석하고, 3.0 이하로 떨어지면 CS 팀장에게 알림을 전송합니다.

## CS 에이전트 활용 팁

- 제품 문서, 릴리즈 노트를 시스템 프롬프트에 포함해 정확한 답변 보장
- 부정 감정 감지 시 더 공감적인 톤으로 응답하도록 프롬프트 조정
- 반복되는 문의는 자동으로 FAQ에 추가하는 루프 구성

---

**최종 수정:** 2026년 2월 28일
