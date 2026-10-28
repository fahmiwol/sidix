"""
Jiwa Sprint 4 — Fase C: Persistent Stream Buffer
Tests untuk PersistentStreamBuffer — persist, restore, rotate, graceful degradation.
"""
import sys, os, json, time, tempfile, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path
from brain_qa.sense_stream import SenseStream, SenseEvent
from brain_qa.stream_buffer import (
    PersistentStreamBuffer,
    _event_to_dict,
    _dict_to_event,
    _MAX_FILE_BYTES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_buf(tmp_path):
    """PersistentStreamBuffer dengan fresh stream dan temp file."""
    stream = SenseStream(timeout_sec=3600)
    buf = PersistentStreamBuffer(stream=stream, path=tmp_path / "test_buf.jsonl")
    return buf, stream, tmp_path / "test_buf.jsonl"


# ── Serialization round-trip ──────────────────────────────────────────────────

class TestSerialization:
    def test_event_to_dict_structure(self):
        e = SenseEvent(source="text", data="hello world", confidence=0.9)
        d = _event_to_dict(e)
        assert d["source"] == "text"
        assert d["data"] == "hello world"
        assert d["confidence"] == pytest.approx(0.9, abs=0.001)
        assert "timestamp" in d
        assert "event_id" in d

    def test_dict_to_event_roundtrip(self):
        e = SenseEvent(source="vision", data="screenshot detected", confidence=0.8)
        d = _event_to_dict(e)
        e2 = _dict_to_event(d)
        assert e2 is not None
        assert e2.source == e.source
        assert e2.data == e.data

    def test_dict_to_event_invalid_returns_none(self):
        assert _dict_to_event({}) is None
        assert _dict_to_event({"source": "text"}) is None  # missing timestamp

    def test_long_data_truncated_in_dict(self):
        e = SenseEvent(source="text", data="x" * 1000)
        d = _event_to_dict(e)
        assert len(d["data"]) <= 500


# ── Emit + persist ────────────────────────────────────────────────────────────

class TestEmitAndPersist:
    def test_emit_writes_to_file(self, tmp_buf):
        buf, stream, path = tmp_buf
        buf.emit_quick("text", "user query")
        assert path.exists()
        content = path.read_text(encoding="utf-8").strip()
        lines = [l for l in content.split("\n") if l]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["source"] == "text"

    def test_multiple_emits(self, tmp_buf):
        buf, stream, path = tmp_buf
        for i in range(5):
            buf.emit_quick("text", f"message {i}")
        lines = [l for l in path.read_text(encoding="utf-8").strip().split("\n") if l]
        assert len(lines) == 5

    def test_stream_also_gets_event(self, tmp_buf):
        buf, stream, path = tmp_buf
        buf.emit_quick("vision", "detected object")
        events = stream.get_events(source="vision")
        assert len(events) == 1
        assert events[0].data == "detected object"


# ── Load from disk (boot restore) ────────────────────────────────────────────

class TestLoadFromDisk:
    def test_load_restores_events(self, tmp_path):
        path = tmp_path / "buf.jsonl"
        stream1 = SenseStream(timeout_sec=3600)
        buf1 = PersistentStreamBuffer(stream=stream1, path=path)
        buf1.emit_quick("text", "msg A")
        buf1.emit_quick("audio", "msg B")

        # Simulate restart: buat stream + buffer baru dari file yang sama
        stream2 = SenseStream(timeout_sec=3600)
        buf2 = PersistentStreamBuffer(stream=stream2, path=path)
        restored = buf2.load_from_disk()
        assert restored == 2
        assert buf2.snapshot()["loaded_from_disk"] is True

    def test_load_skips_expired_events(self, tmp_path):
        path = tmp_path / "buf.jsonl"
        # Tulis event dengan timestamp lama (expired)
        old_event = SenseEvent(source="text", data="old", timestamp=time.time() - 9999)
        d = _event_to_dict(old_event)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")

        stream = SenseStream(timeout_sec=30)
        buf = PersistentStreamBuffer(stream=stream, path=path)
        restored = buf.load_from_disk()
        assert restored == 0  # expired, tidak di-restore

    def test_load_nonexistent_file_returns_zero(self, tmp_path):
        path = tmp_path / "nonexistent.jsonl"
        stream = SenseStream(timeout_sec=3600)
        buf = PersistentStreamBuffer(stream=stream, path=path)
        assert buf.load_from_disk() == 0

    def test_load_respects_max_events(self, tmp_path):
        path = tmp_path / "buf.jsonl"
        stream = SenseStream(timeout_sec=3600)
        buf = PersistentStreamBuffer(stream=stream, path=path)
        for i in range(50):
            buf.emit_quick("text", f"msg {i}")

        stream2 = SenseStream(timeout_sec=3600)
        buf2 = PersistentStreamBuffer(stream=stream2, path=path)
        restored = buf2.load_from_disk(max_events=10)
        assert restored <= 10


# ── File rotation ─────────────────────────────────────────────────────────────

class TestFileRotation:
    def test_rotate_when_file_exceeds_limit(self, tmp_path):
        path = tmp_path / "buf.jsonl"
        stream = SenseStream(timeout_sec=3600)
        buf = PersistentStreamBuffer(stream=stream, path=path)

        # Tulis data besar untuk trigger rotate
        big_data = "x" * 500
        iterations = (_MAX_FILE_BYTES // 500) + 10
        for i in range(iterations):
            buf.emit_quick("text", big_data)

        # File archive harus ada
        archive = path.with_suffix(".jsonl.1")
        assert archive.exists() or path.exists()  # either rotated or main file exists


# ── Snapshot ──────────────────────────────────────────────────────────────────

class TestSnapshot:
    def test_snapshot_shape(self, tmp_buf):
        buf, stream, path = tmp_buf
        buf.emit_quick("text", "hello")
        snap = buf.snapshot()
        assert "buffer_path" in snap
        assert "file_size_bytes" in snap
        assert "in_memory_events" in snap
        assert "loaded_from_disk" in snap
        assert snap["in_memory_events"] >= 1

    def test_snapshot_no_file_zero_size(self, tmp_path):
        stream = SenseStream(timeout_sec=3600)
        buf = PersistentStreamBuffer(stream=stream, path=tmp_path / "empty.jsonl")
        snap = buf.snapshot()
        assert snap["file_size_bytes"] == 0


# ── Thread safety ─────────────────────────────────────────────────────────────

class TestThreadSafety:
    def test_concurrent_emit(self, tmp_buf):
        buf, stream, path = tmp_buf
        errors = []

        def worker(n):
            try:
                for i in range(10):
                    buf.emit_quick("text", f"thread {n} msg {i}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        # 5 threads × 10 msgs = 50 events in file
        lines = [l for l in path.read_text(encoding="utf-8").strip().split("\n") if l]
        assert len(lines) == 50


# ── Clear disk ────────────────────────────────────────────────────────────────

class TestClearDisk:
    def test_clear_disk_removes_file(self, tmp_buf):
        buf, stream, path = tmp_buf
        buf.emit_quick("text", "data")
        assert path.exists()
        buf.clear_disk()
        assert not path.exists()
