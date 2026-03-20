from typing import List, Dict, Optional
from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from pinecone import Pinecone
from openai import OpenAI

settings = get_settings()
pc = Pinecone(api_key=settings.pinecone.api_key)

FIELD_WEIGHTS = {
    "problem_context": 0.30,
    "goal": 0.25,
    "current_attempt": 0.15,
    "desired_output": 0.15,
    "ai_usage_level": 0.10,
    "extra_context": 0.05
}

class CourseRequestVectorSearchService:
    def __init__(self):
        self.request_index = pc.Index(settings.pinecone.index_name_course_request)
        self.video_index = pc.Index(settings.pinecone.index_name)

    def search_similar_request_ids_from_video_ids(
        self,
        video_ids: List[int],
        top_k: int = 20,
        exclude_request_ids: Optional[List[int]] = None
    ) -> Dict[int, Dict]:
        try:
            if not video_ids:
                return {}

            video_vectors = []
            for video_id in video_ids:
                video_result = self.video_index.query(
                    vector=[0.0] * 3072,
                    top_k=100,
                    include_values=True,
                    include_metadata=True,
                    filter={"video_id": str(video_id)}
                )

                matches = video_result.get("matches", [])

                for match in matches:
                    video_vectors.append({
                        "vector": match["values"],
                        "video_text": match["metadata"].get("text", "")
                    })

            if not video_vectors:
                return {}

            request_matches: Dict[int, Dict[str, Dict]] = {}

            for item in video_vectors:
                vector = item["vector"]
                video_text = item["video_text"]

                # ★ filter에 request_id $nin 추가
                query_filter = {}
                if exclude_request_ids:
                    # Pinecone 필드가 string으로 저장되어 있으므로, str 변환 필요
                    query_filter["request_id"] = {"$nin": [str(rid) for rid in exclude_request_ids]}

                search_result = self.request_index.query(
                    vector=vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=query_filter if query_filter else None  # ★
                )

                matches = search_result.get("matches", [])

                for match in matches:
                    vector_id = match["id"]
                    score = match["score"]
                    metadata = match.get("metadata", {}) or {}
                    request_id_str = str(metadata.get("request_id") or "")
                    field = (metadata.get("field") or "").strip()

                    if request_id_str.isdigit():
                        request_id = int(request_id_str)
                    else:
                        parts = vector_id.split("-")
                        if len(parts) < 3 or not parts[1].isdigit():
                            continue
                        request_id = int(parts[1])
                    if not field:
                        parts = vector_id.split("-")
                        if len(parts) < 3:
                            continue
                        field = parts[2]

                    if field not in FIELD_WEIGHTS:
                        continue

                    if request_id not in request_matches:
                        request_matches[request_id] = {}

                    if field not in request_matches[request_id] or request_matches[request_id][field]["similarity"] < score:
                        request_text = (metadata.get("text") or "").strip()
                        if not request_text:
                            # metadata에 text가 없을 때 안전한 기본값
                            request_text = "[요청 내용 없음]"
                        request_matches[request_id][field] = {
                            "similarity": score,
                            "request_text": request_text,
                            "video_text": video_text
                        }

            if not request_matches:
                raise APIException(ErrorCode.NO_VECTOR_MATCHES_FOUND)

            request_id_to_score: Dict[int, Dict] = {}
            total_weight_all = sum(FIELD_WEIGHTS.values())

            for request_id, field_data in request_matches.items():
                weighted_sum = 0.0

                for field_key, weight in FIELD_WEIGHTS.items():
                    similarity = field_data.get(field_key, {}).get("similarity", 0.0)
                    weighted_sum += similarity * weight

                final_score = weighted_sum / total_weight_all if total_weight_all > 0 else 0.0

                eligible_items = [(k, v) for k, v in field_data.items() if k in FIELD_WEIGHTS]
                if not eligible_items:
                    continue

                best_field, best_info = max(
                    eligible_items,
                    key=lambda x: x[1]["similarity"] * FIELD_WEIGHTS.get(x[0], 0.0)
                )

                request_id_to_score[request_id] = {
                    "max_score": final_score,
                    "details": [
                        {
                            "field": best_field,
                            "similarity": best_info["similarity"],
                            "request_text": best_info["request_text"],
                            "video_text": best_info["video_text"]
                        }
                    ]
                }

            if not request_id_to_score:
                raise APIException(ErrorCode.NO_VECTOR_MATCHES_FOUND)
            return request_id_to_score

        except APIException:
            raise
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def search_similar_request_ids_from_creator_vectors(
        self,
        creator_vectors: Dict[str, List[float]],
        top_k: int = 20,
        exclude_request_ids: Optional[List[int]] = None  # ★ 추가
    ) -> Dict[int, Dict[str, float]]:

        request_matches: Dict[int, Dict[str, float]] = {}

        for field_key, vector in creator_vectors.items():
            # 바뀐 6key 아닌 기존요청이면 Fail
            if field_key not in FIELD_WEIGHTS:
                continue

            if not vector:
                continue

            # ★ filter에 request_id $nin 추가
            query_filter = {"field": field_key}
            if exclude_request_ids:
                query_filter["request_id"] = {"$nin": [str(rid) for rid in exclude_request_ids]}

            try:
                result = self.request_index.query(
                    vector=vector,
                    top_k=top_k,
                    include_metadata=True,
                    filter=query_filter  # ★
                )
            except Exception as e:
                raise APIException(ErrorCode.NO_VECTOR_MATCHES_FOUND, details=[f"{field_key} 검색 실패: {str(e)}"])

            matches = result.get("matches", [])
            for match in matches:
                vector_id = match["id"]
                score = match["score"]
                metadata = match.get("metadata", {}) or {}

                request_id_str = str(metadata.get("request_id") or "")

                if request_id_str.isdigit():
                    request_id = int(request_id_str)
                else:
                    parts = vector_id.split("-")
                    if len(parts) < 3 or not parts[1].isdigit():
                        continue
                    request_id = int(parts[1])

                if request_id not in request_matches:
                    request_matches[request_id] = {}

                # 동일 필드가 여러 벡터와 매칭될 수 있으므로 최고 점수만 유지
                if field_key not in request_matches[request_id] or request_matches[request_id][field_key] < score:
                    request_matches[request_id][field_key] = score

        return request_matches
