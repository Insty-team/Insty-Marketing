from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from fastapi import Request
from app.integrations.mixpanel.domain.protocol import AnalyticsEventPublisherProtocol
from app.integrations.mixpanel.component.keys import FIELD_ENDPOINT, FIELD_HTTP_METHOD

T = TypeVar("T")

## FastAPI Request 컨텍스트 기반의 초간단 파사드로, 라우트에서 한 줄로 호출하기 위해 만들었음.
def build_default_event_fields_from_request(
    request: Request,
    additional_event_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    FastAPI Request 컨텍스트에서 기본 이벤트 필드(endpoint, http_method)를 생성하고
    추가 필드를 병합하여 반환한다.
    """
    default_fields: Dict[str, Any] = {
        FIELD_ENDPOINT: request.url.path,
        FIELD_HTTP_METHOD: request.method,
    }
    if additional_event_fields:
        default_fields.update(additional_event_fields)
    return default_fields


class MixpanelRequestEventTracker:
    """
    Request.state.mixpanel(AnalyticsEventPublisherProtocol)을 이용해
    - 기능 사용 이벤트 단발 전송
    - 비즈니스 로직 실행의 성공/실패 결과를 자동 트래킹
    - try/except 없는 컨텍스트 기반 성공/실패 트래킹
    을 담당한다.
    """

    def __init__(self, request: Request):
        self.request = request
        self.publisher: AnalyticsEventPublisherProtocol = request.state.mixpanel

    async def publish_feature_used_event_with_request_context(
        self,
        event_name: str,
        distinct_user_id: str,
        additional_event_fields: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        “해당 기능이 사용되었다”는 성격의 단발 이벤트를 전송한다.
        Request 컨텍스트에서 endpoint, http_method를 자동으로 포함한다.
        """
        await self.publisher.publish_event(
            event_name=event_name,
            distinct_id=distinct_user_id,
            fields=build_default_event_fields_from_request(self.request, additional_event_fields),
        )

    async def execute_business_operation_and_track_event_outcome_with_request_context(
        self,
        event_name: str,
        distinct_user_id: str,
        base_event_fields: Dict[str, Any],
        business_operation_coroutine: Callable[[], Awaitable[T]],
    ) -> T:
        """
        비즈니스 코루틴을 실행하고, 성공/실패 결과를 이벤트로 자동 트래킹한다.
        - 성공 시: is_success=True
        - 실패 시: is_success=False + error 타입명을 필드로 추가하여 전송 후 예외 재전파
        """
        try:
            result = await business_operation_coroutine()
            await self.publisher.publish_event_with_outcome(
                event_name=event_name,
                distinct_id=distinct_user_id,
                fields=build_default_event_fields_from_request(self.request, base_event_fields),
                is_success=True,
            )
            return result
        except Exception as error:
            failure_event_fields = dict(base_event_fields)
            failure_event_fields["error"] = type(error).__name__
            await self.publisher.publish_event_with_outcome(
                event_name=event_name,
                distinct_id=distinct_user_id,
                fields=build_default_event_fields_from_request(self.request, failure_event_fields),
                is_success=False,
            )
            raise

    @asynccontextmanager
    async def track_event_outcome_within_async_block_using_request_context(
        self,
        event_name: str,
        distinct_user_id: str,
        base_event_fields: Dict[str, Any],
    ):
        """
        비즈니스 블록을 async context로 감싸서 성공/실패를 자동 트래킹한다.
        사용 예:
            async with tracker.track_event_outcome_within_async_block_using_request_context(
                "event_name", user_id, {"course_id": 1}
            ):
                await do_business()
        """
        try:
            yield
            await self.publisher.publish_event_with_outcome(
                event_name=event_name,
                distinct_id=distinct_user_id,
                fields=build_default_event_fields_from_request(self.request, base_event_fields),
                is_success=True,
            )
        except Exception as error:
            failure_event_fields = dict(base_event_fields)
            failure_event_fields["error"] = type(error).__name__
            await self.publisher.publish_event_with_outcome(
                event_name=event_name,
                distinct_id=distinct_user_id,
                fields=build_default_event_fields_from_request(self.request, failure_event_fields),
                is_success=False,
            )
            raise


def get_mixpanel_request_event_tracker(request: Request) -> MixpanelRequestEventTracker:
    """
    라우트에서 명확한 이름으로 파사드를 가져오기 위한 엔트리 함수.
    예) tracker = get_mixpanel_request_event_tracker(http_request)
    """
    return MixpanelRequestEventTracker(request)
