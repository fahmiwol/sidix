"""
inventory_memory.py — Vol 23 MVP: Atomic Knowledge Units (AKU) Storage

Per note 239 (sanad consensus) + note 244 (brain anatomy: hippocampus) +
user's whitepaper "Proof-of-Hifdz Knowledge-Integrity Consensus":

AKU = atomic knowledge unit. Every validated claim from SIDIX learning loops
(classroom sessions, shadow experiences, sanad consensus) becomes one AKU.
AKUs accumulate over time → SIDIX grows.

Storage: SQLite (`/opt/sidix/.data/inventory.db`)
- Lightweight, no extra deps (sqlite3 in stdlib)
- Full-text search via FTS5 (built-in)
- Persistent, survives restart
- Easy to query + audit

Schema:
- aku_id           — hash(subject + predicate + object + ts_day)
- subject          — what is being talked about (e.g. "Indonesia")
- predicate        — relation (e.g. "presiden_2024")
- object           — value/answer (e.g. "Prabowo Subianto")
- context          — JSON dict (period, source_chain, conditions)
- confidence       — float [0,1] from sanad agreement
- source_chain     — JSON list of {type, url, provider, retrieved_at}
- created_ts       — first seen
- last_seen_ts     — last reinforced
- reinforcement_count — how many times this claim repeated/confirmed
- contradicts      — JSON list of conflicting AKU ids
- domain           — fiqh/medis/coding/factual/casual/current_events
- decayed          — bool (low-confidence aged out)

Usage:
    from brain_qa.inventory_memory import lookup, ingest, stats
    hit = lookup("siapa presiden indonesia 2024", min_confidence=0.7)
    ingest(claim="Prabowo Subianto", subject="Indonesia",
           predicate="presiden_2024", sources=[{...}])
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_DB_PATH = Path("/opt/sidix/.data/inventory.db")
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── Schema bootstrap ────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS aku (
    aku_id              TEXT PRIMARY KEY,
    subject             TEXT NOT NULL,
    predicate           TEXT NOT NULL,
    object              TEXT NOT NULL,
    context             TEXT DEFAULT '{}',     -- JSON
    confidence          REAL DEFAULT 0.5,
    source_chain        TEXT DEFAULT '[]',     -- JSON list
    created_ts          INTEGER NOT NULL,
    last_seen_ts        INTEGER NOT NULL,
    reinforcement_count INTEGER DEFAULT 1,
    contradicts         TEXT DEFAULT '[]',     -- JSON list of aku_ids
    domain              TEXT DEFAULT 'general',
    decayed             INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_aku_subject ON aku(subject);
CREATE INDEX IF NOT EXISTS idx_aku_predicate ON aku(predicate);
CREATE INDEX IF NOT EXISTS idx_aku_domain_conf ON aku(domain, confidence);
CREATE INDEX IF NOT EXISTS idx_aku_created ON aku(created_ts);

-- FTS5 virtual table for fast natural-language lookup
CREATE VIRTUAL TABLE IF NOT EXISTS aku_fts USING fts5(
    aku_id UNINDEXED,
    subject,
    predicate,
    object,
    domain UNINDEXED,
    tokenize='porter unicode61'
);

-- Trigger: keep FTS in sync with main table
CREATE TRIGGER IF NOT EXISTS aku_ai AFTER INSERT ON aku BEGIN
    INSERT INTO aku_fts(aku_id, subject, predicate, object, domain)
    VALUES (new.aku_id, new.subject, new.predicate, new.object, new.domain);
END;

CREATE TRIGGER IF NOT EXISTS aku_ad AFTER DELETE ON aku BEGIN
    DELETE FROM aku_fts WHERE aku_id = old.aku_id;
END;

CREATE TRIGGER IF NOT EXISTS aku_au AFTER UPDATE ON aku BEGIN
    UPDATE aku_fts SET subject=new.subject, predicate=new.predicate,
                       object=new.object, domain=new.domain
    WHERE aku_id = new.aku_id;
END;
"""


