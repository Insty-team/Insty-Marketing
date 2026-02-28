#!/bin/bash
# SessionStart Hook: 세션 시작 시 프로젝트 컨텍스트를 stdout으로 출력
# Claude가 이 출력을 컨텍스트로 받아 이전 작업을 이어갈 수 있음

set -e

# 프로젝트 루트 (git root 기준)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

echo "=== 세션 컨텍스트 자동 로드 ==="

# 1. 진행 상황 (docs/progress.md)
if [ -f "${PROJECT_ROOT}/docs/progress.md" ]; then
  echo ""
  echo "--- 진행 상황 ---"
  head -30 "${PROJECT_ROOT}/docs/progress.md"
fi

# 2. 핸드오버가 있으면 최근 것 표시 (로컬)
MEMORY_DIR="${HOME}/.claude/projects/-home-samwoo-github-repos-insty-marketing/memory"
HANDOVER_DIR="${MEMORY_DIR}/handovers"
if [ -d "$HANDOVER_DIR" ]; then
  LATEST_HANDOVER=$(ls -t "$HANDOVER_DIR"/HANDOVER-*.md 2>/dev/null | head -1)
  if [ -n "$LATEST_HANDOVER" ]; then
    echo ""
    echo "--- 최근 핸드오버 ---"
    head -30 "$LATEST_HANDOVER"
  fi
fi

echo ""
echo "=== 프로젝트 지식은 docs/ 디렉토리 참조. CLAUDE.md 자동 로드됨. ==="
