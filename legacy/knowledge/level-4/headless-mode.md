<!-- 원본: https://claude-code-playbook-nu.vercel.app/docs/level-4/headless-mode -->

# Headless 자동화 모드

Headless 모드는 Claude Code를 대화 없이 **스크립트나 파이프라인에서 직접 실행**하는 방식입니다. CI/CD, 배치 작업, 코드 생성 자동화 등에 활용합니다.

### 공식 명칭 변경

Anthropic 공식 문서에서는 이 기능을 **Agent SDK CLI**로 리브랜딩했습니다. `-p` 플래그와 모든 CLI 옵션은 동일하게 작동합니다.

## `--print` 플래그

`--print` (`-p`) 플래그를 사용하면 Claude Code가 단일 요청을 처리하고 결과를 stdout으로 출력한 뒤 종료합니다.

```bash
# 기본 사용법
claude --print "이 함수의 복잡도를 분석해줘" < src/complex.ts

# 파일 내용 파이프
cat error.log | claude --print "에러 원인 분석해줘"

# 결과를 파일로 저장
claude --print "API 명세 작성해줘" > docs/api.md
```

## 권한 자동 승인

헤드리스 환경에서는 사용자 승인이 불가능하므로 권한을 사전 설정합니다:

```bash
# 모든 권한 자동 승인 (격리된 CI 환경에서만 사용)
claude --dangerously-skip-permissions --print "코드 수정해줘"
```

또는 `settings.json`으로 특정 도구만 자동 승인:

```json
{
  "permissions": {
    "allow": ["Read(*)", "Write(*)", "Edit(*)", "Bash(npm test)"],
    "deny": ["Bash(rm *)"]
  }
}
```

## 실전 자동화 스크립트

### 배치 파일 처리

여러 파일을 자동으로 처리:

```bash
#!/bin/bash
# 모든 TypeScript 파일에 JSDoc 추가
for file in src/**/*.ts; do
  echo "처리 중: $file"
  claude --print "이 파일의 공개 함수와 클래스에 JSDoc 주석을 추가해줘.
  기존 코드 로직은 변경하지 말고 주석만 추가해줘." < "$file" > "${file}.tmp"
  # 결과 검증 후 교체
  if [ -s "${file}.tmp" ]; then
    mv "${file}.tmp" "$file"
  else
    rm "${file}.tmp"
    echo "경고: $file 처리 실패"
  fi
done
echo "완료!"
```

### 코드 리뷰 리포트 자동 생성

```bash
#!/bin/bash
# PR 리뷰 리포트 생성
BRANCH=${1:-HEAD}
BASE=${2:-main}
DIFF=$(git diff $BASE...$BRANCH)

if [ -z "$DIFF" ]; then
  echo "변경사항 없음"
  exit 0
fi

echo "$DIFF" | claude --print "이 코드 변경사항을 리뷰해줘.
다음 형식으로 마크다운 리포트를 작성해줘:

## 요약
## 주요 변경사항
## 잠재적 문제
## 개선 제안
## 승인 여부 (승인 / 수정 요청)" > review-report.md

echo "리뷰 리포트 생성 완료: review-report.md"
```

### 자동 마이그레이션

```bash
#!/bin/bash
# API v1 → v2 마이그레이션
FILES=$(grep -rl "api/v1" src/)

for file in $FILES; do
  echo "마이그레이션: $file"
  cat "$file" | claude --print "이 파일에서 'api/v1' 엔드포인트를 'api/v2'로 업데이트해줘.
  엔드포인트 경로만 변경하고, 로직은 그대로 유지해줘.
  수정된 전체 파일 내용만 출력해줘 (설명 없이)." > "$file.migrated"
  mv "$file.migrated" "$file"
done
```

## 출력 형식 (`--output-format`)

`--output-format` 플래그로 응답 형식을 제어합니다:

| 형식 | 설명 | 용도 |
|------|------|------|
| `text` | 일반 텍스트 (기본값) | 사람이 읽는 경우 |
| `json` | 구조화된 JSON (세션 ID, 메타데이터 포함) | 스크립트에서 파싱 |
| `stream-json` | 줄바꿈 구분 JSON 스트리밍 | 실시간 처리 |

```bash
# JSON 형식으로 결과 받기
claude -p "프로젝트 요약해줘" --output-format json

# jq로 결과 텍스트만 추출
claude -p "프로젝트 요약해줘" --output-format json | jq -r '.result'
```

### JSON 스키마로 구조화된 출력

