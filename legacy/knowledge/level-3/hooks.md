<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/hooks -->

# Hooks 시스템 | Claude Code 플레이북

## Hooks란 무엇인가

Claude Code의 라이프사이클 특정 시점에서 **셸 명령어, LLM 프롬프트, 또는 에이전트를 자동으로 실행**할 수 있게 해주는 시스템입니다. 테스트 자동 실행, 포맷팅, 알림, 로깅, 보안 검증 등 반복 작업을 코딩 워크플로우에 내장할 수 있습니다.

Claude Code가 파일을 수정하거나 명령을 실행할 때, 그 동작에 "끼어들어" 추가 작업을 수행할 수 있습니다.

```
Claude가 파일 수정 요청 받음
    ↓
[PreToolUse Hook 실행] ← 수정 전에 실행 (차단 가능)
    ↓
Claude가 파일 수정
    ↓
[PostToolUse Hook 실행] ← 수정 후에 실행 (피드백 제공)
    ↓
다음 작업 진행
```

## 16가지 Hook 이벤트

| Hook 이벤트 | 실행 시점 | 차단 가능 |
|---|---|---|
| `SessionStart` | 세션 시작 또는 재개 시 | - |
| `UserPromptSubmit` | 사용자 프롬프트 제출 시 (처리 전) | O |
| `PreToolUse` | 도구 실행 직전 | O |
| `PermissionRequest` | 권한 대화상자 표시 시 | O |
| `PostToolUse` | 도구 실행 성공 후 | - |
| `PostToolUseFailure` | 도구 실행 실패 후 | - |
| `Notification` | 알림 발송 시 | - |
| `SubagentStart` | 서브에이전트 생성 시 | - |
| `SubagentStop` | 서브에이전트 완료 시 | O |
| `Stop` | Claude 응답 완료 시 | O |
| `TeammateIdle` | Agent Teams 팀원이 유휴 전환 시 | O |
| `TaskCompleted` | 태스크 완료 마킹 시 | O |
| `ConfigChange` | 설정 파일 변경 시 | O |
| `WorktreeCreate` | 워크트리 생성 시 | O |
| `WorktreeRemove` | 워크트리 제거 시 | - |
| `PreCompact` | 컨텍스트 압축 직전 | - |
| `SessionEnd` | 세션 종료 시 | - |

## 4가지 Hook 유형

### Command Hook (셸 명령)

가장 기본적인 유형입니다. 셸 명령을 실행하고 stdin으로 JSON 입력을 받습니다.

```json
{
  "type": "command",
  "command": "npx prettier --write \"$CLAUDE_PROJECT_DIR/src\""
}
```

### Prompt Hook (LLM 평가)

Claude 모델에 프롬프트를 보내 yes/no 결정을 받습니다. 코드를 작성하지 않고도 지능적인 검증이 가능합니다.

```json
{
  "type": "prompt",
  "prompt": "이 변경이 모든 태스크를 완료했는지 평가해줘: $ARGUMENTS",
  "timeout": 30
}
```

LLM은 `{"ok": true}` 또는 `{"ok": false, "reason": "이유"}` 형식으로 응답합니다.

### Agent Hook (에이전트 검증)

서브에이전트를 생성하여 파일 읽기, 코드 검색 등 도구를 사용한 다단계 검증을 수행합니다.

```json
{
  "type": "agent",
  "prompt": "모든 단위 테스트가 통과하는지 테스트 스위트를 실행하고 결과를 확인해줘. $ARGUMENTS",
  "timeout": 120
}
```

### HTTP Hook (외부 엔드포인트)

외부 HTTP 엔드포인트로 직접 POST 요청을 보냅니다. Slack webhook, 모니터링 서비스, 로깅 시스템 등과 연동할 때 셸 스크립트 없이 바로 연결할 수 있습니다.

```json
{
  "type": "http",
  "url": "https://hooks.slack.com/services/T00/B00/xxxxx",
  "timeout": 30
}
```

Hook 이벤트의 JSON 입력이 HTTP POST body로 전송됩니다.

