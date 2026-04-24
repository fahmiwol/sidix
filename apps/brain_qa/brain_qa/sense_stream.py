"""
sense_stream.py — Active Sense Streaming

Event bus untuk sense inputs yang aktif secara real-time.
Setiap sense menghasilkan SenseEvent, ReAct loop subscribe ke stream.

Fitur:
- Auto-timeout: events older than 30s discarded
- Deduplication: identical text dari text+STT di-merge
- Thread-safe: multiple senses bisa emit events bersamaan

Jiwa Sprint 3 Fase D (Kimi)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Constants ────────────────────────────────────────────────────────────────

_DEFAULT_TIMEOUT_SEC = 30.0
_DEDUP_WINDOW_SEC = 5.0


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SenseEvent:
    """Satu event dari satu sense."""
    source: str           # text | vision | audio | emotional | sensor_hub
    data: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"evt-{time.time():.6f}")


# ── Stream ───────────────────────────────────────────────────────────────────

class SenseStream:
    """Thread-safe event bus untuk sense inputs."""

    def __init__(self, timeout_sec: float = _DEFAULT_TIMEOUT_SEC):
        self.timeout_sec = timeout_sec
        self._events: list[SenseEvent] = []
        self._lock = threading.Lock()
        self._subscribers: list[callable] = []
        self._sub_lock = threading.Lock()

    def emit(self, event: SenseEvent) -> None:
        """Emit satu event ke stream. Thread-safe."""
        with self._lock:
            self._events.append(event)
            self._deduplicate_recent()
            self._prune_old()

        # Notify subscribers (outside lock to avoid deadlock)
        with self._sub_lock:
            subs = list(self._subscribers)
        for cb in subs:
            try:
                cb(event)
            except Exception:
                pass

    def emit_quick(self, source: str, data: str, confidence: float = 1.0, **meta: Any) -> None:
        """Convenience: emit tanpa bikin SenseEvent manual."""
        self.emit(SenseEvent(source=source, data=data, confidence=confidence, metadata=meta))

    def get_events(
        self,
        source: str | None = None,
        since: float = 0.0,
    ) -> list[SenseEvent]:
        """Get events, optionally filtered by source and time."""
        with self._lock:
            self._prune_old()
            result = [
                e for e in self._events
                if (source is None or e.source == source)
                and e.timestamp >= since
            ]
            return list(result)

    def get_latest(self, source: str | None = None) -> SenseEvent | None:
        """Get event terbaru, optionally filtered by source."""
        events = self.get_events(source=source)
        return events[-1] if events else None

    def snapshot(self) -> dict[str, Any]:
        """Snapshot semua events untuk debug/dashboard."""
        with self._lock:
            self._prune_old()
            return {
                "event_count": len(self._events),
                "sources": list({e.source for e in self._events}),
                "events": [
                    {
                        "source": e.source,
                        "data": e.data[:100],
                        "confidence": e.confidence,
                        "age_sec": round(time.time() - e.timestamp, 2),
                    }
                    for e in self._events
                ],
            }

    def clear(self) -> None:
        """Clear semua events."""
        with self._lock:
            self._events = []

    def subscribe(self, callback: callable) -> None:
        """Subscribe ke stream — callback dipanggil setiap emit."""
        with self._sub_lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: callable) -> None:
        """Unsubscribe dari stream."""
        with self._sub_lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _prune_old(self) -> None:
        """Remove events older than timeout_sec. Must hold _lock."""
        cutoff = time.time() - self.timeout_sec
        self._events = [e for e in self._events if e.timestamp >= cutoff]

    def _deduplicate_recent(self) -> None:
        """Merge identical text inputs from different sources in dedup window. Must hold _lock."""
        cutoff = time.time() - _DEDUP_WINDOW_SEC
        recent = [e for e in self._events if e.timestamp >= cutoff]
        # Group by normalized data
        by_data: dict[str, list[SenseEvent]] = {}
        for e in recent:
            key = e.data.strip().lower()
            by_data.setdefault(key, []).append(e)

        # For each group with multiple sources, keep highest confidence + merge sources
        merged: list[SenseEvent] = []
        for key, group in by_data.items():
            if len(group) > 1 and len({e.source for e in group}) > 1:
                best = max(group, key=lambda e: e.confidence)
                sources = ", ".join({e.source for e in group})
                best.metadata["dedup_sources"] = sources
                best.metadata["dedup_count"] = len(group)
                merged.append(best)
            else:
                merged.extend(group)

        # Replace recent events with merged, keep old events
        old = [e for e in self._events if e.timestamp < cutoff]
        self._events = old + merged


# ── Singleton convenience ────────────────────────────────────────────────────

_default_stream: SenseStream | None = None
_stream_lock = threading.Lock()


def get_sense_stream() -> SenseStream:
    global _default_stream
    with _stream_lock:
        if _default_stream is None:
            _default_stream = SenseStream()
        return _default_stream


def emit_sense_event(source: str, data: str, confidence: float = 1.0, **meta: Any) -> None:
    get_sense_stream().emit_quick(source, data, confidence, **meta)


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Sense Stream Self-Test ===\n")

    stream = SenseStream(timeout_sec=10.0)

    # Test 1: emit + get
    stream.emit_quick("text", "Halo SIDIX")
    events = stream.get_events()
    assert len(events) == 1
    assert events[0].source == "text"
    print("[1] Emit + get: OK\n")

    # Test 2: filter by source
    stream.emit_quick("vision", "Gambar kucing")
    text_events = stream.get_events(source="text")
    assert len(text_events) == 1
    assert text_events[0].data == "Halo SIDIX"
    print("[2] Filter by source: OK\n")

    # Test 3: get latest
    latest = stream.get_latest()
    assert latest.source == "vision"
    print("[3] Get latest: OK\n")

    # Test 4: deduplication
    stream.emit_quick("text", "Halo SIDIX")
    stream.emit_quick("audio", "Halo SIDIX")  # identical text, different source
    all_events = stream.get_events()
    # Should be deduplicated — count halo events
    halo_events = [e for e in all_events if e.data.strip().lower() == "halo sidix"]
    assert len(halo_events) == 1
    assert "audio" in halo_events[0].metadata.get("dedup_sources", "")
    print("[4] Deduplication: OK\n")

    # Test 5: subscribe
    received = []
    def handler(evt):
        received.append(evt.source)
    stream.subscribe(handler)
    stream.emit_quick("emotional", "User senang")
    assert "emotional" in received
    stream.unsubscribe(handler)
    print("[5] Subscribe/unsubscribe: OK\n")

    # Test 6: snapshot
    snap = stream.snapshot()
    assert snap["event_count"] > 0
    assert "sources" in snap
    print("[6] Snapshot: OK\n")

    # Test 7: clear
    stream.clear()
    assert len(stream.get_events()) == 0
    print("[7] Clear: OK\n")

    print("[OK] All self-tests passed")
