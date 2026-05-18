"""
hafidz_ledger.py — Sprint 37 Hafidz Ledger MVP

Provenance trail audit-able untuk lesson + skill yang lahir dari evolusi
diri agent (Sprint 36 reflection cycle, Sprint 38 tool synthesis, dll).

Filosofi (note 141 + 248 + 276): Sanad sebagai SPIRIT validator + chain
of provenance untuk evolusi internal SIDIX. Bukan religious adoption,
tapi METODE governance.

MVP scope:
- SHA-256 cas_hash dari canonical content
- isnad_chain (parent refs) tracking provenance
- Append-only JSONL store di .data/hafidz_ledger.jsonl
- Stateless functions, thread-safe append

Phase 4 future:
- Full Merkle tree
- Reed-Solomon erasure shares (4-of-5 recovery)
- Distributed P2P sync

Reference:
- research note 141 (Hafidz spec full)
- research note 248 (canonical pivot, sanad METODE)
- research note 276 (sanad SPIRIT validator multi-dimensi)
- research note 282 (synthesis adoption — Sprint 37 priority 18/20)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


_LEDGER_FILE = "/opt/sidix/.data/hafidz_ledger.jsonl"
_LOCK = threading.Lock()


@dataclass
class LedgerEntry:
    """One immutable provenance entry for a piece of content."""
    cas_hash: str  # SHA-256 of canonical content (PK)
    content_id: str  # human-readable id (e.g., "lesson-2026-04-27")
    content_type: str  # "lesson" | "skill" | "research_note" | "decision"
    isnad_chain: list[str] = field(default_factory=list)  # parent content_id refs
    tabayyun_quality_gate: Optional[bool] = None  # validation pass/fail
    owner_verdict: str = "pending"  # "pending" | "approved" | "rejected"
    sources: list[str] = field(default_factory=list)  # url/file paths source
    metadata: dict = field(default_factory=dict)  # extensible
    created_at: str = ""  # ISO timestamp UTC
    cycle_id: str = ""  # which cycle/sprint produced this


def compute_cas_hash(content: str) -> str:
    """Compute SHA-256 dari canonical content (deterministic).

    Strip leading/trailing whitespace + normalize line endings supaya
    hash sama untuk content equivalent.
    """
    if not isinstance(content, (str, bytes)):
        content = str(content)
    if isinstance(content, str):
        # Normalize: strip + LF line endings only
        normalized = content.strip().replace("\r\n", "\n").replace("\r", "\n")
        content_bytes = normalized.encode("utf-8")
    else:
        content_bytes = content
    return hashlib.sha256(content_bytes).hexdigest()


def _ensure_ledger_dir():
    """Ensure parent dir exists for ledger file."""
    p = Path(_LEDGER_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)


def write_entry(
    content: str,
    content_id: str,
    content_type: str,
    *,
    isnad_chain: Optional[list[str]] = None,
    tabayyun_quality_gate: Optional[bool] = None,
    owner_verdict: str = "pending",
    sources: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
    cycle_id: str = "",
) -> LedgerEntry:
    """Write a new ledger entry (append-only). Returns the entry.

    Thread-safe append via lock. Hash deterministic — kalau same content_id
    + same content append twice, the entry hashes will match (dedup hint).
    """
    from datetime import datetime, timezone

    cas_hash = compute_cas_hash(content)
    entry = LedgerEntry(
        cas_hash=cas_hash,
        content_id=content_id,
        content_type=content_type,
        isnad_chain=isnad_chain or [],
        tabayyun_quality_gate=tabayyun_quality_gate,
        owner_verdict=owner_verdict,
        sources=sources or [],
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat(),
        cycle_id=cycle_id,
    )

    _ensure_ledger_dir()
    with _LOCK:
        with open(_LEDGER_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    log.info(
        "[hafidz] entry written: id=%s type=%s hash=%s...",
        content_id, content_type, cas_hash[:12],
    )
    return entry


def read_entry_by_id(content_id: str) -> Optional[LedgerEntry]:
    """Find latest entry by content_id (last write wins kalau ada multiple)."""
    p = Path(_LEDGER_FILE)
    if not p.exists():
        return None
    found = None
    with _LOCK:
        with open(_LEDGER_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("content_id") == content_id:
                        found = LedgerEntry(**data)
                except Exception:
                    continue
    return found


def read_entry_by_hash(cas_hash: str) -> Optional[LedgerEntry]:
    """Find entry by SHA-256 cas_hash."""
    p = Path(_LEDGER_FILE)
    if not p.exists():
        return None
    with _LOCK:
        with open(_LEDGER_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("cas_hash") == cas_hash:
                        return LedgerEntry(**data)
                except Exception:
                    continue
    return None


def trace_isnad(content_id: str, max_depth: int = 10) -> list[LedgerEntry]:
    """Walk isnad_chain backwards. Return list of ancestor entries.

    Stops at max_depth atau saat parent tidak ditemukan.
    """
    chain: list[LedgerEntry] = []
    seen = set()
    current_id = content_id
    while current_id and len(chain) < max_depth:
        if current_id in seen:
            log.warning("[hafidz] isnad cycle detected at %s", current_id)
            break
        seen.add(current_id)
        entry = read_entry_by_id(current_id)
        if not entry:
            break
        chain.append(entry)
        # Pick first parent dari isnad_chain (kalau multiple, baru handle Phase 4)
        if entry.isnad_chain:
            current_id = entry.isnad_chain[0]
        else:
            break
    return chain


def update_owner_verdict(content_id: str, verdict: str, rejection_reason: str = "") -> bool:
    """Append a NEW entry dengan updated verdict (append-only, no mutation).

    Pattern: untuk update verdict, write entry baru dengan content_id sama
    + isnad_chain yang reference entry sebelumnya. Last entry wins di lookup.

    Returns True kalau write sukses.
    """
    if verdict not in ("pending", "approved", "rejected"):
        log.warning("[hafidz] invalid verdict: %s", verdict)
        return False
    existing = read_entry_by_id(content_id)
    if not existing:
        log.warning("[hafidz] content_id not found: %s", content_id)
        return False
    # Compose: same content reference, new metadata for update
    update_content = f"verdict_update:{content_id}:{verdict}"
    if rejection_reason:
        update_content += f":{rejection_reason}"
    new_entry = write_entry(
        content=update_content,
        content_id=content_id,
        content_type=f"{existing.content_type}_verdict",
        isnad_chain=[existing.cas_hash],
        owner_verdict=verdict,
        metadata={"rejection_reason": rejection_reason} if rejection_reason else {},
        cycle_id=f"verdict-update-{int(time.time())}",
    )
    return True


def list_recent_entries(limit: int = 20) -> list[LedgerEntry]:
    """Return last N entries (newest first) dari ledger."""
    p = Path(_LEDGER_FILE)
    if not p.exists():
        return []
    entries: list[LedgerEntry] = []
    with _LOCK:
        with open(_LEDGER_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entries.append(LedgerEntry(**data))
                except Exception:
                    continue
    return entries[-limit:][::-1]  # newest first


def stats() -> dict:
    """Quick stats for /audit endpoint health check."""
    p = Path(_LEDGER_FILE)
    if not p.exists():
        return {"total_entries": 0, "ledger_path": _LEDGER_FILE, "exists": False}
    count = 0
    types = {}
    verdicts = {}
    with _LOCK:
        with open(_LEDGER_FILE, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                count += 1
                try:
                    data = json.loads(line.strip())
                    types[data.get("content_type", "?")] = types.get(data.get("content_type", "?"), 0) + 1
                    verdicts[data.get("owner_verdict", "?")] = verdicts.get(data.get("owner_verdict", "?"), 0) + 1
                except Exception:
                    continue
    return {
        "total_entries": count,
        "by_type": types,
        "by_verdict": verdicts,
        "ledger_path": _LEDGER_FILE,
        "exists": True,
    }


__all__ = [
    "LedgerEntry",
    "compute_cas_hash",
    "write_entry",
    "read_entry_by_id",
    "read_entry_by_hash",
    "trace_isnad",
    "update_owner_verdict",
    "list_recent_entries",
    "stats",
]
