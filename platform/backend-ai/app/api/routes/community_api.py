from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.db import get_db
from app.schemas.common import ResponseModel
from app.schemas.user import User
from app.schemas.community import (
    AnswerDraftResponse,
    CourseFormResponse,
    CourseRequest,
    CourseRequestRecommendationResponse,
    CourseRequestStatusUpdateRequest,
    CourseRequestStatusUpdateResponse,
    CourseRequestSuggestion,
    CourseResponse,
    CourseResponseSuggestion,
    CreatorInterestForm,
    CreatorRecommendationFormResponse,
    FormCheckResponse,
    DraftRequest,
    QuestionDraftResponse,
    ThoughtDraftResponse,
    CourseRequestAvailabilityResponse
)
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.services.community.draft_service import CommunityAnswerDraftService
from app.services.course.course_form_service import CourseFormService
from app.services.course.course_request_service import CourseRequestService
from app.services.course.course_request_recommendation_service import CourseRequestRecommendationService
from app.services.course.course_request_suggestion_service import CourseRequestSuggestionService
from app.services.course.creator_recommendation_form_service import CreatorRecommendationFormService
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.run_service_method_in_threadpool import run_with_service_in_threadpool
from app.integrations.mixpanel.component.events import (
    COURSE_REQUEST_SUGGESTION_USED, 
    COURSE_REQUEST_CREATED,
    COURSE_REQUEST_RECO_WITH_BASE,
    COURSE_REQUEST_RECO_WITHOUT_BASE,
    COMMUNITY_ANSWER_DRAFT_CREATED,
    COMMUNITY_QUESTION_DRAFT_CREATED,
    COMMUNITY_THOUGHT_DRAFT_CREATED
)
from app.docs.deco import op

router = APIRouter(prefix="/community", tags=["community"])

