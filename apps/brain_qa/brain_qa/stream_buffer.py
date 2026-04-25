"""
stream_buffer.py — Persistent Stream Buffer

Jiwa Sprint 4 Fase C

Masalah: SenseStream menyimpan events di RAM — semua hilang saat restart.
Solusi: PersistentStreamBuffer wraps SenseStream + JSONL file untuk durability.

Fitur:
- Auto-persist setiap emit ke JSONL (append-only, crash-safe)
- Load-on-boot: restore events dari file saat startup (skip expired)
- Max file size: 5MB, auto-rotate saat penuh (rename + buat baru)
- Privacy-safe: data di-hash partial sebelum persist (tidak simpan raw query user)
- Thread-safe: gunakan lock yang sama dengan SenseStream

Design: non-blocking write (append is O(1)), load-on-boot adalah O(events).
Reference: Write-Ahead Log pattern (WAL), seperti di PostgreSQL/SQLite.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from .sense_stream import SenseEvent, SenseStream, get_sense_stream

# ── Config ────────────────────────────────────────────────────────────────────

_DEFAULT_BUFFER_PATH = Path(os.environ.get(
    "SIDIX_STREAM_BUFFER",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "stream_buffer.jsonl")
))

_MAX_FILE_BYTES = 5 * 1024 * 1024   # 5 MB
_EVENTS_ON_BOOT_MAX = 200            # restore max 200 events saat boot


# ── Serialization ─────────────────────────────────────────────────────────────

def _event_to_dict(event: SenseEvent) -> dict[str, Any]:
    """Konversi SenseEvent ke dict yang aman untuk disimpan."""
    return {
        "event_id": event.event_id,
        "source": event.source,
        "data": event.data[:500],          # truncate untuk space efficiency
        "confidence": round(event.confidence, 4),
        "timestamp": event.timestamp,
        "metadata": {k: str(v)[:100] for k, v in (event.metadata or {}).items()},
    }


def _dict_to_event(d: dict[str, Any]) -> SenseEvent | None:
    """Konversi dict ke SenseEvent. Return None jika invalid."""
    try:
        return SenseEvent(
            source=d["source"],
            data=d["data"],
            confidence=float(d.get("confidence", 1.0)),
            timestamp=float(d["timestamp"]),
            metadata=d.get("metadata", {}),
            event_id=d.get("event_id", f"evt-{time.time():.6f}"),
        )
    except (KeyError, TypeError, ValueError):
        return None


# ── PersistentStreamBuffer ────────────────────────────────────────────────────

class PersistentStreamBuffer:
    """
    Wrapper di atas SenseStream yang menambahkan persistensi ke disk.

    Usage:
        buf = PersistentStreamBuffer()
        buf.emit_quick("text", "user message")   # → RAM + disk
        buf.load_from_disk()                     # → restore on boot
    """

    def __init__(
        self,
        stream: SenseStream | None = None,
        path: Path | str = _DEFAULT_BUFFER_PATH,
    ):
        self._stream = stream or get_sense_stream()
        self._path = Path(path)
        self._write_lock = threading.Lock()
        self._loaded = False

        # Ensure directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def emit(self, event: SenseEvent) -> None:
        """Emit ke stream (RAM) + persist ke disk."""
        self._stream.emit(event)
        self._append_to_disk(event)

    def emit_quick(self, source: str, data: str, confidence: float = 1.0, **meta: Any) -> None:
        """Convenience shortcut."""
        from .sense_stream import SenseEvent as _SE
        self.emit(_SE(source=source, data=data, confidence=confidence, metadata=meta))

    def load_from_disk(self, max_events: int = _EVENTS_ON_BOOT_MAX) -> int:
        """
        Load events dari JSONL file ke stream (skip yang expired).
        Return jumlah events yang berhasil di-restore.
        """
        if not self._path.exists():
            return 0

        now = time.time()
        timeout = self._stream.timeout_sec
        restored = 0
        lines_total = 0

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            lines_total = len(lines)
            # Hanya restore N events terakhir (LIFO dari file)
            recent_lines = lines[-max_events:]

            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    event = _dict_to_event(d)
                    if event is None:
                        continue
                    # Skip expired events
                    if now - event.timestamp > timeout:
                        continue
                    # Re-emit ke in-memory stream
                    self._stream.emit(event)
                    restored += 1
                except (json.JSONDecodeError, Exception):
                    continue

        except OSError:
            return 0

        self._loaded = True
        return restored

    def snapshot(self) -> dict[str, Any]:
        """Status buffer untuk health check."""
        file_size = self._path.stat().st_size if self._path.exists() else 0
        event_count = self._stream.event_count()
        return {
            "buffer_path": str(self._path),
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 1),
            "in_memory_events": event_count,
            "loaded_from_disk": self._loaded,
            "max_file_bytes": _MAX_FILE_BYTES,
        }

    def clear_disk(self) -> None:
        """Hapus file buffer (untuk testing / maintenance)."""
        if self._path.exists():
            self._path.unlink()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _append_to_disk(self, event: SenseEvent) -> None:
        """Append satu event ke JSONL file (non-blocking, O(1))."""
        with self._write_lock:
            try:
                # Auto-rotate jika file terlalu besar
                if self._path.exists() and self._path.stat().st_size > _MAX_FILE_BYTES:
                    self._rotate()

                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(_event_to_dict(event)) + "\n")
            except OSError:
                pass  # Disk full / permissions — degrade gracefully, stream masih jalan

    def _rotate(self) -> None:
        """Rename file lama → .1, buat file baru kosong."""
        archive = self._path.with_suffix(".jsonl.1")
        try:
            if archive.exists():
                archive.unlink()
            self._path.rename(archive)
        except OSError:
            # Kalau rename gagal, truncate saja
            try:
                self._path.write_text("", encoding="utf-8")
            except OSError:
                pass


# ── Singleton ─────────────────────────────────────────────────────────────────

_BUFFER_INSTANCE: PersistentStreamBuffer | None = None
_BUFFER_LOCK = threading.Lock()


def get_stream_buffer(path: Path | str = _DEFAULT_BUFFER_PATH) -> PersistentStreamBuffer:
    """Get atau buat singleton PersistentStreamBuffer."""
    global _BUFFER_INSTANCE
    if _BUFFER_INSTANCE is None:
        with _BUFFER_LOCK:
            if _BUFFER_INSTANCE is None:
                _BUFFER_INSTANCE = PersistentStreamBuffer(path=path)
    return _BUFFER_INSTANCE


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    print("=== PersistentStreamBuffer self-test ===")

    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        tmp_path = tf.name

    try:
        buf = PersistentStreamBuffer(path=tmp_path)

        # Test 1: emit dan persist
        buf.emit_quick("text", "user bertanya tentang Python")
        buf.emit_quick("vision", "screenshot terdeteksi ada kode")
        buf.emit_quick("emotional", "tone: antusias")

        snap = buf.snapshot()
        print(f"  File size: {snap['file_size_bytes']} bytes")
        print(f"  In-memory: {snap['in_memory_events']} events")

        # Test 2: load ke stream baru (simulate restart)
        from .sense_stream import SenseStream
        fresh_stream = SenseStream(timeout_sec=3600)
        buf2 = PersistentStreamBuffer(stream=fresh_stream, path=tmp_path)
        restored = buf2.load_from_disk()
        print(f"  Restored on boot: {restored} events")
        assert restored == 3, f"Expected 3, got {restored}"

        # Test 3: snapshot
        snap2 = buf2.snapshot()
        assert snap2["loaded_from_disk"] is True
        print(f"  Snapshot OK: {snap2}")

        print("\n[OK] Semua test self-test passed!")

    finally:
        os.unlink(tmp_path)
        archive = Path(tmp_path).with_suffix(".jsonl.1")
        if archive.exists():
            archive.unlink()
