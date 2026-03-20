<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-5/claude-api-patterns -->

# Claude API 패턴

Claude Code(Agent SDK)와 달리, **Anthropic Claude API**를 직접 사용하면 더 세밀한 제어가 가능합니다. 자체 AI 애플리케이션을 구축할 때 필요한 패턴들을 다룹니다.

## Claude API vs Agent SDK

| 구분 | Claude API (Anthropic) | Agent SDK (Claude Code) |
|------|----------------------|----------------------|
| 용도 | 자체 AI 앱 구축 | Claude Code 자동화 |
| 파일 접근 | 직접 없음 (직접 구현) | 내장 도구 (Read, Edit 등) |
| 컨텍스트 | 직접 관리 | 자동 관리 |
| 제어 수준 | 완전한 제어 | 제한적 |
| 시작 난이도 | 높음 | 낮음 |

## 기본 메시지 API

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

// 기본 호출
async function simpleChat(userMessage: string): Promise<string> {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 4096,
    messages: [
      { role: "user", content: userMessage }
    ]
  });

  return response.content[0].type === "text"
    ? response.content[0].text
    : "";
}

// 시스템 프롬프트 포함
async function expertChat(
  systemPrompt: string,
  userMessage: string): Promise<string> {
  const response = await client.messages.create({
    model: "claude-opus-4-6",
    max_tokens: 8192,
    system: systemPrompt,
    messages: [
      { role: "user", content: userMessage }
    ]
  });

  return response.content[0].type === "text"
    ? response.content[0].text
    : "";
}
```

## 대화 히스토리 관리

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

type Message = {
  role: "user" | "assistant";
  content: string;
};

class ConversationManager {
  private history: Message[] = [];
  private systemPrompt: string;

  constructor(systemPrompt: string) {
    this.systemPrompt = systemPrompt;
  }

  async chat(userMessage: string): Promise<string> {
    this.history.push({ role: "user", content: userMessage });

    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      system: this.systemPrompt,
      messages: this.history
    });

    const assistantMessage = response.content[0].type === "text"
      ? response.content[0].text
      : "";

    this.history.push({ role: "assistant", content: assistantMessage });

    if (this.history.length > 20) {
      this.history = this.history.slice(-20);
    }

    return assistantMessage;
  }

  clearHistory() {
    this.history = [];
  }
}

// 사용
const assistant = new ConversationManager(
  "당신은 친절한 코딩 튜터입니다. 한국어로 답변해주세요.");

const reply1 = await assistant.chat("재귀 함수가 뭔가요?");
const reply2 = await assistant.chat("피보나치 수열로 예시를 보여주세요.");
```

## 스트리밍 응답

긴 응답을 실시간으로 처리:

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

async function streamResponse(prompt: string): Promise<string> {
  let fullText = "";

  const stream = client.messages.stream({
    model: "claude-sonnet-4-6",
    max_tokens: 4096,
    messages: [{ role: "user", content: prompt }]
  });

  stream.on("text", (text) => {
    process.stdout.write(text);
    fullText += text;
  });

  await stream.finalMessage();
  console.log();

  return fullText;
}

// async iterator 방식
async function streamWithIterator(prompt: string) {
  const stream = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 4096,
    stream: true,
    messages: [{ role: "user", content: prompt }]
  });

  for await (const event of stream) {
    if (
      event.type === "content_block_delta" &&
      event.delta.type === "text_delta"
    ) {
      process.stdout.write(event.delta.text);
    }
  }
}
```

## 도구 사용 (Tool Use)

Claude에게 함수를 제공하고 호출하게 만들기:

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

const tools: Anthropic.Tool[] = [
  {
    name: "get_weather",
    description: "특정 도시의 현재 날씨를 가져옵니다",
    input_schema: {
      type: "object",
      properties: {
        city: {
          type: "string",
          description: "날씨를 조회할 도시명 (예: Seoul, Tokyo)"
        },
        unit: {
          type: "string",
          enum: ["celsius", "fahrenheit"],
          description: "온도 단위"
        }
      },
      required: ["city"]
    }
  },
  {
    name: "search_database",
    description: "내부 데이터베이스에서 정보를 검색합니다",
    input_schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "검색 쿼리" },
        limit: { type: "number", description: "최대 결과 수" }
      },
      required: ["query"]
    }
  }
];

async function executeTool(
  name: string,
  input: Record<string, any>): Promise<string> {
  if (name === "get_weather") {
    return JSON.stringify({
      city: input.city,
      temperature: 22,
      condition: "맑음",
      unit: input.unit || "celsius"
    });
  }

  if (name === "search_database") {
    return JSON.stringify({
      results: [`${input.query} 관련 결과 1`, `${input.query} 관련 결과 2`],
      total: 2
    });
  }

  return "도구를 찾을 수 없습니다.";
}

async function agentLoop(userMessage: string): Promise<string> {
  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: userMessage }
  ];

  while (true) {
    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      tools,
      messages
    });

    messages.push({ role: "assistant", content: response.content });

    if (response.stop_reason === "end_turn") {
      const textBlock = response.content.find(b => b.type === "text");
      return textBlock?.type === "text" ? textBlock.text : "";
    }

    const toolUses = response.content.filter(b => b.type === "tool_use");
    const toolResults: Anthropic.ToolResultBlockParam[] = await Promise.all(
      toolUses.map(async (toolUse) => {
        if (toolUse.type !== "tool_use") return null!;
        const result = await executeTool(
          toolUse.name,
          toolUse.input as Record<string, any>
        );
        return {
          type: "tool_result" as const,
          tool_use_id: toolUse.id,
          content: result
        };
      })
    );

    messages.push({ role: "user", content: toolResults });
  }
}
```

## 프롬프트 캐싱

반복 사용하는 긴 프롬프트를 캐싱해 비용 절감:

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

async function cachedDocumentQA(
  document: string,
  questions: string[]): Promise<string[]> {
  const answers: string[] = [];

  for (const question of questions) {
    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 2048,
      system: [
        {
          type: "text",
          text: "당신은 문서 분석 전문가입니다.",
        },
        {
          type: "text",
          text: document,
          // @ts-ignore - cache_control은 베타 기능
          cache_control: { type: "ephemeral" }
        }
      ],
      messages: [{ role: "user", content: question }]
    });

    const text = response.content[0].type === "text"
      ? response.content[0].text
      : "";
    answers.push(text);

    console.log("캐시 생성:", response.usage.cache_creation_input_tokens ?? 0);
    console.log("캐시 읽기:", response.usage.cache_read_input_tokens ?? 0);
  }

  return answers;
}
```

## 모델 선택 기준

- **claude-opus-4-6**: 복잡한 추론, 긴 문서 분석 (최고 성능, 높은 비용)
- **claude-sonnet-4-6**: 균형 잡힌 성능 (대부분의 프로덕션 케이스에 적합)
- **claude-haiku-4-5**: 빠른 응답, 단순 작업 (낮은 비용, 높은 처리량)

## API 직접 사용 시 주의

- Rate limit: 분당 요청 수와 토큰 수 제한 존재
- 에러 핸들링: 429 (rate limit), 529 (overloaded) 재시도 필수
- 비용 추적: `usage.input_tokens`, `usage.output_tokens` 모니터링 필수

---

**최종 수정**: 2026년 2월 28일
