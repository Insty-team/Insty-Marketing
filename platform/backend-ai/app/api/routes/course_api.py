from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth import get_current_user
from app.schemas.user import User
from app.schemas.common import ResponseModel
from app.schemas.course import (
    PurchaseAssistantRequest, 
    PurchaseAssistantResponse, 
    PurchaseAssistantUsageInfo
)
from app.services.course.purchase_assistant_service import PurchaseAssistantService
from app.docs.deco import op 
from app.integrations.mixpanel.tracking import execute_business_and_track_outcome
from app.integrations.mixpanel.run_service_method_in_threadpool import run_with_service_in_threadpool
from app.integrations.mixpanel.component.events import PURCHASE_ASSISTANT_USED

router = APIRouter(prefix="/courses", tags=["courses"])


@op("ai_courses_purchase_assistant", tags=["courses"])
@router.post("/purchase-assistant", response_model=ResponseModel[PurchaseAssistantResponse])
async def assist_purchase_decision(
    request: PurchaseAssistantRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PurchaseAssistantService(db)

    result = await execute_business_and_track_outcome(
        request=http_request,
        user_id=current_user.id,
        event_name=PURCHASE_ASSISTANT_USED,
        base_event_fields={},
        business_operation=lambda: run_with_service_in_threadpool(
            PurchaseAssistantService,
            lambda service: service.assist_user(
                user_id=current_user.id,
                request=request,
            ),
        ),
    )

    return ResponseModel(success=True, data=result)


@op("ai_courses_purchase_assistant_usage_info", tags=["courses"])
@router.get("/purchase-assistant/usage-info", response_model=ResponseModel[PurchaseAssistantUsageInfo])
def get_usage_info(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PurchaseAssistantService(db)
    result = service.get_usage_info(current_user.id, course_id)
    return ResponseModel(success=True, data=result)