<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-5/multi-agent-cowork -->

# 멀티에이전트 Co-work

멀티에이전트 Co-work는 **여러 Claude 인스턴스가 각자 역할을 맡아 협력**하는 방식입니다. 한 에이전트가 모든 것을 처리하는 대신, 전문화된 에이전트들이 병렬로 작업하고 결과를 통합합니다.

## Co-work vs 단일 에이전트

| 구분 | 단일 에이전트 | 멀티에이전트 Co-work |
|------|-------------|-------------------|
| 처리 방식 | 순차적 | 병렬 |
| 컨텍스트 | 하나의 긴 컨텍스트 | 각자 독립된 컨텍스트 |
| 전문성 | 범용 | 역할별 특화 |
| 속도 | 느림 | 빠름 |
| 비용 | 낮음 | 높음 (병렬만큼 증가) |
| 적합 케이스 | 단순 작업 | 복잡한 대규모 작업 |

## 기본 Co-work 패턴

### 역할 분담 아키텍처

```
[사용자 요청]
      ↓
[코디네이터 에이전트] — 작업 분석 및 역할 배정
      ↓
┌─────────────────────────────────────────────┐
│  [리서처]      [개발자]      [리뷰어]        │
│  (정보 수집)   (코드 작성)   (품질 검토)     │
└─────────────────────────────────────────────┘
      ↓
[코디네이터 에이전트] — 결과 통합 및 최종 응답
```

### Claude Code에서 Co-work 요청

```
> 우리 결제 시스템에 새 기능을 추가해야 해.
세 가지 역할로 나눠서 진행해줘:
  1. 리서처: 현재 payment/ 코드를 분석해서
     아키텍처와 패턴을 파악해줘
  2. 개발자: 리서처 결과를 바탕으로
     환불 기능 구현해줘
  3. 리뷰어: 개발자 코드를 검토하고
     보안 이슈와 엣지케이스 찾아줘
```

## Agent SDK로 Co-work 구현

### 전문가 패널 패턴

여러 전문가 에이전트가 동일한 문제를 각자 분석:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

interface ExpertOpinion {
  role: string;
  analysis: string;
  recommendation: string;
}

