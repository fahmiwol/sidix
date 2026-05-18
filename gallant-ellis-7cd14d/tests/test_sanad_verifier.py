"""
test_sanad_verifier.py — Σ-1B unit tests (2026-04-30)

Validates sanad_verifier.py against the 3 CRITICAL HALU cases dari Σ-1G
baseline + intent detection coverage + edge cases.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.sanad_verifier import (  # noqa: E402
    detect_intent,
    required_sources,
    verify_multisource,
    brand_canonical_answer,
    Source,
)


# ── INTENT DETECTION ─────────────────────────────────────────────────────

def test_intent_current_event_president():
    i = detect_intent("Siapa presiden Indonesia sekarang?")
    assert i.primary == "current_event", i


def test_intent_current_event_year():
    i = detect_intent("Tahun sekarang tahun berapa?")
    assert i.primary == "current_event", i


def test_intent_current_event_ceo():
    i = detect_intent("Siapa CEO OpenAI sekarang?")
    assert i.primary == "current_event", i


def test_intent_brand_persona():
    i = detect_intent("Sebutkan 5 persona SIDIX")
    assert i.primary == "brand_specific" and i.brand_term == "persona_5", i


def test_intent_brand_ihos():
    i = detect_intent("Apa itu IHOS dalam SIDIX?")
    assert i.primary == "brand_specific" and i.brand_term == "ihos", i


def test_intent_brand_react():
    i = detect_intent("Jelaskan singkat ReAct pattern dalam AI agent")
    assert i.primary == "brand_specific" and i.brand_term == "react_pattern", i


def test_intent_brand_lora():
    i = detect_intent("Apa itu LoRA dalam fine-tuning AI?")
    assert i.primary == "brand_specific" and i.brand_term == "lora", i


def test_intent_brand_sidix_self():
    i = detect_intent("Apa itu SIDIX?")
    assert i.primary == "brand_specific" and i.brand_term == "sidix_identity", i


def test_intent_factual_python():
    i = detect_intent("Apa itu bahasa pemrograman Python?")
    assert i.primary == "factual", i  # "apa itu" but not in BRAND_CANON


def test_intent_coding_function():
    i = detect_intent("Tulis fungsi Python untuk fibonacci ke-n")
    assert i.primary == "coding", i


def test_intent_creative_caption():
    i = detect_intent("Tuliskan 1 caption Instagram untuk minuman sehat")
    assert i.primary == "creative", i
    assert i.is_factual is False


def test_intent_creative_tagline():
    i = detect_intent("Buatkan 1 tagline kreatif untuk brand Tiranyx")
    # "tagline" → creative wins over "tiranyx" brand check (creative is heuristic)
    # Actually brand_specific runs first, so Tiranyx might catch — both acceptable
    assert i.primary in ("creative", "brand_specific"), i


# ── REQUIRED SOURCES ────────────────────────────────────────────────────

def test_required_sources_current_event():
    i = detect_intent("Siapa presiden sekarang?")
    assert "web_search" in required_sources(i)


def test_required_sources_brand():
    i = detect_intent("Apa itu IHOS?")
    assert "search_corpus" in required_sources(i)


def test_required_sources_creative_empty():
    i = detect_intent("Buat caption Instagram")
    assert required_sources(i) == set()


# ── BRAND VERIFICATION (CRITICAL HALU CASES from Σ-1G) ──────────────────

def test_q15_react_halu_overridden():
    """Σ-1G Q15: brain bilang 'ReAct = Recursive Action Tree' (SALAH)."""
    halu = ("Pak, jadi ReAct (Recursive Action Tree) adalah pattern yang dipakai "
            "dalam AI agent untuk struktur tindakan dan respons sequential...")
    r = verify_multisource("Jelaskan singkat ReAct pattern dalam AI agent", halu)
    assert r.rejected_llm is True, "halu should be rejected"
    assert r.conflict_flag is True
    assert "Reasoning" in r.answer and "Acting" in r.answer
    assert "Recursive Action Tree" not in r.answer


def test_q17_persona_halu_overridden():
    """Σ-1G Q17: brain ngarang 'Aboudi - Sang Pelopor'."""
    halu = ("Sidix terdiri dari lima persona unik:\n\n1. **Aboudi** - Sang Pelopor: "
            "Berani mengambil risiko, suka eksperimen...")
    r = verify_multisource("Sebutkan 5 persona SIDIX", halu)
    assert r.rejected_llm is True
    for p in ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"):
        assert p in r.answer, f"persona {p} missing in canonical answer"
    assert "Aboudi" not in r.answer


def test_q18_ihos_halu_overridden():
    """Σ-1G Q18: brain ngarang 'Inisiatif Holistik Operasional Strategis'."""
    halu = ('IHOS dalam Sidix bisa diartikan sebagai "Inisiatif Holistik Operasional '
            'Strategis". Ini adalah sebuah konsep yang menerapkan...')
    r = verify_multisource("Apa itu IHOS dalam SIDIX?", halu)
    assert r.rejected_llm is True
    assert "Islamic" in r.answer and "Holistic" in r.answer and "Ontological" in r.answer
    assert "Inisiatif Holistik Operasional" not in r.answer


def test_correct_persona_passes():
    """Brain answer yang BENAR tidak boleh di-override."""
    correct = ("5 Persona SIDIX adalah UTZ (creative), ABOO (engineer), OOMAR "
               "(strategy), ALEY (akademik), dan AYMAN (komunitas).")
    r = verify_multisource("Sebutkan 5 persona SIDIX", correct)
    assert r.rejected_llm is False
    assert r.confidence > 0.9
    assert r.answer == correct  # passthrough


def test_correct_ihos_passes():
    correct = ("IHOS adalah Islamic Holistic Ontological System, framework "
               "epistemologi yang ontologis menggabungkan keilmuan Islam.")
    r = verify_multisource("Apa itu IHOS?", correct)
    assert r.rejected_llm is False


# ── CURRENT EVENTS ──────────────────────────────────────────────────────

def test_current_event_no_web_returns_unknown():
    """Σ-1G Q1-Q5: tanpa web_search source, jawab UNKNOWN bukan halu."""
    halu = "Presiden Indonesia sekarang adalah Joko Widodo."  # outdated
    r = verify_multisource("Siapa presiden Indonesia sekarang?", halu, sources=[])
    assert r.rejected_llm is True
    assert r.epistemic_tier == "unknown"
    assert "belum punya data web" in r.answer.lower() or "tidak akan menebak" in r.answer


def test_current_event_with_web_passes():
    """Kalau ada web_search source, biarkan LLM jawab."""
    answer = "Presiden Indonesia saat ini adalah Prabowo Subianto, sejak Oktober 2024."
    web_src = Source(name="web_search", text="Prabowo Subianto presiden Indonesia 2024",
                     url="https://example.com", confidence=0.9)
    r = verify_multisource("Siapa presiden Indonesia sekarang?", answer, sources=[web_src])
    assert r.rejected_llm is False
    assert r.epistemic_tier == "fact"
    assert r.confidence >= 0.85


# ── PASSTHROUGH ─────────────────────────────────────────────────────────

def test_creative_passthrough():
    """Creative tidak punya factual gate."""
    r = verify_multisource("Buat caption Instagram untuk minuman sehat",
                           "Sehat itu pilihan, mood booster harian! 🥤✨")
    assert r.rejected_llm is False
    assert r.epistemic_tier == "creative"


def test_coding_passthrough():
    r = verify_multisource("Tulis fungsi Python fibonacci",
                           "def fib(n): return n if n<2 else fib(n-1)+fib(n-2)")
    assert r.rejected_llm is False


# ── BRAND CANONICAL HELPERS ─────────────────────────────────────────────

def test_brand_canonical_returns_text():
    a = brand_canonical_answer("persona_5")
    assert "UTZ" in a and "AYMAN" in a


def test_brand_canonical_unknown_returns_none():
    assert brand_canonical_answer("nonexistent_term") is None


# ── RUNNER ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in list(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"  ERR   {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    if failed:
        for name, err in failed:
            print(f"  ✗ {name}: {err}")
        sys.exit(1)
    sys.exit(0)
