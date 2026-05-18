"""
test_sanad_orchestra.py — Unit tests for Sanad Orchestra (Sprint A)

Test coverage:
1. Claim extraction (LLM + regex fallback)
2. Claim verification (corpus + web + tools)
3. Consensus calculation
4. Verdict determination
5. End-to-end validation

Author: Mighan Lab / SIDIX
License: MIT
"""
import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.sanad_orchestra import (
    Claim,
    ValidationResult,
    _extract_claims_regex,
    calculate_consensus,
    determine_verdict,
    get_threshold,
    SanadOrchestra,
    validate_answer,
)


# ── Claim Extraction Tests ───────────────────────────────────────────────

class TestClaimExtraction:
    def test_extract_claims_regex_basic(self):
        """Test regex fallback claim extraction with factual statements."""
        answer = (
            "Prabowo Subianto adalah Presiden Indonesia ke-8. "
            "Dia dilantik pada 20 Oktober 2024. "
            "Sebelumnya dia menjabat sebagai Menteri Pertahanan."
        )
        claims = _extract_claims_regex(answer)
        assert len(claims) > 0
        # Should extract sentences with named entities
        assert any("Prabowo" in c.text for c in claims)
    
    def test_extract_claims_empty(self):
        """Test extraction with empty answer."""
        claims = _extract_claims_regex("")
        assert len(claims) == 0
    
    def test_extract_claims_no_facts(self):
        """Test extraction with opinion-only answer."""
        answer = "Menurut saya, ini adalah hal yang sangat menarik dan penting."
        claims = _extract_claims_regex(answer)
        # May or may not extract depending on heuristics
        # Should not crash
        assert isinstance(claims, list)


# ── Consensus Calculation Tests ──────────────────────────────────────────

class TestConsensusCalculation:
    def test_all_verified(self):
        """All claims verified → high consensus."""
        claims = [
            Claim(text="A", confidence=1.0, verdict="verified"),
            Claim(text="B", confidence=1.0, verdict="verified"),
        ]
        score = calculate_consensus(claims)
        assert score >= 0.95
    
    def test_all_unverified(self):
        """All claims unverified → low consensus."""
        claims = [
            Claim(text="A", confidence=1.0, verdict="unverified"),
            Claim(text="B", confidence=1.0, verdict="unverified"),
        ]
        score = calculate_consensus(claims)
        assert score <= 0.25
    
    def test_mixed(self):
        """Mixed verified + unverified → medium consensus."""
        claims = [
            Claim(text="A", confidence=1.0, verdict="verified"),
            Claim(text="B", confidence=1.0, verdict="unverified"),
        ]
        score = calculate_consensus(claims)
        assert 0.3 < score < 0.7
    
    def test_empty_claims(self):
        """No claims extracted → neutral score."""
        score = calculate_consensus([])
        assert score == 0.5
    
    def test_weighted_confidence(self):
        """Higher confidence claims have more weight."""
        claims = [
            Claim(text="A", confidence=0.9, verdict="verified"),
            Claim(text="B", confidence=0.3, verdict="unverified"),
        ]
        score = calculate_consensus(claims)
        # Should be closer to verified due to high weight
        assert score > 0.5


# ── Verdict Determination Tests ──────────────────────────────────────────

class TestVerdictDetermination:
    def test_golden(self):
        """Score well above threshold → golden."""
        verdict = determine_verdict(0.98, 0.85, [])
        assert verdict == "golden"
    
    def test_pass(self):
        """Score at threshold → pass."""
        verdict = determine_verdict(0.85, 0.85, [])
        assert verdict == "pass"
    
    def test_retry(self):
        """Score below threshold but above 70% → retry."""
        verdict = determine_verdict(0.60, 0.85, [])
        assert verdict == "retry"
    
    def test_fail(self):
        """Score well below threshold → fail."""
        verdict = determine_verdict(0.30, 0.85, [])
        assert verdict == "fail"
    
    def test_threshold_simple(self):
        """Simple factual has highest threshold."""
        threshold = get_threshold("simple", [])
        assert threshold == 0.92
    
    def test_threshold_tool_output(self):
        """Tool output has highest threshold."""
        threshold = get_threshold("analytical", ["calculator"])
        assert threshold == 0.95
    
    def test_threshold_creative(self):
        """Creative has lowest threshold."""
        threshold = get_threshold("creative", [])
        assert threshold == 0.75


# ── Sanad Orchestra Integration Tests ────────────────────────────────────

class TestSanadOrchestra:
    @pytest.mark.asyncio
    async def test_validate_factual(self):
        """Test validation of a factual answer."""
        orchestra = SanadOrchestra()
        result = await orchestra.validate(
            answer="Presiden Indonesia saat ini adalah Prabowo Subianto.",
            query="siapa presiden indonesia?",
            sources={},
            persona="AYMAN",
            tools_used=[],
            tool_outputs=[],
            complexity="simple",
        )
        
        assert isinstance(result, ValidationResult)
        assert 0.0 <= result.consensus_score <= 1.0
        assert result.verdict in ("golden", "pass", "retry", "fail")
        assert len(result.claims) >= 0
        assert "n_claims" in result.metadata
    
    @pytest.mark.asyncio
    async def test_validate_creative(self):
        """Test validation of a creative answer (lower threshold)."""
        orchestra = SanadOrchestra()
        result = await orchestra.validate(
            answer="Sebuah puisi tentang cinta yang indah dan penuh harapan.",
            query="buat puisi cinta",
            sources={},
            persona="UTZ",
            tools_used=[],
            tool_outputs=[],
            complexity="creative",
        )
        
        assert isinstance(result, ValidationResult)
        assert result.verdict in ("golden", "pass", "retry", "fail")
    
    @pytest.mark.asyncio
    async def test_validate_with_tool_output(self):
        """Test validation with calculator tool output."""
        orchestra = SanadOrchestra()
        result = await orchestra.validate(
            answer="Hasil dari 25 × 4 adalah 100.",
            query="berapa 25 kali 4?",
            sources={"calculator": {"result": 100, "expression": "25 * 4"}},
            persona="ABOO",
            tools_used=["calculator"],
            tool_outputs=[{"result": 100, "expression": "25 * 4"}],
            complexity="simple",
        )
        
        assert isinstance(result, ValidationResult)
        assert result.verdict in ("golden", "pass", "retry", "fail")
    
    @pytest.mark.asyncio
    async def test_stats(self):
        """Test statistics tracking."""
        orchestra = SanadOrchestra()
        
        # Run a few validations
        await orchestra.validate(
            answer="Test 1",
            query="test",
            sources={},
            persona="AYMAN",
            tools_used=[],
            tool_outputs=[],
        )
        await orchestra.validate(
            answer="Test 2",
            query="test",
            sources={},
            persona="AYMAN",
            tools_used=[],
            tool_outputs=[],
        )
        
        stats = orchestra.get_stats()
        assert stats["validations"] == 2
        assert "golden_rate" in stats or "pass_rate" in stats or "retry_rate" in stats or "fail_rate" in stats
    
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test validate_answer convenience function."""
        result = await validate_answer(
            answer="Indonesia merdeka pada 17 Agustus 1945.",
            query="kapan indonesia merdeka?",
            sources={},
        )
        
        assert isinstance(result, ValidationResult)
        assert 0.0 <= result.consensus_score <= 1.0


# ── Run tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
