<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-5/production-deployment -->

# 프로덕션 배포

Claude 기반 시스템을 프로덕션에 배포할 때는 일반 소프트웨어와 다른 AI 특유의 과제를 해결해야 합니다: **비결정적 응답, 비용, API 안정성, 응답 속도**.

## 프로덕션 아키텍처

```
[클라이언트] → [API Gateway] → [AI 미들웨어] → [Anthropic API]
                   ↓                  ↓
              인증/Rate Limit    프롬프트 템플릿
              요청 로깅         캐싱 (Redis)
                               큐 (Bull/BullMQ)
                               비용 추적
                                    ↓
                              [응답 후처리]
                              검증/포맷 변환/로깅
```

## 환경 설정

```typescript
// config.ts
export const config = {
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY!,
    model: process.env.AI_MODEL || "claude-sonnet-4-6",
    maxTokens: parseInt(process.env.AI_MAX_TOKENS || "4096"),
    timeout: parseInt(process.env.AI_TIMEOUT_MS || "30000"),
    maxRetries: parseInt(process.env.AI_MAX_RETRIES || "3"),
  },
  budget: {
    dailyLimitUSD: parseFloat(process.env.DAILY_BUDGET_USD || "50"),
    monthlyLimitUSD: parseFloat(process.env.MONTHLY_BUDGET_USD || "1000"),
  },
  cache: {
    ttlSeconds: parseInt(process.env.CACHE_TTL || "3600"),
    redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
  }
};
```

## 응답 캐싱

동일한 요청에 대한 중복 API 호출 방지:

```typescript
import { createHash } from "crypto";
import Redis from "ioredis";

const redis = new Redis(config.cache.redisUrl);

function getCacheKey(prompt: string, model: string): string {
  return `ai:${createHash("sha256")
    .update(`${model}:${prompt}`)
    .digest("hex")}`;
}

async function cachedQuery(
  prompt: string,
  model: string = config.anthropic.model
): Promise<string> {
  const key = getCacheKey(prompt, model);

  const cached = await redis.get(key);
  if (cached) {
    console.log("Cache HIT");
    return cached;
  }

  console.log("Cache MISS");
  const response = await callClaude(prompt, model);

  await redis.setex(key, config.cache.ttlSeconds, response);

  return response;
}
```

## 비용 모니터링

```typescript
interface UsageRecord {
  timestamp: Date;
  model: string;
  inputTokens: number;
  outputTokens: number;
  costUSD: number;
  requestId: string;
}

const MODEL_PRICING: Record<string, { input: number; output: number }> = {
  "claude-opus-4-6": { input: 15.0 / 1_000_000, output: 75.0 / 1_000_000 },
  "claude-sonnet-4-6": { input: 3.0 / 1_000_000, output: 15.0 / 1_000_000 },
  "claude-haiku-4-5": { input: 0.25 / 1_000_000, output: 1.25 / 1_000_000 },
};

function calculateCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): number {
  const pricing = MODEL_PRICING[model];
  if (!pricing) return 0;
  return inputTokens * pricing.input + outputTokens * pricing.output;
}
```

## 큐 기반 비동기 처리

```typescript
import { Queue, Worker } from "bullmq";

const aiQueue = new Queue("ai-tasks", {
  connection: { host: "localhost", port: 6379 }
});

const worker = new Worker("ai-tasks", async (job) => {
  const { prompt, model, userId } = job.data;

  const result = await cachedQuery(prompt, model);

  // 결과를 WebSocket으로 사용자에게 전달
  notifyUser(userId, { taskId: job.id, result });

  return result;
}, {
  connection: { host: "localhost", port: 6379 },
  concurrency: 3,
  limiter: { max: 10, duration: 60000 }
});
```

## 관측성 (Observability)

```typescript
import { trace, SpanKind } from "@opentelemetry/api";

const tracer = trace.getTracer("ai-service");

async function tracedQuery(prompt: string): Promise<string> {
  return tracer.startActiveSpan("claude-query", {
    kind: SpanKind.CLIENT,
    attributes: {
      "ai.model": config.anthropic.model,
      "ai.prompt_length": prompt.length,
    }
  }, async (span) => {
    try {
      const response = await callClaude(prompt);
      span.setAttributes({
        "ai.response_length": response.length,
        "ai.tokens.input": getInputTokens(),
        "ai.tokens.output": getOutputTokens(),
      });
      return response;
    } catch (error) {
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## 헬스체크

```typescript
app.get("/health", async (req, res) => {
  const checks = {
    api: await checkAnthropicAPI(),
    redis: await checkRedis(),
    queue: await checkQueueDepth(),
  };

  const healthy = Object.values(checks).every(c => c.ok);

  res.status(healthy ? 200 : 503).json({
    status: healthy ? "healthy" : "degraded",
    checks,
    timestamp: new Date().toISOString()
  });
});
```

## 배포 전 체크리스트

### 보안
- [ ] API 키가 환경 변수로만 관리되고 코드에 없음
- [ ] 입력 유효성 검사 (프롬프트 인젝션 방어)
- [ ] 출력 새니타이징 (사용자에게 반환 전)
- [ ] 사용자별 인증/인가

### 안정성
- [ ] 모든 API 호출에 재시도 로직
- [ ] 타임아웃 설정 (기본 30초)
- [ ] 서킷 브레이커 패턴
- [ ] 그레이스풀 셧다운

### 비용
- [ ] 일일/월간 예산 한도 설정
- [ ] 토큰 사용량 실시간 추적
- [ ] 80% 도달 시 알림
- [ ] 응답 캐싱 활성화

### 관측성
- [ ] 분산 추적 (OpenTelemetry)
- [ ] 메트릭 대시보드
- [ ] 에러 알림 (PagerDuty/Slack)
- [ ] 요청/응답 로깅 (PII 제외)

---

**최종 수정**: 2026년 2월 28일
