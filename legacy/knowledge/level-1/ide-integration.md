<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-1/ide-integration -->

# IDE 연동

> 💡 **이 챕터에서 배우는 것**: VS Code Extension 설치, JetBrains 플러그인, IDE 없이 터미널만 사용하는 방법

## 참고

IDE 연동은 선택 사항입니다. Claude Code는 **터미널만으로도 완전히 사용 가능**합니다. IDE 연동을 하면 클릭 한 번으로 실행하거나, 코드와 AI 창을 나란히 볼 수 있어 편리합니다.

---

## VS Code 연동

### 공식 확장 프로그램 설치

1. VS Code 열기
2. 확장 프로그램 마켓플레이스 (`Ctrl+Shift+X` / `Cmd+Shift+X`)
3. **"Claude Code"** 검색
4. Anthropic 공식 확장 프로그램 → **Install**

### VS Code에서 Claude Code 실행

설치 후 두 가지 방법으로 실행할 수 있습니다:

**방법 1: 통합 터미널에서 실행**

```
View → Terminal (Ctrl+` / Ctrl+백틱)
```

터미널에 `claude` 입력

**방법 2: 사이드바 패널로 실행**

* 활동 표시줄(왼쪽)에 Claude 아이콘이 생깁니다
* 클릭하면 Claude Code 패널이 열립니다

### VS Code 권장 설정

`settings.json`에 추가하면 편리합니다:

```json
{
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.defaultProfile.osx": "zsh",
  "terminal.integrated.defaultProfile.windows": "Git Bash",
  "files.autoSave": "afterDelay"
}
```

---

## JetBrains IDE 연동

IntelliJ IDEA, PyCharm, WebStorm, GoLand 등 JetBrains 제품군에서 사용 가능합니다.

### 플러그인 설치

1. **Settings** (`Ctrl+Alt+S` / `Cmd+,`) → **Plugins**
2. Marketplace 탭 → **"Claude Code"** 검색
3. Anthropic 공식 플러그인 → **Install**
4. IDE 재시작

### JetBrains에서 Claude Code 실행

* 우하단 상태 표시줄 → Claude Code 아이콘 클릭
* 또는 **Tools → Claude Code** 메뉴

---

## 터미널만 사용하기 (IDE 없이)

IDE 없이 터미널만으로도 Claude Code의 모든 기능을 사용할 수 있습니다. 특히 서버 환경이나 SSH 접속 시 유용합니다.

```bash
# 프로젝트 폴더로 이동
cd ~/my-project

# Claude Code 시작
claude
```

Claude Code는 현재 디렉토리를 작업 공간으로 인식합니다.

---

## 어떤 방식이 좋을까?

| 상황 | 권장 방식 |
|------|---------|
| 일반 개발 작업 | VS Code + 통합 터미널 |
| JetBrains 헤비 유저 | JetBrains 플러그인 |
| 서버/원격 작업 | 터미널 단독 |
| 처음 시작 | 터미널 단독 (단순함) |

---

## 핵심 정리

* IDE 연동은 선택 사항, 터미널만으로도 모든 기능 사용 가능
* VS Code: 공식 Claude Code 확장 프로그램 설치
* JetBrains: JetBrains Marketplace에서 플러그인 설치
* 항상 **프로젝트 폴더 안에서** `claude` 실행 권장

---

## 다음 단계

→ [첫 번째 실행](/docs/level-1/first-run) — Claude Code를 처음 실행하고 기본 인터페이스를 익혀봅시다

**최종 수정: 2026년 2월 28일**
