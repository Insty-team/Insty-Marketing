from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.integrations.mixpanel.infrastructure.track_http_client import AsyncMixpanelClient
from app.integrations.mixpanel.component.keys import FIELD_DISTINCT_ID,FIELD_TIMESTAMP_MILLIS,FIELD_TRACK_OUTCOME,FIELD_TOKEN, OUTCOME_FAILURE, OUTCOME_SUCCESS

## 공통 필드 주입 + outcome 래핑을 담당하는 도메인 퍼블리셔
class MixpanelEventPublisher:
    """
    Mixpanel 이벤트 퍼블리셔.
    - 설정상 비활성/토큰 미제공이면 no-op
    - 공통 필드(token, distinct_id, time(ms))를 주입하여 이벤트 전송
    - 성공/실패 결과(outcome) 필드 헬퍼 제공
    """

    def __init__(self, client: AsyncMixpanelClient, token: Optional[str], enabled: bool):
        self.client = client
        self.token = token
        self.is_enabled = bool(enabled and token)

    def _build_common_event_fields(self, distinct_id: str, input_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        이벤트에 공통 컨텍스트 필드(token, distinct_id, timestamp[ms])를 병합해 반환한다.
        """
        merged_fields = dict(input_fields or {})
        merged_fields[FIELD_TOKEN] = self.token
        merged_fields[FIELD_DISTINCT_ID] = distinct_id
        # NS -> MS(소수점 오차 없애기 위해서)
        merged_fields[FIELD_TIMESTAMP_MILLIS] = time.time_ns() // 1_000_000
        return merged_fields

    async def publish_event(self, event_name: str, distinct_id: str, fields: Dict[str, Any]) -> None:
        """
        단일 이벤트를 /track 로 배치 포맷(1개)으로 전송한다.
        - 비활성화 상태면 즉시 반환(no-op)
        """
        if not self.is_enabled:
            return
        payload_fields = self._build_common_event_fields(distinct_id, fields)
        await self.client.send_event_batch_to_track_endpoint(
            [{"event": event_name, "properties": payload_fields}]
        )

    async def publish_event_with_outcome(
        self, event_name: str, distinct_id: str, fields: Dict[str, Any], is_success: bool
    ) -> None:
        """
        outcome(SUCCESS/FAILURE) 필드를 포함해 이벤트를 전송한다.
        """
        enriched_fields = dict(fields or {})
        enriched_fields[FIELD_TRACK_OUTCOME] = OUTCOME_SUCCESS if is_success else OUTCOME_FAILURE
        await self.publish_event(event_name, distinct_id, enriched_fields)
