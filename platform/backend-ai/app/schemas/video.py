from pydantic import BaseModel
from typing import List, Optional

class TranscribeVideoRequest(BaseModel):
    file_url: str


class TranscribeVideoResponse(BaseModel):
    video_id: int


class MetadataSuggestionResponse(BaseModel):
    title: str
    description: str
    price: str
    target: str
    tags: List[str]
    installation_checklist: List[str] 
    core_contents: List[str]          


class TitleSuggestionRequest(BaseModel):
    original_title: str


class TitleSuggestionResponse(BaseModel):
    title: str


class DescriptionSuggestionRequest(BaseModel):
    original_description: str
    

class DescriptionSuggestionResponse(BaseModel):
    description: str
    

class TranscriptionStatusResponse(BaseModel):
    status: str
    progress: int
    step: str
    reason: Optional[str] = None
    

class VectorStatusResponse(BaseModel):
    status: str
    progress: int
    step: str
    
    
class PracticeGuideSuggestionResponse(BaseModel):
    practice_draft: str
