from pydantic import BaseModel
from typing import List


class PurchaseAssistantRequest(BaseModel):
    course_id: int
    query: str


class PurchaseAssistantUsageInfo(BaseModel):
    usage_count: int
    remaining: int


class PurchaseAssistantResponse(BaseModel):
    recommendation: str
    judgment: str
    reasons: List[str]
    usage_count: int