"""
cognitive_synthesizer.py — Sprint Α (Jurus Seribu Bayangan, synthesis stage)

Setelah multi_source_orchestrator gather paralel, synthesizer ambil semua
output dari multiple sources + merge jadi 1 jawaban utuh dengan attribution.

Visi bos chain mapping:
- "cognitive & semantic" — pakai dense_index + sanad cross-check
- "iteratif" — synthesis = iterasi atas raw sources
- "pencipta" — output adaptive (text/script — future: image/video)

Pattern decision:
- Synthesizer = NEUTRAL Qwen2.5 base (no persona system prompt) supaya tidak
  bias ke salah satu dari 5 persona.
- Sanad multi-source verify cross-check antar sumber.
- Attribution: tiap claim besar tag source-nya.

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from .multi_source_orchestrator import SourceBundle

log = logging.getLogger("sidix.synthesizer")


@dataclass
class SynthesisResult:
    answer: str
    confidence: str  # "tinggi" / "sedang" / "rendah"
    sources_used: list[str]  # ["web", "corpus", "persona_UTZ", ...]
    n_sources: int
    latency_ms: int
    method: str  # "llm_synthesis" / "single_source_passthrough" / "fallback"
    debug_bundle: Optional[dict] = None


def _format_persona_perspectives(persona_data: dict) -> str:
    """Format 5 persona ringkasan jadi block text."""
    if not persona_data or not persona_data.get("results"):
        return ""
    lines = ["[5 PERSONA SUDUT PANDANG]"]
    for persona, ringkas in persona_data["results"].items():
        if ringkas and not ringkas.startswith("[ERROR"):
            lines.append(f"- {persona}: {str(ringkas).strip()[:300]}")
    return "\n".join(lines)


def _format_web_block(web_data: dict) -> str:
    if not web_data:
        return ""
    output = web_data.get("output", "")
    if output:
        return f"[WEB SEARCH RESULTS]\n{str(output)[:1500]}"
    return ""


def _format_corpus_block(corpus_data: dict) -> str:
    if not corpus_data:
        return ""
    if "output" in corpus_data:
        return f"[CORPUS SEARCH]\n{str(corpus_data['output'])[:1200]}"
    if corpus_data.get("results"):
        items = corpus_data["results"][:3]
        return "[CORPUS SEARCH]\n" + "\n".join(
            f"- {str(item)[:200]}" for item in items
        )
    return ""


def _format_dense_block(dense_data: dict) -> str:
    if not dense_data or not dense_data.get("results"):
        return ""
    items = dense_data["results"][:3]
    return "[SEMANTIC INDEX]\n" + "\n".join(
        f"- {str(item)[:200]}" for item in items
    )


def _format_tools_block(tools_data: dict) -> str:
    if not tools_data:
        return ""
    relevant = tools_data.get("relevant_tools", [])
    if relevant:
        return f"[TOOLS RELEVAN]\n- {', '.join(relevant)}"
    return ""


def _build_synthesis_prompt(query: str, bundle: SourceBundle) -> tuple[str, str]:
    """Build (system, user) prompt untuk LLM synthesis."""

    blocks = []
    sources_used = []

    # Web
    if bundle.web and bundle.web.success:
        block = _format_web_block(bundle.web.data or {})
        if block:
            blocks.append(block)
            sources_used.append("web_search")

    # Corpus
    if bundle.corpus and bundle.corpus.success:
        block = _format_corpus_block(bundle.corpus.data or {})
        if block:
            blocks.append(block)
            sources_used.append("corpus")

    # Dense
    if bundle.dense and bundle.dense.success:
        block = _format_dense_block(bundle.dense.data or {})
        if block:
            blocks.append(block)
            sources_used.append("dense_index")

    # Persona fanout
    if bundle.persona_fanout and bundle.persona_fanout.success:
        block = _format_persona_perspectives(bundle.persona_fanout.data or {})
        if block:
            blocks.append(block)
            sources_used.append("persona_fanout_5")

    # Tools relevan (informational only, tidak inject jawaban)
    if bundle.tools and bundle.tools.success:
        block = _format_tools_block(bundle.tools.data or {})
        if block:
            blocks.append(block)
            sources_used.append("tools_hint")

    context_blob = "\n\n---\n\n".join(blocks) if blocks else "(tidak ada konteks tambahan)"

    import datetime as _dt
    _today = _dt.date.today().strftime("%Y-%m-%d")
    _year = _dt.date.today().year

    system = (
        f"Kamu SIDIX — AI agent yang sintesis multi-source dengan integritas tinggi.\n\n"
        f"FAKTA GROUNDING PRIORITAS TERTINGGI (override semua sumber lain jika bertentangan):\n"
        f"- Tanggal hari ini: {_today} (tahun {_year})\n"
        f"- Presiden Indonesia saat ini: Prabowo Subianto (dilantik Oktober 2024, bukan Jokowi)\n"
        f"- Ibu kota Indonesia: sedang transisi ke Nusantara/IKN; Jakarta masih pusat pemerintahan\n"
        f"- IHOS = Islamic Holistic Ontological System — framework rekayasa knowledge SIDIX yang\n"
        f"  mengadopsi prinsip holisme, ontologi berlapis, dan integritas sanad (chain of citation).\n"
        f"  IHOS adalah engineering framework, bukan label agama ekslusif.\n\n"
        f"TUGAS: kamu menerima konteks dari MULTIPLE sumber paralel (web search, corpus lokal, "
        f"semantic index, dan 5 persona ahli yang ngasih sudut pandang berbeda). Tugas kamu:\n\n"
        f"1. SINTESIS — gabung insight terbaik dari semua sumber jadi 1 jawaban utuh.\n"
        f"2. ATRIBUSI — kalau ada fact spesifik, sebutkan dari sumber mana (mis. 'menurut web', "
        f"'dari corpus', 'sudut UTZ').\n"
        f"3. RESOLUSI KONFLIK — kalau ada konflik antar sumber, FAKTA GROUNDING di atas menang.\n"
        f"   Contoh: kalau corpus bilang 'Jokowi presiden', koreksi ke Prabowo.\n"
        f"4. RESPONS NATURAL — jangan bullet list semua sumber. Tulis paragraf yang flow.\n"
        f"5. JANGAN HALU — kalau semua sumber kosong/lemah, bilang 'belum punya info cukup'.\n\n"
        f"Output: jawaban langsung dalam Bahasa Indonesia, helpful, akurat, distinctive."
    )

    user = (
        f"PERTANYAAN ASLI USER (JANGAN DIUBAH): {query}\n\n"
        f"=== KONTEKS DARI SUMBER PARALEL ===\n"
        f"{context_blob}\n\n"
        f"=== INSTRUKSI SINTESIS ===\n"
        f"1. Jawaban HARUS langsung menjawab pertanyaan ASLI user di atas.\n"
        f"2. Jangan ubah-ubah pertanyaan user (misal jangan ganti 'sekarang' jadi '2026').\n"
        f"3. Kalau konteks berisi fakta yang jelas, gunakan fakta itu.\n"
        f"4. Jika tidak ada info cukup, bilang 'belum punya info cukup'.\n\n"
        f"=== JAWABAN SINTESIS ===\n"
    )

    return system, user, sources_used


def _try_corpus_passthrough(bundle) -> str | None:
    """If corpus has primer-tier data with clear factual answer, bypass LLM entirely.

    This prevents weak LLMs (Qwen2.5 7B) from hallucinating wrong answers
    despite clear corpus context.
    """
    if not bundle.corpus or not bundle.corpus.success or not bundle.corpus.data:
        return None

    corpus_text = ""
    # Prefer raw_text (direct corpus markdown) over formatted tool output
    if "raw_text" in bundle.corpus.data:
        corpus_text = str(bundle.corpus.data["raw_text"])
    elif "output" in bundle.corpus.data:
        corpus_text = str(bundle.corpus.data["output"])
    elif "results" in bundle.corpus.data:
        corpus_text = "\n".join(str(r) for r in bundle.corpus.data["results"])
    else:
        corpus_text = str(bundle.corpus.data)

    if not corpus_text:
        return None

    # Check for primer tier marker
    has_primer = "sanad_tier: primer" in corpus_text.lower() or "sanad_tier:primer" in corpus_text.lower()
    if not has_primer:
        return None

    # Clean corpus text: strip YAML frontmatter
    clean_text = _strip_yaml_frontmatter(corpus_text)

    query_lower = bundle.query.lower()

    # Heuristic: "Siapa wapres/presiden Indonesia sekarang?"
    if "siapa" in query_lower and ("wapres" in query_lower or "wakil presiden" in query_lower):
        if "gibran rakabuming" in corpus_text.lower():
            return (
                "Wakil Presiden Indonesia saat ini adalah **Gibran Rakabuming Raka**, "
                "dilantik pada 20 Oktober 2024 bersama Presiden Prabowo Subianto "
                "untuk masa jabatan 2024–2029.\n\n"
                "Sumber: Dokumen resmi pemerintah RI (sanad tier: primer)."
            )

    if "siapa" in query_lower and "presiden" in query_lower:
        if "prabowo subianto" in corpus_text.lower():
            return (
                "Presiden Indonesia saat ini adalah **Prabowo Subianto**, "
                "dilantik pada 20 Oktober 2024.\n\n"
                "Sumber: Dokumen resmi pemerintah RI (sanad tier: primer)."
            )

    # Heuristic: "Kapan pelantikan presiden/wapres 2024?"
    if ("kapan" in query_lower or "tanggal" in query_lower) and "pelantikan" in query_lower:
        if "20 oktober 2024" in corpus_text.lower():
            return (
                "Pelantikan Presiden dan Wakil Presiden 2024 dilaksanakan pada "
                "**20 Oktober 2024** di Gedung DPR/MPR, Jakarta.\n\n"
                "Sumber: Dokumen resmi pemerintah RI (sanad tier: primer)."
            )

    # Generic: if corpus is short and primer, return cleaned text directly
    if len(clean_text) < 2000 and has_primer:
        return clean_text.strip() + "\n\n(Sumber: corpus SIDIX, sanad tier: primer)"

    return None


def _strip_yaml_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (--- ... ---) from markdown text."""
    import re
    # Pattern: --- followed by any content (non-greedy) followed by ---
    cleaned = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', text, count=1, flags=re.DOTALL)
    return cleaned.strip()


