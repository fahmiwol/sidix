from brain_qa.omnyx_direction import (
    IntentClassifier,
    _personal_memory_response,
    _select_relevant_web_answer,
)


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
