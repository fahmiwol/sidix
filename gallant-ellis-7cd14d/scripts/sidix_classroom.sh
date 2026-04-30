#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_classroom.sh — SIDIX Learning Classroom (background)
# ─────────────────────────────────────────────────────────────────────────────
#
# Setiap 1 jam: ambil 1 curriculum question, kirim ke SEMUA teacher LLM
# yang available (gemini/kimi/openrouter/groq/together/hf/cloudflare/ownpod),
# log jawaban masing-masing, extract pattern, simpan untuk training data.
#
# Output:
#   .data/classroom_log.jsonl  — per-question multi-teacher transcript
#   .data/classroom_pairs.jsonl — extracted (Q, multi-A consensus) pairs
#
# Curriculum: rotates over 50+ topics:
#   - faktual umum (geografi, sejarah, sains)
#   - SIDIX domain (Islamic epistemology, AI agent, persona system)
#   - coding patterns (Python, async, refactoring)
#   - current events (politik, teknologi, ekonomi)
#
# Cron: 0 * * * * /opt/sidix/scripts/sidix_classroom.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
CLASSROOM_LOG="$LOG_DIR/classroom_log.jsonl"
PAIRS_LOG="$LOG_DIR/classroom_pairs.jsonl"

mkdir -p "$LOG_DIR"
cd "$SIDIX_PATH"

# Load env
if [ -f "$SIDIX_PATH/apps/brain_qa/.env" ]; then
    set -a; source "$SIDIX_PATH/apps/brain_qa/.env"; set +a
fi

CYCLE_ID="cls-$(date +%s)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] [$CYCLE_ID] SIDIX Classroom session START"

PYTHONPATH="$SIDIX_PATH/apps/brain_qa" CLASSROOM_LOG="$CLASSROOM_LOG" PAIRS_LOG="$PAIRS_LOG" CYCLE_ID="$CYCLE_ID" python3 <<'PYEOF'
import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone

CLASSROOM_LOG = os.environ["CLASSROOM_LOG"]
PAIRS_LOG = os.environ["PAIRS_LOG"]
CYCLE_ID = os.environ["CYCLE_ID"]

CURRICULUM = [
    # SIDIX domain
    "Apa itu sanad dalam tradisi keilmuan Islam?",
    "Jelaskan konsep ReAct dalam AI agent",
    "Apa beda RAG dan fine-tuning untuk knowledge update?",
    "Bagaimana cara menerapkan epistemic honesty di output LLM?",
    "Apa itu LoRA adapter dan kenapa lebih efisien dari full fine-tuning?",
    # Faktual
    "Apa ibu kota baru Indonesia?",
    "Siapa presiden Indonesia saat ini?",
    "Berapa jumlah provinsi di Indonesia?",
    "Apa bahasa resmi Singapura?",
    "Kapan kemerdekaan Indonesia diproklamasikan?",
    # Coding / tech
    "Apa beda async dan multi-threading di Python?",
    "Kapan harus pakai dataclass vs Pydantic?",
    "Bagaimana pattern Producer-Consumer di asyncio?",
    "Apa itu HTTP/2 multiplexing?",
    "Kapan harus pakai Redis vs PostgreSQL?",
    # Filosofis / reflektif
    "Apa beda pengetahuan dan kebijaksanaan?",
    "Kenapa AI butuh epistemic humility?",
    "Apa peran sanad chain dalam validasi klaim?",
    # Current events
    "Apa berita teknologi penting 2025?",
    "Bagaimana perkembangan open-source AI tahun ini?",
]

# Pick 1 question this cycle (rotation by hour)
hour = datetime.now().hour
question = CURRICULUM[hour % len(CURRICULUM)]

print(f"Question (h{hour}): {question}")

async def run_classroom():
    from brain_qa.external_llm_pool import consensus_async, list_available_providers, consensus_summary
    available = list_available_providers()
    enabled = [p for p, ok in available.items() if ok]
    print(f"Available teachers: {enabled}")
    if not enabled:
        return None
    answers = await consensus_async(
        question, persona="ALEY",
        providers=enabled, timeout=30.0,
    )
    summary = consensus_summary(answers)
    return question, answers, summary, enabled

result = asyncio.run(run_classroom())
if result is None:
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "question": question,
        "error": "no teachers available",
    }
    with open(CLASSROOM_LOG, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    print("No teachers configured. Set API keys in .env.")
else:
    q, answers, summary, enabled = result
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "question": q,
        "summary": summary,
        "responses": [
            {"provider": a.provider, "model": a.model, "text": a.text,
             "duration_ms": a.duration_ms, "error": a.error[:200] if a.error else ""}
            for a in answers
        ],
    }
    with open(CLASSROOM_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # Extract training pair (multi-teacher consensus = high-quality answer)
    valid = [a for a in answers if a.text and not a.error]
    if len(valid) >= 2:
        # Use longest non-empty answer as primary (proxy for completeness)
        best = max(valid, key=lambda a: len(a.text))
        pair = {
            "question": q,
            "answer": best.text,
            "consensus_size": len(valid),
            "all_providers": [a.provider for a in valid],
            "primary_provider": best.provider,
            "primary_model": best.model,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        with open(PAIRS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        print(f"Training pair extracted: {len(valid)} teachers contributed")

    print(f"\nSummary: {json.dumps(summary, indent=2, ensure_ascii=False)[:500]}")
PYEOF

CLASSROOM_COUNT=$(wc -l < "$CLASSROOM_LOG" 2>/dev/null || echo 0)
PAIRS_COUNT=$(wc -l < "$PAIRS_LOG" 2>/dev/null || echo 0)
echo "[$TIMESTAMP] [$CYCLE_ID] classroom done. Total sessions: $CLASSROOM_COUNT, pairs: $PAIRS_COUNT"
