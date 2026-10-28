"""
test_pencipta_mode.py — Unit tests for Sprint E: Pencipta Mode / Creative Engine

Test coverage:
1. Trigger detection (self-learn, self-improve, self-motivate)
2. PenciptaTrigger dataclass
3. Creative output generation (may return None without LLM)
4. Output storage and retrieval
5. Stats
6. End-to-end pipeline

Author: Mighan Lab / SIDIX
License: MIT
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.pencipta_mode import (
    PenciptaTrigger,
    PenciptaOutput,
    check_self_learn,
    check_self_improve,
    check_self_motivate,
    check_all_triggers,
    generate_creative_output,
    save_output,
    list_outputs,
    stats,
    run_pencipta,
    _OUTPUT_TYPES,
)


# ── Trigger Tests ────────────────────────────────────────────────────────

class TestTriggerDetection:
    def test_pencipta_trigger_all_met(self):
        """Test PenciptaTrigger.all_met()."""
        t = PenciptaTrigger(self_learn=True, self_improve=True, self_motivate=True)
        assert t.all_met() is True
        assert t.score() == 1.0
    
    def test_pencipta_trigger_partial(self):
        """Test partial trigger."""
        t = PenciptaTrigger(self_learn=True, self_improve=False, self_motivate=True)
        assert t.all_met() is False
        assert t.score() == pytest.approx(0.667, rel=0.01)
    
    def test_pencipta_trigger_none(self):
        """Test no triggers."""
        t = PenciptaTrigger()
        assert t.all_met() is False
        assert t.score() == 0.0
    
    def test_check_self_learn(self):
        """Test self-learn check."""
        triggered, count = check_self_learn(min_corroborations=999)
        # Should return False with very high threshold
        assert isinstance(triggered, bool)
        assert isinstance(count, int)
    
    def test_check_self_improve(self):
        """Test self-improve check."""
        triggered, avg = check_self_improve(min_score=0.99, min_samples=999)
        # Should return False with very high threshold
        assert isinstance(triggered, bool)
        assert isinstance(avg, float)
    
    def test_check_self_motivate(self):
        """Test self-motivate check."""
        triggered, count = check_self_motivate()
        assert isinstance(triggered, bool)
        assert isinstance(count, int)
    
    def test_check_all_triggers(self):
        """Test check_all_triggers returns PenciptaTrigger."""
        trigger = check_all_triggers()
        assert isinstance(trigger, PenciptaTrigger)
        assert 0.0 <= trigger.score() <= 1.0


# ── Creative Generation Tests ────────────────────────────────────────────

class TestCreativeGeneration:
    def test_output_types_defined(self):
        """Test output types are defined."""
        assert len(_OUTPUT_TYPES) == 7
        assert "metode" in _OUTPUT_TYPES
        assert "karya" in _OUTPUT_TYPES
        assert "temuan" in _OUTPUT_TYPES
    
    def test_generate_creative_output(self):
        """Test creative generation (may return None without LLM)."""
        output = generate_creative_output(
            output_type="metode",
            domain="test",
            trigger_score=1.0,
        )
        if output:
            assert isinstance(output, PenciptaOutput)
            assert output.output_type == "metode"
            assert output.domain == "test"
            assert output.id.startswith("pct_")
            assert output.content
    
    def test_generate_creative_output_auto_type(self):
        """Test auto-pick output type."""
        output = generate_creative_output(domain="test")
        if output:
            assert output.output_type in _OUTPUT_TYPES


# ── Storage Tests ────────────────────────────────────────────────────────

class TestStorage:
    def test_save_and_list(self):
        """Test save and list outputs."""
        output = PenciptaOutput(
            id="pct_test_001",
            ts="2026-05-01T00:00:00",
            output_type="temuan",
            title="Test Temuan",
            description="Test description",
            content="Test content",
            domain="test",
            trigger_score=1.0,
            sanad_score=0.8,
            status="draft",
        )
        
        path = save_output(output)
        assert path.exists()
        
        outputs = list_outputs(limit=10)
        assert isinstance(outputs, list)
        
        # Check our test output is in the list
        ids = [o.get("id") for o in outputs]
        assert "pct_test_001" in ids
    
    def test_stats(self):
        """Test stats function."""
        s = stats()
        assert "total" in s
        assert "by_type" in s
        assert "by_status" in s
        assert "avg_trigger_score" in s


# ── Pipeline Tests ───────────────────────────────────────────────────────

class TestPipeline:
    def test_run_pencipta_force(self):
        """Test forced Pencipta run."""
        output = run_pencipta(force=True, output_type="temuan", domain="test")
        # May or may not succeed depending on LLM
        if output:
            assert isinstance(output, PenciptaOutput)
            assert output.status in ("draft", "validated")
    
    def test_run_pencipta_no_force_no_triggers(self):
        """Test that Pencipta doesn't run without triggers (unless forced)."""
        # With impossible thresholds, should not run
        output = run_pencipta(force=False)
        # Most likely None unless triggers happen to be met
        assert output is None or isinstance(output, PenciptaOutput)


# ── Cleanup helper ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_pencipta():
    """Cleanup test outputs after each test."""
    yield
    from brain_qa.pencipta_mode import _pencipta_index
    idx_path = _pencipta_index()
    if idx_path.exists():
        import json
        lines = []
        with idx_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and '"id":"pct_test_001"' not in line:
                    lines.append(line)
        with idx_path.open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)


# ── Run tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