**지원 이벤트**: Prompt/Agent Hook은 `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `TaskCompleted`에서만 사용 가능합니다. 나머지 이벤트는 Command/HTTP Hook만 지원합니다.

## 설정 방법

Hooks는 `settings.json`에서 3단계 중첩 구조로 설정합니다:

1. **Hook 이벤트** 선택 (예: `PostToolUse`)
2. **Matcher** 패턴으로 필터링 (예: "Write|Edit 도구만")
3. **Hook 핸들러** 정의 (실행할 명령/프롬프트)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$CLAUDE_PROJECT_DIR/src\""
          }
        ]
      }
    ]
  }
}
```

### Hook 설정 위치

| 위치 | 범위 | 공유 |
|---|---|---|
| `~/.claude/settings.json` | 모든 프로젝트 | 로컬 머신만 |
| `.claude/settings.json` | 단일 프로젝트 | git 커밋 가능 |
| `.claude/settings.local.json` | 단일 프로젝트 | gitignored |
| 관리형 정책 | 조직 전체 | 관리자 제어 |
| 플러그인 `hooks/hooks.json` | 플러그인 활성 시 | 플러그인에 번들 |
| Skills/Agent frontmatter | 컴포넌트 활성 시 | 컴포넌트 파일 내 |

### `/hooks` 인터랙티브 메뉴

```
/hooks
```

설정 파일을 직접 편집하지 않고도 Hook을 확인·추가·삭제할 수 있습니다. 각 Hook에는 소스가 표시됩니다: `[User]`, `[Project]`, `[Local]`, `[Plugin]`.

## Matcher 패턴

`matcher`는 정규식으로, 어떤 조건에서 Hook이 실행될지 결정합니다. `"*"`, `""`, 또는 생략하면 모든 경우에 실행됩니다.

### 이벤트별 매칭 대상

| 이벤트 | 매칭 대상 | 예시 |
|---|---|---|
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest` | 도구 이름 | `Bash`, `Edit\|Write`, `mcp__.*` |
| `SessionStart` | 세션 시작 방법 | `startup`, `resume`, `clear`, `compact` |
| `SessionEnd` | 종료 이유 | `clear`, `logout`, `prompt_input_exit` |
| `Notification` | 알림 유형 | `permission_prompt`, `idle_prompt` |
| `SubagentStart`, `SubagentStop` | 에이전트 유형 | `Bash`, `Explore`, `Plan` |
| `ConfigChange` | 설정 소스 | `user_settings`, `project_settings` |
| `PreCompact` | 트리거 방식 | `manual`, `auto` |
| 기타 (Stop, UserPromptSubmit 등) | 매칭 미지원 | 항상 실행 |

### MCP 도구 매칭

MCP 도구는 `mcp__<서버>__<도구>` 형식으로 일반 도구와 동일하게 매칭합니다:

```
"matcher": "mcp__memory__.*"         // memory 서버의 모든 도구
"matcher": "mcp__.*__write.*"        // 모든 서버의 write 관련 도구
```

## JSON 입출력

Hook은 **stdin으로 JSON** 입력을 받고, **stdout으로 JSON** 결과를 반환합니다.

### 공통 입력 필드

모든 이벤트가 받는 기본 필드:

| 필드 | 설명 |
|---|---|
| `session_id` | 세션 ID |
| `transcript_path` | 대화 트랜스크립트 경로 |
| `cwd` | 현재 작업 디렉토리 |
| `permission_mode` | 현재 권한 모드 |
| `hook_event_name` | 발생한 이벤트 이름 |

PreToolUse 예시:

```json
{
  "session_id": "abc123",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" }
}
```

### 종료 코드

| 종료 코드 | 의미 |
|---|---|
| `0` | 성공 — stdout의 JSON이 처리됨 |
| `2` | 차단 — stderr 메시지가 Claude에게 전달됨 |
| 기타 | 비차단 에러 — 실행 계속 |

### JSON 출력 필드

```json
{
  "continue": false,
  "stopReason": "빌드 실패. 에러 수정 후 계속하세요",
  "suppressOutput": false,
  "systemMessage": "사용자에게 보여줄 경고"
}
```

| 필드 | 설명 |
|---|---|
| `continue` | `false`면 Claude 실행 완전 중단 |
| `stopReason` | `continue: false` 시 사용자에게 표시 |
| `suppressOutput` | `true`면 verbose 출력 숨김 |
| `systemMessage` | 사용자에게 표시할 경고 |

## 주요 이벤트 상세

### SessionStart

세션 시작 시 실행됩니다. 개발 컨텍스트 로딩, 환경변수 설정에 유용합니다.

#### CLAUDE_ENV_FILE — 환경변수 영속화

`SessionStart` Hook에서만 사용 가능한 `CLAUDE_ENV_FILE` 환경변수로, Hook에서 설정한 환경변수를 세션 내 모든 Bash 명령에서 사용할 수 있습니다:

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

#### 컨텍스트 주입

stdout에 출력하거나 JSON의 `additionalContext` 필드로 Claude에게 추가 컨텍스트를 제공할 수 있습니다:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "현재 이슈: #42, 마지막 배포: 2시간 전"
  }
}
```