async function expertPanel(problem: string): Promise<string> {
  const experts = [
    {
      role: "보안 전문가",
      prompt: `보안 전문가로서 다음 문제를 분석해줘.
        보안 취약점과 위험 요소에 집중해:
        ${problem}`
    },
    {
      role: "성능 전문가",
      prompt: `성능 최적화 전문가로서 다음 문제를 분석해줘.
        병목 지점과 확장성 이슈에 집중해:
        ${problem}`
    },
    {
      role: "UX 전문가",
      prompt: `UX 디자이너로서 다음 문제를 분석해줘.
        사용자 경험과 접근성에 집중해:
        ${problem}`
    }
  ];

  // 모든 전문가가 동시에 분석
  const opinions = await Promise.all(
    experts.map(async (expert) => {
      const response = await query({
        prompt: expert.prompt,
        options: { maxTurns: 8 }
      });
      return {
        role: expert.role,
        analysis: extractText(response)
      } as ExpertOpinion;
    })
  );

  // 코디네이터가 의견 종합
  const synthesis = await query({
    prompt: `다음 세 전문가의 의견을 종합해서
    균형 잡힌 최종 권고안을 작성해줘:
    ${opinions.map(o => `### ${o.role}\n${o.analysis}`).join("\n\n")}
    상충되는 의견은 트레이드오프를 설명하고
    우선순위와 함께 제시해줘.`,
    options: { maxTurns: 5 }
  });

  return extractText(synthesis);
}
```

### 파이프라인 Co-work 패턴

각 에이전트가 이전 에이전트의 작업을 이어받아 개선:

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function writingPipeline(topic: string): Promise<string> {
  // 1단계: 리서처가 자료 수집
  console.log("리서처: 자료 수집 중...");
  const research = await query({
    prompt: `${topic}에 대해 리서치해줘.
      핵심 개념, 최신 트렌드, 주요 데이터를
      구조화해서 정리해줘.`,
    options: {
      maxTurns: 10,
      allowedTools: ["WebSearch", "Read"]
    }
  });
  const researchResult = extractText(research);

  // 2단계: 작가가 초안 작성
  console.log("작가: 초안 작성 중...");
  const draft = await query({
    prompt: `다음 리서치 자료를 바탕으로
    블로그 포스트 초안을 작성해줘.
    독자: 개발자 / 톤: 친근하지만 전문적
    리서치 자료:
    ${researchResult}`,
    options: { maxTurns: 8 }
  });
  const draftResult = extractText(draft);

  // 3단계: 편집자가 다듬기
  console.log("편집자: 교정 및 개선 중...");
  const edited = await query({
    prompt: `다음 블로그 초안을 편집해줘:
    - 명확하지 않은 문장 개선
    - 논리 흐름 점검
    - SEO를 위한 키워드 최적화
    - 독자 참여를 높이는 CTA 추가
    초안:
    ${draftResult}`,
    options: { maxTurns: 6 }
  });

  return extractText(edited);
}
```

## 역할 특화 시스템 프롬프트

각 에이전트에 명확한 페르소나 부여:

```typescript
const agentConfigs = {
  architect: {
    systemPrompt: `당신은 시니어 소프트웨어 아키텍트입니다.
      항상 확장성, 유지보수성, 패턴 일관성을 최우선으로 생각합니다.
      코드 작성보다 설계 결정에 집중하세요.`,
    maxTurns: 5
  },
  developer: {
    systemPrompt: `당신은 풀스택 개발자입니다.
      아키텍처 결정에 따라 실제 구현 코드를 작성합니다.
      테스트 가능하고 읽기 쉬운 코드를 작성하세요.`,
    maxTurns: 20,
    allowedTools: ["Read", "Edit", "Write", "Bash"]
  },
  tester: {
    systemPrompt: `당신은 QA 엔지니어입니다.
      엣지 케이스, 예외 상황, 보안 취약점을 찾는 것이 목표입니다.
      개발자가 놓친 부분을 집중적으로 검토하세요.`,
    maxTurns: 10,
    allowedTools: ["Read", "Glob", "Grep"]
  }
};

async function developFeature(requirement: string) {
  // 1. 아키텍트가 설계
  const designResponse = await query({
    prompt: requirement,
    options: agentConfigs.architect
  });
  const design = extractText(designResponse);

  // 2. 개발자가 구현
  const implementResponse = await query({
    prompt: `다음 아키텍처 설계를 구현해줘:\n${design}`,
    options: agentConfigs.developer
  });
  const implementation = extractText(implementResponse);

  // 3. QA가 검토
  const reviewResponse = await query({
    prompt: `다음 구현 코드를 검토해줘:\n${implementation}`,
    options: agentConfigs.tester
  });

  return {
    design,
    implementation,
    review: extractText(reviewResponse)
  };
}
```

## 충돌 해결 패턴

에이전트 간 의견 충돌을 처리하는 방법:

```typescript
async function resolveConflict(
  agentA: string,
  agentB: string,
  opinions: [string, string]): Promise<string> {

  const mediator = await query({
    prompt: `두 전문가의 의견이 충돌합니다.
    객관적으로 분석하고 최선의 결론을 도출해줘.
    ${agentA}의 의견:
    ${opinions[0]}
    ${agentB}의 의견:
    ${opinions[1]}
    결론 형식:
    1. 각 의견의 타당한 점
    2. 핵심 충돌 지점
    3. 권장 해결책과 이유`,
    options: { maxTurns: 4 }
  });

  return extractText(mediator);
}
```

## Agent Teams (내장 기능)

위의 Agent SDK 기반 구현 외에, Claude Code에는 **내장 Agent Teams 기능**이 있습니다. 코드를 작성하지 않고도 자연어로 멀티에이전트 협업을 요청할 수 있습니다.

> **실험적 기능**
>
> Agent Teams는 현재 실험적 기능입니다. 세션 이어가기(resume), 태스크 조율, 종료 동작에 알려진 제한사항이 있습니다.

### 서브에이전트 vs Agent Teams

| 구분 | 서브에이전트 | Agent Teams |
|------|-----------|-----------|
| **컨텍스트** | 결과만 메인에 반환 | 완전히 독립 |
| **커뮤니케이션** | 메인 에이전트에만 보고 | 팀원 간 직접 메시지 |
| **조율 방식** | 메인 에이전트가 관리 | 공유 작업 목록 + 자율 선택 |
| **적합한 경우** | 결과만 중요한 집중 태스크 | 토론과 협업이 필요한 복잡한 작업 |
| **토큰 비용** | 낮음 (결과만 요약) | 높음 (각 팀원이 독립 인스턴스) |

### 활성화

```json
// settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 팀 아키텍처

| 구성 요소 | 역할 |
|---------|------|
| **팀 리더** | 메인 Claude Code 세션. 팀원 생성, 작업 배정, 결과 조율 |
| **팀원** | 별도의 Claude Code 인스턴스. 배정된 작업을 독립 수행 |
| **작업 목록** | 공유 태스크 리스트. 팀원이 자율적으로 작업을 가져감 |
| **메일박스** | 팀원 간 직접 메시지 시스템 (message + broadcast) |

팀과 태스크는 로컬에 저장됩니다:

* 팀 설정: `~/.claude/teams/{team-name}/config.json`
* 태스크: `~/.claude/tasks/{team-name}/`

### 최적 사용 시나리오

* **리서치와 리뷰**: 여러 팀원이 다른 관점에서 동시에 조사
* **새 모듈/기능**: 각 팀원이 서로 다른 부분을 소유
* **경쟁 가설 디버깅**: 여러 이론을 병렬로 검증하고 수렴
* **크로스 레이어 작업**: 프론트엔드, 백엔드, 테스트를 각각 소유

### 사용 예시

```
> CLI 도구를 설계해야 해. 다른 관점에서 탐색할 Agent Team을 만들어줘:
  - UX 담당 1명
  - 기술 아키텍처 담당 1명
  - 반론을 제기할 비평가 1명
```

Claude가 팀을 생성하고, 팀원을 스폰하며, 공유 태스크 리스트로 작업을 조율합니다.

### 표시 모드

| 모드 | 설명 | 요구사항 |
|-----|------|--------|
| **in-process** | 한 터미널에서 `Shift+Down`으로 전환 | 없음 (기본) |
| **split-panes** | 각 팀원이 별도 패널 | tmux 또는 iTerm2 |
| **auto** | tmux 세션이면 split, 아니면 in-process | - |

```json
// settings.json
{ "teammateMode": "in-process" }
```

```bash
# 세션별 오버라이드
claude --teammate-mode in-process
```

> **Split Pane 제한**
>
> Split-pane 모드는 VS Code 통합 터미널, Windows Terminal, Ghostty에서는 지원되지 않습니다. tmux 또는 iTerm2가 필요합니다.

### 팀원과 직접 소통

각 팀원은 완전한 독립 Claude Code 세션입니다:

**In-process 모드**:

* `Shift+Down`: 팀원 간 전환
* `Enter`: 팀원 세션 진입 → `Esc`로 중단
* `Ctrl+T`: 태스크 리스트 토글

**Split-pane 모드**:

* 패널 클릭으로 직접 상호작용

### 태스크 관리

태스크는 세 가지 상태로 관리됩니다: **pending → in progress → completed**. 태스크 간 의존성도 지원됩니다.

* **리더가 배정**: 특정 팀원에게 태스크 지정
* **자율 선택**: 팀원이 완료 후 다음 미배정+미차단 태스크를 자동 선택
* **파일 락킹**: 여러 팀원이 동시에 같은 태스크를 선택하는 것을 방지

### Plan 승인

복잡하거나 위험한 작업에는 팀원에게 구현 전 계획 승인을 요구할 수 있습니다:

```
인증 모듈을 리팩토링할 아키텍트 팀원을 만들어줘.
변경 전에 계획 승인을 받도록 해.
```

팀원이 계획을 완료하면 리더에게 승인을 요청합니다. 거절 시 피드백과 함께 재계획합니다.

### 팀 정리

```
> 팀을 정리해줘
```

리더를 통해 정리하세요. 팀원이 아직 실행 중이면 먼저 종료해야 합니다.

### 품질 게이트 Hook

```json
{
  "hooks": {
    "TaskCompleted": [{
      "hooks": [{
        "type": "command",
        "command": "npm test -- --related $CHANGED_FILES"
      }]
    }],
    "TeammateIdle": [{
      "hooks": [{
        "type": "command",
        "command": "./scripts/check-remaining-work.sh"
      }]
    }]
  }
}
```

종료 코드 2를 반환하면 팀원에게 피드백이 전달되고 작업을 계속합니다.

### 베스트 프랙티스

* **3~5명의 팀원**으로 시작 (비용 대비 효과 최적)
* 팀원당 **5~6개 태스크** 배정이 적당
* 팀원 간 **파일 소유권을 분리** (같은 파일 동시 수정 방지)
* Worktree와 결합하면 파일 충돌 완전 방지
* 리서치/리뷰 작업부터 시작하고, 익숙해지면 구현 작업으로 확장
* 팀원에게 **충분한 컨텍스트**를 제공 (대화 기록은 상속되지 않음)
* 팀원 모델로 **Sonnet 사용** 권장 (능력과 비용의 균형)
* 주기적으로 진행 상황을 확인하고 방향 수정

### 제한사항

* `/resume`과 `/rewind`는 in-process 팀원을 복원하지 않음
* 태스크 상태가 지연될 수 있어 수동 업데이트가 필요할 때 있음
* 세션당 하나의 팀만 관리 가능
* 중첩 팀 불가 (팀원은 자체 팀을 만들 수 없음)
* 모든 팀원은 리더의 권한 모드로 시작 (스폰 후 개별 변경 가능)

## Co-work 설계 원칙

### 효과적인 Co-work 설계

1. **역할 명확화**: 각 에이전트의 책임 범위를 겹치지 않게 정의
2. **인터페이스 통일**: 에이전트 간 데이터 교환 형식을 표준화
3. **독립성 보장**: 한 에이전트의 실패가 전체를 멈추지 않도록 설계
4. **컨텍스트 요약**: 에이전트 간 전달 내용은 핵심만 압축

### 흔한 실수

* 에이전트 간 데이터를 너무 많이 전달 → 컨텍스트 낭비
* 역할 경계가 모호해서 같은 작업을 중복 수행
* 실패 처리 없이 순차적 의존 → 한 에이전트 실패 시 전체 중단

---

**최종 수정**: 2026년 2월 28일
