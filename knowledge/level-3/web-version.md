<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/web-version -->

# Claude Code on the Web | Claude Code 플레이북

## Claude Code on the Web

브라우저에서 Claude Code를 실행하는 기능입니다. Anthropic이 관리하는 클라우드 VM에서 코드를 분석하고 수정하며, diff 뷰로 변경사항을 검토한 후 바로 PR을 생성할 수 있습니다.

## 핵심 특징

| Feature | Claude Code on the Web | 로컬 CLI |
|---------|------------------------|---------|
| 실행 위치 | Anthropic 클라우드 VM | 내 컴퓨터 |
| 설치 | 불필요 (브라우저만) | npm 설치 필요 |
| 로컬 파일 접근 | 불가 (GitHub 연동) | 가능 |
| 병렬 작업 | 여러 개 동시 가능 | CLI 인스턴스당 1개 |
| MCP 서버 | 제한적 | 완전 지원 |
| Git 연동 | GitHub만 | 모든 Git |

## 이용 가능 플랜

| Plan | 사용 가능 |
|------|---------|
| Pro | O |
| Max | O |
| Team | O |
| Enterprise | Premium 또는 Chat+Claude Code 시트 |

## 시작하기

1. claude.ai/code 방문
2. GitHub 계정 연결
3. Claude GitHub 앱을 리포지토리에 설치
4. 기본 환경 선택
5. 코딩 태스크 제출
6. diff 뷰에서 변경사항 검토 → PR 생성

## 작동 원리

1. 리포지토리를 클라우드 VM에 클론
2. 보안 환경 준비 (의존성, 네트워크 설정)
3. 코드 분석, 수정, 테스트 실행
4. 완료 알림
5. 브랜치에 푸시 → PR 생성 준비

> Claude Code는 `CLAUDE.md` 컨텍스트를 존중하며, SessionStart Hook도 실행됩니다.

## Diff 뷰

- diff 통계 (+/- 줄 수) 표시
- 파일별 변경사항 검토
- 특정 변경에 코멘트 작성
- 드래프트 PR 없이 반복 검토 가능

## 웹 ↔ 터미널 전환

### 터미널 → 웹 (`--remote`)

```
claude --remote "src/auth/login.ts의 인증 버그 수정해줘"
```

- claude.ai에 새 웹 세션 생성
- 클라우드에서 태스크 실행, 로컬에서는 다른 작업 가능
- `/tasks`로 진행 상황 확인
- claude.ai나 모바일 앱에서 피드백 가능

**병렬 실행 예시**:

```
claude --remote "API 엔드포인트 리팩토링"
claude --remote "테스트 커버리지 개선"
```

> 로컬에서 먼저 계획하기 위해 `--permission-mode plan`으로 로컬에서 먼저 코드를 탐색한 후, `--remote`로 실제 작업을 웹에 위임하면 효율적입니다.

### 웹 → 터미널 (`/teleport`)

```
/teleport
/tp
claude --teleport
claude --teleport <session-id>
```

`/tasks`에서 `t` 키를 눌러 텔레포트하거나, 웹 인터페이스의 "Open in CLI" 버튼 사용 가능.

### 텔레포트 요구사항

| 조건 | 설명 |
|-----|-----|
| 깨끗한 git 상태 | 커밋되지 않은 변경이 있으면 stash 프롬프트 |
| 같은 리포지토리 | fork가 아닌 같은 리포에서 실행 |
| 브랜치 이용 가능 | 리모트에 푸시된 브랜치 (자동 fetch+checkout) |
| 같은 계정 | 동일한 claude.ai 계정으로 인증 |

## 세션 공유

| Plan | 공유 범위 |
|------|---------|
| Enterprise/Team | Private 또는 Team (조직 멤버에게 공개) |
| Max/Pro | Private 또는 Public (모든 로그인 사용자에게 공개) |

> Team/Public 공유 시 리포지토리 접근 권한 검증이 이루어집니다. Settings → Claude Code → Sharing settings에서 접근 검증 활성화와 이름 숨기기를 설정할 수 있습니다.

