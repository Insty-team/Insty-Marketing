<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/custom-skills -->

# Skills 시스템

Skills는 Claude Code에게 **특정 상황에서 따를 지침이나 실행할 워크플로우**를 정의하는 시스템입니다. 슬래시 커맨드(`/commit`, `/review`)로 직접 호출하거나, Claude가 상황에 맞게 자동으로 로드할 수 있습니다.

## SKILL.md 파일 형식

모든 Skill은 `SKILL.md` 파일을 엔트리포인트로 합니다. YAML frontmatter와 마크다운 본문으로 구성됩니다:

```
---
name: explain-code
description: 코드를 시각적 다이어그램과 비유로 설명합니다. "이 코드 어떻게 동작해?"라고 물을 때 사용됩니다.
---

코드를 설명할 때 항상 포함할 것:

1. **비유로 시작**: 코드를 일상적인 것에 비교
2. **다이어그램 그리기**: ASCII 아트로 흐름/구조/관계 시각화
3. **단계별 설명**: 코드가 실행되는 과정을 순서대로
4. **주의점 강조**: 흔한 실수나 오해
```

### 두 가지 콘텐츠 유형

| 유형 | 목적 | 실행 방식 |
|------|------|---------|
| **참조 콘텐츠** | 컨벤션, 패턴, 스타일 가이드 등 | 대화 컨텍스트와 함께 인라인 적용 |
| **태스크 콘텐츠** | 배포, 커밋, 코드 생성 등 단계별 지침 | `/skill-name`으로 직접 호출, 종종 `disable-model-invocation: true` 사용 |

**SKILL.md 크기 제한**

SKILL.md는 500줄 이내로 유지하세요. 상세 참조 자료는 별도 지원 파일로 분리합니다.

## YAML Frontmatter 필드

모든 필드는 선택사항입니다. `description`만 권장됩니다.

| 필드 | 설명 |
|------|------|
| `name` | 표시 이름. 소문자, 숫자, 하이픈만 (최대 64자). 생략 시 디렉토리 이름 사용 |
| `description` | Skill의 용도와 사용 시점. Claude가 자동 호출 여부 판단에 사용 |
| `argument-hint` | 자동완성 힌트. 예: `[issue-number]`, `[filename] [format]` |
| `disable-model-invocation` | `true`면 사용자만 호출 가능 (Claude 자동 호출 차단) |
| `user-invocable` | `false`면 `/` 메뉴에서 숨김 (Claude만 호출 가능) |
| `allowed-tools` | Skill 활성 시 권한 없이 사용할 수 있는 도구 |
| `model` | Skill 활성 시 사용할 모델 |
| `context` | `fork`로 설정하면 서브에이전트에서 격리 실행 |
| `agent` | `context: fork` 시 사용할 에이전트 유형 (`Explore`, `Plan`, `general-purpose`, 커스텀) |
| `hooks` | Skill 라이프사이클에 스코프된 Hook |

### 호출 제어

| Frontmatter | 사용자 호출 | Claude 호출 | 컨텍스트 로딩 |
|-------------|-----------|-----------|-------------|
| (기본값) | O | O | 설명 항상 로드, 호출 시 전체 로드 |
| `disable-model-invocation: true` | O | X | 설명 비로드, 호출 시에만 전체 로드 |
| `user-invocable: false` | X | O | 설명 항상 로드, 호출 시 전체 로드 |

## Skill 디렉토리 구조

```
.claude/skills/
└── my-skill/
    ├── SKILL.md           # 메인 지침 (필수)
    ├── template.md        # Claude가 채울 템플릿
    ├── examples/
    │   └── sample.md      # 기대 출력 예시
    └── scripts/
        └── validate.sh    # Claude가 실행할 스크립트
```

### 저장 위치별 범위

| 위치 | 적용 범위 | 우선순위 |
|------|---------|---------|
| 관리형 설정 | 조직 전체 | 최고 |
| `~/.claude/skills/` | 모든 프로젝트 (개인) | 높음 |
| `.claude/skills/` | 현재 프로젝트 | 중간 |
| 플러그인 `skills/` | 플러그인 활성 시 | 낮음 |

같은 이름의 Skill이 여러 레벨에 있으면 우선순위가 높은 것이 적용됩니다. 플러그인 Skill은 `plugin-name:skill-name` 네임스페이스를 사용하므로 충돌하지 않습니다.

**레거시 호환**

`.claude/commands/` 파일은 여전히 동작하며 같은 frontmatter를 지원합니다. 같은 이름이면 `.claude/skills/`가 우선합니다.

## 문자열 치환

Skill 본문에서 동적 값을 사용할 수 있습니다:

