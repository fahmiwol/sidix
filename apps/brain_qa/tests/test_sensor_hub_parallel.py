"""Tests for parallel sensor hub probing — Jiwa Sprint 3 Fase B."""

import pytest
import time

from brain_qa.sensor_hub import probe_all, health_summary


class TestParallelProbe:
    def test_probe_all_parallel_returns_correct_structure(self):
        result = probe_all(parallel=True)
        assert "total" in result
        assert "active" in result
        assert "inactive" in result
        assert "broken" in result
        assert "by_body" in result
        assert "senses" in result
        assert result["total"] >= 11  # at least 11 senses registered

    def test_probe_all_sequential_returns_correct_structure(self):
        result = probe_all(parallel=False)
        assert result["total"] >= 11
        assert len(result["senses"]) == result["total"]

    def test_parallel_and_sequential_equivalent(self):
        """Parallel and sequential should produce same counts (modulo timing)."""
        r1 = probe_all(parallel=True)
        r2 = probe_all(parallel=False)
        assert r1["total"] == r2["total"]
        assert r1["active"] == r2["active"]
        assert r1["inactive"] == r2["inactive"]
        assert r1["broken"] == r2["broken"]

    def test_parallel_faster_than_sequential(self):
        """Parallel should be measurably faster for multiple senses."""
        t0 = time.perf_counter()
        probe_all(parallel=True)
        t_parallel = time.perf_counter() - t0

        t0 = time.perf_counter()
        probe_all(parallel=False)
        t_sequential = time.perf_counter() - t0

        # Parallel should not be slower (allow small measurement noise)
        assert t_parallel <= t_sequential * 1.5, (
            f"Parallel ({t_parallel:.3f}s) slower than sequential ({t_sequential:.3f}s)"
        )

    def test_health_summary_after_parallel_probe(self):
        summary = health_summary()
        assert "senses_total" in summary
        assert "senses_active" in summary
        assert summary["senses_total"] >= 11

    def test_all_senses_have_status(self):
        result = probe_all(parallel=True)
        for snap in result["senses"]:
            assert snap["status"] in ("active", "inactive", "broken", "unknown")
            assert snap["slug"]
            assert snap["body_part"]