def _conn() -> sqlite3.Connection:
    """Get connection (creates DB on first call)."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


# ── AKU dataclass ────────────────────────────────────────────────────────────

@dataclass
class AKU:
    """Atomic Knowledge Unit."""
    aku_id: str
    subject: str
    predicate: str
    object: str
    context: dict
    confidence: float
    source_chain: list[dict]
    created_ts: int
    last_seen_ts: int
    reinforcement_count: int
    contradicts: list[str]
    domain: str
    decayed: bool = False

    def to_dict(self) -> dict:
        return {
            "aku_id": self.aku_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "context": self.context,
            "confidence": self.confidence,
            "source_chain": self.source_chain,
            "created_ts": self.created_ts,
            "last_seen_ts": self.last_seen_ts,
            "reinforcement_count": self.reinforcement_count,
            "contradicts": self.contradicts,
            "domain": self.domain,
            "decayed": self.decayed,
        }


def _row_to_aku(row: sqlite3.Row) -> AKU:
    return AKU(
        aku_id=row["aku_id"],
        subject=row["subject"],
        predicate=row["predicate"],
        object=row["object"],
        context=json.loads(row["context"] or "{}"),
        confidence=row["confidence"],
        source_chain=json.loads(row["source_chain"] or "[]"),
        created_ts=row["created_ts"],
        last_seen_ts=row["last_seen_ts"],
        reinforcement_count=row["reinforcement_count"],
        contradicts=json.loads(row["contradicts"] or "[]"),
        domain=row["domain"],
        decayed=bool(row["decayed"]),
    )


def _make_aku_id(subject: str, predicate: str, object_: str) -> str:
    """Stable hash for AKU identity (collisions on identical claim = good, reinforce)."""
    raw = f"{subject.lower().strip()}|{predicate.lower().strip()}|{object_.lower().strip()}"
    return "aku-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


# ── Public API ──────────────────────────────────────────────────────────────

def ingest(
    *,
    subject: str,
    predicate: str,
    object: str,  # noqa: A002 (shadow builtin OK — schema field name)
    context: Optional[dict] = None,
    sources: Optional[list[dict]] = None,
    confidence: float = 0.7,
    domain: str = "general",
) -> str:
    """
    Insert or REINFORCE an AKU.
    Returns aku_id. If already exists: bump reinforcement_count + update confidence.

    `sources` example: [{"type":"web", "url":"...", "provider":"brave", "retrieved_at":ts}]
    """
    if not subject or not predicate or not object:
        raise ValueError("subject/predicate/object required")
    aku_id = _make_aku_id(subject, predicate, object)
    now = int(time.time())
    ctx_json = json.dumps(context or {}, ensure_ascii=False)
    src_json = json.dumps(sources or [], ensure_ascii=False)

    with _conn() as c:
        existing = c.execute(
            "SELECT aku_id, confidence, reinforcement_count, source_chain FROM aku WHERE aku_id=?",
            (aku_id,),
        ).fetchone()
        if existing:
            # Reinforce: blend confidence + add sources + bump count
            old_conf = existing["confidence"]
            new_conf = min(1.0, (old_conf + confidence) / 2 + 0.05)  # slight upward bias
            old_sources = json.loads(existing["source_chain"] or "[]")
            new_sources = old_sources + (sources or [])
            # Dedup sources by URL
            seen_urls = set()
            uniq_sources = []
            for s in new_sources:
                url = s.get("url", "")
                if url and url in seen_urls:
                    continue
                seen_urls.add(url)
                uniq_sources.append(s)
            c.execute(
                "UPDATE aku SET confidence=?, last_seen_ts=?, reinforcement_count=reinforcement_count+1, "
                "source_chain=? WHERE aku_id=?",
                (new_conf, now, json.dumps(uniq_sources, ensure_ascii=False), aku_id),
            )
            log.info("[inventory] reinforced %s conf=%.2f→%.2f", aku_id, old_conf, new_conf)
        else:
            c.execute(
                "INSERT INTO aku (aku_id, subject, predicate, object, context, confidence, "
                "source_chain, created_ts, last_seen_ts, reinforcement_count, contradicts, "
                "domain, decayed) VALUES (?,?,?,?,?,?,?,?,?,1,'[]',?,0)",
                (aku_id, subject, predicate, object, ctx_json, confidence, src_json,
                 now, now, domain),
            )
            log.info("[inventory] inserted %s subj=%r pred=%r obj=%r",
                     aku_id, subject[:30], predicate[:30], object[:50])
        c.commit()
    return aku_id


def lookup(
    query: str,
    *,
    min_confidence: float = 0.6,
    limit: int = 5,
    domain: Optional[str] = None,
) -> list[AKU]:
    """
    Natural-language lookup via FTS5 (BM25-ranked).
    Returns top-K AKUs with confidence ≥ threshold.
    """
    if not query.strip():
        return []
    # FTS5 needs OR-token query for natural lang match (vs phrase strict).
    # Tokenize: lowercase, strip punctuation, drop stopwords + short tokens
    import re
    stopwords = {"siapa", "apa", "kapan", "yang", "itu", "ini", "dari",
                 "ke", "di", "dan", "atau", "the", "is", "what", "who", "of"}
    tokens = re.findall(r"\w+", query.lower())
    keep = [t for t in tokens if t not in stopwords and len(t) >= 3]
    if not keep:
        keep = tokens  # fallback if all stopwords
    if not keep:
        return []
    # Build OR query: word1 OR word2 OR ...
    fts_query = " OR ".join(keep[:8])  # cap at 8 tokens
    with _conn() as c:
        try:
            rows = c.execute(
                "SELECT aku.* FROM aku JOIN aku_fts ON aku.aku_id = aku_fts.aku_id "
                "WHERE aku_fts MATCH ? AND aku.confidence >= ? AND aku.decayed = 0 "
                + ("AND aku.domain = ? " if domain else "") +
                "ORDER BY bm25(aku_fts) ASC, aku.confidence DESC LIMIT ?",
                ([fts_query, min_confidence] + ([domain] if domain else []) + [limit]),
            ).fetchall()
        except sqlite3.OperationalError as e:
            log.debug("[inventory] FTS error (likely empty/special chars): %s", e)
            return []
    return [_row_to_aku(r) for r in rows]


def lookup_exact(subject: str, predicate: str) -> Optional[AKU]:
    """Direct lookup by subject + predicate (skip FTS, exact match)."""
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM aku WHERE subject=? AND predicate=? AND decayed=0 "
            "ORDER BY confidence DESC LIMIT 1",
            (subject.strip(), predicate.strip()),
        ).fetchone()
    return _row_to_aku(row) if row else None


def stats() -> dict:
    """Inventory health snapshot."""
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM aku").fetchone()[0]
        active = c.execute("SELECT COUNT(*) FROM aku WHERE decayed=0").fetchone()[0]
        by_domain = dict(c.execute(
            "SELECT domain, COUNT(*) FROM aku WHERE decayed=0 GROUP BY domain"
        ).fetchall())
        avg_conf = c.execute("SELECT AVG(confidence) FROM aku WHERE decayed=0").fetchone()[0] or 0
        top_reinforced = c.execute(
            "SELECT subject, predicate, object, reinforcement_count, confidence "
            "FROM aku WHERE decayed=0 ORDER BY reinforcement_count DESC LIMIT 5"
        ).fetchall()
        latest = c.execute(
            "SELECT subject, predicate, object, created_ts FROM aku ORDER BY created_ts DESC LIMIT 5"
        ).fetchall()
    return {
        "total_akus": total,
        "active": active,
        "decayed": total - active,
        "avg_confidence": round(avg_conf, 3),
        "by_domain": by_domain,
        "top_reinforced": [
            {"s": r["subject"][:40], "p": r["predicate"][:30], "o": r["object"][:60],
             "count": r["reinforcement_count"], "conf": round(r["confidence"], 2)}
            for r in top_reinforced
        ],
        "latest": [
            {"s": r["subject"][:40], "p": r["predicate"][:30], "o": r["object"][:60],
             "created": datetime.fromtimestamp(r["created_ts"], timezone.utc).isoformat()}
            for r in latest
        ],
        "db_path": str(_DB_PATH),
        "db_size_kb": round(_DB_PATH.stat().st_size / 1024, 1) if _DB_PATH.exists() else 0,
    }


def decay_old(days: int = 30, threshold: float = 0.5) -> int:
    """
    Mark old low-confidence AKUs as decayed (soft-delete).
    Returns count decayed.
    """
    cutoff = int(time.time()) - days * 86400
    with _conn() as c:
        cur = c.execute(
            "UPDATE aku SET decayed=1 WHERE last_seen_ts<? AND confidence<? AND decayed=0",
            (cutoff, threshold),
        )
        c.commit()
        return cur.rowcount


def _jaccard_4gram(a: str, b: str) -> float:
    """Cheap similarity: 4-char ngram Jaccard. Fast for short strings."""
    if not a or not b:
        return 0.0
    set_a = set(a[i:i+4] for i in range(len(a) - 3))
    set_b = set(b[i:i+4] for i in range(len(b) - 3))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def synthesize(
    *,
    same_subject_threshold: float = 0.6,
    same_object_threshold: float = 0.7,
    dry_run: bool = False,
) -> dict:
    """
    Vol 23c: Synthesis pass over inventory.
    - Cluster AKUs by similar subject (>=threshold)
    - Within cluster, find duplicates (similar object) → merge: keep highest
      confidence, blend sources, increment reinforcement
    - Soft-delete (decayed=1) the weaker duplicates

    Returns stats: clusters_found, merges_applied, akus_decayed
    """
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM aku WHERE decayed=0 ORDER BY confidence DESC"
        ).fetchall()

    akus = [_row_to_aku(r) for r in rows]
    n_in = len(akus)

    # 1. Greedy cluster by subject similarity
    clusters: list[list[AKU]] = []
    for a in akus:
        placed = False
        for cluster in clusters:
            if _jaccard_4gram(a.subject.lower(), cluster[0].subject.lower()) >= same_subject_threshold:
                cluster.append(a)
                placed = True
                break
        if not placed:
            clusters.append([a])

    # 2. Within each cluster, find pairs with similar object → merge
    merges = []  # list of (canonical_id, decay_id)
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        # Sort by confidence desc — first wins as canonical
        cluster.sort(key=lambda x: (x.confidence, x.reinforcement_count), reverse=True)
        canonical = cluster[0]
        for dup in cluster[1:]:
            obj_sim = _jaccard_4gram(canonical.object.lower(), dup.object.lower())
            if obj_sim >= same_object_threshold:
                merges.append((canonical.aku_id, dup.aku_id, obj_sim))

    if dry_run:
        return {
            "input_akus": n_in,
            "clusters_found": len(clusters),
            "multi_member_clusters": sum(1 for c in clusters if len(c) > 1),
            "merge_candidates": len(merges),
            "dry_run": True,
            "sample_merges": merges[:5],
        }

    # 3. Apply: blend confidence + sources, soft-delete duplicate
    if merges:
        with _conn() as c:
            for canonical_id, dup_id, sim in merges:
                # Get both AKUs
                can_row = c.execute("SELECT * FROM aku WHERE aku_id=?", (canonical_id,)).fetchone()
                dup_row = c.execute("SELECT * FROM aku WHERE aku_id=?", (dup_id,)).fetchone()
                if not can_row or not dup_row:
                    continue
                # Blend: max conf, sum reinforcement, merge sources
                new_conf = min(1.0, max(can_row["confidence"], dup_row["confidence"]) + 0.05)
                new_reinforce = can_row["reinforcement_count"] + dup_row["reinforcement_count"]
                can_sources = json.loads(can_row["source_chain"] or "[]")
                dup_sources = json.loads(dup_row["source_chain"] or "[]")
                merged_sources = can_sources + dup_sources
                # Dedup
                seen = set()
                uniq = []
                for s in merged_sources:
                    key = s.get("url", "") + s.get("provider", "")
                    if key in seen:
                        continue
                    seen.add(key)
                    uniq.append(s)
                # Update canonical
                c.execute(
                    "UPDATE aku SET confidence=?, reinforcement_count=?, source_chain=?, "
                    "last_seen_ts=? WHERE aku_id=?",
                    (new_conf, new_reinforce, json.dumps(uniq, ensure_ascii=False),
                     int(time.time()), canonical_id),
                )
                # Soft-delete dup
                c.execute("UPDATE aku SET decayed=1 WHERE aku_id=?", (dup_id,))
            c.commit()

    return {
        "input_akus": n_in,
        "clusters_found": len(clusters),
        "multi_member_clusters": sum(1 for cl in clusters if len(cl) > 1),
        "merges_applied": len(merges),
        "dry_run": False,
    }


def format_lookup_for_render(akus: list[AKU]) -> str:
    """Format AKU lookup result as LLM context string."""
    if not akus:
        return ""
    lines = []
    for i, a in enumerate(akus, 1):
        sources_summary = ""
        if a.source_chain:
            sources_summary = f" [sumber: {len(a.source_chain)} ref]"
        lines.append(
            f"{i}. {a.subject} {a.predicate}: {a.object} "
            f"(conf={a.confidence:.2f}, reinforced={a.reinforcement_count}x{sources_summary})"
        )
    return "\n".join(lines)


__all__ = [
    "AKU", "ingest", "lookup", "lookup_exact",
    "stats", "decay_old", "synthesize", "format_lookup_for_render",
]
