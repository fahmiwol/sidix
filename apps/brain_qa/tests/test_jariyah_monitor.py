"""
test_jariyah_monitor.py — Test Jariyah Rate Monitor

Jiwa Sprint 4 (Kimi)
"""

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from brain_qa.jariyah_monitor import (
    calculate_rates,
    check_alerts,
    monitor,
    JariyahRateSnapshot,
    JariyahAlert,
)


class TestJariyahMonitor:

    def _make_pairs_file(self, pairs: list[dict]) -> Path:
        """Helper: buat temporary JSONL file."""
        fd = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
        for p in pairs:
            fd.write(json.dumps(p, ensure_ascii=False) + "\n")
        fd.close()
        return Path(fd.name)

    def test_empty_file(self):
        fd = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
        fd.close()
        result = calculate_rates(Path(fd.name))
        assert result.total_pairs == 0
        assert result.trend == "insufficient_data"
        import os
        os.unlink(fd.name)

    def test_basic_calculation(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q1", "response": "r1", "rating": 1, "timestamp": now},
            {"query": "q2", "response": "r2", "rating": 1, "timestamp": now},
            {"query": "q3", "response": "r3", "rating": -1, "timestamp": now},
        ]
        path = self._make_pairs_file(pairs)
        result = calculate_rates(path)

        assert result.total_pairs == 3
        assert result.thumbs_up == 2
        assert result.thumbs_down == 1
        assert result.approval_rate == pytest.approx(2/3, 0.01)
        assert result.quality_score == pytest.approx(1/3, 0.01)
        assert result.trend == "insufficient_data"  # only 3 pairs, need 5 for trend
        path.unlink()

    def test_approval_rate_alert(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q", "response": "r", "rating": -1, "timestamp": now}
            for _ in range(10)
        ]
        # Add 4 upvotes = 4/14 = 28% approval < 60% threshold
        for _ in range(4):
            pairs.append({"query": "q", "response": "r", "rating": 1, "timestamp": now})

        path = self._make_pairs_file(pairs)
        result = calculate_rates(path)
        alerts = check_alerts(result)

        alert_types = [a.alert_type for a in alerts]
        assert "low_approval" in alert_types
        path.unlink()

    def test_high_rejection_alert(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q", "response": "r", "rating": -1, "timestamp": now}
            for _ in range(5)
        ]
        pairs.append({"query": "q", "response": "r", "rating": 1, "timestamp": now})

        path = self._make_pairs_file(pairs)
        result = calculate_rates(path)
        alerts = check_alerts(result)

        alert_types = [a.alert_type for a in alerts]
        assert "high_rejection" in alert_types
        path.unlink()

    def test_healthy_no_alerts(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q", "response": "r", "rating": 1, "timestamp": now}
            for _ in range(20)
        ]
        path = self._make_pairs_file(pairs)
        result = monitor(path)

        assert result["healthy"] is True
        assert result["alert_count"] == 0
        path.unlink()

    def test_trend_detection_improving(self):
        now = datetime.now(timezone.utc)
        # Old pairs: mixed
        pairs = []
        for i in range(5):
            pairs.append({
                "query": "q", "response": "r",
                "rating": 1 if i % 2 == 0 else -1,
                "timestamp": (now - timedelta(hours=48)).isoformat(),
            })
        # Recent pairs: all thumbs up = improving
        for _ in range(5):
            pairs.append({
                "query": "q", "response": "r",
                "rating": 1,
                "timestamp": (now - timedelta(hours=1)).isoformat(),
            })

        path = self._make_pairs_file(pairs)
        result = calculate_rates(path, lookback_hours=24)
        assert result.trend == "improving"
        path.unlink()

    def test_trend_detection_declining(self):
        now = datetime.now(timezone.utc)
        # Old pairs: all thumbs up
        pairs = []
        for _ in range(5):
            pairs.append({
                "query": "q", "response": "r",
                "rating": 1,
                "timestamp": (now - timedelta(hours=48)).isoformat(),
            })
        # Recent pairs: all thumbs down = declining
        for _ in range(5):
            pairs.append({
                "query": "q", "response": "r",
                "rating": -1,
                "timestamp": (now - timedelta(hours=1)).isoformat(),
            })

        path = self._make_pairs_file(pairs)
        result = calculate_rates(path, lookback_hours=24)
        assert result.trend == "declining"

        alerts = check_alerts(result)
        alert_types = [a.alert_type for a in alerts]
        assert "quality_drop" in alert_types
        path.unlink()

    def test_monitor_api_format(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q", "response": "r", "rating": 1, "timestamp": now}
            for _ in range(10)
        ]
        path = self._make_pairs_file(pairs)
        result = monitor(path)

        assert "snapshot" in result
        assert "alerts" in result
        assert "alert_count" in result
        assert "healthy" in result
        assert isinstance(result["snapshot"]["approval_rate"], float)
        path.unlink()

    def test_no_rating_counted(self):
        now = datetime.now(timezone.utc).isoformat()
        pairs = [
            {"query": "q", "response": "r", "rating": 0, "timestamp": now}
            for _ in range(5)
        ]
        path = self._make_pairs_file(pairs)
        result = calculate_rates(path)

        assert result.total_pairs == 5
        assert result.no_rating == 5
        assert result.thumbs_up == 0
        assert result.thumbs_down == 0
        path.unlink()

    def test_parse_timestamp_variants(self):
        from brain_qa.jariyah_monitor import _parse_timestamp
        # ISO with Z
        dt1 = _parse_timestamp("2026-04-25T10:00:00Z")
        assert dt1.year == 2026
        # ISO with offset
        dt2 = _parse_timestamp("2026-04-25T10:00:00+00:00")
        assert dt2.year == 2026
        # Plain ISO
        dt3 = _parse_timestamp("2026-04-25T10:00:00")
        assert dt3.year == 2026