| 변수 | 설명 | 예시 |
|------|------|------|
| `$ARGUMENTS` | 전달된 모든 인수 | `/fix-issue 123` → `$ARGUMENTS` = `123` |
| `$ARGUMENTS[N]` | N번째 인수 (0-based) | `/migrate A B C` → `$ARGUMENTS[1]` = `B` |
| `$N` | `$ARGUMENTS[N]`의 축약형 | `$0`, `$1`, `$2` |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID | 로깅, 세션별 파일 생성 |

```
---
name: fix-issue
description: GitHub 이슈 수정
disable-model-invocation: true
---

GitHub 이슈 $ARGUMENTS를 우리 코딩 표준에 맞게 수정해줘.

1. 이슈 설명 읽기
2. 요구사항 파악
3. 수정 구현
4. 테스트 작성
5. 커밋 생성
```

`/fix-issue 123` 실행 시 `$ARGUMENTS`가 `123`으로 치환됩니다.

**인수 미사용 시**

Skill에 `$ARGUMENTS`가 없으면 Claude Code가 자동으로 `ARGUMENTS: <입력값>`을 본문 끝에 추가합니다.

## 동적 컨텍스트 주입 (`` !`command` ``)

`` !`command` `` 구문은 Skill이 Claude에게 전달되기 **전에** 셸 명령을 실행하고, 그 출력으로 대체합니다:

```
---
name: pr-summary
description: PR 변경사항 요약
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## PR 컨텍스트
- PR diff: !`gh pr diff`
- PR 코멘트: !`gh pr view --comments`
- 변경 파일: !`gh pr diff --name-only`

## 할 일
이 PR을 요약해줘...
```

Claude는 명령어가 아닌 **실제 실행 결과**를 받습니다.

## 서브에이전트 실행 (`context: fork`)

`context: fork`를 설정하면 Skill이 격리된 서브에이전트에서 실행됩니다:

```
---
name: deep-research
description: 주제를 깊이 조사
context: fork
agent: Explore
---

$ARGUMENTS를 깊이 조사해줘:

1. Glob과 Grep으로 관련 파일 찾기
2. 코드 읽고 분석
3. 구체적 파일 참조와 함께 요약
```

서브에이전트는 대화 기록에 접근하지 않고, 결과만 메인 대화에 반환합니다. `agent` 필드로 실행 환경(모델, 도구, 권한)을 결정합니다.

## Agent Skills 오픈 스탠다드

Claude Code Skills는 [Agent Skills](https://agentskills.io) 오픈 스탠다드를 따릅니다. 이 표준은 여러 AI 도구에서 동작합니다. Claude Code는 추가로 호출 제어, 서브에이전트 실행, 동적 컨텍스트 주입을 지원합니다.

## 실전 예시

### 코드 리뷰 Skill

```
---
name: review
description: 코드 리뷰 수행
allowed-tools: Read, Grep, Glob
---

코드 리뷰를 수행해줘:

1. 변경된 파일 파악
2. 보안 취약점 확인
3. 성능 문제 점검
4. 코드 스타일 일관성 확인
5. 구체적 개선 제안 제시
```

### 커밋 Skill

```
---
name: commit
description: 스테이징된 변경사항으로 커밋 생성
disable-model-invocation: true
allowed-tools: Bash(git *)
---

스테이징된 변경사항을 분석하고 적절한 커밋 메시지를 작성해줘:

1. `git diff --staged` 확인
2. Conventional Commits 형식 사용
3. 변경의 "왜"에 집중
```

### 배포 Skill (동적 컨텍스트)

```
---
name: deploy
description: 프로덕션 배포 실행
disable-model-invocation: true
context: fork
---

## 현재 상태
- 현재 브랜치: !`git branch --show-current`
- 최근 커밋: !`git log --oneline -5`
- 테스트 상태: !`npm test 2>&1 | tail -3`

## 배포 절차
$ARGUMENTS 환경에 배포해줘...
```

## Skill 관리

### 생성과 호출

```
/skill-name              # 직접 호출
/skill-name 인수값       # 인수와 함께 호출
/skill-name arg1 arg2    # 여러 인수
```

### 권한으로 제어

```json
{
  "permissions": {
    "allow": ["Skill(commit)"],      // 특정 Skill만 허용
    "deny": ["Skill(deploy *)"]      // 특정 Skill 차단
  }
}
```

### 배포 범위

* **프로젝트**: `.claude/skills/`를 git에 커밋
* **플러그인**: 플러그인의 `skills/` 디렉토리에 패키징
* **관리형**: 조직 전체에 관리형 설정으로 배포

---

**최종 수정**: 2026년 2월 28일
