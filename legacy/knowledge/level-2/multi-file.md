<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-2/multi-file -->

# 멀티파일 작업 | Claude Code 플레이북

## 멀티파일 작업

실제 프로젝트는 수십~수천 개의 파일로 이루어집니다. 단일 파일 작업과 달리, 멀티파일 작업에서는 **파일 간 의존성**, **컨텍스트 효율**, **작업 순서**를 잘 관리해야 합니다.

## Claude Code가 파일을 이해하는 방식

Claude Code는 작업 요청을 받으면 먼저 관련 파일을 탐색합니다:

1. **디렉토리 구조 파악** — `ls`, `find` 등으로 전체 구조 이해
2. **관련 파일 식별** — 요청과 관련된 파일들을 찾음
3. **의존성 추적** — import/require 관계를 따라가며 연관 파일 파악
4. **변경 계획 수립** — 어떤 파일을 어떤 순서로 수정할지 결정

이 과정이 자동으로 이루어지므로, 관련 파일을 일일이 알려줄 필요가 없습니다.

## 멀티파일 작업 요청 방법

### 기능 단위로 요청하기

```
사용자 인증 기능을 추가해줘. 로그인, 회원가입, 로그아웃 포함. 기존 User 모델 활용해서.
```

Claude Code가 알아서 다음을 판단합니다:

- 어떤 파일을 새로 만들지
- 어떤 파일을 수정해야 하는지 (라우터, 미들웨어 등)
- 어떤 순서로 작업할지

### 범위를 명확히 지정하기

```
src/auth/ 디렉토리를 중심으로 JWT 인증 구현해줘. 기존 src/users/ 코드는 건드리지 말고,
src/middleware/ 에 미들웨어만 추가해.
```

"건드리지 말 것"을 명확히 하면 실수를 줄일 수 있습니다.

### 단계별로 진행하기

한 번에 너무 많은 파일을 바꾸면 검토가 어렵습니다:

```
1단계: 타입 정의만 먼저 해줘 (types/auth.ts)
[검토 후]
2단계: 서비스 레이어 구현해줘 (services/auth.ts)
[검토 후]
3단계: API 라우트 연결해줘 (routes/auth.ts)
```

## 파일 참조 패턴

### 특정 파일 명시적으로 참조

```
src/services/payment.ts 와 src/types/payment.ts 를 기반으로 환불 서비스 추가해줘
```

### 디렉토리 단위로 참조

```
src/components/ui/ 안의 모든 컴포넌트에 dark mode 지원 추가해줘
```

### 관련 파일 자동 탐색 유도

```
UserService와 관련된 파일들 모두 찾아서 이름을 AccountService로 리팩토링해줘
```

## 대규모 리팩토링

여러 파일에 걸친 리팩토링은 Claude Code의 강점 중 하나입니다.

### 네이밍 변경

```
프로젝트 전체에서 "userId"를 "accountId"로 바꿔줘.
DB 스키마, 타입, API 응답 모두 포함.
단, 외부 API와 통신하는 파일은 건드리지 마.
```

### 패턴 일관성 적용

```
src/api/ 디렉토리의 모든 라우트 핸들러를 현재 auth.ts 스타일로 통일해줘.
(try-catch, 에러 포맷, 응답 구조)
```

### 의존성 교체

```
axios를 fetch API로 교체해줘. 영향받는 파일 모두 업데이트하고,
axios 패키지 제거해줘.
```

## 작업 전 스냅샷: 필수 습관

멀티파일 작업 전에는 반드시 git 커밋을 먼저 하세요:

```
git add . && git commit -m "chore: 리팩토링 전 스냅샷"
claude --dangerously-skip-permissions
```

뭔가 잘못되면 즉시 복구할 수 있습니다:

```
git checkout .          # 모든 변경 취소
git reset HEAD~1        # 마지막 커밋 취소
```

## 실전 패턴: 기능 추가 워크플로우

### 예시: REST API에 새 리소스 추가

```
상품(Product) CRUD API를 추가해줘.
기존 User API 패턴(src/api/users/) 참고해서 동일한 구조로 만들어줘.
```

Claude 응답 예시:
```
다음 파일들을 생성/수정하겠습니다:

생성:
- src/types/product.ts
- src/models/Product.ts
- src/services/product.service.ts
- src/api/products/index.ts
- tests/product.test.ts

수정:
- src/api/index.ts (라우터 등록)
- prisma/schema.prisma (Product 모델 추가)

진행할까요?
```

Claude Code가 미리 계획을 보여줄 때는 반드시 검토하세요. 원하지 않는 파일이 포함되어 있으면 수정을 요청하세요.

### 예시: 기존 기능에 필드 추가

```
User 모델에 phoneNumber 필드 추가해줘.
DB, 타입, API, 테스트 모두 업데이트해줘.
```

Claude 응답 예시:
```
영향받는 파일:
- prisma/schema.prisma (필드 추가)
- src/types/user.ts (타입 업데이트)
- src/api/users/register.ts (요청 처리)
- src/api/users/profile.ts (응답 포함)
- tests/user.test.ts (테스트 케이스 추가)
- 마이그레이션 파일 생성
```

## 파일 간 충돌 방지

### "읽기 전용" 명시

```
src/auth/ 를 구현해줘.
src/config/ 파일들은 절대 건드리지 마.
그 설정들은 변경되면 안 돼.
```

### 영향 범위 먼저 확인

```
실제로 수정하기 전에, 이 변경이 어떤 파일들에 영향을 주는지만 먼저 알려줘.
```

Claude Code가 변경 계획을 먼저 보여주면, 예상치 못한 파일이 포함되어 있는지 확인할 수 있습니다.

## 테스트와 함께 멀티파일 작업

좋은 멀티파일 작업은 항상 테스트를 포함합니다:

```
Product 서비스 구현해줘.
구현 파일과 테스트 파일을 함께 만들어줘.
TDD 방식으로: 테스트 먼저, 구현 나중에.
```

```
방금 만든 모든 파일에 대해 테스트 실행해줘.
실패하는 테스트 있으면 바로 고쳐줘.
```

## 문서화와 함께

```
방금 구현한 Payment 모듈에 대해:
1. 각 함수에 JSDoc 주석 추가
2. src/docs/payment-api.md 작성 (API 명세)
3. README.md에 결제 섹션 추가
```

## 멀티파일 작업 체크리스트

대규모 작업을 시작하기 전에:

- git 커밋으로 스냅샷 확보
- CLAUDE.md에 금지 파일/디렉토리 명시
- 작업 범위를 작게 나눠서 계획
- 첫 변경 후 빌드/테스트 실행 확인
- 단계별로 git 커밋하면서 진행

---

**이전:** [메모리 시스템](/docs/level-2/memory-system)
**다음:** [체크포인트 시스템](/docs/level-2/checkpointing)

**최종 수정:** 2026년 2월 28일

이 페이지에 오류가 있나요? [오류 제보하기 →](https://forms.gle/Mj4zGLjxJJnVeTECA)
