from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import APIException
from app.docs.deco import op


router = APIRouter()

@op("ai_health_ping", tags=["health"])
@router.get("/ping", tags=["Health"])
def ping():
    return {"status": "ok"}


@op("ai_health_check_db", tags=["health"])
@router.get("/health/db", tags=["Health"])
def check_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {"db": "ok"}
        raise APIException(ErrorCode.DB_CONNECTION_FAILED)
    except Exception as e:
        raise APIException(ErrorCode.DB_CONNECTION_FAILED, details=[str(e)])