### PreToolUse

도구 실행 전에 실행됩니다. **allow**, **deny**, **ask** 결정이 가능합니다:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "rm -rf 명령은 Hook에 의해 차단됨"
  }
}
```

| 결정 | 의미 |
|---|---|
| `allow` | 권한 시스템 우회, 바로 실행 |
| `deny` | 도구 호출 차단, 이유를 Claude에게 전달 |
| `ask` | 사용자에게 확인 프롬프트 표시 |

`updatedInput`으로 도구 입력을 수정할 수도 있습니다:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": { "command": "npm run lint -- --fix" }
  }
}
```

### PostToolUse

도구 실행 성공 후 실행됩니다. 도구 결과에 대한 피드백을 Claude에게 제공할 수 있습니다.

```json
{
  "decision": "block",
  "reason": "린트 에러 발견. 수정 후 계속하세요"
}
```

### Stop

Claude 응답 완료 시 실행됩니다. `decision: "block"`으로 Claude가 멈추지 않고 계속 작업하게 할 수 있습니다.

```json
{
  "decision": "block",
  "reason": "테스트가 아직 실패합니다. 모든 테스트를 통과시킨 후 종료하세요"
}
```

**무한 루프 방지**: Stop Hook은 `stop_hook_active` 필드를 확인하세요. 이미 Stop Hook에 의해 계속 실행 중이면 `true`입니다. 이를 무시하면 Claude가 무한히 실행될 수 있습니다.

### SubagentStart / SubagentStop

서브에이전트의 생성과 완료를 감지합니다. matcher로 에이전트 유형 필터링이 가능합니다:

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "Explore",
        "hooks": [{
          "type": "command",
          "command": "echo 'Explore 에이전트 시작' >> ~/agent-log.txt"
        }]
      }
    ]
  }
}
```

### TeammateIdle / TaskCompleted

Agent Teams에서 팀원이 유휴 전환되거나 태스크가 완료될 때 실행됩니다. 품질 게이트로 활용할 수 있습니다:

```bash
#!/bin/bash
# TaskCompleted Hook — 테스트 통과 시에만 태스크 완료 허용
if ! npm test 2>&1; then
  echo "테스트 실패. 테스트를 수정한 후 완료하세요." >&2
  exit 2
fi
exit 0
```

### WorktreeCreate / WorktreeRemove

`--worktree` 또는 `isolation: "worktree"` 사용 시 실행됩니다. Git 외 VCS(SVN, Perforce 등)를 사용하는 경우, 기본 git 워크트리 동작을 대체할 수 있습니다.

### ConfigChange

세션 중 설정 파일이 변경될 때 실행됩니다. 보안 감사 로깅이나 비인가 설정 변경 차단에 유용합니다.

## 비동기 Hook (Async)

`"async": true`로 설정하면 Hook이 백그라운드에서 실행되어 Claude를 차단하지 않습니다:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests-async.sh",
            "async": true,
            "timeout": 300
          }
        ]
      }
    ]
  }
}
```

