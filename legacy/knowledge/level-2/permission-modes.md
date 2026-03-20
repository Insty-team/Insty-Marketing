<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-2/permission-modes -->

# 권한 모드 | Claude Code 플레이북

## 권한 모드

Claude Code는 파일 수정, 명령어 실행 등 실제 시스템에 영향을 주는 작업을 합니다. 이런 작업을 얼마나 자유롭게 허용할지 결정하는 것이 **권한 시스템**입니다.

## 권한 계층

Claude Code는 도구 유형에 따라 승인 수준이 다릅니다:

| 도구 유형 | 예시 | 승인 필요 | "다시 묻지 않기" 범위 |
|-----------|------|---------|-------------------|
| 읽기 전용 | 파일 읽기, Grep, Glob | 불필요 | - |
| Bash 명령 | 셸 실행 | 필요 | 프로젝트 디렉토리당 영구 저장 |
| 파일 수정 | Edit, Write | 필요 | 세션 종료까지 |

## 5가지 권한 모드

| 모드 | 설명 | 사용 시점 |
|------|------|---------|
| `default` | 도구 첫 사용 시 승인 요청 | 일반적인 개발 작업 |
| `acceptEdits` | 파일 수정 자동 승인 | 신뢰할 수 있는 로컬 개발 |
| `plan` | 분석만 가능, 수정/실행 불가 | 코드 탐색, 아키텍처 검토 |
| `dontAsk` | 사전 승인된 도구만 허용, 나머지 자동 거부 | 제한된 자동화 |
| `bypassPermissions` | 모든 승인 건너뜀 | 격리된 컨테이너/VM만 |

### 실시간 모드 전환

세션 중에 `Shift+Tab` 또는 `Alt+M`으로 모드를 실시간 전환할 수 있습니다:

```
기본 모드 → Shift+Tab → 자동승인 모드 → Shift+Tab → Plan 모드 → Shift+Tab → 기본 모드
```

### 승인 옵션 이해하기

기본 모드에서 Claude가 승인을 요청할 때:

```
Claude: auth/login.ts를 생성하겠습니다. 허용하시겠습니까?
[y] Yes  [n] No  [a] Always allow this type  [d] Don't allow
```

