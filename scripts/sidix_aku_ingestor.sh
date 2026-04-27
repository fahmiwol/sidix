#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_aku_ingestor.sh — Vol 23b: Auto-ingest AKU from new log entries
# ─────────────────────────────────────────────────────────────────────────────
#
# Cron every 10 min: scans shadow_experience.jsonl + classroom_log.jsonl +
# task_results.jsonl since last run, ingest new entries to inventory.db.
#
# Checkpoint: /opt/sidix/.data/aku_last_ingested_ts  (unix ts of last cycle)
# Output: /opt/sidix/.data/aku_ingest.log (cycle summary)
#
# This is what makes SIDIX literally TUMBUH otonom — every shadow worker
# cycle, every classroom session, every successful task → new AKU.
# 144 cycles/day max throughput (cron */10).
# ─────────────────────────────────────────────────────────────────────────────

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
CHECKPOINT="$LOG_DIR/aku_last_ingested_ts"
INGEST_LOG="$LOG_DIR/aku_ingest.log"

mkdir -p "$LOG_DIR"
touch "$CHECKPOINT" "$INGEST_LOG"
cd "$SIDIX_PATH"

CYCLE_ID="ing-$(date +%s)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LAST_TS=$(cat "$CHECKPOINT" 2>/dev/null || echo "0")
NOW_TS=$(date +%s)

echo "[$TIMESTAMP] [$CYCLE_ID] AKU ingestor: last=$LAST_TS now=$NOW_TS" >> "$INGEST_LOG"

PYTHONPATH="$SIDIX_PATH/apps/brain_qa" \
LAST_TS="$LAST_TS" CYCLE_ID="$CYCLE_ID" INGEST_LOG="$INGEST_LOG" \
python3 <<'PYEOF'
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/sidix/apps/brain_qa")
from brain_qa.inventory_memory import ingest, stats, decay_old

LAST_TS = float(os.environ.get("LAST_TS", "0") or 0)
CYCLE_ID = os.environ["CYCLE_ID"]
INGEST_LOG = os.environ["INGEST_LOG"]
DATA_DIR = Path("/opt/sidix/.data")


def parse_iso_to_ts(iso_str):
    """Parse ISO timestamp → unix ts (or 0 on fail)."""
    if not iso_str:
        return 0
    try:
        s = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0


# Same heuristics as sidix_aku_bootstrap.py (kept inline for cron simplicity)
QUESTION_PATTERNS = [
    (r"siapa\s+(.+?)(?:\?|$)", "identitas"),
    (r"apa\s+itu\s+(.+?)(?:\?|$)", "definisi"),
    (r"bagaimana\s+cara\s+(.+?)(?:\?|$)", "cara"),
    (r"jelaskan\s+(.+?)(?:\?|$)", "penjelasan"),
    (r"apa\s+(?:beda|perbedaan)\s+(.+?)(?:\?|$)", "perbedaan"),
    (r"kapan\s+(.+?)(?:\?|$)", "waktu"),
    (r"berapa\s+(.+?)(?:\?|$)", "jumlah"),
    (r"apa\s+(.+?)(?:\?|$)", "info"),
]

def infer_subject_predicate(question):
    q = question.lower().strip().rstrip("?!.,;")
    for pattern, pred in QUESTION_PATTERNS:
        m = re.match(pattern, q)
        if m:
            subj = m.group(1).strip()
            if subj:
                return subj[:200], pred
    return q[:200], "info"

def classify_domain(question, claim):
    text = (question + " " + claim).lower()
    if any(k in text for k in ["fiqh", "hukum", "puasa", "shalat", "hadith", "mazhab"]):
        return "fiqh"
    if any(k in text for k in ["python", "javascript", "code", "function", "async", "api"]):
        return "coding"
    if any(k in text for k in ["presiden", "menteri", "pemilu", "kpu"]):
        return "politics"
    if any(k in text for k in ["paper", "study", "arxiv", "research"]):
        return "science"
    if any(k in text for k in ["bisnis", "marketing", "saas", "startup"]):
        return "business"
    if any(k in text for k in ["ai", "llm", "model", "transformer", "neural"]):
        return "ai_research"
    return "general"

def shorten(claim, n=500):
    if len(claim) <= n:
        return claim.strip()
    cut = claim[:n]
    p = cut.rfind(".")
    if p > n * 0.5:
        return cut[:p+1].strip()
    return cut.strip()


# ── Mine each source for entries with ts > LAST_TS ──────────────────────────

n_shadow = n_class = n_pairs = n_tasks = 0

# Shadow experience
p = DATA_DIR / "shadow_experience.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
                ts = parse_iso_to_ts(e.get("ts", ""))
                if ts <= LAST_TS:
                    continue
                q = e.get("question", "")
                claim = e.get("claim", "")
                if not q or not claim:
                    continue
                subj, pred = infer_subject_predicate(q)
                domain = classify_domain(q, claim)
                sources = [
                    {"type": s.get("type", "web"), "url": s.get("url", ""),
                     "title": s.get("title", ""),
                     "provider": e.get("primary_teacher", "shadow"),
                     "retrieved_at": e.get("ts", "")}
                    for s in (e.get("sources") or [])
                ]
                conf = 0.65 if not sources else 0.75
                ingest(subject=subj, predicate=pred, object=shorten(claim),
                       context={"original_question": q, "shadow": e.get("shadow", "")},
                       sources=sources, confidence=conf, domain=domain)
                n_shadow += 1
            except Exception as ex:
                pass

