from fastapi import Depends, Request
from app.integrations.mixpanel.domain.protocol import AnalyticsEventPublisherProtocol
from app.integrations.mixpanel.infrastructure.dependencies import get_mixpanel_publisher

async def attach_mixpanel_to_request(
    request: Request,
    publisher: AnalyticsEventPublisherProtocol = Depends(get_mixpanel_publisher),
):
    # 모든 엔드포인트 진입 전에 request.state에 바인딩
    request.state.mixpanel = publisher