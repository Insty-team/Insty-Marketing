import logging
import uvicorn
import threading
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.utils.sqs_listener import start_sqs_listener
from app.docs.loader import inject_openapi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(f"실행 환경: {settings.ENVIRONMENT}")

def custom_generate_unique_id(route: APIRoute) -> str:
    op_id = getattr(route.endpoint, "__operation_id__", None)
    if op_id:
        return op_id
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    docs_url="/api/v1/ai/docs",
    # redoc_url=None,  # 필요시 주석 해제
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
register_exception_handlers(app)

inject_openapi(app, locale="ko")

@app.on_event("startup")
def start_sqs_listener_thread():
    thread = threading.Thread(target=start_sqs_listener, daemon=True)
    thread.start()
    logger.info("SQS 리스너 스레드 시작 완료")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)