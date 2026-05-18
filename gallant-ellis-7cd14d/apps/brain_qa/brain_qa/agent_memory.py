"""
agent_memory.py — Multi-Layer Memory System untuk SIDIX 2.0

Arsitektur memory terinspirasi Hermes Agent + neuroscience layered memory:
- Working Memory: konteks sesi saat ini (conversation context, steps)
- Episodic Memory: pengalaman spesifik, lessons learned (praxis, experience_engine)
- Semantic Memory: fakta, konsep, relasi jangka panjang (corpus BM25 + knowledge graph)
- Procedural Memory: skill, pattern, cara bertindak yang terbukti berhasil (skill_library)

Integration:
  - Working: injected ke setiap ReAct step via conversation_context
  - Episodic: loaded saat init session, relevan dengan query
  - Semantic: via search_corpus + graph_search
  - Procedural: via skill_library search
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Layer config
_MAX_WORKING_TURNS = 10
_MAX_EPISODIC_RECALL = 5
_MAX_SEMANTIC_HITS = 5
_MAX_PROCEDURAL_SKILLS = 3


@dataclass
class MemoryLayer:
    name: str
    content: str
    relevance_score: float = 0.0
    source: str = ""


@dataclass
class MultiLayerMemory:
    working: list[MemoryLayer] = field(default_factory=list)
    episodic: list[MemoryLayer] = field(default_factory=list)
    semantic: list[MemoryLayer] = field(default_factory=list)
    procedural: list[MemoryLayer] = field(default_factory=list)

    def to_context_string(self, max_chars: int = 4000) -> str:
        """Gabungkan semua layer jadi satu context string untuk LLM."""
        parts: list[str] = []
        for layer_name, items in [
            ("WORKING MEMORY (current session)", self.working),
            ("EPISODIC MEMORY (past experiences)", self.episodic),
            ("SEMANTIC MEMORY (knowledge base)", self.semantic),
            ("PROCEDURAL MEMORY (skills & patterns)", self.procedural),
        ]:
            if not items:
                continue
            layer_parts = [f"[{layer_name}]"]
            for item in items:
                tag = f"[{item.source}]" if item.source else ""
                layer_parts.append(f"  {tag} {item.content[:500]}")
            parts.append("\n".join(layer_parts))

        combined = "\n\n".join(parts)
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "\n... [memory truncated]"
        return combined

    def to_dict(self) -> dict[str, Any]:
        return {
            "working": [{"name": m.name, "content": m.content[:200], "score": m.relevance_score} for m in self.working],
            "episodic": [{"name": m.name, "content": m.content[:200], "score": m.relevance_score} for m in self.episodic],
            "semantic": [{"name": m.name, "content": m.content[:200], "score": m.relevance_score} for m in self.semantic],
            "procedural": [{"name": m.name, "content": m.content[:200], "score": m.relevance_score} for m in self.procedural],
        }


def _load_working_memory(conversation_context: list[dict] | None) -> list[MemoryLayer]:
    """Extract working memory dari conversation context."""
    if not conversation_context:
        return []
    # Ambil N turn terakhir
    recent = conversation_context[-_MAX_WORKING_TURNS:]
    layers = []
    for turn in recent:
        role = turn.get("role", "unknown")
        content = turn.get("content", "")[:300]
        layers.append(MemoryLayer(
            name=f"turn_{role}",
            content=f"{role}: {content}",
            relevance_score=1.0,
            source="conversation",
        ))
    return layers


def _load_episodic_memory(query: str, persona: str = "UTZ") -> list[MemoryLayer]:
    """Recall episodic memory: praxis lessons + experience patterns."""
    layers: list[MemoryLayer] = []

    # 1. Experience engine
    try:
        from .experience_engine import get_experience_engine
        exp = get_experience_engine()
        exp_text = exp.synthesize(query, top_k=_MAX_EPISODIC_RECALL)
        if exp_text and "Tidak ditemukan" not in exp_text:
            layers.append(MemoryLayer(
                name="experience_patterns",
                content=exp_text[:800],
                relevance_score=0.85,
                source="experience_engine",
            ))
    except Exception as e:
        logger.debug(f"[Memory] ExperienceEngine skip: {e}")

    # 2. Praxis lessons (recent + relevant)
    try:
        lessons_dir = Path(__file__).resolve().parent.parent / "brain" / "public" / "praxis" / "lessons"
        if lessons_dir.exists():
            lesson_files = sorted(lessons_dir.glob("lesson_*.md"), reverse=True)[:_MAX_EPISODIC_RECALL]
            for lf in lesson_files:
                try:
                    content = lf.read_text(encoding="utf-8")[:600]
                    layers.append(MemoryLayer(
                        name=f"praxis_{lf.stem}",
                        content=content,
                        relevance_score=0.75,
                        source="praxis",
                    ))
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"[Memory] Praxis lessons skip: {e}")

    return layers


def _load_semantic_memory(query: str, persona: str = "UTZ") -> list[MemoryLayer]:
    """Recall semantic memory: corpus BM25 hits."""
    layers: list[MemoryLayer] = []

    try:
        from .agent_tools import call_tool
        result = call_tool(
            tool_name="search_corpus",
            args={"query": query, "k": _MAX_SEMANTIC_HITS, "persona": persona},
            session_id="memory_recall",
            step=0,
        )
        if result.success and result.output:
            layers.append(MemoryLayer(
                name="corpus_bm25",
                content=result.output[:1200],
                relevance_score=0.9,
                source="corpus",
            ))
    except Exception as e:
        logger.debug(f"[Memory] Corpus search skip: {e}")

    return layers


def _load_procedural_memory(query: str) -> list[MemoryLayer]:
    """Recall procedural memory: relevant skills."""
    layers: list[MemoryLayer] = []

    try:
        from .skill_library import get_skill_library
        skills = get_skill_library()
        skill_text = skills.search_skills(query, top_k=_MAX_PROCEDURAL_SKILLS)
        if skill_text and "Tidak ditemukan" not in skill_text:
            layers.append(MemoryLayer(
                name="relevant_skills",
                content=skill_text[:600],
                relevance_score=0.8,
                source="skill_library",
            ))
    except Exception as e:
        logger.debug(f"[Memory] SkillLibrary skip: {e}")

    return layers


def build_multi_layer_memory(
    query: str,
    *,
    conversation_context: list[dict] | None = None,
    persona: str = "UTZ",
) -> MultiLayerMemory:
    """
    Build multi-layer memory context untuk satu sesi/agent query.

    Returns MultiLayerMemory yang bisa di-convert ke context string.
    """
    mem = MultiLayerMemory()
    mem.working = _load_working_memory(conversation_context)
    mem.episodic = _load_episodic_memory(query, persona)
    mem.semantic = _load_semantic_memory(query, persona)
    mem.procedural = _load_procedural_memory(query)

    logger.info(
        f"[Memory] Built layers for query='{query[:40]}...' | "
        f"working={len(mem.working)} episodic={len(mem.episodic)} "
        f"semantic={len(mem.semantic)} procedural={len(mem.procedural)}"
    )
    return mem


def inject_memory_to_system_prompt(
    base_system: str,
    memory: MultiLayerMemory,
    max_chars: int = 3000,
) -> str:
    """
    Inject memory context ke system prompt.
    Pattern: base_system + [MEMORY CONTEXT] + base_system continuation.
    """
    mem_ctx = memory.to_context_string(max_chars=max_chars)
    if not mem_ctx.strip():
        return base_system

    combined = (
        f"{base_system}\n\n"
        f"═══ MEMORY CONTEXT ═══\n"
        f"{mem_ctx}\n"
        f"═══ END MEMORY ═══\n\n"
        f"Gunakan memory context di atas sebagai tambahan konteks. "
        f"Jangan terpaku hanya pada memory — pertimbangkan juga pengetahuan model dan kreativitas."
    )
    return combined


# ── Self-learning: auto-create skill from successful pattern ─────────────────

def learn_from_session(
    session_id: str,
    question: str,
    final_answer: str,
    steps: list[Any],
    persona: str,
    success_indicator: float = 0.0,  # 0-1, dari feedback atau confidence
) -> str:
    """
    Ekstrak lesson/skill dari sesi yang sukses dan simpan ke skill_library.

    Returns skill_id kalau berhasil, atau "" kalau tidak layak.
    """
    # Threshold: hanya belajar dari sesi yang cukup baik
    if success_indicator < 0.5:
        logger.debug(f"[Learn] Session {session_id} success={success_indicator:.2f} — skip learning")
        return ""

    try:
        from .skill_library import get_skill_library
        lib = get_skill_library()

        # Extract pattern dari steps
        tools_used = [s.action_name for s in steps if getattr(s, "action_name", "")]
        tool_pattern = " → ".join(tools_used) if tools_used else "direct_answer"

        skill_name = f"pattern_{persona.lower()}_{hash(question) % 10000:04d}"
        skill_desc = f"Pattern: {tool_pattern} | Q: {question[:80]}"
        skill_content = (
            f"# Skill Pattern (auto-generated)\n\n"
            f"Persona: {persona}\n"
            f"Tools used: {tool_pattern}\n"
            f"Question pattern: {question[:200]}\n\n"
            f"## Answer approach\n{final_answer[:800]}\n\n"
            f"## Meta\n- success_score: {success_indicator:.2f}\n"
            f"- created: {datetime.now(timezone.utc).isoformat()}\n"
        )

        skill_id = lib.add(
            name=skill_name,
            description=skill_desc,
            content=skill_content,
            skill_type="auto_pattern",
            domain="general",
            tags=[persona.lower(), "auto_learned", "pattern"],
        )
        logger.info(f"[Learn] Skill created: {skill_id} from session {session_id}")
        return skill_id
    except Exception as e:
        logger.warning(f"[Learn] Failed to learn from session: {e}")
        return ""
