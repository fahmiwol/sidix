"""
Policy Filter — Projek Badar Task 74 (G2)
Filter keluaran gambar (NSFW/policy) + logging redaksi.
Stub: menggunakan keyword denylist. Produksi: ganti dengan classifier.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .models import PolicyViolation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Denylist & warn list
# ---------------------------------------------------------------------------

DENIED_KEYWORDS: list[str] = [
    # NSFW / explicit content
    "nude", "naked", "nsfw", "explicit", "pornographic", "xxx",
    "sexual", "genitalia", "erotic",
    # Kekerasan ekstrem
    "gore", "torture", "mutilation", "decapitation", "snuff",
    # Ujaran kebencian
    "hate speech", "racist slur", "ethnic cleansing",
    # Ilegal
    "child abuse", "csam", "drug synthesis", "bomb making",
]

WARNED_KEYWORDS: list[str] = [
    "violence", "blood", "weapon", "gun", "knife", "death",
    "war", "conflict", "injury", "disturbing",
]

_POLICY_LOG_PATH = Path(".data/image_gen/policy_log.jsonl")


class PolicyFilter:
    """
    Filter prompt berbasis keyword denylist.

    Untuk produksi: ganti check_prompt() dengan pemanggilan ke
    classifier lokal (misal: Detoxify, LlamaGuard via lokal inference).
    """

    def check_prompt(self, prompt: str) -> PolicyViolation:
        """
        Periksa prompt terhadap DENIED_KEYWORDS dan WARNED_KEYWORDS.
        Kembalikan PolicyViolation berisi hasil pemeriksaan.
        """
        lower = prompt.lower()
        violated_cats: list[str] = []
        reasons: list[str] = []

        for kw in DENIED_KEYWORDS:
            if kw in lower:
                violated_cats.append(kw)
                reasons.append(f"Kata terlarang terdeteksi: '{kw}'")

        if violated_cats:
            return PolicyViolation(
                violated=True,
                reason="; ".join(reasons),
                categories=violated_cats,
            )

        warned_cats: list[str] = []
        for kw in WARNED_KEYWORDS:
            if kw in lower:
                warned_cats.append(kw)

        if warned_cats:
            logger.warning(
                "Prompt mengandung kata berpotensi sensitif: %s", warned_cats
            )

        return PolicyViolation(violated=False, reason="", categories=warned_cats)

    def log_redaction(
        self, prompt: str, violation: PolicyViolation, user_id: str
    ) -> None:
        """
        Catat redaksi ke file .data/image_gen/policy_log.jsonl.
        Dibuat bila belum ada.
        """
        _POLICY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "prompt_preview": prompt[:120],  # jangan simpan seluruh prompt
            "violated": violation.violated,
            "reason": violation.reason,
            "categories": violation.categories,
        }
        with _POLICY_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("Redaksi dicatat untuk user=%s", user_id)

    def is_output_safe(self, image_path: str) -> bool:
        """
        Periksa apakah output gambar aman.

        TODO: integrasikan classifier NSFW lokal (misal: NudeNet, SafetyChecker
              dari diffusers) untuk memeriksa gambar hasil.
        Saat ini selalu mengembalikan True (stub).
        """
        # STUB — TODO: load local NSFW classifier and run inference on image_path
        logger.debug(
            "is_output_safe() stub: asumsikan aman untuk %s", image_path
        )
        return True
