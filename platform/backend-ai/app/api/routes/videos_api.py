from fastapi import Header, Request, APIRouter, Depends, Body, HTTPException
from uuid import UUID
from typing import List, cast
from sqlalchemy.orm import Session

import redis
import json

from app.services.video.video_transcription_service import VideoTranscriptionService
from app.services.video.video_metadata_service import VideoMetadataService
from app.services.video.video_title_suggestion_service import VideoTitleSuggestionService
from app.services.video.video_description_suggestion_service import VideoDescriptionSuggestionService
from app.services.video.video_practice_guide_service import VideoPracticeGuideService
from app.services.video.delete_video_service import DeleteVideoService
from app.repositories.video.video_course_repository import VideoCourseRepository
from app.tasks.video.vector_tasks import run_vector_upsert_task

from app.core.db import get_db
from app.core.auth import get_current_user
from app.schemas.user import User
from app.schemas.common import ResponseModel
from app.schemas.video import (
    TranscribeVideoRequest,
    TranscribeVideoResponse,
    MetadataSuggestionResponse,
    TitleSuggestionRequest,
    TitleSuggestionResponse,
    DescriptionSuggestionRequest,
    DescriptionSuggestionResponse,
    TranscriptionStatusResponse,
    VectorStatusResponse,
    PracticeGuideSuggestionResponse
)
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.run_service_method_in_threadpool import run_with_service_in_threadpool
from app.integrations.mixpanel.component.events import (
    PRACTICE_GUIDE_GENERATED,
    VIDEO_TITLE_SUGGESTED,
    VIDEO_METADATA_SUGGESTED,
    VIDEO_DESCRIPTION_SUGGESTED,
)

from app.docs.deco import op

router = APIRouter(prefix="/videos", tags=["videos"])

redis_client = redis.Redis(host="redis", port=6379, db=2)

