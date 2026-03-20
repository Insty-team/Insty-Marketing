<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-2/claude-md -->

# CLAUDE.md 작성법 | Claude Code 플레이북

## CLAUDE.md 작성법

CLAUDE.md는 Claude Code에게 "이 프로젝트에서는 이렇게 행동해"라고 미리 알려두는 설정 파일입니다. 프롬프트를 매번 반복하지 않아도, 프로젝트의 규칙·컨벤션·주의사항을 영구적으로 기억시킬 수 있습니다.

## 왜 CLAUDE.md인가?

Claude Code를 처음 쓸 때 가장 흔히 하는 실수는 **매 세션마다 같은 컨텍스트를 반복 설명하는 것**입니다.

> "이 프로젝트는 TypeScript야. ESLint 규칙 꼭 지켜줘. 테스트는 Vitest 써. 코드 스타일은 Airbnb야."

이걸 매번 입력하는 건 낭비입니다. CLAUDE.md에 한 번 써두면 Claude Code가 세션 시작 시 자동으로 읽습니다.

## 파일 위치와 우선순위

CLAUDE.md는 여러 위치에 둘 수 있으며, 더 구체적인 위치가 우선합니다:

| 메모리 유형 | 위치 | 용도 | 공유 범위 |
|------------|------|------|---------|
| **관리형 정책** | OS별 시스템 경로 | 조직 전체 코딩 표준, 보안 정책 | 조직 전체 |
| **사용자** | `~/.claude/CLAUDE.md` | 개인 코딩 스타일, 도구 설정 | 나만 (모든 프로젝트) |
| **프로젝트** | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 팀 공유 프로젝트 규칙 | 팀 (소스 컨트롤) |
| **프로젝트 규칙** | `./.claude/rules/*.md` | 모듈화된 주제별 규칙 | 팀 (소스 컨트롤) |
| **로컬** | `./CLAUDE.local.md` | 개인 프로젝트별 설정 | 나만 (현재 프로젝트) |
| **서브디렉토리** | `{subdir}/CLAUDE.md` | 특정 모듈 전용 규칙 | 해당 디렉토리 작업 시만 |

### 로딩 방식

- **상위 디렉토리**: 작업 디렉토리에서 루트까지 재귀적으로 올라가며 모든 CLAUDE.md, CLAUDE.local.md를 찾아 전량 로드
- **하위 디렉토리**: 해당 서브트리의 파일을 Claude가 읽을 때 온디맨드로 로드
- 더 구체적인(좁은 범위의) 지시가 더 넓은 범위의 지시보다 우선

> **빠른 시작**
> `/init` 커맨드로 현재 프로젝트에 맞는 CLAUDE.md를 자동 생성할 수 있습니다.

## CLAUDE.local.md

팀에 공유하지 않고 나만 쓰는 프로젝트별 설정은 `CLAUDE.local.md`에 작성합니다.

```
# 내 로컬 설정

## 샌드박스 URL
- API: http://localhost:3001
- DB: postgresql://localhost:5433/mydb

## 테스트 데이터
- 테스트 사용자: test@example.com / test1234
```

> **자동 gitignore**
> CLAUDE.local.md는 Claude Code가 자동으로 `.gitignore`에 추가합니다. 소스 컨트롤에 커밋되지 않으므로 개인 정보를 안전하게 저장할 수 있습니다.

## CLAUDE.md 기본 구조

좋은 CLAUDE.md는 크게 4개 영역으로 구성됩니다.

```
# {프로젝트명}

## 프로젝트 개요
[프로젝트가 무엇인지 1-3문장]

## 기술 스택
[사용 기술, 버전, 중요한 라이브러리]

## 코드 컨벤션
[언어 규칙, 포맷, 네이밍 규칙]

## 주의사항 / 절대 하지 말 것
[잘못하면 큰일 나는 것들]
```

## 실전 예시: Next.js + TypeScript 프로젝트

```
# E-Commerce Platform

## 프로젝트 개요
Next.js 14 (App Router) 기반 B2C 이커머스 플랫폼.
결제는 Stripe, 인증은 NextAuth.js, DB는 PostgreSQL + Prisma 사용.

## 기술 스택
- Next.js 14.2, React 18, TypeScript 5.3
- Tailwind CSS 3.4 (CSS Modules 사용 금지)
- Prisma ORM, PostgreSQL 15
- Vitest (테스트), ESLint + Prettier (포맷)
- pnpm (패키지 매니저) — npm/yarn 사용 금지

## 디렉토리 구조
- `app/` — App Router 페이지 및 레이아웃
- `components/` — 재사용 컴포넌트 (ui/, features/ 구분)
- `lib/` — 유틸리티, DB 클라이언트
- `prisma/` — 스키마, 마이그레이션

## 코드 컨벤션
- 컴포넌트: PascalCase, named export 사용
- 훅: `use` 접두사, `hooks/` 디렉토리
- API Route: RESTful 네이밍, 에러는 항상 `{ error: string }` 형태로 반환
- 타입은 `type` 키워드 사용 (interface 지양)
- async/await 사용, Promise chain(.then) 지양

## 테스트 규칙
- 새 기능마다 Vitest 단위 테스트 필수
- 테스트 파일: `{name}.test.ts` (같은 디렉토리)
- `describe > it` 구조 사용

## 절대 하지 말 것
- `any` 타입 사용 금지 (unknown 또는 정확한 타입 사용)
- `console.log` 프로덕션 코드에 남기지 말 것
- DB 쿼리 직접 작성 금지 — 반드시 Prisma 사용
- `process.env` 직접 접근 금지 — `lib/env.ts` 통해 접근

## 환경 변수
- `DATABASE_URL`: Prisma 연결 문자열
- `NEXTAUTH_SECRET`: NextAuth 시크릿
- `STRIPE_SECRET_KEY`: Stripe 비밀키 (절대 클라이언트에 노출 금지)
```

