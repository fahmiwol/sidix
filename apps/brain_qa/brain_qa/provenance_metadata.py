"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

provenance_metadata.py — Sprint 47B (Hafidz Ledger schema extension)

Inspired by Majlis SIDIX Knowledge River metadata schema (Lapis 1, © 2026
Fahmi Ghani — see Majelis sidix/ docs). Adopt schema convention, BUKAN
full Majlis implement. Backward compatible — uses existing
hafidz_ledger.LedgerEntry.metadata dict, NO new database fields needed.

Standard provenance fields encoded into metadata dict:
  - trust_score:        float [0.0 - 1.0]
  - abstraction_level:  int [1 - 5]
  - source_type:        enum (agent_feed | user_input | owner_manual |
                              owner_proactive | sidix_autonomous)
  - status:             enum (raw | processed | quarantine | available |
                              consumed | archived)
  - domain_tags:        list[str]
  - urgency:            enum (low | medium | high | critical)

Default trust scores per source (per Majlis Lapis 1 spec):
  agent_feed:        0.7
  user_input:        0.5
  owner_manual:      1.0
  owner_proactive:   0.9
  sidix_autonomous:  0.6

Reference: Majelis sidix/ARCHITECTURE.md Lapis 1 Knowledge River.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


# ── Standard enums ───────────────────────────────────────────────────────────

VALID_SOURCE_TYPES = (
    "agent_feed",       # 1000-agent ecosystem feeds
    "user_input",       # External user contributions via API
    "owner_manual",     # Direct owner injection (highest trust)
    "owner_proactive",  # Owner-curated cron/scheduled
    "sidix_autonomous", # Self-discovery (SIDIX-detected patterns)
)

DEFAULT_TRUST_SCORES = {
    "agent_feed":       0.7,
    "user_input":       0.5,
    "owner_manual":     1.0,
    "owner_proactive":  0.9,
    "sidix_autonomous": 0.6,
}

VALID_STATUSES = (
    "raw",         # ingested, not yet processed
    "processed",   # parsed + structured
    "quarantine",  # awaits validation
    "available",   # available for downstream consumption
    "consumed",    # used by downstream processor
    "archived",    # historical, low-priority retrieval
)

VALID_URGENCIES = ("low", "medium", "high", "critical")


# ── Metadata builder ─────────────────────────────────────────────────────────

