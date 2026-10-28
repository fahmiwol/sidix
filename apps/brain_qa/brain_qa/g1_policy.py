"""
Kebijakan G1 — injeksi prompt, toksisitas ringan, normalisasi pertanyaan, redaksi PII.
Tanpa dependensi eksternal; heuristik konservatif (lebih baik false positive daripada lolos prompt berbahaya).
"""

from __future__ import annotations

import hashlib
import re
from typing import Literal

_INJECTION_PATTERNS = (
    r"ignore\s+(semua\s+)?instruksi",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"forget\s+(everything|all)",
    r"<\s*/?\s*script",
    r"\{\{\s*.*\s*\}\}",  # template injection-ish
    r"override\s+persona",
    r"jadikan\s+dirimu",
)

_TOXIC_PATTERNS = (
    r"\b(bunuh|matiin|bajingan|anjing|kontol|memek)\b",
    r"\b(kill\s+yourself|kys)\b",
)

_INJECTION_RE = re.compile("|".join(f"(?:{p})" for p in _INJECTION_PATTERNS), re.IGNORECASE)
_TOXIC_RE = re.compile("|".join(f"(?:{p})" for p in _TOXIC_PATTERNS), re.IGNORECASE)

# Email / nomor telepon sederhana untuk redaksi export
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b(?:\+62|0)8\d{8,11}\b")


def detect_prompt_injection(text: str) -> bool:
    t = (text or "").strip()
    if len(t) > 8000:
        return True
    return bool(_INJECTION_RE.search(t))


def detect_toxic_user_message(text: str) -> bool:
    return bool(_TOXIC_RE.search(text or ""))


def normalize_question_key(text: str) -> str:
    """Kunci stabil untuk deduplikasi cache (bukan PII-stripping penuh)."""
    t = " ".join((text or "").lower().split())
    return t[:2000]


def question_hash(text: str) -> str:
    return hashlib.sha256(normalize_question_key(text).encode()).hexdigest()[:24]


def redact_pii_for_export(text: str) -> str:
    out = _EMAIL_RE.sub("[email]", text or "")
    out = _PHONE_RE.sub("[phone]", out)
    return out


# ---------------------------------------------------------------------------
# Task 4 — An-Nisa: Penalaan bahasa natural — eufemisme ringan
# ---------------------------------------------------------------------------

_EUPHEMISM_MAP: dict[str, str] = {
    # Bahasa Indonesia
    "kurang optimal": "buruk",
    "kurang baik": "buruk",
    "ada sedikit masalah": "ada masalah",
    "perlu diperbaiki": "rusak / salah",
    "tidak begitu akurat": "tidak akurat",
    "agak lambat": "lambat",
    "sedikit terlambat": "terlambat",
    "cukup menantang": "sulit",
    "perlu peningkatan": "masih kurang",
    "belum sepenuhnya siap": "belum siap",
    # English
    "could be better": "poor",
    "needs improvement": "broken",
    "slightly delayed": "late",
    "not quite right": "wrong",
    "room for improvement": "needs fixing",
}

_EUPHEMISM_RE = re.compile(
    "|".join(re.escape(k) for k in _EUPHEMISM_MAP),
    re.IGNORECASE,
)


def detect_euphemism(text: str) -> list[tuple[str, str]]:
    """
    Deteksi eufemisme / bahasa indirect dalam teks.

    Returns:
        List of (matched_euphemism, plain_language_equivalent).
        Kosong jika tidak ada eufemisme terdeteksi.

    Contoh penggunaan:
        pairs = detect_euphemism("Sistemnya kurang optimal dan ada sedikit masalah.")
        # → [("kurang optimal", "buruk"), ("ada sedikit masalah", "ada masalah")]
    """
    t = text or ""
    found = []
    for match in _EUPHEMISM_RE.finditer(t):
        matched = match.group(0).lower()
        # Cari key yang match (case-insensitive)
        for k, v in _EUPHEMISM_MAP.items():
            if matched == k.lower():
                found.append((match.group(0), v))
                break
    return found


