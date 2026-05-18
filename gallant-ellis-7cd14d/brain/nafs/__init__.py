"""
Nafs — Self-Respond System (Pilar 1)
3-layer knowledge fusion: parametric + dynamic + static.
"""

from brain.nafs.response_orchestrator import (
    NafsOrchestrator,
    NafsResponse,
    LayerResult,
    PERSONAS,
    TOPIC_PATTERNS,
)

__all__ = [
    "NafsOrchestrator",
    "NafsResponse",
    "LayerResult",
    "PERSONAS",
    "TOPIC_PATTERNS",
]
