<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-2/memory-system -->

# 메모리 시스템

Claude Code는 세션 종료 후 대화 내용을 기억하지 않지만, **6가지 메모리 계층**으로 이를 보완합니다.

### 메모리 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│  관리형 정책      (시스템 경로/CLAUDE.md)                      │
│  ─ 조직 전체 강제, IT/DevOps 관리, 최고 우선순위              │
├─────────────────────────────────────────────────────────────┤
│  사용자 메모리    (~/.claude/CLAUDE.md, ~/.claude/rules/)     │
│  ─ 개인 전역 설정, 모든 프로젝트에 적용                       │
├─────────────────────────────────────────────────────────────┤
│  프로젝트 메모리  (./CLAUDE.md, .claude/CLAUDE.md)            │
│  ─ 팀 전체 공유, git 커밋, 영구 유지                         │
├─────────────────────────────────────────────────────────────┤
│  프로젝트 규칙    (.claude/rules/*.md)                        │
│  ─ 모듈화된 주제별 규칙, 경로별 조건부 적용                    │
├─────────────────────────────────────────────────────────────┤
│  로컬 메모리      (./CLAUDE.local.md)                         │
│  ─ 개인 프로젝트별, git 미추적                               │
├─────────────────────────────────────────────────────────────┤
│  자동 메모리      (~/.claude/projects/<project>/memory/)      │
│  ─ Claude가 자동으로 저장, 프로젝트별 학습 결과               │
└─────────────────────────────────────────────────────────────┘
```

더 구체적인(좁은 범위의) 지시가 더 넓은 범위의 지시보다 우선합니다.

---

## 1. 관리형 정책 (Enterprise)

조직 관리자가 시스템 레벨에서 배포하는 CLAUDE.md입니다. 모든 사용자에게 강제 적용되며, 어떤 설정으로도 재정의할 수 없습니다.

| OS | 경로 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

MDM, Group Policy, Ansible 등의 구성 관리 시스템으로 배포합니다.

---

## 2. 사용자 메모리

**저장 위치**: `~/.claude/CLAUDE.md` (Windows: `C:\Users\{이름}\.claude\CLAUDE.md`)
**유지 기간**: 영구
**적용 범위**: 모든 프로젝트

### 사용자 메모리에 저장할 것

```markdown
# 개인 설정

## 코딩 스타일 선호
- 함수형 프로그래밍 선호
- 짧은 변수명 싫어함 (i, j, k 같은 것 피해줘)
- 주석은 "왜"에 집중 (무엇은 코드로 표현)

## 소통 방식
- 코드 변경 전 반드시 계획 먼저 설명해줘
- 한 번에 너무 많이 바꾸지 말고 단계적으로

## 자주 쓰는 기술
- Next.js, TypeScript, Prisma 주로 씀
- 테스트는 Vitest 선호
- 스타일은 Tailwind CSS
```

### 사용자 레벨 규칙

`~/.claude/rules/`에 개인 규칙 파일을 만들면 모든 프로젝트에 적용됩니다:

```
~/.claude/rules/
├── preferences.md    # 개인 코딩 선호도
└── workflows.md      # 선호 워크플로우
```

### 전역 메모리 초기 설정

처음 Claude Code를 설치했다면 전역 CLAUDE.md부터 만드세요:

```bash
mkdir -p ~/.claude
claude> 내 코딩 스타일과 선호도 인터뷰해줘. ~/.claude/CLAUDE.md에 저장해줘.
```

Claude Code가 몇 가지 질문을 하고 전역 설정을 만들어줍니다.

---

## 3. 프로젝트 메모리: CLAUDE.md

**저장 위치**: `{프로젝트 루트}/CLAUDE.md` 또는 `.claude/CLAUDE.md`
**유지 기간**: 영구 (git에 커밋)
**적용 범위**: 해당 프로젝트의 모든 팀원

[CLAUDE.md 작성법](/docs/level-2/claude-md) 챕터에서 자세히 다룹니다.

### 프로젝트 메모리에 저장할 것

```markdown
# My Project

## 기술 스택
[영구적인 기술 스택 정보]

## 팀 컨벤션
[팀 전체가 공유해야 할 규칙]

## 아키텍처 결정사항 (ADR)
[중요한 기술 결정과 이유]

## 빌드/테스트 커맨드
[자주 사용하는 명령어 — 반복 검색 방지]
```

#### /init으로 자동 생성

`/init` 커맨드로 현재 프로젝트에 맞는 CLAUDE.md를 자동 생성할 수 있습니다.

---

## 4. 프로젝트 규칙: `.claude/rules/`

대규모 프로젝트에서는 하나의 CLAUDE.md 대신 **모듈화된 규칙 파일**로 관리합니다.

```
.claude/rules/
├── code-style.md      # 코드 스타일
├── testing.md         # 테스트 규칙
├── frontend/
│   ├── react.md       # React 컨벤션
│   └── styles.md      # 스타일 가이드
└── backend/
    └── api.md         # API 규칙
```

YAML frontmatter의 `paths` 필드로 특정 파일에서만 적용되는 조건부 규칙도 가능합니다:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API 개발 규칙
- 모든 엔드포인트에 입력 검증 포함
- 표준 에러 응답 형식 사용
```

자세한 내용은 [CLAUDE.md 작성법 → .claude/rules/](/docs/level-2/claude-md#clauderules--%EB%AA%A8%EB%93%88%ED%99%94%EB%90%9C-%EA%B7%9C%EC%B9%99) 섹션을 참고하세요.

---

## 5. 로컬 메모리: CLAUDE.local.md

**저장 위치**: `{프로젝트 루트}/CLAUDE.local.md`
**유지 기간**: 영구 (로컬에서만)
**적용 범위**: 나만, 이 프로젝트에서만

자동으로 `.gitignore`에 추가되므로 개인 정보를 안전하게 저장할 수 있습니다. 팀에 공유하기 전에 지시사항을 테스트하거나, 머신별 설정을 저장할 때 유용합니다.

---

## 6. Auto Memory: Claude의 자동 메모리

Auto Memory는 Claude가 작업하면서 스스로 발견한 학습·패턴·인사이트를 자동으로 저장하는 기능입니다. CLAUDE.md와 달리 사용자가 작성하는 것이 아니라 **Claude가 자신을 위해 기록하는 노트**입니다.

### 기본 활성화

Auto Memory는 기본으로 활성화되어 있습니다. `/memory` 커맨드에서 토글로 켜고 끌 수 있습니다.

### Claude가 기억하는 것

- **프로젝트 패턴**: 빌드 커맨드, 테스트 컨벤션, 코드 스타일
- **디버깅 인사이트**: 까다로운 문제의 해결책, 흔한 에러 원인
- **아키텍처 노트**: 핵심 파일, 모듈 관계, 중요한 추상화
- **사용자 선호**: 소통 스타일, 워크플로우 습관, 도구 선택

### Auto Memory 파일 구조

각 프로젝트마다 별도의 메모리 디렉토리를 가집니다:

```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # 간결한 인덱스 (세션마다 자동 로드)
├── debugging.md       # 디버깅 패턴 상세 노트
├── api-conventions.md # API 설계 결정사항
└── ...                # Claude가 필요에 따라 생성
```

`<project>` 경로는 git 저장소 루트에서 파생됩니다. 같은 저장소의 모든 서브디렉토리는 하나의 Auto Memory를 공유합니다. Git 워크트리는 별도 메모리 디렉토리를 받습니다.

### MEMORY.md의 200줄 제한

`MEMORY.md`의 **처음 200줄만** 세션 시작 시 자동 로드됩니다. 200줄을 초과하는 내용은 로드되지 않습니다. Claude는 자동으로 상세 노트를 별도 주제 파일(예: `debugging.md`, `patterns.md`)로 분리하여 MEMORY.md를 간결하게 유지합니다.

주제 파일은 세션 시작 시 로드되지 않고, Claude가 필요할 때 직접 읽어옵니다.

### Auto Memory 관리

```bash
/memory     # 메모리 파일 열기 + 토글
```

Claude에게 직접 저장을 지시할 수도 있습니다:

```
> pnpm을 사용하는 프로젝트라는 거 기억해줘
> API 테스트에 로컬 Redis가 필요하다는 거 메모리에 저장해줘
```

### Auto Memory 비활성화

```javascript
// ~/.claude/settings.json (전역 비활성화)
{ "autoMemoryEnabled": false }

// .claude/settings.json (프로젝트별 비활성화)
{ "autoMemoryEnabled": false }
```

환경변수로 모든 설정을 덮어쓸 수 있습니다 (CI/관리 환경에 유용):

```bash
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1  # 강제 비활성화
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0  # 강제 활성화
```

---

## 세션 메모리: 대화 컨텍스트

현재 대화창의 내용입니다. 세션이 끝나면 사라집니다.

### 세션 메모리를 영구화하는 패턴

중요한 결정이나 정보는 세션이 끝나기 전에 저장하세요:

```
> 오늘 결제 모듈 완성했어. 중요한 결정사항 있으면 CLAUDE.md에 업데이트해줘.

Claude: CLAUDE.md를 업데이트했습니다:
- 환불 정책: 72시간 내, Stripe API 직접 호출
- 웹훅 시크릿: 환경변수 STRIPE_WEBHOOK_SECRET
- 결제 실패 재시도: 3회, exponential backoff
```

---

## 메모리 계층별 활용 전략

### 팀 프로젝트

```
관리형 정책 (IT/DevOps)
  └─ 조직 보안 정책, 코딩 표준

프로젝트 CLAUDE.md (git 커밋)
  └─ 팀 컨벤션, 기술 스택, 아키텍처

.claude/rules/ (git 커밋)
  └─ 주제별 세분화된 규칙

개인 ~/.claude/CLAUDE.md
  └─ 개인 코딩 스타일, 소통 방식

CLAUDE.local.md
  └─ 개인 테스트 환경, 로컬 설정

Auto Memory
  └─ 각자의 작업 패턴, 디버깅 경험
```

### 개인 프로젝트

```
프로젝트 CLAUDE.md
  └─ 프로젝트 현황, 기술 결정사항

개인 ~/.claude/CLAUDE.md
  └─ 전역 설정 (모든 프로젝트에 적용)

Auto Memory
  └─ 프로젝트 패턴, 학습 내용
```

---

## 메모리 관리 팁

### `/memory`로 확인과 편집

```bash
/memory
```

`/memory` 커맨드는 시스템 에디터에서 메모리 파일을 열어주며, Auto Memory 토글도 포함합니다. 로드된 모든 메모리 파일 목록을 확인할 수 있습니다.

### 정기적으로 CLAUDE.md 업데이트

작업이 완료될 때마다 현황을 업데이트하세요:

```
> 오늘 작업 끝. CLAUDE.md 현황 섹션 업데이트해줘.
```

### 오래된 정보 정리

메모리가 쌓이면 오히려 혼란이 생깁니다:

```
> CLAUDE.md에서 완료된 항목들 정리해줘. 현재 진행 중인 것만 남겨.
```

### 추가 디렉토리 메모리 로드

`--add-dir`로 추가한 디렉토리의 CLAUDE.md는 기본적으로 로드되지 않습니다. 로드하려면:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

---

## 메모리 시스템 전체 흐름

```
새 세션 시작
│
├─ 관리형 CLAUDE.md 로드 (조직 정책)
├─ ~/.claude/CLAUDE.md + rules/ 로드 (사용자 메모리)
├─ ./CLAUDE.md + .claude/rules/ 로드 (프로젝트 메모리)
├─ ./CLAUDE.local.md 로드 (로컬 메모리)
└─ MEMORY.md 처음 200줄 로드 (자동 메모리)

│    [작업 진행]
│
│    중간에 중요한 결정
│    → CLAUDE.md에 즉시 기록
│
│    Claude가 패턴 발견
│    → Auto Memory에 자동 저장
│
│    /compact (컨텍스트 압축)
│    → 핵심 요약 유지
│
세션 종료
│
└─ "오늘 작업 CLAUDE.md에 업데이트해줘"
    → 다음 세션에 이어갈 정보 저장
```

---

**최종 수정**: 2026년 2월 28일
