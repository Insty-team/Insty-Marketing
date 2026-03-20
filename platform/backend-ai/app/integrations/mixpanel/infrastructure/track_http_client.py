from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger(__name__)

MIXPANEL_TRACK_SUCCESS_BODY = "1"          # /track 성공 시 본문
LOG_RESPONSE_PREVIEW_MAXLEN = 200          # 로그에 실을 응답 본문 미리보기 길이
FORM_FIELD_DATA_KEY = "data"               # Mixpanel /track form-data 필드명

## Mixpanel /track 호출 전용 HTTP 비동기 클라이언트
class AsyncMixpanelClient:
    """
    Mixpanel /track 비동기 클라이언트.
    - 이벤트 배치 전송
    - 짧은 타임아웃 + 지수 백오프 재시도
    - 최종 실패 시 경고 로그만 남기고 예외 전파하지 않음 (no-throw)
    """

    def __init__(
        self,
        api_endpoint: str,
        connect_timeout_seconds: float,
        read_timeout_seconds: float,
        total_timeout_seconds: float,
        max_retries: int,
        backoff_base_seconds: float,
    ):
        # 전송 대상 엔드포인트 (/track)
        self.api_endpoint = api_endpoint

        # httpx 타임아웃 구성
        self.timeout = httpx.Timeout(
            timeout=total_timeout_seconds,
            connect=connect_timeout_seconds,
            read=read_timeout_seconds,
        )

        # 재시도/백오프 파라미터
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

        # 지연 생성되는 httpx.AsyncClient
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_or_create_httpx_client(self) -> httpx.AsyncClient:
        """
        내부 httpx AsyncClient를 지연 생성 후 재사용한다.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    @staticmethod
    def _encode_events_to_form_data(events: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        이벤트 리스트를 Mixpanel /track 규격의 form-data로 변환한다.
        - 'data' 필드에 base64(JSON) 문자열을 담는다.
        - JSON 직렬화는 공백 제거(separators)로 최소화한다.
        """
        payload_bytes = json.dumps(events, separators=(",", ":")).encode("utf-8")
        return {FORM_FIELD_DATA_KEY: base64.b64encode(payload_bytes).decode("utf-8")}

    @staticmethod
    def _is_successful_track_response(response: httpx.Response) -> bool:
        """
        /track 성공 여부를 판별한다.
        - HTTP 200 && 본문이 "1"
        """
        return response.status_code == 200 and response.text.strip() == MIXPANEL_TRACK_SUCCESS_BODY

    async def send_event_batch_to_track_endpoint(self, events: List[Dict[str, Any]]) -> None:
        """
        이벤트 배치를 /track 엔드포인트로 전송한다.
        - 빈 리스트는 호출하지 않는다.
        - 성공 시 즉시 반환, 실패 시 지수 백오프로 재시도한다.
        - 모든 시도 실패 시 경고 로그만 남기고 종료(no-throw).
        """
        if not events:
            return

        client = await self._get_or_create_httpx_client()
        form_data = self._encode_events_to_form_data(events)

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(self.api_endpoint, data=form_data)

                if self._is_successful_track_response(response):
                    return

                preview = response.text[:LOG_RESPONSE_PREVIEW_MAXLEN]
                raise RuntimeError(f"Mixpanel error: status={response.status_code}, body={preview}")

            except Exception as error:
                is_last_attempt = attempt >= self.max_retries
                if is_last_attempt:
                    log.warning("Mixpanel track failed after retries: %s", str(error))
                    return

                # Jitter를 추가해서 실패들을 동시에 재시작하는 것을 방지
                backoff_seconds = self.backoff_base_seconds * (2 ** attempt)
                backoff_seconds *= (0.9 + random.random() * 0.2)
                await asyncio.sleep(backoff_seconds)

    async def close(self) -> None:
        """
        내부 httpx AsyncClient를 종료하여 커넥션 풀 자원을 정리한다.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
