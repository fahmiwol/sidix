"""Tests for sense_stream.py — Jiwa Sprint 3 Fase D."""

import pytest
import time

from brain_qa.sense_stream import (
    SenseStream,
    SenseEvent,
    get_sense_stream,
    emit_sense_event,
)


class TestSenseStream:
    def test_emit_and_get(self):
        stream = SenseStream()
        stream.emit_quick("text", "Hello")
        events = stream.get_events()
        assert len(events) == 1
        assert events[0].source == "text"
        assert events[0].data == "Hello"

    def test_filter_by_source(self):
        stream = SenseStream()
        stream.emit_quick("text", "T1")
        stream.emit_quick("vision", "V1")
        text_events = stream.get_events(source="text")
        assert len(text_events) == 1
        assert text_events[0].data == "T1"

    def test_get_latest(self):
        stream = SenseStream()
        stream.emit_quick("text", "First")
        stream.emit_quick("text", "Second")
        latest = stream.get_latest(source="text")
        assert latest.data == "Second"

    def test_deduplication(self):
        stream = SenseStream()
        stream.emit_quick("text", "Same message")
        stream.emit_quick("audio", "Same message")
        all_events = stream.get_events()
        same_msgs = [e for e in all_events if e.data == "Same message"]
        assert len(same_msgs) == 1
        assert "dedup_sources" in same_msgs[0].metadata

    def test_no_dedup_different_content(self):
        stream = SenseStream()
        stream.emit_quick("text", "A")
        stream.emit_quick("audio", "B")
        assert len(stream.get_events()) == 2

    def test_subscribe(self):
        stream = SenseStream()
        received = []
        def handler(evt):
            received.append(evt.data)
        stream.subscribe(handler)
        stream.emit_quick("text", "Test")
        assert "Test" in received
        stream.unsubscribe(handler)

    def test_snapshot(self):
        stream = SenseStream()
        stream.emit_quick("text", "Snap")
        snap = stream.snapshot()
        assert snap["event_count"] == 1
        assert "text" in snap["sources"]

    def test_clear(self):
        stream = SenseStream()
        stream.emit_quick("text", "X")
        stream.clear()
        assert len(stream.get_events()) == 0

    def test_timeout_prunes_old(self):
        stream = SenseStream(timeout_sec=0.1)
        stream.emit_quick("text", "Old")
        time.sleep(0.2)
        stream.emit_quick("text", "New")
        events = stream.get_events()
        assert len(events) == 1
        assert events[0].data == "New"

    def test_since_filter(self):
        stream = SenseStream()
        t0 = time.time()
        stream.emit_quick("text", "Before")
        time.sleep(0.05)
        stream.emit_quick("text", "After")
        events = stream.get_events(since=t0 + 0.02)
        assert len(events) == 1
        assert events[0].data == "After"

    def test_thread_safety(self):
        stream = SenseStream()
        import threading
        threads = []
        for i in range(10):
            t = threading.Thread(target=stream.emit_quick, args=("text", f"msg-{i}"))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(stream.get_events()) == 10


class TestSingleton:
    def test_get_sense_stream(self):
        s1 = get_sense_stream()
        s2 = get_sense_stream()
        assert s1 is s2

    def test_emit_sense_event(self):
        stream = get_sense_stream()
        stream.clear()
        emit_sense_event("text", "Singleton test")
        assert len(stream.get_events(source="text")) >= 1
