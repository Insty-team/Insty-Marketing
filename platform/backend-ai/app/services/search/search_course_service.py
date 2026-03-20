from collections import defaultdict
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session
from openai import OpenAI
from pinecone import Pinecone

from app.repositories.search.search_chat_message_repository import SearchCourseMessageRepository
from app.repositories.search.search_course_result_log_repository import SearchCourseResultLogRepository
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.repositories.course.course_repository import CourseRepository
from app.repositories.file.file_repository import FileRepository

from app.schemas.search import (
    RecommendedCourse,
    RecommendationHistoryResponse,
    UserMessageItem,
    AssistantMessageItem,
)

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from app.utils.prompt_loader import load_prompt
from app.utils.clean_gpt_text import enforce_html_breaks
from app.utils.s3_to_cloudfront_url import convert_s3_to_cloudfront_url
from app.utils.query_expander import expand_queries

settings = get_settings()

openai_client = OpenAI(api_key=settings.openai.api_key)
pinecone = Pinecone(api_key=settings.pinecone.api_key)
index = pinecone.Index(settings.pinecone.index_name)

SIMILARITY_THRESHOLD = 0.3

# RRF 결합 상수
RRF_K = 60
MAX_EXPANSIONS = 5  # query_expander가 생성할 최대 확장 수


