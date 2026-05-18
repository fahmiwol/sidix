"""
knowledge_accumulator.py — OMNYX Knowledge Accumulation Pipeline

Setiap jawaban yang dihasilkan oleh SIDIX (terutama yang confidence tinggi)
secara otomatis disimpan ke corpus sebagai pengetahuan baru.

Fitur:
  1. Auto-store verified answers as corpus notes
  2. Auto-index via BM25 setelah store
  3. Persona-specific knowledge tagging
  4. Daily harvest from web sources
  5. Knowledge deduplication (skip if similar note exists)

File output: brain/public/omnyx_knowledge/YYYY-MM-DD/<note>.md

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("sidix.knowledge")

# Knowledge base root
DEFAULT_KNOWLEDGE_ROOT = Path("brain/public/omnyx_knowledge")
PERSONA_CORPUS_ROOT = Path("brain/public/persona_corpus")


async def store_knowledge(
    question: str,
    answer: str,
    sources: list[str],
    persona: str = "OMNYX",
    confidence: str = "sedang",
) -> dict:
    """Store a verified answer to the knowledge corpus.

    Returns {"stored": bool, "path": str, "note_id": str}
    """
    # Check for duplicates
    if _is_duplicate(question, answer):
        log.info("[knowledge] Duplicate detected, skipping store")
        return {"stored": False, "reason": "duplicate", "path": None}

    # Build note content
    note_id = _generate_note_id(question)
    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Sanitize content
    clean_question = _sanitize(question)
    clean_answer = _sanitize(answer)
    source_tags = _extract_tags(question, answer, sources)

    frontmatter = f"""---
title: "{clean_question[:100]}"
date: {date_str}
sanad_tier: sekunder
source: omnyx_synthesis
persona: {persona}
confidence: {confidence}
tags: {source_tags}
knowledge_id: {note_id}
---

# {clean_question}

## Jawaban

{clean_answer}

## Sumber

- {", ".join(sources)}
- Dihasilkan oleh: OMNYX Direction ({persona})
- Waktu: {now}

## Metadata OMNYX

