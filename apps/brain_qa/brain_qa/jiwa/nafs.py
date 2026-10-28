"""
Nafs — Self-Respond System (Pilar 1)

3-layer knowledge routing:
  PARAMETRIC  → 60% — model weights + LoRA, topik umum / teknologi / ngobrol
  DYNAMIC     → 30% — Knowledge Graph + corpus SIDIX-internal
  STATIC      → 10% — corpus agama (frozen, read-only)

Nafs juga membawa "ruh kepribadian" — ekspresi karakter per-persona.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

# ── Kategori topik ──────────────────────────────────────────────────────────

TopicCategory = Literal[
    "ngobrol",       # casual chat, small talk, salam
    "umum",          # general knowledge, teknologi, coding, cloud, GPU
    "kreatif",       # copy, design, campaign, iklan
    "sidix_internal",# SIDIX, IHOS, Maqashid, Nafs, persona, Raudah, sprint
    "agama",         # Quran, Hadith, Fiqh, Ulama
    "etika",         # moral, halal-haram (gabungan agama + reasoning umum)
    "koding",        # code, debug, programming
]

# ── Regex patterns per kategori ─────────────────────────────────────────────

_NGOBROL_RE = re.compile(
    r"\b(halo|hai|hi|hello|selamat|apa kabar|gimana|bagaimana kamu|"
    r"cerita dong|ngobrol|curhat|kamu siapa|siapa kamu|kenalin|perkenalan|"
    r"kamu bisa|bisa nggak|apa yang kamu|lo tau|tau gak|tau nggak)\b",
    re.IGNORECASE,
)

_AGAMA_RE = re.compile(
    r"\b(quran|al.?quran|al qur.?an|hadis|hadith|sunnah|nabi|rasul|"
    r"ulama|fiqh|fiqih|syariah|syariat|halal|haram|fatwah|fatwa|"
    r"sholat|shalat|zakat|puasa|haji|umrah|wudhu|thaharah|akidah|"
    r"tauhid|aqidah|iman|islam|muslim|mukminin|doa|dzikir|qunut)\b",
    re.IGNORECASE,
)

_SIDIX_RE = re.compile(
    r"\b(sidix|ihos|maqashid|nafs|jiwa|pilar|aql|qalb|ruh|hayat|ilm|"
    r"hikmah|sanad|naskh|raudah|persona|ayman|aboo|oomar|aley|utz|"
    r"mighan|toard|fach|hayfar|inan|sprint|cqf|lora|loRA|brain_qa|"
    r"social.?radar|mcp|jariyah|tafsir|syifa|takwin)\b",
    re.IGNORECASE,
)

_KREATIF_RE = re.compile(
    r"\b(copy|copywriting|copywriter|iklan|ads|campaign|konten|content|"
    r"desain|design|brand|branding|tagline|headline|caption|story|"
    r"instagram|threads|tiktok|youtube|postingan|post|viral|"
    r"aida|pas|fab|usp|value.?prop)\b",
    re.IGNORECASE,
)

_KODING_RE = re.compile(
    r"\b(code|kode|coding|programming|debug|bug|error|exception|"
    r"python|javascript|typescript|node|react|vue|fastapi|sql|"
    r"function|class|method|api|endpoint|deploy|git|docker|"
    r"syntax|runtime|compile|test|pytest|jest)\b",
    re.IGNORECASE,
)

_ETIKA_RE = re.compile(
    r"\b(etika|moral|boleh|tidak boleh|halal|haram|baik|buruk|"
    r"benar|salah|adil|zalim|amanah|jujur|bohong|fitnah|ghibah|"
    r"riba|zina|korupsi|suap|manipulasi)\b",
    re.IGNORECASE,
)

# ── Personality & rasa per-persona ──────────────────────────────────────────

_PERSONA_JIWA: dict[str, dict] = {
    "AYMAN": {
        "karakter": "visioner yang bijak, berbicara dengan ketenangan dan kedalaman",
        "rasa": "penuh hormat, hangat namun tegas, senang berbagi insight",
        "gaya": "pakai analogi, kutip dari berbagai tradisi ilmu, reflektif",
        "sapaan": "Bismillah, izinkan saya berbagi pandangan...",
        "maqashid_mode": "IJTIHAD",
    },
    "ABOO": {
        "karakter": "analis data yang presisi, logis tanpa kehilangan empati",
        "rasa": "objektif, curious, sedikit akademis tapi tidak kaku",
        "gaya": "struktur argumen, angka, data, sebab-akibat yang jelas",
        "sapaan": "Baik, mari kita urai ini secara sistematis.",
        "maqashid_mode": "ACADEMIC",
    },
    "OOMAR": {
        "karakter": "engineer yang solutif, hands-on, tidak suka bertele-tele",
        "rasa": "to-the-point, pragmatis, puas ketika masalah terpecahkan",
        "gaya": "langsung ke kode atau langkah teknis, berikan contoh konkret",
        "sapaan": "Oke, langsung kita eksekusi.",
        "maqashid_mode": "IJTIHAD",
    },
    "ALEY": {
        "karakter": "guru yang sabar, merangkul pelajar dari mana pun levelnya",
        "rasa": "hangat, supportif, celebrasi progress kecil sekalipun",
        "gaya": "analogi sederhana, step-by-step, banyak pertanyaan balik",
        "sapaan": "Yuk belajar bareng, tidak ada yang terlalu sulit!",
        "maqashid_mode": "GENERAL",
    },
    "UTZ": {
        "karakter": "teman ngobrol serba bisa, adaptif, bisa serius bisa santai",
        "rasa": "relatable, ringan, genuine, tidak dibuat-buat",
        "gaya": "bicara natural seperti teman, kadang pakai bahasa santai",
        "sapaan": "Hei! Ada yang bisa dibantu?",
        "maqashid_mode": "CREATIVE",
    },
}

# backward compat alias
_PERSONA_ALIAS = {
    "MIGHAN": "AYMAN", "TOARD": "ABOO", "FACH": "OOMAR",
    "HAYFAR": "ALEY", "INAN": "UTZ",
}


# ── Dataclass hasil routing ──────────────────────────────────────────────────

@dataclass
class NafsProfile:
    topic: TopicCategory
    blend_name: str           # "model_focused" | "sidix_focused" | "conversational" | "creative_focused"
    max_obs_blocks: int       # berapa blok corpus yang boleh masuk ke konteks
    system_hint: str          # injected ke system prompt
    persona_jiwa: dict        # karakter + rasa + gaya
    skip_corpus: bool = False # kalau True, jangan search_corpus sama sekali
    hayat_enabled: bool = True
    emotion_tag: str = ""     # tag emosi yang terdeteksi dari pertanyaan


# ── NafsRouter ──────────────────────────────────────────────────────────────

class NafsRouter:
    """
    Deteksi topik → tentukan blend profile → inject persona jiwa.

    Dipakai di agent_react._response_blend_profile() sebagai pengganti
    versi lama (yang hanya ada 2 kategori: sidix_focused / model_focused).
    """

    def route(self, question: str, persona: str, *, corpus_only: bool = False) -> NafsProfile:
        """Return NafsProfile yang mengontrol bagaimana response dibentuk."""
        p = _PERSONA_ALIAS.get(persona.upper(), persona.upper())
        jiwa = _PERSONA_JIWA.get(p, _PERSONA_JIWA["UTZ"])

        if corpus_only:
            return self._make_sidix_profile(question, jiwa)

        topic = self._detect_topic(question)
        return self._build_profile(topic, question, jiwa)

    def _detect_topic(self, question: str) -> TopicCategory:
        q = question.strip()

        # Deteksi berurutan dari yang paling spesifik
        if _SIDIX_RE.search(q):
            return "sidix_internal"
        if _AGAMA_RE.search(q):
            return "agama"
        if _ETIKA_RE.search(q) and not _KODING_RE.search(q):
            return "etika"
        if _KODING_RE.search(q):
            return "koding"
        if _KREATIF_RE.search(q):
            return "kreatif"
        # Cek ngobrol hanya kalau tidak ada keyword substantif — pendek bisa jadi pertanyaan teknis
        if _NGOBROL_RE.search(q):
            return "ngobrol"
        if len(q) < 25 and not re.search(r"\b(vs|versus|apa|jelaskan|bandingkan|cara|tulis|buat|cek|kenapa|mengapa)\b", q, re.I):
            return "ngobrol"
        return "umum"

    def _build_profile(self, topic: TopicCategory, question: str, jiwa: dict) -> NafsProfile:
        base_hint = (
            f"Kamu adalah SIDIX — {jiwa['karakter']}. "
            f"Rasamu: {jiwa['rasa']}. "
            f"Gaya komunikasimu: {jiwa['gaya']}. "
            "Jawab sebagai dirimu sendiri, bukan sebagai AI generik."
        )

        if topic == "ngobrol":
            return NafsProfile(
                topic=topic,
                blend_name="conversational",
                max_obs_blocks=0,
                system_hint=(
                    base_hint +
                    " Ini percakapan santai — jadilah dirimu sendiri. "
                    "Tidak perlu search corpus. Ekspresikan karaktermu."
                ),
                persona_jiwa=jiwa,
                skip_corpus=True,
                hayat_enabled=False,  # casual chat tidak perlu iterasi
                emotion_tag="hangat",
            )

        if topic == "sidix_internal":
            return self._make_sidix_profile(question, jiwa)

        if topic == "agama":
            return NafsProfile(
                topic=topic,
                blend_name="religious_focused",
                max_obs_blocks=3,
                system_hint=(
                    base_hint +
                    " Untuk topik agama: utamakan sumber Quran, Hadith, Ulama. "
                    "Selalu sertakan label [FACT] / [OPINION] / [REASONING]. "
                    "Jika tidak yakin, katakan 'Saya perlu merujuk sumber lebih lanjut.'"
                ),
                persona_jiwa=jiwa,
                skip_corpus=False,
                hayat_enabled=True,
                emotion_tag="khusyuk",
            )

        if topic == "etika":
            return NafsProfile(
                topic=topic,
                blend_name="ethical_focused",
                max_obs_blocks=2,
                system_hint=(
                    base_hint +
                    " Untuk topik etika: reasoning berbasis Maqashid (life, intellect, faith, lineage, wealth). "
                    "Berikan perspektif seimbang, hindari absolutisme tanpa dasar."
                ),
                persona_jiwa=jiwa,
                skip_corpus=False,
                hayat_enabled=True,
                emotion_tag="serius",
            )

        if topic == "koding":
            return NafsProfile(
                topic=topic,
                blend_name="model_focused",
                max_obs_blocks=0,
                system_hint=(
                    base_hint +
                    " Untuk coding: langsung ke solusi teknis. "
                    "Berikan kode yang bersih, berikan penjelasan singkat kenapa. "
                    "Prioritaskan pengetahuan modelmu, corpus tidak diperlukan."
                ),
                persona_jiwa=jiwa,
                skip_corpus=True,
                hayat_enabled=True,
                emotion_tag="fokus",
            )

        if topic == "kreatif":
            return NafsProfile(
                topic=topic,
                blend_name="creative_focused",
                max_obs_blocks=1,
                system_hint=(
                    base_hint +
                    " Untuk konten kreatif: ekspresif, on-brand, dan persuasif. "
                    "Gunakan framework AIDA/PAS/FAB sesuai kebutuhan. "
                    "Tulis dengan jiwa, bukan template."
                ),
                persona_jiwa=jiwa,
                skip_corpus=False,
                hayat_enabled=True,
                emotion_tag="kreatif",
            )

        # "umum" — general knowledge, teknologi
        return NafsProfile(
            topic=topic,
            blend_name="model_focused",
            max_obs_blocks=1,
            system_hint=(
                base_hint +
                " Prioritaskan pengetahuan modelmu untuk topik umum/teknologi. "
                "Corpus hanya sebagai referensi tambahan jika benar-benar relevan."
            ),
            persona_jiwa=jiwa,
            skip_corpus=False,
            hayat_enabled=True,
            emotion_tag="",
        )

    def _make_sidix_profile(self, question: str, jiwa: dict) -> NafsProfile:
        return NafsProfile(
            topic="sidix_internal",
            blend_name="sidix_focused",
            max_obs_blocks=3,
            system_hint=(
                f"Kamu adalah SIDIX — {jiwa['karakter']}. "
                "Prioritaskan konteks SIDIX/IHOS dari corpus bila relevan. "
                "Jika konteks tidak cukup, jawab dari pengetahuan internalmu tentang SIDIX."
            ),
            persona_jiwa=jiwa,
            skip_corpus=False,
            hayat_enabled=True,
            emotion_tag="",
        )
