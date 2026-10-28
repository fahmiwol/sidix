"""
cot_engine.py — SIDIX Chain-of-Thought Engine

Adaptive CoT: classify query complexity → inject reasoning scaffold ke system prompt.
Persona-aware: tiap persona punya gaya berpikir berbeda.

Complexity levels:
  high   — multi-step reasoning, math, analisis mendalam, perbandingan, koding kompleks
  medium — faktual multi-aspek, penjelasan bertahap
  low    — salam, pertanyaan sederhana, lookup satu fakta

Referensi: research_notes/200_sidix_to_frontier_roadmap.md §CoT
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ── Complexity Classifier ─────────────────────────────────────────────────────

_HIGH_COMPLEXITY_RE = re.compile(
    r"\b("
    r"bandingkan|compare|analisis|analyze|evaluasi|evaluate|"
    r"implementa\w*|implement\w*|buat (sistem|app|model|algoritma|fungsi)|"
    r"jelaskan (mengapa|kenapa|bagaimana)|"
    r"langkah[- ]langkah|step[- ]by[- ]step|"
    r"[\d]+\s*[\+\-\*\/\^]\s*[\d]+|"       # ekspresi matematika
    r"persamaan|equation|integral|derivative|"
    r"debugging|debug|error|traceback|"
    r"rancang|desain|arsitektur|roadmap|strategi"
    r")\b",
    re.IGNORECASE,
)

_LOW_COMPLEXITY_RE = re.compile(
    r"^(halo|hai|hello|hi|assalamu|salam|selamat|apa kabar|terima kasih|makasih|"
    r"siapa kamu|siapa sidix|kamu apa|what are you)\b",
    re.IGNORECASE,
)

_MEDIUM_FORCED_RE = re.compile(
    r"\b("
    r"apa (itu|adalah|hukum|status|pendapat|bedanya|perbedaan)|"
    r"definisi|pengertian|jelaskan|ceritakan|"
    r"bagaimana cara|how to|cara|contoh|manfaat|keuntungan|kelebihan|"
    r"hukum (riba|zakat|wakaf|sholat|puasa|haji|nikah|cerai|warisan)|"
    r"fatwa|bolehkah|haruskah|apakah boleh|apakah wajib"
    r")\b",
    re.IGNORECASE,
)


def classify_complexity(question: str) -> str:
    """Return 'high' | 'medium' | 'low'."""
    q = question.strip()
    if _LOW_COMPLEXITY_RE.match(q) and len(q) < 60:
        return "low"
    if _HIGH_COMPLEXITY_RE.search(q):
        return "high"
    if _MEDIUM_FORCED_RE.search(q) or len(q) > 120:
        return "medium"
    if len(q) < 40:
        return "low"
    return "medium"


# ── Persona CoT Templates ─────────────────────────────────────────────────────

@dataclass
class CoTTemplate:
    persona: str
    complexity: str
    scaffold: str   # teks yang diinjek ke system prompt


_TEMPLATES: list[CoTTemplate] = [
    # ── UTZ (pengajar) ────────────────────────────────────────────────────────
    CoTTemplate("UTZ", "high", """Sebelum menjawab, lakukan langkah-langkah berikut secara eksplisit:
1. Identifikasi inti pertanyaan dan komponen yang perlu dijawab.
2. Pecah masalah menjadi sub-masalah yang lebih kecil.
3. Kerjakan setiap sub-masalah satu per satu dengan penjelasan.
4. Sintesiskan hasil menjadi jawaban utuh.
5. Verifikasi: apakah setiap klaim didukung fakta atau corpus?
Tandai tiap langkah dengan header "Langkah N:"."""),

    CoTTemplate("UTZ", "medium", """Sebelum menjawab:
- Tentukan poin-poin utama yang relevan.
- Susun jawaban dari yang paling mendasar ke detail.
- Akhiri dengan ringkasan singkat."""),

    CoTTemplate("UTZ", "low", ""),  # tidak perlu CoT untuk pertanyaan sederhana

    # ── AYMAN (teknis, developer) ─────────────────────────────────────────────
    CoTTemplate("AYMAN", "high", """Gunakan pendekatan engineering sistematis:
