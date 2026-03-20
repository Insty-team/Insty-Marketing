<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/remote-control -->

# Remote Control | Claude Code 플레이북

## Remote Control

데스크톱에서 시작한 Claude Code 세션을 스마트폰이나 태블릿에서 이어서 사용할 수 있는 기능입니다. 모바일 기기는 "리모컨" 역할을 하며, 코드 실행은 로컬 머신에서 계속됩니다.

## 작동 방식

```
로컬 PC (Claude Code 실행)
    ↕ HTTPS
Anthropic 릴레이 (메시지 라우팅)
    ↕ HTTPS
모바일/브라우저 (입력 & 출력)
```

- 모든 파일, MCP 서버, SSH 키가 내 컴퓨터에 유지됩니다
- 아웃바운드 전용 연결 (인바운드 포트 불필요)
- 모든 통신은 TLS로 암호화됩니다
- 기기가 슬립해도 자동 재연결됩니다

## 시작하기

### 방법 1: 전용 세션 시작

```
claude remote-control
```

세션 URL과 QR 코드가 표시됩니다.

### 방법 2: 기존 세션에서 전환

```
/rc
/remote-control
/mobile
```

### 방법 3: 모든 세션에서 활성화

```
/config
```

설정에서 Remote Control을 기본 활성화할 수 있습니다.

## 모바일에서 접근

- QR 코드를 스캔합니다
- 세션 URL을 직접 열 수 있습니다
- Claude 앱에서 세션을 찾을 수 있습니다 (초록색 온라인 표시)

## 보안 참고사항

세션 URL은 bearer 토큰처럼 작동합니다 — URL을 가진 누구나 세션에 접근할 수 있습니다.

- 메시징 앱을 통해 URL을 공유하지 마세요
- 화면 공유 또는 녹화 시 주의하세요
- 모든 작업에 수동 승인이 필요합니다
- `--dangerously-skip-permissions` 플래그를 지원하지 않습니다

## 현재 제한사항

- CLI 인스턴스당 하나의 동시 연결만 지원
- 로컬 터미널을 열어둬야 합니다
- 네트워크 연결 끊김 시 약 10분 타임아웃
- API 키가 아닌 `claude.ai` 로그인이 필요합니다
- 현재 Max 플랜 사용자를 위한 리서치 프리뷰로 제공

---

**이전**: [프롬프트 전략](/docs/level-3/prompting-strategy)

**다음**: [Claude Code on the Web](/docs/level-3/web-version)

**최종 수정**: 2026년 2월 28일