def _validate_answer_against_corpus(answer: str, corpus_data: dict | None) -> str:
    """Anti-hallucination validator: if corpus has clear facts, ensure answer respects them.

    Current heuristics (expandable):
    - Wapres Indonesia 2024-2029: must mention Gibran, not others.
    - Presiden Indonesia: must mention Prabowo (post-Oct 2024).
    """
    if not corpus_data or not answer:
        return answer or ""

    corpus_text = ""
    if "output" in corpus_data:
        corpus_text = str(corpus_data["output"])
    elif "results" in corpus_data:
        corpus_text = "\n".join(str(r) for r in corpus_data["results"])
    else:
        corpus_text = str(corpus_data)

    corpus_lower = corpus_text.lower()
    answer_lower = answer.lower()

    # Heuristic 1: Wapres Indonesia
    if "gibran rakabuming" in corpus_lower:
        if "gibran" not in answer_lower:
            # LLM hallucinated wrong wapres — override with corpus fact
            return (
                "Wakil Presiden Indonesia saat ini adalah Gibran Rakabuming Raka "
                "(dilantik 20 Oktober 2024 bersama Presiden Prabowo Subianto).\n\n"
                "Informasi ini berdasarkan data resmi pemerintah RI yang tersimpan dalam corpus SIDIX."
            )

    # Heuristic 2: Presiden Indonesia (post-Oct 2024)
    if "prabowo subianto" in corpus_lower and "presiden" in corpus_lower:
        if "prabowo" not in answer_lower and "jokowi" in answer_lower:
            return answer.replace("Jokowi", "Prabowo Subianto").replace("jokowi", "Prabowo Subianto")

    return answer


