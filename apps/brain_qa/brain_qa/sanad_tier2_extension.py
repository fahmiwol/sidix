"""
sanad_tier2_extension.py — Sprint Anti-Halu Tier-2

Extend sanad multi-source verifier dengan:
1. Numerical claim verification — extract angka dari LLM answer, cross-check
   apakah angka itu muncul di multiple sources. Kalau cuma 1 sumber atau
   conflict antar sumber, flag sebagai "[ANGKA TIDAK TERVERIFIKASI]".

2. Date claim verification — sama untuk tahun/tanggal.

3. Quote attribution — kalau answer pakai "menurut X bilang...", verify bahwa
   X memang muncul di context multi-source.

Pattern compound atas Sigma-1 Anti-Halu (sanad_verifier.py existing).
Tier-2 fokus pada precision verification, bukan brand canon override.

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ClaimVerification:
    claim_type: str  # "number" | "date" | "quote_attribution"
    claim_text: str
    verified: bool
    sources_supporting: int
    confidence: str  # "tinggi" | "sedang" | "rendah"


# Patterns
_NUMBER_RE = re.compile(r"\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+\.\d+|\d+)\s*(juta|miliar|trilliun|billion|million|trillion|persen|%|km|kg|tahun|year)?\b", re.IGNORECASE)
_DATE_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_QUOTE_ATTR_RE = re.compile(r"menurut\s+([A-Z][a-zA-Z\s]+?)(?:[\,\.]|$)|kata\s+([A-Z][a-zA-Z\s]+?)(?:[\,\.]|$)|berdasarkan\s+([A-Z][a-zA-Z\s]+?)(?:[\,\.]|$)", re.IGNORECASE)


def verify_numerical_claims(
    answer: str,
    sources_text: list[str],
    min_sources_required: int = 2,
) -> list[ClaimVerification]:
    """Extract numbers from answer, check kalau muncul di sources juga.

    Args:
        answer: LLM synthesis output
        sources_text: list of raw text dari multiple sources (web/corpus/dll)
        min_sources_required: minimum sources yang harus mention angka

    Returns: list of ClaimVerification per number found.
    """
    if not answer or not sources_text:
        return []

    # Extract unique numbers from answer
    numbers_in_answer = set()
    for m in _NUMBER_RE.finditer(answer):
        num_str = m.group(1).replace(",", "").replace(".", "")
        if num_str.isdigit() and len(num_str) >= 2:  # ignore 1-digit
            numbers_in_answer.add(m.group(0).strip())

    verifications = []
    combined_sources = " ".join(sources_text).lower()

    for num in numbers_in_answer:
        # Count appearances in source text (case-insensitive)
        appearances = combined_sources.count(num.lower())
        verified = appearances >= min_sources_required
        confidence = "tinggi" if appearances >= 3 else ("sedang" if appearances >= 1 else "rendah")
        verifications.append(ClaimVerification(
            claim_type="number",
            claim_text=num,
            verified=verified,
            sources_supporting=appearances,
            confidence=confidence,
        ))

    return verifications


def verify_date_claims(
    answer: str,
    sources_text: list[str],
) -> list[ClaimVerification]:
    """Verify year claims (1900-2099) di answer vs sources."""
    if not answer or not sources_text:
        return []

    years_in_answer = set(_DATE_YEAR_RE.findall(answer))
    combined_sources = " ".join(sources_text)

    verifications = []
    for year in years_in_answer:
        appearances = combined_sources.count(year)
        verified = appearances >= 1  # minimal 1 source mention
        confidence = "tinggi" if appearances >= 2 else ("sedang" if appearances == 1 else "rendah")
        verifications.append(ClaimVerification(
            claim_type="date",
            claim_text=year,
            verified=verified,
            sources_supporting=appearances,
            confidence=confidence,
        ))

    return verifications


def verify_quote_attributions(
    answer: str,
    sources_text: list[str],
) -> list[ClaimVerification]:
    """Verify 'menurut X' attribution — pastikan X muncul di sources."""
    if not answer or not sources_text:
        return []

    combined_sources = " ".join(sources_text).lower()

    verifications = []
    for m in _QUOTE_ATTR_RE.finditer(answer):
        # Get the captured name (one of 3 groups)
        name = next((g for g in m.groups() if g), "").strip()
        if not name or len(name) < 3:
            continue
        appearances = combined_sources.count(name.lower())
        verified = appearances >= 1
        confidence = "tinggi" if appearances >= 2 else ("sedang" if appearances == 1 else "rendah")
        verifications.append(ClaimVerification(
            claim_type="quote_attribution",
            claim_text=name,
            verified=verified,
            sources_supporting=appearances,
            confidence=confidence,
        ))

    return verifications


@dataclass
class Tier2VerificationResult:
    overall_score: float  # 0.0 - 1.0
    numerical_claims: list[ClaimVerification]
    date_claims: list[ClaimVerification]
    quote_attributions: list[ClaimVerification]
    flagged_unverified: list[str]
    summary: str


def verify_tier2(answer: str, sources_text: list[str]) -> Tier2VerificationResult:
    """Run all Tier-2 verifications + return aggregate result."""
    nums = verify_numerical_claims(answer, sources_text)
    dates = verify_date_claims(answer, sources_text)
    quotes = verify_quote_attributions(answer, sources_text)

    all_claims = nums + dates + quotes
    if not all_claims:
        return Tier2VerificationResult(
            overall_score=1.0,
            numerical_claims=[],
            date_claims=[],
            quote_attributions=[],
            flagged_unverified=[],
            summary="No verifiable claims detected (text-only answer)",
        )

    verified_count = sum(1 for c in all_claims if c.verified)
    score = verified_count / len(all_claims)

    flagged = [
        f"{c.claim_type}:{c.claim_text}"
        for c in all_claims
        if not c.verified
    ]

    summary = (
        f"Tier-2 verification: {verified_count}/{len(all_claims)} claims verified "
        f"({len(nums)} numbers, {len(dates)} dates, {len(quotes)} quotes). "
        f"Unverified: {len(flagged)}"
    )

    return Tier2VerificationResult(
        overall_score=score,
        numerical_claims=nums,
        date_claims=dates,
        quote_attributions=quotes,
        flagged_unverified=flagged,
        summary=summary,
    )


__all__ = [
    "ClaimVerification",
    "Tier2VerificationResult",
    "verify_numerical_claims",
    "verify_date_claims",
    "verify_quote_attributions",
    "verify_tier2",
]
