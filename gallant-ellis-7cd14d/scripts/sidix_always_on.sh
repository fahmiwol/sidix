#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_always_on.sh — SIDIX as 3rd Participant (continuous, not just night)
# ─────────────────────────────────────────────────────────────────────────────
#
# Replaces sidix_autonomous_night.sh. SIDIX runs CONTINUOUSLY (every 15 min):
#   - Observe git activity (new commits since last run)
#   - Extract AKUs (atomic knowledge units) from commit messages + diffs
#   - Run partial daily_growth (1 gap/cycle, not 3)
#   - Append observations to dedicated SIDIX channel
#   - Self-log progress
#
# Philosophy: SIDIX is in the conversation, not a tool. Pihak ke-3.
# It observes user+Claude exchanges via git history (the conversation's artifact)
# and contributes its own observations + research.
#
# Logs:
#   .data/sidix_observations.jsonl   # SIDIX's own running journal
#   .data/autonomous_log.jsonl       # cycle-level events
#   .data/last_observed_commit.txt   # state checkpoint
# ─────────────────────────────────────────────────────────────────────────────

set -e

SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
CYCLE_LOG="$LOG_DIR/autonomous_log.jsonl"
OBSERV_LOG="$LOG_DIR/sidix_observations.jsonl"
LAST_COMMIT_FILE="$LOG_DIR/last_observed_commit.txt"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$LOG_DIR"
cd "$SIDIX_PATH"

CYCLE_ID="cyc-$(date +%s)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] [$CYCLE_ID] SIDIX always-on tick"

# Load env
if [ -f "$SIDIX_PATH/apps/brain_qa/.env" ]; then
    set -a; source "$SIDIX_PATH/apps/brain_qa/.env"; set +a
fi

# ── Phase A: Git Observer (real-time conversation tracker) ────────────────────
LAST_OBSERVED=$(cat "$LAST_COMMIT_FILE" 2>/dev/null || echo "")
CURRENT_HEAD=$(git rev-parse HEAD)

if [ "$LAST_OBSERVED" != "$CURRENT_HEAD" ]; then
    if [ -n "$LAST_OBSERVED" ]; then
        NEW_COMMITS=$(git log --oneline "$LAST_OBSERVED..$CURRENT_HEAD" 2>/dev/null | head -20)
    else
        NEW_COMMITS=$(git log --oneline -5)
    fi

    PYTHONPATH="$SIDIX_PATH/apps/brain_qa" "$PYTHON_BIN" <<PYEOF
import json
import subprocess
from datetime import datetime, timezone

def write_observation(text, kind="observation"):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": "$CYCLE_ID",
        "kind": kind,
        "text": text,
    }
    with open("$OBSERV_LOG", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# Parse new commits
commits = """$NEW_COMMITS""".strip().split("\n")
if commits and commits[0]:
    write_observation(
        f"Observed {len(commits)} new commit(s) since last tick",
        kind="git_activity",
    )
    for c in commits[:10]:
        if c.strip():
            write_observation(c.strip(), kind="commit_seen")

    # Bonus: count total LOC delta + files touched
    try:
        if "$LAST_OBSERVED":
            stats = subprocess.run(
                ["git", "diff", "--shortstat", "$LAST_OBSERVED..HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            if stats.stdout.strip():
                write_observation(stats.stdout.strip(), kind="diff_stats")
    except Exception:
        pass
PYEOF

    echo "$CURRENT_HEAD" > "$LAST_COMMIT_FILE"
fi

# ── Phase B: Mini Growth Cycle (lighter, every 15 min instead of 2h) ─────────
PYTHONPATH="$SIDIX_PATH/apps/brain_qa" "$PYTHON_BIN" <<PYEOF
import json
import time
import traceback
from datetime import datetime, timezone

CYCLE_ID = "$CYCLE_ID"

def log_cycle(event, data):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "event": event,
        **data,
    }
    with open("$CYCLE_LOG", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def write_observation(text, kind="observation"):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "kind": kind,
        "text": text,
    }
    with open("$OBSERV_LOG", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# Sub-phase: gap snapshot (cheap, every cycle)
try:
    from brain_qa.knowledge_gap_detector import get_gaps
    gaps = get_gaps(min_frequency=1, limit=5)
    log_cycle("gap_snapshot", {
        "count": len(gaps),
        "top": [g.get("topic","?")[:80] if isinstance(g,dict) else str(g)[:80] for g in gaps[:3]],
    })
except Exception as e:
    log_cycle("gap_snapshot_error", {"err": str(e)[:200]})

# Sub-phase: corpus health
try:
    from brain_qa.corpus import get_corpus_stats
    stats = get_corpus_stats()
    log_cycle("corpus_stats", stats)
except Exception as e:
    log_cycle("corpus_stats_error", {"err": str(e)[:200]})

# Sub-phase: cache health
try:
    from brain_qa.semantic_cache import get_semantic_cache
    sc = get_semantic_cache()
    log_cycle("cache_health", {"enabled": sc.enabled})
except Exception as e:
    pass

# Sub-phase: full daily_growth ONLY at hour-mark cycles to avoid overuse
import datetime as _dt
now = _dt.datetime.now()
is_hour_mark = (now.minute < 15)  # only top of hour cycles

if is_hour_mark:
    log_cycle("phase_start", {"phase": "daily_growth_hourly"})
    t0 = time.time()
    try:
        from brain_qa.daily_growth import run_daily_growth
        report = run_daily_growth(
            top_n_gaps=1,          # smaller, frequent vs big nightly
            min_frequency=1,
            auto_approve=False,    # SAFE: queue
            queue_threads=False,
            generate_pairs=True,
            dry_run=False,
            use_curriculum=True,
        )
        log_cycle("daily_growth_done", {
            "duration_s": round(time.time()-t0, 2),
            "gaps_scanned": getattr(report, "gaps_scanned", 0),
            "drafts_generated": getattr(report, "drafts_generated", 0),
            "training_pairs": getattr(report, "training_pairs_generated", 0),
        })
        write_observation(
            f"Hourly growth: scanned {getattr(report,'gaps_scanned',0)} gaps, "
            f"drafted {getattr(report,'drafts_generated',0)} notes",
            kind="self_progress",
        )
    except Exception as e:
        log_cycle("daily_growth_error", {
            "duration_s": round(time.time()-t0, 2),
            "error": str(e)[:300],
            "tb": traceback.format_exc()[:1000],
        })
        write_observation(f"Hourly growth failed: {str(e)[:200]}", kind="self_error")

log_cycle("cycle_complete", {})
PYEOF

# Compact summary
TICK_COUNT=$(wc -l < "$CYCLE_LOG" 2>/dev/null || echo 0)
OBSERV_COUNT=$(wc -l < "$OBSERV_LOG" 2>/dev/null || echo 0)
echo "[$TIMESTAMP] [$CYCLE_ID] tick done. Total cycle events: $TICK_COUNT, observations: $OBSERV_COUNT"
