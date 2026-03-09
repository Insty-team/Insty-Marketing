<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-3/cicd-integration -->

# CI/CD 통합 | Claude Code 플레이북

## Overview

Claude Code를 CI/CD 파이프라인에 통합하면 "PR 자동 리뷰, 코드 품질 검사, 자동 문서화 등을 파이프라인의 일부로 만들 수 있습니다."

## 핵심 활용 시나리오

- **PR 자동 리뷰**: PR 생성 시 Claude가 코드 리뷰 코멘트 작성
- **이슈 자동 해결**: 이슈에 Claude를 멘션하면 자동으로 수정 PR 생성
- **자동 테스트 생성**: 새 코드에 대한 테스트 자동 제안
- **릴리즈 노트 자동화**: 커밋 기록에서 릴리즈 노트 생성
- **코드 품질 게이트**: 품질 기준 미달 시 PR 차단

## 공식 GitHub Action

Anthropic이 제공하는 `anthropics/claude-code-action@v1`을 사용하여 별도 설정 없이 Claude Code를 GitHub Actions에 통합할 수 있습니다.

### 빠른 시작: PR 리뷰

`.github/workflows/claude-review.yml`:

```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
  issue_comment:
    types: [created]
jobs:
  claude-review:
    if: |
      github.event_name == 'pull_request' ||
      (github.event_name == 'issue_comment' &&
       contains(github.event.comment.body, '@claude'))
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

PR에서 `@claude` 멘션 시 자동 리뷰가 작동합니다.

### 주요 설정 파라미터

| 파라미터 | 설명 | 기본값 |
|---------|------|-------|
| `anthropic_api_key` | Anthropic API 키 | (필수) |
| `github_token` | GitHub 토큰 | `github.token` |
| `prompt` | Claude에게 전달할 추가 프롬프트 | - |
| `claude_args` | Claude Code CLI 인수 | - |
| `trigger_phrase` | 멘션 트리거 문구 | `@claude` |
| `assignee_trigger` | 이슈 담당자 지정 시 자동 실행 | `false` |
| `timeout_minutes` | 최대 실행 시간(분) | `60` |
| `model` | 사용할 모델 | - |
| `claude_env` | Claude Code에 전달할 환경변수 | - |
| `use_bedrock` | AWS Bedrock 사용 | `false` |
| `use_vertex` | Google Vertex AI 사용 | `false` |

### 커스텀 프롬프트 예시

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: |
      코드 리뷰 시 다음 기준에 집중해줘:
      1. 보안 취약점 (OWASP Top 10)
      2. 성능 병목 가능성
      3. TypeScript 타입 안전성
      4. 테스트 커버리지 부족 영역
    claude_args: "--model claude-sonnet-4-6"
```

### 이슈 자동 해결

이슈에 `@claude`를 멘션하면 자동으로 수정 PR을 생성합니다:

```yaml
name: Claude Issue Resolver
on:
  issues:
    types: [opened, assigned]
  issue_comment:
    types: [created]
jobs:
  resolve:
    if: |
      (github.event_name == 'issue_comment' &&
       contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'issues' &&
       contains(github.event.issue.assignees.*.login, 'claude-bot'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          assignee_trigger: true
```

### AWS Bedrock 통합

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    use_bedrock: true
    claude_env: |
      ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-6-20250514-v1:0
    claude_args: "--model us.anthropic.claude-sonnet-4-6-20250514-v1:0"
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_REGION: us-east-1
```

### Google Vertex AI 통합

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    use_vertex: true
    claude_env: |
      CLOUD_ML_REGION=us-east5
      ANTHROPIC_VERTEX_PROJECT_ID=${{ secrets.GCP_PROJECT_ID }}
      ANTHROPIC_MODEL=claude-sonnet-4-6@20250514
  env:
    GOOGLE_APPLICATION_CREDENTIALS: ${{ steps.auth.outputs.credentials_file_path }}
```

**공식 Action vs 커스텀 워크플로우**: 공식 Action은 PR 컨텍스트 자동 로딩, 이슈 연동, 코멘트 자동 게시 등을 자동 처리합니다. 간단한 CI 작업이면 공식 Action을, 고도로 커스터마이즈된 파이프라인이면 커스텀 워크플로우를 사용하세요.

## 커스텀 워크플로우

공식 Action 대신 직접 Claude Code CLI를 사용하는 워크플로우입니다.

### PR 리뷰 (CLI 직접 사용)

```yaml
name: Claude Code Review (Custom)
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Run Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          CHANGED_FILES=$(git diff --name-only origin/${{ github.base_ref }}...HEAD)
          claude -p "다음 파일들의 변경사항을 리뷰해줘.
          버그, 보안 이슈, 성능 문제, 코드 스타일을 확인해줘.
          각 파일별로 구체적인 피드백을 제공해줘:
          $CHANGED_FILES" \
          --allowedTools "Read,Grep,Glob" > review.md
          gh pr comment ${{ github.event.pull_request.number }} --body-file review.md
```

