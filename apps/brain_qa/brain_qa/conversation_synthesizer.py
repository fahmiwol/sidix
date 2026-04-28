"""
conversation_synthesizer.py — Sprint 41 (Conversation Synthesizer, "Claude as guru")

Takes a conversation transcript (founder ↔ external AI like Claude/GPT/Gemini)
and synthesizes it into a SIDIX research note + Hafidz Ledger entry.

Founder mandate (LOCK 2026-04-29): *"setiap percakapan kita juga harus bisa
di sintesis sama sidix, kamu sebagai guru."*

Compound effect: setiap sesi founder dengan AI eksternal = SIDIX corpus
growth otomatis. External AI sebagai guru, SIDIX sebagai murid yang
synthesize → research note → corpus permanent.

Pipeline:

    raw_transcript (any format: Claude Code / ChatGPT export / plain Q&A)
       ↓
    parse_turns() — detect speaker boundaries via regex pattern
       ↓
    detect_topic() — extract main topic from content
       ↓
    extract_qa_pairs() — pair user question + assistant answer
       ↓
    extract_decisions() — find decision-like statements
       ↓
    extract_facts() — surface factual claims with sources
       ↓
    extract_open_questions() — unresolved questions for future work
       ↓
    [Phase 2] persona_research_fanout — multi-angle analysis
       ↓
    generate_note() — markdown format with sanad chain
       ↓
    write to brain/public/research_notes/
       ↓
    hafidz_ledger.write_entry(sanad: external_ai as guru)

Reference:
- project_sidix_distribution_pixel_basirport.md (founder mandate)
- project_sidix_multi_agent_pattern.md (persona fanout)
- brain/public/research_notes/* (output format reference)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Speaker detection patterns ────────────────────────────────────────────────

# Order matters — more specific first
_SPEAKER_PATTERNS: list[tuple[str, str]] = [
    # Claude Code / Anthropic format
    (r"^Human:\s*", "user"),
    (r"^Assistant:\s*", "assistant"),
    # ChatGPT export
    (r"^User:\s*", "user"),
    (r"^ChatGPT:\s*", "assistant"),
    # Generic
    (r"^You:\s*", "user"),
    (r"^AI:\s*", "assistant"),
    (r"^Bot:\s*", "assistant"),
    # Markdown bold variants
    (r"^\*\*Human\*\*:?\s*", "user"),
    (r"^\*\*Assistant\*\*:?\s*", "assistant"),
    (r"^\*\*User\*\*:?\s*", "user"),
    (r"^\*\*ChatGPT\*\*:?\s*", "assistant"),
]

# Decision-like cue phrases (Indonesian + English)
_DECISION_CUES = [
    "saya pilih", "pilih", "kita gas", "gas", "lock", "setuju",
    "I'll go with", "let's go with", "decision:", "we decided",
    "rekomendasi:", "recommend:", "kita lanjut", "proceed",
    "pilihan:", "choice:", "decided to",
]

# Fact-like cue phrases (claims that have value to corpus)
_FACT_CUES = [
    "menurut", "sumber:", "source:", "according to", "per ",
    "data menunjukkan", "research shows", "studi menemukan",
    "fakta:", "fact:", "[FAKTA]", "[FACT]",
]

# Open question indicators
_OPEN_Q_CUES = [
    "open question:", "perlu cek", "need to verify",
    "TBD", "TODO", "?", "belum yakin", "not sure",
]


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ConversationTurn:
    speaker: str           # "user" | "assistant" | "unknown"
    content: str
    line_start: int = 0    # 1-indexed line in source
    line_end: int = 0


@dataclass
class QAPair:
    question: str
    answer: str
    turn_index: int = 0    # which turn the user question appeared


@dataclass
class SynthesisResult:
    """Output bundle from synthesizing a conversation."""
    topic: str = ""
    domain: str = "general"        # tech | biz | research | creative | general
    turn_count: int = 0
    qa_pairs: list[QAPair] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    persona_analysis: dict = field(default_factory=dict)  # Phase 2 fanout
    note_path: str = ""            # output path after write
    note_number: int = 0
    sanad_chain: list[dict] = field(default_factory=list)
    raw_word_count: int = 0


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_turns(transcript: str) -> list[ConversationTurn]:
    """Split a transcript into ordered (speaker, content) turns."""
    if not transcript.strip():
        return []
    lines = transcript.splitlines()
    turns: list[ConversationTurn] = []
    current_speaker = "unknown"
    current_buffer: list[str] = []
    current_start = 1

    def _flush(end_line: int) -> None:
        if current_buffer:
            content = "\n".join(current_buffer).strip()
            if content:
                turns.append(ConversationTurn(
                    speaker=current_speaker,
                    content=content,
                    line_start=current_start,
                    line_end=end_line,
                ))

    for idx, line in enumerate(lines, start=1):
        matched = False
        for pattern, speaker in _SPEAKER_PATTERNS:
            m = re.match(pattern, line)
            if m:
                _flush(end_line=idx - 1)
                current_speaker = speaker
                current_buffer = [line[m.end():]]
                current_start = idx
                matched = True
                break
        if not matched:
            current_buffer.append(line)
    _flush(end_line=len(lines))
    return turns


# ── Extractors ───────────────────────────────────────────────────────────────

def detect_topic(turns: list[ConversationTurn], max_words: int = 8) -> str:
    """Heuristic topic detection: first user turn first sentence."""
    for t in turns:
        if t.speaker == "user" and t.content.strip():
            first_sentence = re.split(r"[.!?\n]", t.content, maxsplit=1)[0]
            words = first_sentence.split()[:max_words]
            return " ".join(words).strip() or "untitled"
    return "untitled"


def detect_domain(transcript: str) -> str:
    """Classify domain by keyword frequency."""
    text = transcript.lower()
    domain_keywords = {
        "tech":     ["code", "function", "api", "deploy", "git", "python", "javascript", "bug", "error"],
        "biz":      ["bisnis", "revenue", "monetisasi", "pricing", "market", "acquirer", "umkm"],
        "research": ["research", "paper", "study", "literature", "hipotesis", "metodologi"],
        "creative": ["design", "image", "video", "audio", "brand", "logo", "creative", "moodboard"],
    }
    scores = {d: sum(1 for kw in kws if kw in text) for d, kws in domain_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def extract_qa_pairs(turns: list[ConversationTurn]) -> list[QAPair]:
    """Pair adjacent user→assistant turns."""
    pairs: list[QAPair] = []
    i = 0
    while i < len(turns) - 1:
        if turns[i].speaker == "user" and turns[i + 1].speaker == "assistant":
            pairs.append(QAPair(
                question=turns[i].content[:500],
                answer=turns[i + 1].content[:1000],
                turn_index=i,
            ))
            i += 2
        else:
            i += 1
    return pairs


def _extract_by_cues(text: str, cues: list[str], context_chars: int = 200) -> list[str]:
    """Find lines containing cue phrases, return with surrounding context."""
    out: list[str] = []
    text_lower = text.lower()
    seen: set[str] = set()
    for cue in cues:
        cue_lower = cue.lower()
        start = 0
        while True:
            pos = text_lower.find(cue_lower, start)
            if pos == -1:
                break
            # Extract sentence containing this cue
            line_start = text.rfind("\n", 0, pos)
            line_end = text.find("\n", pos)
            if line_start == -1:
                line_start = 0
            if line_end == -1:
                line_end = len(text)
            snippet = text[line_start:line_end].strip()
            if snippet and len(snippet) > 10 and snippet not in seen:
                out.append(snippet[:context_chars])
                seen.add(snippet)
            start = pos + len(cue_lower)
    return out[:20]  # cap


def extract_decisions(transcript: str) -> list[str]:
    return _extract_by_cues(transcript, _DECISION_CUES)


def extract_facts(transcript: str) -> list[str]:
    return _extract_by_cues(transcript, _FACT_CUES)


def extract_open_questions(transcript: str) -> list[str]:
    return _extract_by_cues(transcript, _OPEN_Q_CUES, context_chars=150)


# ── Note generator ───────────────────────────────────────────────────────────

def get_next_note_number(notes_dir: Path) -> int:
    """Find highest existing note number + 1."""
    if not notes_dir.exists():
        return 1
    nums: list[int] = []
    for f in notes_dir.iterdir():
        m = re.match(r"^(\d+)_", f.name)
        if m:
            try:
                nums.append(int(m.group(1)))
            except ValueError:
                continue
    return (max(nums) + 1) if nums else 1


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"-+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len] or "untitled"


def generate_note(result: SynthesisResult, source_label: str) -> str:
    """Format SynthesisResult ke markdown research note."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n = result.note_number

    parts = [
        f"# Note {n} — Conversation Synthesis: {result.topic}",
        "",
        f"**Sanad**: synthesized from external AI session ({source_label}) "
        f"per founder mandate 2026-04-29 — *\"setiap percakapan kita juga harus "
        f"bisa di sintesis sama sidix, kamu sebagai guru.\"*",
        f"**Tanggal**: {today}",
        f"**Domain**: {result.domain}",
        f"**Source guru**: {source_label}",
        f"**Turns**: {result.turn_count} | **Q&A pairs**: {len(result.qa_pairs)} | "
        f"**Word count**: {result.raw_word_count}",
        "",
        "---",
        "",
        "## 1 · Topic & Domain",
        "",
        f"**Topic detected:** {result.topic}",
        f"**Domain classification:** {result.domain}",
        "",
    ]

    if result.decisions:
        parts.extend(["## 2 · Decisions Captured", ""])
        for d in result.decisions[:10]:
            parts.append(f"- {d}")
        parts.append("")

    if result.facts:
        parts.extend(["## 3 · Facts / Claims", ""])
        for f in result.facts[:10]:
            parts.append(f"- {f}")
        parts.append("")

    if result.open_questions:
        parts.extend(["## 4 · Open Questions / TODOs", ""])
        for q in result.open_questions[:10]:
            parts.append(f"- {q}")
        parts.append("")

    if result.qa_pairs:
        parts.extend(["## 5 · Notable Q&A Pairs", ""])
        for i, qa in enumerate(result.qa_pairs[:5], 1):
            parts.extend([
                f"### Pair {i}",
                "",
                f"**Q:** {qa.question[:400].strip()}",
                "",
                f"**A:** {qa.answer[:600].strip()}",
                "",
            ])

    if result.persona_analysis:
        parts.extend(["## 6 · Multi-Persona Analysis (Phase 2 fanout)", ""])
        for persona, analysis in result.persona_analysis.items():
            parts.extend([f"**{persona}**: {analysis}", ""])

    parts.extend([
        "---",
        "",
        "## Sanad chain",
        "",
        f"- Source: {source_label} (external AI as *guru*)",
        f"- Synthesizer: SIDIX conversation_synthesizer.py (Sprint 41)",
        f"- Date: {today}",
        f"- Pattern: founder mandate 2026-04-29 (Conversation Synthesizer / Claude as guru)",
        "",
        "*Auto-generated by SIDIX. Future agent: refine + verify claims sebelum quote sebagai authoritative.*",
    ])
    return "\n".join(parts)


