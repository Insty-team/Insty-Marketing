"""YouTube 자막 추출 (youtube-transcript-api)."""

import logging
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)


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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 수동 자막 우선, 없으면 자동 생성 자막
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(languages)
            except NoTranscriptFound:
                logger.warning(f"자막 없음: {video_id} (언어: {languages})")
                return None

        entries = transcript.fetch()

        if include_timestamps:
            lines = []
            for entry in entries:
                ts = _seconds_to_timestamp(entry["start"])
                text = entry["text"].replace("\n", " ")
                lines.append(f"[{ts}] {text}")
            return "\n".join(lines)
        else:
            return " ".join(entry["text"].replace("\n", " ") for entry in entries)

    except TranscriptsDisabled:
        logger.warning(f"자막 비활성화: {video_id}")
        return None
    except VideoUnavailable:
        logger.warning(f"영상 접근 불가: {video_id}")
        return None
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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(languages)

        return transcript.fetch()
    except Exception as e:
        logger.error(f"세그먼트 추출 실패 [{video_id}]: {e}")
        return None


def _seconds_to_timestamp(seconds: float) -> str:
    """초를 MM:SS 형식으로 변환."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"