## 실전 예시: Python FastAPI 프로젝트

```
# ML Inference API

## 개요
PyTorch 모델을 서빙하는 FastAPI 기반 추론 API.
Docker 컨테이너로 배포, GPU 서버에서 실행.

## 기술 스택
- Python 3.11, FastAPI 0.110, Uvicorn
- PyTorch 2.2 (CUDA 12.1)
- Pydantic v2 (v1 문법 사용 금지)
- pytest, ruff (린터), mypy (타입체크)

## 코드 스타일
- 모든 함수에 타입 힌트 필수
- docstring: Google 스타일
- 라인 길이: 88자 (ruff 기본값)
- 클래스명: PascalCase, 함수/변수: snake_case

## API 설계 규칙
- 모든 엔드포인트에 response_model 명시
- 에러: HTTPException, 상태코드 명확히
- 비동기 엔드포인트 우선 (async def)

## 주의
- GPU 메모리 누수 주의: 추론 후 반드시 torch.cuda.empty_cache()
- 모델 가중치 파일(.pt, .pth) git 커밋 금지
```

## 임포트 (`@`) 구문

CLAUDE.md에서 다른 파일을 `@` 접두사로 참조하면 해당 내용도 컨텍스트에 포함됩니다.

```
# My Project

@README.md 를 참고해서 프로젝트 개요를 파악해.
@package.json 에서 사용 가능한 npm 스크립트 확인.

## 추가 지침
- git 워크플로우 @docs/git-instructions.md
```

### 경로 규칙

| 경로 형식 | 의미 | 예시 |
|----------|------|------|
| `@filename` | 현재 CLAUDE.md 기준 상대 경로 | `@README.md` |
| `@path/to/file` | 현재 CLAUDE.md 기준 상대 경로 | `@docs/spec.md` |
| `@~/path` | 홈 디렉토리 기준 | `@~/.claude/my-project-instructions.md` |

상대 경로는 **CLAUDE.md 파일이 있는 디렉토리** 기준으로 해석됩니다 (작업 디렉토리가 아닙니다).

### 재귀 임포트

임포트된 파일에서 다시 다른 파일을 임포트할 수 있습니다. 최대 깊이는 **5단계**입니다.

### 코드 블록 내 보호

마크다운 코드 스팬이나 코드 블록 내부의 `@`는 임포트로 처리되지 않습니다:

```
이것은 임포트가 아닙니다: `@anthropic-ai/claude-code`
```

> **첫 승인 필요**
> 프로젝트에서 처음 외부 임포트를 발견하면 승인 대화상자가 표시됩니다. 한 번 승인하면 이후에는 자동 로드됩니다. 거절하면 해당 임포트는 비활성화됩니다.

### 워크트리에서의 활용

Git 워크트리를 여러 개 사용하는 경우, `CLAUDE.local.md`는 하나의 워크트리에만 존재합니다. 모든 워크트리에서 공유하려면 홈 디렉토리 임포트를 사용하세요:

```
# 개인 설정
- @~/.claude/my-project-instructions.md
```

## `.claude/rules/` — 모듈화된 규칙

대규모 프로젝트에서는 하나의 CLAUDE.md 대신 여러 규칙 파일로 나눌 수 있습니다.

### 기본 구조

```
your-project/
├── .claude/
│   ├── CLAUDE.md              # 메인 프로젝트 지침
│   └── rules/
│       ├── code-style.md      # 코드 스타일 가이드라인
│       ├── testing.md         # 테스트 컨벤션
│       ├── security.md        # 보안 요구사항
│       ├── frontend/          # 서브디렉토리로 그룹화
│       │   ├── react.md
│       │   └── styles.md
│       └── backend/
│           ├── api.md
│           └── database.md
```

`.claude/rules/` 내의 모든 `.md` 파일은 자동으로 프로젝트 메모리로 로드됩니다 (`.claude/CLAUDE.md`와 동일한 우선순위).

### 경로별 조건부 규칙

YAML frontmatter의 `paths` 필드로 특정 파일에서만 적용되는 규칙을 만들 수 있습니다:

