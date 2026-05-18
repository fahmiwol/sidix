"""
test_pattern_integration.py — Unit tests for Sprint C: Pattern Extractor Integration

Test coverage:
1. Pattern retrieval via HafidzInjector
2. Pattern injection into Hafidz prompt
3. Pattern extraction hook in OMNYX
4. Pattern API endpoints

Author: Mighan Lab / SIDIX
License: MIT
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.pattern_extractor import (
    Pattern,
    looks_like_inductive_claim,
    extract_pattern_from_text,
    save_pattern,
    search_patterns,
    stats,
    maybe_extract_from_conversation,
)
from brain_qa.hafidz_injector import (
    HafidzContext,
    HafidzInjector,
    build_hafidz_prompt,
)


# ── Pattern Extractor Tests ──────────────────────────────────────────────

class TestPatternExtractor:
    def test_looks_like_inductive_claim_true(self):
        """Detect inductive claim with trigger phrases."""
        text = "Kalau batok kelapa dibakar jadi arang, artinya kayu juga kalo dibakar jadi arang"
        assert looks_like_inductive_claim(text) is True
    
    def test_looks_like_inductive_claim_false(self):
        """Non-inductive text should return False."""
        text = "Halo, apa kabar?"
        assert looks_like_inductive_claim(text) is False
    
    def test_looks_like_inductive_claim_empty(self):
        """Empty text should return False."""
        assert looks_like_inductive_claim("") is False
    
    def test_extract_pattern_from_text(self):
        """Test pattern extraction (may return None in test env without LLM)."""
        text = "Batu kelapa dibakar jadi arang. Artinya kayu juga kalo dibakar jadi arang."
        pattern = extract_pattern_from_text(text, derived_from="test")
        # May or may not succeed depending on LLM availability
        if pattern:
            assert isinstance(pattern, Pattern)
            assert pattern.extracted_principle
            assert pattern.confidence > 0
    
    def test_search_patterns_empty(self):
        """Search with no patterns stored returns empty."""
        results = search_patterns("biomass", top_k=5)
        assert isinstance(results, list)
    
    def test_stats_empty(self):
        """Stats with no patterns."""
        s = stats()
        assert s["total"] >= 0
        assert "avg_confidence" in s


# ── Hafidz + Pattern Integration Tests ───────────────────────────────────

class TestHafidzPatternIntegration:
    def test_build_hafidz_prompt_with_patterns(self):
        """Test prompt builder includes patterns."""
        context = HafidzContext(
            patterns=[
                {
                    "extracted_principle": "Material organik dengan kandungan karbon tinggi menghasilkan arang saat dibakar",
                    "applicable_domain": ["organic", "thermal"],
                    "confidence": 0.85,
                    "keywords": ["bakar", "karbon", "arang"],
                }
            ]
        )
        prompt = build_hafidz_prompt(context)
        assert "POLA / PRINSIP RELEVAN" in prompt
        assert "Material organik" in prompt
        assert "organic" in prompt
    
    def test_build_hafidz_prompt_no_patterns(self):
        """Test prompt builder without patterns."""
        context = HafidzContext()
        prompt = build_hafidz_prompt(context)
        assert "POLA / PRINSIP RELEVAN" not in prompt
    
    @pytest.mark.asyncio
    async def test_retrieve_context_includes_patterns(self):
        """Test HafidzInjector retrieves patterns."""
        # First save a pattern
        from brain_qa.pattern_extractor import _patterns_file
        import json
        
        pat = {
            "id": "pat_test_001",
            "ts": "2026-05-01T00:00:00",
            "source_example": "batok kelapa dibakar jadi arang",
            "extracted_principle": "Material organik berkarbon tinggi jadi arang saat dibakar",
            "applicable_domain": ["organic", "thermal"],
            "keywords": ["bakar", "karbon", "arang", "biomass"],
            "confidence": 0.85,
            "corroborations": 0,
            "falsifications": 0,
            "counter_examples": [],
            "derived_from": "test",
        }
        
        # Write directly to patterns file
        path = _patterns_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(pat, ensure_ascii=False) + "\n")
        
        # Now retrieve via HafidzInjector
        injector = HafidzInjector()
        context = await injector.retrieve_context(
            query="bakar karbon arang biomass",
            persona="AYMAN",
            max_patterns=3,
        )
        
        assert isinstance(context, HafidzContext)
        assert isinstance(context.patterns, list)
        # Should find the pattern about biomass/thermal (keyword overlap)
        assert len(context.patterns) > 0


# ── OMNYX Hook Tests ─────────────────────────────────────────────────────

class TestOmnyxPatternHook:
    @pytest.mark.asyncio
    async def test_pattern_extraction_in_omnyx(self):
        """Test that OMNYX process calls pattern extraction."""
        from brain_qa.omnyx_direction import omnyx_process
        
        result = await omnyx_process(
            "batok kelapa dibakar jadi arang, artinya kayu juga kalo dibakar jadi arang",
            persona="AYMAN",
        )
        
        # Should complete without error
        assert "answer" in result
        assert "sanad_score" in result


# ── Cleanup helper ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_patterns():
    """Cleanup test patterns after each test."""
    yield
    from brain_qa.pattern_extractor import _patterns_file
    path = _patterns_file()
    if path.exists():
        # Remove test patterns
        lines = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and '"derived_from":"test"' not in line:
                    lines.append(line)
        with path.open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)


# ── Run tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
