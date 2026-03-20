from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode


class VectorDeleteService:
    def __init__(self, index=None):
        self.index = index

    def delete_by_video_id(self, video_id: int):
        if self.index is None:
            return 0

        try:
            fake_vector = [0.0] * 3072  # Just for query API requirement
            response = self.index.query(
                vector=fake_vector,
                top_k=1000,
                filter={"video_id": str(video_id)},
                include_metadata=True
            )
            ids_to_delete = [match["id"] for match in response.get("matches", [])]
            if ids_to_delete:
                self.index.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def delete_by_video_ids(self, video_ids: list[int]) -> int:
        if self.index is None or not video_ids:
            return 0

        try:
            fake_vector = [0.0] * 3072

            response = self.index.query(
                vector=fake_vector,
                top_k=1000,
                filter={"video_id": {"$in": [str(v_id) for v_id in video_ids]}},
                include_metadata=True
            )

            ids_to_delete = [match["id"] for match in response.get("matches", [])]
            if ids_to_delete:
                self.index.delete(ids=ids_to_delete)

            return len(ids_to_delete)

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
