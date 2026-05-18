"""
Pytest suite untuk Pivot 2026-04-25 Maturity Sprint.

Covers:
  - Response hygiene (_apply_hygiene, _strip_leaked_block, _dedupe_label)
  - Follow-up detection (_is_followup, _reformulate_with_context)
  - Self-critique lite (_self_critique_lite)
  - Persona alignment (_score_persona, resolve_style_persona)
  - Current-events routing (_needs_web_search)

Diangkat dari scripts/_test_*.py menjadi pytest proper supaya:
  1. Masuk CI (173 → 190+ tests)
  2. Regression protection otomatis
  3. Bisa dipanggil via `pytest tests/test_pivot_maturity.py`
"""

from __future__ import annotations

import pytest

from brain_qa.agent_react import (
    _apply_hygiene,
    _cognitive_self_check,
    _dedupe_label,
    _is_followup,
    _needs_web_search,
    _reformulate_with_context,
    _self_critique_lite,
    _strip_leaked_block,
)
from brain_qa.persona import _score_persona, resolve_style_persona


# ── Response Hygiene ──────────────────────────────────────────────────────────


class TestResponseHygiene:
    def test_dedupe_sanad_missing(self):
        text = "[⚠️ SANAD MISSING]\n[⚠️ SANAD MISSING]\ncontent"
        out = _apply_hygiene(text)
        assert out.count("[⚠️ SANAD MISSING]") == 1

    def test_dedupe_exploratory(self):
        text = "body\n\n[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]\n[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]"
        out = _apply_hygiene(text)
        assert out.count("[EXPLORATORY") == 1

    def test_dedupe_fakta_multiple(self):
        text = "[FAKTA] A\n[FAKTA] B\n[FAKTA] C\n[FAKTA] D"
        out = _apply_hygiene(text)
        assert out.count("[FAKTA]") == 1

    def test_strip_leaked_konteks_block(self):
        text = "[KONTEKS DARI KNOWLEDGE BASE SIDIX]\nSome dump\nMore dump\n\nReal answer here."
        out = _apply_hygiene(text)
        assert "KONTEKS DARI KNOWLEDGE BASE" not in out
        assert "Real answer here" in out

    def test_strip_leaked_aturan_block(self):
        text = "[ATURAN PEMAKAIAN KONTEKS]\nGunakan sebagai panduan\n\nJawaban: halo!"
        out = _apply_hygiene(text)
        assert "ATURAN PEMAKAIAN" not in out
        assert "halo" in out

    def test_collapse_blank_lines(self):
        text = "Baris 1\n\n\n\n\nBaris 2"
        out = _apply_hygiene(text)
        assert "\n\n\n" not in out

    def test_edge_empty(self):
        assert _apply_hygiene("") == ""

    def test_edge_whitespace_only(self):
        result = _apply_hygiene("   ")
        assert result == "   "

    def test_edge_none(self):
        assert _apply_hygiene(None) is None

    def test_clean_text_preserved(self):
        text = "[FAKTA] Recursion adalah fungsi.\n\nContoh: faktorial."
        out = _apply_hygiene(text)
        assert "[FAKTA]" in out
        assert "Recursion" in out


# ── Follow-up Detection ───────────────────────────────────────────────────────


class TestFollowupDetection:
    @pytest.mark.parametrize("question", [
        "itu apa?",
        "yang tadi",
        "lebih singkat dong",
        "lebih ringkas",
        "terjemahkan ke inggris",
        "terjemahkan ke bahasa arab",
        "coba yang lain",
        "coba yang lebih pendek",
        "kasih contoh",
        "berikan contoh",
        "kenapa begitu?",
        "lanjut",
        "lanjutkan",
        "ringkas dong",
        "jelaskan lebih",
        "oke, terus gimana?",
    ])
    def test_positive_detection(self, question):
        assert _is_followup(question) is True

    @pytest.mark.parametrize("question", [
        "apa itu recursion?",
        "Jelaskan Big O notation",
        "Siapa presiden Indonesia saat ini?",
        "hai sidix",
        "",
    ])
    def test_negative_detection(self, question):
        assert _is_followup(question) is False

    def test_reformulate_with_context(self):
        context = [
            {"role": "user", "content": "Apa itu recursion dalam programming?"},
            {"role": "assistant", "content": "Recursion adalah fungsi yang memanggil dirinya."},
        ]
        out = _reformulate_with_context("kasih contoh", context)
        assert "FOLLOW-UP" in out
        assert "recursion" in out.lower()

    def test_reformulate_no_context_unchanged(self):
        out = _reformulate_with_context("kasih contoh", [])
        assert out == "kasih contoh"

    def test_reformulate_non_followup_unchanged(self):
        context = [{"role": "user", "content": "prev"}]
        out = _reformulate_with_context("Apa itu pointer dalam C?", context)
        assert out == "Apa itu pointer dalam C?"


