"""
Prompt Validation — Projek Badar Task 82 (G2)
Validasi prompt melanggar kebijakan sebelum render.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from .policy_filter import PolicyFilter, DENIED_KEYWORDS, WARNED_KEYWORDS

logger = logging.getLogger(__name__)

_MIN_PROMPT_LENGTH = 5
_MAX_PROMPT_LENGTH = 1000

_policy_filter = PolicyFilter()


@dataclass
class ValidationResult:
    """Hasil validasi prompt sebelum render."""

    valid: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sanitized_prompt: str = ""


def validate_prompt(prompt: str) -> ValidationResult:
    """
    Validasi prompt sebelum dikirim ke pipeline render.

    Pemeriksaan:
    1. Panjang minimum (5 karakter).
    2. Panjang maksimum (1000 karakter, truncate).
    3. Policy violations (keyword denylist via PolicyFilter).
    4. Sanitasi: strip whitespace berlebih, truncate.

    Returns:
        ValidationResult berisi status valid, pelanggaran, peringatan,
        dan prompt yang sudah disanitasi.
    """
    violations: list[str] = []
    warnings: list[str] = []

    # 1. Sanitasi awal: strip whitespace
    sanitized = re.sub(r"\s+", " ", prompt.strip())

    # 2. Cek panjang minimum
    if len(sanitized) < _MIN_PROMPT_LENGTH:
        violations.append(
            f"Prompt terlalu pendek (minimum {_MIN_PROMPT_LENGTH} karakter, "
            f"diberikan {len(sanitized)})."
        )

    # 3. Truncate bila terlalu panjang
    if len(sanitized) > _MAX_PROMPT_LENGTH:
        warnings.append(
            f"Prompt dipotong dari {len(sanitized)} ke {_MAX_PROMPT_LENGTH} karakter."
        )
        sanitized = sanitized[:_MAX_PROMPT_LENGTH]

    # 4. Cek policy violations
    violation = _policy_filter.check_prompt(sanitized)
    if violation.violated:
        violations.extend(
            [f"Policy violation: {violation.reason}"]
            + [f"Kategori terlarang: {cat}" for cat in violation.categories]
        )
    elif violation.categories:
        # Warned keywords
        warnings.extend(
            [f"Kata sensitif terdeteksi: '{kw}'" for kw in violation.categories]
        )

    is_valid = len(violations) == 0

    if not is_valid:
        logger.warning(
            "Prompt gagal validasi: %d pelanggaran. Preview: '%s...'",
            len(violations),
            sanitized[:40],
        )
    elif warnings:
        logger.info(
            "Prompt valid dengan %d peringatan. Preview: '%s...'",
            len(warnings),
            sanitized[:40],
        )

    return ValidationResult(
        valid=is_valid,
        violations=violations,
        warnings=warnings,
        sanitized_prompt=sanitized if is_valid else "",
    )