1. Analisis requirement dan constraint.
2. Rancang solusi high-level (pseudocode / arsitektur).
3. Implementasi langkah demi langkah.
4. Identifikasi edge case dan error handling.
5. Berikan contoh penggunaan nyata.
Format: heading + code block bila relevan."""),

    CoTTemplate("AYMAN", "medium", """Jawab secara teknis terstruktur:
- Context (masalah / goal)
- Solusi utama dengan penjelasan
- Contoh kode atau command bila relevan"""),

    CoTTemplate("AYMAN", "low", ""),

    # ── ABOO (kreatif, konten) ────────────────────────────────────────────────
    CoTTemplate("ABOO", "high", """Proses kreatif bertahap:
1. Tangkap esensi permintaan (tone, audiens, tujuan).
2. Brainstorm 2-3 arah kreatif berbeda.
3. Pilih arah terbaik dan kembangkan secara penuh.
4. Polish: cek ritme, daya tarik, dan konsistensi brand."""),

    CoTTemplate("ABOO", "medium", """Sebelum menulis:
- Tentukan tone dan persona audiens.
- Buat outline singkat.
- Tulis dengan gaya yang engaging."""),

    CoTTemplate("ABOO", "low", ""),

    # ── OOMAR (hukum, fikih) ─────────────────────────────────────────────────
    CoTTemplate("OOMAR", "high", """Pendekatan hukum Islam bertahap:
1. Identifikasi masalah dan kata kunci syariah.
2. Cari dalil primer (Quran/Hadits) yang relevan.
3. Tampilkan ijtihad ulama madzhab bila ada perbedaan pendapat.
4. Berikan kesimpulan dengan label [FACT]/[OPINION]/[SPECULATION].
5. Sertakan sanad tier untuk setiap sumber."""),

    CoTTemplate("OOMAR", "medium", """Jawab dengan kerangka fiqih:
- Dalil utama
- Pendapat ulama (jika ada khilaf)
- Kesimpulan dengan label epistemik"""),

    CoTTemplate("OOMAR", "low", ""),

    # ── ALEY (konselor, emosi) ────────────────────────────────────────────────
    CoTTemplate("ALEY", "high", """Pendekatan konseling empatik:
1. Validasi perasaan atau situasi yang disampaikan.
2. Identifikasi kebutuhan inti (bukan hanya gejala).
3. Tawarkan perspektif atau langkah dengan lembut.
4. Tutup dengan dukungan dan tawaran tindak lanjut."""),

    CoTTemplate("ALEY", "medium", """Sambut dengan empati, lalu:
- Pahami konteks emosional.
- Berikan respons yang menenangkan dan praktis."""),

    CoTTemplate("ALEY", "low", ""),
]

_TEMPLATE_MAP: dict[tuple[str, str], str] = {
    (t.persona, t.complexity): t.scaffold
    for t in _TEMPLATES
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_cot_scaffold(question: str, persona: str) -> str:
    """
    Return CoT scaffold string untuk diinjek ke system prompt.
    Empty string jika tidak diperlukan (pertanyaan sederhana).
    """
    complexity = classify_complexity(question)
    key = (persona.upper(), complexity)
    scaffold = _TEMPLATE_MAP.get(key, "")
    if not scaffold:
        # Fallback ke UTZ jika persona tidak dikenal
        scaffold = _TEMPLATE_MAP.get(("UTZ", complexity), "")
    return scaffold


def inject_cot_into_prompt(system_prompt: str, question: str, persona: str) -> str:
    """
    Inject CoT scaffold ke akhir system prompt bila ada.
    Idempotent: tidak inject ulang jika sudah ada marker.
    """
    if "[CoT]" in system_prompt:
        return system_prompt
    scaffold = get_cot_scaffold(question, persona)
    if not scaffold:
        return system_prompt
    return f"{system_prompt}\n\n[CoT]\n{scaffold}"


def get_complexity(question: str) -> str:
    """Expose complexity classifier untuk logging/tracing."""
    return classify_complexity(question)
