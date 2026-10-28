"""
Prompt A/B Variants — Projek Badar Task 78 (G2)
Variasi prompt A/B untuk kualitas estetika.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_AB_LOG_PATH = Path(".data/image_gen/ab_results.jsonl")


@dataclass
class PromptVariant:
    """Representasi satu varian prompt A/B."""

    variant_id: str
    prompt: str
    style_suffix: str
    weight: float = 1.0


class ABVariantGenerator:
    """
    Generator varian prompt untuk A/B testing kualitas estetika.

    Gunakan select_winner() untuk memilih varian terbaik berdasarkan
    skor (misal: user rating atau aesthetic scorer lokal).
    """

    def generate_variants(
        self, base_prompt: str, count: int = 2
    ) -> list[PromptVariant]:
        """
        Buat beberapa varian dari base_prompt.

        - Varian A: high quality, detailed
        - Varian B: artistic, stylized
        - Varian C (bila count > 2): minimalist, clean
        """
        variants: list[PromptVariant] = []

        # Varian A
        suffix_a = "high quality, detailed, sharp focus"
        variants.append(
            PromptVariant(
                variant_id=str(uuid.uuid4()),
                prompt=f"{base_prompt}, {suffix_a}",
                style_suffix=suffix_a,
                weight=1.0,
            )
        )

        # Varian B
        suffix_b = "artistic, stylized, painterly"
        variants.append(
            PromptVariant(
                variant_id=str(uuid.uuid4()),
                prompt=f"{base_prompt}, {suffix_b}",
                style_suffix=suffix_b,
                weight=1.0,
            )
        )

        # Varian C (opsional)
        if count > 2:
            suffix_c = "minimalist, clean, simple composition"
            variants.append(
                PromptVariant(
                    variant_id=str(uuid.uuid4()),
                    prompt=f"{base_prompt}, {suffix_c}",
                    style_suffix=suffix_c,
                    weight=1.0,
                )
            )

        logger.info(
            "Dibuat %d varian prompt untuk base: '%s...'",
            len(variants),
            base_prompt[:40],
        )
        return variants

    def select_winner(
        self, variant_a_score: float, variant_b_score: float
    ) -> str:
        """
        Pilih varian pemenang berdasarkan skor.

        Returns:
            "A" atau "B"
        """
        winner = "A" if variant_a_score >= variant_b_score else "B"
        logger.info(
            "A/B winner: %s (score A=%.3f, B=%.3f)", winner, variant_a_score, variant_b_score
        )
        return winner

    def log_result(
        self, variant_id: str, score: float, data_dir: str = ".data/image_gen"
    ) -> None:
        """
        Catat hasil A/B test ke file JSONL.

        Args:
            variant_id: ID varian yang dinilai.
            score: Skor estetika (0.0 – 1.0, atau skala lain).
            data_dir: Direktori untuk menyimpan ab_results.jsonl.
        """
        log_path = Path(data_dir) / "ab_results.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "variant_id": variant_id,
            "score": score,
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.debug("A/B result dicatat: %s score=%.3f", variant_id, score)
