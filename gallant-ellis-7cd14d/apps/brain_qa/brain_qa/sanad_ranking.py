"""Sanad-tier weights for corpus retrieval reranking (Sprint 1 T1.2)."""

from __future__ import annotations

# Epistemic priority: primary sources and scholarly chain > aggregators.
SANAD_WEIGHTS: dict[str, float] = {
    "primer": 1.5,
    "ulama": 1.3,
    "peer_review": 1.2,
    "aggregator": 0.9,
    "unknown": 1.0,
}

_ALLOWED = frozenset(SANAD_WEIGHTS.keys())


def normalize_sanad_tier(val: str | None) -> str:
    if val is None or not isinstance(val, str):
        return "unknown"
    v = val.strip().lower().replace("-", "_")
    if v in _ALLOWED:
        return v
    return "unknown"


def apply_sanad_weight(sanad_tier: str, base_score: float) -> float:
    """BM25 (or similar) score multiplied by tier weight."""
    tier = normalize_sanad_tier(sanad_tier)
    w = SANAD_WEIGHTS.get(tier, 1.0)
    return float(base_score) * w


def extract_sanad_tier_from_markdown(raw: str) -> str:
    """Parse YAML frontmatter for `sanad_tier:` (first --- block only)."""
    raw_l = raw.lstrip("\ufeff")
    if not raw_l.startswith("---"):
        return "unknown"
    parts = raw_l.split("---", 2)
    if len(parts) < 2:
        return "unknown"
    fm = parts[1]
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("sanad_tier"):
            if ":" not in line:
                continue
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            return normalize_sanad_tier(val)
    return "unknown"
