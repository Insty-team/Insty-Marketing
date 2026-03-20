<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/docker-environment -->

# Docker 환경

Docker는 Claude Code 에이전트를 **격리된 안전한 환경**에서 실행하기에 이상적입니다. 에이전트가 호스트 시스템에 영향을 주지 않고, 실험적인 코드 변경도 안심하고 실행할 수 있습니다.

## Docker를 써야 하는 이유

| 상황 | Docker 없이 | Docker와 함께 |
|------|-----------|------------|
| 에이전트 실수 | 호스트 파일 손상 가능 | 컨테이너만 영향 |
| 의존성 충돌 | 프로젝트 환경 오염 | 격리된 환경 |
| CI 실행 | 환경 불일치 | 재현 가능한 환경 |
| 팀 공유 | "내 PC에서는 됐는데..." | 동일한 환경 보장 |

## 기본 Dockerfile

Claude Code를 포함한 개발 환경:

```dockerfile
FROM node:20-slim

# 기본 도구 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Claude Code 설치
RUN npm install -g @anthropic-ai/claude-code

# 작업 디렉토리
WORKDIR /workspace

# 기본 git 설정 (커밋용)
RUN git config --global user.email "agent@automation.local" \
    && git config --global user.name "Claude Agent"

# 프로젝트 의존성
COPY package*.json ./
RUN npm ci
COPY . .

CMD ["bash"]
```

## 컨테이너 실행

### 기본 실행

```bash
# 이미지 빌드
docker build -t my-claude-env .

# 인터랙티브 실행 (현재 디렉토리 마운트)
docker run -it --rm \
  -v $(pwd):/workspace \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  my-claude-env \
  bash

# 컨테이너 내에서 Claude Code 실행
claude "코드베이스를 분석해줘"
```

### 헤드리스 자동화

```bash
# 단일 작업 실행 후 종료
docker run --rm \
  -v $(pwd):/workspace \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  my-claude-env \
  claude --dangerously-skip-permissions --print \
  "테스트 커버리지 90% 달성을 위해 테스트를 추가해줘"
```

## 보안 강화 설정

### 읽기 전용 볼륨

분석만 할 때는 쓰기 권한을 제거:

```bash
docker run --rm \
  -v $(pwd):/workspace:ro \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  my-claude-env \
  claude --print "보안 취약점 분석해줘"
```

### 네트워크 격리

```bash
# 인터넷 접근 차단 (내부 코드만 분석)
docker run --rm \
  --network none \
  -v $(pwd):/workspace:ro \
  my-claude-env \
  claude --print "코드 리뷰해줘"
```

### 리소스 제한

```bash
docker run --rm \
  --memory="2g" \
  --cpus="1.0" \
  -v $(pwd):/workspace \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  my-claude-env \
  claude --print "최적화해줘"
```

## Docker Compose 설정

팀에서 공유할 수 있는 설정:

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-agent:
    build: .
    volumes:
      - .:/workspace
      - claude-cache:/root/.claude  # Claude 설정 캐시
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    working_dir: /workspace
    stdin_open: true
    tty: true

  # 분석 전용 (읽기 전용)
  claude-analyzer:
    build: .
    volumes:
      - .:/workspace:ro
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    command: >
      claude --dangerously-skip-permissions --print
      "전체 코드베이스 보안 감사를 실행해줘"

volumes:
  claude-cache:
```

실행:

```bash
# 인터랙티브 에이전트
docker-compose run claude-agent

# 자동화 분석기
docker-compose run claude-analyzer
```

## CI/CD에서 Docker 활용

```yaml
# .github/workflows/claude-agent.yml
name: Claude Code Agent

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시

jobs:
  weekly-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build agent image
        run: docker build -t claude-agent .
      - name: Run security audit
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          docker run --rm \
            -v ${{ github.workspace }}:/workspace:ro \
            -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
            claude-agent \
            claude --dangerously-skip-permissions --print \
            "주간 보안 감사를 실행하고 리포트를 작성해줘" \
            > audit-report.md
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: weekly-audit-report
          path: audit-report.md
```

## 컨테이너 내 Git 작업

Docker에서 Claude Code가 커밋까지 수행하려면:

```dockerfile
FROM node:20-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /workspace

# 빌드 시 git 설정
ARG GIT_USER_EMAIL=agent@ci.local
ARG GIT_USER_NAME="Claude Agent"

RUN git config --global user.email "$GIT_USER_EMAIL" \
    && git config --global user.name "$GIT_USER_NAME" \
    && git config --global --add safe.directory /workspace
```

```bash
# SSH 키를 마운트해서 push도 가능하게
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.ssh:/root/.ssh:ro \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  claude-agent \
  claude --dangerously-skip-permissions --print \
  "버그 수정하고 커밋까지 해줘"
```

### 개발 속도 팁

Docker 이미지 빌드 시간을 줄이려면 `node_modules`를 명명된 볼륨으로 분리하세요. 코드 변경만으로 전체 의존성을 재설치하지 않아도 됩니다.

---

**최종 수정**: 2026년 2월 28일