### 자동 릴리즈 노트 생성

```yaml
name: Release Notes
on:
  push:
    tags:
      - 'v*'
jobs:
  release-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Generate Release Notes
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1)
          COMMITS=$(git log $PREV_TAG..HEAD --oneline)
          claude -p "다음 커밋 목록을 바탕으로
          사용자 친화적인 한국어 릴리즈 노트를 작성해줘.
          새 기능, 버그 수정, 개선사항으로 분류해줘:
          $COMMITS" > release-notes.md
          gh release edit ${{ github.ref_name }} --notes-file release-notes.md
```

## GitLab CI 통합

`.gitlab-ci.yml`:

```yaml
stages:
  - review

claude-review:
  stage: review
  image: node:20
  script:
    - npm install -g @anthropic-ai/claude-code
    - CHANGED=$(git diff --name-only origin/main...HEAD)
    - claude -p "코드 리뷰해줘: $CHANGED"
      --allowedTools "Read,Grep,Glob" > review.md
    - cat review.md
  only:
    - merge_requests
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

## 헤드리스 모드

CI 환경에서는 `-p` (또는 `--print`) 플래그로 비대화형 모드를 사용합니다:

```bash
# 단일 명령 실행 후 종료
claude -p "이 코드의 보안 취약점 분석해줘" < vulnerable-code.ts

# 파이프라인 입력 처리
cat error.log | claude -p "이 에러 로그 분석해서 근본 원인 찾아줘"

# JSON 출력 형식
claude -p "API 스키마 생성해줘" --output-format json

# 스트리밍 출력
claude -p "코드 분석해줘" --output-format stream-json
```

### 멀티턴 대화 (SDK 연동)

`claude -p`는 단일 턴입니다. 여러 턴이 필요하면 SDK를 사용합니다:

```javascript
import { ClaudeCode } from "@anthropic-ai/claude-code";

const claude = new ClaudeCode();
const conversation = await claude.startConversation();

// 1턴: 분석
const analysis = await conversation.send("코드 분석해줘");

// 2턴: 분석 결과 기반 수정
const fix = await conversation.send("발견한 문제 수정해줘");
```

## 보안 설정

### API 키 관리

```yaml
# GitHub Secrets에 저장
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

절대 워크플로우 파일에 API 키를 직접 입력하지 마세요.

### 권한 최소화

```yaml
permissions:
  contents: read        # 코드 읽기만
  pull-requests: write  # PR 코멘트 작성
  issues: write         # 이슈 코멘트 (필요시)
```

### 도구 제한

CI 환경에서는 `--allowedTools`와 `--disallowedTools`로 사용 가능한 도구를 제한하세요:

```bash
# 읽기 전용 리뷰
claude -p "코드 리뷰해줘" \
  --allowedTools "Read,Grep,Glob" \
  --disallowedTools "Bash,Edit,Write"

# 수정 허용 (격리된 환경에서만)
claude -p "버그 수정해줘" \
  --allowedTools "Read,Edit,Write,Bash(npm test *)"
```

**CI 환경의 권한 모드**: CI에서 `--dangerously-skip-permissions` 대신 `--allowedTools`로 필요한 도구만 명시적으로 허용하는 것이 더 안전합니다. 격리된 컨테이너에서만 bypass 모드를 사용하세요.

## 비용 고려사항

CI에서 Claude API를 사용하면 비용이 발생합니다. 다음 전략으로 비용을 관리하세요:

```yaml
# 특정 레이블의 PR에만 실행
if: contains(github.event.pull_request.labels.*.name, 'needs-review')

# 변경 파일 수 제한
- name: Check file count
  run: |
    COUNT=$(git diff --name-only origin/main...HEAD | wc -l)
    if [ $COUNT -gt 20 ]; then
      echo "파일 수 초과 - Claude 리뷰 스킵"
      exit 0
    fi

# 경량 모델 사용
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude_args: "--model claude-haiku-4-5-20251001"
```

## 실전 파이프라인: 전체 예시

```yaml
name: Full CI Pipeline with Claude
on:
  pull_request:
  push:
    branches: [main]
jobs:
  # 1단계: 린트 및 빌드
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - run: npm run lint

  # 2단계: 테스트
  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test -- --coverage

  # 3단계: Claude 리뷰 (PR에만 실행)
  claude-review:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            코드 리뷰 시 다음을 확인해줘:
            1. 버그와 보안 취약점
            2. 성능 문제
            3. 테스트 커버리지

  # 4단계: 배포 (main 브랜치에만)
  deploy:
    runs-on: ubuntu-latest
    needs: [build, test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "배포 스크립트 실행"
```

---

**다음 챕터**: [대규모 코드베이스](/docs/level-3/large-codebase)

**최종 수정**: 2026년 2월 28일