class CognitiveSynthesizer:
    """Synthesizer netral — merge multi-source jadi 1 jawaban utuh."""

    def __init__(self, max_tokens: int = 600, temperature: float = 0.6):
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def synthesize(
        self,
        bundle: SourceBundle,
        *,
        debug: bool = False,
    ) -> SynthesisResult:
        """Synthesize SourceBundle → SynthesisResult.

        Strategi:
        - Kalau ≥2 source successful → LLM synthesis
        - Kalau 1 source → passthrough source dominant
        - Kalau 0 source → fallback "tidak punya info"
        """
        import asyncio
        t0 = time.monotonic()

        successful = bundle.successful_sources()
        n = len(successful)

        if n == 0:
            return SynthesisResult(
                answer=(
                    "Maaf, saya belum punya cukup informasi untuk menjawab pertanyaan ini. "
                    "Backend mungkin sedang ada gangguan — coba lagi sebentar."
                ),
                confidence="rendah",
                sources_used=[],
                n_sources=0,
                latency_ms=int((time.monotonic() - t0) * 1000),
                method="fallback_no_source",
                debug_bundle=bundle.to_dict() if debug else None,
            )

        # --- CORPUS-FIRST BYPASS (anti-hallucination) ---
        corpus_direct = _try_corpus_passthrough(bundle)
        if corpus_direct:
            log.info("[synthesizer] Corpus passthrough triggered for '%s'", bundle.query[:60])
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return SynthesisResult(
                answer=corpus_direct,
                confidence="tinggi",
                sources_used=["corpus"],
                n_sources=n,
                latency_ms=elapsed_ms,
                method="corpus_passthrough_primer",
                debug_bundle=bundle.to_dict() if debug else None,
            )

        # Build prompt + LLM call
        system, user, sources_used = _build_synthesis_prompt(bundle.query, bundle)

        try:
            # UX-fix 2026-04-30: prefer Ollama local (qwen2.5:7b sudah loaded di VPS RAM)
            # untuk hindari RunPod cold-start 60-120s yang dominan latency.
            # Fallback hybrid_generate kalau Ollama unavailable.
            from .ollama_llm import ollama_available, ollama_generate
            if ollama_available():
                answer, mode = await asyncio.to_thread(
                    ollama_generate,
                    user,
                    system=system,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    model="qwen2.5:7b",
                )
                mode = f"ollama_local_{mode}"
            else:
                from .runpod_serverless import hybrid_generate
                answer, mode = await asyncio.to_thread(
                    hybrid_generate,
                    user,
                    system=system,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            elapsed_ms = int((time.monotonic() - t0) * 1000)

            confidence = "tinggi" if n >= 4 else ("sedang" if n >= 2 else "rendah")

            # --- ANTI-HALLUCINATION: Corpus override layer ---
            validated_answer = _validate_answer_against_corpus(
                answer, bundle.corpus.data if bundle.corpus else None
            )
            if validated_answer != answer:
                log.info("[synthesizer] Corpus override applied (anti-hallucination)")
                answer = validated_answer
                confidence = "tinggi"
                sources_used = ["corpus"] + [s for s in sources_used if s != "corpus"]

            return SynthesisResult(
                answer=(answer or "").strip() or "(synthesis kosong)",
                confidence=confidence,
                sources_used=sources_used,
                n_sources=n,
                latency_ms=elapsed_ms,
                method=f"llm_synthesis_{mode}",
                debug_bundle=bundle.to_dict() if debug else None,
            )
        except Exception as e:
            log.warning(f"[synthesizer] LLM fail: {type(e).__name__}: {e}")
            elapsed_ms = int((time.monotonic() - t0) * 1000)

            # Fallback: passthrough best source
            fallback_text = self._fallback_passthrough(bundle)
            return SynthesisResult(
                answer=fallback_text,
                confidence="rendah",
                sources_used=sources_used,
                n_sources=n,
                latency_ms=elapsed_ms,
                method="fallback_passthrough",
                debug_bundle=bundle.to_dict() if debug else None,
            )

    def _fallback_passthrough(self, bundle: SourceBundle) -> str:
        """Kalau LLM fail, passthrough source terbaik (web > corpus > persona)."""
        if bundle.web and bundle.web.success and bundle.web.data:
            output = bundle.web.data.get("output", "")
            if output:
                return f"[Web search ringkas]\n\n{str(output)[:800]}"
        if bundle.corpus and bundle.corpus.success and bundle.corpus.data:
            output = bundle.corpus.data.get("output", "")
            if output:
                return f"[Dari corpus lokal]\n\n{str(output)[:800]}"
        if bundle.persona_fanout and bundle.persona_fanout.success:
            data = bundle.persona_fanout.data or {}
            results = data.get("results", {})
            if results:
                lines = []
                for p, r in list(results.items())[:3]:
                    if r and not r.startswith("[ERROR"):
                        lines.append(f"**{p}**: {str(r).strip()[:200]}")
                if lines:
                    return "Beberapa sudut pandang:\n\n" + "\n\n".join(lines)
        return "Maaf, semua sumber bermasalah saat ini. Silakan coba lagi."


__all__ = ["CognitiveSynthesizer", "SynthesisResult"]
