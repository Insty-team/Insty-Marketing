# Insty AI Backend (FastAPI)

Insty 프로젝트의 AI 백엔드입니다.  


### 패키지 설치
```bash
poetry install
```

### 로컬 서버 실행
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
### 서버 Docker로 실행
```bash
docker build -t insty-ai-backend .
docker run -p 8000:8000 --env-file .env insty-ai-backend
```

### 로컬 Redis Docker로 실행
```bash
docker run -d --name redis-dev -p 6379:6379 redis:7-alpine
```
