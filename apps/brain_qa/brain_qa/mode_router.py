"""
mode_router.py — SIDIX Mode System Router
==========================================

4 modes: instant | thinking | agent | deep_research
Adopted from Kimi K2.5 (Instant/Thinking/Agent/Agent Swarm) + ChatGPT model picker.

Integration:
  - agent_serve.py: ChatRequest.mode → ModeRouter.classify() → execute
  - ado_state.py: ADOState.mode tracking
  - Frontend: mode toggle + auto-detect + user override

Author: Claude Code | Date: 2026-05-07
"""

from __future__ import annotations

import re
from typing import Optional
from enum import Enum


class SidixMode(str, Enum):
    INSTANT = "instant"
    THINKING = "thinking"
    AGENT = "agent"
    DEEP_RESEARCH = "deep_research"


# ── Mode Configuration ─────────────────────────────────────────────────────────

MODE_CONFIG = {
    SidixMode.INSTANT: {
        "max_tokens": 350,
        "temperature": 0.7,
        "tools": [],
        "persona": "AYMAN",
        "iterations": 0,
        "web_search": False,
        "corpus_search": False,
        "persona_fanout": False,
        "streaming": True,
        "sanad_required": False,
        "recursive_research": False,
    },
    SidixMode.THINKING: {
        "max_tokens": 800,
        "temperature": 0.5,
        "tools": ["code_sandbox", "calculator", "search_corpus"],
        "persona": "auto",
        "iterations": 3,
        "web_search": False,
        "corpus_search": True,
        "persona_fanout": False,
        "streaming": True,
        "sanad_required": True,
        "recursive_research": False,
    },
    SidixMode.AGENT: {
        "max_tokens": 1200,
        "temperature": 0.7,
        "tools": ["web_search", "web_fetch", "search_corpus", "code_sandbox",
                  "calculator", "pdf_extract", "workspace_list", "workspace_read"],
        "persona": "all",
        "iterations": 5,
        "web_search": True,
        "corpus_search": True,
        "dense_search": True,
        "persona_fanout": True,
        "streaming": True,
        "sanad_required": True,
        "recursive_research": False,
    },
    SidixMode.DEEP_RESEARCH: {
        "max_tokens": 2000,
        "temperature": 0.3,
        "tools": ["web_search", "web_fetch", "search_corpus", "code_sandbox",
                  "arxiv_search", "wikipedia_search", "pdf_extract"],
        "persona": "ALEY",
        "iterations": 10,
        "web_search": True,
        "corpus_search": True,
        "dense_search": True,
        "persona_fanout": True,
        "streaming": False,
        "sanad_required": True,
        "recursive_research": True,
    },
}


# ── Keyword-based Classifier ───────────────────────────────────────────────────

_INSTANT_KEYWORDS = re.compile(
    r"\b(halo|hai|hi|hello|hey|selamat\s+(pagi|siang|sore|malam)|"
    r"apa\s+kabar|terima\s+kasih|thanks|makasih|oke|ok|baik|"
    r"sampai\s+jumpa|dadah|bye|see\s+you)\b",
    re.IGNORECASE,
)

_DEEP_RESEARCH_KEYWORDS = re.compile(
    r"\b(laporan|report|analisis\s+menyeluruh|deep\s+research|"
    r"riset\s+komprehensif|due\s+diligence|literature\s+review|"
    r"tinjauan\s+pustaka|benchmark|komparatif\s+lengkap|"
    r"buatkan\s+.*\s+laporan|generate\s+.*\s+report)\b",
    re.IGNORECASE,
)

_THINKING_KEYWORDS = re.compile(
    r"\b(jelaskan|cara\s+kerja|bagaimana|kenapa|mengapa|"
    r"apa\s+itu|definisi|konsep|rumus|hitung|solve|"
    r"code|kode|program|debug|error|fix|algorithm|"
    r"python|javascript|html|css|sql)\b",
    re.IGNORECASE,
)

_SIMPLE_FACTUAL = re.compile(
    r"^(berapa|siapa|kapan|dimana|di\s+mana|apa|apakah)\s+",
    re.IGNORECASE,
)


class ModeRouter:
    """Route user query ke mode yang tepat."""

    @staticmethod
    def classify(query: str, override: Optional[str] = None) -> SidixMode:
        """
        Klasifikasikan query ke mode.

        Priority:
        1. User override (/instant, /think, /agent, /deep)
        2. Keyword deep research
        3. Keyword instant
        4. Keyword thinking / simple factual
        5. Default = AGENT
        """
        q = (query or "").strip()

        # 1. User override
        if override:
            try:
                return SidixMode(override.lower())
            except ValueError:
                pass

        # Slash commands in query
        lower_q = q.lower()
        if lower_q.startswith("/instant"):
            return SidixMode.INSTANT
        if lower_q.startswith("/think"):
            return SidixMode.THINKING
        if lower_q.startswith("/agent"):
            return SidixMode.AGENT
        if lower_q.startswith("/deep"):
            return SidixMode.DEEP_RESEARCH

        # 2. Deep research
        if _DEEP_RESEARCH_KEYWORDS.search(q):
            return SidixMode.DEEP_RESEARCH

        # 3. Instant (greeting / very short)
        if len(q) < 30 and _INSTANT_KEYWORDS.search(q):
            return SidixMode.INSTANT

        # 4. Thinking (coding / explanation / simple factual)
        if _THINKING_KEYWORDS.search(q) or _SIMPLE_FACTUAL.match(q):
            return SidixMode.THINKING

        # 5. Default
        return SidixMode.AGENT

    @staticmethod
    def get_config(mode: SidixMode) -> dict:
        """Ambil konfigurasi untuk mode."""
        return MODE_CONFIG.get(mode, MODE_CONFIG[SidixMode.AGENT]).copy()

    @staticmethod
    def detect_persona(query: str) -> str:
        """Auto-detect persona untuk mode THINKING."""
        q = query.lower()
        if any(k in q for k in ["code", "kode", "program", "debug", "algorithm", "python", "javascript", "sql", "api", "backend", "frontend"]):
            return "ABOO"
        if any(k in q for k in ["logo", "design", "warna", "gambar", "copywriting", "brand", "kreatif", "visual", "art", "musik", "seni"]):
            return "UTZ"
        if any(k in q for k in ["strategi", "bisnis", "marketing", "revenue", "gtm", "roadmap", "plan", "investor", "startup", "umkm"]):
            return "OOMAR"
        if any(k in q for k in ["paper", "jurnal", "penelitian", "studies", "evidence", "arxiv", "science", "research", "literature"]):
            return "ALEY"
        return "AYMAN"

    @staticmethod
    def strip_override(query: str) -> str:
        """Hapus slash command dari query."""
        q = query.strip()
        for cmd in ["/instant ", "/think ", "/agent ", "/deep "]:
            if q.lower().startswith(cmd):
                return q[len(cmd):].strip()
        return q


def resolve_mode(query: str, override: Optional[str] = None) -> tuple[SidixMode, dict]:
    """
    Convenience: classify + get_config dalam satu call.
    Returns: (mode, config_dict)
    """
    router = ModeRouter()
    mode = router.classify(query, override)
    config = router.get_config(mode)

    if mode == SidixMode.THINKING and config.get("persona") == "auto":
        config["persona"] = router.detect_persona(query)

    return mode, config


__all__ = [
    "SidixMode",
    "MODE_CONFIG",
    "ModeRouter",
    "resolve_mode",
]
