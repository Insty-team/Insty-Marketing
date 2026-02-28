#!/bin/bash
set -e

case "${1:-cron}" in
  cron)
    echo "[entrypoint] Starting cron mode..."
    # .env를 cron 환경에 주입
    env | grep -E '^(YOUTUBE_|GEMINI_|NOTION_|AI_)' >> /etc/environment
    cron -f
    ;;
  manual)
    echo "[entrypoint] Running full pipeline (manual)..."
    python -m scripts.run_pipeline
    ;;
  discovery)
    echo "[entrypoint] Running discovery only..."
    python -m scripts.run_discovery
    ;;
  script)
    echo "[entrypoint] Running script generation only..."
    python -m scripts.run_script_gen
    ;;
  keywords)
    echo "[entrypoint] Refreshing keywords..."
    python -m scripts.run_keyword_refresh
    ;;
  *)
    exec "$@"
    ;;
esac
