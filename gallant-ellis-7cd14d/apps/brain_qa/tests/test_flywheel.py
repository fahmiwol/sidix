"""
Unit tests untuk auto_train_flywheel.py — isolated, using mocks.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from brain_qa.jariyah_exporter import LORA_READY_THRESHOLD


class TestFlywheelCheck:
    def test_check_with_no_data(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        monkeypatch.setattr(fw, "JARIYAH_PAIRS", tmp_path / "nonexistent.jsonl")
        monkeypatch.setattr(fw, "SYNTHETIC_DIR", tmp_path / "syn")
        monkeypatch.setattr(fw, "DPO_PAIRS", tmp_path / "dpo.jsonl")
        result = fw.step_check()
        assert result["ready"] is False
        assert result["total"] == 0

    def test_check_with_enough_data(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        pairs_file = tmp_path / "jariyah_pairs.jsonl"
        with open(pairs_file, "w") as f:
            for i in range(LORA_READY_THRESHOLD + 10):
                f.write(json.dumps({"query": f"q{i}", "response": f"r{i}", "rating": 1}) + "\n")
        monkeypatch.setattr(fw, "JARIYAH_PAIRS", pairs_file)
        monkeypatch.setattr(fw, "SYNTHETIC_DIR", tmp_path / "syn")
        monkeypatch.setattr(fw, "DPO_PAIRS", tmp_path / "dpo.jsonl")
        monkeypatch.setattr(fw, "MIN_PAIRS", LORA_READY_THRESHOLD)
        result = fw.step_check()
        assert result["ready"] is True
        assert result["jariyah"] >= LORA_READY_THRESHOLD


class TestFlywheelExport:
    def test_export_empty(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        monkeypatch.setattr(fw, "TRAIN_DATASET", tmp_path / "train.jsonl")
        result = fw.step_export({"total": 0})
        assert result["exported"] == 0

    def test_export_with_jariyah(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        import brain_qa.jariyah_exporter as je
        pairs_file = tmp_path / "jariyah_pairs.jsonl"
        with open(pairs_file, "w") as f:
            f.write(json.dumps({"query": "q", "response": "r", "rating": 1, "score": 0.9}) + "\n")
        monkeypatch.setattr(fw, "JARIYAH_PAIRS", pairs_file)
        monkeypatch.setattr(je, "PAIRS_PATH", pairs_file)
        monkeypatch.setattr(fw, "SYNTHETIC_DIR", tmp_path / "syn")
        monkeypatch.setattr(fw, "DPO_PAIRS", tmp_path / "dpo.jsonl")
        monkeypatch.setattr(fw, "TRAIN_DATASET", tmp_path / "train.jsonl")
        monkeypatch.setattr(fw, "FLYWHEEL_DIR", tmp_path)
        result = fw.step_export({"total": 1})
        assert result["exported"] >= 1
        assert (tmp_path / "train.jsonl").exists()


class TestFlywheelTrain:
    def test_train_mock(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        monkeypatch.setattr(fw, "TRAIN_MODE", "mock")
        result = fw.step_train({"dataset_path": str(tmp_path / "train.jsonl")}, dry_run=False)
        assert result["status"] == "mock_complete"
        assert result["loss"] > 0

    def test_train_dry_run(self, monkeypatch, tmp_path):
        import scripts.auto_train_flywheel as fw
        result = fw.step_train({"dataset_path": str(tmp_path / "train.jsonl")}, dry_run=True)
        assert result["status"] == "dry_run"
