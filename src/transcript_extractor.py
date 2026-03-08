"""YouTube 자막 추출 (youtube-transcript-api v1.x)."""

import logging
import time
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

# 싱글톤 클라이언트
_ytt = YouTubeTranscriptApi()

# IP 차단 방지용 요청 간 딜레이 (초)
_REQUEST_DELAY = 3
_last_request_time = 0.0


def _rate_limit():
    """YouTube IP 차단 방지를 위한 요청 간 딜레이."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _REQUEST_DELAY:
        time.sleep(_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def extract_transcript(
    video_id: str,
    languages: tuple[str, ...] = ("en",),
    include_timestamps: bool = True,
) -> Optional[str]:
    """YouTube 영상의 자막을 추출.

    Args:
        video_id: YouTube 영상 ID
        languages: 선호 언어 순서
        include_timestamps: 타임스탬프 포함 여부

    Returns:
        자막 텍스트 (타임스탬프 포함) 또는 None
    """
    try:
        _rate_limit()
        transcript = _ytt.fetch(video_id, languages=list(languages))

        if include_timestamps:
            lines = []
            for snippet in transcript.snippets:
                ts = _seconds_to_timestamp(snippet.start)
                text = snippet.text.replace("\n", " ")
                lines.append(f"[{ts}] {text}")
            return "\n".join(lines)
        else:
            return " ".join(
                snippet.text.replace("\n", " ") for snippet in transcript.snippets
            )

    except Exception as e:
        logger.error(f"자막 추출 실패 [{video_id}]: {e}")
        return None


def extract_transcript_with_segments(
    video_id: str,
    languages: tuple[str, ...] = ("en",),
) -> Optional[list[dict]]:
    """자막을 세그먼트 리스트로 반환 (스크립트 생성용).

    Returns:
        [{"start": float, "duration": float, "text": str}, ...]
    """
    try:
        _rate_limit()
        transcript = _ytt.fetch(video_id, languages=list(languages))
        return [
            {"start": s.start, "duration": s.duration, "text": s.text}
            for s in transcript.snippets
        ]
    except Exception as e:
        logger.error(f"세그먼트 추출 실패 [{video_id}]: {e}")
        return None


def _seconds_to_timestamp(seconds: float) -> str:
    """초를 MM:SS 형식으로 변환."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"