@op("community_create_course_request", tags=["community"])
@router.post("/course-requests", response_model=ResponseModel[CourseResponse])
async def create_course_request(
    request: CourseRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestService(db)

    base_fields = {
        "title_length": len(getattr(request, "title", "") or ""),
        "description_length": len(getattr(request, "description", "") or ""),
        "tags_count": len(getattr(request, "tags", []) or []),
    }

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COURSE_REQUEST_CREATED,
        base_event_fields=base_fields,
        business_operation=lambda: run_with_service_in_threadpool(
            CourseRequestService,
            lambda service: service.create_course_request(
                request=request,
                user_id=current_user.id,
            ),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("community_get_my_course_requests", tags=["community"])
@router.get("/course-requests", response_model=ResponseModel[List[CourseResponse]])
async def get_my_course_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CourseRequestService(db)
    result = service.get_request_with_answers(current_user.id)
    return ResponseModel(success=True, data=result)


@op("community_delete_course_request", tags=["community"])
@router.delete("/course-requests/{request_id}", response_model=ResponseModel[None])
async def delete_course_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CourseRequestService(db)
    service.delete_request(request_id, current_user.id)
    return ResponseModel(success=True, data=None)


@op("community_get_course_request_form", tags=["community"])
@router.get("/course-requests/form", response_model=ResponseModel[CourseFormResponse])
async def get_course_request_form(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CourseFormService(db=db)
    result = service.get_form()
    return ResponseModel(success=True, data=result)


@op("community_get_creator_recommendation_form", tags=["community"])
@router.get("/creator-recommendation/form", response_model=ResponseModel[CreatorRecommendationFormResponse])
async def get_creator_recommendation_form(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CreatorRecommendationFormService(db=db)
    result = service.get_form()
    return ResponseModel(success=True, data=result)


@op("community_recommend_with_base", tags=["community"])
@router.post("/course-request-recommendation/with-base", response_model=ResponseModel[CourseRequestRecommendationResponse])
async def recommend_with_base(
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestRecommendationService(db=db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COURSE_REQUEST_RECO_WITH_BASE,
        base_event_fields={},
        business_operation=lambda: run_with_service_in_threadpool(
            CourseRequestRecommendationService,
            lambda service: service.recommend_with_base(current_user.id),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("community_recommend_without_base", tags=["community"])
@router.post("/course-request-recommendation/without-base", response_model=ResponseModel[CourseRequestRecommendationResponse])
async def recommend_without_base(
    form: CreatorInterestForm,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestRecommendationService(db=db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COURSE_REQUEST_RECO_WITHOUT_BASE,
        base_event_fields={},
        business_operation=lambda: run_with_service_in_threadpool(
            CourseRequestRecommendationService,
            lambda service: service.recommend_without_base(
                current_user.id,
                form,
            ),
        ),
    )
    return ResponseModel(success=True, data=result)


@op("community_update_recommendation_action_status", tags=["community"])
@router.patch("/course-request-recommendation/{request_id}/status",response_model=ResponseModel[CourseRequestStatusUpdateResponse])
async def update_recommendation_action_status(
    request_id: int,
    payload: CourseRequestStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestRecommendationService(db=db)
    updated = service.update_action_status(
        creator_id=current_user.id,
        request_id=request_id,
        new_status=payload.action_status
    )
    return ResponseModel(success=True, data=updated)


@op("community_check_course_request_availability", tags=["community"])
@router.get("/course-request-recommendation/{request_id}/availability", response_model=ResponseModel[CourseRequestAvailabilityResponse])
async def check_course_request_availability(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestRecommendationService(db=db)
    result = service.check_request_availability(request_id=request_id)
    return ResponseModel(success=True, data=result)


@op("community_get_course_request_final_result", tags=["community"])
@router.get("/course-requests/{request_id}/final-result", response_model=ResponseModel[dict])
async def get_course_request_final_result(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CourseRequestService(db)
    result = service.get_finalized_result(request_id)
    return ResponseModel(success=True, data=result)


@op("community_get_last_creator_form", tags=["community"])
@router.get("/creator-recommendation/form/last",response_model=ResponseModel[FormCheckResponse])
async def get_last_creator_form(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CreatorRecommendationFormService(db=db)
    result = service.get_last_submitted_form(current_user.id)
    return ResponseModel(success=True, data=result)


@op("community_suggest_lecture_request", tags=["community"])
@router.post("/course-request-suggestion", response_model=ResponseModel[CourseResponseSuggestion])
async def suggest_lecture_request(
    request: CourseRequestSuggestion,
    http_request: Request,
    current_user: User = Depends(get_current_user),
):
    service = CourseRequestSuggestionService()

    # 민감 데이터가 포함되어 있을 수 있으므로 raw data 전체를 보내지 않고 통계용 길이/개수만 보냄
    base_fields = {
        "problem_context_length": len(request.problem_context or ""),
        "goal_length": len(request.goal or ""),
        "current_attempt_length": len(request.current_attempt or ""),
        "desired_output_length": len(request.desired_output or ""),
        "has_extra_context": bool((request.extra_context or "").strip()),
    }

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COURSE_REQUEST_SUGGESTION_USED,
        base_event_fields=base_fields,
        business_operation=lambda: run_with_service_in_threadpool(
            CourseRequestSuggestionService,
            lambda service: service.suggest(request=request),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("community_generate_question_draft", tags=["community"])
@router.post("/question-draft", response_model=ResponseModel[QuestionDraftResponse])
async def generate_question_draft(
    http_request: Request, 
    request: DraftRequest = Depends(DraftRequest.as_form),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommunityAnswerDraftService(
        video_course_repo=VideoCourseRepository(db)
    )

    base_fields = {
        "course_id": request.course_id,
        "query_length": len(request.query or ""),
        "has_attachment": bool(files),
        "attachments_count": len(files or []),
        "draft_type": "question",
    }

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COMMUNITY_QUESTION_DRAFT_CREATED,
        base_event_fields=base_fields,
        business_operation=lambda: run_with_service_in_threadpool(
            # 생성자가 db를 안 받고 video_course_repo를 받기 때문에 from_db사용
            CommunityAnswerDraftService.from_db,
            lambda service: service.generate_draft_response(
                course_id=request.course_id,
                text=request.query,
                draft_type="question",
                attachment_files=files,
            ),
        ),
    )

    return ResponseModel(
        success=True,
        data=QuestionDraftResponse(**result, has_attachment=bool(files))
    )

@op("community_generate_answer_draft", tags=["community"])
@router.post("/answer-draft", response_model=ResponseModel[AnswerDraftResponse])
async def generate_answer_draft(
    http_request: Request,
    request: DraftRequest = Depends(DraftRequest.as_form),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommunityAnswerDraftService(
        video_course_repo=VideoCourseRepository(db)
    )

    base_fields = {
        "course_id": request.course_id,
        "query_length": len(request.query or ""),
        "has_attachment": bool(files),
        "attachments_count": len(files or []),
        "draft_type": "answer",
    }

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COMMUNITY_ANSWER_DRAFT_CREATED,
        base_event_fields=base_fields,
        business_operation=lambda: run_with_service_in_threadpool(
            # 생성자가 db를 안 받고 video_course_repo를 받기 때문에 from_db사용
            CommunityAnswerDraftService.from_db,
            lambda service: service.generate_draft_response(
                course_id=request.course_id,
                text=request.query,
                draft_type="answer",
                attachment_files=files,
            ),
        ),
    )

    return ResponseModel(
        success=True,
        data=AnswerDraftResponse(**result, has_attachment=bool(files))
    )

@op("community_generate_thought_draft", tags=["community"])
@router.post("/thought-draft", response_model=ResponseModel[ThoughtDraftResponse])
async def generate_thought_draft(
    http_request: Request, 
    request: DraftRequest = Depends(DraftRequest.as_form),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CommunityAnswerDraftService(
        video_course_repo=VideoCourseRepository(db)
    )

    base_fields = {
        "course_id": request.course_id,
        "query_length": len(request.query or ""),
        "has_attachment": bool(files),
        "attachments_count": len(files or []),
        "draft_type": "thought",
    }

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=COMMUNITY_THOUGHT_DRAFT_CREATED,
        base_event_fields=base_fields,
        business_operation=lambda: run_with_service_in_threadpool(
            # 생성자가 db를 안 받고 video_course_repo를 받기 때문에 from_db사용
            CommunityAnswerDraftService.from_db,
            lambda service: service.generate_draft_response(
                course_id=request.course_id,
                text=request.query,
                draft_type="thought",
                attachment_files=files,
            ),
        ),
    )

    return ResponseModel(
        success=True,
        data=ThoughtDraftResponse(**result, has_attachment=bool(files))
    )
