"""
hafidz_injector.py — Hafidz Memory Injection Engine (Sprint B)

Arsitektur:
  Hafidz Injector = memory retrieval + injection + storage untuk SIDIX.
  
  Konsep "Two-Drawer" (dari visi bos):
    - Golden Store: Q&A berkualitas tinggi (sanad >= threshold) → inject ke OTAK sebagai few-shot
    - Lesson Store: SEMUA output + failure metadata → negative filter untuk Sanad
  
  Flow:
    Pre-query:
      1. Search Golden Store untuk similar past queries (BM25 + persona filter)
      2. Search Lesson Store untuk failure patterns (what NOT to do)
      3. Search Pattern Store untuk domain-relevant patterns
      4. Inject ke system prompt sebagai few-shot context
    
    Post-query:
      1. Receive query, answer, sanad_score
      2. If sanad_score >= threshold → Golden Store
      3. If sanad_score < threshold → Lesson Store (with failure metadata)
      4. Trigger async re-index

  Storage:
    - Golden: brain/public/hafidz/golden/YYYY-MM-DD/<id>.md
    - Lesson: brain/public/hafidz/lesson/YYYY-MM-DD/<id>.md
    - Patterns: brain/public/hafidz/patterns/<domain>.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("sidix.hafidz")


# ── Storage Roots ────────────────────────────────────────────────────────

DEFAULT_HAFIDZ_ROOT = Path("brain/public/hafidz")
GOLDEN_ROOT = DEFAULT_HAFIDZ_ROOT / "golden"
LESSON_ROOT = DEFAULT_HAFIDZ_ROOT / "lesson"
PATTERN_ROOT = DEFAULT_HAFIDZ_ROOT / "patterns"

# Also search legacy knowledge accumulator for backward compat
LEGACY_KNOWLEDGE_ROOT = Path("brain/public/omnyx_knowledge")
LEGACY_PERSONA_CORPUS = Path("brain/public/persona_corpus")


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class HafidzExample:
    """A single example from Golden Store."""
    query: str
    answer: str
    persona: str
    sanad_score: float
    sources_used: list[str]
    date: str
    knowledge_id: str


@dataclass
class HafidzLesson:
    """A single lesson from Lesson Store."""
    query: str
    answer: str
    persona: str
    sanad_score: float
    failure_context: str
    tools_used: list[str]
    date: str
    knowledge_id: str


@dataclass
class HafidzContext:
    """Context to inject into prompt."""
    golden_examples: list[HafidzExample] = field(default_factory=list)
    lesson_warnings: list[HafidzLesson] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)  # Sprint C: extracted patterns


# ── Storage Helpers ──────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    """Ensure all Hafidz directories exist."""
    for d in [GOLDEN_ROOT, LESSON_ROOT, PATTERN_ROOT]:
        d.mkdir(parents=True, exist_ok=True)


def _generate_id(query: str, answer: str) -> str:
    """Generate unique ID for Hafidz entry."""
    h = hashlib.sha256(f"{query}:{answer}".encode()).hexdigest()[:12]
    return f"hafidz_{h}"


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Golden Store ─────────────────────────────────────────────────────────

async def store_golden(
    query: str,
    answer: str,
    persona: str,
    sanad_score: float,
    sources_used: list[str],
    tools_used: list[str],
    metadata: dict = None,
) -> dict:
    """Store high-quality Q&A to Golden Store."""
    _ensure_dirs()
    
    note_id = _generate_id(query, answer)
    date_str = _today_str()
    now = datetime.now(timezone.utc).isoformat()
    
    frontmatter = f"""---
title: "{query[:100]}"
date: {date_str}
sanad_tier: golden
sanad_score: {sanad_score:.3f}
persona: {persona}
sources: {sources_used}
tools: {tools_used}
knowledge_id: {note_id}
auto_generated: true
store_type: golden
---

# {query}

## Jawaban

{answer}

## Metadata

