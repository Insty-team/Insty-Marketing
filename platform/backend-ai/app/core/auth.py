from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional

from app.core.exceptions import APIException, CustomHTTPBearer
from app.core.error_codes import ErrorCode
from app.schemas.user import User
from app.core.config import get_settings

security = CustomHTTPBearer()
optional_security = CustomHTTPBearer(auto_error=False)
settings = get_settings()
ALGORITHM = "HS512"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise APIException(ErrorCode.UNAUTHORIZED, details=["Token payload invalid."])

        return User(id=int(user_id))

    except ExpiredSignatureError:
        raise APIException(ErrorCode.UNAUTHORIZED, details=["Token has expired."])
    except JWTError:
        raise APIException(ErrorCode.UNAUTHORIZED, details=["Invalid JWT token."])

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[User]:
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return User(id=int(user_id))
    except (ExpiredSignatureError, JWTError):
        return None