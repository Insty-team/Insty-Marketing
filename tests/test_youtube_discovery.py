"""YouTube Discovery 모듈 테스트."""

import pytest
from src.youtube_discovery import _iso_duration_to_minutes, _calculate_score, _passes_filter


class TestIsoDurationToMinutes:
    def test_hours_minutes_seconds(self):
        assert _iso_duration_to_minutes("PT1H2M30S") == 62.5

    def test_minutes_only(self):
        assert _iso_duration_to_minutes("PT15M") == 15.0

    def test_seconds_only(self):
        assert _iso_duration_to_minutes("PT30S") == 0.5

    def test_hours_only(self):
        assert _iso_duration_to_minutes("PT2H") == 120.0

    def test_empty(self):
        assert _iso_duration_to_minutes("") == 0

    def test_invalid(self):
        assert _iso_duration_to_minutes("invalid") == 0


class TestPassesFilter:
    def test_passes_all(self):
        video = {"views": 10000, "duration_minutes": 10}
        assert _passes_filter(video) is True

    def test_low_views(self):
        video = {"views": 100, "duration_minutes": 10}
        assert _passes_filter(video) is False

    def test_too_short(self):
        video = {"views": 10000, "duration_minutes": 2}
        assert _passes_filter(video) is False

    def test_too_long(self):
        video = {"views": 10000, "duration_minutes": 60}
        assert _passes_filter(video) is False


class TestCalculateScore:
    def test_high_engagement(self):
        video = {
            "views": 100000,
            "likes": 5000,
            "comments": 500,
            "published_at": "2026-02-01T00:00:00Z",
        }
        score = _calculate_score(video)
        assert 0 <= score <= 100

    def test_low_engagement(self):
        video = {
            "views": 5000,
            "likes": 10,
            "comments": 1,
            "published_at": "2025-08-01T00:00:00Z",
        }
        score = _calculate_score(video)
        assert 0 <= score <= 100

    def test_higher_views_higher_score(self):
        base = {"likes": 100, "comments": 10, "published_at": "2026-02-01T00:00:00Z"}
        low = _calculate_score({**base, "views": 5000})
        high = _calculate_score({**base, "views": 500000})
        assert high > low