- **sanad_score**: {sanad_score:.3f}
- **sources_used**: {", ".join(sources_used)}
- **tools_used**: {", ".join(tools_used)}
- **stored_at**: {now}
- **persona**: {persona}
"""
    
    golden_dir = GOLDEN_ROOT / date_str
    golden_dir.mkdir(parents=True, exist_ok=True)
    note_path = golden_dir / f"{note_id}.md"
    note_path.write_text(frontmatter, encoding="utf-8")
    
    log.info("[hafidz] Golden stored: %s (score=%.3f)", note_id, sanad_score)
    
    # Trigger re-index
    asyncio.create_task(_trigger_reindex())
    
    return {"stored": True, "path": str(note_path), "note_id": note_id, "store": "golden"}


# ── Lesson Store ─────────────────────────────────────────────────────────

async def store_lesson(
    query: str,
    answer: str,
    persona: str,
    sanad_score: float,
    failure_context: str,
    sources_used: list[str],
    tools_used: list[str],
    metadata: dict = None,
) -> dict:
    """Store failure case to Lesson Store for negative learning."""
    _ensure_dirs()
    
    note_id = _generate_id(query, answer)
    date_str = _today_str()
    now = datetime.now(timezone.utc).isoformat()
    
    frontmatter = f"""---
title: "{query[:100]}"
date: {date_str}
sanad_tier: lesson
sanad_score: {sanad_score:.3f}
persona: {persona}
sources: {sources_used}
tools: {tools_used}
knowledge_id: {note_id}
auto_generated: true
store_type: lesson
failure_context: |
  {failure_context}
---

# {query}

## Jawaban (FAILED)

{answer}

## Failure Context

{failure_context}

## Metadata

