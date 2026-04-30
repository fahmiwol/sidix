"""
user_intelligence.py — SIDIX User Intelligence Module
======================================================
Memahami "frekuensi" pengguna: bahasa, literasi, maksud, konteks budaya.

Pipeline:
    raw_input → detect_language → infer_literacy → classify_intent
              → detect_cultural_frame → UserProfile
              → agent_react dapat adjust tone/depth/style otomatis

Author: SIDIX Core Team
Date: 2026-04-17
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class Language(str, Enum):
    INDONESIAN   = "id"
    ARABIC       = "ar"
    ENGLISH      = "en"
    JAVANESE     = "jv"
    SUNDANESE    = "su"
    CODE_MIXING  = "mixed"   # ID+EN dominan
    UNKNOWN      = "unknown"


class LiteracyLevel(str, Enum):
    AWAM       = "awam"       # Bahasa sehari-hari, hindari jargon
    MENENGAH   = "menengah"   # Tahu konsep dasar, boleh sedikit teknis
    AHLI       = "ahli"       # Jargon OK, referensi teknis OK
    AKADEMIK   = "akademik"   # Sitasi, terminologi formal, critical analysis


class IntentArchetype(str, Enum):
    CREATIVE        = "creative"        # ingin membuat, berkarya
    TECHNICAL       = "technical"       # butuh solusi teknis, kode
    ANALYTICAL      = "analytical"      # ingin memahami, analisis
    FACTUAL         = "factual"         # butuh fakta/data spesifik
    PROCEDURAL      = "procedural"      # langkah-langkah cara melakukan
    PHILOSOPHICAL   = "philosophical"   # diskusi ide, makna, etika
    CONVERSATIONAL  = "conversational"  # ngobrol, sambat, curhat
    ISLAMIC         = "islamic"         # fiqih, tafsir, akidah, ibadah
    UNKNOWN         = "unknown"


class CulturalFrame(str, Enum):
    NUSANTARA = "nusantara"   # Javanese/Sundanese/Betawi etc. cultural context
    ISLAMIC   = "islamic"     # Deen-centric framing
    WESTERN   = "western"     # Global/Western secular framing
    ACADEMIC  = "academic"    # Academic/scholarly framing
    MIXED     = "mixed"       # Multiple frames detected
    NEUTRAL   = "neutral"     # No strong cultural signal


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """Profil pengguna yang diinfer dari satu input atau akumulasi sesi."""
    language: Language             = Language.UNKNOWN
    literacy: LiteracyLevel        = LiteracyLevel.MENENGAH
    intent: IntentArchetype        = IntentArchetype.UNKNOWN
    cultural_frame: CulturalFrame  = CulturalFrame.NEUTRAL

    # Confidence scores [0.0–1.0]
    language_confidence: float     = 0.0
    literacy_confidence: float     = 0.0
    intent_confidence: float       = 0.0

    # Derived tone suggestions for agent_react
    suggested_formality: str       = "semiformal"   # formal / semiformal / kasual
    suggested_depth: str           = "medium"       # brief / medium / deep
    suggested_style: str           = "direct"       # direct / narrative / Socratic

    # Raw signals (for debugging / explainability)
    detected_signals: list[str]    = field(default_factory=list)

    def to_system_hint(self) -> str:
        """Generate system hint string untuk di-inject ke agent_react prompt."""
        parts = [
            f"[USER_PROFILE]",
            f"Bahasa: {self.language.value} (conf={self.language_confidence:.2f})",
            f"Literasi: {self.literacy.value} (conf={self.literacy_confidence:.2f})",
            f"Intent: {self.intent.value} (conf={self.intent_confidence:.2f})",
            f"Budaya: {self.cultural_frame.value}",
            f"Gaya respons yang disarankan: formality={self.suggested_formality}, "
            f"depth={self.suggested_depth}, style={self.suggested_style}",
        ]
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# LANGUAGE DETECTION
# ---------------------------------------------------------------------------

# Stopwords & markers per bahasa
_ID_MARKERS = {
    "yang", "dan", "di", "dengan", "untuk", "adalah", "ini", "itu", "ada",
    "tidak", "bisa", "akan", "sudah", "juga", "saya", "kamu", "kami", "kita",
    "mereka", "apa", "bagaimana", "kenapa", "gimana", "dong", "lah", "kan",
    "banget", "emang", "udah", "aja", "yuk", "nih", "sih", "deh", "nya",
    "sangat", "lebih", "dari", "ke", "pada", "dalam", "atau", "jika",
    "kalau", "supaya", "agar", "karena", "sehingga", "namun", "tetapi",
    "maka", "oleh", "tentang", "seperti", "bahwa", "belum", "bukan",
    "tolong", "mohon", "coba", "perlu", "harus",
}

_AR_MARKERS = {
    "في", "من", "إلى", "على", "هذا", "هذه", "ما", "لا", "مع", "عن",
    "كيف", "لماذا", "هل", "نعم", "لا", "الله", "رسول", "قال", "حديث",
    "آية", "سورة", "القرآن", "الفقه", "الحكم", "المسألة", "الدليل",
    "والسلام", "عليكم", "السلام", "بسم", "الرحمن", "الرحيم",
}

_EN_MARKERS = {
    "the", "is", "are", "was", "were", "have", "has", "do", "does",
    "can", "could", "should", "would", "will", "that", "this", "with",
    "from", "about", "what", "how", "why", "when", "where", "who",
    "please", "help", "need", "want", "know", "think", "make", "get",
}

_JV_MARKERS = {
    "aku", "kowe", "iki", "iku", "ora", "lan", "nanging", "yen",
    "mangga", "sugeng", "matur", "nuwun", "monggo", "nggih",
    "pundi", "menapa", "punapa",
}

_SU_MARKERS = {
    "abdi", "anjeun", "ieu", "eta", "sareng", "teu", "naha",
    "kumaha", "mana", "hatur", "nuhun", "wilujeng",
}

# Arabic Unicode block: U+0600–U+06FF
_AR_UNICODE_RE = re.compile(r'[\u0600-\u06FF]')

# Code-mixing signal: English word inside Indonesian sentence
_EN_WORD_IN_ID_CONTEXT = re.compile(
    r'\b(update|install|download|click|login|setting|error|bug|file|'
    r'server|database|api|request|response|frontend|backend|deploy|'
    r'testing|debug|feature|fix|merge|push|pull|commit|branch)\b',
    re.IGNORECASE
)


def detect_language(text: str) -> tuple[Language, float]:
    """
    Deteksi bahasa dominan dari teks input.

    Returns:
        (Language, confidence_score 0.0–1.0)
    """
    if not text or not text.strip():
        return Language.UNKNOWN, 0.0

    text_lower = text.lower()
    tokens = re.findall(r'\b\w+\b', text_lower)
    total = max(len(tokens), 1)

    # Check Arabic Unicode presence first (script-level detection)
    ar_chars = len(_AR_UNICODE_RE.findall(text))
    if ar_chars > 3:
        conf = min(1.0, ar_chars / max(len(text.replace(" ", "")), 1))
        return Language.ARABIC, round(conf, 2)

    # Count marker hits
    id_hits = sum(1 for t in tokens if t in _ID_MARKERS)
    en_hits = sum(1 for t in tokens if t in _EN_MARKERS)
    jv_hits = sum(1 for t in tokens if t in _JV_MARKERS)
    su_hits = sum(1 for t in tokens if t in _SU_MARKERS)

    id_score = id_hits / total
    en_score = en_hits / total

    # Code-mixing: Indonesian base + significant English tech terms
    code_mix_hits = len(_EN_WORD_IN_ID_CONTEXT.findall(text))
    if id_score > 0.05 and code_mix_hits >= 2:
        conf = min(1.0, (id_score + 0.1) * 0.9)
        return Language.CODE_MIXING, round(conf, 2)

    # Javanese / Sundanese check (before ID, as some overlap)
    if jv_hits >= 2 and jv_hits > su_hits:
        conf = min(1.0, jv_hits / total * 3)
        return Language.JAVANESE, round(conf, 2)
    if su_hits >= 2:
        conf = min(1.0, su_hits / total * 3)
        return Language.SUNDANESE, round(conf, 2)

    scores = {
        Language.INDONESIAN: id_score,
        Language.ENGLISH: en_score,
    }
    best_lang = max(scores, key=scores.get)
    best_score = scores[best_lang]

    if best_score < 0.05:
        return Language.UNKNOWN, round(best_score, 2)

    confidence = min(1.0, best_score * 4)  # normalize: 0.25 hit rate → 1.0 conf
    return best_lang, round(confidence, 2)


# ---------------------------------------------------------------------------
# LITERACY LEVEL INFERENCE
# ---------------------------------------------------------------------------

# Jargon/istilah teknis per domain
_TECHNICAL_JARGON = {
    # Programming
    "api", "rest", "graphql", "endpoint", "asyncio", "coroutine", "docker",
    "kubernetes", "microservice", "orm", "schema", "migration", "refactor",
    "polymorphism", "inheritance", "decorator", "middleware", "webhook",
    "payload", "serialization", "deserialization", "vector", "embedding",
    "tokenizer", "inference", "fine-tune", "lora", "qlora", "grpo",
    "debug", "debugging", "stacktrace", "traceback", "exception", "runtime",
    "fastapi", "django", "flask", "pytorch", "tensorflow", "langchain",
    "llm", "rag", "bm25", "faiss", "chromadb", "weaviate",
    # Science/Math
    "distribusi", "hipotesis", "regresi", "korelasi", "variance", "sigmoid",
    "gradient", "backpropagation", "entropy", "perplexity", "likelihood",
    # Islamic scholarship
    "sanad", "matan", "isnad", "rawi", "jarh", "ta'dil", "mutawatir",
    "ahad", "shahih", "hasan", "dhaif", "maudu", "fiqih", "ushul",
    "qiyas", "ijma", "ijtihad", "maqashid", "kulliyyat", "daruriyyat",
    "hajiyyat", "tahsiniyyat", "tahlil", "tarkib", "i'rab",
    # Design/Visual
    "aperture", "bokeh", "kerning", "leading", "tracking", "cmyk", "rgb",
    "codec", "bitrate", "latent", "diffusion", "vae", "transformer",
}

_ACADEMIC_SIGNALS = {
    "menurut", "berdasarkan", "analisis", "metodologi", "hipotesis",
    "teori", "paradigma", "epistemologi", "ontologi", "aksiologi",
    "literatur", "referensi", "sitasi", "abstrak", "variabel",
    "korelasi", "kausalitas", "signifikan", "validitas", "reliabilitas",
    # English academic
    "according", "based", "analysis", "methodology", "framework",
    "paradigm", "epistemology", "epistemological", "ontology", "theory",
    "hypothesis", "literature", "implications", "inference", "bayesian",
    "implications", "authentication", "correlation", "causality",
    "significance", "validity", "reliability", "theoretical",
}

_AWAM_SIGNALS = {
    # Bahasa sangat informal / sehari-hari
    "gimana", "gitu", "gini", "iya", "nggak", "enggak", "ngga",
    "banget", "bgt", "yg", "trs", "jd", "krn", "udah", "udh",
    "mau", "pengen", "pgn", "blm", "blum", "kaya", "kayak", "emang",
    "nih", "deh", "sih", "loh", "lo", "gue", "lu",
}

_QUESTION_COMPLEXITY_RE = re.compile(
    r'\b(perbedaan antara|bagaimana cara kerja|apa implikasi|mengapa|'
    r'jelaskan|bandingkan|evaluasi|analisis|what is the difference|'
    r'how does .+ work|what are the implications|explain|compare|'
    r'evaluate|analyze)\b',
    re.IGNORECASE
)


def infer_literacy(text: str, language: Language = Language.INDONESIAN) -> tuple[LiteracyLevel, float]:
    """
    Infer tingkat literasi/teknis pengguna dari cara mereka menulis.

    Signals:
    - Jumlah jargon teknis
    - Kosakata akademik
    - Bahasa informal/slang
    - Kompleksitas pertanyaan
    - Panjang kalimat rata-rata

    Returns:
        (LiteracyLevel, confidence_score)
    """
    if not text or not text.strip():
        return LiteracyLevel.MENENGAH, 0.0

    text_lower = text.lower()
    tokens = re.findall(r'\b\w+\b', text_lower)
    total = max(len(tokens), 1)

    # Count signals
    jargon_hits = sum(1 for t in tokens if t in _TECHNICAL_JARGON)
    academic_hits = sum(1 for t in tokens if t in _ACADEMIC_SIGNALS)
    awam_hits = sum(1 for t in tokens if t in _AWAM_SIGNALS)
    complexity_hits = len(_QUESTION_COMPLEXITY_RE.findall(text))

    jargon_ratio = jargon_hits / total
    awam_ratio = awam_hits / total

    # Sentence length as sophistication proxy
    sentences = re.split(r'[.!?؟]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    avg_sentence_len = (
        sum(len(s.split()) for s in sentences) / len(sentences)
        if sentences else 5
    )

    # --- Decision Tree (priority order) ---

    # 1. AKADEMIK: strong academic vocabulary (>=3) OR jargon-heavy + long formal prose
    #    Require academic_hits>=1 to avoid misclassifying short technical questions
    if academic_hits >= 3 or (academic_hits >= 1 and jargon_ratio > 0.08 and avg_sentence_len > 15):
        return LiteracyLevel.AKADEMIK, min(1.0, 0.6 + academic_hits * 0.05)

    # 2. AWAM: informal signals dominate (check BEFORE ahli to avoid jargon override)
    #    Awam wins if: awam_ratio significant AND awam_hits >= jargon_hits
    if awam_ratio > 0.06 or (awam_hits >= 1 and awam_hits >= jargon_hits):
        return LiteracyLevel.AWAM, min(1.0, 0.5 + awam_ratio * 3 + awam_hits * 0.05)

    # 3. AHLI: clear technical jargon (>=2 hits OR ratio significant) OR complex question
    #    Require >=2 jargon hits to prevent single-word false positives (e.g. "fiqih")
    if (jargon_hits >= 2 and jargon_ratio > 0.04) or complexity_hits >= 2:
        return LiteracyLevel.AHLI, min(1.0, 0.5 + jargon_ratio * 5)

    # 4. Default: MENENGAH
    return LiteracyLevel.MENENGAH, 0.65


# ---------------------------------------------------------------------------
# INTENT CLASSIFICATION
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: dict[IntentArchetype, list[str]] = {
    IntentArchetype.CREATIVE: [
        r'\b(buat|bikin|tulis|generate|ciptakan|desain|gambar|karang|'
        r'compose|create|write|generate|design|draw|craft|make)\b',
        r'\b(puisi|cerpen|lagu|skenario|konten|artikel|caption|novel|'
        r'poem|story|song|script|content|article)\b',
    ],
    IntentArchetype.TECHNICAL: [
        r'\b(kode|code|bug|error|fix|debug|install|deploy|setup|'
        r'implementasi|implement|fungsi|function|class|method|api|'
        r'database|query|server|docker|git)\b',
        r'\b(bagaimana cara|how to|how do i|cara membuat|cara install)\b',
    ],
    IntentArchetype.ANALYTICAL: [
        r'\b(analisis|analisa|bandingkan|compare|perbedaan|difference|'
        r'kelebihan|kekurangan|pros|cons|evaluasi|evaluate|mengapa|why|'
        r'jelaskan|explain|hubungan|relationship|dampak|impact|efek)\b',
    ],
    IntentArchetype.FACTUAL: [
        r'\b(apa itu|what is|siapa|who is|kapan|when|di mana|where is|'
        r'berapa|how many|how much|definisi|definition|pengertian|'
        r'fakta|fact|data|statistik|statistics|sejarah|history)\b',
    ],
    IntentArchetype.PROCEDURAL: [
        r'\b(langkah|step|cara|how to|tutorial|panduan|guide|instruksi|'
        r'instruction|proses|process|metode|method|prosedur|procedure)\b',
    ],
    IntentArchetype.PHILOSOPHICAL: [
        r'\b(makna|meaning|hakikat|essence|esensi|filsafat|philosophy|'
        r'etika|ethics|moral|nilai|value|benar|salah|right|wrong|'
        r'eksistensi|existence|kesadaran|consciousness|kebenaran|truth)\b',
    ],
    IntentArchetype.CONVERSATIONAL: [
        r'\b(hai|halo|hi|hello|apa kabar|how are you|ngobrol|chat|'
        r'cerita|curhat|sambat|sharing|pendapat|opinion|pikiran|thought)\b',
        r'^(halo|hai|hi|hello|assalamu|salam)\b',
    ],
    IntentArchetype.ISLAMIC: [
        r'\b(hukum|dalil|hadits|quran|sunnah|fiqih|syariah|ibadah|'
        r'sholat|puasa|zakat|haji|doa|dzikir|tafsir|aqidah|akhlak|'
        r'halal|haram|makruh|mubah|wajib|sunnah|muamalah|nikah|talak|'
        r'faraid|wasiat|wakaf|jihad|taubat|istighfar|tawakkal|sabar)\b',
        r'\b(allah|rasulullah|nabi|muhammad|islam|muslim|muslimah|'
        r'masjid|ustadz|ulama|imam|khutbah|dakwah|hijrah)\b',
    ],
}

# Compile patterns
_COMPILED_INTENT = {
    archetype: [re.compile(p, re.IGNORECASE) for p in patterns]
    for archetype, patterns in _INTENT_PATTERNS.items()
}


def classify_intent(text: str) -> tuple[IntentArchetype, float]:
    """
    Klasifikasi intent utama dari input pengguna.

    Returns:
        (IntentArchetype, confidence_score)
    """
    if not text or not text.strip():
        return IntentArchetype.UNKNOWN, 0.0

    scores: dict[IntentArchetype, int] = {}

    for archetype, patterns in _COMPILED_INTENT.items():
        hits = 0
        for pat in patterns:
            hits += len(pat.findall(text))
        if hits > 0:
            scores[archetype] = hits

    if not scores:
        # Fallback: short texts without clear signal → conversational
        if len(text.split()) < 10:
            return IntentArchetype.CONVERSATIONAL, 0.4
        return IntentArchetype.UNKNOWN, 0.0

    best = max(scores, key=scores.get)
    total_hits = sum(scores.values())
    confidence = min(1.0, scores[best] / max(total_hits, 1) * 1.5)

    return best, round(confidence, 2)


# ---------------------------------------------------------------------------
# CULTURAL FRAME DETECTION
# ---------------------------------------------------------------------------

_CULTURAL_SIGNALS: dict[CulturalFrame, list[str]] = {
    CulturalFrame.NUSANTARA: [
        "batik", "wayang", "gamelan", "gotong royong", "musyawarah", "mufakat",
        "adat", "budaya", "suku", "daerah", "jawa", "sunda", "betawi", "minang",
        "batak", "bugis", "bali", "papua", "nusantara", "kearifan lokal",
        "pancasila", "bhinneka", "bhineka",
    ],
    CulturalFrame.ISLAMIC: [
        "bismillah", "alhamdulillah", "insyaallah", "subhanallah", "masya allah",
        "barakallah", "jazakallah", "assalamualaikum", "waalaikumsalam",
        "shalawat", "quran", "hadits", "sunnah", "fiqih", "syariah",
        "halal", "haram", "taqwa", "iman", "ihsan", "ikhlas",
        "dakwah", "hijrah", "ummat", "umat", "masjid", "ulama",
    ],
    CulturalFrame.WESTERN: [
        "deadline", "meeting", "brainstorm", "kpi", "roi", "startup",
        "agile", "sprint", "feedback", "framework", "best practice",
        "networking", "branding", "marketing", "pitch", "investor",
        "efficiency", "productivity", "mindset", "growth hacking",
    ],
    CulturalFrame.ACADEMIC: [
        "penelitian", "jurnal", "paper", "publikasi", "metodologi",
        "literatur", "referensi", "sitasi", "abstrak", "hipotesis",
        "variabel", "sampel", "populasi", "signifikan", "validitas",
        "reliabilitas", "paradigma", "epistemologi", "ontologi",
        "research", "journal", "publication", "methodology",
    ],
}

_COMPILED_CULTURAL = {
    frame: [re.compile(r'\b' + re.escape(sig) + r'\b', re.IGNORECASE) for sig in signals]
    for frame, signals in _CULTURAL_SIGNALS.items()
}


def detect_cultural_frame(text: str) -> CulturalFrame:
    """
    Deteksi framing budaya dari input pengguna.
    """
    if not text or not text.strip():
        return CulturalFrame.NEUTRAL

    scores: dict[CulturalFrame, int] = {}

    for frame, patterns in _COMPILED_CULTURAL.items():
        hits = sum(1 for pat in patterns if pat.search(text))
        if hits > 0:
            scores[frame] = hits

    if not scores:
        return CulturalFrame.NEUTRAL

    if len(scores) >= 3:
        return CulturalFrame.MIXED

    # Islamic + Nusantara often co-occur — return ISLAMIC as primary (more specific)
    if CulturalFrame.ISLAMIC in scores and CulturalFrame.NUSANTARA in scores:
        return CulturalFrame.ISLAMIC

    return max(scores, key=scores.get)


# ---------------------------------------------------------------------------
# RESPONSE STYLE DERIVATION
# ---------------------------------------------------------------------------

_FORMALITY_MAP: dict[tuple[Language, LiteracyLevel], str] = {
    (Language.INDONESIAN, LiteracyLevel.AWAM): "kasual",
    (Language.INDONESIAN, LiteracyLevel.MENENGAH): "semiformal",
    (Language.INDONESIAN, LiteracyLevel.AHLI): "formal",
    (Language.INDONESIAN, LiteracyLevel.AKADEMIK): "formal",
    (Language.CODE_MIXING, LiteracyLevel.AWAM): "kasual",
    (Language.CODE_MIXING, LiteracyLevel.MENENGAH): "semiformal",
    (Language.ENGLISH, LiteracyLevel.AWAM): "casual",
    (Language.ENGLISH, LiteracyLevel.MENENGAH): "semiformal",
    (Language.ENGLISH, LiteracyLevel.AHLI): "formal",
    (Language.ARABIC, LiteracyLevel.AHLI): "formal",
    (Language.ARABIC, LiteracyLevel.AKADEMIK): "formal",
}

_DEPTH_MAP: dict[IntentArchetype, str] = {
    IntentArchetype.FACTUAL: "brief",
    IntentArchetype.CONVERSATIONAL: "brief",
    IntentArchetype.PROCEDURAL: "medium",
    IntentArchetype.CREATIVE: "medium",
    IntentArchetype.TECHNICAL: "deep",
    IntentArchetype.ANALYTICAL: "deep",
    IntentArchetype.PHILOSOPHICAL: "deep",
    IntentArchetype.ISLAMIC: "medium",
    IntentArchetype.UNKNOWN: "medium",
}

_STYLE_MAP: dict[IntentArchetype, str] = {
    IntentArchetype.CONVERSATIONAL: "narrative",
    IntentArchetype.PHILOSOPHICAL: "Socratic",
    IntentArchetype.ANALYTICAL: "Socratic",
    IntentArchetype.TECHNICAL: "direct",
    IntentArchetype.PROCEDURAL: "direct",
    IntentArchetype.FACTUAL: "direct",
    IntentArchetype.CREATIVE: "narrative",
    IntentArchetype.ISLAMIC: "narrative",
    IntentArchetype.UNKNOWN: "direct",
}


def _derive_response_style(
    language: Language,
    literacy: LiteracyLevel,
    intent: IntentArchetype,
    cultural_frame: CulturalFrame,
) -> tuple[str, str, str]:
    """
    Returns (formality, depth, style) tuple.
    """
    formality = _FORMALITY_MAP.get(
        (language, literacy),
        "semiformal"
    )

    # Islamic context → more formal even for awam
    if cultural_frame == CulturalFrame.ISLAMIC and formality == "kasual":
        formality = "semiformal"

    depth = _DEPTH_MAP.get(intent, "medium")
    style = _STYLE_MAP.get(intent, "direct")

    return formality, depth, style


# ---------------------------------------------------------------------------
# MAIN API
# ---------------------------------------------------------------------------

def analyze_user(text: str) -> UserProfile:
    """
    Analisis lengkap input pengguna → UserProfile.

    Ini adalah fungsi utama yang dipanggil oleh agent_react.

    Args:
        text: Raw input dari pengguna (satu turn)

    Returns:
        UserProfile dengan semua field terisi
    """
    signals: list[str] = []

    # 1. Language detection
    lang, lang_conf = detect_language(text)
    signals.append(f"lang={lang.value}({lang_conf:.2f})")

    # 2. Literacy inference
    literacy, lit_conf = infer_literacy(text, lang)
    signals.append(f"literacy={literacy.value}({lit_conf:.2f})")

    # 3. Intent classification
    intent, intent_conf = classify_intent(text)
    signals.append(f"intent={intent.value}({intent_conf:.2f})")

    # 4. Cultural frame
    cultural = detect_cultural_frame(text)
    signals.append(f"cultural={cultural.value}")

    # 5. Derive response style
    formality, depth, style = _derive_response_style(lang, literacy, intent, cultural)

    return UserProfile(
        language=lang,
        literacy=literacy,
        intent=intent,
        cultural_frame=cultural,
        language_confidence=lang_conf,
        literacy_confidence=lit_conf,
        intent_confidence=intent_conf,
        suggested_formality=formality,
        suggested_depth=depth,
        suggested_style=style,
        detected_signals=signals,
    )


def get_response_instructions(profile: UserProfile) -> str:
    """
    Generate instruksi bahasa Indonesia untuk agent_react berdasarkan profil pengguna.
    Dirancang untuk dimasukkan ke dalam system prompt / context agent.
    """
    lines = []

    # Language instruction
    lang_instrs = {
        Language.INDONESIAN: "Balas dalam Bahasa Indonesia yang natural.",
        Language.ARABIC: "Balas dalam Bahasa Arab yang fasih dan tepat.",
        Language.ENGLISH: "Reply in natural English.",
        Language.JAVANESE: "Gunakan Bahasa Indonesia dengan sedikit nuansa Jawa jika sesuai.",
        Language.SUNDANESE: "Gunakan Bahasa Indonesia dengan sedikit nuansa Sunda jika sesuai.",
        Language.CODE_MIXING: "Gunakan Bahasa Indonesia; istilah teknis dalam bahasa Inggris OK.",
        Language.UNKNOWN: "Gunakan Bahasa Indonesia sebagai default.",
    }
    lines.append(lang_instrs.get(profile.language, lang_instrs[Language.UNKNOWN]))

    # Literacy instruction
    lit_instrs = {
        LiteracyLevel.AWAM: (
            "Pengguna masih baru di topik ini. "
            "Gunakan bahasa sehari-hari, analogi sederhana, hindari jargon. "
            "Jika perlu istilah teknis, jelaskan dulu."
        ),
        LiteracyLevel.MENENGAH: (
            "Pengguna memahami konsep dasar. "
            "Boleh gunakan istilah teknis umum, tapi tetap beri konteks."
        ),
        LiteracyLevel.AHLI: (
            "Pengguna paham bidangnya. "
            "Gunakan terminologi teknis tanpa perlu menjelaskan dari awal. "
            "Langsung ke inti jawaban."
        ),
        LiteracyLevel.AKADEMIK: (
            "Pengguna berorientasi akademik/riset. "
            "Boleh gunakan sitasi, terminologi formal, dan analisis kritis. "
            "Sertakan nuansa ketidakpastian dan batasan jika relevan."
        ),
    }
    lines.append(lit_instrs.get(profile.literacy, lit_instrs[LiteracyLevel.MENENGAH]))

    # Depth instruction
    depth_instrs = {
        "brief": "Jawab singkat dan padat. Tidak perlu elaborasi panjang.",
        "medium": "Berikan jawaban yang cukup lengkap dengan contoh bila relevan.",
        "deep": "Berikan jawaban mendalam: latar belakang, analisis, contoh, dan implikasi.",
    }
    lines.append(depth_instrs.get(profile.suggested_depth, depth_instrs["medium"]))

    # Style instruction
    style_instrs = {
        "direct": "Gaya langsung: pernyataan jelas, struktur bullet/numbered jika perlu.",
        "narrative": "Gaya naratif: alur yang mengalir, tidak kaku, terasa seperti percakapan.",
        "Socratic": "Gaya Sokrates: bantu pengguna berpikir dengan pertanyaan pembuka, lalu analisis bersama.",
    }
    lines.append(style_instrs.get(profile.suggested_style, style_instrs["direct"]))

    # Cultural/Islamic addendum
    if profile.cultural_frame == CulturalFrame.ISLAMIC:
        lines.append(
            "Konteks Islami terdeteksi. "
            "Gunakan referensi quran/hadits bila relevan, "
            "hormati sensitivitas fiqih, dan tunjukkan adab."
        )
    elif profile.cultural_frame == CulturalFrame.NUSANTARA:
        lines.append(
            "Konteks budaya Nusantara terdeteksi. "
            "Gunakan analogi lokal bila cocok."
        )

    return "\n".join(f"- {line}" for line in lines)


# ---------------------------------------------------------------------------
# SESSION ACCUMULATOR (untuk multi-turn context)
# ---------------------------------------------------------------------------

class SessionIntelligence:
    """
    Akumulasi sinyal lintas giliran dalam satu sesi.
    Memberikan profil yang lebih akurat dari satu pesan saja.
    """

    def __init__(self) -> None:
        self._turns: list[UserProfile] = []

    def update(self, text: str) -> UserProfile:
        """Proses satu turn baru, return profil kumulatif."""
        profile = analyze_user(text)
        self._turns.append(profile)
        return self.aggregate()

    def aggregate(self) -> UserProfile:
        """Agregasi profil dari semua turn."""
        if not self._turns:
            return UserProfile()

        if len(self._turns) == 1:
            return self._turns[0]

        # Language: vote dari semua turn
        lang_votes: dict[Language, float] = {}
        for t in self._turns:
            lang_votes[t.language] = lang_votes.get(t.language, 0) + t.language_confidence
        best_lang = max(lang_votes, key=lang_votes.get)
        lang_conf = lang_votes[best_lang] / len(self._turns)

        # Literacy: take maximum observed (pengguna menunjukkan kemampuan tertingginya)
        _lit_order = [LiteracyLevel.AWAM, LiteracyLevel.MENENGAH,
                      LiteracyLevel.AHLI, LiteracyLevel.AKADEMIK]
        max_lit = max(self._turns, key=lambda t: _lit_order.index(t.literacy))
        literacy = max_lit.literacy

        # Intent: last turn is most relevant
        last = self._turns[-1]

        # Cultural frame: any Islamic signal dominates (conservative default)
        cultural_votes: dict[CulturalFrame, int] = {}
        for t in self._turns:
            cultural_votes[t.cultural_frame] = cultural_votes.get(t.cultural_frame, 0) + 1
        if CulturalFrame.ISLAMIC in cultural_votes:
            cultural = CulturalFrame.ISLAMIC
        else:
            cultural = max(cultural_votes, key=cultural_votes.get)

        formality, depth, style = _derive_response_style(best_lang, literacy, last.intent, cultural)

        return UserProfile(
            language=best_lang,
            literacy=literacy,
            intent=last.intent,
            cultural_frame=cultural,
            language_confidence=round(lang_conf, 2),
            literacy_confidence=max_lit.literacy_confidence,
            intent_confidence=last.intent_confidence,
            suggested_formality=formality,
            suggested_depth=depth,
            suggested_style=style,
            detected_signals=[f"turns={len(self._turns)}"] + last.detected_signals,
        )

    @property
    def turn_count(self) -> int:
        return len(self._turns)


# ---------------------------------------------------------------------------
# QUICK SELF-TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    _tests = [
        ("Gimana cara install docker di ubuntu?", Language.INDONESIAN, LiteracyLevel.AWAM),
        ("Assalamualaikum, apa hukum jual beli saham menurut fiqih?", Language.INDONESIAN, LiteracyLevel.MENENGAH),
        ("Analyze the epistemological implications of Bayesian inference in hadith authentication.", Language.ENGLISH, LiteracyLevel.AKADEMIK),
        # Arabic test: use ASCII-safe display
        ("\u0643\u064a\u0641 \u064a\u0645\u0643\u0646\u0646\u064a \u062a\u0639\u0644\u0645 \u0627\u0644\u0644\u063a\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0628\u0633\u0631\u0639\u0629\u061f", Language.ARABIC, LiteracyLevel.MENENGAH),
        ("Help me debug this error in my FastAPI app when calling the endpoint", Language.ENGLISH, LiteracyLevel.AHLI),
    ]

    print("=" * 60)
    print("SIDIX User Intelligence - Quick Test")
    print("=" * 60)

    all_pass = True
    for i, (text, expected_lang, expected_lit) in enumerate(_tests, 1):
        profile = analyze_user(text)
        lang_ok = profile.language == expected_lang
        lit_ok = profile.literacy == expected_lit
        status = "PASS" if (lang_ok and lit_ok) else "WARN"
        if not (lang_ok and lit_ok):
            all_pass = False
        print(f"\n[{status}] Test {i}: {text[:50]}...")
        print(f"  Lang: {profile.language.value} (expected: {expected_lang.value}) {'OK' if lang_ok else 'MISMATCH'}")
        print(f"  Literacy: {profile.literacy.value} (expected: {expected_lit.value}) {'OK' if lit_ok else 'MISMATCH'}")
        print(f"  Intent: {profile.intent.value} ({profile.intent_confidence:.2f})")
        print(f"  Culture: {profile.cultural_frame.value}")
        print(f"  Style: {profile.suggested_formality} / {profile.suggested_depth} / {profile.suggested_style}")

    print("\n" + "=" * 60)
    print(f"Result: {'ALL PASS' if all_pass else 'SOME WARNINGS (check mismatches)'}")
    print("=" * 60)
