"""
shadow_pool.py — Jurus 1000 Bayangan (Vol 25 MVP)

User vision (notes 239 + 244): each "shadow" = specialized agent dengan
domain knowledge sendiri. Saat task masuk, shadow yang relevan dispatch
parallel, hasil di-merge via consensus.

MVP scope (small first, scale later):
- 8 specialized shadows (politics, fiqh, code, science, business, tech, indonesian, general)
- Each shadow has:
  - domain tag
  - default search query enrichment
  - preferred LLM teacher (from external_llm_pool)
  - validation strategy

Dispatch flow:
1. Task arrives with {question, hints}
2. relevance_check: each shadow scores its fit (cheap regex+keyword)
3. Top-K shadows (default 3) execute parallel
4. Each shadow: web_search + LLM ask = answer
5. Consensus: cluster claims, vote
6. Return: validated answer + sanad chain

Future Vol 25+:
- Embedding-based fingerprint (replace regex)
- Trust score per shadow (Vol 26)
- Dynamic specialization (shadows learn over time)
- 100+ shadows (current: 8)
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ShadowAgent:
    """One specialized knowledge node."""
    name: str
    domain: str
    keywords: list[str]              # for relevance check (lowercase)
    search_query_template: str = "{question}"   # how to enrich search
    preferred_teachers: list[str] = field(default_factory=lambda: ["ownpod", "gemini"])
    relevance_threshold: float = 0.3

    def relevance(self, question: str) -> float:
        """Cheap score: keyword match ratio."""
        ql = question.lower()
        if not self.keywords:
            return 0.5  # neutral
        hits = sum(1 for kw in self.keywords if kw in ql)
        return min(1.0, hits / max(1, len(self.keywords) // 2))

    async def execute(self, question: str) -> dict:
        """Single shadow: web fetch + LLM ask + return claim."""
        from .external_llm_pool import consensus_async
        t0 = time.time()
        result = {
            "shadow": self.name, "domain": self.domain,
            "question": question, "claim": "", "sources": [],
            "duration_ms": 0, "error": "",
        }
        try:
            # Web context (try brave_search async, then wiki fallback)
            web_ctx = ""
            try:
                from .brave_search import brave_search_async
                hits = await brave_search_async(
                    self.search_query_template.format(question=question),
                    max_results=3,
                )
                if hits:
                    web_ctx = "\n".join(f"- {h.title}: {h.snippet[:200]}" for h in hits[:3])
                    result["sources"] = [{"url": h.url, "title": h.title} for h in hits[:3]]
            except Exception as _e:
                log.debug("[shadow:%s] brave fail: %s", self.name, _e)

            if not web_ctx:
                try:
                    from .wiki_lookup import wiki_lookup_fast
                    wiki_hits = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: wiki_lookup_fast(question, max_articles=2)
                    )
                    if wiki_hits:
                        web_ctx = "\n".join(f"- {h.title}: {h.extract[:300]}" for h in wiki_hits)
                        result["sources"] = [{"url": h.url, "title": h.title} for h in wiki_hits]
                except Exception as _e:
                    log.debug("[shadow:%s] wiki fail: %s", self.name, _e)

            # Ask preferred teachers (parallel)
            sys_prompt = (
                f"Kamu shadow agent SIDIX domain {self.domain}. "
                f"Jawab pertanyaan singkat (max 2 kalimat) berdasarkan KONTEKS WEB di bawah. "
                "Akurat, sertakan tahun/sumber kalau ada. Untuk klaim faktual sensitif, "
                "label [FAKTA] di awal."
            )
            full_q = f"{question}\n\n[KONTEKS]\n{web_ctx[:2000]}" if web_ctx else question
            answers = await consensus_async(
                full_q, persona="ALEY",
                providers=self.preferred_teachers,
                timeout=15.0,
            )
            valid = [a for a in answers if a.text and not a.error]
            if valid:
                # Take longest non-empty as claim
                best = max(valid, key=lambda a: len(a.text))
                result["claim"] = best.text
                result["primary_teacher"] = best.provider
            else:
                result["error"] = "no teacher answered"
        except Exception as e:
            result["error"] = str(e)[:200]

        result["duration_ms"] = int((time.time() - t0) * 1000)
        return result


# ── Default shadow registry (8 specializations) ─────────────────────────────

DEFAULT_SHADOWS: list[ShadowAgent] = [
    ShadowAgent(
        name="shadow_id_politics",
        domain="indonesian_politics",
        keywords=["presiden", "menteri", "pemilu", "kpu", "indonesia", "jakarta", "dpr", "mpr"],
        search_query_template="{question} site:kompas.com OR site:tempo.co OR site:detik.com",
    ),
    ShadowAgent(
        name="shadow_fiqh",
        domain="islamic_fiqh",
        keywords=["fiqh", "hukum", "puasa", "shalat", "haji", "zakat", "halal", "haram", "mazhab", "hadith"],
        search_query_template="{question} fiqh mazhab hadith",
    ),
    ShadowAgent(
        name="shadow_code",
        domain="programming",
        keywords=["python", "javascript", "code", "function", "async", "api", "git", "library", "framework"],
        search_query_template="{question} stackoverflow OR github",
    ),
    ShadowAgent(
        name="shadow_science",
        domain="science_research",
        keywords=["paper", "study", "research", "physics", "biology", "chemistry", "neuroscience", "arxiv"],
        search_query_template="{question} arxiv OR pubmed",
    ),
    ShadowAgent(
        name="shadow_business",
        domain="business_strategy",
        keywords=["bisnis", "strategi", "marketing", "saas", "startup", "funding", "valuation", "b2b"],
        search_query_template="{question} business strategy",
    ),
    ShadowAgent(
        name="shadow_tech_news",
        domain="tech_current_events",
        keywords=["tech", "ai", "openai", "anthropic", "google", "rilis", "update", "2024", "2025", "2026"],
        search_query_template="{question} 2024 OR 2025 OR 2026",
    ),
    ShadowAgent(
        name="shadow_indonesia_culture",
        domain="indonesian_culture",
        keywords=["indonesia", "bahasa", "budaya", "kuliner", "wisata", "tradisi", "bali", "jawa"],
        search_query_template="{question} indonesia",
    ),
    ShadowAgent(
        name="shadow_general",
        domain="general_knowledge",
        keywords=[],  # always neutral fit
        search_query_template="{question}",
        relevance_threshold=0.0,  # accepts anything
    ),
]


# ── Dispatcher (jurus 1000 bayangan, MVP version) ───────────────────────────

@dataclass
class ShadowDispatchResult:
    question: str
    contributing_shadows: list[str]
    consensus_claim: str
    all_responses: list[dict]
    total_duration_ms: int


async def dispatch(
    question: str,
    *,
    shadows: Optional[list[ShadowAgent]] = None,
    top_k: int = 3,
    timeout: float = 25.0,
) -> ShadowDispatchResult:
    """
    Jurus 1000 Bayangan: dispatch question ke top-K relevant shadows parallel.

    Per note 239 + 244: only relevant shadows answer, others stay silent.
    Saves compute, increases signal.
    """
    if shadows is None:
        shadows = DEFAULT_SHADOWS

    t_start = time.time()

    # 1. Score relevance, pick top-K
    scored = [(s, s.relevance(question)) for s in shadows]
    scored.sort(key=lambda x: x[1], reverse=True)
    selected = [s for s, score in scored[:top_k] if score >= s.relevance_threshold]
    if not selected:
        # All below threshold → use general shadow only
        selected = [s for s in shadows if s.name == "shadow_general"]

    log.info("[shadow_pool] question=%r selected=%s",
             question[:60], [s.name for s in selected])

    # 2. Execute parallel
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*[s.execute(question) for s in selected],
                           return_exceptions=False),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        log.warning("[shadow_pool] dispatch timeout")
        return ShadowDispatchResult(
            question=question, contributing_shadows=[],
            consensus_claim="", all_responses=[],
            total_duration_ms=int((time.time()-t_start)*1000),
        )

    # 3. Naive consensus: pick claim from shadow with most non-empty + sources
    valid = [r for r in results if r.get("claim") and not r.get("error")]
    consensus_claim = ""
    if valid:
        best = max(valid, key=lambda r: (len(r["sources"]), len(r["claim"])))
        consensus_claim = best["claim"]

    # ── Experience Transfer (Kage Bunshin: pengalaman balik ke yang asli) ──
    # Saat bunshin menghilang, semua pengetahuan transfer balik. SIDIX equivalent:
    # tulis findings ke .data/shadow_experience.jsonl — bisa di-ingest oleh
    # daily_growth ke corpus permanen (LoRA next retrain).
    try:
        import json as _json, os as _os
        from datetime import datetime, timezone
        exp_file = _os.path.join("/opt/sidix/.data", "shadow_experience.jsonl")
        for r in results:
            if r.get("error") or not r.get("claim"):
                continue
            xfer = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "shadow": r["shadow"],
                "domain": r["domain"],
                "question": question,
                "claim": r["claim"][:1500],
                "sources": r["sources"][:5],
                "primary_teacher": r.get("primary_teacher", ""),
                "duration_ms": r["duration_ms"],
                "kind": "shadow_experience",  # marker for daily_growth ingest
            }
            with open(exp_file, "a", encoding="utf-8") as f:
                f.write(_json.dumps(xfer, ensure_ascii=False) + "\n")
        log.info("[shadow_pool] experience transfer: %d shadows persisted", len(valid))
    except Exception as _e:
        log.debug("[shadow_pool] experience transfer error: %s", _e)

    return ShadowDispatchResult(
        question=question,
        contributing_shadows=[r["shadow"] for r in valid],
        consensus_claim=consensus_claim,
        all_responses=results,
        total_duration_ms=int((time.time()-t_start)*1000),
    )


# ── Chakra Budget Tracker (per Naruto canon: chakra dibagi ke setiap clone) ──
# SIDIX equivalent: per-cycle compute budget across providers + API quota.

@dataclass
class ChakraBudget:
    """Track resource budget across shadow dispatches in current window."""
    window_seconds: int = 600  # 10 min sliding
    max_shadow_calls: int = 30  # per window
    max_total_llm_calls: int = 60  # across all teachers
    _calls: list = field(default_factory=list)  # list of (timestamp, shadow_name)

    def can_dispatch(self, n_shadows: int = 3) -> bool:
        self._cleanup()
        return (len(self._calls) + n_shadows) <= self.max_shadow_calls

    def record(self, shadow_names: list[str]):
        now = time.time()
        for name in shadow_names:
            self._calls.append((now, name))
        self._cleanup()

    def _cleanup(self):
        cutoff = time.time() - self.window_seconds
        self._calls = [(t, n) for t, n in self._calls if t >= cutoff]


# Global budget instance (singleton-ish for module-level tracking)
_chakra = ChakraBudget()


def get_chakra_status() -> dict:
    _chakra._cleanup()
    return {
        "active_calls_in_window": len(_chakra._calls),
        "max_per_window": _chakra.max_shadow_calls,
        "window_seconds": _chakra.window_seconds,
        "remaining": _chakra.max_shadow_calls - len(_chakra._calls),
    }


__all__ = [
    "ShadowAgent", "ShadowDispatchResult",
    "DEFAULT_SHADOWS", "dispatch",
    "ChakraBudget", "get_chakra_status",
]
