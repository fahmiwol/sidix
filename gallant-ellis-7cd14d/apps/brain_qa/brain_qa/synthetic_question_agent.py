"""
synthetic_question_agent.py — Agent Dummy yang Generate Pertanyaan untuk Latih SIDIX
=====================================================================================

Sebelum file ini ada, SIDIX HANYA belajar dari pertanyaan user real. Masalah:
- Cold-start corpus baru: tidak ada pertanyaan untuk evaluate retrieval quality
- Persona under-tested: persona ALEY (academic) jarang di-trigger user casual
- Domain coverage gap: corpus punya 1182 doc tapi user tanya 10-20 topik dominan
- Quality drift: tidak ada baseline test rutin untuk detect regression

Solusi: Agent dummy yang AUTONOMOUS bikin pertanyaan di background → eksekusi
ke ReAct loop → record QnA pair + evaluate quality → feed ke training pipeline.

Tiga mode:

  1. **CORPUS-DRIVEN** — sample chunk corpus → generate Q yang answerable dari chunk
     itu, plus 1 follow-up Q yang butuh reasoning. Eval: apakah retrieval
     mengembalikan chunk asal? (gold-standard auto-eval).

  2. **GAP-DRIVEN** — baca knowledge_gap_detector output → generate Q baru di
     domain yang gap-nya tinggi (bukan repeat Q lama).

  3. **PERSONA-DIVERSE** — generate Q untuk tiap 5 persona (UTZ creative, ABOO
     engineer, OOMAR strategist, ALEY academic, AYMAN general) → eksekusi
     dengan persona match → record per-persona quality metric.

Hasil: catat ke `.data/synthetic_qna.jsonl` dengan label `gold_chunk_id`,
`expected_persona`, `expected_difficulty`, plus actual ReAct response +
relevance_score + latency_ms.

Cron: panggil `run_synthetic_batch(n=10)` tiap 4 jam (6x/hari = 60 Q/hari =
~420/minggu). Cukup untuk training signal yang konsisten.

NOT vendor LLM — reuse `local_llm.generate_sidix()` (Qwen2.5-7B + LoRA SIDIX).
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SyntheticQ:
    """1 pertanyaan synthetic + metadata + hasil eksekusi."""
    id: str
    ts: str
    mode: str                       # "corpus" | "gap" | "persona"
    question: str
    expected_persona: str = "AYMAN"
    expected_difficulty: str = "easy"   # easy | medium | hard
    gold_chunk_id: str = ""             # source chunk yang harusnya retrieved (mode=corpus)
    target_domain: str = ""

    # Eksekusi
    answer: str = ""
    actual_persona: str = ""
    citations_count: int = 0
    retrieved_gold: bool = False        # apakah gold_chunk_id ada di citations
    confidence: float = 0.0
    latency_ms: int = 0
    error: str = ""

    # Skor turunan
    relevance_score: float = 0.0
    quality_grade: str = ""             # A-F


# ── Path helpers ───────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _output_path() -> Path:
    return _data_dir() / "synthetic_qna.jsonl"


# ── Question generation strategies ─────────────────────────────────────────────

def _persona_seed_prompts() -> dict[str, list[str]]:
    """Seed prompt per persona — bukan template kaku, jadi inspirasi diversitas."""
    return {
        "UTZ": [
            "Bayangkan {topic} sebagai metafora visual — apa bentuknya?",
            "Kalau {topic} jadi gambar, palet warnanya seperti apa?",
            "Bagaimana cara menjelaskan {topic} ke anak 8 tahun pakai cerita?",
        ],
        "ABOO": [
            "Kapan {topic} fail dalam praktik dan bagaimana cara debug-nya?",
            "Tradeoff utama implementasi {topic} di sistem skala produksi?",
            "Kasih contoh code yang demonstrate {topic} dengan edge case.",
        ],
        "OOMAR": [
            "Strategi go-to-market untuk produk berbasis {topic}?",
            "Cost structure dan break-even untuk venture di {topic}?",
            "Risk profile {topic} untuk founder Indonesia tier-2 city?",
        ],
        "ALEY": [
            "Apa empirical evidence untuk klaim {topic}? Sebut 2 paper.",
            "Bandingkan 2 mazhab utama dalam riset {topic}.",
            "Apa critique paling tajam terhadap {topic}?",
        ],
        "AYMAN": [
            "Penjelasan {topic} dalam 3 kalimat mudah.",
            "Apa hubungan {topic} dengan kehidupan sehari-hari?",
            "Kalau saya pemula, dari mana saya mulai belajar {topic}?",
        ],
    }


def _sample_corpus_chunk() -> Optional[dict]:
    """
    Sample 1 chunk acak dari corpus index untuk corpus-driven Q.
    Return dict {id, text, source_path, source_title} atau None.
    """
    try:
        from .paths import default_index_dir
        chunks_path = default_index_dir() / "chunks.jsonl"
        if not chunks_path.exists():
            return None
        # Reservoir sampling 1 chunk dari N total (memory-efficient)
        chosen = None
        n = 0
        with chunks_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                n += 1
                if random.randint(1, n) == 1:
                    try:
                        chosen = json.loads(line)
                    except Exception:
                        continue
        return chosen
    except Exception as e:
        log.warning("[synthetic_q] corpus sampling fail: %s", e)
        return None


def _generate_question_from_chunk(chunk: dict, persona: str) -> Optional[str]:
    """
    Bisik LLM untuk generate Q yang BUTUH chunk ini untuk dijawab.
    Reuse local_llm — generative SIDIX self-loop, no vendor API.
    """
    try:
        from .ollama_llm import generate as llm_gen
    except Exception:
        try:
            from .local_llm import generate_sidix as llm_gen
        except Exception:
            return None

    text = (chunk.get("text") or "")[:600]
    title = chunk.get("source_title", "")
    if not text:
        return None

    prompt = (
        f"Sebagai bahan latihan SIDIX, buat 1 pertanyaan singkat (max 18 kata) "
        f"yang HANYA bisa dijawab dengan baik kalau pembaca tahu detail spesifik "
        f"dari teks berikut. Jangan pertanyaan generik. Sumber: {title}.\n\n"
        f"TEKS:\n{text}\n\n"
        f"Pertanyaan (langsung, tanpa preamble):"
    )

    try:
        # Try ollama_llm.generate signature first
        out = llm_gen(prompt, max_tokens=80, temperature=0.7)
        if isinstance(out, dict):
            q = (out.get("text") or out.get("response") or "").strip()
        else:
            q = (out or "").strip()
        # Clean: strip leading "Pertanyaan:" / quotes / numbering
        q = q.split("\n")[0].strip().strip('"\'').lstrip("0123456789. )")
        if len(q) < 5 or len(q) > 200:
            return None
        return q
    except Exception as e:
        log.debug("[synthetic_q] LLM gen fail: %s", e)
        return None


# ── Run synthetic batch ────────────────────────────────────────────────────────

def _run_react_safely(
    question: str,
    persona: str,
    *,
    timeout_s: int = 90,
) -> dict:
    """
    Eksekusi ReAct loop untuk pertanyaan synthetic. Return dict dengan
    answer + citations + latency. Best-effort, jangan crash.
    """
    t_start = time.time()
    try:
        from .agent_react import run_react
        session = run_react(
            question=question,
            persona=persona,
            client_id="synthetic_agent",
            conversation_id="",
            corpus_only=False,
            allow_web_fallback=True,
            simple_mode=True,        # lebih cepat untuk batch
            agent_mode=False,        # filter on supaya quality terukur
            strict_mode=False,
        )
        latency_ms = int((time.time() - t_start) * 1000)

        cits = []
        for step in session.steps:
            cits.extend(step.action_args.get("_citations", []))
        cits.extend(session.citations)

        return {
            "answer": session.final_answer,
            "actual_persona": session.persona,
            "citations": cits,
            "confidence": float(session.confidence_score or 0.0),
            "latency_ms": latency_ms,
            "error": "",
        }
    except Exception as e:
        return {
            "answer": "",
            "actual_persona": persona,
            "citations": [],
            "confidence": 0.0,
            "latency_ms": int((time.time() - t_start) * 1000),
            "error": str(e)[:200],
        }


def _evaluate_relevance(sq: SyntheticQ) -> tuple[float, str]:
    """
    Hitung relevance_score [0.0-1.0] + quality grade A-F.

    Komponen:
      - 0.4 × confidence (model self-rating)
      - 0.3 × retrieved_gold (corpus-driven: 1.0 kalau gold chunk in citations)
      - 0.2 × citations_count_normalized (lebih banyak = lebih grounded, cap 5)
      - 0.1 × latency_score (cepat = baik, target <15s)
      - error → 0
    """
    if sq.error:
        return 0.0, "F"

    conf_part = max(0.0, min(1.0, sq.confidence))
    gold_part = 1.0 if sq.retrieved_gold else (0.5 if sq.mode != "corpus" else 0.0)
    cit_part = min(1.0, sq.citations_count / 5.0)
    # Latency: <5s perfect, 15s baseline (0.7), >60s zero
    lat_s = sq.latency_ms / 1000.0
    if lat_s <= 5:
        lat_part = 1.0
    elif lat_s <= 15:
        lat_part = 0.7
    elif lat_s <= 30:
        lat_part = 0.4
    elif lat_s <= 60:
        lat_part = 0.2
    else:
        lat_part = 0.0

    score = 0.4 * conf_part + 0.3 * gold_part + 0.2 * cit_part + 0.1 * lat_part
    score = max(0.0, min(1.0, score))

    if score >= 0.85: grade = "A"
    elif score >= 0.7: grade = "B"
    elif score >= 0.55: grade = "C"
    elif score >= 0.4: grade = "D"
    else: grade = "F"

    return score, grade


def _persist_synthetic(sq: SyntheticQ) -> None:
    """Append SyntheticQ ke synthetic_qna.jsonl."""
    try:
        path = _output_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(sq), ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[synthetic_q] persist fail: %s", e)


def run_synthetic_batch(n: int = 10, mode: str = "corpus") -> dict:
    """
    Run N synthetic questions, eksekusi ReAct, simpan hasil + score.

    Returns summary: {generated, executed, avg_score, avg_latency, by_grade}.

    Args:
        n: jumlah pertanyaan dibikin (default 10)
        mode: "corpus" (corpus-driven, paling akurat) | "persona" (diverse)

    Cron suggestion:
        */240 * * * * curl -X POST http://localhost:8765/agent/synthetic/batch \\
                          -H "x-admin-token: $TOKEN" -d '{"n":10}'
    """
    personas = ["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"]
    seed_prompts = _persona_seed_prompts()
    results: list[SyntheticQ] = []

    for i in range(n):
        persona = personas[i % len(personas)]

        if mode == "corpus":
            chunk = _sample_corpus_chunk()
            if not chunk:
                continue
            q = _generate_question_from_chunk(chunk, persona)
            if not q:
                continue
            sq = SyntheticQ(
                id=f"synth_{int(time.time())}_{i}",
                ts=datetime.now(timezone.utc).isoformat(),
                mode="corpus",
                question=q,
                expected_persona=persona,
                expected_difficulty="medium",
                gold_chunk_id=chunk.get("id", chunk.get("source_path", ""))[:128],
                target_domain=chunk.get("source_title", "")[:60],
            )
        else:
            # persona-diverse fallback (no LLM gen, pakai seed)
            templates = seed_prompts.get(persona, seed_prompts["AYMAN"])
            template = random.choice(templates)
            topics = ["maqashid", "fintech indonesia", "halal supply chain",
                      "lora finetuning", "konsep tawakkul", "biopharma riset"]
            q = template.format(topic=random.choice(topics))
            sq = SyntheticQ(
                id=f"synth_{int(time.time())}_{i}",
                ts=datetime.now(timezone.utc).isoformat(),
                mode="persona",
                question=q,
                expected_persona=persona,
                expected_difficulty="easy",
            )

        # Eksekusi
        out = _run_react_safely(sq.question, sq.expected_persona)
        sq.answer = (out["answer"] or "")[:1200]
        sq.actual_persona = out["actual_persona"]
        sq.citations_count = len(out["citations"])
        sq.confidence = out["confidence"]
        sq.latency_ms = out["latency_ms"]
        sq.error = out["error"]

        # Cek apakah gold chunk retrieved (mode corpus)
        if sq.gold_chunk_id and out["citations"]:
            for cit in out["citations"]:
                cit_id = (cit.get("id") or cit.get("source_path") or
                          cit.get("source_title") or "")
                if sq.gold_chunk_id and sq.gold_chunk_id in cit_id:
                    sq.retrieved_gold = True
                    break

        # Score + persist
        sq.relevance_score, sq.quality_grade = _evaluate_relevance(sq)
        _persist_synthetic(sq)
        results.append(sq)

    # Summary
    if not results:
        return {"generated": 0, "executed": 0, "avg_score": 0.0,
                "avg_latency_ms": 0, "by_grade": {}}

    avg_score = sum(r.relevance_score for r in results) / len(results)
    avg_lat = sum(r.latency_ms for r in results) / len(results)
    by_grade: dict[str, int] = {}
    for r in results:
        by_grade[r.quality_grade] = by_grade.get(r.quality_grade, 0) + 1

    return {
        "generated": n,
        "executed": len(results),
        "avg_score": round(avg_score, 3),
        "avg_latency_ms": int(avg_lat),
        "by_grade": by_grade,
        "samples": [
            {
                "q": r.question[:80],
                "grade": r.quality_grade,
                "score": round(r.relevance_score, 2),
                "latency_ms": r.latency_ms,
                "persona": r.actual_persona,
            }
            for r in results[:5]
        ],
    }


def list_recent(limit: int = 50) -> list[dict]:
    """Read tail dari synthetic_qna.jsonl."""
    path = _output_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        out = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
                if len(out) >= limit:
                    break
            except Exception:
                continue
        return out
    except Exception:
        return []


def stats() -> dict:
    """Summary stats untuk admin dashboard."""
    entries = list_recent(limit=1000)
    if not entries:
        return {"total": 0, "avg_score": 0.0, "avg_latency_ms": 0,
                "by_grade": {}, "by_mode": {}, "by_persona": {}}

    by_grade: dict[str, int] = {}
    by_mode: dict[str, int] = {}
    by_persona: dict[str, int] = {}
    scores: list[float] = []
    lats: list[int] = []

    for e in entries:
        g = e.get("quality_grade", "F")
        by_grade[g] = by_grade.get(g, 0) + 1
        m = e.get("mode", "unknown")
        by_mode[m] = by_mode.get(m, 0) + 1
        p = e.get("actual_persona") or e.get("expected_persona", "?")
        by_persona[p] = by_persona.get(p, 0) + 1
        if e.get("relevance_score"):
            scores.append(float(e["relevance_score"]))
        if e.get("latency_ms"):
            lats.append(int(e["latency_ms"]))

    return {
        "total": len(entries),
        "avg_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "avg_latency_ms": int(sum(lats) / len(lats)) if lats else 0,
        "by_grade": by_grade,
        "by_mode": by_mode,
        "by_persona": by_persona,
    }


__all__ = ["SyntheticQ", "run_synthetic_batch", "list_recent", "stats"]