| 선택 | 의미 |
|------|------|
| `y` (Yes) | 이번 한 번만 허용 |
| `n` (No) | 거절, Claude가 다른 방법 시도 |
| `a` (Always) | 이 세션에서 같은 종류 작업 자동 허용 |
| `d` (Don't allow) | 이 세션에서 이 종류 작업 항상 거절 |

> **bypassPermissions 주의**
>
> `bypassPermissions` 모드는 모든 권한 검사를 비활성화합니다. **격리된 환경**(Docker, VM)에서만 사용하세요. 조직 관리자는 managed settings에서 `disableBypassPermissionsMode: "disable"`로 이 모드를 차단할 수 있습니다.

## 권한 규칙 관리

`/permissions` 커맨드로 현재 규칙을 확인하고 관리합니다:

```
/permissions
Allow:
  - Read(*)
  - Edit(/src/**)
  - Bash(npm test *)
Deny:
  - Bash(rm *)
  - Bash(git push *)
```

규칙 평가 순서: **deny → ask → allow**. deny가 항상 우선합니다.

## 권한 규칙 문법

### 기본 형식

`도구명` 또는 `도구명(지정자)` 형식입니다.

```json
{
  "permissions": {
    "allow": [
      "Read",                    // 모든 파일 읽기 허용
      "Bash(npm run *)",         // npm run으로 시작하는 모든 명령
      "Edit(/src/**/*.ts)"       // src 하위 TypeScript 파일만 수정
    ],
    "deny": [
      "Bash(rm *)",              // rm 명령 차단
      "Bash(git push *)"         // git push 차단
    ]
  }
}
```

### Bash 규칙: 와일드카드 매칭

`*`는 글로브 패턴으로 동작합니다. 명령어 어디에서든 사용 가능합니다:

| 규칙 | 매칭 |
|------|------|
| `Bash(npm run build)` | 정확히 `npm run build`만 |
| `Bash(npm run *)` | `npm run test`, `npm run lint` 등 |
| `Bash(* --version)` | `node --version`, `npm --version` 등 |
| `Bash(git * main)` | `git checkout main`, `git merge main` 등 |

> **공백+\* vs \***
>
> `Bash(ls *)`는 `ls -la`에 매칭되지만 `lsof`에는 매칭되지 않습니다. 공백이 단어 경계를 강제합니다. `Bash(ls*)`는 둘 다 매칭됩니다.

> **셸 연산자 인식**
>
> Claude Code는 `&&` 같은 셸 연산자를 인식합니다. `Bash(safe-cmd *)`는 `safe-cmd && dangerous-cmd`를 허용하지 않습니다.

### Read/Edit 규칙: gitignore 스타일 패턴

파일 경로 규칙은 gitignore 스펙을 따릅니다:

| 패턴 | 의미 | 예시 |
|------|------|------|
| `//path` | 파일시스템 절대 경로 | `Read(//Users/alice/secrets/**)` |
| `~/path` | 홈 디렉토리 기준 | `Read(~/Documents/*.pdf)` |
| `/path` | 프로젝트 루트 기준 | `Edit(/src/**/*.ts)` |
| `path` | 현재 디렉토리 기준 | `Read(*.env)` |

```json
{
  "permissions": {
    "allow": [
      "Edit(/docs/**)",          // 프로젝트 docs/ 하위만 수정 허용
      "Read(~/.zshrc)"           // 홈 디렉토리 .zshrc 읽기 허용
    ],
    "deny": [
      "Read(.env)",              // .env 파일 읽기 차단
      "Edit(//etc/*)"            // /etc/ 수정 차단
    ]
  }
}
```

> **\* vs \*\***
>
> `*`는 한 디렉토리 내 파일만 매칭, `**`는 하위 디렉토리까지 재귀적으로 매칭합니다.

### MCP 도구 규칙

```json
{
  "permissions": {
    "allow": [
      "mcp__puppeteer",                       // puppeteer 서버의 모든 도구
      "mcp__github__github_list_repos"         // github 서버의 특정 도구만
    ]
  }
}
```

### 서브에이전트(Task) 규칙

```json
{
  "permissions": {
    "deny": [
      "Task(Explore)"           // Explore 서브에이전트 비활성화
    ]
  }
}
```

## settings.json 계층

권한 규칙은 여러 위치에 정의할 수 있으며, 우선순위는:

```
Managed (조직) → CLI 인수 → Local 프로젝트 → Shared 프로젝트 → User 전역
```

| 위치 | 파일 | 우선순위 |
|------|------|---------|
| 조직 관리형 | MDM/서버 정책 | 최고 |
| CLI 인수 | `--allowedTools`, `--disallowedTools` | 높음 |
| 로컬 프로젝트 | `.claude/settings.local.json` | 중간 |
| 공유 프로젝트 | `.claude/settings.json` | 중간 |
| 전역 사용자 | `~/.claude/settings.json` | 낮음 |

프로젝트 설정이 사용자 설정보다 우선합니다. 사용자 settings에서 허용하더라도 프로젝트 settings에서 거부하면 차단됩니다.

## 추가 디렉토리 접근

기본적으로 Claude는 실행 디렉토리의 파일만 접근합니다. 추가 디렉토리를 열려면:

```bash
# 시작 시 추가
claude --add-dir /path/to/other-project

# 세션 중 추가
/add-dir /path/to/other-project
```

## 샌드박스와의 관계

권한(permissions)과 샌드박스(sandboxing)는 상호 보완적입니다:

| | 권한 | 샌드박스 |
|---|------|---------|
| **적용 대상** | 모든 도구 | Bash 명령만 |
| **동작** | Claude의 도구 사용 제어 | OS 수준 파일/네트워크 격리 |
| **방어** | Claude의 의사결정 제한 | 프롬프트 인젝션 우회 방지 |

둘을 함께 사용하면 **심층 방어(defense-in-depth)**를 구현할 수 있습니다.

## 모드 선택 가이드

```
지금 뭘 하려고?
│
├─ 새 코드베이스 탐색/이해
│   → Plan 모드 (읽기 전용)
│
├─ 혼자 로컬에서 빠르게 개발
│   → acceptEdits 또는 기본 모드 (git 커밋 먼저)
│
├─ 팀 프로젝트, 중요한 코드
│   → 기본 모드 + 프로젝트 settings.json에 규칙 정의
│
├─ CI/CD, 자동화 스크립트
│   → 헤드리스 모드 + allowedTools 지정
│
└─ 격리된 Docker/VM 테스트 환경
    → bypassPermissions (주의!)
```

## 실전 설정 예시

### 안전한 개발 환경

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Edit(/src/**)",
      "Bash(npm test *)",
      "Bash(npm run lint *)",
      "Bash(git diff *)",
      "Bash(git status *)",
      "Bash(git log *)"
    ],
    "deny": [
      "Bash(rm *)",
      "Bash(git push *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Edit(*.env)"
    ]
  }
}
```

### CI/CD 환경 (헤드리스)

```bash
claude -p "코드 리뷰해줘" \
  --allowedTools "Read,Grep,Glob" \
  --disallowedTools "Bash,Edit,Write"
```

---

**최종 수정:** 2026년 2월 28일

이 페이지에 오류가 있나요? [오류 제보하기 →](https://forms.gle/Mj4zGLjxJJnVeTECA)
