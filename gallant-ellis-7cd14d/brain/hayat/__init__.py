"""
Hayat — Self-Iterate System (Pilar 5)
generate → evaluate (CQF) → refine (max 3 rounds, target CQF >= 8.0)
"""

from brain.hayat.iteration_engine import (
    HayatIterationEngine,
    RefinementResult,
    DISCLAIMER_PATTERNS,
    QUALITY_KEYWORDS,
)

__all__ = [
    "HayatIterationEngine",
    "RefinementResult",
    "DISCLAIMER_PATTERNS",
    "QUALITY_KEYWORDS",
]
