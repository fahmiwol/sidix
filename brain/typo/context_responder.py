"""
Layer 4: Context-Aware Responder
Generate response prefix/suffix based on confidence tier.

PRINSIP UTAMA: JANGAN PERNAH mempermalukan user karena typo.
Koreksi dilakukan diam-diam. Kalau perlu mention, lakukan dengan empati.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from brain.typo.confidence_scorer import ConfidenceResult


# ---------------------------------------------------------------------------
# Intent → topic label mapping (untuk template)
# ---------------------------------------------------------------------------
INTENT_TOPIC_LABELS: dict[str, str] = {
    "setup_gpu": "konfigurasi GPU / training",
    "install_plugin": "instalasi plugin",
    "deploy_request": "deployment / server",
    "debug_request": "debugging / error",
    "maqashid_explain": "Maqashid Syariah",
    "naskh_explain": "Naskh dalam Ushul Fiqh",
    "raudah_explain": "sistem multi-agent Raudah",
    "sanad_explain": "Sanad / rantai periwayatan",
    "creative_request": "pembuatan konten kreatif",
    "brand_request": "branding / identitas merek",
    "campaign_request": "strategi kampanye",
    "code_request": "penulisan kode",
    "research_request": "riset / pencarian informasi",
    "analysis_request": "analisis data / kompetitor",
    "learn_request": "penjelasan / tutorial",
    "greeting": "salam pembuka",
    "farewell": "penutup percakapan",
    "feedback_positive": "apresiasi",
    "feedback_negative": "koreksi / masukan",
    "general_question": "pertanyaan umum",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class ResponseContext:
    prefix: str
    suffix: str
    normalized_question: str
    should_correct: bool
    correction_note: str
    action: str
    intent: str
    topic_label: str = ""
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ContextResponder
# ---------------------------------------------------------------------------
class ContextResponder:
    """
    Layer 4 — siapkan konteks respons berdasarkan confidence tier.
    Output ini dipakai pipeline untuk wrap jawaban SIDIX.
    """

    def prepare_context(
        self,
        confidence_result: ConfidenceResult,
        normalized_text: str,
        corrections: list[str],
    ) -> ResponseContext:
        """
        Siapkan prefix, suffix, dan metadata untuk respons.

        Parameters
        ----------
        confidence_result : ConfidenceResult
            Output dari ConfidenceScorer.
        normalized_text : str
            Teks yang sudah di-normalize (Layer 1).
        corrections : list[str]
            Daftar koreksi yang diterapkan (format "typo→benar").

        Returns
        -------
        ResponseContext
        """
        action = confidence_result.action
        intent = confidence_result.intent
        topic = INTENT_TOPIC_LABELS.get(intent, "topik ini")

        prefix = self._build_prefix(action, topic, normalized_text)
        suffix = self._build_suffix(action, corrections)
        should_correct = action in ("respond_with_note", "respond_with_disclaimer")
        correction_note = self._build_correction_note(corrections) if should_correct else ""

        return ResponseContext(
            prefix=prefix,
            suffix=suffix,
            normalized_question=normalized_text,
            should_correct=should_correct,
            correction_note=correction_note,
            action=action,
            intent=intent,
            topic_label=topic,
            metadata={
                "combined_score": confidence_result.combined_score,
                "norm_confidence": confidence_result.norm_confidence,
                "intent_confidence": confidence_result.intent_confidence,
                "n_corrections": confidence_result.norm_corrections,
            },
        )

    # ------------------------------------------------------------------
    # Private builders
    # ------------------------------------------------------------------
    @staticmethod
    def _build_prefix(action: str, topic: str, normalized_text: str) -> str:
        """Buat prefix respons sesuai action tier."""
        if action == "respond_directly":
            # Tidak ada prefix — SIDIX langsung menjawab
            return ""

        elif action == "respond_with_note":
            return f"Saya pahami kamu bertanya tentang {topic}. Berikut penjelasannya:"

        elif action == "respond_with_disclaimer":
            # Potong pertanyaan yang sudah dinormalisasi untuk preview
            preview = (normalized_text[:60] + "…") if len(normalized_text) > 60 else normalized_text
            return (
                f"Kalau saya tidak salah tangkap, kamu menanyakan tentang {topic}: "
                f'"{preview}". Tolong koreksi kalau saya keliru ya.'
            )

        elif action == "ask_clarification":
            return (
                "Bisa diperjelas sedikit? Saya ingin memastikan saya membantu dengan tepat 😊 "
                "Pertanyaan kamu bisa diulang dengan kata-kata yang berbeda?"
            )

        return ""

    @staticmethod
    def _build_suffix(action: str, corrections: list[str]) -> str:
        """Buat suffix kecil kalau relevan."""
        if action == "respond_directly":
            return ""
        # Untuk tier lain, tidak ada suffix khusus (cukup prefix)
        return ""

    @staticmethod
    def _build_correction_note(corrections: list[str]) -> str:
        """Format koreksi menjadi catatan singkat yang tidak menghakimi."""
        if not corrections:
            return ""
        # Ambil maks 3 koreksi paling signifikan (bukan levenshtein minor)
        clean = [c for c in corrections if "lev" not in c]
        if not clean:
            clean = corrections
        sample = clean[:3]
        pairs = [f'"{c.split("→")[0]}" → "{c.split("→")[1]}"' for c in sample if "→" in c]
        if not pairs:
            return ""
        return "(Catatan internal: " + ", ".join(pairs) + ")"

    @staticmethod
    def _sanitize(text: str) -> str:
        """Bersihkan teks dari karakter aneh."""
        return re.sub(r"[^\w\s\.,!?;:\-'\"()]", "", text).strip()
