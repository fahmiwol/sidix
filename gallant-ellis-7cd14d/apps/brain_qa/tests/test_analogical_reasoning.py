"""
test_analogical_reasoning.py — Test Analogical Reasoning Engine

Jiwa Sprint 4 (Kimi)
"""

import pytest
from brain_qa.analogical_reasoning import (
    find_analogy,
    explain_with_analogy,
    AnalogyResult,
    Analogy,
    _normalize_concept,
    _fuzzy_match_concept,
)


class TestAnalogicalReasoning:

    def test_find_neural_network_analogy(self):
        result = find_analogy("neural network")
        assert result.best_analogy is not None
        assert "otak" in result.best_analogy.familiar_analog.lower() or "jaringan" in result.best_analogy.familiar_analog.lower()
        assert result.best_analogy.confidence > 0.5

    def test_find_blockchain_analogy(self):
        result = find_analogy("blockchain")
        assert result.best_analogy is not None
        assert result.best_analogy.confidence > 0.5
        assert len(result.analogies) >= 1

    def test_find_gradient_descent_analogy(self):
        result = find_analogy("gradient descent")
        assert result.best_analogy is not None
        assert "gunung" in result.best_analogy.familiar_analog.lower()
        assert result.best_analogy.mapping  # should have mappings

    def test_find_quantum_superposition(self):
        result = find_analogy("quantum superposition")
        assert result.best_analogy is not None
        assert "koin" in result.best_analogy.familiar_analog.lower()

    def test_synonym_lookup_deep_learning(self):
        result = find_analogy("deep learning")  # synonym for neural network
        assert result.best_analogy is not None

    def test_synonym_lookup_bitcoin(self):
        result = find_analogy("bitcoin")  # synonym for blockchain
        assert result.best_analogy is not None

    def test_unknown_concept_fallback(self):
        result = find_analogy("xyz_unknown_concept_123")
        assert result.best_analogy is None
        assert "belum ada" in result.fallback_explanation.lower() or "no analogy" in result.fallback_explanation.lower()

    def test_fuzzy_match_from_query(self):
        result = find_analogy("Can you explain how neural networks work?")
        assert result.best_analogy is not None

    def test_preferred_domain_filter(self):
        result_all = find_analogy("neural network")
        result_bio = find_analogy("neural network", preferred_domain="biologi")
        result_social = find_analogy("neural network", preferred_domain="sosial")

        # All should find something
        assert result_all.best_analogy is not None
        # Preferred domain filter should work when match exists
        if result_bio.best_analogy:
            assert result_bio.best_analogy.source_domain == "biologi"

    def test_explain_with_analogy_brief(self):
        text = explain_with_analogy("neural network", detail_level="brief")
        assert "neural network" in text.lower()
        assert len(text) > 20

    def test_explain_with_analogy_detailed(self):
        text = explain_with_analogy("blockchain", detail_level="detailed")
        assert "blockchain" in text.lower()
        assert "mapping" in text.lower() or "detail" in text.lower()

    def test_explain_unknown_concept(self):
        text = explain_with_analogy("unknown_xyz", detail_level="brief")
        assert "belum" in text.lower() or "TODO" in text

    def test_analogy_result_structure(self):
        result = find_analogy("compound interest")
        assert isinstance(result, AnalogyResult)
        assert result.concept == "compound interest"
        assert isinstance(result.analogies, list)
        if result.best_analogy:
            assert isinstance(result.best_analogy, Analogy)
            assert result.best_analogy.confidence >= 0.0
            assert result.best_analogy.confidence <= 1.0

    def test_normalize_concept(self):
        assert _normalize_concept("Neural Network") == "neural network"
        assert _normalize_concept("deep learning") == "neural network"  # synonym
        assert _normalize_concept("Bitcoin") == "blockchain"  # synonym

    def test_fuzzy_match_concept(self):
        assert _fuzzy_match_concept("how does neural network work") == "neural network"
        assert _fuzzy_match_concept("explain blockchain to me") == "blockchain"
        assert _fuzzy_match_concept("random unrelated text") is None

    def test_multiple_analogies_returned(self):
        result = find_analogy("blockchain", max_results=2)
        assert len(result.analogies) <= 2
        if len(result.analogies) >= 2:
            # Should be sorted by confidence descending
            assert result.analogies[0].confidence >= result.analogies[1].confidence

    def test_islamic_concepts(self):
        result = find_analogy("qiyas")
        assert result.best_analogy is not None
        assert "resep" in result.best_analogy.familiar_analog.lower() or "memasak" in result.best_analogy.familiar_analog.lower()

        result2 = find_analogy("ijtihad")
        assert result2.best_analogy is not None
