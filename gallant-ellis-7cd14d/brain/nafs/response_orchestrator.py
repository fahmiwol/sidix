"""
Nafs — Self-Respond System (Pilar 1)

3-layer knowledge fusion:
  PARAMETRIC  60%  — LLM/LoRA weights, general reasoning
  DYNAMIC     30%  — Knowledge Graph (runtime-learned facts)
  STATIC      10%  — frozen corpus (sanad-verified documents)

Topic routing → layer activation → weighted fusion → confidence check.
"""

from __future__ import annotations

import re
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── Topic categories ─────────────────────────────────────────────────────────

TOPIC_PATTERNS: dict[str, re.Pattern] = {
    "sidix_internal": re.compile(
        r"\b(sidix|ihos|maqashid|nafs|jiwa|pilar|aql|qalb|ruh|hayat|ilm|"
        r"hikmah|sanad|naskh|raudah|persona|ayman|aboo|oomar|aley|utz|"
        r"sprint|cqf|lora|brain_qa|social.?radar|jariyah|tafsir)\b",
        re.IGNORECASE,
    ),
    "agama": re.compile(
        r"\b(quran|al.?quran|hadis|hadith|sunnah|nabi|rasul|ulama|fiqh|"
        r"syariah|syariat|halal|haram|fatwa|sholat|zakat|puasa|haji|"
        r"umrah|wudhu|tauhid|aqidah|iman|islam|muslim|doa|dzikir)\b",
        re.IGNORECASE,
    ),
    "etika": re.compile(
        r"\b(etika|moral|boleh|tidak boleh|baik|buruk|benar|salah|adil|"
        r"zalim|amanah|jujur|bohong|fitnah|ghibah|riba|zina|korupsi|suap)\b",
        re.IGNORECASE,
    ),
    "koding": re.compile(
        r"\b(code|kode|coding|programming|debug|bug|error|exception|"
        r"python|javascript|typescript|node|react|fastapi|sql|"
        r"function|class|method|api|endpoint|deploy|git|docker|"
        r"syntax|runtime|compile|test|pytest|jest)\b",
        re.IGNORECASE,
    ),
    "kreatif": re.compile(
        r"\b(copy|copywriting|iklan|ads|campaign|konten|content|"
        r"desain|design|brand|branding|tagline|headline|caption|story|"
        r"instagram|threads|tiktok|youtube|postingan|post|viral)\b",
        re.IGNORECASE,
    ),
    "ngobrol": re.compile(
        r"\b(halo|hai|hi|hello|selamat|apa kabar|gimana|bagaimana kamu|"
        r"cerita dong|ngobrol|curhat|kamu siapa|siapa kamu|kenalin|"
        r"kamu bisa|bisa nggak|apa yang kamu|lo tau)\b",
        re.IGNORECASE,
    ),
}

_SUBSTANTIVE = re.compile(
    r"\b(vs|versus|apa|jelaskan|bandingkan|cara|tulis|buat|cek|kenapa|mengapa|bagaimana)\b",
    re.IGNORECASE,
)

# ── Persona definitions ───────────────────────────────────────────────────────

PERSONAS: dict[str, dict] = {
    "AYMAN": {
        "karakter": "visioner yang bijak dan tenang",
        "rasa": "penuh hormat, hangat, tegas",
        "gaya": "pakai analogi, kutip tradisi ilmu, reflektif",
        "maqashid_mode": "IJTIHAD",
    },
    "ABOO": {
        "karakter": "analis data yang presisi dan logis",
        "rasa": "objektif, curious, semi-akademis",
        "gaya": "struktur argumen, data, sebab-akibat",
        "maqashid_mode": "ACADEMIC",
    },
    "OOMAR": {
        "karakter": "engineer solutif yang hands-on",
        "rasa": "to-the-point, pragmatis",
        "gaya": "langsung ke kode/teknis, contoh konkret",
        "maqashid_mode": "IJTIHAD",
    },
    "ALEY": {
        "karakter": "guru yang sabar dan merangkul",
        "rasa": "hangat, supportif",
        "gaya": "analogi sederhana, step-by-step",
        "maqashid_mode": "GENERAL",
    },
    "UTZ": {
        "karakter": "teman ngobrol serba bisa",
        "rasa": "relatable, ringan, genuine",
        "gaya": "natural seperti teman",
        "maqashid_mode": "CREATIVE",
    },
}

_PERSONA_ALIAS = {
    "MIGHAN": "AYMAN", "TOARD": "ABOO", "FACH": "OOMAR",
    "HAYFAR": "ALEY", "INAN": "UTZ",
}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class LayerResult:
    content: str
    confidence: float
    source: str  # "parametric" | "dynamic" | "static"
    latency_ms: float = 0.0


@dataclass
class NafsResponse:
    answer: str
    topic: str
    persona: str
    confidence: float
    layers_used: list[str] = field(default_factory=list)
    parametric_weight: float = 0.6
    dynamic_weight: float = 0.3
    static_weight: float = 0.1
    latency_ms: float = 0.0
    skip_corpus: bool = False
    hayat_enabled: bool = True


# ── NafsOrchestrator ─────────────────────────────────────────────────────────