- **sanad_score**: {sanad_score:.3f}
- **failure_context**: {failure_context[:200]}
- **sources_used**: {", ".join(sources_used)}
- **tools_used**: {", ".join(tools_used)}
- **stored_at**: {now}
- **persona**: {persona}
"""
    
    lesson_dir = LESSON_ROOT / date_str
    lesson_dir.mkdir(parents=True, exist_ok=True)
    note_path = lesson_dir / f"{note_id}.md"
    note_path.write_text(frontmatter, encoding="utf-8")
    
    log.info("[hafidz] Lesson stored: %s (score=%.3f)", note_id, sanad_score)
    
    # Trigger re-index
    asyncio.create_task(_trigger_reindex())
    
    return {"stored": True, "path": str(note_path), "note_id": note_id, "store": "lesson"}


# ── Retrieval ────────────────────────────────────────────────────────────

def _bm25_search(query: str, docs: list[Path], top_k: int = 5) -> list[tuple[Path, float]]:
    """Simple BM25-like scoring for document ranking."""
    if not docs:
        return []
    
    query_terms = set(re.findall(r'\w{3,}', query.lower()))
    if not query_terms:
        return []
    
    scored = []
    for doc in docs:
        try:
            content = doc.read_text(encoding="utf-8").lower()
            doc_terms = set(re.findall(r'\w{3,}', content))
            
            # Simple overlap scoring
            overlap = len(query_terms & doc_terms)
            score = overlap / max(len(query_terms), 1)
            
            if score > 0.1:  # minimum relevance
                scored.append((doc, score))
        except Exception:
            continue
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def _parse_hafidz_note(path: Path) -> Optional[dict]:
    """Parse a Hafidz note file into dict."""
    try:
        content = path.read_text(encoding="utf-8")
        
        # Extract frontmatter
        fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not fm_match:
            return None
        
        fm_text = fm_match.group(1)
        
        # Parse simple key: value frontmatter
        metadata = {}
        for line in fm_text.split('\n'):
            if ':' in line and not line.startswith('#'):
                key, val = line.split(':', 1)
                metadata[key.strip()] = val.strip()
        
        # Extract query (first h1)
        query_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        query = query_match.group(1) if query_match else ""
        
        # Extract answer (between ## Jawaban and next ##)
        answer_match = re.search(r'## Jawaban\n\n(.*?)(?:\n## |\Z)', content, re.DOTALL)
        answer = answer_match.group(1) if answer_match else ""
        
        return {
            "path": str(path),
            "query": query,
            "answer": answer,
            "metadata": metadata,
            "content": content,
        }
    except Exception as e:
        log.debug("[hafidz] Parse failed for %s: %s", path, e)
        return None


def _get_all_docs(root: Path) -> list[Path]:
    """Get all markdown docs under root recursively."""
    if not root.exists():
        return []
    return list(root.rglob("*.md"))


async def retrieve_golden_examples(
    query: str,
    persona: str,
    max_examples: int = 3,
    min_score: float = 0.80,
) -> list[HafidzExample]:
    """Retrieve high-quality examples from Golden Store."""
    _ensure_dirs()
    
    # Search both Hafidz Golden and legacy knowledge accumulator
    all_docs = _get_all_docs(GOLDEN_ROOT) + _get_all_docs(LEGACY_KNOWLEDGE_ROOT)
    
    # Filter by persona if specified
    if persona:
        persona_lower = persona.lower()
        all_docs = [d for d in all_docs if persona_lower in d.read_text(encoding="utf-8").lower()]
    
    # BM25 search
    ranked = _bm25_search(query, all_docs, top_k=max_examples * 2)
    
    examples = []
    for path, score in ranked:
        parsed = _parse_hafidz_note(path)
        if not parsed:
            continue
        
        # Check sanad_score from metadata
        meta = parsed.get("metadata", {})
        sanad_score_str = meta.get("sanad_score", "0.5")
        try:
            sanad_score = float(sanad_score_str)
        except (ValueError, TypeError):
            sanad_score = 0.5
        
        # Skip if below minimum score
        if sanad_score < min_score:
            continue
        
        # Parse sources
        sources_str = meta.get("sources", "[]")
        try:
            sources = json.loads(sources_str.replace("'", '"'))
        except (json.JSONDecodeError, ValueError):
            sources = sources_str.strip("[]").split(", ") if sources_str != "[]" else []
        
        examples.append(HafidzExample(
            query=parsed.get("query", ""),
            answer=parsed.get("answer", ""),
            persona=meta.get("persona", persona),
            sanad_score=sanad_score,
            sources_used=sources if isinstance(sources, list) else [],
            date=meta.get("date", _today_str()),
            knowledge_id=meta.get("knowledge_id", ""),
        ))
        
        if len(examples) >= max_examples:
            break
    
    log.info("[hafidz] Retrieved %d golden examples for %r", len(examples), query[:60])
    return examples


async def retrieve_lesson_warnings(
    query: str,
    persona: str,
    max_warnings: int = 2,
) -> list[HafidzLesson]:
    """Retrieve failure patterns from Lesson Store (what NOT to do)."""
    _ensure_dirs()
    
    all_docs = _get_all_docs(LESSON_ROOT)
    
    # Filter by persona
    if persona:
        persona_lower = persona.lower()
        all_docs = [d for d in all_docs if persona_lower in d.read_text(encoding="utf-8").lower()]
    
    # BM25 search
    ranked = _bm25_search(query, all_docs, top_k=max_warnings * 2)
    
    lessons = []
    for path, score in ranked:
        parsed = _parse_hafidz_note(path)
        if not parsed:
            continue
        
        meta = parsed.get("metadata", {})
        sanad_score_str = meta.get("sanad_score", "0.3")
        try:
            sanad_score = float(sanad_score_str)
        except (ValueError, TypeError):
            sanad_score = 0.3
        
        failure = meta.get("failure_context", "Unknown failure")
        
        lessons.append(HafidzLesson(
            query=parsed.get("query", ""),
            answer=parsed.get("answer", ""),
            persona=meta.get("persona", persona),
            sanad_score=sanad_score,
            failure_context=failure,
            tools_used=[],
            date=meta.get("date", _today_str()),
            knowledge_id=meta.get("knowledge_id", ""),
        ))
        
        if len(lessons) >= max_warnings:
            break
    
    log.info("[hafidz] Retrieved %d lesson warnings for %r", len(lessons), query[:60])
    return lessons


# ── Context Injection ────────────────────────────────────────────────────

def build_hafidz_prompt(context: HafidzContext) -> str:
    """Build prompt injection string from Hafidz context."""
    lines = []
    
    # Golden examples (few-shot)
    if context.golden_examples:
        lines.append("## CONTOH BERKUALITAS TINGGI (dari pengalaman sebelumnya)")
        for i, ex in enumerate(context.golden_examples, 1):
            lines.append(f"\n**Contoh {i}** (score: {ex.sanad_score:.2f}):")
            lines.append(f"Q: {ex.query}")
            lines.append(f"A: {ex.answer[:500]}")
        lines.append("\n---\n")
    
    # Lesson warnings (negative filter)
    if context.lesson_warnings:
        lines.append("## PERINGATAN: Hindari kesalahan berikut")
        for i, lesson in enumerate(context.lesson_warnings, 1):
            lines.append(f"\n**Kesalahan {i}** (score: {lesson.sanad_score:.2f}):")
            lines.append(f"Q: {lesson.query}")
            lines.append(f"Masalah: {lesson.failure_context[:300]}")
        lines.append("\n---\n")
    
    # Sprint C: Extracted patterns (inductive generalizations)
    if context.patterns:
        lines.append("## POLA / PRINSIP RELEVAN (dari pengalaman sebelumnya)")
        for i, pat in enumerate(context.patterns, 1):
            principle = pat.get("extracted_principle", "")
            domain = ", ".join(pat.get("applicable_domain", []))
            conf = pat.get("confidence", 0.5)
            lines.append(f"\n**Pola {i}** ({domain}, confidence: {conf:.2f}):")
            lines.append(f"{principle[:300]}")
        lines.append("\n---\n")
    
    return "\n".join(lines)


# ── Main Injector Class ──────────────────────────────────────────────────

class HafidzInjector:
    """Injects few-shot context from Golden/Lesson Store to prompt."""
    
    def __init__(self):
        self.stats = {"retrievals": 0, "stores": 0}
    
    async def retrieve_context(
        self,
        query: str,
        persona: str,
        max_examples: int = 3,
        max_warnings: int = 2,
        max_patterns: int = 3,  # Sprint C
    ) -> HafidzContext:
        """Retrieve context for injection into prompt."""
        golden = await retrieve_golden_examples(query, persona, max_examples)
        warnings = await retrieve_lesson_warnings(query, persona, max_warnings)
        
        # Sprint C: Retrieve relevant patterns
        patterns = []
        try:
            from .pattern_extractor import search_patterns
            patterns = search_patterns(query, top_k=max_patterns, min_confidence=0.4)
            if patterns:
                log.info("[hafidz] Retrieved %d patterns for %r", len(patterns), query[:60])
        except Exception as e:
            log.debug("[hafidz] Pattern retrieval failed: %s", e)
        
        self.stats["retrievals"] += 1
        
        return HafidzContext(
            golden_examples=golden,
            lesson_warnings=warnings,
            patterns=patterns,
        )
    
    async def store_result(
        self,
        query: str,
        answer: str,
        persona: str,
        sanad_score: float,
        threshold: float,
        sources_used: list[str],
        tools_used: list[str],
        failure_context: str = "",
        metadata: dict = None,
    ) -> dict:
        """Store result to Golden Store (score >= threshold) or Lesson Store (score < threshold)."""
        if sanad_score >= threshold:
            result = await store_golden(
                query=query,
                answer=answer,
                persona=persona,
                sanad_score=sanad_score,
                sources_used=sources_used,
                tools_used=tools_used,
                metadata=metadata,
            )
        else:
            result = await store_lesson(
                query=query,
                answer=answer,
                persona=persona,
                sanad_score=sanad_score,
                failure_context=failure_context or f"Score {sanad_score:.2f} below threshold {threshold:.2f}",
                sources_used=sources_used,
                tools_used=tools_used,
                metadata=metadata,
            )
        
        self.stats["stores"] += 1
        return result
    
    def get_stats(self) -> dict:
        return self.stats


# ── Re-index trigger ─────────────────────────────────────────────────────

async def _trigger_reindex() -> None:
    """Trigger BM25 re-index asynchronously (non-blocking)."""
    try:
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "brain_qa", "index",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=30.0)
    except Exception as e:
        log.debug("[hafidz] Re-index trigger failed: %s", e)


# ── Public API ───────────────────────────────────────────────────────────

async def get_hafidz_context(
    query: str,
    persona: str = "UTZ",
    max_examples: int = 3,
) -> HafidzContext:
    """Convenience function to retrieve Hafidz context."""
    injector = HafidzInjector()
    return await injector.retrieve_context(query, persona, max_examples)


async def store_to_hafidz(
    query: str,
    answer: str,
    persona: str,
    sanad_score: float,
    threshold: float,
    sources_used: list[str] = None,
    tools_used: list[str] = None,
    failure_context: str = "",
) -> dict:
    """Convenience function to store result to Hafidz."""
    injector = HafidzInjector()
    return await injector.store_result(
        query=query,
        answer=answer,
        persona=persona,
        sanad_score=sanad_score,
        threshold=threshold,
        sources_used=sources_used or [],
        tools_used=tools_used or [],
        failure_context=failure_context,
    )
