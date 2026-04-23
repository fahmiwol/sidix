"""
Hayat — Self-Iterate System (Pilar 5)

generate → evaluate (CQF) → refine (max 3 rounds, target CQF ≥ 8.0)
Menjamin kualitas jawaban SIDIX melalui loop perbaikan otomatis.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ── Keyword sets untuk CQF heuristic ─────────────────────────────────────────

# Disclaimer phrases yang menurunkan skor
DISCLAIMER_PATTERNS = re.compile(
    r"\b(tidak bisa|tidak dapat|maaf saya|saya tidak tahu|"
    r"I cannot|I don't know|I'm not sure|as an AI|sebagai AI)\b",
    re.IGNORECASE,
)

# Topic-specific quality keywords
QUALITY_KEYWORDS: dict[str, list[str]] = {
    "agama": ["quran", "hadis", "ulama", "sanad", "dalil", "sunnah", "fiqh", "Allah"],
    "koding": ["def", "function", "class", "return", "import", "example", "code", "error"],
    "kreatif": ["headline", "tagline", "copy", "brand", "target", "pesan", "visual"],
    "etika": ["nilai", "prinsip", "dampak", "perspektif", "konteks", "pertimbangan"],
    "umum": ["karena", "oleh karena itu", "dengan demikian", "contoh", "misalnya"],
    "sidix_internal": ["pilar", "cqf", "aql", "nafs", "corpus", "training", "jiwa"],
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class RefinementResult:
    final_answer: str
    iterations: int
    scores_history: list[float] = field(default_factory=list)
    improved: bool = False
    original_answer: str = ""
    topic: str = "umum"
    total_latency_ms: float = 0.0

    @property
    def final_score(self) -> float:
        return self.scores_history[-1] if self.scores_history else 0.0

    @property
    def score_delta(self) -> float:
        if len(self.scores_history) < 2:
            return 0.0
        return round(self.scores_history[-1] - self.scores_history[0], 2)


# ── HayatIterationEngine ──────────────────────────────────────────────────────

class HayatIterationEngine:
    """
    Self-iteration engine SIDIX.

    Mengambil jawaban awal dan melakukan refinement loop sampai CQF target
    tercapai atau batas iterasi habis.

    Usage:
        hayat = HayatIterationEngine()
        result = hayat.refine(
            question="Apa itu zakat?",
            initial_answer="Zakat adalah ...",
            generate_fn=my_llm_generate,
            topic="agama",
        )
        print(result.final_answer, result.iterations)
    """

    DEFAULT_MAX_ROUNDS = 3
    DEFAULT_TARGET_SCORE = 8.0
    MIN_ANSWER_LENGTH = 50     # karakter minimum untuk jawaban yang diterima

    def __init__(self):
        pass

    # ── Public API ────────────────────────────────────────────────────────────

    def refine(
        self,
        *,
        question: str,
        initial_answer: str,
        generate_fn: Callable[[str], str],
        topic: str = "umum",
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        target_score: float = DEFAULT_TARGET_SCORE,
    ) -> RefinementResult:
        """
        Lakukan refinement loop.

        Args:
            question: pertanyaan user
            initial_answer: jawaban pertama dari NafsOrchestrator
            generate_fn: callable(prompt: str) -> str — fungsi generative model
            topic: topik untuk heuristic scoring
            max_rounds: maksimal iterasi (default 3)
            target_score: skor CQF target (default 8.0)

        Returns:
            RefinementResult dengan jawaban final dan riwayat skor
        """
        t0 = time.monotonic()
        current_answer = initial_answer
        scores: list[float] = []
        improved = False

        # Score initial answer
        initial_score = self._score_answer(question, current_answer, topic)
        scores.append(initial_score)

        logger.debug(
            "Hayat: initial score %.2f (target %.1f, topic=%s)",
            initial_score, target_score, topic,
        )

        # Already good enough — skip refinement
        if initial_score >= target_score:
            return RefinementResult(
                final_answer=current_answer,
                iterations=0,
                scores_history=scores,
                improved=False,
                original_answer=initial_answer,
                topic=topic,
                total_latency_ms=(time.monotonic() - t0) * 1000,
            )

        # Refinement loop
        for round_num in range(1, max_rounds + 1):
            try:
                prompt = self._build_refinement_prompt(
                    question, current_answer, scores[-1], topic
                )
                refined = generate_fn(prompt)

                if not refined or len(refined.strip()) < self.MIN_ANSWER_LENGTH:
                    logger.debug("Hayat: round %d returned empty/short answer, stopping", round_num)
                    break

                refined = refined.strip()
                new_score = self._score_answer(question, refined, topic)
                scores.append(new_score)

                logger.debug("Hayat: round %d score %.2f → %.2f", round_num, scores[-2], new_score)

                # Accept refinement only if score improved
                if new_score > scores[-2]:
                    current_answer = refined
                    improved = True

                if new_score >= target_score:
                    logger.debug("Hayat: target %.1f reached at round %d", target_score, round_num)
                    break

            except Exception as e:
                logger.warning("Hayat: round %d generate_fn failed: %s — using previous", round_num, e)
                break

        return RefinementResult(
            final_answer=current_answer,
            iterations=len(scores) - 1,
            scores_history=scores,
            improved=improved,
            original_answer=initial_answer,
            topic=topic,
            total_latency_ms=(time.monotonic() - t0) * 1000,
        )

    # ── CQF Heuristic Scoring ─────────────────────────────────────────────────

    def _score_answer(self, question: str, answer: str, topic: str) -> float:
        """
        Heuristic CQF score (0.0–10.0) berdasarkan:
        1. Panjang jawaban (0–3 poin)
        2. Keyword coverage untuk topik (0–4 poin)
        3. Tidak ada disclaimer (0–2 poin)
        4. Kualitas struktur (0–1 poin)

        Total maks: 10.0
        """
        score = 0.0

        # 1. Panjang jawaban
        length = len(answer.strip())
        if length >= 500:
            score += 3.0
        elif length >= 200:
            score += 2.0
        elif length >= 100:
            score += 1.5
        elif length >= 50:
            score += 0.8
        else:
            score += 0.2

        # 2. Keyword coverage
        keywords = QUALITY_KEYWORDS.get(topic, QUALITY_KEYWORDS["umum"])
        answer_lower = answer.lower()
        found = sum(1 for kw in keywords if kw.lower() in answer_lower)
        keyword_score = min(4.0, (found / max(len(keywords), 1)) * 4.0)
        score += keyword_score

        # 3. Disclaimer check (makin banyak disclaimer → skor turun)
        disclaimer_matches = len(DISCLAIMER_PATTERNS.findall(answer))
        if disclaimer_matches == 0:
            score += 2.0
        elif disclaimer_matches == 1:
            score += 1.0
        else:
            score += 0.0  # banyak disclaimer = kurang percaya diri

        # 4. Struktur: ada paragraf / poin / contoh
        has_structure = bool(
            re.search(r"\n{2,}|\d+\.\s|[-*]\s|:\n|\bcontoh\b|\bmisal\b", answer, re.IGNORECASE)
        )
        if has_structure:
            score += 1.0

        return round(min(10.0, max(0.0, score)), 2)

    # ── Refinement Prompt ─────────────────────────────────────────────────────

    def _build_refinement_prompt(
        self,
        question: str,
        answer: str,
        score: float,
        topic: str,
    ) -> str:
        """
        Bangun prompt untuk model agar memperbaiki jawaban.
        """
        gap = 8.0 - score
        severity = (
            "sangat perlu ditingkatkan" if score < 5.0
            else "perlu perbaikan" if score < 6.5
            else "perlu sedikit penyempurnaan"
        )

        topic_hint = ""
        if topic == "agama":
            topic_hint = "Sertakan dalil (Quran/Hadis) dan pendapat ulama jika relevan."
        elif topic == "koding":
            topic_hint = "Sertakan contoh kode yang konkret dan penjelasan error/solusi."
        elif topic == "kreatif":
            topic_hint = "Jadikan lebih persuasif, kuat secara pesan, dan jelas target audiensnya."
        elif topic == "etika":
            topic_hint = "Berikan perspektif dari berbagai sisi, berimbang dan tidak satu dimensi."

        return (
            f"Pertanyaan: {question}\n\n"
            f"Jawaban sebelumnya (skor {score:.1f}/10, {severity}, perlu +{gap:.1f}):\n"
            f"{answer}\n\n"
            f"Tugas: Perbaiki jawaban di atas agar lebih lengkap, akurat, dan informatif. "
            f"{topic_hint} "
            f"Berikan jawaban yang lebih baik tanpa memulai dengan disclaimer atau permintaan maaf. "
            f"Langsung jawab pertanyaannya."
        )