- **knowledge_id**: {note_id}
- **auto_generated**: true
- **verification_status**: {confidence}
- **persona_origin**: {persona}
"""

    # Write to knowledge root
    knowledge_root = DEFAULT_KNOWLEDGE_ROOT / date_str
    knowledge_root.mkdir(parents=True, exist_ok=True)
    note_path = knowledge_root / f"{note_id}.md"
    note_path.write_text(frontmatter, encoding="utf-8")

    # Also write to persona-specific corpus if applicable
    if persona and persona.upper() in ("UTZ", "ABOO", "ALEY", "AYMAN", "OOMAR"):
        persona_dir = PERSONA_CORPUS_ROOT / persona.lower()
        persona_dir.mkdir(parents=True, exist_ok=True)
        persona_path = persona_dir / f"{note_id}.md"
        persona_path.write_text(frontmatter, encoding="utf-8")

    # Trigger re-index (async, non-blocking)
    asyncio.create_task(_trigger_reindex())

    log.info("[knowledge] Stored: %s → %s", note_id, note_path)
    return {
        "stored": True,
        "path": str(note_path),
        "persona_path": str(persona_path) if persona else None,
        "note_id": note_id,
    }


def _generate_note_id(question: str) -> str:
    """Generate short hash-based note ID."""
    h = hashlib.sha256(question.encode()).hexdigest()[:12]
    return f"omnyx_{h}"


def _sanitize(text: str) -> str:
    """Sanitize text for markdown frontmatter."""
    # Remove YAML delimiter conflicts
    text = text.replace("---", "—")
    # Escape quotes for frontmatter
    text = text.replace('"', '\\"')
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_tags(question: str, answer: str, sources: list[str]) -> str:
    """Extract relevant tags from content."""
    tags = set()

    # Persona tags
    for p in ["UTZ", "ABOO", "ALEY", "AYMAN", "OOMAR"]:
        if p.lower() in question.lower() or p.lower() in answer.lower():
            tags.add(p.lower())

    # Domain tags (simple heuristics)
    domain_keywords = {
        "politik": ["presiden", "wapres", "menteri", "pemilu", "dpr"],
        "teknologi": ["ai", "machine learning", "coding", "program", "software"],
        "ekonomi": ["ekonomi", "inflasi", "gdp", "rupiah", "saham"],
        "sains": ["fisika", "kimia", "biologi", "matematika", "sains"],
        "agama": ["islam", "quran", "hadits", "fiqih", "tauhid"],
        "sejarah": ["sejarah", "kerajaan", "kolonial", "kemerdekaan"],
        "kesehatan": ["kesehatan", "penyakit", "obat", "dokter", "rumah sakit"],
        "olahraga": ["bola", "badminton", "sepak", "olahraga", "kejuaraan"],
    }

    combined = f"{question} {answer}".lower()
    for domain, keywords in domain_keywords.items():
        if any(kw in combined for kw in keywords):
            tags.add(domain)

    # Source-based tags
    for src in sources:
        if "web" in src.lower():
            tags.add("web_sourced")
        if "corpus" in src.lower():
            tags.add("corpus_sourced")

    # Default
    if not tags:
        tags.add("general")

    return str(list(sorted(tags)))


def _is_duplicate(question: str, answer: str) -> bool:
    """Check if similar note already exists."""
    q_hash = hashlib.sha256(question.encode()).hexdigest()[:12]
    # Simple check: look for existing note with same hash prefix
    for root in [DEFAULT_KNOWLEDGE_ROOT, PERSONA_CORPUS_ROOT]:
        if not root.exists():
            continue
        for pattern in [f"**/*{q_hash}*", f"**/*omnyx_*"]:
            matches = list(root.glob(pattern))
            if matches:
                # Check similarity (exact question match)
                for m in matches[:3]:
                    content = m.read_text(encoding="utf-8")
                    if question[:80] in content:
                        return True
    return False


async def _trigger_reindex() -> None:
    """Trigger BM25 re-index asynchronously."""
    try:
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "brain_qa", "index",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=30.0)
        log.info("[knowledge] Re-index triggered")
    except Exception as e:
        log.debug("[knowledge] Re-index failed (non-critical): %s", e)


# ── Daily Harvest ────────────────────────────────────────────────────────

async def daily_harvest(
    topics: Optional[list[str]] = None,
    max_notes: int = 10,
) -> dict:
    """Daily knowledge harvest from web sources.

    Auto-generate corpus notes from trending topics or scheduled queries.
    """
    from .multi_source_orchestrator import _src_web_search

    default_topics = topics or [
        "berita Indonesia hari ini",
        "teknologi AI terbaru",
        "ekonomi Indonesia",
        " perkembangan IKN Nusantara",
    ]

    harvested = []
    for topic in default_topics[:max_notes]:
        try:
            result = await _src_web_search(topic)
            if result.get("output"):
                store_result = await store_knowledge(
                    question=topic,
                    answer=result["output"],
                    sources=[result.get("engine", "web")],
                    persona="OMNYX",
                    confidence="sedang",
                )
                harvested.append({
                    "topic": topic,
                    "stored": store_result["stored"],
                    "path": store_result.get("path"),
                })
        except Exception as e:
            log.warning("[harvest] Failed for %s: %s", topic, e)

    log.info("[harvest] Daily harvest complete: %d notes", len(harvested))
    return {"harvested": len(harvested), "notes": harvested}


# ── Persona Brain Management ─────────────────────────────────────────────

def ensure_persona_corpus() -> dict:
    """Ensure persona-specific corpus directories exist.

    Returns mapping of persona → corpus directory.
    """
    personas = ["utz", "aboo", "aley", "ayman", "oomar"]
    mapping = {}
    for p in personas:
        p_dir = PERSONA_CORPUS_ROOT / p
        p_dir.mkdir(parents=True, exist_ok=True)
        # Create README for each persona brain
        readme = p_dir / "README.md"
        if not readme.exists():
            readme.write_text(
                f"""---
title: Persona Brain — {p.upper()}
date: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
persona: {p.upper()}
---

# Otak Persona {p.upper()}

Folder ini berisi pengetahuan khusus yang dihasilkan oleh dan untuk persona {p.upper()}.

- Setiap interaksi dengan persona {p.upper()} akan menambah pengetahuan ke folder ini
- Prioritas BM25: folder persona aktif akan di-query pertama kali
- Tag: persona_{p.lower()}
""",
                encoding="utf-8",
            )
        mapping[p.upper()] = str(p_dir)
    return mapping


# Init on module load
ensure_persona_corpus()
