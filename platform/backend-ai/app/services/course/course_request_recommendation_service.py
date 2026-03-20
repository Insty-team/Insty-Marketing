from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import APIException
from app.core.error_codes import ErrorCode

from app.schemas.community import (
    CourseRequestRecommendationResponse,
    CourseRequestRecommendationItem,
    SelectedFieldItem,
    CreatorInterestForm,
    CourseRequestAvailabilityResponse
)

from app.models.creator_recommendation import CreatorRecommendationFormAnswer

from app.repositories.course.course_request_repository import CourseRequestRepository
from app.repositories.course.creator_recommendation_repository import CreatorRecommendationRepository
from app.repositories.course.creator_recommendation_form_repository import CreatorRecommendationFormRepository
from app.repositories.video.video_course_repository import VideoCourseRepository

from app.common.vector_store.course_request.vector_search_service import CourseRequestVectorSearchService, FIELD_WEIGHTS
from app.utils.prompt_loader import load_prompt

settings = get_settings()
client = OpenAI(api_key=settings.openai.api_key)


class CourseRequestRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.video_course_repo = VideoCourseRepository(db)
        self.vector_search_service = CourseRequestVectorSearchService()
        self.course_request_repo = CourseRequestRepository(db)
        self.creator_recommendation_repo = CreatorRecommendationRepository(db)  
        self.creator_recommendation_form_repo = CreatorRecommendationFormRepository(db)  

    def recommend_with_base(self, creator_id: int) -> CourseRequestRecommendationResponse:
        video_ids = self.video_course_repo.get_uploaded_video_ids(creator_id)
        if not video_ids:
            raise APIException(ErrorCode.NO_UPLOADED_VIDEOS, details=["업로드된 영상이 없습니다."])

        excludable_requests = self.course_request_repo.get_excludable_requests(creator_id)
        exclude_request_ids = [req.id for req in excludable_requests]

        return self._recommend_based_on_uploaded_videos(creator_id, video_ids, exclude_request_ids)

    def recommend_without_base(self, creator_id: int, form: CreatorInterestForm) -> CourseRequestRecommendationResponse:
        # 1. 병합된 field_key → text (임베딩용)
        form_answers_for_embedding = [
            CreatorRecommendationFormAnswer(
                field_id=ans.field_id,
                answer_text=ans.answer_text,
                answer_options=ans.answer_option_ids,
            )
            for ans in form.answers
        ]
        field_key_to_text = self.creator_recommendation_form_repo.get_creator_fields_flat_from_instances(
            answers=form_answers_for_embedding
        )

        # 2. OpenAI 임베딩 (DB 작업 전에 끝내기)
        creator_vectors = self._embed_fields_to_vectors(field_key_to_text)

        # 3. Pinecone 벡터 검색
        excludable_requests = self.course_request_repo.get_excludable_requests(creator_id)
        exclude_request_ids = [req.id for req in excludable_requests]

        request_matches = self.vector_search_service.search_similar_request_ids_from_creator_vectors(
            creator_vectors=creator_vectors,
            top_k=20,
            exclude_request_ids=exclude_request_ids
        )
        if not request_matches:
            raise APIException(ErrorCode.NO_SIMILAR_REQUESTS_FOUND)


        # 4. 가중 평균 점수 계산
        scored_requests = self._compute_weighted_scores(request_matches)

        # 5. 상위 3개 요청 선택
        sorted_requests = sorted(scored_requests.items(), key=lambda x: x[1], reverse=True)
        top_pairs = sorted_requests[:3]
        top_request_ids = [rid for rid, _ in top_pairs]

        # 6. 요청 상세 조회
        req_map = self.course_request_repo.get_request_with_answers(top_request_ids)
        recommendations: List[CourseRequestRecommendationItem] = []

        for request_id, score in top_pairs:
            data = req_map.get(request_id)
            if not data:
                continue

            title = data.get("title")
            description = data.get("description")
            safe_title = title.strip() if title else "[제목 없음]"
            safe_description = description.strip() if description else "[설명 없음]"

            selected_fields = [
                SelectedFieldItem(
                    field_key=a.get("field_key", ""),
                    answer_text=(a.get("answer_text") or "").strip(),
                )
                for a in data.get("answers", [])
                if (a.get("answer_text") or "").strip()
            ]

            field_scores = request_matches.get(request_id, {})
            top_field = max(
                field_scores.items(),
                key=lambda kv: kv[1] * FIELD_WEIGHTS.get(kv[0], 0.0)
            )[0] if field_scores else None
            answers = data.get("answers", [])
            request_field_text_map = {
                (a.get("field_key") or ""): (a.get("answer_text") or "").strip()
                for a in answers
            }
            request_text_for_top_field = request_field_text_map.get(top_field, "")
            reason = self._generate_reason_with_gpt_for_form(
                details=[{
                "field": top_field,
                "request_text": request_text_for_top_field,
                "creator_text": field_key_to_text.get(top_field, "")
                }],
                title=safe_title,
                description=safe_description
            )

            recommendations.append(
                CourseRequestRecommendationItem(
                    request_id=request_id,
                    title=safe_title,
                    description=safe_description,
                    selected_fields=selected_fields,
                    reason=reason,
                )
            )

        if not recommendations:
            raise APIException(ErrorCode.FAILED_TO_LOAD_REQUEST_DETAILS)

        try:
            # 저작된 form, 컨퍼플리티 등을 DB에 저장
            form_id, form_answer_objs = self.creator_recommendation_form_repo.create_answers_with_new_form_id(form.answers)


            result_ids = self.creator_recommendation_repo.save_recommendation_results(
            course_request_ids=top_request_ids,
            receiver_id=creator_id,
            matched_by_form=True,
            return_ids=True
            )


            self.course_request_repo.update_recommendation_status(
            course_request_ids=top_request_ids,
            new_status="IGNORED"
            )


            self.creator_recommendation_repo.link_form_answers_to_recommendation_results(
            recommendation_result_ids=result_ids,
            form_id=form_id
            )


            self.db.flush()
            self.db.commit()


            return CourseRequestRecommendationResponse(recommendations=recommendations)


        except Exception as e:
            self.db.rollback()
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"트랜잭션 실패: {str(e)}"])

    def _generate_reason_with_gpt_for_form(self, details: List[dict], title: str, description: str) -> str:
        if not details:
            return "추천 이유를 생성할 데이터가 부족합니다."

        top_match = details[0]
        minimal_details = [{
            "field": top_match.get("field", ""),
            "request_text": top_match.get("request_text", ""),
            "creator_text": top_match.get("creator_text", "")
        }]

        try:
            prompt = load_prompt("course_request_reason_with_form_prompt.j2", {
                "title": title,
                "description": description,
                "matches": minimal_details
            })
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"Form 기반 프롬프트 로딩 실패: {str(e)}"])

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "왜 이 추천이 적절한지 한 문장으로 설명해줘."},
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "추천 이유 생성에 실패했습니다."


    def _recommend_based_on_uploaded_videos(
        self,
        creator_id: int,
        video_ids: List[int],
        exclude_request_ids: Optional[List[int]] = None,
    ) -> CourseRequestRecommendationResponse:
        request_id_to_score = self.vector_search_service.search_similar_request_ids_from_video_ids(
            video_ids=video_ids,
            top_k=20,
            exclude_request_ids=exclude_request_ids
        )
        if not request_id_to_score:
            raise APIException(ErrorCode.NO_SIMILAR_REQUESTS_FOUND)

        sorted_requests = sorted(
            request_id_to_score.items(),
            key=lambda x: x[1]["max_score"],
            reverse=True,
        )

        TOP_N = 3
        top_pairs = sorted_requests[:TOP_N]
        top_request_ids = [rid for rid, _ in top_pairs]

        req_map = self.course_request_repo.get_request_with_answers(top_request_ids)

        recommendations: List[CourseRequestRecommendationItem] = []

        for request_id, score_info in top_pairs:
            data = req_map.get(request_id)
            if not data:
                continue

            title = data.get("title")
            description = data.get("description")
            safe_title = title if title and title.strip() else "[제목 없음]"
            safe_description = description if description and description.strip() else "[설명 없음]"

            selected_fields = [
                SelectedFieldItem(
                    field_key=a.get("field_key", ""),
                    answer_text=(a.get("answer_text") or "").strip(),
                )
                for a in data.get("answers", [])
                if (a.get("answer_text") or "").strip()
            ]

            reason = self._generate_reason_with_gpt(
                details=score_info.get("details", []),
                title=safe_title,
                description=safe_description
            )

            recommendations.append(
                CourseRequestRecommendationItem(
                    request_id=request_id,
                    title=safe_title,
                    description=safe_description,
                    selected_fields=selected_fields,
                    reason=reason,
                )
            )

        if not recommendations:
            raise APIException(ErrorCode.FAILED_TO_LOAD_REQUEST_DETAILS)

        self.creator_recommendation_repo.save_recommendation_results(
            course_request_ids=top_request_ids,
            receiver_id=creator_id,
            matched_by_form=False
        )
        
        self.course_request_repo.update_recommendation_status(
            course_request_ids=top_request_ids,
            new_status="IGNORED"
        )

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"DB 커밋 실패: {str(e)}"])

        return CourseRequestRecommendationResponse(recommendations=recommendations)

    def _generate_reason_with_gpt(self, details: List[dict], title: str, description: str) -> str:
        if not details:
            return "추천 이유를 생성할 데이터가 부족합니다."

        top_match = details[0]
        minimal_details = [{
            "field": top_match.get("field", ""),
            "request_text": top_match.get("request_text", ""),
            "video_text": top_match.get("video_text", "")
        }]

        try:
            prompt = load_prompt("course_request_reason_with_base_prompt.j2", {
                "title": title,
                "description": description,
                "matches": minimal_details
            })
        except Exception as e:
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"Reason 프롬프트 로딩 실패: {str(e)}"])

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "주어진 요청과 영상 정보를 바탕으로, 왜 이 추천이 적절한지 한 문장으로 설명해줘."},
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "추천 이유 생성에 실패했습니다."

    def _embed_fields_to_vectors(self, field_key_to_text: Dict[str, str]) -> Dict[str, List[float]]:
        embedded = {}
        for field_key, text in field_key_to_text.items():
            if text.strip(): 
                try:
                    response = client.embeddings.create(
                        model="text-embedding-3-large",
                        input=text
                    )
                    embedded[field_key] = response.data[0].embedding
                except Exception as e:
                    raise APIException(ErrorCode.VECTOR_UPSERT_FAILED, details=[f"{field_key} 임베딩 실패: {str(e)}"])
        return embedded

    def _compute_weighted_scores(self, request_matches: Dict[int, Dict[str, float]]) -> Dict[int, float]:
        total_weight_all = sum(FIELD_WEIGHTS.values())
        result = {}

        for request_id, field_scores in request_matches.items():
            weighted_sum = 0.0

            for field_key, weight in FIELD_WEIGHTS.items():
                weighted_sum += field_scores.get(field_key, 0.0) * weight
            result[request_id] = weighted_sum / total_weight_all if total_weight_all > 0 else 0.0
        return result
    
    def update_action_status(self, creator_id: int, request_id: int, new_status: str):
        valid_statuses = {"ACCEPTED", "DECLINED", "IGNORED", "COMPLETED"}
        if new_status not in valid_statuses:
            raise APIException(
                ErrorCode.INVALID_TYPE_PARAMETER,
                details=[f"action_status는 다음 중 하나여야 합니다: {', '.join(valid_statuses)}"]
            )

        try:
            with self.db.begin():
                result = self.creator_recommendation_repo.get_recommendation_result_by_request_id(request_id)
                if not result:
                    raise APIException(
                        ErrorCode.RESOURCE_NOT_FOUND,
                        details=[f"해당 추천 결과를 찾을 수 없습니다."]
                    )

                if result.receiver_id != creator_id:
                    raise APIException(
                        ErrorCode.FORBIDDEN,
                        details=[f"해당 추천 결과에 대한 접근 권한이 없습니다."]
                    )

                self.creator_recommendation_repo.update_action_status(
                    receiver_id=creator_id,
                    course_request_id=request_id,
                    new_status=new_status,
                    action_at=datetime.utcnow()
                )

                self.course_request_repo.update_recommendation_status(
                    course_request_ids=[request_id],
                    new_status=new_status
                )

                self.db.flush()

        except APIException:
            raise
        except Exception as e:
            self.db.rollback()
            raise APIException(ErrorCode.INTERNAL_ERROR, details=[f"요청 상태 업데이트 실패: {str(e)}"])


    def check_request_availability(self, request_id: int) -> CourseRequestAvailabilityResponse:
        # 1. 요청 존재 여부 확인
        exists = self.course_request_repo.exists_by_id(request_id)
        if not exists:
            raise APIException(ErrorCode.RESOURCE_NOT_FOUND, details=["존재하지 않는 요청입니다."])

        # 2. 추천된 이력이 있는지 확인 (추천이 한 번도 안 된 경우)
        if not self.creator_recommendation_repo.exists_by_course_request_id(request_id):
            return CourseRequestAvailabilityResponse(available=False, status="NOT_RECOMMENDED")

        # 3. 추천 결과들에서 action_status 조회
        statuses = self.creator_recommendation_repo.get_action_statuses_by_request_id(request_id)

        if not statuses:
            return CourseRequestAvailabilityResponse(available=True, status="IGNORED")

        status_set = set(statuses)

        if "COMPLETED" in status_set:
            return CourseRequestAvailabilityResponse(available=False, status="COMPLETED")

        if "ACCEPTED" in status_set:
            return CourseRequestAvailabilityResponse(available=False, status="ACCEPTED")

        if status_set == {"IGNORED"}:
            return CourseRequestAvailabilityResponse(available=True, status="IGNORED")

        if status_set.issubset({"IGNORED", "DECLINED"}):
            return CourseRequestAvailabilityResponse(available=True, status="DECLINED")

        return CourseRequestAvailabilityResponse(available=False, status="UNKNOWN")
            

