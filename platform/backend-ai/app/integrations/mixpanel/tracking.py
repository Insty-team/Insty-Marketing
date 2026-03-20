from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar
from fastapi import Request
from app.integrations.mixpanel.application.request_context_event_tracker import (
    get_mixpanel_request_event_tracker,
)

T = TypeVar("T")

# 비즈니스 루틴(business_operation)을 실행하고, 끝난 뒤 성공/실패 결과를 자동으로 트래킹
async def execute_business_and_track_outcome(
    request: Request,
    user_id: int,
    event_name: str,
    base_event_fields: Dict[str, Any],
    business_operation: Callable[[], Awaitable[T]],
) -> T:
    tracker = get_mixpanel_request_event_tracker(request)
    return await tracker.execute_business_operation_and_track_event_outcome_with_request_context(
        event_name=event_name,
        distinct_user_id=str(user_id),
        base_event_fields=base_event_fields,
        business_operation_coroutine=business_operation,
    )