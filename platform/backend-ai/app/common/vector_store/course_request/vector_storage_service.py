# /app/common/vector_store/course_request/vector_storage_service.py

from typing import List, Dict
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from pinecone import Pinecone
from openai import OpenAI
import tiktoken

settings = get_settings()

# Initialize clients
openai_client = OpenAI(api_key=settings.openai.api_key)
pc = Pinecone(api_key=settings.pinecone.api_key)
index = pc.Index(settings.pinecone.index_name_course_request)

FIELD_ORDER = [
    "problem_context",
    "goal",
    "current_attempt",
    "ai_usage_level",
    "desired_output",
    "extra_context",
]


class CourseRequestVectorStorageService:
    def __init__(self):
        self.index = index
        self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            response = openai_client.embeddings.create(
                input=texts,
                model="text-embedding-3-large"
            )
            return [r.embedding for r in response.data]
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def upsert_request_vectors(self, request_id: int, fields: Dict[str, str]) -> List[str]:
        try:
            fields = _normalize_fields(fields)
            texts = []
            field_keys = []

            for key in FIELD_ORDER:
                value = fields.get(key, "").strip()
                if value:
                    texts.append(value)
                    field_keys.append(key)

            if not texts:
                raise APIException(ErrorCode.BAD_REQUEST_BODY, details=["입력된 유효한 텍스트가 없습니다."])

            embeddings = self._embed_texts(texts)
            items = []

            for i, (text, vector) in enumerate(zip(texts, embeddings)):
                vector_id = f"request-{request_id}-{field_keys[i]}"
                items.append({
                    "id": vector_id,
                    "values": vector,
                    "metadata": {
                        "request_id": str(request_id),
                        "field": field_keys[i],
                        "text": text,
                    }
                })

            self.index.upsert(vectors=items)
            return [item["id"] for item in items]

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

def _normalize_fields(fields: Dict[str, str]) -> Dict[str, str]:
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in (fields or {}).items()}
