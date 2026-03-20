from typing import List
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode
from app.repositories.video.video_course_repository import VideoCourseRepository
from pinecone import Pinecone
from openai import OpenAI

settings = get_settings()

openai_client = OpenAI(api_key=settings.openai.api_key)
pc = Pinecone(api_key=settings.pinecone.api_key)
index = pc.Index(settings.pinecone.index_name)


class VectorSearchService:
    def __init__(self, video_course_repo: VideoCourseRepository):
        self.index = index
        self.video_course_repo = video_course_repo

    def search_similar_chunks(self, course_id: int, query: str, top_k: int = 5) -> List[str]:
        try:
            video_course = self.video_course_repo.get_by_course_id(course_id)            # course_id로 video_id 조회
            if not video_course:
                raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["해당 course_id에 대한 비디오가 없습니다."])

            video_id = video_course.id

            embedding_response = openai_client.embeddings.create(            # 임베딩 생성
                input=query,
                model="text-embedding-3-large"
            )
            query_vector = embedding_response.data[0].embedding

            search_result = self.index.query(            # 벡터 검색
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={"video_id": str(video_id)}
            )

            chunks = [match.metadata.get("text", "") for match in search_result.get("matches", [])]
            return chunks

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