```yaml
---
paths:
  - "src/api/**/*.ts"
---

# API 개발 규칙
- 모든 API 엔드포인트에 입력 검증 포함
- 표준 에러 응답 형식 사용
- OpenAPI 문서화 주석 포함
```

`paths` 필드가 없는 규칙은 무조건 로드되어 모든 파일에 적용됩니다.

### 글로브 패턴

| 패턴 | 매칭 |
|------|------|
| `**/*.ts` | 모든 디렉토리의 TypeScript 파일 |
| `src/**/*` | src/ 하위 모든 파일 |
| `*.md` | 프로젝트 루트의 마크다운 파일 |
| `src/components/*.tsx` | 특정 디렉토리의 React 컴포넌트 |
| `src/**/*.{ts,tsx}` | 중괄호 확장 — .ts와 .tsx 모두 매칭 |
| `{src,lib}/**/*.ts` | 여러 디렉토리 매칭 |

### 심링크

`.claude/rules/` 디렉토리는 심링크를 지원합니다. 여러 프로젝트에서 공통 규칙을 공유할 때 유용합니다:

```bash
# 공유 규칙 디렉토리 심링크
ln -s ~/shared-claude-rules .claude/rules/shared

# 개별 규칙 파일 심링크
ln -s ~/company-standards/security.md .claude/rules/security.md
```

순환 심링크는 자동으로 감지되어 안전하게 처리됩니다.

### 사용자 레벨 규칙

모든 프로젝트에 적용되는 개인 규칙은 `~/.claude/rules/`에 만듭니다:

```
~/.claude/rules/
├── preferences.md    # 개인 코딩 선호도
└── workflows.md      # 선호 워크플로우
```

사용자 레벨 규칙은 프로젝트 규칙보다 먼저 로드되므로, 프로젝트 규칙이 더 높은 우선순위를 가집니다.

> **rules/ 베스트 프랙티스**
> - **주제별 분리**: 각 파일은 하나의 주제만 (예: `testing.md`, `api-design.md`)
> - **설명적 파일명**: 파일명만 보고 내용을 알 수 있도록
> - **조건부 규칙은 신중히**: 정말로 특정 파일에만 적용되는 규칙만 `paths` 사용
> - **서브디렉토리로 정리**: 관련 규칙 그룹화 (예: `frontend/`, `backend/`)

## 관리형 정책 (Enterprise)

조직 관리자는 시스템 레벨에서 CLAUDE.md를 배포하여 모든 사용자에게 강제할 수 있습니다:

| OS | 경로 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

MDM, Group Policy, Ansible 등 구성 관리 시스템으로 배포합니다.

## 추가 디렉토리의 메모리 로드

`--add-dir`로 추가한 디렉토리의 CLAUDE.md는 기본적으로 로드되지 않습니다. 로드하려면 환경변수를 설정하세요:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

이렇게 하면 추가 디렉토리의 CLAUDE.md, .claude/CLAUDE.md, .claude/rules/*.md가 모두 로드됩니다.

## 작성 팁 5가지

**1. 명령형으로 써라**

- ❌ "TypeScript를 사용하는 프로젝트입니다"
- ✅ "TypeScript만 사용해. JavaScript 파일 생성 금지"

**2. 부정형(하지 말 것)도 명시해라**

Claude가 하지 말아야 할 것을 명확히 쓰면 실수가 줄어듭니다.

```
## 금지 사항
- 라이브러리 추가 시 반드시 물어볼 것 (임의로 설치 금지)
- 기존 테스트 삭제 금지
- TODO 주석 임의로 제거 금지
```

**3. 구체적으로 써라**

"좋은 코드를 써줘"는 의미 없습니다. "함수 하나당 30줄 초과 시 분리할 것"처럼 구체적으로 쓰세요.

**4. 너무 길면 역효과**

CLAUDE.md가 너무 길면 중요한 내용이 묻힙니다. 핵심만 넣고, 상세 스펙은 `@docs/spec.md`로 임포트하거나 `.claude/rules/`로 분리하세요.

**5. 팀이 함께 관리해라**

CLAUDE.md는 코드 리뷰 대상입니다. 팀원이 PR로 수정하고, 다 같이 검토하는 문화를 만드세요.

## CLAUDE.md 빠른 시작 템플릿

```
# {프로젝트명}

## 한 줄 설명
{이 프로젝트가 뭔지 한 문장}

## 기술 스택
- 언어:
- 프레임워크:
- DB:
- 테스트:
- 패키지 매니저: (이것만 사용, 다른 것 금지)

## 코드 스타일
- {린터/포맷터 및 설정}
- {네이밍 컨벤션}

## 금지 사항
- {절대 하면 안 되는 것}

## 참고 문서
@{관련 문서 경로}
```

이 템플릿을 복사해서 프로젝트에 맞게 채우거나, `/init` 커맨드로 자동 생성하세요.

---

**최종 수정: 2026년 2월 28일**

이 페이지에 오류가 있나요? [오류 제보하기 →](https://forms.gle/Mj4zGLjxJJnVeTECA)
