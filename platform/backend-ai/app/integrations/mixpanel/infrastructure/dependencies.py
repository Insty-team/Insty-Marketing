from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.integrations.mixpanel.infrastructure.track_http_client import AsyncMixpanelClient
from app.integrations.mixpanel.domain.publisher import MixpanelEventPublisher
from app.integrations.mixpanel.domain.protocol import AnalyticsEventPublisherProtocol

# providers.py
# - Mixpanel 의존성(HTTP 클라이언트, 퍼블리셔)을 앱 전역에서 재사용하도록 제공
# - lru_cache로 프로세스 내 싱글톤처럼 동작 (테스트에서 캐시 초기화 주의)
# - 앱 종료 시 close_mixpanel_client()로 httpx 커넥션 정리

@lru_cache
def get_mixpanel_client() -> AsyncMixpanelClient:
    """
    Mixpanel HTTP 클라이언트를 생성/캐시한다.
    - 설정값을 바탕으로 타임아웃/재시도/백오프 구성
    - lru_cache로 최초 1회만 생성하여 커넥션 풀 재사용
    """
    mixpanel_settings = get_settings().mixpanel

    return AsyncMixpanelClient(
        api_endpoint=mixpanel_settings.api_endpoint,
        connect_timeout_seconds=mixpanel_settings.connect_timeout_seconds,
        read_timeout_seconds=mixpanel_settings.read_timeout_seconds,
        total_timeout_seconds=mixpanel_settings.total_timeout_seconds,
        max_retries=mixpanel_settings.max_retries,
        backoff_base_seconds=mixpanel_settings.backoff_base_seconds,
    )

@lru_cache
def get_mixpanel_publisher() -> AnalyticsEventPublisherProtocol:
    """
    Mixpanel 이벤트 퍼블리셔를 생성/캐시한다.
    - 토큰/활성화 여부를 반영해 no-op 여부 결정
    - 내부적으로 get_mixpanel_client()를 사용(의존성 공유)
    """
    mixpanel_settings = get_settings().mixpanel

    return MixpanelEventPublisher(
        client=get_mixpanel_client(),
        token=mixpanel_settings.token,
        enabled=bool(mixpanel_settings.enabled and mixpanel_settings.token),
    )


# 애플리케이션 종료 시 클라이언트 정리 (lifespan에서 호출)
async def close_mixpanel_client() -> None:
    """
    앱 종료 시 호출하여 httpx AsyncClient를 정리한다.
    - 커넥션 풀/파일 디스크립터 누수 방지
    """
    client = get_mixpanel_client()
    await client.close()

# lru_cache 싱글톤은 테스트 격리에 불편할 수 있어서 사용하는 리셋 함수
def reset_mixpanel_singletons_for_test() -> None:
    get_mixpanel_client.cache_clear()
    get_mixpanel_publisher.cache_clear()