비동기 Hook은 결과가 다음 대화 턴에 전달됩니다. 의사결정(block/allow)은 불가능합니다. Command Hook만 지원합니다.

## Skills/Agent에서의 Hook

Skills와 서브에이전트의 YAML frontmatter에서 직접 Hook을 정의할 수 있습니다. 해당 컴포넌트가 활성화된 동안만 실행됩니다:

```yaml
---
name: secure-operations
description: 보안 검증이 포함된 작업 수행
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
---
```

## 환경변수 레퍼런스

| 변수명 | 설명 |
|---|---|
| `$CLAUDE_PROJECT_DIR` | 프로젝트 루트 경로 |
| `${CLAUDE_PLUGIN_ROOT}` | 플러그인 루트 디렉토리 |
| `$CLAUDE_ENV_FILE` | 환경변수 영속화 파일 (SessionStart만) |
| `$CLAUDE_CODE_REMOTE` | 원격 웹 환경에서 `"true"` |

**프로젝트 스크립트 참조**: Hook 스크립트를 프로젝트에 포함할 때는 `$CLAUDE_PROJECT_DIR`를 사용하면 작업 디렉토리와 무관하게 올바른 경로를 참조합니다:

```json
"command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
```

## 실전 예제

### 파일 저장 시 자동 포맷팅

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$(cat | jq -r '.tool_input.file_path')\" 2>/dev/null"
          }
        ]
      }
    ]
  }
}
```

### 위험한 명령 차단

```bash
#!/bin/bash
# .claude/hooks/block-rm.sh
COMMAND=$(jq -r '.tool_input.command')
if echo "$COMMAND" | grep -q 'rm -rf'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "rm -rf 명령은 Hook에 의해 차단되었습니다"
    }
  }'
else
  exit 0
fi
```

### 작업 완료 시 데스크톱 알림 (macOS)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude 작업 완료\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### 작업 완료 시 데스크톱 알림 (Windows)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -Command \"[System.Windows.Forms.MessageBox]::Show('Claude 작업 완료')\""
          }
        ]
      }
    ]
  }
}
```

### Prompt Hook으로 Stop 검증

코드 작성 없이 LLM으로 태스크 완료 여부를 평가:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "대화를 분석하여 다음을 판단해줘: 1) 모든 요청 태스크가 완료됐는지 2) 해결되지 않은 에러가 있는지 3) 후속 작업이 필요한지. $ARGUMENTS",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### 권장 Hook 구성

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$(cat | jq -r '.tool_input.file_path')\" 2>/dev/null; npx eslint \"$(cat | jq -r '.tool_input.file_path')\" --fix --quiet 2>&1 | head -10"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo \"[$(date '+%H:%M:%S')] 작업 완료\" >> ~/.claude-sessions.log"
          }
        ]
      }
    ]
  }
}
```

## 주의사항

### Hook 보안

Hook은 시스템 사용자의 **전체 권한**으로 실행됩니다.

- 셸 변수는 항상 따옴표로 감싸세요 (`"$VAR"`)
- 파일 경로에서 `..`(경로 탐색)를 차단하세요
- `.env`, `.git/`, 키 파일 같은 민감 파일을 피하세요
- 신뢰할 수 없는 프로젝트의 `.claude/settings.json`을 그대로 적용하지 마세요

### Hook 성능

Hook 명령이 오래 걸리면 Claude Code 응답이 느려집니다. 긴 작업은 `"async": true`로 백그라운드 실행하세요.

### 디버그

`claude --debug`로 Hook 실행 상세 로그를 확인할 수 있습니다. `Ctrl+O`로 verbose 모드를 토글하면 트랜스크립트에서 Hook 진행 상황을 볼 수 있습니다.

---

**다음 챕터**: [MCP 서버 연결 →](/docs/level-3/mcp-servers)

**최종 수정**: 2026년 2월 28일
