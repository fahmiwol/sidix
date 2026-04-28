"""
tool_synthesis.py — Sprint 38 Tool Synthesis MVP (Pencipta Milestone)

SIDIX literal MENCIPTA skill baru dari pattern berulang. Compound dengan
Sprint 36 reflect_day (data raw) + Sprint 37 Hafidz Ledger (provenance).

Filosofi (note 278 + 282):
- Pillar Pencipta dari aspirasional → real
- Differentiator vs ChatGPT/Claude/Gemini (note 277)
- Realisasi 4 mekanisme cipta-dari-kekosongan (note 278):
  1. Pattern Extraction (Tesla pattern) — induktif generalisasi
  2. Aspiration Detector — deteksi kebutuhan berulang
  3. Tool Synthesis — compose tool baru dari yang ada
  4. Polya 4-phase — decompose → plan → execute → review

MVP scope:
- detect_repeated_sequences() — scan activity_log untuk tool sequence repeat
- propose_macro() — generate YAML macro proposal
- write_proposal_to_quarantine() — file di skills/quarantine/
- hook ke Hafidz Ledger entry per propose

Defer (Sprint 38b/c):
- Actual sandbox execution
- Auto-test pada supporting episodes
- Owner approve workflow (compound Sprint 40 Telegram)

Reference:
- research note 278 (Cipta dari Kekosongan, 4 mekanisme)
- research note 282 (synthesis adoption priority 17/20)
- Voyager (NeurIPS 2023) blueprint
- ROADMAP_SPRINT_36_PLUS.md Sprint 38
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


_ACTIVITY_LOG = "/opt/sidix/.data/sidix_observations.jsonl"
_QUARANTINE_DIR = "/opt/sidix/.data/skills/quarantine"


@dataclass
class ToolSequence:
    """Detected repeated tool sequence (Sprint 38 detector output)."""
    sequence: tuple[str, ...]  # ordered tool names
    count: int  # how many times observed
    supporting_episodes: list[str] = field(default_factory=list)  # session/cycle IDs
    first_seen: str = ""
    last_seen: str = ""


@dataclass
class MacroProposal:
    """YAML macro proposal (Sprint 38 proposer output)."""
    skill_id: str
    composed_from: list[str]  # tool names di sequence
    trigger_pattern: str  # query pattern hint untuk dispatch
    born_from_episodes: list[str]  # cycle/session IDs supporting
    frequency: int
    confidence: str  # "low" | "medium" | "high"
    auto_test: str = "pending"  # "pending" | "passed" | "failed"
    owner_verdict: str = "pending"  # "pending" | "approved" | "rejected"
    proposed_at: str = ""
    cycle_id: str = ""


def detect_repeated_sequences(
    window_days: int = 7,
    min_count: int = 3,
    sequence_length: int = 3,
) -> list[ToolSequence]:
    """Scan activity log untuk tool sequence repeat dalam window.

    Algorithm:
    1. Load activity_log dari N hari terakhir
    2. Extract tool actions per session
    3. Sliding window N tools = 1 sequence
    4. Count frequency
    5. Return sequence yang count >= min_count

    Args:
        window_days: berapa hari ke belakang scan
        min_count: minimum frequency untuk kandidat
        sequence_length: berapa tool dalam 1 sequence

    Returns:
        list[ToolSequence] sorted by count desc.
    """
    activity = Path(_ACTIVITY_LOG)
    if not activity.exists():
        log.warning("[tool_synth] activity log not found: %s", _ACTIVITY_LOG)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    seq_counter: Counter = Counter()
    seq_supporting: dict[tuple, list[str]] = {}
    seq_timestamps: dict[tuple, list[str]] = {}

    # Group tools per session/cycle untuk extract sequence
    session_tools: dict[str, list[tuple[str, str]]] = {}  # session_id → [(ts, tool)]

    with open(activity, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            ts_str = e.get("ts") or e.get("timestamp") or ""
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if ts < cutoff:
                continue
            tool = e.get("action") or e.get("tool") or e.get("name") or ""
            if not tool or tool == "":
                continue
            session = e.get("session_id") or e.get("cycle_id") or "default"
            session_tools.setdefault(session, []).append((ts_str, tool))

    # Sliding window per session
    for session, items in session_tools.items():
        items.sort(key=lambda x: x[0])
        tools = [t for _, t in items]
        for i in range(len(tools) - sequence_length + 1):
            seq = tuple(tools[i : i + sequence_length])
            seq_counter[seq] += 1
            seq_supporting.setdefault(seq, []).append(session)
            seq_timestamps.setdefault(seq, []).append(items[i][0])

    # Build ToolSequence kandidat
    results = []
    for seq, count in seq_counter.most_common():
        if count < min_count:
            break  # most_common sorted desc, stop early
        timestamps = seq_timestamps.get(seq, [])
        results.append(ToolSequence(
            sequence=seq,
            count=count,
            supporting_episodes=list(set(seq_supporting.get(seq, [])))[:5],
            first_seen=min(timestamps) if timestamps else "",
            last_seen=max(timestamps) if timestamps else "",
        ))
    return results


def propose_macro(seq: ToolSequence, cycle_id: str = "") -> MacroProposal:
    """Generate macro proposal dari detected sequence.

    Confidence rule:
    - count ≥10 → high
    - count ≥5 → medium
    - else → low (still propose untuk review)
    """
    # Generate skill_id (snake_case dari sequence)
    skill_id = "_".join(s.lower().replace("-", "_") for s in seq.sequence)
    if len(skill_id) > 60:
        skill_id = skill_id[:60]

    # Heuristic trigger pattern (placeholder — owner refines)
    trigger = " then ".join(seq.sequence)

    if seq.count >= 10:
        confidence = "high"
    elif seq.count >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    return MacroProposal(
        skill_id=skill_id,
        composed_from=list(seq.sequence),
        trigger_pattern=trigger,
        born_from_episodes=seq.supporting_episodes,
        frequency=seq.count,
        confidence=confidence,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        cycle_id=cycle_id or f"synthesis-{int(time.time())}",
    )


def write_proposal_to_quarantine(proposal: MacroProposal) -> str:
    """Write proposal as YAML ke skills/quarantine/. Returns file path.

    Compound dengan Sprint 37 Hafidz Ledger: write entry dengan content_id =
    skill_id, content_type = "skill_proposal".
    """
    Path(_QUARANTINE_DIR).mkdir(parents=True, exist_ok=True)
    file_path = Path(_QUARANTINE_DIR) / f"{proposal.skill_id}.yaml"

    # Manual YAML format (no PyYAML dep — keep lean)
    lines = [
        f"# Sprint 38 Tool Synthesis — Macro Proposal (PENDING owner review)",
        f"# Sandbox quarantine 7 hari minimum sebelum promote ke skills/active/",
        f"",
        f"skill_id: {proposal.skill_id}",
        f"composed_from:",
    ]
    for tool in proposal.composed_from:
        lines.append(f"  - {tool}")
    lines.extend([
        f"trigger_pattern: \"{proposal.trigger_pattern}\"",
        f"frequency: {proposal.frequency}",
        f"confidence: {proposal.confidence}",
        f"auto_test: {proposal.auto_test}",
        f"owner_verdict: {proposal.owner_verdict}",
        f"proposed_at: {proposal.proposed_at}",
        f"cycle_id: {proposal.cycle_id}",
        f"born_from_episodes:",
    ])
    for ep in proposal.born_from_episodes:
        lines.append(f"  - {ep}")

    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Sprint 37 Hafidz Ledger hook — write entry per proposal
    try:
        from .hafidz_ledger import write_entry
        content = file_path.read_text(encoding="utf-8")
        write_entry(
            content=content,
            content_id=f"skill-proposal-{proposal.skill_id}",
            content_type="skill_proposal",
            isnad_chain=[],  # primary entry; future: add lesson refs jika lahir dari reflection
            sources=[str(file_path)],
            metadata={
                "frequency": proposal.frequency,
                "confidence": proposal.confidence,
                "composed_from_count": len(proposal.composed_from),
            },
            cycle_id=proposal.cycle_id,
        )
        log.info("[tool_synth] Hafidz entry written for skill: %s", proposal.skill_id)
    except Exception as e:
        log.debug("[tool_synth] hafidz hook skip: %s", e)

    return str(file_path)


def run_synthesis(
    window_days: int = 7,
    min_count: int = 3,
    sequence_length: int = 3,
    cycle_id: str = "",
) -> dict:
    """Full synthesis run: detect → propose → write.

    Returns summary dict untuk CLI / cron logging.
    """
    cycle_id = cycle_id or f"synthesis-{int(time.time())}"
    log.info("[tool_synth] cycle %s START — window=%dd min_count=%d", cycle_id, window_days, min_count)

    sequences = detect_repeated_sequences(window_days, min_count, sequence_length)
    log.info("[tool_synth] detected %d candidate sequences", len(sequences))

    proposals = []
    written_files = []
    for seq in sequences:
        prop = propose_macro(seq, cycle_id=cycle_id)
        path = write_proposal_to_quarantine(prop)
        proposals.append(prop)
        written_files.append(path)
        log.info("[tool_synth] proposal: %s (freq=%d, conf=%s)", prop.skill_id, prop.frequency, prop.confidence)

    return {
        "cycle_id": cycle_id,
        "window_days": window_days,
        "min_count": min_count,
        "sequences_detected": len(sequences),
        "proposals_written": len(proposals),
        "files": written_files,
        "proposals": [asdict(p) for p in proposals],
    }


__all__ = [
    "ToolSequence",
    "MacroProposal",
    "detect_repeated_sequences",
    "propose_macro",
    "write_proposal_to_quarantine",
    "run_synthesis",
]
