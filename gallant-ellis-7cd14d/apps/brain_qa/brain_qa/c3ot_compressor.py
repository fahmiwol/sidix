# -*- coding: utf-8 -*-
"""
c3ot_compressor.py — C3oT Compression for SIDIX (Jiwa Sprint 4+)

Compress Chain-of-Thought reasoning traces dari Praxis lessons
menjadi versi singkat yang tetap informatif untuk LoRA training.

Inspired by: C3oT (Chain-of-Thought Compression, 2025) — 30% token reduction
             tanpa accuracy drop pada small models.

Input:  Praxis lessons (Markdown with Thought → Action → Observation)
Output: Compressed reasoning traces (JSONL untuk LoRA dataset)

Methods:
  1. HEURISTIC — rule-based: remove filler, merge redundant, keep decision points
  2. STRUCTURAL — ekstrak hanya "key insight" thoughts (yang mengubah arah reasoning)
  3. SEGMENT — group consecutive similar thoughts, summarize per group

Domain: Kimi (Jiwa) — taste, creativity, corpus territory.
Zero overlap dengan Claude (deploy/core).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("sidix.c3ot")

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_PRAXIS_DIR = _BASE.parent.parent.parent / "brain" / "public" / "praxis" / "lessons"
_OUTPUT_DIR = _BASE.parent.parent / "output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Config ───────────────────────────────────────────────────────────────────
DEFAULT_COMPRESSION_RATIO = 0.5    # target: 50% token reduction
MIN_THOUGHT_LENGTH = 20            # thoughts lebih pendek dari ini di-merge
FILLER_PHRASES: list[str] = [
    "saya pikir", "saya rasa", "mungkin", "sepertinya", "ehm", "hmm",
    "jadi", "oke", "baiklah", "marilah", "pertama-tama", "sebelumnya",
    "sebenarnya", "sebetulnya", "kalau dipikir-pikir", "kalau saya perhatikan",
]
REDUNDANT_PATTERNS: list[str] = [
    r"\b(sama seperti|serupa dengan|mirip dengan)\b.*?(?=[.\n])",
    r"\b(ulangi|ulang kembali|sekali lagi)\b.*?(?=[.\n])",
    r"\b(tidak perlu dijelaskan lagi|sudah jelas)\b.*?(?=[.\n])",
]


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class ReasoningStep:
    """Satu langkah reasoning dari Praxis lesson."""
    step_num: int
    thought: str
    action: str
    observation: str
    is_key_decision: bool = False   # True kalau thought ini mengubah arah reasoning


@dataclass
class CompressedTrace:
    """Hasil compress satu trace lengkap."""
    original_steps: int
    compressed_steps: int
    compression_ratio: float
    compressed_text: str
    key_decisions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class C3oTBatch:
    """Batch compress dari multiple lessons."""
    source_files: list[str] = field(default_factory=list)
    total_original_tokens: int = 0
    total_compressed_tokens: int = 0
    overall_ratio: float = 0.0
    output_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Parser: Praxis Markdown → ReasoningStep ──────────────────────────────────

def parse_praxis_lesson(markdown_text: str) -> list[ReasoningStep]:
    """
    Parse Praxis lesson Markdown menjadi list ReasoningStep.

    Format yang diharapkan:
      ### Langkah N
      - **Thought:** ...
      - **Action:** `tool_name` — args: ...
      - **Observation (cuplikan):** ...
    """
    steps: list[ReasoningStep] = []

    # Split by "### Langkah" atau "### Step"
    sections = re.split(r"\n###\s+(?:Langkah|Step)\s+(\d+)", markdown_text)

    for i in range(1, len(sections), 2):
        if i + 1 >= len(sections):
            continue
        step_num = int(sections[i])
        section = sections[i + 1]

        thought_match = re.search(r"\*\*Thought:\*\*\s*(.+?)(?=\n\s*-\s+\*\*Action|\Z)", section, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r"\*\*Action:\*\*\s*`?([^`\n]+)`?", section, re.IGNORECASE)
        obs_match = re.search(r"\*\*Observation.*?:\*\*\s*(.+?)(?=\n###|\Z)", section, re.DOTALL | re.IGNORECASE)

        thought = (thought_match.group(1).strip() if thought_match else "").replace("\n", " ")
        action = (action_match.group(1).strip() if action_match else "").replace("\n", " ")
        observation = (obs_match.group(1).strip() if obs_match else "").replace("\n", " ")

        # Detect key decision: thought yang mengandung kata-kata perubahan arah
        is_key = bool(re.search(
            r"\b(tetapi|namun|sebaliknya|alternatif|ganti|ubah|revisi|koreksi|perbaiki|" +
            r"seharusnya|justru|malah|ternyata|kesimpulannya|akhirnya|kesimpulan)\b",
            thought.lower(),
        ))

        steps.append(ReasoningStep(
            step_num=step_num,
            thought=thought,
            action=action,
            observation=observation,
            is_key_decision=is_key,
        ))

    return steps


# ── Heuristic Compressor ─────────────────────────────────────────────────────

def _remove_filler(text: str) -> str:
    """Hilangkan filler phrases."""
    for phrase in FILLER_PHRASES:
        text = re.sub(rf"\b{re.escape(phrase)}\b[,.]?\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _remove_redundant(text: str) -> str:
    """Hilangkan redundant patterns."""
    for pattern in REDUNDANT_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()


def _merge_short_thoughts(steps: list[ReasoningStep]) -> list[ReasoningStep]:
    """Merge consecutive short thoughts into one."""
    if not steps:
        return steps

    merged: list[ReasoningStep] = []
    current = steps[0]

    for nxt in steps[1:]:
        # Merge hanya jika current short, non-key, DAN next juga non-key
        if (
            len(current.thought) < MIN_THOUGHT_LENGTH
            and not current.is_key_decision
            and not nxt.is_key_decision
        ):
            current.thought = f"{current.thought}; {nxt.thought}"
            current.action = f"{current.action} -> {nxt.action}" if nxt.action else current.action
            current.observation = f"{current.observation}; {nxt.observation}" if nxt.observation else current.observation
            current.is_key_decision = current.is_key_decision or nxt.is_key_decision
        else:
            merged.append(current)
            current = nxt

    merged.append(current)
    return merged


def compress_steps(steps: list[ReasoningStep], target_ratio: float = DEFAULT_COMPRESSION_RATIO) -> CompressedTrace:
    """
    Compress list ReasoningStep menggunakan heuristic methods.

    Args:
        steps: list ReasoningStep dari parse_praxis_lesson
        target_ratio: target compression ratio (0.5 = 50% reduction)

    Returns:
        CompressedTrace
    """
    if not steps:
        return CompressedTrace(original_steps=0, compressed_steps=0, compression_ratio=0.0, compressed_text="")

    original_text = "\n".join(
        f"Step {s.step_num}: {s.thought} → {s.action} → {s.observation[:80]}"
        for s in steps
    )
    original_tokens = len(original_text.split())

    # 1. Remove filler & redundant
    compressed_steps = []
    for s in steps:
        thought = _remove_filler(s.thought)
        thought = _remove_redundant(thought)
        compressed_steps.append(ReasoningStep(
            step_num=s.step_num,
            thought=thought,
            action=s.action,
            observation=s.observation[:120],  # truncate observation
            is_key_decision=s.is_key_decision,
        ))

    # 2. Merge short thoughts
    compressed_steps = _merge_short_thoughts(compressed_steps)

    # 3. If still not compressed enough, drop non-key steps selectively
    current_tokens = sum(len(s.thought.split()) + len(s.action.split()) for s in compressed_steps)
    current_ratio = current_tokens / max(original_tokens, 1)

    if current_ratio > target_ratio:
        # Drop non-key steps yang paling pendek
        key_steps = [s for s in compressed_steps if s.is_key_decision]
        non_key = [s for s in compressed_steps if not s.is_key_decision]
        # Sort non-key by length desc, keep enough to meet target
        non_key.sort(key=lambda s: len(s.thought), reverse=True)

        max_non_key = max(0, int(len(compressed_steps) * target_ratio) - len(key_steps))
        compressed_steps = key_steps + non_key[:max_non_key]
        compressed_steps.sort(key=lambda s: s.step_num)

    # Build compressed text
    lines = []
    key_decisions = []
    for s in compressed_steps:
        lines.append(f"[{s.step_num}] {s.thought} → {s.action}")
        if s.is_key_decision:
            key_decisions.append(s.thought)

    compressed_text = "\n".join(lines)
    compressed_tokens = len(compressed_text.split())
    ratio = compressed_tokens / max(original_tokens, 1)

    return CompressedTrace(
        original_steps=len(steps),
        compressed_steps=len(compressed_steps),
        compression_ratio=round(ratio, 2),
        compressed_text=compressed_text,
        key_decisions=key_decisions,
        metadata={
            "method": "heuristic_c3ot",
            "target_ratio": target_ratio,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
        },
    )


# ── Batch Processor ──────────────────────────────────────────────────────────

def compress_praxis_lessons(
    lessons_dir: Path | None = None,
    output_path: Path | None = None,
    target_ratio: float = DEFAULT_COMPRESSION_RATIO,
) -> C3oTBatch:
    """
    Compress semua Praxis lessons di direktori menjadi JSONL untuk LoRA training.

    Args:
        lessons_dir: direktori Praxis lessons (default: brain/public/praxis/lessons)
        output_path: path output JSONL (default: output/c3ot_compressed_YYYYMMDD.jsonl)
        target_ratio: target compression ratio

    Returns:
        C3oTBatch dengan statistik
    """
    lessons_dir = lessons_dir or _PRAXIS_DIR
    if output_path is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        output_path = _OUTPUT_DIR / f"c3ot_compressed_{date_str}.jsonl"

    batch = C3oTBatch(
        source_files=[],
        output_path=str(output_path),
    )

    records = []
    lesson_files = sorted(lessons_dir.glob("lesson_*.md"))

    for lesson_file in lesson_files:
        try:
            text = lesson_file.read_text(encoding="utf-8")
            steps = parse_praxis_lesson(text)
            if not steps:
                continue

            compressed = compress_steps(steps, target_ratio=target_ratio)
            batch.source_files.append(str(lesson_file.name))
            batch.total_original_tokens += compressed.metadata.get("original_tokens", 0)
            batch.total_compressed_tokens += compressed.metadata.get("compressed_tokens", 0)

            # Format untuk LoRA training: system + reasoning trace + jawaban
            # Ekstrak jawaban akhir dari markdown
            answer_match = re.search(
                r"## Jawaban akhir.*?\n(.+?)(?=\n## |\Z)", text, re.DOTALL | re.IGNORECASE
            )
            answer = (answer_match.group(1).strip() if answer_match else "").replace("\n", " ")[:500]

            # Pertanyaan
            q_match = re.search(
                r"## Pertanyaan.*?\n(.+?)(?=\n## |\Z)", text, re.DOTALL | re.IGNORECASE
            )
            question = (q_match.group(1).strip() if q_match else "").replace("\n", " ")[:300]

            record = {
                "messages": [
                    {"role": "system", "content": "Kamu adalah SIDIX. Berpikir langkah demi langkah."},
                    {"role": "user", "content": question},
                    {
                        "role": "assistant",
                        "content": f"<think>\n{compressed.compressed_text}\n</think>\n\n{answer}",
                    },
                ],
                "metadata": {
                    "source": lesson_file.name,
                    "original_steps": compressed.original_steps,
                    "compressed_steps": compressed.compressed_steps,
                    "compression_ratio": compressed.compression_ratio,
                    "key_decisions": compressed.key_decisions,
                    "method": "c3ot_heuristic",
                },
            }
            records.append(record)

        except Exception as e:
            logger.warning(f"[C3oT] Failed to process {lesson_file.name}: {e}")

    # Write JSONL
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    batch.overall_ratio = (
        batch.total_compressed_tokens / max(batch.total_original_tokens, 1)
    )

    logger.info(
        f"[C3oT] Compressed {len(records)} lessons → {output_path}. "
        f"Ratio: {batch.overall_ratio:.0%} ({batch.total_compressed_tokens}/{batch.total_original_tokens} tokens)"
    )

    return batch


# ── Main API ─────────────────────────────────────────────────────────────────

def get_compression_stats() -> dict:
    """Return statistik compression terbaru."""
    latest = None
    for path in sorted(_OUTPUT_DIR.glob("c3ot_compressed_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        latest = path
        break

    if not latest:
        return {"status": "no_data", "files": 0}

    count = 0
    with latest.open(encoding="utf-8") as f:
        for _ in f:
            count += 1

    return {
        "status": "ok",
        "latest_file": str(latest.name),
        "records": count,
        "output_dir": str(_OUTPUT_DIR),
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== C3oT Compressor Self-Test ===\n")

    # Test 1: Parse Praxis lesson
    sample = """