# ── Self-Critique Lite ────────────────────────────────────────────────────────


class TestSelfCritiqueLite:
    def test_over_label_reduction(self):
        text = "\n".join([f"[FAKTA] claim {i}" for i in range(7)])
        out = _self_critique_lite(text, "test", "ABOO")
        assert out.count("[FAKTA]") == 1

    def test_question_mirror_strip(self):
        q = "Apa itu recursion?"
        text = "Apa itu recursion? Recursion adalah fungsi yang call dirinya."
        out = _self_critique_lite(text, q, "ABOO")
        assert not out.lower().startswith("apa itu recursion")

    def test_persona_boilerplate_strip(self):
        text = "Gue ABOO, bagian dari SIDIX dengan keahlian teknis. Recursion itu simple."
        out = _self_critique_lite(text, "q", "ABOO")
        assert "bagian dari SIDIX" not in out
        assert "Recursion itu simple" in out

    def test_clean_text_preserved(self):
        text = "Recursion adalah fungsi yang memanggil dirinya sendiri."
        out = _self_critique_lite(text, "q", "ABOO")
        assert "Recursion adalah fungsi" in out

    def test_too_short_guard(self):
        # Output <20 char → fallback to original (no damage)
        assert _self_critique_lite("ok", "test", "ABOO") == "ok"

    def test_empty_safe(self):
        assert _self_critique_lite("", "q", "p") == ""
        assert _self_critique_lite(None, "q", "p") is None


# ── Persona Alignment ─────────────────────────────────────────────────────────


class TestPersonaAlignment:
    @pytest.mark.parametrize("question,expected", [
        ("Buatkan fungsi Python untuk reverse string", "ABOO"),
        ("Debug error stack trace saya", "ABOO"),
        ("Design logo untuk kedai kopi", "UTZ"),
        ("Kasih ide caption marketing instagram", "UTZ"),
        ("Riset metodologi paper tentang LLM", "ALEY"),
        ("Apa itu statistik inferensial dalam tesis", "ALEY"),
        ("Bikin roadmap arsitektur microservices", "OOMAR"),
        ("Strategi marketing untuk startup B2B", "OOMAR"),
        ("Apa hukum riba dalam Islam?", "AYMAN"),
        ("Jelaskan tentang sholat tahajud", "AYMAN"),
        ("Halo sidix", "AYMAN"),
    ])
    def test_auto_persona_selection(self, question, expected):
        scores = _score_persona(question)
        top = max(scores, key=scores.get)
        assert top == expected, f"For {question!r}: got {top}, scores={scores}"

    @pytest.mark.parametrize("style,expected", [
        ("teknis", "ABOO"),
        ("technical", "ABOO"),
        ("kreatif", "UTZ"),
        ("creative", "UTZ"),
        ("akademik", "ALEY"),
        ("academic", "ALEY"),
        ("strategi", "OOMAR"),
        ("rencana", "OOMAR"),
        ("singkat", "AYMAN"),
    ])
    def test_style_map_aligned(self, style, expected):
        actual = resolve_style_persona(style, "AYMAN")
        assert actual == expected


# ── Current-Events Routing ────────────────────────────────────────────────────


