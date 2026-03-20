from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.orm import Session
from typing import Optional

from app.core.auth import get_current_user, get_optional_user
from app.core.db import get_db

from app.docs.deco import op
from app.schemas.common import ResponseModel
from app.schemas.search import (
    CourseRecommendationRequest,
    CourseRecommendationResponse,
    RecommendationHistoryResponse,
    AIServiceRecommendationRequest,
    AIServiceRecommendationResponse,
)
from app.schemas.user import User

from app.services.search.search_course_service import SearchCourseService
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.component.events import COURSE_RECOMMENDATION_COMPLETED
from app.services.search.ai_service_recommendation_service import AIServiceRecommendationService
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.component.events import (
    COURSE_RECOMMENDATION_COMPLETED,
    AI_SERVICE_RECOMMENDATION_COMPLETED
)
from app.integrations.mixpanel.run_service_method_in_threadpool import run_with_service_in_threadpool

router = APIRouter(prefix="/search", tags=["search"])


@op("ai_search_recommend", tags=["search"])
@router.post("/recommend", response_model=ResponseModel[CourseRecommendationResponse])
async def recommend_courses(
    http_request: Request,
    request_body: CourseRecommendationRequest = Body(...),

    db: Session = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_user),
):
    # 게스트: Mixpanel 안 탐
    if optional_user is None:
        result = await run_with_service_in_threadpool(
            SearchCourseService,
            lambda service: service.recommend_for_guest(
                query=request_body.query,
            ),
        )
        return ResponseModel(success=True, data=result)

    # 로그인: 기존 트래킹 유지
    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=optional_user.id,
        event_name=COURSE_RECOMMENDATION_COMPLETED,
        base_event_fields={
            "query_length": len(request_body.query or ""),
        },
        business_operation=lambda: run_with_service_in_threadpool(
            SearchCourseService,
            lambda service: service.recommend(
                user_id=optional_user.id,
                query=request_body.query,
            ),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("ai_search_recommend_history", tags=["search"])
@router.get("/recommend", response_model=ResponseModel[RecommendationHistoryResponse])
def get_latest_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SearchCourseService(db)
    result = service.get_recommend_courses(user_id=current_user.id)
    return ResponseModel(success=True, data=result)


@op("ai_search_recommend_services", tags=["search"])
@router.post("/recommend-services", response_model=ResponseModel[AIServiceRecommendationResponse])
async def recommend_ai_services_with_courses(
    request_body: AIServiceRecommendationRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIServiceRecommendationService(db)
    
    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=AI_SERVICE_RECOMMENDATION_COMPLETED,
        base_event_fields={
            "query_length": len(request_body.query or ""),
        },
        business_operation=lambda: run_with_service_in_threadpool(
            AIServiceRecommendationService,
            lambda service: service.recommend_ai_services_with_courses(
                user_id=current_user.id,
                query=request_body.query,
            ),
        ),
    )
    
    return ResponseModel(success=True, data=result)