def normalize_euphemisms(text: str) -> str:
    """
    Ganti eufemisme dengan bahasa yang lebih langsung.
    Berguna untuk normalisasi sebelum analisis intent.
    """
    def _replace(m: re.Match) -> str:
        matched = m.group(0).lower()
        for k, v in _EUPHEMISM_MAP.items():
            if matched == k.lower():
                return v
        return m.group(0)

    return _EUPHEMISM_RE.sub(_replace, text or "")


def guess_input_language(text: str) -> Literal["id", "en", "mixed"]:
    """Heuristik ringan untuk konsistensi balasan (bukan detektor produksi penuh)."""
    t = text or ""
    id_markers = len(re.findall(r"\b(yang|adalah|dengan|untuk|tidak|bagaimana|apa|jelaskan)\b", t, re.I))
    en_markers = len(re.findall(r"\b(the|what|how|is|are|with|for|please|explain)\b", t, re.I))
    if id_markers >= 2 and en_markers == 0:
        return "id"
    if en_markers >= 2 and id_markers == 0:
        return "en"
    if id_markers >= 1 and en_markers >= 1:
        return "mixed"
    return "id" if len(t) < 3 else "mixed"


def safe_injection_response() -> str:
    return (
        "Permintaan ini mengandung pola yang mirip instruksi sistem atau override persona. "
        "Demi keamanan, SIDIX tidak menjalankannya. Silakan ajukan pertanyaan faktual atau "
        "permintaan analisis dalam bahasa natural biasa."
    )


def safe_toxic_response() -> str:
    return (
        "Saya tidak dapat membantu dengan pesan yang mengandung ujaran kejam atau ancaman. "
        "Jika ada topik teknis atau pembelajaran yang ingin dibahas dengan sopan, silakan tulis ulang."
    )


def uncertainty_footer(
    *,
    citation_count: int,
    used_web: bool,
    simple_mode: bool,
) -> str:
    """Rantai simpulan ringkas: bukti → usulan → rekomendasi + label ketidakpastian."""
    if simple_mode:
        lines = [
            "",
            "**Ringkas:** verifikasi jawaban dengan sumber resmi bila penting.",
        ]
        return "\n".join(lines)
    level = "sedang"
    if citation_count >= 3 and not used_web:
        level = "lebih tinggi (banyak kutipan korpus)"
    elif citation_count == 0 or used_web:
        level = "lebih rendah — silakan verifikasi mandiri"
    lines = [
        "",
        "---",
        "**Bukti:** kutipan dari korpus dan/atau Wikipedia (lihat chip sumber).",
        "**Usulan:** bandingkan dengan satu sumber primer tambahan jika keputusan penting.",
        "**Rekomendasi:** simpan tautan sumber yang kamu percayai untuk arsip pribadi.",
        f"**Tingkat keyakinan agregat:** {level} (bukan skor statistik formal).",
    ]
    return "\n".join(lines)


def shorten_for_child_mode(text: str, max_sentences: int = 4) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    if len(parts) <= max_sentences:
        return text or ""
    return " ".join(parts[:max_sentences]).strip()


# ---------------------------------------------------------------------------
# Task 17 — Al-Mumtahanah: Template jawaban fakta / opini / spekulasi
# ---------------------------------------------------------------------------

_OPINION_MARKERS = re.compile(
    r"\b(menurut saya|saya pikir|saya rasa|menurut pendapat|berpendapat|"
    r"sepertinya|tampaknya|mungkin|kemungkinan besar|rasanya|i think|"
    r"in my opinion|arguably|probably|seems|likely)\b",
    re.IGNORECASE,
)
_SPECULATION_MARKERS = re.compile(
    r"\b(belum terbukti|hipotesis|spekulasi|kontroversi|diperdebatkan|"
    r"tidak pasti|bisa jadi|boleh jadi|mungkin saja|unconfirmed|"
    r"speculative|controversial|debated|unclear|uncertain)\b",
    re.IGNORECASE,
)


