<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/worktree-mode -->

# Worktree 병렬 개발

Claude Code를 여러 터미널에서 동시에 실행하면 **같은 파일을 동시에 수정**하는 충돌이 발생합니다. `--worktree` 플래그를 사용하면 각 세션이 **격리된 코드 복사본**에서 작업하므로 충돌 없이 병렬 개발이 가능합니다.

## 핵심 개념

```
프로젝트 루트 (main 브랜치)
├── src/
├── .claude/
│   └── worktrees/
│       ├── feature-auth/      ← 세션 A (worktree-feature-auth 브랜치)
│       │   └── src/
│       └── bugfix-123/        ← 세션 B (worktree-bugfix-123 브랜치)
│           └── src/
```

각 Worktree는:

* 독립된 Git 브랜치 (`worktree-<이름>`)
* 독립된 파일 시스템 복사본
* 독립된 Claude Code 세션

## 사용 방법

### 기본 사용

```bash
# 이름을 지정해서 Worktree 시작
claude --worktree feature-auth

# 또 다른 터미널에서 별도 Worktree
claude --worktree bugfix-123

# 짧은 플래그
claude -w feature-auth

# 이름 자동 생성 (예: bright-running-fox)
claude --worktree
```

### 세션 중 Worktree 전환

대화 중에도 자연어로 요청할 수 있습니다:

```
> worktree에서 작업해줘
> 새 worktree 시작해줘
```

Claude가 자동으로 Worktree를 생성하고 전환합니다.

### 디렉토리 구조

| 항목 | 경로 |
|------|------|
| Worktree 디렉토리 | `<프로젝트>/.claude/worktrees/<이름>/` |
| 브랜치 이름 | `worktree-<이름>` |
| 기반 브랜치 | 기본 원격 브랜치 (보통 `main`) |

> .gitignore에 추가
>
> `.claude/worktrees/`를 `.gitignore`에 추가하세요. Worktree 디렉토리가 실수로 커밋되는 것을 방지합니다.

## 서브에이전트 격리

커스텀 서브에이전트에서도 Worktree 격리를 활용할 수 있습니다:

```yaml
---
name: refactor-agent
isolation: worktree
---

이 에이전트는 코드 리팩토링을 수행합니다.
변경 사항이 없으면 Worktree가 자동으로 정리됩니다.
```

서브에이전트의 Worktree는:

* 변경 없이 종료 → 자동 삭제
* 변경/커밋 존재 → Worktree 경로와 브랜치 반환

## Worktree 정리

세션을 종료하면 Claude가 확인합니다:

* **변경 없음**: Worktree와 브랜치 자동 삭제
* **변경 있음**: 유지/삭제 선택 프롬프트
  * **유지**: 디렉토리와 브랜치 보존 (나중에 `git worktree remove`로 수동 삭제)
  * **삭제**: 커밋되지 않은 변경 포함 모두 삭제

```bash
# 수동 정리
git worktree list                          # 모든 Worktree 확인
git worktree remove .claude/worktrees/feature-auth  # 특정 Worktree 삭제
git branch -d worktree-feature-auth        # 브랜치 삭제
```

## 실전 활용 패턴

### 패턴 1: 기능 + 버그 수정 동시 진행

```bash
# 터미널 1: 새 기능 개발
claude -w feature-payment
> 결제 모듈 구현해줘

# 터미널 2: 긴급 버그 수정
claude -w hotfix-login
> 로그인 세션 만료 버그 수정해줘
```

각각 독립 브랜치에서 작업하므로, 완료 후 `main`에 개별 PR을 생성합니다.

### 패턴 2: 실험적 접근 비교

```bash
# 접근 A: REST API 방식
claude -w approach-rest
> REST API로 알림 시스템 구현해줘

# 접근 B: WebSocket 방식
claude -w approach-websocket
> WebSocket으로 알림 시스템 구현해줘
```

두 결과를 비교한 뒤 더 나은 접근을 선택합니다.

### 패턴 3: Agent Teams와 결합

Agent Teams(Level 5)에서 각 팀원이 별도 Worktree에서 작업하면 파일 충돌 없이 병렬 개발이 가능합니다:

```
팀 리더 (main)
├── 팀원 A → worktree-frontend (UI 개발)
├── 팀원 B → worktree-backend  (API 개발)
└── 팀원 C → worktree-tests    (테스트 작성)
```

## Git 외 VCS 지원

Mercurial, Perforce, SVN 등을 사용하는 경우, Hook으로 커스텀 Worktree 로직을 구현할 수 있습니다:

```json
// .claude/settings.json
{
  "hooks": {
    "WorktreeCreate": [{
      "command": "./scripts/create-worktree.sh $WORKTREE_NAME"
    }],
    "WorktreeRemove": [{
      "command": "./scripts/remove-worktree.sh $WORKTREE_PATH"
    }]
  }
}
```

이 Hook이 설정되면 `--worktree` 플래그가 Git 대신 커스텀 스크립트를 실행합니다.

## 주의사항

> Worktree 간 의존성
>
> 각 Worktree는 독립된 파일 시스템이므로, `npm install`로 설치한 의존성은 공유되지 않습니다. 각 Worktree에서 별도로 의존성을 설치해야 합니다.

* Worktree는 디스크 공간을 추가로 사용합니다 (프로젝트 크기 x Worktree 수)
* `node_modules` 등 무거운 디렉토리가 있으면 생성 시간이 길어질 수 있습니다
* Worktree에서의 메모리(Auto Memory)는 메인 프로젝트와 별도로 관리됩니다

---

**최종 수정**: 2026년 2월 28일
