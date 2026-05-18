"""
self_modifier.py — Sprint L1: Self-Modifying Engine
=====================================================

SIDIX mengevaluasi diri sendiri secara periodik:
1. Baca error_registry (apa yang gagal)
2. Baca pattern_extractor (apa yang dipelajari)
3. Baca self_test_loop stats (kualitas jawaban)
4. LLM analisis holistic → proposal perbaikan
5. Save proposal ke .data/self_improvement_proposals.jsonl
6. Owner review → approve → apply

Ini adalah implementasi dari "reflective loop" di arsitektur SIDIX —
seperti otak yang consolidate memori saat tidur dan buang yang tidak
berguna + perkuat yang penting.

Public API:
    generate_improvement_proposal(llm_fn) -> dict
    get_pending_proposals() -> list[dict]
    mark_proposal_reviewed(proposal_id, approved, notes) -> bool
    get_proposal_stats() -> dict
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# ── Storage ────────────────────────────────────────────────────────────────────

def _resolve_proposals_path() -> Path:
    try:
        from .paths import workspace_root
        p = workspace_root() / ".data" / "self_improvement_proposals.jsonl"
    except Exception:
        p = Path(__file__).resolve().parents[3] / ".data" / "self_improvement_proposals.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

_PROPOSALS_PATH: Path | None = None
_lock = threading.Lock()

def _proposals_path() -> Path:
    global _PROPOSALS_PATH
    if _PROPOSALS_PATH is None:
        _PROPOSALS_PATH = _resolve_proposals_path()
    return _PROPOSALS_PATH


# ── Data Collection ────────────────────────────────────────────────────────────

def _collect_error_summary() -> dict:
    try:
        from .error_registry import get_error_stats, get_recent_errors
        stats = get_error_stats()
        recent = get_recent_errors(n=20)
        error_examples = [
            f"[{e.get('error_type')}] {e.get('message','')[:80]}"
            for e in recent[-10:]
        ]
        return {"stats": stats, "examples": error_examples}
    except Exception as e:
        return {"stats": {}, "examples": [], "error": str(e)}


def _collect_pattern_summary() -> dict:
    try:
        from .pattern_extractor import stats as pattern_stats
        return pattern_stats()
    except Exception as e:
        return {"total": 0, "error": str(e)}


def _collect_selftest_summary() -> dict:
    try:
        from .self_test_loop import get_self_test_stats
        return get_self_test_stats()
    except Exception as e:
        return {"error": str(e)}


def _collect_corpus_stats() -> dict:
    try:
        from .agent_tools import _tool_list_sources
        result = _tool_list_sources({})
        return {"corpus_output": str(getattr(result, "output", ""))[:300]}
    except Exception as e:
        return {"error": str(e)}


# ── Main Generator ────────────────────────────────────────────────────────────

def generate_improvement_proposal(llm_fn=None) -> dict:
    """
    Kumpulkan semua diagnostic data → LLM analisis → proposal perbaikan.
    Proposal disimpan ke file untuk owner review.

    llm_fn: callable(prompt: str) -> str
    Returns: proposal dict dengan id, proposals list, dan metadata
    """
    proposal_id = uuid.uuid4().hex[:12]
    ts = datetime.now(timezone.utc).isoformat()

    # Kumpulkan diagnostics
    errors = _collect_error_summary()
    patterns = _collect_pattern_summary()
    self_test = _collect_selftest_summary()
    corpus = _collect_corpus_stats()

    diagnostics = {
        "errors": errors,
        "patterns": patterns,
        "self_test": self_test,
        "corpus": corpus,
    }

    if llm_fn is None:
        proposal = {
            "id": proposal_id,
            "ts": ts,
            "diagnostics": diagnostics,
            "proposals": [],
            "status": "no_llm",
            "message": "llm_fn tidak disediakan — hanya diagnostics dikumpulkan",
        }
        _save_proposal(proposal)
        return proposal

    # Format diagnostics untuk LLM
    error_stats = errors.get("stats", {})
    error_examples = "\n".join(errors.get("examples", [])[:10])

    prompt = f"""Kamu adalah SIDIX self-improvement engine.

## Diagnostic Report SIDIX

