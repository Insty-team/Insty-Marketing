FROM python:3.10-slim

# 1. 시스템 패키지 업데이트 및 의존성 설치 (psycopg3 + ffmpeg 포함)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc ffmpeg \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Poetry 설치
RUN pip install --no-cache-dir poetry

# 4. Poetry 관련 파일 복사
COPY poetry.lock pyproject.toml /app/

# 5. 가상환경 없이 poetry 설치
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --only main,dev

# 6. 전체 프로젝트 복사
COPY . /app

# 7. 앱 실행 (FastAPI 서버)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