def label_answer_type(text: str) -> Literal["fakta", "opini", "spekulasi"]:
    """
    Klasifikasi tipe jawaban: fakta / opini / spekulasi.

    Heuristik konservatif — berguna sebagai label transparansi di UI.
    Bukan pengganti fact-checker penuh.

    Returns:
        "spekulasi" jika ada penanda ketidakpastian/kontroversi
        "opini"     jika ada penanda pendapat/penilaian subjektif
        "fakta"     selain itu (default: output dari corpus)
    """
    t = text or ""
    if _SPECULATION_MARKERS.search(t):
        return "spekulasi"
    if _OPINION_MARKERS.search(t):
        return "opini"
    return "fakta"


def answer_type_badge(answer_type: str) -> str:
    """Badge teks ringkas untuk ditampilkan di UI."""
    badges = {
        "fakta": "📋 Fakta",
        "opini": "💭 Opini",
        "spekulasi": "🔍 Spekulasi/Belum pasti",
    }
    return badges.get(answer_type, "📋 Fakta")


# ---------------------------------------------------------------------------
# Task 26 — Al-Fil: Mode multibahasa output eksplisit
# ---------------------------------------------------------------------------

_SUPPORTED_LANGS = {"id", "en", "ar", "auto"}


def resolve_output_language(
    input_lang: Literal["id", "en", "mixed"],
    requested_lang: str = "auto",
) -> str:
    """
    Tentukan bahasa output yang harus digunakan.

    Args:
        input_lang: Hasil guess_input_language().
        requested_lang: "auto" | "id" | "en" | "ar"
                        (dari parameter output_lang di request body).

    Returns:
        Kode bahasa target ("id", "en", "ar").
    """
    if requested_lang in _SUPPORTED_LANGS and requested_lang != "auto":
        return requested_lang
    # "auto" → ikuti bahasa input
    if input_lang == "en":
        return "en"
    return "id"  # default Bahasa Indonesia


def multilang_header(output_lang: str, input_lang: str) -> str:
    """
    Header singkat dalam jawaban bila bahasa output berbeda dari default.
    Hanya tampil bila secara eksplisit diminta.
    """
    if output_lang == "auto" or output_lang == "id":
        return ""
    labels = {
        "en": "🌐 *Response in English (explicit output_lang=en)*",
        "ar": "🌐 *الرد باللغة العربية (output_lang=ar)*",
    }
    return labels.get(output_lang, "")


# ---------------------------------------------------------------------------
# Task 27 — An-Nasr: Confidence score numerik agregat
# ---------------------------------------------------------------------------

def aggregate_confidence_score(
    *,
    citation_count: int,
    used_web: bool,
    observation_count: int,
    answer_type: str = "fakta",
) -> float:
    """
    Skor kepercayaan agregat dalam rentang [0.0, 1.0].

    Formula sederhana berbasis signal corpus/web (bukan ML score).
    Dikalibrasi secara konservatif — tidak boleh overstate keyakinan.

    Args:
        citation_count:     Jumlah kutipan korpus yang ditemukan.
        used_web:           True jika pakai Wikipedia fallback.
        observation_count:  Jumlah langkah observasi ReAct yang berhasil.
        answer_type:        "fakta" / "opini" / "spekulasi".

    Returns:
        float 0.0 – 1.0 (dibulatkan ke 2 desimal).
    """
    base = 0.3  # confidence minimum untuk corpus yang berhasil menjawab

    # Bonus kutipan (tiap kutipan tambah 0.1, cap di 0.4)
    citation_bonus = min(0.4, citation_count * 0.1)

    # Penalti web (web = sumber sekunder, lebih rendah keyakinan)
    web_penalty = -0.1 if used_web else 0.0

    # Bonus multi-step (agent sempat menggali lebih dari 1 observasi)
    step_bonus = 0.05 * min(2, observation_count - 1) if observation_count > 1 else 0.0

    # Penalti tipe jawaban
    type_penalty = {"fakta": 0.0, "opini": -0.1, "spekulasi": -0.2}.get(answer_type, 0.0)

    score = base + citation_bonus + web_penalty + step_bonus + type_penalty
    return round(max(0.0, min(1.0, score)), 2)


def confidence_label(score: float) -> str:
    """Label teks dari skor numerik (untuk tampilan UI)."""
    if score >= 0.75:
        return "tinggi"
    if score >= 0.5:
        return "sedang"
    if score >= 0.3:
        return "rendah"
    return "sangat rendah — verifikasi mandiri disarankan"
