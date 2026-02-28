"""Transcript extractor 유틸리티 테스트."""

from src.transcript_extractor import _seconds_to_timestamp


class TestSecondsToTimestamp:
    def test_zero(self):
        assert _seconds_to_timestamp(0) == "00:00"

    def test_seconds_only(self):
        assert _seconds_to_timestamp(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert _seconds_to_timestamp(125) == "02:05"

    def test_float(self):
        assert _seconds_to_timestamp(90.7) == "01:30"

    def test_large(self):
        assert _seconds_to_timestamp(3661) == "61:01"
