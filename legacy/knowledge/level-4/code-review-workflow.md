<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/code-review-workflow -->

# 코드 리뷰 워크플로우

코드 리뷰는 두 단계로 나뉩니다: **작성자 셀프 리뷰**(PR 제출 전)와 **리뷰어 보조 리뷰**(PR 제출 후). Claude Code로 양쪽 모두를 강화하면 리뷰 품질이 크게 향상됩니다.

## 작성자 셀프 리뷰

PR을 올리기 전에 Claude로 자체 검토:

```
> git diff main...HEAD를 분석해서 내가 놓친 부분을 찾아줘:
  - 테스트 누락
  - 에러 핸들링 빠진 곳
  - 하드코딩된 값
  - 네이밍 일관성
```

### 커밋 메시지 자동 생성 Skill

```
---
name: commit
description: 스테이징된 변경사항으로 커밋 생성
disable-model-invocation: true
allowed-tools: Bash(git *)
---

스테이징된 변경사항을 분석하고 적절한 커밋 메시지를 작성해줘:

1. `git diff --staged` 확인
2. Conventional Commits 형식 사용 (feat/fix/refactor/test/docs/chore)
3. 변경의 "왜"에 집중
4. 한국어로 작성, 기술 용어는 영어
```

### PR 설명 자동 작성

```
> 이 브랜치의 변경사항을 분석해서 PR 설명을 작성해줘.
  포함할 내용:
  - 왜 이 변경이 필요한가 (배경)
  - 무엇을 바꿨는가 (요약)
  - 어떻게 테스트했는가 (테스트 방법)
```

## 리뷰어 보조 리뷰

### 빠른 컨텍스트 파악

```
> gh pr diff 123을 읽고 이 PR의 변경사항을 요약해줘.
  핵심 변경 파일과 영향 범위를 알려줘.
```

### 심층 리뷰

```
> 이 PR을 시니어 개발자 관점에서 리뷰해줘:
  1. 아키텍처 적합성
  2. 성능 영향
  3. 보안 우려사항
  4. 엣지 케이스
  5. 테스트 충분성
```

### 리뷰 코멘트 자동 생성

```
> 리뷰 결과를 GitHub PR 코멘트로 작성해줘.
  건설적이고 구체적인 톤으로.
  문제마다 개선 제안을 포함해.
```

## Pre-PR Skill 템플릿

```
---
name: pre-pr
description: PR 제출 전 자동 검사
disable-model-invocation: true
allowed-tools: Bash(*), Read(*), Grep(*), Glob(*)
---

PR 제출 전 다음을 검사해줘:

1. **테스트 커버리지**: 새 코드에 테스트가 있는가?
2. **에러 핸들링**: try-catch 누락은 없는가?
3. **하드코딩 값**: 설정으로 빼야 할 값은 없는가?
4. **린트/타입체크**: `npm run lint && npm run type-check` 실행
5. **변경 요약**: 커밋 목록과 핵심 변경사항 정리
```

## 팀 리뷰 체크리스트

CLAUDE.md에 팀 리뷰 기준을 명시:

```markdown
## 코드 리뷰 기준

### 필수 통과 조건
- [ ] 테스트 통과 (`npm test`)
- [ ] 타입 체크 통과 (`npm run type-check`)
- [ ] 린트 통과 (`npm run lint`)
- [ ] 빌드 성공 (`npm run build`)

### 리뷰 포인트 (우선순위 순)
1. **보안 이슈** → 블로커
2. **기능 버그** → 블로커
3. **성능 문제** → 중요
4. **코드 가독성** → 권장
5. **코드 스타일** → 선택
```

## 실전 리뷰 사이클

### 작성자 플로우

```bash
# 1. 개발 완료 후 셀프 리뷰
claude "git diff main...HEAD를 분석해서 문제점 찾아줘"

# 2. 발견된 이슈 수정
claude "에러 핸들링 누락된 부분 수정해줘"

# 3. 커밋 및 PR
/commit
claude "PR 설명 작성해줘"
gh pr create --title "..." --body "..."
```

### 리뷰어 플로우

```bash
# 1. PR 컨텍스트 파악
claude "gh pr diff 123을 분석해서 요약해줘"

# 2. 심층 리뷰
claude "보안과 성능 관점에서 리뷰해줘"

# 3. 코멘트 작성
claude "발견된 이슈를 GitHub 코멘트로 작성해줘"
# 반드시 사람이 확인 후 게시
```

## 리뷰 메트릭 활용

```
> 최근 한 달간 PR 리뷰 코멘트를 분석해서:
  - 자주 지적되는 패턴 Top 5
  - 팀 코딩 스타일 개선 포인트
  - CLAUDE.md에 추가할 새 규칙 제안
```

---

**최종 수정**: 2026년 2월 28일