class SearchCourseService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = SearchCourseMessageRepository(db)
        self.result_repo = SearchCourseResultLogRepository(db)
        self.video_repo = VideoCourseRepository(db)
        self.course_repo = CourseRepository(self.db)
        self.file_repo = FileRepository(db)

    def recommend_for_guest(self, query: str, top_k: int = 3, search_k: int = 20) -> dict:
        try:
            recommendation_message, courses, _ = self._build_recommendation_result(
                query=query,
                top_k=top_k,
                search_k=search_k
            )
            return {"message": recommendation_message, "courses": courses}
        except APIException:
            raise
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def recommend(self, user_id: int, query: str, top_k: int = 3, search_k: int = 20) -> dict:
        try:
            user_message = self.chat_repo.create(
                user_id=user_id,
                sender_type="user",
                message_text=query,
                has_recommendation=False
            )

            recommendation_message, courses, course_ids_in_rank_order = self._build_recommendation_result(
                query=query,
                top_k=top_k,
                search_k=search_k
            )

            self.chat_repo.update_has_recommendation(user_message.id, True)

            for rank, course_id in enumerate(course_ids_in_rank_order, start=1):
                self.result_repo.create(
                    message_id=user_message.id,
                    user_id=user_id,
                    course_id=course_id,
                    rank=rank
                )

            self.chat_repo.create(
                user_id=user_id,
                sender_type="assistant",
                message_text=recommendation_message,
                has_recommendation=True
            )

            return {"message": recommendation_message, "courses": courses}
        except APIException:
            raise
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _build_recommendation_result(
        self,
        query: str,
        top_k: int = 3,
        search_k: int = 20
    ) -> Tuple[str, List[Dict], List[int]]:
        # 확장 질의 생성
        expanded = expand_queries(query, n=MAX_EXPANSIONS)
        all_queries = [query] + [q for q in expanded if q.strip().lower() != query.strip().lower()]

        # 배치 임베딩
        query_vectors = self._embed_queries(all_queries)

        # per-query top_k 예산 분배
        per_query_k = max(1, search_k // len(all_queries))

        # RRF 점수 결합 구조
        rrf_scores = defaultdict(float)  # video_id -> fused score
        video_texts: Dict[int, str] = {}  # video_id -> 대표 텍스트

        for q_vec in query_vectors:
            resp = index.query(
                vector=q_vec,
                top_k=per_query_k,
                include_metadata=True
            )

            for rank, match in enumerate(resp.get("matches", []), start=1):
                metadata = match.get("metadata") or {}
                score = match.get("score", 0.0)

                vid_raw = metadata.get("video_id")
                try:
                    vid = int(vid_raw)
                except (ValueError, TypeError):
                    continue

                chunk_text = metadata.get("text")
                if not chunk_text or score < SIMILARITY_THRESHOLD:
                    continue

                rrf_scores[vid] += 1.0 / (RRF_K + rank)

                if vid not in video_texts:
                    video_texts[vid] = chunk_text

        if not rrf_scores:
            not_found_message = (
                "관련된 영상을 찾을 수 없습니다.<br>"
                "[강의 요청을 하시겠습니까? 여기를 클릭해주세요.](https://docs.google.com/forms/d/e/1FAIpQLSdfy0jpk-zmcQoNgzI_H76TcPZjCVU9CkBDMCEl1Mb9uqzIdQ/viewform)"
            )
            return not_found_message, [], []

        sorted_video_scores = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # video 기준으로는 더 많이 뽑되, course 기준으로 top_k를 안정적으로 맞추기 위해 search_k를 상한으로 사용
        candidate_video_limit = [int(vid) for vid, _ in sorted_video_scores[:max(top_k, min(search_k, len(sorted_video_scores)))]]

        video_objs = self.video_repo.get_by_video_ids(candidate_video_limit)

        # video.id -> course.id 매핑
        video_id_to_course_id: Dict[int, int] = {}
        for video in video_objs:
            course_id = getattr(video, "course_id", None)
            if course_id is None and getattr(video, "course", None) is not None:
                course_id = getattr(video.course, "id", None)
            if course_id is None:
                continue
            video_id_to_course_id[video.id] = int(course_id)

        filtered_candidate_video_ids = [vid for vid in candidate_video_limit if vid in video_id_to_course_id]
        if not filtered_candidate_video_ids:
            not_found_message = (
                "관련된 강의를 찾을 수 없습니다.<br>"
                "강의 등록 상태를 확인한 뒤 다시 시도해주세요."
            )
            return not_found_message, [], []

        # course 단위로 순서 유지 dedupe (top_k 보장)
        course_ids_in_rank_order: List[int] = []
        seen_course_ids = set()

        # 대표 텍스트는 "최초로 선택된 video" 기준으로 가져오기 위해 course_id -> video_id를 기록
        course_id_to_representative_video_id: Dict[int, int] = {}

        for vid in filtered_candidate_video_ids:
            course_id = video_id_to_course_id[vid]
            if course_id in seen_course_ids:
                continue

            seen_course_ids.add(course_id)
            course_ids_in_rank_order.append(course_id)
            course_id_to_representative_video_id[course_id] = vid

            if len(course_ids_in_rank_order) >= top_k:
                break

        if not course_ids_in_rank_order:
            not_found_message = (
                "관련된 강의를 찾을 수 없습니다.<br>"
                "강의 등록 상태를 확인한 뒤 다시 시도해주세요."
            )
            return not_found_message, [], []

        # 추천 메시지 생성에 사용할 텍스트: video_id 기준으로 대표 video 텍스트 모으기
        filtered_video_texts: Dict[int, str] = {}
        for course_id, representative_vid in course_id_to_representative_video_id.items():
            if representative_vid in video_texts:
                filtered_video_texts[representative_vid] = video_texts[representative_vid]

        recommendation_message = self._generate_recommendation_message(query, filtered_video_texts)

        # course 정보 조회 및 썸네일 조립
        course_objs = self.course_repo.get_by_ids(course_ids_in_rank_order)
        course_id_to_title = {course.id: course.title for course in course_objs}

        courses: List[Dict] = []
        for course_id in course_ids_in_rank_order:
            status, video_uuid = self.course_repo.get_thumbnail_status(course_id)

            if status == "custom":
                file = self.file_repo.get_course_thumbnail_by_course_id(course_id)
                if not file or not file.name:
                    raise Exception(f"Missing thumbnail file for course_id={course_id}")
                thumbnail_url = convert_s3_to_cloudfront_url(
                    f"/file/COURSE_THUMBNAIL/{file.container_id}/{file.name}"
                )
            elif status == "default" and video_uuid:
                thumbnail_url = convert_s3_to_cloudfront_url(
                    f"/file/VIDEO_BASIC_THUMBNAIL/{video_uuid}/basic_thumbnail.jpg"
                )
            else:
                thumbnail_url = None

            courses.append({
                "course_id": str(course_id),
                "course_title": course_id_to_title.get(course_id, "제목 없음"),
                "thumbnail_url": thumbnail_url
            })

        return recommendation_message, courses, course_ids_in_rank_order

    def _embed_queries(self, queries: List[str]) -> List[List[float]]:
        try:
            resp = openai_client.embeddings.create(
                input=queries,
                model="text-embedding-3-large"
            )
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _embed_query(self, query: str) -> List[float]:
        try:
            response = openai_client.embeddings.create(
                input=[query],
                model="text-embedding-3-large"
            )
            return response.data[0].embedding
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def _generate_recommendation_message(self, query: str, video_texts: Dict[int, str]) -> str:
        try:
            prompt = load_prompt("recommendation_prompt.j2", {
                "query": query,
                "video_texts": video_texts
            })

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.choices[0].message.content.strip()
            return enforce_html_breaks(raw)
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])

    def get_recommend_courses(self, user_id: int) -> RecommendationHistoryResponse:
        try:
            raw_messages = self.chat_repo.get_message_history_with_courses(user_id)

            all_course_ids = {
                course_id
                for msg in raw_messages
                if msg["sender"] == "assistant" and "course_ids" in msg
                for course_id in msg["course_ids"]
            }

            videos = self.video_repo.get_by_course_ids(list(all_course_ids))
            video_dict = {video.course_id or video.id: video for video in videos}

            course_objs = self.course_repo.get_by_ids(list(all_course_ids))
            course_id_to_title = {course.id: course.title for course in course_objs}

            thumbnail_map = {}
            for course_id, video in video_dict.items():
                status, video_uuid = self.course_repo.get_thumbnail_status(course_id)

                if status == "custom":
                    file = self.file_repo.get_course_thumbnail_by_course_id(course_id)
                    if file and file.name:
                        url = convert_s3_to_cloudfront_url(
                            f"/file/COURSE_THUMBNAIL/{file.container_id}/{file.name}"
                        )
                    else:
                        url = None
                elif status == "default" and video_uuid:
                    url = convert_s3_to_cloudfront_url(
                        f"/file/VIDEO_BASIC_THUMBNAIL/{video_uuid}/basic_thumbnail.jpg"
                    )
                else:
                    url = None

                thumbnail_map[str(course_id)] = {
                    "course_title": course_id_to_title.get(course_id, "제목 없음"),
                    "thumbnail_url": url
                }

            messages = []
            for msg in raw_messages:
                if msg["sender"] == "user":
                    messages.append(UserMessageItem(
                        message_id=msg["message_id"],
                        sender="user",
                        content=msg["content"],
                        created_at=msg["created_at"]
                    ))

                elif msg["sender"] == "assistant":
                    courses = []

                    if "course_ids" in msg:
                        for cid in msg["course_ids"]:
                            cid_str = str(cid)
                            course_info = thumbnail_map.get(cid_str)
                            if course_info:
                                courses.append(RecommendedCourse(
                                    course_id=cid_str,
                                    course_title=course_info["course_title"],
                                    thumbnail_url=course_info["thumbnail_url"]
                                ))

                    messages.append(AssistantMessageItem(
                        message_id=msg["message_id"],
                        sender="assistant",
                        content=msg["content"],
                        courses=courses,
                        created_at=msg["created_at"]
                    ))

            return RecommendationHistoryResponse(messages=messages)

        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[str(e)])
