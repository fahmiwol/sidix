from brain_qa.omnyx_direction import (
    IntentClassifier,
    _current_datetime_response,
    _current_indonesia_official_response,
    _sanitize_public_answer,
    _personal_memory_response,
    _select_relevant_web_answer,
)
from datetime import datetime, timezone
from brain_qa.agent_react import _apply_hygiene, _reformulate_with_context


def test_hijau_does_not_match_hi_greeting():
    intent, tools = IntentClassifier.classify(
        "Untuk test memori: nama saya Mighan dan warna favorit saya hijau zamrud."
    )

    assert intent == "personal_memory"
    assert tools == []


def test_select_relevant_web_answer_prefers_distance_sentence():
    web_text = """
Matahari — Wikipedia: Matahari

Matahari adalah bintang di pusat Tata Surya.
Jarak rata-ratanya dari Bumi adalah sekitar 1,496×108 kilometer atau sekitar 8 menit cahaya.
Diameternya sekitar 1,391,400 km.
"""

    answer = _select_relevant_web_answer(
        "Berapa jarak rata-rata Bumi ke Matahari? Jawab singkat.",
        web_text,
    )

    assert "Jarak rata-ratanya dari Bumi" in answer
    assert "1,496" in answer
    assert len(answer) < 260


def test_personal_memory_response_reads_color_from_context():
    query = """[KONTEKS PERCAKAPAN SEBELUMNYA]
User: Untuk test memori: nama saya Mighan dan warna favorit saya hijau zamrud. Jawab singkat saja.
Assistant: Siap, saya catat.
[AKHIR KONTEKS]

[PERTANYAAN SAAT INI]
Apa warna favorit saya tadi?"""

    answer = _personal_memory_response(query, "UTZ")

    assert answer == "Warna favorit Anda tadi: hijau zamrud."


def test_personal_memory_response_does_not_invent_without_context():
    answer = _personal_memory_response("Apa warna favorit saya tadi? Jawab singkat.", "UTZ")

    assert "belum punya catatan warna favorit" in answer
    assert "tadi?" not in answer


def test_personal_memory_response_reads_structured_notes_from_context():
    query = """[KONTEKS PERCAKAPAN SEBELUMNYA]
User: Tolong catat untuk QA: Fakta 1: kode taman saya adalah Raudah-Alpha. Jawab OK saja.
Assistant: Siap, saya catat.
User: Tolong catat untuk QA: Fakta 7: prioritas saya adalah anti-halusinasi. Jawab OK saja.
Assistant: Siap, saya catat.
[AKHIR KONTEKS]

[PERTANYAAN SAAT INI]
Dari catatan QA tadi, apa kode taman saya dan apa prioritas saya? Jawab singkat."""

    answer = _personal_memory_response(query, "UTZ")

    assert "Kode taman Anda: Raudah-Alpha" in answer
    assert "Prioritas Anda: anti-halusinasi" in answer


def test_followup_wakilnya_reformulates_from_president_context():
    context = [
        {"role": "user", "content": "siapa presiden indonesia?"},
        {
            "role": "assistant",
            "content": "Presiden Indonesia saat ini adalah Prabowo Subianto, dilantik pada Oktober 2024.",
        },
    ]

    reformulated = _reformulate_with_context("kalo wakilnya?", context)

    assert reformulated == "Siapa wakil presiden Indonesia saat ini?"


def test_current_indonesia_official_fast_path_answers_president():
    answer = _current_indonesia_official_response("siapa presiden indonesia?")

    assert answer == "Presiden Indonesia saat ini adalah Prabowo Subianto."


def test_current_datetime_fast_path_answers_day_without_web_search():
    now = datetime(2026, 5, 2, 9, 51, tzinfo=timezone.utc)

    answer = _current_datetime_response("hari apa sekarang?", now=now)

    assert answer == "Sekarang hari Sabtu, 2 Mei 2026 (WIB)."
    assert "Hari Bumi" not in answer


def test_current_indonesia_official_fast_path_answers_vice_president():
    answer = _current_indonesia_official_response("Siapa wakil presiden Indonesia saat ini?")

    assert answer == "Wakil Presiden Indonesia saat ini adalah Gibran Rakabuming Raka."


def test_public_answer_sanitizer_removes_prompt_leak_sections():
    leaky = """Presiden Indonesia saat ini adalah Prabowo Subianto.

---

**ATRIBUSI**

- Web Search: Dari Wikipedia.

---

**RESPONS NATURAL**

Kalau kamu perlu informasi lebih lanjut, hubungi saya!
[AKHIR KONTEKS]

[PERTANYAAN SAAT INI]
kalo wakilnya?
"""

    answer = _sanitize_public_answer(leaky)
    hygienic = _apply_hygiene(leaky)

    assert answer == "Presiden Indonesia saat ini adalah Prabowo Subianto."
    assert "[AKHIR KONTEKS]" not in hygienic
    assert "[PERTANYAAN SAAT INI]" not in hygienic
