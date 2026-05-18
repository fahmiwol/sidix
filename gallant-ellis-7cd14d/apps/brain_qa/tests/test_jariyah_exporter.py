"""
Tests untuk jariyah_exporter.py

Menggunakan tmp_path pytest agar tidak menyentuh file data real.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Pastikan module brain_qa bisa diimport dari test runner
sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa import jariyah_exporter as exporter


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_pairs(path: Path, pairs: list[dict]) -> None:
    """Tulis list pair ke JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")


def _make_pair(
    query: str = "Apa itu SIDIX?",
    response: str = "SIDIX adalah AI lokal.",
    rating: int = 1,
    score: float | None = None,
) -> dict:
    return {
        "query": query,
        "response": response,
        "rating": rating,
        "persona": "UTZ",
        "session_id": "test-session-001",
        "timestamp": "2026-04-24T00:00:00+00:00",
        **({"score": score} if score is not None else {}),
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestExportEmpty:
    """test_export_empty — tidak ada pairs, return exported=0."""

    def test_returns_zero_when_no_file(self, tmp_path):
        fake_pairs_path = tmp_path / "data" / "jariyah_pairs.jsonl"
        with patch.object(exporter, "PAIRS_PATH", fake_pairs_path):
            result = exporter.export_to_lora_jsonl(output_path=tmp_path / "out.jsonl")

        assert result["exported"] == 0
        assert result["ready_for_lora"] is False
        assert result["output_path"] is None

    def test_returns_zero_when_file_is_empty(self, tmp_path):
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        pairs_file.parent.mkdir(parents=True)
        pairs_file.write_text("", encoding="utf-8")

        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=tmp_path / "out.jsonl")

        assert result["exported"] == 0
        assert result["ready_for_lora"] is False


class TestExportFiltersByScore:
    """test_export_filters_by_score — hanya export pairs dengan score >= 0.7."""

    def test_filters_low_score_no_thumbsup(self, tmp_path):
        """Pair dengan score rendah dan bukan thumbs_up harus di-skip."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Q1", response="R1", rating=0, score=0.5),   # skip
            _make_pair(query="Q2", response="R2", rating=-1, score=0.3),  # skip
            _make_pair(query="Q3", response="R3", rating=0, score=0.8),   # export (score >= 0.7)
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=out_file, min_score=0.7)

        assert result["exported"] == 1
        assert result["skipped"] == 2

    def test_thumbsup_always_exported_regardless_of_score(self, tmp_path):
        """Pair thumbs_up (rating=1) harus diekspor meski score < threshold."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Q1", response="R1", rating=1, score=0.2),  # export (thumbs_up)
            _make_pair(query="Q2", response="R2", rating=0, score=0.2),  # skip
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=out_file, min_score=0.7)

        assert result["exported"] == 1

    def test_skips_empty_query_or_response(self, tmp_path):
        """Pair dengan query atau response kosong harus selalu di-skip."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="", response="R1", rating=1),        # skip: query kosong
            _make_pair(query="Q2", response="", rating=1),        # skip: response kosong
            _make_pair(query="Q3", response="R3", rating=1),      # export
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=out_file)

        assert result["exported"] == 1

    def test_custom_min_score(self, tmp_path):
        """min_score custom diterapkan dengan benar."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Q1", response="R1", rating=0, score=0.6),  # export kalau threshold=0.5
            _make_pair(query="Q2", response="R2", rating=0, score=0.4),  # skip
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=out_file, min_score=0.5)

        assert result["exported"] == 1


