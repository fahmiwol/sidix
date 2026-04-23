"""
Jiwa — Master Orchestrator (7 Pilar Kemandirian SIDIX)

Digunakan oleh agent_react.py sebagai pengganti _response_blend_profile()
dan sebagai post-response hook.

Usage:
    from brain_qa.jiwa.orchestrator import jiwa

    # Di _response_blend_profile():
    profile = jiwa.nafs.route(question, persona, corpus_only=corpus_only)

    # Setelah final_answer terbentuk:
    jiwa.post_response(question, final_answer, persona, topic=profile.topic)
"""

from __future__ import annotations

import logging

from .nafs import NafsRouter, NafsProfile
from .hayat import hayat_refine
from .aql import aql_on_response
from .qalb import start_monitoring, get_monitor

log = logging.getLogger("sidix.jiwa")


class JiwaOrchestrator:
    """
    Orchestrator 7 Pilar — entry point tunggal dari agent_react.

    Pilar 1  Nafs  — route(): topic routing + persona jiwa
    Pilar 2  Aql   — post_response(): fire-and-forget learning
    Pilar 3  Qalb  — background monitor (auto-start)
    Pilar 4  Ruh   — delegates to daily_growth.py (sudah ada)
    Pilar 5  Hayat — refine(): self-iteration CQF loop
    Pilar 6  Ilm   — delegates to learn_agent.py (sudah ada)
    Pilar 7  Hikmah— delegates to auto_lora.py (sudah ada)
    """

    def __init__(self):
        self.nafs = NafsRouter()
        self._qalb = get_monitor()
        # Auto-start background health monitor
        try:
            start_monitoring()
        except Exception:
            pass

    # ── Pilar 1: Nafs ──────────────────────────────────────────────────────

    def route(
        self, question: str, persona: str, *, corpus_only: bool = False
    ) -> NafsProfile:
        """Deteksi topik → kembalikan NafsProfile untuk agent_react."""
        return self.nafs.route(question, persona, corpus_only=corpus_only)

    # ── Pilar 5: Hayat ─────────────────────────────────────────────────────

    def refine(
        self,
        *,
        question: str,
        answer: str,
        generate_fn,
        topic: str = "umum",
        hayat_enabled: bool = True,
    ) -> str:
        """
        Self-iterate jawaban. Kembalikan jawaban terbaik.
        Non-blocking bila iteration gagal → fallback ke `answer` asli.
        """
        if not hayat_enabled:
            return answer

        # Pilih domain CQF berdasarkan topik
        domain_map = {
            "kreatif": "copywriting",
            "koding": "generic",
            "agama": "education",
            "etika": "education",
            "sidix_internal": "education",
        }
        domain = domain_map.get(topic, "generic")

        result = hayat_refine(
            question=question,
            initial_answer=answer,
            generate_fn=generate_fn,
            domain=domain,
        )
        return result["final"]

    # ── Pilar 2: Aql ───────────────────────────────────────────────────────

    def post_response(
        self,
        question: str,
        answer: str,
        persona: str,
        *,
        topic: str = "umum",
        platform: str = "direct",
        cqf_score: float = 0.0,
    ) -> None:
        """
        Fire-and-forget post-response hook.
        Dipanggil setelah session.final_answer di-set — tidak blocking.
        """
        aql_on_response(
            question=question,
            answer=answer,
            persona=persona,
            topic=topic,
            platform=platform,
            cqf_score=cqf_score,
        )

    # ── Pilar 3: Qalb ──────────────────────────────────────────────────────

    @property
    def health(self) -> str:
        return self._qalb.current_health.value


# Singleton
jiwa = JiwaOrchestrator()
