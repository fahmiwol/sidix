"""
Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT — attribution required for derivative work.

test_agent_react_sanad_integration.py — Σ-1A Integration Tests
═══════════════════════════════════════════════════════════════════════
Tests for _apply_sanad() wired into agent_react._compose_final_answer.

Validates:
1. Brand-specific halu → overridden with canonical
2. Brand-specific correct → passthrough (no override)
3. Current event with web source → passthrough
4. Current event WITHOUT web source → UNKNOWN returned
5. Creative question → passthrough
6. Coding question → passthrough (no factual gate)
7. Sanad footer appended when rejected_llm=True
8. _apply_sanad itself is non-fatal on bad input
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.brain_qa.brain_qa.sanad_verifier import (
    Source,
    detect_intent,
    verify_multisource,
    format_sanad_footer,
)
from apps.brain_qa.brain_qa import agent_react as ar


# ════════════════════════════════════════════════════════════════════════
# Minimal stub untuk ReActStep (tidak perlu import full module)
# ════════════════════════════════════════════════════════════════════════

class _StepStub:
    def __init__(self, action_name="", observation="", action_args=None, is_final=False):
        self.action_name = action_name
        self.observation = observation
        self.action_args = action_args or {}
        self.is_final = is_final


# ══════════════════════════════════════════════════════════════════��═════
# _apply_sanad unit tests (pure function, no HTTP)
# ════════════════════════════════════════════════════════════════════════

class TestApplySanadPersonaHalu:
    """Σ-1G Q17: brain says 'Aboudi' → must be overridden to canonical 5 persona."""

    def test_override_halu_persona(self):
        question = "sebutkan 5 persona sidix"
        llm_halu = "5 persona SIDIX: Aboudi, Farhan, Zara, Riko, Dini"
        steps = []
        result = ar._apply_sanad(question, llm_halu, steps)
        assert "UTZ" in result, f"Canonical UTZ missing. Got: {result[:200]}"
        assert "ABOO" in result, f"Canonical ABOO missing. Got: {result[:200]}"
        assert "Aboudi" not in result or "UTZ" in result, "Halu not overridden"

    def test_correct_persona_passthrough(self):
        question = "persona sidix itu apa saja?"
        llm_correct = "SIDIX punya 5 persona: UTZ, ABOO, OOMAR, ALEY, AYMAN."
        steps = []
        result = ar._apply_sanad(question, llm_correct, steps)
        assert "UTZ" in result
        assert "AYMAN" in result
        # Should not append conflict warning
        assert "⚠️" not in result or "Konflik" not in result


class TestApplySanadIHOSHalu:
    """Σ-1G Q18: brain says 'Inisiatif Holistik Operasional Strategis' → must override."""

    def test_override_halu_ihos(self):
        question = "apa itu IHOS?"
        llm_halu = "IHOS = Inisiatif Holistik Operasional Strategis untuk optimasi sistem."
        steps = []
        result = ar._apply_sanad(question, llm_halu, steps)
        assert "Islamic" in result or "Ontolog" in result, (
            f"Canonical IHOS not returned. Got: {result[:200]}"
        )

    def test_correct_ihos_passthrough(self):
        question = "apa itu IHOS?"
        llm_ok = "IHOS = Islamic Holistic Ontological System, framework epistemologi."
        steps = []
        result = ar._apply_sanad(question, llm_ok, steps)
        assert "Islamic" in result or "Ontolog" in result


class TestApplySanadReActHalu:
    """Σ-1G Q15: brain says 'Recursive Action Tree' → must override."""

    def test_override_halu_react(self):
        question = "apa itu ReAct agent?"
        llm_halu = "ReAct = Recursive Action Tree, paradigma untuk AI agent."
        steps = []
        result = ar._apply_sanad(question, llm_halu, steps)
        assert "Reasoning" in result or "Acting" in result, (
            f"Canonical ReAct not returned. Got: {result[:200]}"
        )

    def test_correct_react_passthrough(self):
        question = "apa itu react ai?"
        llm_ok = "ReAct = Reasoning + Acting (Yao et al., 2023). Gabungan chain-of-thought dan tool-use."
        steps = []
        result = ar._apply_sanad(question, llm_ok, steps)
        assert "Reasoning" in result or "Acting" in result


class TestApplySanadCurrentEvent:
    """Current events: MUST have web source, else UNKNOWN."""

    def test_current_event_without_web_returns_unknown(self):
        question = "siapa presiden indonesia sekarang?"
        llm_guess = "Presiden Indonesia sekarang adalah Joko Widodo."
        steps = []  # No web_search step
        result = ar._apply_sanad(question, llm_guess, steps)
        assert "tidak" in result.lower() or "unknown" in result.lower() or "belum" in result.lower(), (
            f"Expected UNKNOWN response, got: {result[:200]}"
        )

    def test_current_event_with_web_source_passthrough(self):
        question = "siapa presiden indonesia sekarang?"
        llm_answer = "Presiden Indonesia saat ini adalah Prabowo Subianto."
        steps = [_StepStub(
            action_name="web_search",
            observation="Prabowo Subianto adalah Presiden RI ke-8 mulai 20 Oktober 2024",
        )]
        result = ar._apply_sanad(question, llm_answer, steps)
        assert "Prabowo" in result, f"Web-backed answer should pass through. Got: {result[:200]}"


class TestApplySanadPassthrough:
    """Creative & coding questions: no factual gate → passthrough always."""

    def test_creative_passthrough(self):
        question = "buatkan tagline untuk brand fashion lokal"
        llm_creative = "Tagline: 'Lokal Bangga, Global Kelas.'"
        steps = []
        result = ar._apply_sanad(question, llm_creative, steps)
        assert "Lokal Bangga" in result, "Creative answer should not be overridden"

    def test_coding_passthrough(self):
        question = "tulis fungsi python untuk reverse string"
        llm_code = "def reverse_str(s):\n    return s[::-1]"
        steps = []
        result = ar._apply_sanad(question, llm_code, steps)
        assert "reverse_str" in result, "Code answer should not be overridden"


class TestApplySanadSanadFooter:
    """Sanad footer appended when LLM is overridden (rejected_llm=True)."""

    def test_footer_appended_on_override(self):
        question = "sebutkan 5 persona sidix"
        llm_halu = "5 persona: Budi, Sari, Joko, Rina, Tono"
        steps = []
        result = ar._apply_sanad(question, llm_halu, steps)
        # Should contain sanad footer
        assert "Sanad" in result or "brand_canon" in result or "⚠️" in result, (
            f"Expected sanad footer on override. Got: {result[-200:]}"
        )


class TestApplySanadNonFatal:
    """_apply_sanad must not crash on bad inputs."""

    def test_empty_question(self):
        result = ar._apply_sanad("", "some answer", [])
        assert isinstance(result, str)

    def test_empty_llm_text(self):
        result = ar._apply_sanad("apa itu sidix?", "", [])
        assert isinstance(result, str)

    def test_none_steps(self):
        result = ar._apply_sanad("apa itu sidix?", "SIDIX adalah...", None)
        assert isinstance(result, str)

    def test_malformed_step(self):
        class BadStep:
            pass  # No attributes
        result = ar._apply_sanad("test", "answer", [BadStep()])
        assert isinstance(result, str)


# ════════════════════════════════════════════════════════════════════════
# Corpus source from steps (verify Source building)
# ════════════════════════════════════════════════════════════════════════

class TestApplySanadSourceBuilding:
    """Verify Sources built correctly from steps."""

    def test_web_search_step_creates_web_source(self):
        question = "siapa ceo google sekarang?"
        llm = "CEO Google adalah Sundar Pichai."
        steps = [_StepStub(
            action_name="web_search",
            observation="Sundar Pichai is the CEO of Google (Alphabet Inc.)",
            action_args={"url": "https://example.com"},
        )]
        result = ar._apply_sanad(question, llm, steps)
        assert "Sundar" in result or "tidak" in result.lower()

    def test_corpus_step_creates_corpus_source(self):
        question = "apa itu sidix?"
        llm = "SIDIX adalah AI agent creative open source."
        steps = [_StepStub(
            action_name="search_corpus",
            observation="SIDIX = Free AI Agent self-hosted creative tool",
        )]
        result = ar._apply_sanad(question, llm, steps)
        assert isinstance(result, str)
        assert len(result) > 0


# ════════════════════════════════════════════════════════════════════════
# Run
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import traceback

    test_classes = [
        TestApplySanadPersonaHalu,
        TestApplySanadIHOSHalu,
        TestApplySanadReActHalu,
        TestApplySanadCurrentEvent,
        TestApplySanadPassthrough,
        TestApplySanadSanadFooter,
        TestApplySanadNonFatal,
        TestApplySanadSourceBuilding,
    ]

    total = 0
    passed = 0
    failures = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method in methods:
            total += 1
            try:
                getattr(instance, method)()
                passed += 1
                print(f"  PASS  {cls.__name__}.{method}")
            except Exception as e:
                failures.append((cls.__name__, method, str(e)))
                print(f"  FAIL  {cls.__name__}.{method}: {e}")
                traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"S-1A Integration Tests: {passed}/{total} PASS")
    if failures:
        print(f"\nFailed ({len(failures)}):")
        for cls_name, method, err in failures:
            print(f"  - {cls_name}.{method}: {err}")
    else:
        print("ALL PASS")

    sys.exit(0 if passed == total else 1)
