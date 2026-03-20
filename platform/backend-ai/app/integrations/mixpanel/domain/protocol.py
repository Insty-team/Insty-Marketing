from __future__ import annotations
from typing import Any, Dict, Protocol

## 퍼블리셔의 최소 인터페이스(테스트/Mock 용이하게 하기 위한 용도. 실제로 사용되지는 않음)
class AnalyticsEventPublisherProtocol(Protocol):
    async def publish_event(self, event_name: str, distinct_id: str, fields: Dict[str, Any]) -> None: ...
    async def publish_event_with_outcome(
        self, event_name: str, distinct_id: str, fields: Dict[str, Any], is_success: bool
    ) -> None: ...
