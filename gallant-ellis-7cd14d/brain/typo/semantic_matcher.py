"""
Layer 2: Semantic Matcher
Intent detection via pattern matching + cosine similarity (manual implementation).
Tidak butuh library eksternal — hanya stdlib Python.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# INTENT PATTERNS — 20 intent dengan keywords
# ---------------------------------------------------------------------------
INTENT_PATTERNS: dict[str, list[str]] = {
    # Teknis / infra
    "setup_gpu": [
        "gpu", "cuda", "nvidia", "vram", "training", "latih", "finetune", "fine-tune",
        "lora", "qlora", "akselerasi", "accelerate", "tensorboard", "grafis",
    ],
    "install_plugin": [
        "install", "pasang", "setup", "konfigurasi", "integrasi", "plugin",
        "ekstensi", "extension", "addon", "mcp", "sdk",
    ],
    "deploy_request": [
        "deploy", "production", "prod", "server", "vps", "hosting",
        "pm2", "nginx", "ssl", "domain", "launch", "rilis", "live",
    ],
    "debug_request": [
        "error", "bug", "crash", "gagal", "tidak bisa", "tidak jalan",
        "masalah", "problem", "issue", "exception", "traceback", "fix",
    ],
    # Islamik
    "maqashid_explain": [
        "maqashid", "maqasid", "tujuan syariah", "daruriyyat", "hajiyyat",
        "tahsiniyyat", "hifzh", "nafs", "aql", "nasab", "mal", "din",
    ],
    "naskh_explain": [
        "naskh", "nasikh", "mansukh", "abrogasi", "penghapusan hukum",
        "ushul fiqh", "usul", "qiyas", "ijma", "ijtihad",
    ],
    "raudah_explain": [
        "raudah", "multi-agent", "orkestrator", "orchestrate", "kolaborasi agent",
        "task graph", "dag", "pipeline kompleks", "workflow",
    ],
    "sanad_explain": [
        "sanad", "silsilah", "rantai periwayatan", "hadits", "rawi",
        "isnad", "matan", "rijal", "jarh", "ta'dil",
    ],
    # Kreatif
    "creative_request": [
        "buatkan", "buat", "tulis", "caption", "copywriting", "iklan",
        "konten", "content", "kreatif", "creative", "slogan", "tagline",
        "marketing", "branding", "campaign", "promosi", "poster",
    ],
    "brand_request": [
        "brand", "merek", "identitas", "logo", "visual", "tone of voice",
        "brand guidelines", "brand identity", "positioning", "diferensiasi",
    ],
    "campaign_request": [
        "kampanye", "campaign", "strategi", "strategy", "funnel",
        "awareness", "engagement", "konversi", "conversion", "ads", "iklan",
    ],
    # Coding
    "code_request": [
        "kode", "code", "script", "program", "fungsi", "function",
        "class", "api", "endpoint", "backend", "frontend", "database",
        "query", "algoritma", "algorithm", "python", "javascript",
    ],
    # Riset / Analisis
    "research_request": [
        "riset", "research", "cari", "temukan", "find", "investigasi",
        "telusuri", "studi", "study", "literatur", "referensi", "sumber",
    ],
    "analysis_request": [
        "analisis", "analisa", "analyze", "evaluasi", "evaluate", "bandingkan",
        "compare", "kompetitor", "competitor", "tren", "trend", "insight",
        "statistik", "data", "laporan", "report",
    ],
    # Edukasi
    "learn_request": [
        "ajarkan", "jelaskan", "explain", "bagaimana", "how to", "cara",
        "tutorial", "panduan", "guide", "pelajari", "belajar", "learn",
        "apa itu", "what is", "definisi", "pengertian",
    ],
    # Social
    "greeting": [
        "halo", "hai", "hello", "hi", "selamat pagi", "selamat siang",
        "selamat malam", "assalamualaikum", "salam", "good morning", "good evening",
    ],
    "farewell": [
        "bye", "dadah", "sampai jumpa", "wassalam", "dah", "terima kasih",
        "makasih", "thanks", "thank you", "selesai", "cukup", "done",
    ],
    "feedback_positive": [
        "bagus", "keren", "mantap", "bermanfaat", "helpful", "suka",
        "good", "great", "awesome", "perfect", "tepat", "benar",
    ],
    "feedback_negative": [
        "salah", "keliru", "kurang", "tidak tepat", "wrong", "incorrect",
        "buruk", "jelek", "tidak sesuai", "perbaiki", "revisi",
    ],
    # Misc
    "general_question": [
        "apa", "siapa", "kapan", "dimana", "mengapa", "kenapa",
        "apakah", "bisakah", "bolehkah", "tolong", "minta",
    ],
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class IntentResult:
    intent: str
    confidence: float
    matched_pattern: list[str] = field(default_factory=list)
    alternatives: list[tuple[str, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SemanticMatcher
# ---------------------------------------------------------------------------
class SemanticMatcher:
    """
    Layer 2 — deteksi intent dari teks yang sudah di-normalize.
    Gunakan pattern matching dahulu, cosine similarity sebagai fallback.
    """

    def __init__(self, patterns: dict[str, list[str]] | None = None) -> None:
        self._patterns = patterns if patterns is not None else INTENT_PATTERNS
        # Build vocabulary dari semua pattern words
        self._vocab: dict[str, int] = {}
        self._intent_vectors: dict[str, list[float]] = {}
        self._build_index()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def match_intent(self, text: str) -> IntentResult:
        """Deteksi intent dari text. Return IntentResult dengan confidence."""
        text_lower = text.lower()
        words = re.findall(r"[\w]+", text_lower)

        # --- Fase 1: Pattern matching langsung ---
        pattern_scores: dict[str, tuple[float, list[str]]] = {}
        for intent, keywords in self._patterns.items():
            matched: list[str] = []
            for kw in keywords:
                if kw in text_lower:
                    matched.append(kw)
            if matched:
                # score = ratio keywords matched * boost untuk multi-match
                score = len(matched) / len(keywords) + min(len(matched) * 0.05, 0.2)
                score = min(score, 1.0)
                pattern_scores[intent] = (score, matched)

        if pattern_scores:
            best_intent = max(pattern_scores, key=lambda k: pattern_scores[k][0])
            best_score, matched_kws = pattern_scores[best_intent]

            alternatives = [
                (intent, round(score, 4))
                for intent, (score, _) in sorted(
                    pattern_scores.items(), key=lambda x: x[1][0], reverse=True
                )
                if intent != best_intent
            ][:3]

            return IntentResult(
                intent=best_intent,
                confidence=round(min(best_score, 1.0), 4),
                matched_pattern=matched_kws,
                alternatives=alternatives,
            )

        # --- Fase 2: Cosine similarity fallback ---
        text_vec = self._text_to_vector(text_lower)
        best_intent = "general_question"
        best_sim = 0.0
        alt_sims: list[tuple[str, float]] = []

        for intent, intent_vec in self._intent_vectors.items():
            sim = self._compute_similarity(text_vec, intent_vec)
            alt_sims.append((intent, round(sim, 4)))
            if sim > best_sim:
                best_sim = sim
                best_intent = intent

        alt_sims.sort(key=lambda x: x[1], reverse=True)
        # Kalau similarity sangat rendah, fallback ke general_question
        if best_sim < 0.05:
            best_intent = "general_question"
            best_sim = 0.3  # baseline confidence

        return IntentResult(
            intent=best_intent,
            confidence=round(min(best_sim + 0.1, 1.0), 4),  # slight bump untuk cosine path
            matched_pattern=[],
            alternatives=[t for t in alt_sims if t[0] != best_intent][:3],
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------
    def _build_index(self) -> None:
        """Build vocabulary dan intent vectors dari INTENT_PATTERNS."""
        # Kumpulkan semua kata unik
        all_words: set[str] = set()
        for keywords in self._patterns.values():
            for kw in keywords:
                for w in kw.split():
                    all_words.add(w)

        self._vocab = {w: i for i, w in enumerate(sorted(all_words))}
        vocab_size = len(self._vocab)

        # Build TF vector per intent
        for intent, keywords in self._patterns.items():
            vec = [0.0] * vocab_size
            for kw in keywords:
                for w in kw.split():
                    idx = self._vocab.get(w)
                    if idx is not None:
                        vec[idx] += 1.0
            # Normalize
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            self._intent_vectors[intent] = vec

    def _text_to_vector(self, text: str) -> list[float]:
        """Simple bag-of-words TF vector. No library needed."""
        vocab_size = len(self._vocab)
        vec = [0.0] * vocab_size
        words = re.findall(r"[\w]+", text)
        for w in words:
            idx = self._vocab.get(w)
            if idx is not None:
                vec[idx] += 1.0
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    @staticmethod
    def _compute_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Cosine similarity manual (bukan library). Asumsi kedua vector sudah ternormalisasi."""
        if len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        # Sudah ternormalisasi → cosine = dot product
        return max(0.0, min(1.0, dot))
