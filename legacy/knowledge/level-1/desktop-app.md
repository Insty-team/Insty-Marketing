<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-1/desktop-app -->

# Desktop 앱

CLI가 익숙하지 않거나 시각적인 작업 환경을 선호한다면, **Claude Code Desktop 앱**을 사용할 수 있습니다. CLI와 동일한 엔진을 GUI로 감싼 것으로, 비주얼 diff, 앱 프리뷰, 병렬 세션 같은 추가 기능을 제공합니다.

---

## CLI vs Desktop

| 기능 | CLI | Desktop |
|------|-----|---------|
| 파일 수정/명령 실행 | O | O |
| CLAUDE.md, MCP, Hooks, Skills | O | O (공유) |
| 비주얼 diff 리뷰 | - | O |
| 앱 프리뷰 (내장 브라우저) | - | O |
| 이미지/PDF 첨부 | - | O |
| 병렬 세션 (자동 Worktree) | 수동 | O (자동) |
| @파일 자동완성 | - | O |
| 헤드리스/자동화 | O | - |
| Agent Teams | O | - |
| Bedrock/Vertex/Foundry | O | - |
| Linux | O | - |

### 설정 공유

Desktop과 CLI는 CLAUDE.md, MCP 서버(`~/.claude.json`, `.mcp.json`), Hooks, Skills, settings를 공유합니다. 어느 쪽에서 설정해도 양쪽에 적용됩니다. 단, `claude_desktop_config.json`(Chat 앱용)은 별도입니다.

---

## 시작하기

### 1. 설치

Claude Desktop 앱에서 **Code** 탭으로 접근합니다:

* **macOS**: [claude.ai/download](https://claude.ai/download)에서 다운로드 (Apple Silicon 필수, Intel Mac은 Code 탭 미지원)
* **Windows**: 같은 링크에서 다운로드 (ARM64 완전 지원)

Pro, Max, Team, Enterprise 플랜이 필요합니다.

### 2. 세션 시작 전 설정

세션을 시작하기 전에 4가지를 설정합니다:

| 설정 | 설명 |
|------|------|
| **환경** | Local(내 PC), Remote(클라우드), SSH(원격 서버) |
| **프로젝트 폴더** | Claude가 작업할 디렉토리 또는 리포지토리 |
| **모델** | Sonnet, Opus, Haiku 중 선택 (세션 시작 후 변경 불가) |
| **권한 모드** | Claude의 자율성 수준 (세션 중 변경 가능) |

### 3. 프롬프트 입력

* 프롬프트 박스에 작업을 입력하고 `Enter`
* `@파일명`으로 파일을 컨텍스트에 추가 (자동완성 지원)
* 이미지, PDF를 드래그&드롭 또는 첨부 버튼으로 추가
* 작업 중 언제든 중단 버튼이나 수정 입력으로 방향 전환

---

## 핵심 기능

### 앱 프리뷰

Desktop은 dev 서버를 자동으로 시작하고 내장 브라우저로 결과를 보여줍니다:

* Claude가 코드를 수정하면 자동으로 변경 확인 (스크린샷, DOM 검사, 클릭, 폼 입력)
* 쿠키와 localStorage가 재시작 후에도 유지
* **Preview** 드롭다운에서 서버 설정 편집 가능

프리뷰 서버 설정은 `.claude/launch.json`에 저장합니다:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "web",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 3000
    }
  ]
}
```

### 비주얼 Diff 리뷰

코드 변경사항을 파일별로 시각적으로 검토합니다:

* 특정 줄에 인라인 코멘트 추가
* `Cmd+Enter`(macOS) / `Ctrl+Enter`(Windows)로 코멘트 일괄 제출
* **Review code** 버튼으로 Claude에게 변경사항 평가 요청

### PR 모니터링

PR을 열면 CI 상태 바가 나타납니다:

* **Auto-fix**: CI 체크 실패 시 Claude가 자동 수정
* **Auto-merge**: 모든 체크 통과 시 자동 머지

GitHub CLI(`gh`)가 설치되고 인증되어 있어야 합니다.

### 병렬 세션

**+ New session**으로 여러 작업을 동시에 진행합니다. Git 리포지토리에서는 각 세션이 자동으로 Worktree로 격리되어 서로 영향을 주지 않습니다.

---

## 환경별 특징

| 환경 | 특징 |
|------|------|
| **Local** | 셸 환경변수 상속, Extended Thinking 기본 활성 |
| **Remote** | 앱 닫아도 백그라운드 실행, 구독에 포함 (추가 비용 없음) |
| **SSH** | 원격 머신에서 실행, Claude Code가 원격에 설치되어 있어야 함 |

---

## Connectors

프롬프트 박스의 **+** → **Connectors**에서 외부 도구를 연결합니다:

* GitHub, Slack, Linear, Notion, Google Calendar 등
* Remote 세션에서는 사용 불가

---

## 슬래시 커맨드와 플러그인

* `/`를 입력하면 빌트인 커맨드, 커스텀 Skills, 플러그인 Skills 표시
* **+** → **Plugins**에서 플러그인 설치/관리

---

## 다른 환경으로 전환

툴바 오른쪽 하단의 **Continue in** 메뉴에서:

* Claude Code on the Web으로 이동
* 지원되는 IDE에서 열기

---

## 핵심 정리

* Desktop은 CLI와 동일한 엔진 + 시각적 UI
* 비주얼 diff, 앱 프리뷰, 병렬 세션이 추가 장점
* CLI와 설정(CLAUDE.md, MCP, Hooks)을 공유
* macOS(Apple Silicon) 또는 Windows(ARM64) 필요

**최종 수정: 2026년 2월 28일**
