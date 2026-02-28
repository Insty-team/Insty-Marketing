#!/bin/bash
# PreCompact Hook: 컴팩션 전 핸드오버 문서 자동 생성
# stdin으로 JSON 입력 받음: { "session_id": "...", "transcript_path": "..." }

set -e

MEMORY_DIR="/home/samwoo/.claude/projects/-home-samwoo-github-repos-insty-marketing/memory"
HANDOVER_DIR="${MEMORY_DIR}/handovers"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
HANDOVER_FILE="${HANDOVER_DIR}/HANDOVER-${TIMESTAMP}.md"

# 핸드오버 디렉토리 생성
mkdir -p "$HANDOVER_DIR"

# stdin에서 JSON 입력 읽기
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

# 트랜스크립트가 있으면 핸드오버 문서 생성
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # 트랜스크립트에서 최근 내용 추출 (마지막 200줄)
  RECENT_CONTEXT=$(tail -200 "$TRANSCRIPT_PATH")

  cat > "$HANDOVER_FILE" << EOF
# Handover - ${TIMESTAMP}

## 세션 정보
- 시간: $(date '+%Y-%m-%d %H:%M:%S')
- 트랜스크립트: ${TRANSCRIPT_PATH}

## 최근 작업 컨텍스트
\`\`\`
${RECENT_CONTEXT}
\`\`\`

## 참고
- 이 파일은 PreCompact Hook에 의해 자동 생성됨
- short-term.md와 함께 참조할 것
EOF

  # short-term.md에 핸드오버 기록 추가
  echo "" >> "${MEMORY_DIR}/short-term.md"
  echo "### 핸드오버 생성: ${TIMESTAMP}" >> "${MEMORY_DIR}/short-term.md"
  echo "- 파일: handovers/HANDOVER-${TIMESTAMP}.md" >> "${MEMORY_DIR}/short-term.md"
else
  # 트랜스크립트 없이도 최소 핸드오버 생성
  cat > "$HANDOVER_FILE" << EOF
# Handover - ${TIMESTAMP}

## 세션 정보
- 시간: $(date '+%Y-%m-%d %H:%M:%S')
- 주의: 트랜스크립트를 찾을 수 없어 최소 핸드오버만 생성

## 참고
- short-term.md, mid-term.md 참조하여 컨텍스트 복구할 것
EOF
fi

# 오래된 핸드오버 정리 (30일 이상)
find "$HANDOVER_DIR" -name "HANDOVER-*.md" -mtime +30 -delete 2>/dev/null || true
