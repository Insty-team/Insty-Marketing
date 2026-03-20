<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-2/git-integration -->

# Git 연동 | Claude Code 플레이북

## Git 연동

Claude Code는 git 저장소를 직접 이해합니다. 변경 이력을 분석하고, 커밋 메시지를 제안하고, PR 설명을 작성하는 등 개발 워크플로우 전반에 걸쳐 도움을 줄 수 있습니다.

### Claude Code가 git에서 읽는 것들

Claude Code를 실행하면 자동으로 다음 정보를 파악합니다:

- 현재 브랜치명
- 최근 커밋 히스토리
- staged / unstaged 변경사항
- 파일 구조와 수정 시간

이 컨텍스트 덕분에 "방금 변경한 내용 리뷰해줘"라고만 해도 정확히 무엇이 바뀌었는지 알고 응답합니다.

### 커밋 메시지 자동 생성

가장 많이 쓰는 기능 중 하나입니다.

```
# 변경사항을 스테이징한 뒤
git add src/auth/login.ts tests/auth.test.ts

# Claude Code에 커밋 메시지 요청
claude> 스테이징된 변경사항 보고 커밋 메시지 써줘
```

Claude Code가 실제 코드 변경을 분석해서 의미 있는 커밋 메시지를 제안합니다:

```
feat(auth): JWT refresh token 로직 추가
- 만료된 access token 자동 갱신
- refresh token 유효성 검증 미들웨어 추가
- 관련 단위 테스트 3개 추가
```

#### Conventional Commits 형식 강제

CLAUDE.md에 다음을 추가하면 항상 Conventional Commits 형식으로 메시지를 생성합니다:

```
## 커밋 메시지 규칙
- Conventional Commits 형식 필수: type(scope): description
- type: feat, fix, docs, style, refactor, test, chore
- 한국어로 description 작성
- 본문에 변경 이유와 영향 범위 포함
```

### AI 코드 리뷰

PR을 올리기 전에 Claude Code에게 먼저 리뷰를 받으세요.

```
# 현재 브랜치와 main 브랜치의 차이를 리뷰
claude> main 브랜치와 비교해서 현재 변경사항 코드 리뷰해줘
```

또는 특정 파일에 대해:

```
claude> src/auth/login.ts 리뷰해줘. 보안 취약점 중심으로.
```

#### 리뷰 요청 시 구체적으로 물어보기

| 요청 | 무엇을 분석하나 |
|------|-----------------|
| "보안 취약점 찾아줘" | SQL 인젝션, XSS, 인증 우회 등 |
| "성능 문제 찾아줘" | N+1 쿼리, 불필요한 반복, 메모리 누수 |
| "엣지 케이스 찾아줘" | null 처리, 빈 배열, 타입 불일치 |
| "테스트 커버리지 분석해줘" | 테스트 안 된 경우의 수 |

### PR 설명 자동 작성

```
claude> 현재 브랜치 변경사항으로 GitHub PR 설명 써줘
```

결과 예시:

```
## 변경 사항
- JWT 기반 인증 시스템 추가
- Access token 만료 시 자동 갱신 로직 구현
- 로그인/로그아웃 API 엔드포인트 추가

## 테스트
- [ ] 단위 테스트 통과 확인
- [ ] E2E 로그인 플로우 테스트

## 주의사항
- 환경변수 JWT_SECRET 설정 필요
```

### 브랜치 전략과 함께 쓰기

Claude Code를 브랜치 기반 개발과 함께 쓰면 효과가 배가됩니다.

```
# 1. 기능 브랜치 생성
git checkout -b feature/user-auth

# 2. Claude Code로 구현
claude> JWT 인증 시스템 구현해줘. CLAUDE.md의 기술 스택 참고해서.

# 3. 구현 완료 후 리뷰
claude> 방금 만든 코드 리뷰해줘

# 4. 커밋 메시지 생성
git add .
claude> 커밋 메시지 제안해줘

# 5. PR 설명 생성
claude> PR 설명 써줘
```

### git blame과 히스토리 분석

```
claude> auth/login.ts 파일이 왜 이렇게 짜여있는지 git 히스토리 보고 분석해줘
claude> 지난 주에 누가 뭘 변경했는지 요약해줘
```

Claude Code가 `git log`, `git blame` 등의 정보를 분석해서 코드의 진화 과정을 설명해줍니다.

### 충돌 해결

```
# 머지 충돌이 발생했을 때
claude> 현재 충돌 파일들 보고 어떻게 해결할지 알려줘
```

Claude Code가 충돌 마커(`<<<<<<<`, `=======`, `>>>>>>>`)를 분석하고 양쪽 변경사항의 의도를 파악해서 해결책을 제안합니다.

### .gitignore 관리

```
claude> 이 프로젝트에 맞는 .gitignore 만들어줘
```

또는 특정 파일이 실수로 추적되고 있을 때:

```
claude> node_modules가 git에 추적되고 있는데 어떻게 제거하지?
```

### 실전 워크플로우: 하루의 AI 개발 흐름

```
# 오전: 작업 시작
git pull origin main
git checkout -b feature/payment-integration
claude> 어제 main에 머지된 변경사항 요약해줘

# 작업 중: 구현
claude> Stripe 결제 연동 구현해줘. 웹훅 처리 포함.

# 작업 완료: 정리
git add .
claude> 변경사항 리뷰해줘 (보안, 엣지케이스 중심)
claude> 커밋 메시지 써줘
git commit -m "$(claude -p '스테이징 변경사항으로 커밋 메시지 한 줄만')"

# PR 올리기
claude> PR 설명 써줘
```

---

**이전:** [권한 모드](/docs/level-2/permission-modes)
**다음:** [슬래시 커맨드](/docs/level-2/slash-commands)

**최종 수정:** 2026년 2월 28일

이 페이지에 오류가 있나요? [오류 제보하기 →](https://forms.gle/Mj4zGLjxJJnVeTECA)