### Error Registry
- Total errors: {error_stats.get('total', 0)}
- Distribusi tipe: {error_stats.get('by_type', {})}
- Error 7 hari terakhir: {error_stats.get('recent_7d', 0)}
- Contoh error terbaru:
{error_examples or '(tidak ada)'}

### Pattern Library
{json.dumps(patterns, ensure_ascii=False)[:500]}

### Self-Test Stats
{json.dumps(self_test, ensure_ascii=False)[:300]}

### Corpus Stats
{corpus.get('corpus_output', '(tidak tersedia)')}

---

Berdasarkan diagnostic di atas, identifikasi TOP 3 perbaikan paling impactful untuk SIDIX.

Fokus pada:
1. Error yang paling sering terjadi (bisa dicegah)
2. Gap capability yang terlihat dari self_test stats
3. Pattern yang bisa dioptimasi dalam workflow

Output dalam JSON (jawab JSON saja, tidak ada teks lain):
{{
  "analysis": "Ringkasan 2-3 kalimat situasi SIDIX saat ini",
  "proposals": [
    {{
      "priority": 1,
      "title": "Judul perbaikan singkat",
      "problem": "Apa masalahnya (konkret)",
      "solution": "Apa yang perlu diubah",
      "affected_files": ["file.py"],
      "effort": "low/medium/high",
      "expected_impact": "Apa dampak kalau fix ini diimplementasi"
    }}
  ]
}}"""

    try:
        raw = llm_fn(prompt)
        # Extract JSON from response
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            llm_result = json.loads(m.group())
        else:
            llm_result = {"analysis": raw[:300], "proposals": []}
    except Exception as e:
        log.warning("[self_modifier] LLM analysis failed: %s", e)
        llm_result = {"analysis": f"LLM analysis gagal: {e}", "proposals": []}

    proposal = {
        "id": proposal_id,
        "ts": ts,
        "diagnostics_summary": {
            "total_errors": error_stats.get("total", 0),
            "recent_errors": error_stats.get("recent_7d", 0),
            "pattern_count": patterns.get("total", 0),
        },
        "analysis": llm_result.get("analysis", ""),
        "proposals": llm_result.get("proposals", []),
        "status": "pending_review",
    }

    _save_proposal(proposal)
    log.info("[self_modifier] generated proposal %s with %d suggestions",
             proposal_id, len(proposal["proposals"]))
    return proposal


# ── Persistence ───────────────────────────────────────────────────────────────

def _save_proposal(proposal: dict) -> None:
    with _lock:
        try:
            with open(_proposals_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(proposal, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning("[self_modifier] save proposal failed: %s", e)


def _load_proposals() -> list[dict]:
    p = _proposals_path()
    if not p.exists():
        return []
    entries = []
    with _lock:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
    return entries


def get_pending_proposals() -> list[dict]:
    """Kembalikan proposals yang belum di-review."""
    return [p for p in _load_proposals() if p.get("status") == "pending_review"]


def mark_proposal_reviewed(proposal_id: str, approved: bool, notes: str = "") -> bool:
    """Mark proposal sebagai reviewed. Returns True jika found."""
    all_proposals = _load_proposals()
    found = False
    updated = []
    for p in all_proposals:
        if p.get("id") == proposal_id:
            p["status"] = "approved" if approved else "rejected"
            p["review_ts"] = datetime.now(timezone.utc).isoformat()
            p["review_notes"] = notes
            found = True
        updated.append(p)

    if found:
        # Rewrite entire file
        with _lock:
            try:
                with open(_proposals_path(), "w", encoding="utf-8") as f:
                    for p in updated:
                        f.write(json.dumps(p, ensure_ascii=False) + "\n")
            except Exception as e:
                log.warning("[self_modifier] rewrite failed: %s", e)
    return found


def get_proposal_stats() -> dict:
    all_proposals = _load_proposals()
    from collections import Counter
    status_counts = Counter(p.get("status", "unknown") for p in all_proposals)
    return {
        "total": len(all_proposals),
        "by_status": dict(status_counts),
        "latest_ts": all_proposals[-1].get("ts", "") if all_proposals else "",
    }
