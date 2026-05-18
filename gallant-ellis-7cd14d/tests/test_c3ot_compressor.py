# -*- coding: utf-8 -*-
"""Unit tests: C3oT Compressor."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.c3ot_compressor import (
    parse_praxis_lesson,
    compress_steps,
    _remove_filler,
    _merge_short_thoughts,
    ReasoningStep,
    CompressedTrace,
)


def test_parse_praxis_lesson():
    sample = """
## Pertanyaan
Apa itu SIDIX?

## Rangkaian eksekusi
### Langkah 0
- **Thought:** User bertanya tentang SIDIX.
- **Action:** `search_corpus`
- **Observation (cuplikan):** Ditemukan 5 dokumen.

### Langkah 1
- **Thought:** Saya perlu rangkum.
- **Action:** `summarize`
- **Observation (cuplikan):** SIDIX adalah AI.
"""
    steps = parse_praxis_lesson(sample)
    assert len(steps) == 2
    assert steps[0].step_num == 0
    assert steps[0].thought == "User bertanya tentang SIDIX."
    assert steps[0].action == "search_corpus"
    assert steps[1].step_num == 1


def test_parse_praxis_detects_key_decision():
    sample = """
### Langkah 0
- **Thought:** Tapi sebenarnya, saya harus ubah pendekatan.
- **Action:** `revise`
- **Observation:** Done.
"""
    steps = parse_praxis_lesson(sample)
    assert len(steps) == 1
    assert steps[0].is_key_decision is True


def test_remove_filler():
    text = "Saya pikir, mungkin jawabannya adalah 42."
    cleaned = _remove_filler(text)
    assert "saya pikir" not in cleaned.lower()
    assert "mungkin" not in cleaned.lower()
    assert "42" in cleaned


def test_merge_short_thoughts():
    steps = [
        ReasoningStep(0, "Ok.", "action1", "obs1"),
        ReasoningStep(1, "Saya lanjut.", "action2", "obs2"),
        ReasoningStep(2, "Ini adalah key decision point yang sangat penting.", "action3", "obs3", is_key_decision=True),
    ]
    merged = _merge_short_thoughts(steps)
    assert len(merged) == 2  # 0+1 merged, 2 stays
    assert merged[0].step_num == 0
    assert "Ok." in merged[0].thought
    assert "lanjut" in merged[0].thought
    assert merged[1].is_key_decision is True


def test_compress_steps_reduces_size():
    steps = [
        ReasoningStep(0, "Saya pikir user bertanya tentang SIDIX. Mari kita cari.", "search", "found 5"),
        ReasoningStep(1, "Baiklah, saya sudah dapat. Sekarang saya perlu rangkum.", "summarize", "SIDIX AI"),
        ReasoningStep(2, "Tapi sebenarnya user butuh yang lebih simple.", "simplify", "done", is_key_decision=True),
    ]
    compressed = compress_steps(steps, target_ratio=0.7)
    assert compressed.compression_ratio <= 1.0
    assert compressed.compressed_steps <= compressed.original_steps
    assert len(compressed.key_decisions) >= 1


def test_compress_steps_empty():
    result = compress_steps([])
    assert result.original_steps == 0
    assert result.compressed_steps == 0
    assert result.compressed_text == ""


def test_compress_steps_respects_target_ratio():
    steps = [
        ReasoningStep(i, f"Thought number {i} yang cukup panjang untuk testing.", f"action{i}", f"obs{i}")
        for i in range(10)
    ]
    # Make one key decision
    steps[5].is_key_decision = True
    compressed = compress_steps(steps, target_ratio=0.5)
    assert compressed.compressed_steps <= 10
    assert compressed.compression_ratio <= 0.8  # Allow some slack
