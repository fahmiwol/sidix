#!/usr/bin/env python3
"""
sidix_aku_bootstrap.py — Bootstrap Inventory from existing logs

Sources to mine:
1. .data/shadow_experience.jsonl   — shadow agent findings
2. .data/classroom_log.jsonl       — multi-teacher classroom Q&A (use successful answers)
3. .data/classroom_pairs.jsonl     — extracted training pairs
4. .data/task_results.jsonl        — task worker results (only ok=true ones)

Strategy: each successful answer → AKU. Subject/predicate inferred via simple
heuristic from question pattern. Confidence based on source reliability.

Run: python3 scripts/sidix_aku_bootstrap.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/sidix/apps/brain_qa")
from brain_qa.inventory_memory import ingest, stats  # noqa: E402

DATA_DIR = Path("/opt/sidix/.data")


# ── Heuristic: question → subject + predicate ──────────────────────────────

QUESTION_PATTERNS = [
    # "siapa X" → subject=X, predicate="identitas"
    (r"siapa\s+(.+?)(?:\?|$)", "siapa", lambda m: (m.group(1).strip(), "identitas")),
    # "apa itu X" → subject=X, predicate="definisi"
    (r"apa\s+itu\s+(.+?)(?:\?|$)", "apa_itu", lambda m: (m.group(1).strip(), "definisi")),
    # "bagaimana cara X" → subject=X, predicate="cara"
    (r"bagaimana\s+cara\s+(.+?)(?:\?|$)", "bagaimana", lambda m: (m.group(1).strip(), "cara")),
    # "jelaskan X" → subject=X, predicate="penjelasan"
    (r"jelaskan\s+(.+?)(?:\?|$)", "jelaskan", lambda m: (m.group(1).strip(), "penjelasan")),
    # "apa beda X dan Y" → subject="X dan Y", predicate="perbedaan"
    (r"apa\s+(?:beda|perbedaan)\s+(.+?)(?:\?|$)", "perbedaan", lambda m: (m.group(1).strip(), "perbedaan")),
    # "kapan X" → subject=X, predicate="waktu"
    (r"kapan\s+(.+?)(?:\?|$)", "kapan", lambda m: (m.group(1).strip(), "waktu")),
    # "berapa X" → subject=X, predicate="jumlah"
    (r"berapa\s+(.+?)(?:\?|$)", "berapa", lambda m: (m.group(1).strip(), "jumlah")),
    # "apa X" generic → subject=X, predicate="info"
    (r"apa\s+(.+?)(?:\?|$)", "apa", lambda m: (m.group(1).strip(), "info")),
]


def infer_subject_predicate(question: str) -> tuple[str, str]:
    """Heuristic parse question → (subject, predicate). Fallback: full Q as subject."""
    q = question.lower().strip().rstrip("?!.,;")
    for pattern, _name, extractor in QUESTION_PATTERNS:
        m = re.match(pattern, q)
        if m:
            try:
                subj, pred = extractor(m)
                if subj:
                    return subj[:200], pred
            except Exception:
                continue
    # Fallback: use first 100 chars as subject, "info" as predicate
    return q[:200], "info"


def classify_domain(question: str, claim: str) -> str:
    """Cheap domain classification."""
    text = (question + " " + claim).lower()
    if any(k in text for k in ["fiqh", "hukum", "puasa", "shalat", "hadith", "mazhab", "halal", "haram"]):
        return "fiqh"
    if any(k in text for k in ["python", "javascript", "code", "function", "async", "api", "framework"]):
        return "coding"
    if any(k in text for k in ["presiden", "menteri", "pemilu", "kpu", "ihsg"]):
        return "politics"
    if any(k in text for k in ["paper", "study", "research", "arxiv", "pubmed"]):
        return "science"
    if any(k in text for k in ["bisnis", "marketing", "saas", "startup", "valuation"]):
        return "business"
    if any(k in text for k in ["ai", "llm", "model", "transformer", "neural", "deep learning"]):
        return "ai_research"
    if any(k in text for k in ["medis", "obat", "vaksin", "penyakit"]):
        return "medis"
    return "general"


def shorten_claim(claim: str, max_len: int = 500) -> str:
    """Truncate at sentence boundary."""
    if len(claim) <= max_len:
        return claim.strip()
    cut = claim[:max_len]
    last_period = cut.rfind(".")
    if last_period > max_len * 0.5:
        return cut[:last_period + 1].strip()
    return cut.strip()


# ── Mine each source ────────────────────────────────────────────────────────

def mine_shadow_experience() -> int:
    """Mine .data/shadow_experience.jsonl."""
    path = DATA_DIR / "shadow_experience.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            question = e.get("question", "")
            claim = e.get("claim", "")
            if not question or not claim:
                continue
            subj, pred = infer_subject_predicate(question)
            domain = classify_domain(question, claim) or e.get("domain", "general")
            sources = e.get("sources", []) or []
            sources_normalized = [
                {"type": s.get("type", "web"),
                 "url": s.get("url", ""), "title": s.get("title", ""),
                 "provider": e.get("primary_teacher", "shadow"),
                 "retrieved_at": e.get("ts", "")}
                for s in sources
            ]
            confidence = 0.65 if not sources else 0.75  # source-backed = higher
            try:
                ingest(
                    subject=subj, predicate=pred, object=shorten_claim(claim),
                    context={"original_question": question, "shadow": e.get("shadow", "")},
                    sources=sources_normalized, confidence=confidence, domain=domain,
                )
                count += 1
            except Exception as ex:
                print(f"[mine_shadow] skip ({ex}): q={question[:60]}")
    return count


def mine_classroom() -> int:
    """Mine .data/classroom_log.jsonl — only successful (text non-empty) responses."""
    path = DATA_DIR / "classroom_log.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            question = e.get("question", "")
            if not question:
                continue
            for resp in e.get("responses", []):
                text = resp.get("text", "")
                if not text or len(text) < 30:
                    continue
                subj, pred = infer_subject_predicate(question)
                domain = classify_domain(question, text)
                provider = resp.get("provider", "?")
                model = resp.get("model", "")
                sources = [{"type": "llm_classroom", "provider": provider,
                            "model": model, "retrieved_at": e.get("ts", "")}]
                # Lower confidence for single-LLM (no consensus yet)
                # Higher if multiple succeeded in same session
                multi_ok = sum(1 for r in e.get("responses", []) if r.get("text"))
                confidence = 0.5 + 0.1 * min(multi_ok, 4)  # 0.5-0.9
                try:
                    ingest(
                        subject=subj, predicate=pred, object=shorten_claim(text),
                        context={"original_question": question,
                                 "classroom_session": e.get("cycle_id", "")},
                        sources=sources, confidence=confidence, domain=domain,
                    )
                    count += 1
                except Exception as ex:
                    print(f"[mine_classroom] skip ({ex})")
    return count


def mine_classroom_pairs() -> int:
    """Mine .data/classroom_pairs.jsonl — extracted multi-teacher consensus."""
    path = DATA_DIR / "classroom_pairs.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            q = e.get("question", "")
            ans = e.get("answer", "")
            if not q or not ans:
                continue
            subj, pred = infer_subject_predicate(q)
            domain = classify_domain(q, ans)
            providers = e.get("all_providers", [])
            sources = [{"type": "llm_consensus", "provider": p, "retrieved_at": e.get("ts", "")}
                       for p in providers]
            # High confidence for multi-teacher consensus (≥2 by classroom logic)
            confidence = 0.75 + 0.05 * min(len(providers), 5)
            try:
                ingest(
                    subject=subj, predicate=pred, object=shorten_claim(ans),
                    context={"original_question": q, "primary_provider": e.get("primary_provider", "")},
                    sources=sources, confidence=confidence, domain=domain,
                )
                count += 1
            except Exception as ex:
                print(f"[mine_pairs] skip ({ex})")
    return count


def mine_task_results() -> int:
    """Mine .data/task_results.jsonl — only ok=true."""
    path = DATA_DIR / "task_results.jsonl"
    if not path.exists():
        return 0
    count = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if not r.get("ok") or not r.get("consensus"):
                continue
            q = r.get("question", "")
            consensus = r.get("consensus", "")
            if not q or not consensus:
                continue
            subj, pred = infer_subject_predicate(q)
            domain = classify_domain(q, consensus)
            shadows = r.get("shadows", [])
            sources = [{"type": "shadow_consensus", "provider": s, "retrieved_at": r.get("ts", "")}
                       for s in shadows]
            confidence = 0.7 + 0.05 * min(len(shadows), 4)
            try:
                ingest(
                    subject=subj, predicate=pred, object=shorten_claim(consensus),
                    context={"original_question": q, "task_id": r.get("task_id", "")},
                    sources=sources, confidence=confidence, domain=domain,
                )
                count += 1
            except Exception as ex:
                print(f"[mine_tasks] skip ({ex})")
    return count


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== SIDIX AKU Bootstrap — mining existing logs ===\n")

    print(f"Stats BEFORE: {json.dumps(stats(), indent=2, default=str)}\n")

    n_shadow = mine_shadow_experience()
    print(f"  shadow_experience.jsonl   → {n_shadow} AKUs ingested")

    n_class = mine_classroom()
    print(f"  classroom_log.jsonl       → {n_class} AKUs ingested")

    n_pairs = mine_classroom_pairs()
    print(f"  classroom_pairs.jsonl     → {n_pairs} AKUs ingested")

    n_tasks = mine_task_results()
    print(f"  task_results.jsonl        → {n_tasks} AKUs ingested")

    print(f"\nTotal new AKUs: {n_shadow + n_class + n_pairs + n_tasks}\n")
    print(f"Stats AFTER: {json.dumps(stats(), indent=2, default=str)}")


if __name__ == "__main__":
    main()
