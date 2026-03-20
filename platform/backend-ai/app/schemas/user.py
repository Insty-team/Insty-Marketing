from pydantic import BaseModel
from typing import Dict

class User(BaseModel):
    id: int

class DeleteAIDataResponse(BaseModel):
    success: bool
    deleted_counts: Dict[str, int]