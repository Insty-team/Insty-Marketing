<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/agent-sdk-basics -->

# Agent SDK 기초

Claude Agent SDK는 Claude Code의 기능을 **프로그래밍 방식으로 제어**할 수 있게 해주는 라이브러리입니다. 단순한 대화 넘어서, 자율적으로 작업을 계획하고 실행하는 에이전트를 코드로 구축할 수 있습니다.

## Agent SDK vs Claude Code CLI

| 구분 | Claude Code CLI | Agent SDK |
|------|-----------------|-----------|
| 사용 방법 | 터미널 대화 | 코드로 제어 |
| 적합한 상황 | 개발 중 즉각적인 도움 | 자동화된 파이프라인 |
| 커스터마이징 | CLAUDE.md, Skills | 완전한 프로그래밍 제어 |
| 사용자 | 개발자 개인 | 시스템/애플리케이션 |

## 설치

```bash
npm install @anthropic-ai/claude-agent-sdk
# 또는
pip install anthropic
```

## 기본 에이전트 실행

### Node.js / TypeScript

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function runAgent() {
  // 단일 작업 실행
  const messages = await query({
    prompt: "현재 디렉토리의 TypeScript 파일 목록을 가져오고, 각 파일의 크기를 알려줘",
    options: {
      maxTurns: 5,  // 최대 5번의 도구 호출 허용
    }
  });

  // 최종 응답 출력
  for (const message of messages) {
    if (message.type === "assistant") {
      for (const block of message.content) {
        if (block.type === "text") {
          console.log(block.text);
        }
      }
    }
  }
}

runAgent();
```

### Python

```python
import anthropic
import subprocess
import json

client = anthropic.Anthropic()

def run_agent(task: str) -> str:
    """Claude 에이전트를 실행하고 결과를 반환합니다."""
    result = subprocess.run(
        ["claude", "--print", "--output-format", "json", task],
        capture_output=True,
        text=True,
        timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"에이전트 실행 실패: {result.stderr}")
    return result.stdout

# 사용 예시
output = run_agent("src/ 디렉토리에서 TODO 주석을 모두 찾아서 목록으로 정리해줘")
print(output)
```

## 스트리밍 응답

실시간으로 에이전트의 응답을 처리:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function streamingAgent() {
  const stream = query({
    prompt: "프로젝트 구조를 분석하고 개선점을 제안해줘",
    options: {
      maxTurns: 10,
    }
  });

  for await (const event of stream) {
    if (event.type === "assistant") {
      // 에이전트 응답 처리
      for (const block of event.content) {
        if (block.type === "text") {
          process.stdout.write(block.text);
        }
      }
    } else if (event.type === "tool_use") {
      // 도구 실행 모니터링
      console.log(`\n[도구 실행] ${event.name}`);
    }
  }
}
```

## 시스템 프롬프트 설정

에이전트의 역할과 제약을 설정:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const agentConfig = {
  prompt: "코드베이스에서 보안 취약점을 찾아줘",
  options: {
    systemPrompt: `
      당신은 보안 전문가입니다.
      OWASP Top 10을 기준으로 취약점을 분석합니다.
      발견된 취약점은 [심각도: 높음/중간/낮음] 으로 분류합니다.
      수정 방법도 구체적으로 제시합니다.
      절대로 파일을 수정하지 않고 분석만 합니다.
    `,
    maxTurns: 20,
  }
};

const result = await query(agentConfig);
```

## 도구 제한 설정

에이전트가 사용할 수 있는 도구를 제한:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 읽기 전용 에이전트 (수정 불가)
const readOnlyAgent = {
  prompt: "프로젝트 아키텍처를 분석해줘",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],  // 읽기 도구만
    maxTurns: 15,
  }
};

// 수정 가능 에이전트 (특정 디렉토리만)
const limitedAgent = {
  prompt: "src/utils/ 파일들을 리팩토링해줘",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Edit", "Write"],
    maxTurns: 30,
  }
};
```

## 에이전트 결과 처리

```typescript
import { query, SDKMessage } from "@anthropic-ai/claude-agent-sdk";

async function processResult(prompt: string) {
  const messages: SDKMessage[] = await query({ prompt });

  // 최종 텍스트 응답 추출
  const finalResponse = messages
    .filter(m => m.type === "assistant")
    .flatMap(m => m.content)
    .filter(c => c.type === "text")
    .map(c => c.text)
    .join("\n");

  // 사용된 도구 목록 추출
  const toolsUsed = messages
    .filter(m => m.type === "tool_use")
    .map(m => m.name);

  console.log("응답:", finalResponse);
  console.log("사용된 도구:", [...new Set(toolsUsed)]);

  return { response: finalResponse, tools: toolsUsed };
}
```

## 작업 디렉토리 설정

에이전트가 작업할 디렉토리 지정:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const result = await query({
  prompt: "이 프로젝트의 테스트 커버리지를 확인해줘",
  options: {
    cwd: "/path/to/project",  // 작업 디렉토리 설정
    maxTurns: 10,
  }
});
```

## 다음 단계

Agent SDK를 익혔다면 서브에이전트 패턴 챕터에서 여러 에이전트를 조율하는 방법을 배울 수 있습니다.

## SDK 선택 가이드

- **간단한 자동화**: `claude --print` (헤드리스 CLI)
- **복잡한 파이프라인**: Agent SDK (프로그래밍 제어)
- **대화형 작업**: Claude Code CLI (터미널 대화)

---

**최종 수정**: 2026년 2월 28일
