<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-1/api-key-setup -->

# API 키 설정

> 💡 **이 챕터에서 배우는 것**: API 키 발급, 안전한 설정 방법, 요금제 선택 가이드

## 전제 지식

[설치 가이드](/docs/level-1/installation)를 먼저 완료해야 합니다.

---

## API 키란?

API 키는 Claude AI 서비스에 접근하기 위한 **인증 암호**입니다. Claude Code가 Anthropic 서버와 통신할 때 사용합니다.

> **중요**: API 키는 절대 공개 저장소(GitHub 등)에 올리지 마세요. 유출 시 요금이 청구될 수 있습니다.

---

## API 키 발급 방법

### 1단계: Anthropic Console 접속

[console.anthropic.com](https://console.anthropic.com) 접속 → 계정 생성 또는 로그인

### 2단계: API Keys 메뉴 이동

좌측 사이드바 → **API Keys** 클릭

### 3단계: 새 API 키 생성

**Create Key** 버튼 클릭 → 키 이름 입력 (예: `claude-code-personal`) → **Create Key**

### 4단계: API 키 복사

생성된 키(`sk-ant-api03-...`)를 복사합니다. **이 화면을 벗어나면 다시 볼 수 없으니** 안전한 곳에 보관하세요.

---

## API 키 설정 방법

### 방법 1: Claude Code 대화형 설정 (권장)

처음 실행 시 API 키 입력 프롬프트가 나타납니다.

```bash
claude
# 복사한 키를 붙여넣고 Enter
```

### 방법 2: 환경변수로 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
claude
```

### 방법 3: 셸 설정 파일에 영구 저장

**macOS (zsh 사용 시, 기본 셸):**

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc
```

**macOS/Linux (bash 사용 시):**

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.bashrc
source ~/.bashrc
```

**Windows PowerShell:**

```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-api03-...", "User")
```

---

## 요금제 이해하기

Claude Code는 Anthropic API를 사용하므로 사용량에 따라 비용이 발생합니다.

### 가격 구조 (2026년 기준)

| 모델 | 가격 | 특징 |
|------|------|------|
| Claude Haiku | 저렴 | 빠름, 간단한 작업 |
| Claude Sonnet | 중간 | 균형, **기본값** |
| Claude Opus | 고가 | 최고 성능 |

> 정확한 가격은 [Anthropic 공식 요금 페이지](https://www.anthropic.com/pricing)를 확인하세요.

### 실제 사용량 예시

일반적인 개발 세션(30분):

* 소규모 버그 수정: **$0.01 ~ $0.05**
* 새 기능 구현: **$0.10 ~ $0.50**
* 대규모 리팩토링: **$0.50 ~ $2.00**

### 비용 관리 팁

1. **크레딧 한도 설정**: Console → Settings → Limits에서 월별 사용 한도 설정
2. **Haiku 모델 사용**: 간단한 작업은 Haiku로 (`/model claude-haiku-4-5-20251001`)
3. **캐싱 활용**: 동일 컨텍스트 반복 시 프롬프트 캐싱으로 최대 90% 절감

---

## 무료로 시작하는 방법

### Claude.ai 구독자 (Max 플랜)

Claude.ai Max 구독자는 Claude Code를 추가 비용 없이 사용할 수 있습니다.

```bash
claude
# "Login with Claude.ai" 옵션 선택
```

### API 크레딧 방식

Anthropic Console에서 카드를 등록하고, 최소 $5부터 충전해서 시작할 수 있습니다.

---

## 보안 모범 사례

`.gitignore`에 반드시 추가:

```
.env
*.env
```

**절대 하지 말아야 할 것:**

* API 키를 코드에 하드코딩
* GitHub, GitLab 등 공개 저장소에 키 업로드

**만약 키가 유출됐다면:**

1. 즉시 Console → API Keys → 해당 키 비활성화
2. 새 키 발급
3. 모든 환경에서 키 교체

---

## 핵심 정리

* API 키는 [console.anthropic.com](https://console.anthropic.com)에서 발급
* 환경변수 `ANTHROPIC_API_KEY`로 설정하는 것이 안전
* 사용량에 따라 비용 발생 → 월 한도 설정 권장
* Claude.ai Max 플랜 구독자는 추가 비용 없음

---

## 다음 단계

→ [IDE 연동](/docs/level-1/ide-integration) — VS Code와 JetBrains에서 Claude Code를 더 편리하게 사용하는 방법

**최종 수정: 2026년 2월 28일**
