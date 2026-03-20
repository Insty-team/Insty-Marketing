<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-1/installation -->

# 설치 가이드

> 💡 **이 챕터에서 배우는 것**: Claude Code 설치 전 준비물, OS별 설치 방법, 설치 확인

## 전제 지식

이 챕터를 시작하기 전에 필요한 것:

- 인터넷 연결
- 터미널(명령 프롬프트/PowerShell/Terminal) 기본 사용법

---

## 설치 전 준비물

| 항목 | 버전 | 확인 방법 |
|------|------|---------|
| Node.js | **18 이상** (LTS 권장) | `node --version` |
| npm | Node.js와 함께 설치됨 | `npm --version` |
| Anthropic API 키 | — | [다음 챕터](/docs/level-1/api-key-setup)에서 설명 |

### Node.js 설치 (아직 없다면)

**공식 다운로드**: [nodejs.org](https://nodejs.org) → LTS 버전 선택

#### Windows에서 Node.js 설치

1. [nodejs.org](https://nodejs.org) 접속
2. **LTS** 버전 `.msi` 다운로드
3. 설치 마법사 실행 (기본값 그대로 Next → Next → Install)
4. PowerShell 재시작 후 확인:

```
node --version   # v22.x.x
npm --version    # 10.x.x
```

#### macOS에서 Node.js 설치

Homebrew를 사용하는 방법 (권장):

```bash
# Homebrew가 없다면 먼저 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js 설치
brew install node

# 확인
node --version
npm --version
```

#### Linux(Ubuntu/Debian)에서 Node.js 설치

```bash
# NodeSource 저장소 추가
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -

# 설치
sudo apt-get install -y nodejs

# 확인
node --version
npm --version
```

---

## Claude Code 설치

준비가 됐다면 이 명령 하나로 설치합니다:

```bash
npm install -g @anthropic-ai/claude-code
```

> `-g` 옵션: 전역(global) 설치. 어느 디렉토리에서든 `claude` 명령을 사용할 수 있습니다.

### Windows 사용자 주의사항

Windows PowerShell에서 권한 오류가 날 경우:

```powershell
# PowerShell을 관리자 권한으로 열고 실행
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

또는 **PowerShell 대신 Git Bash** 사용을 권장합니다.

---

## 설치 확인

```bash
claude --version
```

정상 출력 예 (버전 번호는 설치 시점에 따라 다릅니다):

```
1.x.x (Claude Code)
```

---

## 첫 실행 및 API 키 설정

```bash
claude
```

처음 실행하면 API 키를 입력하라는 안내가 나옵니다:

```
Welcome to Claude Code!
Please enter your Anthropic API key to get started.
You can find your API key at https://console.anthropic.com/
API key: sk-ant-...
```

API 키 발급 방법은 [다음 챕터](/docs/level-1/api-key-setup)에서 자세히 설명합니다.

---

## 자주 겪는 설치 문제

### 문제 1: `npm: command not found`

Node.js가 설치되지 않은 상태. 위의 Node.js 설치 과정을 먼저 진행하세요.

### 문제 2: `EACCES: permission denied` (macOS/Linux)

```bash
# npm 전역 디렉토리 권한 문제
# 해결 방법: npm 전역 디렉토리 변경
mkdir ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @anthropic-ai/claude-code
```

### 문제 3: 설치 후 `claude` 명령이 없다고 나올 때

터미널을 완전히 닫고 다시 열어보세요. PATH 환경변수가 새로 적용됩니다.

### 문제 4: 회사 네트워크에서 설치 실패

프록시 설정이 필요할 수 있습니다:

```bash
npm config set proxy http://프록시주소:포트
npm config set https-proxy http://프록시주소:포트
npm install -g @anthropic-ai/claude-code
```

---

## 핵심 정리

- Claude Code는 **Node.js 18+** 필요
- `npm install -g @anthropic-ai/claude-code` 명령으로 설치
- 설치 후 `claude --version`으로 확인
- API 키는 다음 챕터에서 발급

---

## 다음 단계

→ [API 키 설정](/docs/level-1/api-key-setup) — Anthropic Console에서 API 키를 발급하고 설정합니다

**최종 수정: 2026년 2월 28일**
