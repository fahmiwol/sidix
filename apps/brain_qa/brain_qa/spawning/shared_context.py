"""
shared_context.py — Sprint K: Shared Workspace untuk Multi-Agent Spawning

Konsep:
  Shared context = persistent workspace untuk semua sub-agents dalam satu
  spawn session. Tiap agent write output ke workspace; agent berikutnya read.

  Mengadaptasi best practice dari OpenAI Swarm (explicit context management)
  dan production swarm guides (shared workspaces > conversation history).

  Persist ke Hafidz untuk durability dan audit trail.

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("sidix.spawning.context")


# ── Storage ──────────────────────────────────────────────────────────────

SPAWN_ROOT = Path("brain/public/spawning")
SPAWN_ROOT.mkdir(parents=True, exist_ok=True)


# ── Data Structures ──────────────────────────────────────────────────────

@dataclass
class ContextEntry:
    """Single entry in shared context."""
    key: str
    value: dict[str, Any]
    agent_id: str
    agent_type: str
    layer: int
    timestamp: str


@dataclass
class SpawnSession:
    """Complete spawn session state."""
    task_id: str
    goal: str
    status: str = "running"  # running | completed | failed | timeout
    layers: dict[int, list[ContextEntry]] = None
    metadata: dict[str, Any] = None
    created_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if self.layers is None:
            self.layers = {}
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ── SharedContext ────────────────────────────────────────────────────────

class SharedContext:
    """Thread-safe shared workspace untuk multi-agent spawn session.

    Usage:
        ctx = SharedContext("task_001", goal="Buat artikel tentang AI")
        ctx.write("research_output", {"findings": [...]}, agent_id="a1", layer=0)
        findings = ctx.read("research_output")
        layer_0_results = ctx.layer_output(0)
        snapshot = ctx.snapshot()
        ctx.persist_to_hafidz()  # durability
    """

    def __init__(self, task_id: str, goal: str, metadata: Optional[dict] = None):
        self.task_id = task_id
        self.goal = goal
        self._entries: dict[str, ContextEntry] = {}
        self._layer_index: dict[int, list[str]] = {}  # layer → list of keys
        self._lock = threading.RLock()
        self._metadata = metadata or {}
        self._created_at = datetime.now(timezone.utc).isoformat()
        self._status = "running"
        log.debug("[spawning] SharedContext created for task %s", task_id)

    # ── Core Operations ──────────────────────────────────────────────────

    def write(
        self,
        key: str,
        value: dict[str, Any],
        agent_id: str,
        agent_type: str = "unknown",
        layer: int = -1,
    ) -> None:
        """Write an entry to shared context."""
        entry = ContextEntry(
            key=key,
            value=value,
            agent_id=agent_id,
            agent_type=agent_type,
            layer=layer,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._entries[key] = entry
            self._layer_index.setdefault(layer, []).append(key)
        log.debug("[spawning] task=%s agent=%s wrote key=%s layer=%d",
                  self.task_id, agent_id, key, layer)

    def read(self, key: str) -> Optional[dict[str, Any]]:
        """Read an entry by key. Returns dict or None."""
        with self._lock:
            entry = self._entries.get(key)
            return entry.value if entry else None

    def layer_output(self, layer: int) -> list[dict[str, Any]]:
        """Get all outputs from a specific layer."""
        with self._lock:
            keys = self._layer_index.get(layer, [])
            return [self._entries[k].value for k in keys if k in self._entries]

    def all_outputs(self) -> dict[str, dict[str, Any]]:
        """Get all outputs as {key: value}."""
        with self._lock:
            return {k: e.value for k, e in self._entries.items()}

    def snapshot(self) -> dict[str, Any]:
        """Full snapshot of context for synthesis."""
        with self._lock:
            return {
                "task_id": self.task_id,
                "goal": self.goal,
                "status": self._status,
                "created_at": self._created_at,
                "entries": {
                    k: {
                        "value": e.value,
                        "agent_id": e.agent_id,
                        "agent_type": e.agent_type,
                        "layer": e.layer,
                        "timestamp": e.timestamp,
                    }
                    for k, e in self._entries.items()
                },
                "layer_breakdown": {
                    layer: len(keys)
                    for layer, keys in self._layer_index.items()
                },
            }

    # ── Status Management ────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        """Update session status."""
        with self._lock:
            self._status = status
        log.info("[spawning] task=%s status=%s", self.task_id, status)

    def get_status(self) -> str:
        with self._lock:
            return self._status

    # ── Persistence ──────────────────────────────────────────────────────

    def persist(self) -> Path:
        """Persist context snapshot to disk (JSON)."""
        path = SPAWN_ROOT / f"session_{self.task_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = self.snapshot()
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        log.info("[spawning] Persisted task=%s to %s", self.task_id, path)
        return path

    def persist_to_hafidz(self, quality_score: float = 0.0) -> None:
        """Persist final result to Hafidz for long-term memory.

        Args:
            quality_score: composite score for golden/lesson classification
        """
        try:
            from ..hafidz_injector import HafidzInjector
            snapshot = self.snapshot()
            result_text = json.dumps(snapshot, ensure_ascii=False)
            HafidzInjector.store_result(
                query=self.goal,
                answer=result_text,
                sources_used=[],
                sanad_score=quality_score,
                persona="SPAWN",
            )
            log.info("[spawning] task=%s persisted to Hafidz", self.task_id)
        except Exception as e:
            log.warning("[spawning] Hafidz persist failed: %s", e)

    # ── Class Methods ────────────────────────────────────────────────────

    @classmethod
    def load(cls, task_id: str) -> Optional["SharedContext"]:
        """Load a persisted context session."""
        path = SPAWN_ROOT / f"session_{task_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx = cls(task_id=data["task_id"], goal=data["goal"])
            ctx._status = data.get("status", "running")
            ctx._created_at = data.get("created_at", "")
            for key, e in data.get("entries", {}).items():
                ctx.write(
                    key=key,
                    value=e["value"],
                    agent_id=e["agent_id"],
                    agent_type=e["agent_type"],
                    layer=e["layer"],
                )
            return ctx
        except Exception as e:
            log.warning("[spawning] Load failed for %s: %s", task_id, e)
            return None

    @classmethod
    def list_sessions(cls) -> list[str]:
        """List all persisted session IDs."""
        return [
            p.stem.replace("session_", "")
            for p in SPAWN_ROOT.glob("session_*.json")
        ]

    @classmethod
    def cleanup_old(cls, max_age_hours: int = 24) -> int:
        """Remove sessions older than max_age_hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        removed = 0
        for path in SPAWN_ROOT.glob("session_*.json"):
            try:
                stat = path.stat()
                if stat.st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except Exception:
                continue
        log.info("[spawning] Cleaned up %d old sessions", removed)
        return removed
