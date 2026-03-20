<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/multi-model-strategy -->

# 멀티 모델 전략 | Claude Code 플레이북

## 멀티 모델 전략

Claude provides three model families: Opus, Sonnet, and Haiku. Using the most powerful model for every task increases costs, while relying solely on weaker models reduces quality. A multi-model strategy optimizes both performance and cost by selecting appropriate models for different task types.

### 모델 비교

| 모델 | 특징 | 적합한 작업 | 상대 비용 |
|------|------|----------|---------|
| **Opus 4.6** | 최고 성능, 복잡한 추론, 1M 컨텍스트 | 아키텍처 설계, 복잡한 알고리즘 | $$$$$ |
| **Sonnet 4.6** | 균형 잡힌 성능, 1M 컨텍스트 | 일반 코딩, 리뷰, 문서화 | $$$ |
| **Haiku 4.5** | 빠르고 저렴 | 간단한 수정, 포맷팅, 분류 | $ |

### 현재 Claude Code 기본 모델

"Claude Code는 기본적으로 **Sonnet 4.6**을 사용합니다." `/model` 명령어나 `--model` 플래그로 모델을 변경할 수 있습니다.

## 모델 선택 기준

### Opus를 써야 할 때

- 전체 시스템 아키텍처 설계
- 복잡한 버그의 근본 원인 분석
- 성능 최적화 전략 수립
- 보안 취약점 분석
- 처음 보는 대규모 코드베이스 이해

```
claude --model claude-opus-4-6 "이 마이크로서비스 아키텍처의 병목을 분석하고 개선 방안을 제시해줘"
```

### Sonnet을 써야 할 때 (기본값)

- 일반적인 기능 구현
- 코드 리뷰 및 리팩토링
- 테스트 코드 작성
- API 연동 및 데이터 처리
- 문서화 및 주석 작성

```
# 기본값이 Sonnet이므로 별도 지정 불필요
claude "사용자 인증 미들웨어 구현해줘"
```

### Haiku를 써야 할 때

- 파일 포맷팅 및 정리
- 간단한 이름 변경, 타입 수정
- 반복적인 보일러플레이트 생성
- 코드 번역 (언어 변환)
- 로그 분석 및 단순 분류

```
claude --model claude-haiku-4-5-20251001 "이 JSON을 TypeScript 타입으로 변환해줘"
```

## 서브에이전트 멀티 모델 전략

Claude Code의 Task 도구를 활용하면 작업을 여러 모델에 분산할 수 있습니다. 이를 **오케스트레이터-서브에이전트 패턴**이라 합니다.

### 패턴: 계획은 Opus, 실행은 Sonnet

```
사용자 요청 → Opus(계획 수립) → Sonnet × N (병렬 실행)
```

실제 CLAUDE.md 설정 예시:

```
# 작업 전략
- 복잡한 아키텍처 결정: 반드시 상세 계획을 먼저 세우고 실행
- 반복 작업(파일 10개 이상 수정): 병렬 처리 고려
- 포맷팅, 주석 추가: 빠른 처리 우선
```

### 패턴: 검토는 강하게, 구현은 빠르게

```
# 1단계: Haiku로 빠르게 초안 작성
claude --model claude-haiku-4-5-20251001 "CRUD API 보일러플레이트 생성해줘"

# 2단계: Sonnet으로 리뷰 및 개선
claude "방금 작성한 코드 리뷰하고 개선해줘"

# 3단계: 필요시 Opus로 심층 분석
claude --model claude-opus-4-6 "이 코드의 보안 취약점 분석해줘"
```

## 모델 선택 결정 트리

```
새 작업이 들어왔을 때:
1. 작업이 모호하거나 창의적인가?
   → YES: 먼저 Sonnet으로 탐색, 필요시 Opus
2. 코드베이스를 처음 이해해야 하나?
   → YES: Opus로 전체 구조 파악
3. 반복적이고 패턴이 명확한가?
   → YES: Haiku로 충분
4. 그 외 일반적인 개발 작업?
   → Sonnet (기본값)
```

## 실전 적용: 프로젝트 단계별 모델 전략

### 프로젝트 초기 단계 — Opus 집중

```
# 요구사항 분석 및 아키텍처 설계
claude --model claude-opus-4-6 "이 요구사항 문서를 분석해서
최적의 데이터베이스 스키마와 API 구조를 설계해줘: [요구사항]"
```

### 개발 단계 — Sonnet 중심

```
# 일반 기능 구현 (기본값 Sonnet 사용)
claude "설계한 스키마 기반으로 User 서비스 구현해줘"
claude "회원가입 API 테스트 코드 작성해줘"
```

### 반복 작업 — Haiku 활용

```
# 포맷팅, 주석, 단순 변환
claude --model claude-haiku-4-5-20251001 "모든 컨트롤러 파일에 JSDoc 주석 추가해줘"
```

### 코드 리뷰 단계 — Sonnet + 필요시 Opus

```
# 일반 리뷰
claude "PR 변경사항 리뷰해줘"

# 보안/성능 심층 분석
claude --model claude-opus-4-6 "결제 모듈 보안 감사해줘"
```

## 비용 절감 실전 팁

### 1. Haiku로 먼저 탐색

무엇을 해야 할지 모를 때, 비싼 모델로 바로 실행하지 말고:

```
# 먼저 Haiku로 방향 파악
claude --model claude-haiku-4-5-20251001 "이 에러의 원인이 뭔지 간략히 설명해줘"

# 방향이 잡히면 Sonnet으로 해결
claude "이 에러 고쳐줘: [구체적인 에러]"
```

### 2. 컨텍스트 최소화

모델 비용은 입력 토큰 수에도 비례합니다. 불필요한 파일을 포함시키지 마세요:

```
# 비효율: 전체 코드베이스 컨텍스트에서 간단한 수정

# 효율: 관련 파일만 명시
claude "src/utils/format.ts 의 formatDate 함수만 수정해줘"
```

### 3. 배치 처리

유사한 작업은 한 번의 요청으로 묶어서 처리:

```
# 비효율: 파일마다 개별 요청

# 효율: 한 번에 묶어서
claude "src/models/ 안의 모든 모델 파일에 timestamps 필드 추가해줘"
```

## 모델 능력 비교 요약

실제로 느껴지는 차이:

**Haiku**: "이 함수 이름 camelCase로 바꿔줘" → 즉시, 정확하게

**Sonnet**: "이 서비스 레이어 아키텍처를 개선해줘" → 맥락 파악 후 적절한 제안

**Opus**: "10만 줄 규모의 레거시 시스템을 현대화하는 전략을 세워줘" → 깊은 분석, 단계별 계획

### 실용적 조언

대부분의 일상적인 코딩 작업은 Sonnet으로 충분합니다. Opus는 "이 문제를 어떻게 접근해야 할지 모르겠을 때"를 위해 아껴두세요. Haiku는 "분명히 쉬운 작업인데 빠르게 해결하고 싶을 때" 활용하세요.

---

**이전**: [MCP 서버 연결](/docs/level-3/mcp-servers)

**다음**: [비용 최적화](/docs/level-3/cost-optimization)

**최종 수정**: 2026년 2월 28일
