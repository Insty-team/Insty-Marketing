FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY config/ config/
COPY src/ src/
COPY prompts/ prompts/
COPY scripts/ scripts/
COPY docs/ docs/

# 출력 디렉토리
RUN mkdir -p output/csv output/logs

# 크론잡 설정 (주 3회: 월/수/금 09:00 KST)
COPY scripts/crontab /etc/cron.d/pipeline-cron
RUN chmod 0644 /etc/cron.d/pipeline-cron && crontab /etc/cron.d/pipeline-cron

# 엔트리포인트
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["cron"]
