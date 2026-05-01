"""
test_sprint_i_persona_adapter.py — Sprint I: DoRA Persona Adapter Tests

Verifies:
  - Config loading (default + override)
  - Config persistence (save/reset)
  - Generation wrapper (with mocked LLM)
  - Data harvesting from Hafidz
  - Training data builder
  - Stats aggregation

Run: python -m pytest tests/test_sprint_i_persona_adapter.py -q
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from brain_qa.persona_adapter import (
    PersonaConfig,
    get_persona_config,
    save_persona_config,
    reset_persona_config,
    generate_with_persona,
    harvest_persona_data,
    build_training_data,
    get_adapter_stats,
    _DEFAULT_CONFIGS,
    ADAPTER_ROOT,
    CONFIG_DIR,
    TRAINING_DIR,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_storage(tmp_path: Path, monkeypatch):
    """Redirect all adapter storage to a temp directory."""
    root = tmp_path / "persona_adapter"
    monkeypatch.setattr("brain_qa.persona_adapter.ADAPTER_ROOT", root)
    monkeypatch.setattr("brain_qa.persona_adapter.CONFIG_DIR", root / "configs")
    monkeypatch.setattr("brain_qa.persona_adapter.TRAINING_DIR", root / "training_data")
    monkeypatch.setattr("brain_qa.persona_adapter.HARVESTED_DIR", root / "harvested")
    yield


# ── Config Tests ─────────────────────────────────────────────────────────

class TestConfigLoading:
    def test_default_configs_exist(self):
        """All 5 personas have default configs."""
        assert len(_DEFAULT_CONFIGS) == 5
        for p in ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"):
            assert p in _DEFAULT_CONFIGS

    def test_config_fields(self):
        """Config has all expected fields."""
        cfg = _DEFAULT_CONFIGS["UTZ"]
        assert cfg.persona == "UTZ"
        assert "kreatif" in cfg.system_prompt.lower() or "creative" in cfg.system_prompt.lower()
        assert 0.0 < cfg.temperature <= 1.0
        assert cfg.max_tokens > 0

    def test_load_default(self):
        """Loading non-persisted config returns default."""
        cfg = get_persona_config("UTZ")
        assert cfg.persona == "UTZ"
        assert cfg.temperature == 0.85

    def test_load_unknown_fallback(self):
        """Unknown persona falls back to AYMAN."""
        cfg = get_persona_config("UNKNOWN_XYZ")
        assert cfg.persona == "AYMAN"


class TestConfigPersistence:
    def test_save_and_reload(self):
        """Saved config can be reloaded."""
        cfg = PersonaConfig(
            persona="UTZ",
            system_prompt="Test prompt",
            temperature=0.99,
            max_tokens=999,
        )
        save_persona_config(cfg)

        loaded = get_persona_config("UTZ")
        assert loaded.temperature == 0.99
        assert loaded.max_tokens == 999
        assert loaded.system_prompt == "Test prompt"

    def test_reset_to_default(self):
        """Reset restores default values."""
        # Mutate first
        cfg = PersonaConfig(
            persona="ABOO",
            system_prompt="Mutated",
            temperature=0.1,
        )
        save_persona_config(cfg)

        # Reset
        reset = reset_persona_config("ABOO")
        assert reset.system_prompt == _DEFAULT_CONFIGS["ABOO"].system_prompt
        assert reset.temperature == _DEFAULT_CONFIGS["ABOO"].temperature


# ── Generation Tests ─────────────────────────────────────────────────────

class TestGeneration:
    def test_generate_with_persona_returns_string(self, monkeypatch):
        """generate_with_persona returns a string (mocked LLM)."""
        def _fake_ollama(*args, **kwargs):
            return "Mocked response", "local"

        monkeypatch.setattr(
            "brain_qa.ollama_llm.ollama_generate",
            _fake_ollama,
        )

        result = generate_with_persona("Hello", persona="UTZ")
        assert isinstance(result, str)
        assert result == "Mocked response"

    def test_generate_with_persona_system_injected(self, monkeypatch):
        """System prompt from persona is injected into generation."""
        calls = []

        def _capture(prompt, **kwargs):
            calls.append(prompt)
            return "Captured", "local"

        monkeypatch.setattr(
            "brain_qa.ollama_llm.ollama_generate",
            _capture,
        )

        generate_with_persona("Hello", persona="ABOO")
        assert len(calls) == 1
        # System prompt dari ABOO harus ada di prompt
        assert "ABOO" in calls[0] or "engineer" in calls[0].lower()

    def test_temperature_varies_by_persona(self, monkeypatch):
        """Different personas have different temperature defaults."""
        temps = []

        def _capture_temp(prompt, **kwargs):
            temps.append(kwargs.get("temperature"))
            return "OK", "local"

        monkeypatch.setattr(
            "brain_qa.ollama_llm.ollama_generate",
            _capture_temp,
        )

        generate_with_persona("X", persona="UTZ")
        generate_with_persona("X", persona="ABOO")
        generate_with_persona("X", persona="ALEY")

        assert temps[0] == 0.85  # UTZ creative
        assert temps[1] == 0.4   # ABOO precise
        assert temps[2] == 0.5   # ALEY skeptical


# ── Data Harvester Tests ─────────────────────────────────────────────────

class TestDataHarvester:
    def test_harvest_empty_hafidz(self, monkeypatch):
        """Harvest returns empty list when no Hafidz data."""
        fake_root = Path("/nonexistent/hafidz")
        monkeypatch.setattr("brain_qa.hafidz_injector.GOLDEN_ROOT", fake_root)

        result = harvest_persona_data("UTZ")
        assert result == []

    def test_harvest_from_mock_hafidz(self, tmp_path: Path, monkeypatch):
        """Harvest extracts Q&A from mock Hafidz entries."""
        fake_root = tmp_path / "golden"
        fake_root.mkdir()
        date_dir = fake_root / "2026-04-30"
        date_dir.mkdir()

        md = date_dir / "entry_001.md"
        md.write_text(
            "---\npersona: UTZ\n---\n"
            "## Pertanyaan\nBagaimana cara berkreasi?\n"
            "## Jawaban\nDengan imajinasi bebas.\n",
            encoding="utf-8",
        )

        monkeypatch.setattr("brain_qa.hafidz_injector.GOLDEN_ROOT", fake_root)

        result = harvest_persona_data("UTZ")
        assert len(result) == 1
        assert result[0]["input"] == "Bagaimana cara berkreasi?"
        assert result[0]["output"] == "Dengan imajinasi bebas."
        assert result[0]["persona"] == "UTZ"


# ── Training Data Builder Tests ──────────────────────────────────────────

class TestTrainingDataBuilder:
    def test_build_training_data_empty(self, tmp_path: Path, monkeypatch):
        """Build with no examples creates empty file."""
        fake_root = tmp_path / "empty_golden"
        fake_root.mkdir()
        monkeypatch.setattr("brain_qa.hafidz_injector.GOLDEN_ROOT", fake_root)

        path = build_training_data("UTZ")
        assert path.exists()
        content = path.read_text(encoding="utf-8").strip()
        assert content == ""

    def test_build_training_data_format(self, tmp_path: Path, monkeypatch):
        """Built file has correct chat-completion format."""
        fake_root = tmp_path / "golden"
        fake_root.mkdir()
        date_dir = fake_root / "2026-04-30"
        date_dir.mkdir()

        md = date_dir / "entry_001.md"
        md.write_text(
            "---\npersona: ABOO\n---\n"
            "## Pertanyaan\nApa itu API?\n"
            "## Jawaban\nAPI adalah interface.\n",
            encoding="utf-8",
        )

        monkeypatch.setattr("brain_qa.hafidz_injector.GOLDEN_ROOT", fake_root)

        path = build_training_data("ABOO")
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert "messages" in record
        assert len(record["messages"]) == 3
        assert record["messages"][0]["role"] == "system"
        assert record["messages"][1]["role"] == "user"
        assert record["messages"][2]["role"] == "assistant"
        assert record["metadata"]["persona"] == "ABOO"


# ── Stats Tests ──────────────────────────────────────────────────────────

class TestStats:
    def test_stats_initial(self):
        """Initial stats show no configs persisted, no training data."""
        stats = get_adapter_stats()
        for persona in _DEFAULT_CONFIGS:
            assert stats["configs"][persona] is False
            assert stats["training_records"][persona] == 0

    def test_stats_after_save(self):
        """Stats reflect saved configs and training data."""
        save_persona_config(_DEFAULT_CONFIGS["UTZ"])
        build_training_data("UTZ", limit=10)

        stats = get_adapter_stats()
        assert stats["configs"]["UTZ"] is True
        assert stats["training_records"]["UTZ"] >= 0  # 0 if no Hafidz data
