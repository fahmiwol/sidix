"""Thread-safety tests for praxis.py and experience_engine.py — Jiwa Sprint 3 Fase A."""

import pytest
import tempfile
import threading
import time
from pathlib import Path

from brain_qa.praxis import record_praxis_event
from brain_qa.experience_engine import ExperienceRecord, ExperienceStore


class TestPraxisThreadSafety:
    def test_concurrent_writes_no_corruption(self):
        """10 threads write simultaneously — verify no corrupt JSONL lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override praxis dir temporarily
            from brain_qa import praxis as _praxis
            original_dir = _praxis.praxis_sessions_dir
            _praxis.praxis_sessions_dir = lambda: Path(tmpdir)

            try:
                threads = []
                for i in range(10):
                    t = threading.Thread(
                        target=record_praxis_event,
                        args=(f"session_{i % 3}", "test", {"thread": i}),
                    )
                    threads.append(t)

                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

                # Validate all lines are valid JSON
                for fpath in Path(tmpdir).glob("*.jsonl"):
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                import json
                                data = json.loads(line)
                                assert "ts" in data
                                assert "kind" in data
            finally:
                _praxis.praxis_sessions_dir = original_dir


class TestExperienceEngineThreadSafety:
    def test_concurrent_add_no_corruption(self):
        """10 threads add records simultaneously — verify no corrupt JSONL lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmpf:
            tmpf.close()
            store = ExperienceStore(path=Path(tmpf.name))

            records = []
            for i in range(10):
                rec = ExperienceRecord(
                    id=f"rec-{i}",
                    context=f"ctx-{i}",
                    situation=f"sit-{i}",
                    decision=f"dec-{i}",
                    outcome=f"out-{i}",
                    reflection=f"ref-{i}",
                )
                records.append(rec)

            threads = []
            for rec in records:
                t = threading.Thread(target=store.add, args=(rec,))
                threads.append(t)

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Validate all lines are valid JSON
            loaded = store.load_all()
            assert len(loaded) == 10
            ids = {r.id for r in loaded}
            assert len(ids) == 10
            assert all(r.id.startswith("rec-") for r in loaded)

            # Cleanup
            import os
            os.unlink(tmpf.name)

    def test_add_and_load_integrity(self):
        """Single-threaded baseline: add 5 records, load 5 records."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmpf:
            tmpf.close()
            store = ExperienceStore(path=Path(tmpf.name))

            for i in range(5):
                store.add(ExperienceRecord(
                    id=f"r{i}",
                    context="c",
                    situation="s",
                    decision="d",
                    outcome="o",
                    reflection="r",
                ))

            loaded = store.load_all()
            assert len(loaded) == 5

            import os
            os.unlink(tmpf.name)