# Pelajaran Praxis

## Pertanyaan / tugas pengguna
Apa itu SIDIX?

## Rangkaian eksekusi
### Langkah 0
- **Thought:** User bertanya tentang SIDIX. Saya perlu cari di corpus dulu.
- **Action:** `search_corpus` — args: {"query": "SIDIX"}
- **Observation (cuplikan):** Ditemukan 5 dokumen tentang SIDIX.

### Langkah 1
- **Thought:** Baiklah, saya sudah dapat hasil. Sekarang saya perlu rangkum.
- **Action:** `summarize` — args: {"docs": 5}
- **Observation (cuplikan):** SIDIX adalah AI assistant Islamic.

### Langkah 2
- **Thought:** Tapi sebenarnya, user mungkin butuh penjelasan lebih sederhana. Saya ubah pendekatan.
- **Action:** `` — args: {}
- **Observation (cuplikan):** Jawaban final.

## Jawaban akhir (ringkas)
SIDIX adalah AI assistant dengan pendekatan Islamic epistemology.
"""
    steps = parse_praxis_lesson(sample)
    print(f"[1] Parsed steps: {len(steps)}")
    for s in steps:
        print(f"    Step {s.step_num}: key={s.is_key_decision}, thought={s.thought[:50]}")
    assert len(steps) == 3
    assert steps[2].is_key_decision  # Step 2 has "ubah"
    print("    OK\n")

    # Test 2: Compress steps
    compressed = compress_steps(steps, target_ratio=0.6)
    print(f"[2] Compression: {compressed.original_steps} -> {compressed.compressed_steps} steps")
    print(f"    Ratio: {compressed.compression_ratio}")
    print(f"    Key decisions: {len(compressed.key_decisions)}")
    assert compressed.compressed_steps <= compressed.original_steps
    assert compressed.compression_ratio <= 1.0
    print("    OK\n")

    # Test 3: Batch process (if lessons exist)
    if _PRAXIS_DIR.exists():
        batch = compress_praxis_lessons(target_ratio=0.6)
        print(f"[3] Batch: {len(batch.source_files)} files")
        print(f"    Overall ratio: {batch.overall_ratio:.0%}")
        assert batch.overall_ratio <= 1.0
        print("    OK\n")
    else:
        print("[3] Skipped (no praxis lessons dir)\n")

    # Test 4: Stats
    stats = get_compression_stats()
    print(f"[4] Stats: {stats}")
    print("    OK\n")

    print("[OK] All C3oT self-tests passed")
