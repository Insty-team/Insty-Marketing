from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from pinecone import Pinecone

settings = get_settings()
pc = Pinecone(api_key=settings.pinecone.api_key)
index = pc.Index(settings.pinecone.index_name_course_request)

class CourseRequestVectorDeleteService:
    def __init__(self):
        self.index = index

    def delete_request_vectors(self, request_id: int):
        try:
            self.index.delete(filter={"request_id": str(request_id)})
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
