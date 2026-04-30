"""
test_socratic_probe.py — Test Socratic Probe module

Jiwa Sprint 4 (Kimi)
"""

import pytest
from brain_qa.socratic_probe import (
    analyze_question,
    should_probe,
    get_probe_response,
    ProbeDecision,
    SocraticProbe,
)


class TestSocraticProbe:

    def test_vague_question_triggers_socratic(self):
        result = analyze_question("Kenapa begitu?")
        assert result.decision == ProbeDecision.SOCRATIC_GUIDE
        assert len(result.clarifying_questions) > 0
        assert result.confidence > 0.0

    def test_clear_question_answer_directly(self):
        result = analyze_question("Berapa 2+2?")
        assert result.decision == ProbeDecision.ANSWER_DIRECTLY
        assert len(result.clarifying_questions) == 0

    def test_code_question_answer_directly(self):
        result = analyze_question("Bagaimana cara deploy FastAPI ke VPS?")
        assert result.decision == ProbeDecision.ANSWER_DIRECTLY

    def test_too_broad_triggers_clarify(self):
        result = analyze_question("Jelaskan semuanya tentang ekonomi Islam secara lengkap")
        assert result.decision in (ProbeDecision.CLARIFY_FIRST, ProbeDecision.SOCRATIC_GUIDE)

    def test_translate_answer_directly(self):
        result = analyze_question("Translate 'hello' ke bahasa Indonesia")
        assert result.decision == ProbeDecision.ANSWER_DIRECTLY

    def test_persona_aley_more_rigor(self):
        # ALEY = researcher, should be more likely to probe
        result_aley = analyze_question("Apa pendapatmu tentang politik?", persona="ALEY")
        result_ayman = analyze_question("Apa pendapatmu tentang politik?", persona="AYMAN")
        # ALEY should have higher or equal probe tendency
        assert result_aley.confidence >= result_ayman.confidence - 0.1

    def test_deep_conversation_less_probe(self):
        history = ["Halo", "Apa kabar?", "Bisa jelaskan AI?"]
        result_with_history = analyze_question("Bagaimana cara kerjanya?", conversation_history=history)
        result_no_history = analyze_question("Bagaimana cara kerjanya?")
        # With history, should be less likely to probe
        assert result_with_history.confidence <= result_no_history.confidence + 0.1

    def test_empty_question(self):
        result = analyze_question("")
        assert result.decision == ProbeDecision.CLARIFY_FIRST
        assert "kosong" in result.reason.lower()

    def test_should_probe_one_shot(self):
        assert should_probe("Kenapa?") is True
        assert should_probe("Berapa 2+2?") is False

    def test_get_probe_response_format(self):
        result = get_probe_response("Kenapa begitu?")
        assert "probe" in result
        assert "questions" in result
        assert "confidence" in result
        assert result["probe"] in ("socratic", "clarify", "answer")

    def test_difference_question_socratic(self):
        result = analyze_question("Apa perbedaan antara AI dan ML?")
        # Difference questions should trigger at least clarify
        assert result.decision in (ProbeDecision.CLARIFY_FIRST, ProbeDecision.SOCRATIC_GUIDE)

    def test_socratic_questions_not_empty(self):
        result = analyze_question("Mengapa langit biru?")
        if result.decision == ProbeDecision.SOCRATIC_GUIDE:
            assert len(result.clarifying_questions) >= 1
            for q in result.clarifying_questions:
                assert len(q) > 5

    def test_infer_angle(self):
        result = analyze_question("Apa teori relativitas Einstein?")
        assert result.suggested_angle == "theoretical"

        result2 = analyze_question("Bagaimana praktisnya deploy Docker?")
        assert result2.suggested_angle == "practical"
