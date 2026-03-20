from pydantic import BaseModel
from typing import Optional, Generic, TypeVar

T = TypeVar("T")

class ErrorModel(BaseModel):
    code: str
    message: str
    details: Optional[str] = None

class ResponseModel(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None