@op("ai_videos_transcribe", tags=["videos"])
@router.post("/{video_id}/transcribe", response_model=ResponseModel[TranscribeVideoResponse])
def transcribe_video(
    video_id: int,
    request: TranscribeVideoRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = VideoTranscriptionService(db)
    result = service.transcribe_from_url_async(request.file_url, video_id)
    return ResponseModel(success=True, data=result)


@op("ai_videos_transcription_status", tags=["videos"])
@router.get("/{video_uuid}/transcription-status", response_model=ResponseModel[TranscriptionStatusResponse])
def get_transcription_status(
    video_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = VideoCourseRepository(db)
    video = repo.get_active_video_by_uuid(video_uuid)

    if not video:
        raise HTTPException(status_code=404, detail="해당 video_uuid에 대한 비디오를 찾을 수 없습니다.")

    redis_key = f"video:task:{video.id}"
    data = redis_client.get(redis_key)

    if not data:
        return ResponseModel(success=True, data=TranscriptionStatusResponse(
            status="NOT_STARTED",
            progress=0,
            step="대기 중입니다."
        ))

    try:
        status_data = json.loads(data)
    except Exception:
        raise HTTPException(status_code=500, detail="진행 상태 데이터가 손상되었습니다.")

    return ResponseModel(success=True, data=TranscriptionStatusResponse(**status_data))


@op("ai_videos_vector_upsert", tags=["videos"])
@router.post("/{video_uuid}/vector-upsert", response_model=ResponseModel[str])
def start_vector_upsert(
    video_uuid: UUID,
    current_user: User = Depends(get_current_user),
):
    # 비동기 벡터 임베딩 태스크 실행 (uuid 전달)
    run_vector_upsert_task.delay(str(video_uuid))
    return ResponseModel(success=True, data="벡터 임베딩 작업을 시작했습니다.")


@op("ai_videos_vector_status", tags=["videos"])
@router.get("/{video_uuid}/vector-status", response_model=ResponseModel[VectorStatusResponse])
def get_vector_status(
    video_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = VideoCourseRepository(db)
    video = repo.get_active_video_by_uuid(video_uuid)

    if not video:
        raise HTTPException(status_code=404, detail="해당 video_uuid에 대한 비디오를 찾을 수 없습니다.")

    redis_key = f"video:vector:task:{video.id}"
    data = redis_client.get(redis_key)

    if not data:
        return ResponseModel(success=True, data=VectorStatusResponse(
            status="NOT_STARTED",
            progress=0,
            step="대기 중입니다."
        ))

    try:
        status_data = json.loads(data)
    except Exception:
        raise HTTPException(status_code=500, detail="벡터 상태 데이터가 손상되었습니다.")

    return ResponseModel(success=True, data=VectorStatusResponse(**status_data))


@op("ai_videos_metadata_suggestion", tags=["videos"])
@router.post("/{video_uuid}/metadata-suggestion", response_model=ResponseModel[MetadataSuggestionResponse])
async def suggest_metadata(
    video_uuid: UUID,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = VideoMetadataService(db)
    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=VIDEO_METADATA_SUGGESTED,
        base_event_fields={"video_uuid": str(video_uuid)},
        business_operation=lambda: run_with_service_in_threadpool(
            VideoMetadataService,
            lambda service: service.generate_metadata_for_video(video_uuid),
        ),
    )
    return ResponseModel(success=True, data=result)


@op("ai_videos_suggest_title", tags=["videos"])
@router.post("/{video_uuid}/suggest-title", response_model=ResponseModel[TitleSuggestionResponse])
async def suggest_title(
    video_uuid: UUID,
    http_request: Request,
    request: TitleSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VideoTitleSuggestionService(db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=VIDEO_TITLE_SUGGESTED,
        base_event_fields={
            "video_uuid": str(video_uuid),
            "original_title_length": len(request.original_title or ""),
        },
        business_operation=lambda: run_with_service_in_threadpool(
            VideoTitleSuggestionService,
            lambda service: service.suggest_title(video_uuid, request.original_title),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("ai_videos_suggest_description", tags=["videos"])
@router.post("/{video_uuid}/suggest-description", response_model=ResponseModel[DescriptionSuggestionResponse])
async def suggest_description(
    video_uuid: UUID,
    http_request: Request,
    request: DescriptionSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = VideoDescriptionSuggestionService(db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=VIDEO_DESCRIPTION_SUGGESTED,
        base_event_fields={
            "video_uuid": str(video_uuid),
            "original_description_length": len(request.original_description or ""),
        },
        # 서비스는 동기 구현이므로 안전하게 스레드풀에서 실행
        business_operation=lambda: run_with_service_in_threadpool(
            VideoDescriptionSuggestionService,
            lambda service: service.suggest_description(video_uuid, request.original_description),
        ),
    )

    return ResponseModel(success=True, data=result)

@op("ai_videos_suggest_practice_guide", tags=["videos"])
@router.post("/{video_uuid}/suggest-practice-guide", response_model=ResponseModel[PracticeGuideSuggestionResponse])
async def suggest_practice_guide(
    video_uuid: UUID,
    http_request: Request,
    # db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Session의 원래 의도에 맞게 Thread-safe를 위해 해당 service 코드는 사용하지 않음.
    # service = VideoPracticeGuideService(db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=PRACTICE_GUIDE_GENERATED,
        base_event_fields={"video_uuid": str(video_uuid)},
        business_operation=lambda: run_with_service_in_threadpool(
            VideoPracticeGuideService,
            lambda service: service.suggest_practice_guide(video_uuid),
        ),
    )

    return ResponseModel(
        success=True,
        data=PracticeGuideSuggestionResponse(practice_draft=result),
    )

@op("ai_videos_delete", tags=["videos"])
@router.delete("/{video_uuid}", response_model=ResponseModel[None])
def delete_video(
    video_uuid: UUID,
    authorization: str = Header(..., alias="Authorization"),
):
    secret = authorization.replace("Bearer ", "").strip()
    service = DeleteVideoService()
    service.delete_video_by_uuid(video_uuid=video_uuid, secret=secret)
    return ResponseModel(success=True)


@op("ai_videos_batch_delete", tags=["videos"])
@router.delete("/", response_model=ResponseModel[None])
def delete_videos(
    video_uuids: List[UUID] = Body(..., embed=True),
    authorization: str = Header(..., alias="Authorization"),
):
    secret = authorization.replace("Bearer ", "").strip()
    service = DeleteVideoService()
    service.delete_videos_by_uuids(video_uuids=video_uuids, secret=secret)
    return ResponseModel(success=True)