# Classroom log
p = DATA_DIR / "classroom_log.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
                ts = parse_iso_to_ts(e.get("ts", ""))
                if ts <= LAST_TS:
                    continue
                q = e.get("question", "")
                if not q:
                    continue
                multi_ok = sum(1 for r in e.get("responses", []) if r.get("text"))
                conf = 0.5 + 0.1 * min(multi_ok, 4)
                for r in e.get("responses", []):
                    txt = r.get("text", "")
                    if not txt or len(txt) < 30:
                        continue
                    subj, pred = infer_subject_predicate(q)
                    domain = classify_domain(q, txt)
                    sources = [{"type": "llm_classroom",
                                "provider": r.get("provider", "?"),
                                "model": r.get("model", ""),
                                "retrieved_at": e.get("ts", "")}]
                    ingest(subject=subj, predicate=pred, object=shorten(txt),
                           context={"original_question": q,
                                    "classroom_session": e.get("cycle_id", "")},
                           sources=sources, confidence=conf, domain=domain)
                    n_class += 1
            except Exception:
                pass

# Classroom pairs (multi-teacher consensus)
p = DATA_DIR / "classroom_pairs.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
                ts = parse_iso_to_ts(e.get("ts", ""))
                if ts <= LAST_TS:
                    continue
                q = e.get("question", "")
                ans = e.get("answer", "")
                if not q or not ans:
                    continue
                subj, pred = infer_subject_predicate(q)
                domain = classify_domain(q, ans)
                providers = e.get("all_providers", [])
                sources = [{"type": "llm_consensus", "provider": pp,
                            "retrieved_at": e.get("ts", "")} for pp in providers]
                conf = 0.75 + 0.05 * min(len(providers), 5)
                ingest(subject=subj, predicate=pred, object=shorten(ans),
                       context={"original_question": q,
                                "primary_provider": e.get("primary_provider", "")},
                       sources=sources, confidence=conf, domain=domain)
                n_pairs += 1
            except Exception:
                pass

# Task results (only ok=true)
p = DATA_DIR / "task_results.jsonl"
if p.exists():
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                ts = parse_iso_to_ts(r.get("ts", ""))
                if ts <= LAST_TS:
                    continue
                if not r.get("ok") or not r.get("consensus"):
                    continue
                q = r.get("question", "")
                cs = r.get("consensus", "")
                if not q or not cs:
                    continue
                subj, pred = infer_subject_predicate(q)
                domain = classify_domain(q, cs)
                shadows = r.get("shadows", [])
                sources = [{"type": "shadow_consensus", "provider": s,
                            "retrieved_at": r.get("ts", "")} for s in shadows]
                conf = 0.7 + 0.05 * min(len(shadows), 4)
                ingest(subject=subj, predicate=pred, object=shorten(cs),
                       context={"original_question": q, "task_id": r.get("task_id", "")},
                       sources=sources, confidence=conf, domain=domain)
                n_tasks += 1
            except Exception:
                pass

# Decay daily (only on hourly tick — minute=0)
n_decayed = 0
n_synth_merges = 0
now = datetime.now(timezone.utc)
if now.minute < 10:  # within first 10 min of hour
    n_decayed = decay_old(days=30, threshold=0.5)
    # Vol 23c: synthesis loop hourly (cluster duplicates, canonicalize)
    try:
        from brain_qa.inventory_memory import synthesize
        sresult = synthesize(dry_run=False)
        n_synth_merges = sresult.get("merges_applied", 0)
    except Exception as e:
        print(f"[synthesize error] {e}")

total = n_shadow + n_class + n_pairs + n_tasks
log_entry = {
    "ts": now.isoformat(),
    "cycle_id": CYCLE_ID,
    "ingested_total": total,
    "from_shadow": n_shadow,
    "from_classroom": n_class,
    "from_pairs": n_pairs,
    "from_tasks": n_tasks,
    "decayed": n_decayed,
    "synth_merges": n_synth_merges,
    "stats_after": stats(),
}

with open(INGEST_LOG, "a", encoding="utf-8") as f:
    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

print(f"[{CYCLE_ID}] ingested {total} new (shadow={n_shadow} class={n_class} "
      f"pairs={n_pairs} tasks={n_tasks}) decayed={n_decayed}")
print(f"  stats: total={log_entry['stats_after']['total_akus']} "
      f"active={log_entry['stats_after']['active']} "
      f"avg_conf={log_entry['stats_after']['avg_confidence']}")
PYEOF

echo "$NOW_TS" > "$CHECKPOINT"
echo "[$TIMESTAMP] [$CYCLE_ID] checkpoint updated to $NOW_TS" >> "$INGEST_LOG"