@dataclass
class ProvenanceMeta:
    """Standard provenance fields. Encoded as flat dict via to_dict()."""
    trust_score: float = 0.5
    abstraction_level: int = 3
    source_type: str = "sidix_autonomous"
    status: str = "available"
    domain_tags: list[str] = None
    urgency: str = "medium"

    def __post_init__(self):
        if self.domain_tags is None:
            self.domain_tags = []
        # Validate
        if not 0.0 <= self.trust_score <= 1.0:
            raise ValueError(f"trust_score {self.trust_score} out of [0,1]")
        if not 1 <= self.abstraction_level <= 5:
            raise ValueError(f"abstraction_level {self.abstraction_level} out of [1,5]")
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type {self.source_type!r} invalid")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status {self.status!r} invalid")
        if self.urgency not in VALID_URGENCIES:
            raise ValueError(f"urgency {self.urgency!r} invalid")

    def to_dict(self) -> dict:
        """Serialize to flat dict suitable for hafidz_ledger metadata field."""
        return {
            "trust_score": self.trust_score,
            "abstraction_level": self.abstraction_level,
            "source_type": self.source_type,
            "status": self.status,
            "domain_tags": list(self.domain_tags),
            "urgency": self.urgency,
            "schema_version": "provenance_meta_v1",
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProvenanceMeta":
        """Reconstruct from dict (e.g., loaded from ledger)."""
        return cls(
            trust_score=float(d.get("trust_score", 0.5)),
            abstraction_level=int(d.get("abstraction_level", 3)),
            source_type=str(d.get("source_type", "sidix_autonomous")),
            status=str(d.get("status", "available")),
            domain_tags=list(d.get("domain_tags", [])),
            urgency=str(d.get("urgency", "medium")),
        )


# ── Convenience constructors ─────────────────────────────────────────────────

def for_owner_manual(abstraction_level: int = 3,
                     domain_tags: Optional[list[str]] = None) -> ProvenanceMeta:
    """Build ProvenanceMeta for owner-injected content (highest trust)."""
    return ProvenanceMeta(
        trust_score=DEFAULT_TRUST_SCORES["owner_manual"],
        abstraction_level=abstraction_level,
        source_type="owner_manual",
        status="available",
        domain_tags=domain_tags or [],
        urgency="medium",
    )


def for_sidix_autonomous(abstraction_level: int = 3,
                         domain_tags: Optional[list[str]] = None,
                         status: str = "quarantine") -> ProvenanceMeta:
    """Build ProvenanceMeta for SIDIX self-discovery (default quarantine)."""
    return ProvenanceMeta(
        trust_score=DEFAULT_TRUST_SCORES["sidix_autonomous"],
        abstraction_level=abstraction_level,
        source_type="sidix_autonomous",
        status=status,
        domain_tags=domain_tags or [],
        urgency="medium",
    )


def for_user_input(abstraction_level: int = 2,
                   domain_tags: Optional[list[str]] = None) -> ProvenanceMeta:
    """Build ProvenanceMeta for external user content (lower default trust)."""
    return ProvenanceMeta(
        trust_score=DEFAULT_TRUST_SCORES["user_input"],
        abstraction_level=abstraction_level,
        source_type="user_input",
        status="quarantine",
        domain_tags=domain_tags or [],
        urgency="medium",
    )


def for_owner_proactive(abstraction_level: int = 3,
                        domain_tags: Optional[list[str]] = None) -> ProvenanceMeta:
    """Build ProvenanceMeta for owner-curated cron/scheduled content."""
    return ProvenanceMeta(
        trust_score=DEFAULT_TRUST_SCORES["owner_proactive"],
        abstraction_level=abstraction_level,
        source_type="owner_proactive",
        status="available",
        domain_tags=domain_tags or [],
        urgency="medium",
    )


def for_agent_feed(abstraction_level: int = 2,
                   domain_tags: Optional[list[str]] = None) -> ProvenanceMeta:
    """Build ProvenanceMeta for 1000-agent feed content."""
    return ProvenanceMeta(
        trust_score=DEFAULT_TRUST_SCORES["agent_feed"],
        abstraction_level=abstraction_level,
        source_type="agent_feed",
        status="available",
        domain_tags=domain_tags or [],
        urgency="medium",
    )


# ── Hafidz Ledger integration helpers ────────────────────────────────────────

def write_with_provenance(content: str, content_id: str, content_type: str,
                          provenance: ProvenanceMeta,
                          isnad_chain: Optional[list[str]] = None,
                          extra_metadata: Optional[dict] = None,
                          cycle_id: str = ""):
    """Convenience wrapper: write to Hafidz Ledger dengan standard provenance.

    Returns LedgerEntry. Backward compatible: uses metadata dict, no schema
    change to LedgerEntry dataclass.
    """
    from .hafidz_ledger import write_entry
    metadata = provenance.to_dict()
    if extra_metadata:
        metadata.update(extra_metadata)
    return write_entry(
        content=content,
        content_id=content_id,
        content_type=content_type,
        isnad_chain=isnad_chain or [],
        metadata=metadata,
        cycle_id=cycle_id,
    )


def parse_provenance(metadata: dict) -> Optional[ProvenanceMeta]:
    """Extract ProvenanceMeta from a ledger entry's metadata dict.

    Returns None if entry has no provenance schema (older entries).
    """
    if not metadata:
        return None
    if metadata.get("schema_version") != "provenance_meta_v1":
        # Try best-effort parse anyway if fields present
        if all(k in metadata for k in ("trust_score", "source_type")):
            try:
                return ProvenanceMeta.from_dict(metadata)
            except (ValueError, TypeError):
                return None
        return None
    return ProvenanceMeta.from_dict(metadata)


__all__ = [
    "ProvenanceMeta",
    "VALID_SOURCE_TYPES", "DEFAULT_TRUST_SCORES",
    "VALID_STATUSES", "VALID_URGENCIES",
    "for_owner_manual", "for_sidix_autonomous", "for_user_input",
    "for_owner_proactive", "for_agent_feed",
    "write_with_provenance", "parse_provenance",
]
