import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

from app.core.error_codes import ErrorCode

logger = logging.getLogger(__name__)

class APIException(Exception):
    def __init__(self, error: ErrorCode, details: list = None):
        self.error = error
        self.details = details

        if details:
            logger.warning(f"[{error.code}] {error.message} | details: {details}")


class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise APIException(ErrorCode.UNAUTHORIZED, details=["Authorization header is missing or invalid."])
        

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.error.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error.code,
                    "message": exc.error.message
                }
            }
        )
        
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        from app.core.error_codes import ErrorCode
        return JSONResponse(
            status_code=ErrorCode.PARAMETER_VALIDATION_ERROR.status_code,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.PARAMETER_VALIDATION_ERROR.code,
                    "message": ErrorCode.PARAMETER_VALIDATION_ERROR.message
                }
            }
        )
        
    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
        # 로그도 남기기
        logger.error(f"[{ErrorCode.INTERNAL_ERROR.code}] Response validation failed: {exc.errors()}")
        return JSONResponse(
            status_code=ErrorCode.INTERNAL_ERROR.status_code,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.code,
                    "message": ErrorCode.INTERNAL_ERROR.message
                }
            }
        )
    