`--json-schema`로 원하는 출력 형식을 강제할 수 있습니다:

```bash
# 함수 이름을 배열로 추출
claude -p "auth.py의 함수 이름을 추출해줘" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}'

# 구조화된 출력은 .structured_output 필드에 반환
claude -p "코드 분석해줘" --output-format json --json-schema '...' | jq '.structured_output'
```

### 실시간 스트리밍

```bash
# 토큰이 생성될 때마다 실시간으로 수신
claude -p "재귀 설명해줘" --output-format stream-json --verbose

# 텍스트만 실시간으로 출력
claude -p "시를 써줘" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

## 대화 이어가기 (`--continue`, `--resume`)

헤드리스에서도 멀티턴 대화가 가능합니다:

```bash
# 첫 요청
claude -p "이 코드베이스의 성능 문제를 검토해줘"

# 가장 최근 대화 이어가기
claude -p "데이터베이스 쿼리에 집중해줘" --continue
claude -p "발견된 문제들을 요약해줘" --continue
```

여러 대화를 동시에 관리하려면 세션 ID를 사용합니다:

```bash
# 세션 ID 캡처
session_id=$(claude -p "리뷰 시작" --output-format json | jq -r '.session_id')

# 특정 세션 이어가기
claude -p "리뷰 계속해줘" --resume "$session_id"
```

## 도구 자동 승인 (`--allowedTools`)

특정 도구를 프롬프트 없이 자동 승인합니다:

```bash
# 파일 읽기/편집과 Bash 허용
claude -p "테스트 실행하고 실패 수정해줘" \
  --allowedTools "Bash,Read,Edit"

# 커밋 생성 (git 명령어만 허용)
claude -p "스테이징된 변경사항으로 적절한 커밋 만들어줘" \
  --allowedTools "Bash(git diff *),Bash(git log *),Bash(git status *),Bash(git commit *)"
```

### 접미사 `*`로 패턴 매칭

`Bash(git diff *)`는 `git diff`로 시작하는 모든 명령을 허용합니다. `*` 앞의 공백이 중요합니다 -- 없으면 `git diff-index` 같은 다른 명령까지 매칭됩니다.

## 시스템 프롬프트 커스터마이즈

```bash
# 기존 시스템 프롬프트에 추가
gh pr diff "$1" | claude -p \
  --append-system-prompt "보안 엔지니어 관점에서 취약점을 검토해줘." \
  --output-format json

# 시스템 프롬프트 전체 교체
claude -p "코드 분석해줘" \
  --system-prompt "너는 성능 최적화 전문가야."
```

## 환경변수 활용

헤드리스 스크립트에서 컨텍스트를 주입:

```bash
#!/bin/bash
# 환경별 설정 주입
ENVIRONMENT=${APP_ENV:-development}
DB_TYPE=${DB_TYPE:-postgresql}

claude --print "이 마이그레이션 스크립트를 $ENVIRONMENT 환경의
$DB_TYPE 데이터베이스에 맞게 수정해줘." < migration.sql
```

## 에러 처리와 재시도

```bash
#!/bin/bash
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  RESULT=$(claude --print "코드 분석해줘" < src/main.ts 2>&1)
  EXIT_CODE=$?

  if [ $EXIT_CODE -eq 0 ]; then
    echo "$RESULT"
    break
  else
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "실패 ($RETRY_COUNT/$MAX_RETRIES): $RESULT"
    sleep 5
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "최대 재시도 초과"
  exit 1
fi
```

## Make/Task Runner 통합

`Makefile`에 Claude 작업 추가:

```makefile
# Makefile
review:
	@echo "코드 리뷰 실행..."
	@git diff main...HEAD | claude --print "코드 리뷰해줘" > review.md
	@echo "리뷰 완료: review.md"

docs:
	@find src -name "*.ts" -exec sh -c \
	  'claude --print "이 파일 API 문서 생성해줘" < {} > docs/{}.md' \;

migrate:
	@claude --print "이 스키마 변경사항에 맞는 마이그레이션 생성해줘" \
	  < schema.diff > migrations/$$(date +%Y%m%d_%H%M%S)_auto.sql
```

## 헤드리스 모드 주의사항

* `--dangerously-skip-permissions`는 반드시 격리된 환경(Docker, CI 샌드박스)에서만 사용
* 헤드리스로 생성된 코드는 반드시 사람이 검토 후 배포
* 비용 모니터링 필수 -- 대량 배치 처리 시 예상치 못한 비용 발생 가능

---

**최종 수정**: 2026년 2월 28일