class TestCurrentEventsRouting:
    @pytest.mark.parametrize("question", [
        "Apa berita hari ini soal AI?",
        "Harga bitcoin sekarang",
        "Siapa presiden Amerika saat ini",
        "Kurs dollar hari ini",
        "Cuaca hari ini di Jakarta",
    ])
    def test_positive_routing(self, question):
        assert _needs_web_search(question) is True

    @pytest.mark.parametrize("question", [
        "Apa itu rekursi",
        "Jelaskan Big O notation",
        "Apa hukum riba dalam Islam",
        "Halo sidix",
        "",
    ])
    def test_negative_routing(self, question):
        assert _needs_web_search(question) is False


# ── Helpers: _dedupe_label + _strip_leaked_block ──────────────────────────────


class TestHygieneHelpers:
    def test_dedupe_label_single_no_change(self):
        assert _dedupe_label("[FAKTA] once", r"\[FAKTA\]") == "[FAKTA] once"

    def test_dedupe_label_multiple(self):
        out = _dedupe_label("[FAKTA] a [FAKTA] b [FAKTA] c", r"\[FAKTA\]")
        assert out.count("[FAKTA]") == 1

    def test_strip_leaked_block_present(self):
        text = "[PERTANYAAN USER]\nsome stuff\n\nreal answer"
        out = _strip_leaked_block(text, "[PERTANYAAN USER]")
        assert "PERTANYAAN USER" not in out
        assert "real answer" in out

    def test_strip_leaked_block_absent(self):
        text = "no marker here"
        out = _strip_leaked_block(text, "[PERTANYAAN USER]")
        assert out == "no marker here"


# ── Cognitive Self-Check (Brain Upgrade) ──────────────────────────────────────


class TestCognitiveSelfCheck:
    def test_numeric_claims_without_citation_triggers_caveat(self):
        draft = "Perusahaan menghasilkan 500 juta rupiah setiap bulan dan mengalami kenaikan 30%."
        revised, warnings = _cognitive_self_check(draft, citations=[], question="q", persona="OOMAR")
        assert any("numeric_claims_without_citation" in w for w in warnings)
        assert "belum terverifikasi" in revised

    def test_numeric_claims_with_citation_no_caveat(self):
        draft = "Perusahaan menghasilkan 500 juta rupiah setiap bulan dan kenaikan 30%."
        citations = [{"type": "web_search", "url": "https://example.com"}]
        revised, warnings = _cognitive_self_check(draft, citations=citations, question="q", persona="OOMAR")
        assert "belum terverifikasi" not in revised

    def test_over_confidence_softening(self):
        draft = "Python pasti lebih cepat dari Java. Dan selalu lebih baik."
        revised, warnings = _cognitive_self_check(draft, citations=[], question="q", persona="ABOO")
        assert any("over_confidence" in w for w in warnings)
        # "pasti" harus jadi "kemungkinan besar" atau "selalu" → "umumnya"
        assert "pasti" not in revised.lower() or "kemungkinan besar" in revised.lower()

    def test_utz_persona_skipped(self):
        # UTZ = creative, tidak boleh di-critique oleh numeric check
        draft = "Kedai kopi kami pasti punya 100 juta pelanggan setiap bulan dan selalu ramai."
        revised, warnings = _cognitive_self_check(draft, citations=[], question="q", persona="UTZ")
        assert revised == draft  # tidak diubah
        assert warnings == []

    def test_ayman_persona_skipped(self):
        # AYMAN = casual/open-minded, skip CSC agar bisa ngobrol kosong
        # tanpa auto-critique. User direction 2026-04-25.
        draft = "Aku ngerasa hari ini 100% lebih ramai dari kemarin, pasti karena cuaca cerah!"
        revised, warnings = _cognitive_self_check(draft, citations=[], question="q", persona="AYMAN")
        assert revised == draft
        assert warnings == []

    def test_empty_draft_safe(self):
        revised, warnings = _cognitive_self_check("", citations=[], question="q", persona="AYMAN")
        assert revised == ""
        assert warnings == []

    def test_clean_draft_no_warnings(self):
        draft = "Recursion adalah fungsi yang memanggil dirinya sendiri."
        revised, warnings = _cognitive_self_check(draft, citations=[], question="q", persona="ABOO")
        assert revised == draft