## 클라우드 환경 설정

### 기본 환경

**포함 도구**:

| 카테고리 | 도구 |
|---------|-----|
| 언어 | Python 3.x, Node.js LTS, Ruby 3.3, PHP 8.4, Java (OpenJDK), Go, Rust, C++ |
| 패키지 매니저 | pip, poetry, npm, yarn, pnpm, bun, gem, bundler, cargo, Maven, Gradle |
| 데이터베이스 | PostgreSQL 16, Redis 7.0 |

`check-tools` 명령으로 사용 가능한 도구를 확인할 수 있습니다.

### 커스텀 환경

- 웹에서 현재 환경 선택 → "Add environment" 또는 설정 버튼
- 이름, 네트워크 접근, 환경변수 지정
- 터미널에서 `/remote-env`로 기본 환경 선택

### 의존성 설치

**SessionStart Hook 사용**:

```json
// .claude/settings.json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/install_pkgs.sh"
          }
        ]
      }
    ]
  }
}
```

**설치 스크립트 예시**:

```bash
#!/bin/bash
# scripts/install_pkgs.sh
# 클라우드 환경에서만 실행
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi
npm install
pip install -r requirements.txt
exit 0
```

**의존성 관리 제한사항**:

- Hook은 모든 세션에서 실행됩니다. `CLAUDE_CODE_REMOTE` 변수를 확인하여 로컬 실행을 건너뛰세요
- 패키지 레지스트리에 접근하려면 네트워크가 필요합니다
- 일부 패키지 매니저(예: Bun)는 보안 프록시와 호환되지 않을 수 있습니다

## 네트워크와 보안

### 네트워크 정책

- **GitHub 프록시**: 모든 git 상호작용을 투명하게 처리. 샌드박스 내 스코프 제한 자격 증명 사용
- **보안 프록시**: 모든 아웃바운드 트래픽이 프록시를 통과. 악성 요청 차단, 속도 제한, 콘텐츠 필터링
- **git push 제한**: 현재 작업 브랜치에만 푸시 가능

### 접근 수준

| 수준 | 설명 |
|-----|-----|
| 기본 | 허용 목록 도메인만 접근 가능 |
| 커스텀 | 네트워크 접근 비활성화 또는 특정 도메인만 허용 |

기본 허용 도메인에는 Anthropic 서비스, GitHub/GitLab/Bitbucket, 주요 패키지 레지스트리(npm, PyPI, RubyGems, crates.io, Maven 등), 클라우드 플랫폼(AWS, GCP, Azure), 컨테이너 레지스트리 등이 포함됩니다.

### 보안 격리

- 각 세션이 격리된 VM에서 실행
- 민감한 자격 증명은 샌드박스 내부에 존재하지 않음
- 보안 프록시를 통한 인증

> 네트워크 접근을 비활성화해도 Claude Code는 Anthropic API와 통신할 수 있으며, 이를 통해 데이터가 격리된 VM 외부로 나갈 수 있습니다.

## 제한사항

| 제한 | 설명 |
|-----|-----|
| GitHub만 지원 | GitLab이나 GitHub 외 리포지토리는 사용 불가 |
| 세션 인증 | 웹↔로컬 전환 시 같은 계정으로 인증 필요 |
| Rate Limit 공유 | 계정의 모든 Claude 사용과 rate limit 공유 |

## 모범 사례

1. **SessionStart Hook 활용**: 환경 설정과 의존성 설치를 자동화
2. **요구사항 문서화**: `CLAUDE.md`에 의존성과 명령어를 명시
3. **로컬에서 계획, 웹에서 실행**: 복잡한 작업은 Plan 모드로 먼저 탐색
4. **병렬 작업 활용**: `--remote`로 여러 독립 태스크를 동시에 실행

---

**이전**: [Remote Control](/docs/level-3/remote-control)

**다음**: [레벨 4 — 고급 소개](/docs/level-4/intro)

**최종 수정**: 2026년 2월 28일
