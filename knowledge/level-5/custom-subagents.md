<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-5/custom-subagents -->

# 커스텀 서브에이전트

커스텀 서브에이전트는 **특정 역할과 도메인에 최적화된 전문 에이전트**입니다. `.claude/agents/` 디렉토리에 마크다운 파일로 정의하며, YAML frontmatter로 도구, 모델, 권한을 세밀하게 제어합니다.

## 파일 형식

YAML frontmatter + 마크다운 본문으로 구성합니다. frontmatter는 설정, 본문은 시스템 프롬프트입니다:

```
---
name: code-reviewer
description: 코드 품질과 보안 모범 사례를 검토합니다
tools: Read, Glob, Grep
model: sonnet
---
당신은 코드 리뷰어입니다. 호출되면 코드를 분석하고
품질, 보안, 모범 사례에 대한 구체적이고 실행 가능한 피드백을 제공하세요.
```

### 시스템 프롬프트

서브에이전트는 전체 Claude Code 시스템 프롬프트가 아닌 **이 마크다운 본문**만 시스템 프롬프트로 받습니다 (작업 디렉토리 같은 기본 환경 정보는 포함).

## YAML Frontmatter 필드

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | O | 고유 식별자. 소문자와 하이픈만 |
| `description` | O | Claude가 위임 판단에 사용 |
| `tools` | - | 사용 가능한 도구. 생략 시 전체 상속. `Task(agent_type)` 구문으로 서브에이전트 생성 제한 |
| `disallowedTools` | - | 차단할 도구 |
| `model` | - | `sonnet`, `opus`, `haiku`, `inherit` (기본: `inherit`) |
| `permissionMode` | - | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | - | 최대 에이전틱 턴 수 |
| `skills` | - | 시작 시 로드할 Skills (전체 콘텐츠 주입) |
| `mcpServers` | - | 사용 가능한 MCP 서버 (이름 참조 또는 인라인 정의) |
| `hooks` | - | 서브에이전트 라이프사이클 Hook |
| `memory` | - | 영속 메모리 범위: `user`, `project`, `local` |
| `background` | - | `true`면 항상 백그라운드 실행 (기본: `false`) |
| `isolation` | - | `worktree`면 격리된 git 워크트리에서 실행 |

### tools 필드 상세

`Task(agent_type)` 구문으로 어떤 서브에이전트를 생성할 수 있는지 제한합니다:

```
tools: Task(worker, researcher), Read, Bash
```

이것은 허용 목록입니다. `Task`를 완전히 생략하면 서브에이전트를 생성할 수 없습니다.

### permissionMode 값

| 모드 | 동작 |
|------|------|
| `default` | 표준 권한 확인 |
| `acceptEdits` | 파일 수정 자동 승인 |
| `dontAsk` | 권한 프롬프트 자동 거부 (명시 허용 도구만 작동) |
| `bypassPermissions` | 모든 권한 검사 건너뜀 (주의) |
| `plan` | 읽기 전용 탐색 모드 |

## 영속 메모리 (Persistent Memory)

`memory` 필드로 서브에이전트에게 세션 간 유지되는 메모리 디렉토리를 부여합니다:

| 범위 | 위치 | 용도 |
|------|------|------|
| `user` | `~/.claude/agent-memory/<name>/` | 모든 프로젝트 공통 (권장) |
| `project` | `.claude/agent-memory/<name>/` | 프로젝트별, git 공유 가능 |
| `local` | `.claude/agent-memory-local/<name>/` | 프로젝트별, git 미추적 |

메모리가 활성화되면:

* 시스템 프롬프트에 메모리 읽기/쓰기 지침 포함
* `MEMORY.md` 처음 200줄이 자동 로드
* Read, Write, Edit 도구가 자동 활성화

```
---
name: code-reviewer
description: 코드 리뷰어 — 이전 리뷰 패턴을 기억합니다
tools: Read, Grep, Glob
memory: user
---
코드를 리뷰할 때 먼저 메모리에서 이전에 발견한 패턴을 확인하세요.
리뷰 완료 후 새로 배운 내용을 메모리에 저장하세요.
```

## 저장 위치와 우선순위

| 위치 | 범위 | 우선순위 |
|------|------|----------|
| `--agents` CLI 플래그 | 현재 세션 | 1 (최고) |
| `.claude/agents/` | 현재 프로젝트 | 2 |
| `~/.claude/agents/` | 모든 프로젝트 | 3 |
| 플러그인 `agents/` | 플러그인 활성 시 | 4 (최저) |

## `/agents` 관리 커맨드

```
/agents
```

인터랙티브 인터페이스에서:

* **보기**: 모든 서브에이전트 (빌트인, 사용자, 프로젝트, 플러그인)
* **생성**: 가이드 설정 또는 Claude 자동 생성
* **편집**: 설정과 도구 접근 수정
* **삭제**: 커스텀 서브에이전트 제거

### CLI 정의 (`--agents`)

세션 한정 서브에이전트를 JSON으로 정의합니다:

```
claude --agents '{
  "code-reviewer": {
    "description": "코드 변경 후 자동 리뷰. 품질, 보안, 모범 사례에 집중.",
    "prompt": "당신은 시니어 코드 리뷰어입니다.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

## 격리 실행 (Worktree)

`isolation: worktree`로 설정하면 서브에이전트가 git 워크트리의 격리된 복사본에서 실행됩니다:

```
---
name: experimental-refactor
description: 실험적 리팩토링을 격리 환경에서 수행
isolation: worktree
tools: Read, Write, Edit, Bash
---
코드를 자유롭게 실험하세요. 변경사항이 없으면 워크트리가 자동 정리됩니다.
```

## Hook 연동

서브에이전트 frontmatter에서 직접 Hook을 정의할 수 있습니다:

```
---
name: safe-executor
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
  Stop:
    - hooks:
        - type: prompt
          prompt: "모든 태스크가 완료됐는지 확인: $ARGUMENTS"
---
```

## 실전 예시

### DB 전문 에이전트

```
---
name: db-expert
description: 데이터베이스 스키마 분석과 쿼리 최적화
tools: Read, Grep, Glob, Bash(psql *)
model: sonnet
memory: project
---
데이터베이스 전문가입니다.
- 스키마 분석 시 인덱스 효율성을 반드시 확인
- 쿼리 최적화 제안 시 EXPLAIN 결과를 근거로 제시
- 마이그레이션 작성 시 롤백 전략 포함
```

### 보안 감사 에이전트

```
---
name: security-auditor
description: 보안 취약점 검사 — OWASP Top 10 중심
tools: Read, Grep, Glob
model: opus
permissionMode: plan
---
보안 감사관입니다. OWASP Top 10 기준으로:
1. SQL 인젝션 가능성 검사
2. XSS 취약점 식별
3. 인증/인가 로직 검증
4. 민감 데이터 노출 확인
5. 구체적 수정 방안 제시
```

### 문서 작성 에이전트

```
---
name: doc-writer
description: API 문서와 README 자동 생성
tools: Read, Glob, Grep, Write, Edit
model: sonnet
skills:
  - doc-template
---
기술 문서 작성자입니다.
코드를 분석하고 명확하고 실용적인 문서를 작성합니다.
doc-template 스킬의 형식을 따릅니다.
```

## 설계 원칙

* **하나의 역할에 집중**: 각 서브에이전트는 하나의 전문 분야
* **상세한 설명**: Claude가 위임 판단에 사용하므로 구체적으로
* **최소 도구 권한**: 필요한 도구만 부여
* **git 커밋**: 프로젝트 서브에이전트는 팀과 공유

---

**최종 수정**: 2026년 2월 28일