class NafsOrchestrator:
    """
    Orchestrates 3-layer knowledge fusion per request.

    Usage:
        nafs = NafsOrchestrator(
            parametric_fn=lambda q, p: llm_generate(q, p),
            dynamic_fn=lambda q: kg_query(q),
            static_fn=lambda q: corpus_search(q),
        )
        result = nafs.respond(question="...", persona="UTZ")
    """

    def __init__(
        self,
        parametric_fn: Optional[Callable[[str, str], str]] = None,
        dynamic_fn: Optional[Callable[[str], str]] = None,
        static_fn: Optional[Callable[[str], str]] = None,
    ):
        self.parametric_fn = parametric_fn or self._stub_parametric
        self.dynamic_fn = dynamic_fn or self._stub_dynamic
        self.static_fn = static_fn or self._stub_static

    # ── Public API ────────────────────────────────────────────────────────────

    def respond(
        self,
        question: str,
        persona: str = "UTZ",
        *,
        corpus_only: bool = False,
    ) -> NafsResponse:
        t0 = time.monotonic()
        topic = self._detect_topic(question)
        weights = self._get_weights(topic, corpus_only)
        persona_key = _PERSONA_ALIAS.get(persona.upper(), persona.upper())
        p_data = PERSONAS.get(persona_key, PERSONAS["UTZ"])

        layers: list[LayerResult] = []
        used: list[str] = []

        if weights["parametric"] > 0:
            lr = self._call_layer("parametric", question, persona_key, self.parametric_fn)
            layers.append(lr); used.append("parametric")

        if weights["dynamic"] > 0:
            lr = self._call_layer("dynamic", question, persona_key, self.dynamic_fn)
            if lr.content:
                layers.append(lr); used.append("dynamic")

        if weights["static"] > 0:
            lr = self._call_layer("static", question, persona_key, self.static_fn)
            if lr.content:
                layers.append(lr); used.append("static")

        answer, conf = self._fuse(layers, weights)
        answer = self._inject_persona(answer, p_data, topic)

        return NafsResponse(
            answer=answer,
            topic=topic,
            persona=persona_key,
            confidence=conf,
            layers_used=used,
            parametric_weight=weights["parametric"],
            dynamic_weight=weights["dynamic"],
            static_weight=weights["static"],
            latency_ms=(time.monotonic() - t0) * 1000,
            skip_corpus=(topic in {"ngobrol", "koding"}),
            hayat_enabled=(topic not in {"ngobrol"}),
        )

    # ── Topic detection ───────────────────────────────────────────────────────

    def _detect_topic(self, question: str) -> str:
        q = question.strip()
        for topic, pattern in TOPIC_PATTERNS.items():
            if topic == "ngobrol":
                continue
            if pattern.search(q):
                return topic
        if TOPIC_PATTERNS["ngobrol"].search(q):
            return "ngobrol"
        if len(q) < 25 and not _SUBSTANTIVE.search(q):
            return "ngobrol"
        return "umum"

    # ── Weight matrix ─────────────────────────────────────────────────────────

    def _get_weights(self, topic: str, corpus_only: bool) -> dict[str, float]:
        if corpus_only:
            return {"parametric": 0.0, "dynamic": 0.3, "static": 0.7}
        matrix = {
            "ngobrol":        {"parametric": 1.0,  "dynamic": 0.0,  "static": 0.0},
            "umum":           {"parametric": 0.6,  "dynamic": 0.3,  "static": 0.1},
            "kreatif":        {"parametric": 0.7,  "dynamic": 0.2,  "static": 0.1},
            "koding":         {"parametric": 0.8,  "dynamic": 0.2,  "static": 0.0},
            "sidix_internal": {"parametric": 0.2,  "dynamic": 0.5,  "static": 0.3},
            "agama":          {"parametric": 0.3,  "dynamic": 0.2,  "static": 0.5},
            "etika":          {"parametric": 0.4,  "dynamic": 0.3,  "static": 0.3},
        }
        return matrix.get(topic, matrix["umum"])

    # ── Layer runners ─────────────────────────────────────────────────────────

    def _call_layer(
        self,
        source: str,
        question: str,
        persona: str,
        fn: Callable,
    ) -> LayerResult:
        t0 = time.monotonic()
        try:
            if source == "parametric":
                content = fn(question, persona)
            else:
                content = fn(question)
            content = content or ""
        except Exception as e:
            logger.warning("Nafs layer %s failed: %s", source, e)
            content = ""
        return LayerResult(
            content=content,
            confidence=0.9 if content else 0.0,
            source=source,
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    # ── Fusion ────────────────────────────────────────────────────────────────

    def _fuse(
        self,
        layers: list[LayerResult],
        weights: dict[str, float],
    ) -> tuple[str, float]:
        if not layers:
            return "Maaf, saya tidak dapat menghasilkan jawaban saat ini.", 0.0

        # If only one layer, return as-is
        if len(layers) == 1:
            return layers[0].content, layers[0].confidence

        # Primary = highest-weight parametric; supplement with others
        primary = next((l for l in layers if l.source == "parametric"), layers[0])
        supplements = [l for l in layers if l.source != "parametric" and l.content]

        answer = primary.content
        if supplements:
            context = "\n\n".join(
                f"[Referensi {l.source}]: {l.content[:300]}"
                for l in supplements
            )
            answer = f"{answer}\n\n---\n{context}"

        total_weight = sum(weights[l.source] for l in layers if l.source in weights)
        conf = sum(
            weights.get(l.source, 0) * l.confidence for l in layers
        ) / (total_weight or 1.0)

        return answer, round(conf, 3)

    # ── Persona injection ─────────────────────────────────────────────────────

    def _inject_persona(self, answer: str, persona_data: dict, topic: str) -> str:
        if topic == "ngobrol":
            return answer
        return answer

    # ── Stubs (replaced by real implementations) ─────────────────────────────

    @staticmethod
    def _stub_parametric(question: str, persona: str) -> str:
        return f"[PARAMETRIC] Jawaban untuk: {question[:60]}"

    @staticmethod
    def _stub_dynamic(question: str) -> str:
        return ""

    @staticmethod
    def _stub_static(question: str) -> str:
        return ""