class TestExportLoraFormat:
    """test_export_lora_format — output format benar (messages list dengan role user/assistant)."""

    def test_output_has_correct_structure(self, tmp_path):
        """Setiap entry harus punya key 'messages' berisi list 3 item."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Apa itu SIDIX?", response="SIDIX adalah AI lokal.", rating=1),
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            exporter.export_to_lora_jsonl(output_path=out_file)

        lines = out_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert "messages" in entry
        messages = entry["messages"]
        assert len(messages) == 3

    def test_message_roles_are_correct(self, tmp_path):
        """Urutan role harus: system, user, assistant."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Q?", response="A.", rating=1),
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            exporter.export_to_lora_jsonl(output_path=out_file)

        entry = json.loads(out_file.read_text(encoding="utf-8").strip())
        roles = [m["role"] for m in entry["messages"]]
        assert roles == ["system", "user", "assistant"]

    def test_message_content_matches_pair(self, tmp_path):
        """Content user dan assistant harus sama persis dengan query/response pair."""
        query = "Apa itu LoRA?"
        response = "LoRA adalah teknik fine-tuning efisien."
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query=query, response=response, rating=1),
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            exporter.export_to_lora_jsonl(output_path=out_file)

        entry = json.loads(out_file.read_text(encoding="utf-8").strip())
        messages = entry["messages"]
        assert messages[1]["content"] == query
        assert messages[2]["content"] == response

    def test_system_message_is_present_and_non_empty(self, tmp_path):
        """System message harus ada dan tidak kosong."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [_make_pair(rating=1)])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            exporter.export_to_lora_jsonl(output_path=out_file)

        entry = json.loads(out_file.read_text(encoding="utf-8").strip())
        system_msg = entry["messages"][0]
        assert system_msg["role"] == "system"
        assert len(system_msg["content"]) > 10

    def test_multiple_pairs_all_exported(self, tmp_path):
        """Semua pair yang lolos filter harus muncul di output."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query=f"Q{i}", response=f"R{i}", rating=1)
            for i in range(5)
        ])

        out_file = tmp_path / "out.jsonl"
        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            result = exporter.export_to_lora_jsonl(output_path=out_file)

        assert result["exported"] == 5
        lines = out_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5


class TestGetExportStats:
    """test_get_export_stats — return dict dengan keys yang benar."""

    def test_returns_required_keys(self, tmp_path):
        """Hasil harus mengandung semua key yang diperlukan."""
        fake_pairs_path = tmp_path / "data" / "jariyah_pairs.jsonl"
        with patch.object(exporter, "PAIRS_PATH", fake_pairs_path):
            stats = exporter.get_export_stats()

        required_keys = {"total", "exportable", "skipped", "threshold", "ready_for_lora"}
        assert required_keys.issubset(stats.keys())

    def test_stats_when_no_file(self, tmp_path):
        """Jika file tidak ada, total dan exportable harus 0."""
        fake_pairs_path = tmp_path / "data" / "jariyah_pairs.jsonl"
        with patch.object(exporter, "PAIRS_PATH", fake_pairs_path):
            stats = exporter.get_export_stats()

        assert stats["total"] == 0
        assert stats["exportable"] == 0
        assert stats["skipped"] == 0
        assert stats["ready_for_lora"] is False

    def test_stats_threshold_value(self, tmp_path):
        """threshold harus sesuai dengan LORA_READY_THRESHOLD."""
        fake_pairs_path = tmp_path / "data" / "jariyah_pairs.jsonl"
        with patch.object(exporter, "PAIRS_PATH", fake_pairs_path):
            stats = exporter.get_export_stats()

        assert stats["threshold"] == exporter.LORA_READY_THRESHOLD

    def test_stats_counts_correctly(self, tmp_path):
        """Jumlah exportable + skipped harus sama dengan total."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(query="Q1", response="R1", rating=1),          # exportable
            _make_pair(query="Q2", response="R2", rating=0, score=0.8),  # exportable
            _make_pair(query="Q3", response="R3", rating=-1, score=0.3), # skipped
        ])

        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            stats = exporter.get_export_stats()

        assert stats["total"] == 3
        assert stats["exportable"] == 2
        assert stats["skipped"] == 1

    def test_ready_for_lora_false_below_threshold(self, tmp_path):
        """ready_for_lora False jika exportable < LORA_READY_THRESHOLD."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        _write_pairs(pairs_file, [
            _make_pair(rating=1) for _ in range(10)
        ])

        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            stats = exporter.get_export_stats()

        assert stats["ready_for_lora"] is False  # 10 < 500

    def test_ready_for_lora_true_at_threshold(self, tmp_path):
        """ready_for_lora True jika exportable >= LORA_READY_THRESHOLD."""
        pairs_file = tmp_path / "data" / "jariyah_pairs.jsonl"
        threshold = exporter.LORA_READY_THRESHOLD
        _write_pairs(pairs_file, [
            _make_pair(query=f"Q{i}", response=f"R{i}", rating=1)
            for i in range(threshold)
        ])

        with patch.object(exporter, "PAIRS_PATH", pairs_file):
            stats = exporter.get_export_stats()

        assert stats["ready_for_lora"] is True
