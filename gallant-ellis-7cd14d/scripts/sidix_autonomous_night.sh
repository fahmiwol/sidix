#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_autonomous_night.sh — SIDIX Autonomous Self-Learning Cycle
# ─────────────────────────────────────────────────────────────────────────────
#
# Runs every 2 hours via cron. SIDIX:
#   1. Scans corpus untuk knowledge gaps (low-confidence claims, drift)
#   2. Auto-researches gaps via LearnAgent (50+ open data sources)
#   3. Generates draft research notes (queued, NOT auto-approved untuk safety)
#   4. Generates training pairs untuk LoRA retrain (Kaggle/RunPod nightly)
#   5. Logs everything ke /opt/sidix/.data/autonomous_log.jsonl
#
# Output:
#   - .data/autonomous_log.jsonl       — append-only log per cycle
#   - .data/growth_cycles.jsonl        — daily_growth report per cycle
#   - .data/queue/notes_pending/*.md   — draft notes awaiting review
#   - .data/training_pairs/*.jsonl     — training pairs for LoRA retrain
#
# Safety: notes are NOT auto-approved (auto_approve=False).
# Threads NOT auto-posted (queue_threads=False).
# Manual review needed before publishing.
#
# Manual run: bash /opt/sidix/scripts/sidix_autonomous_night.sh
# Cron: 0 */2 * * * /opt/sidix/scripts/sidix_autonomous_night.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
LOG_FILE="$LOG_DIR/autonomous_log.jsonl"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$LOG_DIR"

cd "$SIDIX_PATH"

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CYCLE_ID="cyc-$(date +%s)"

echo "[$TIMESTAMP] [$CYCLE_ID] === SIDIX Autonomous Night Cycle START ==="

# Load .env (BRAIN_QA_ADMIN_TOKEN, RUNPOD_API_KEY, etc)
if [ -f "$SIDIX_PATH/apps/brain_qa/.env" ]; then
    set -a
    source "$SIDIX_PATH/apps/brain_qa/.env"
    set +a
fi

PYTHONPATH="$SIDIX_PATH/apps/brain_qa" "$PYTHON_BIN" <<PYEOF
import json
import sys
import time
import traceback
from datetime import datetime, timezone

CYCLE_ID = "$CYCLE_ID"
LOG_FILE = "$LOG_FILE"

def log_event(event: str, data: dict):
    """Append structured event ke autonomous_log.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "event": event,
        **data,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[{event}] {json.dumps(data, ensure_ascii=False)[:200]}")


# ── Phase 1: daily_growth full cycle ─────────────────────────────────────────
log_event("phase_start", {"phase": "daily_growth"})
t0 = time.time()
try:
    from brain_qa.daily_growth import run_daily_growth
    report = run_daily_growth(
        top_n_gaps=3,
        min_frequency=1,
        auto_approve=False,    # SAFETY: drafts queued, not published
        queue_threads=False,   # SAFETY: no auto-post
        generate_pairs=True,
        dry_run=False,
        use_curriculum=True,   # explore curriculum if no gaps
    )
    duration_s = round(time.time() - t0, 2)
    log_event("daily_growth_done", {
        "duration_s": duration_s,
        "gaps_scanned": getattr(report, "gaps_scanned", 0),
        "drafts_generated": getattr(report, "notes_drafted", 0)
                            or getattr(report, "drafts_generated", 0),
        "drafts_queued": getattr(report, "drafts_queued", 0),
        "notes_approved": getattr(report, "notes_approved", 0),
        "training_pairs": getattr(report, "training_pairs_generated", 0),
        "exploration_topics": getattr(report, "exploration_topics", []),
    })
except Exception as e:
    log_event("daily_growth_error", {
        "duration_s": round(time.time() - t0, 2),
        "error": str(e)[:500],
        "tb": traceback.format_exc()[:1500],
    })


# ── Phase 2: knowledge gap snapshot ──────────────────────────────────────────
log_event("phase_start", {"phase": "gap_snapshot"})
try:
    from brain_qa.knowledge_gap_detector import get_gaps
    gaps = get_gaps(min_frequency=1, limit=10)
    log_event("gap_snapshot_done", {
        "gap_count": len(gaps),
        "top_5": [g.get("topic", "?") if isinstance(g, dict) else str(g)[:80] for g in gaps[:5]],
    })
except Exception as e:
    log_event("gap_snapshot_error", {"error": str(e)[:300]})


# ── Phase 3: corpus stats ────────────────────────────────────────────────────
try:
    from brain_qa.corpus import get_corpus_stats
    stats = get_corpus_stats()
    log_event("corpus_stats", stats)
except Exception as e:
    log_event("corpus_stats_error", {"error": str(e)[:300]})


# ── Phase 4: cache + embedding stats ─────────────────────────────────────────
try:
    from brain_qa.semantic_cache import get_semantic_cache
    from brain_qa.embedding_loader import get_active_model_info
    sc = get_semantic_cache()
    log_event("cache_stats", {
        "enabled": sc.enabled,
        "stats": sc.get_stats() if hasattr(sc, "get_stats") else {},
        "embedding": get_active_model_info(),
    })
except Exception as e:
    log_event("cache_stats_error", {"error": str(e)[:300]})


# ── Phase 5: pending drafts review reminder ──────────────────────────────────
import os
from pathlib import Path
queue_dir = Path("$SIDIX_PATH/.data/queue/notes_pending")
if queue_dir.exists():
    pending = list(queue_dir.glob("*.md"))
    log_event("review_queue", {
        "pending_count": len(pending),
        "oldest": str(min(pending, key=os.path.getctime).name) if pending else None,
        "newest": str(max(pending, key=os.path.getctime).name) if pending else None,
    })

log_event("cycle_complete", {"cycle_id": CYCLE_ID})
PYEOF

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$CYCLE_ID] === Cycle done ==="
echo ""

# Tail last 3 events for visibility
echo "Last 3 events from autonomous_log.jsonl:"
tail -3 "$LOG_FILE" 2>/dev/null || echo "(no log yet)"