# ── Public API ───────────────────────────────────────────────────────────────

def synthesize(
    transcript: str,
    source_label: str = "external_ai",
    notes_dir: Optional[Path] = None,
    write_note: bool = True,
    persona_fanout: bool = False,
) -> SynthesisResult:
    """Synthesize a conversation transcript → research note + Hafidz entry.

    Args:
        transcript: full conversation text
        source_label: "claude_code" | "chatgpt" | "gemini" | custom
        notes_dir: target dir (default: brain/public/research_notes)
        write_note: actually write file (False = dry run)
        persona_fanout: invoke 5-persona research (Phase 2)

    Returns:
        SynthesisResult dengan note_path filled jika write_note=True.
    """
    if notes_dir is None:
        notes_dir = Path(__file__).resolve().parent.parent.parent.parent / "brain" / "public" / "research_notes"

    log.info("[convo_synth] source=%s transcript_len=%d", source_label, len(transcript))

    turns = parse_turns(transcript)
    result = SynthesisResult(
        turn_count=len(turns),
        raw_word_count=len(transcript.split()),
    )
    result.topic = detect_topic(turns)
    result.domain = detect_domain(transcript)
    result.qa_pairs = extract_qa_pairs(turns)
    result.decisions = extract_decisions(transcript)
    result.facts = extract_facts(transcript)
    result.open_questions = extract_open_questions(transcript)

    if persona_fanout:
        # Phase 2: invoke persona_research_fanout.gather()
        from . import persona_research_fanout as prf
        bundle = prf.gather(
            task_id=f"convo-{int(datetime.now(timezone.utc).timestamp())}",
            target_path=source_label,
            goal=f"synthesize conversation: {result.topic}",
        )
        result.persona_analysis = {
            p: c.findings[0] if c.findings else ""
            for p, c in bundle.contributions.items()
        }

    result.sanad_chain = [
        {"role": "guru", "name": source_label},
        {"role": "synthesizer", "name": "sidix_conversation_synthesizer"},
        {"role": "verifier", "name": "owner", "verdict": "pending"},
    ]

    if write_note:
        notes_dir.mkdir(parents=True, exist_ok=True)
        result.note_number = get_next_note_number(notes_dir)
        slug = slugify(f"convo_{result.domain}_{result.topic}")
        filename = f"{result.note_number}_{slug}.md"
        path = notes_dir / filename
        path.write_text(generate_note(result, source_label), encoding="utf-8")
        result.note_path = str(path)
        log.info("[convo_synth] wrote note=%s", path)

        # Hafidz Ledger entry
        try:
            from .hafidz_ledger import write_entry
            write_entry(
                content=f"Conversation synthesis from {source_label}: {result.topic}",
                content_id=f"convo-synth-{result.note_number}",
                content_type="conversation_synthesis",
                isnad_chain=result.sanad_chain,
                metadata={
                    "topic": result.topic,
                    "domain": result.domain,
                    "turn_count": result.turn_count,
                    "qa_pairs": len(result.qa_pairs),
                    "decisions": len(result.decisions),
                    "note_path": result.note_path,
                },
                cycle_id=f"convo-synth-{int(datetime.now(timezone.utc).timestamp())}",
            )
        except Exception as e:
            log.debug("[convo_synth] hafidz write skipped: %s", e)

    return result


__all__ = [
    "ConversationTurn", "QAPair", "SynthesisResult",
    "parse_turns", "detect_topic", "detect_domain",
    "extract_qa_pairs", "extract_decisions", "extract_facts",
    "extract_open_questions", "generate_note", "synthesize",
]
