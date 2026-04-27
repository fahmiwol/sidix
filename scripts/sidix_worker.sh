#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_worker.sh — SIDIX Task Queue Worker (autonomous task execution)
# ─────────────────────────────────────────────────────────────────────────────
#
# User vision: SIDIX terus belajar, kerja, mencatat, eksperimen, iterasi.
# Solusi: task queue (.data/task_queue.jsonl) dengan many tasks pre-filled.
# Worker (cron) ambil 1 task → dispatch ke shadow_pool → log result → mark done.
#
# Cron: every 10 min (massive throughput across 24h = 144 tasks/day max)
# Output:
#   .data/task_results.jsonl      — per-task execution log
#   .data/task_queue_done.jsonl   — completed tasks (archive)
#
# Manual queue add:
#   echo '{"id":"t-001","type":"research","question":"What is X?"}' >> .data/task_queue.jsonl
# ─────────────────────────────────────────────────────────────────────────────

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
QUEUE_FILE="$LOG_DIR/task_queue.jsonl"
DONE_FILE="$LOG_DIR/task_queue_done.jsonl"
RESULTS_FILE="$LOG_DIR/task_results.jsonl"

mkdir -p "$LOG_DIR"
touch "$QUEUE_FILE" "$DONE_FILE" "$RESULTS_FILE"

cd "$SIDIX_PATH"
if [ -f "$SIDIX_PATH/apps/brain_qa/.env" ]; then
    set -a; source "$SIDIX_PATH/apps/brain_qa/.env"; set +a
fi

CYCLE_ID="wkr-$(date +%s)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Pop 1 task from queue (atomic-ish: take head line)
TASK_LINE=$(head -n 1 "$QUEUE_FILE" 2>/dev/null || echo "")
if [ -z "$TASK_LINE" ]; then
    echo "[$TIMESTAMP] [$CYCLE_ID] queue empty"
    exit 0
fi

# Remove popped line from queue
tail -n +2 "$QUEUE_FILE" > "$QUEUE_FILE.tmp" && mv "$QUEUE_FILE.tmp" "$QUEUE_FILE"

echo "[$TIMESTAMP] [$CYCLE_ID] processing task: $TASK_LINE"

PYTHONPATH="$SIDIX_PATH/apps/brain_qa" \
TASK_LINE="$TASK_LINE" CYCLE_ID="$CYCLE_ID" RESULTS_FILE="$RESULTS_FILE" DONE_FILE="$DONE_FILE" \
python3 <<'PYEOF'
import asyncio
import json
import os
import time
import traceback
from datetime import datetime, timezone

TASK_LINE = os.environ["TASK_LINE"]
CYCLE_ID = os.environ["CYCLE_ID"]
RESULTS_FILE = os.environ["RESULTS_FILE"]
DONE_FILE = os.environ["DONE_FILE"]

try:
    task = json.loads(TASK_LINE)
except Exception as e:
    print(f"[error] bad JSON: {e}")
    raise SystemExit(0)

task_id = task.get("id", f"unk-{int(time.time())}")
task_type = task.get("type", "research")
question = task.get("question", "")
hints = task.get("hints", "")

result = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "cycle_id": CYCLE_ID,
    "task_id": task_id,
    "task_type": task_type,
    "question": question,
    "ok": False,
    "consensus": "",
    "shadows": [],
    "error": "",
}

async def run():
    from brain_qa.shadow_pool import dispatch
    try:
        dr = await dispatch(question, top_k=3, timeout=25.0)
        result["ok"] = bool(dr.consensus_claim)
        result["consensus"] = dr.consensus_claim
        result["shadows"] = dr.contributing_shadows
        result["duration_ms"] = dr.total_duration_ms
        result["responses_count"] = len(dr.all_responses)
    except Exception as e:
        result["error"] = str(e)[:300]
        result["traceback"] = traceback.format_exc()[:1000]

asyncio.run(run())

with open(RESULTS_FILE, "a", encoding="utf-8") as f:
    f.write(json.dumps(result, ensure_ascii=False) + "\n")

# Mark task as done
done_entry = dict(task)
done_entry["completed_ts"] = datetime.now(timezone.utc).isoformat()
done_entry["cycle_id"] = CYCLE_ID
with open(DONE_FILE, "a", encoding="utf-8") as f:
    f.write(json.dumps(done_entry, ensure_ascii=False) + "\n")

print(f"[done] task={task_id} ok={result['ok']} shadows={result['shadows']} "
      f"consensus_len={len(result['consensus'])}")
PYEOF

QLEFT=$(wc -l < "$QUEUE_FILE")
DONECNT=$(wc -l < "$DONE_FILE")
echo "[$TIMESTAMP] [$CYCLE_ID] worker done. Queue remaining: $QLEFT, total done: $DONECNT"
