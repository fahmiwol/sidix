#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_reflect_day.sh — Sprint 36 Reflection Cycle (foundation Self-Improvement)
# ─────────────────────────────────────────────────────────────────────────────
#
# Cron: 0 2 * * * (02:00 UTC daily, post ODOA 23:00 + visioner Sun 00:00)
#
# Goal: SIDIX belajar dari kegagalan dirinya sendiri (internal critique),
# bukan cuma teacher consensus eksternal.
#
# Logic:
# 1. Baca activity_log + sidix_observations.jsonl hari kemarin
# 2. Ekstrak: failure pattern (sessions error/timeout), repeated tool sequence
# 3. Generate lessons/draft-{YYYY-MM-DD}.md dengan template
# 4. Owner verdict pending — approve via Telegram (Sprint 40) atau git review
#
# Compound: Sprint 23 ODOA (artifacts tracker), Sprint 31 cron stagger,
# Sprint 37 Hafidz Ledger (provenance hook).
# ─────────────────────────────────────────────────────────────────────────────

set -u
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
LESSONS_DIR="$LOG_DIR/lessons"

# Yesterday's date (UTC)
YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d)
TODAY=$(date -u +%Y-%m-%d)
TIMESTAMP=$(date -u -Iseconds)
CYCLE_ID="reflect-$(date +%s)"

mkdir -p "$LESSONS_DIR"

LESSON_FILE="$LESSONS_DIR/draft-$YESTERDAY.md"

echo "[$TIMESTAMP] [$CYCLE_ID] SIDIX Reflection Cycle START — analyzing $YESTERDAY"

# Sources to analyze
ACTIVITY_LOG="$LOG_DIR/sidix_observations.jsonl"
ODOA_REPORT="$LOG_DIR/odoa_reports/odoa-$YESTERDAY.json"
CLASSROOM_LOG="$LOG_DIR/classroom_log.jsonl"

# Run Python analyzer
PYTHONPATH="$SIDIX_PATH/apps/brain_qa" \
  REFLECT_LESSON_FILE="$LESSON_FILE" \
  REFLECT_DATE="$YESTERDAY" \
  REFLECT_CYCLE_ID="$CYCLE_ID" \
  python3 - <<'PYEOF'
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

LESSON_FILE = os.environ["REFLECT_LESSON_FILE"]
DATE = os.environ["REFLECT_DATE"]
CYCLE_ID = os.environ["REFLECT_CYCLE_ID"]

DATA_DIR = Path("/opt/sidix/.data")
ACTIVITY_LOG = DATA_DIR / "sidix_observations.jsonl"
ODOA_DIR = DATA_DIR / "odoa_reports"

print(f"[reflect] analyzing date={DATE}")

# Parse yesterday's observations
events = []
if ACTIVITY_LOG.exists():
    yesterday_dt = datetime.strptime(DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    next_day = yesterday_dt + timedelta(days=1)
    with open(ACTIVITY_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts_str = e.get("ts") or e.get("timestamp") or ""
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                if yesterday_dt <= ts < next_day:
                    events.append(e)
            except Exception:
                continue

print(f"[reflect] {len(events)} events from {DATE}")

# Pattern: failure detection
failures = []
tool_sequences = []
anomalies = []

for e in events:
    typ = (e.get("type") or e.get("event") or "").lower()
    msg = (e.get("message") or e.get("text") or e.get("desc") or "").lower()
    error = (e.get("error") or "").lower()

    # Failure markers
    if any(marker in msg + error for marker in ["error", "timeout", "failed", "gagal", "exception"]):
        failures.append({
            "ts": e.get("ts", ""),
            "type": typ,
            "summary": (msg or error)[:200],
        })

    # Tool action sequences (kalau ada track)
    if "action" in e or "tool" in typ:
        tool_sequences.append({
            "ts": e.get("ts", ""),
            "tool": e.get("action") or e.get("tool") or e.get("name") or "",
        })

print(f"[reflect] failures: {len(failures)} | tool actions: {len(tool_sequences)} | anomalies: {len(anomalies)}")

# Failure pattern grouping
failure_types = Counter()
for f in failures:
    # Strip variable parts (timestamps, IDs) for pattern grouping
    summary = re.sub(r"\d+", "N", f["summary"])
    summary = re.sub(r"[a-f0-9]{8,}", "HASH", summary)
    summary = summary[:150]
    failure_types[summary] += 1

repeated_failures = [(p, c) for p, c in failure_types.most_common(5) if c >= 2]

# Tool repetition (frequency)
tool_counter = Counter(t["tool"] for t in tool_sequences if t["tool"])
top_tools = tool_counter.most_common(8)

# ODOA report (kalau ada)
odoa_data = None
odoa_file = ODOA_DIR / f"odoa-{DATE}.json"
if odoa_file.exists():
    try:
        with open(odoa_file, encoding="utf-8") as f:
            odoa_data = json.load(f)
    except Exception:
        pass

# Generate lesson draft
lines = [
    "---",
    f"sanad_tier: unknown",
    f"reflection_cycle_id: {CYCLE_ID}",
    f"date: {DATE}",
    f"status: draft",
    f"owner_verdict: pending",
    "---",
    "",
    f"# Reflection Draft — {DATE}",
    "",
    f"**Generated**: {datetime.now(timezone.utc).isoformat()}",
    f"**Cycle**: {CYCLE_ID}",
    f"**Source**: activity_log + observations + ODOA report",
    "",
    "## 📊 Day Stats",
    "",
    f"- Events analyzed: **{len(events)}**",
    f"- Failures detected: **{len(failures)}**",
    f"- Tool actions: **{len(tool_sequences)}**",
]

if odoa_data:
    artifacts = odoa_data.get("artifacts_count", "?")
    commits = len(odoa_data.get("commits", []))
    lines.append(f"- ODOA artifacts: **{artifacts}** | commits: **{commits}**")

lines.extend(["", "## 🔍 Failure Patterns", ""])

if repeated_failures:
    for pattern, count in repeated_failures:
        lines.append(f"### Pattern (×{count}): `{pattern}`")
        # Find supporting episodes (max 3)
        supporting = [f for f in failures if re.sub(r"\d+", "N", re.sub(r"[a-f0-9]{8,}", "HASH", f["summary"]))[:150] == pattern][:3]
        for s in supporting:
            lines.append(f"- {s['ts']} — type={s['type']}")
        lines.append("")
        lines.append(f"**Proposed lesson**: investigate root cause this pattern, propose mitigation.")
        lines.append(f"**Confidence**: medium (auto-detected, owner review needed)")
        lines.append("")
else:
    lines.append("_No repeated failure pattern detected (count ≥2)._")
    lines.append("")

lines.extend(["", "## 🔧 Tool Usage Top-8", ""])
if top_tools:
    for tool, count in top_tools:
        lines.append(f"- `{tool}`: {count}×")
else:
    lines.append("_No tool actions logged._")

# Repeated tool sequence (for Sprint 38 Tool Synthesis seeds)
lines.extend(["", "## 🧬 Repeated Tool Sequences (Sprint 38 Tool Synthesis seed)", ""])
sequence_counter = Counter()
window_size = 3
tools = [t["tool"] for t in tool_sequences if t["tool"]]
for i in range(len(tools) - window_size + 1):
    seq = tuple(tools[i : i + window_size])
    sequence_counter[seq] += 1

repeated_seqs = [(seq, count) for seq, count in sequence_counter.most_common(5) if count >= 3]
if repeated_seqs:
    for seq, count in repeated_seqs:
        lines.append(f"- {' → '.join(seq)} ({count}×)")
    lines.append("")
    lines.append("→ Candidates untuk Tool Synthesis macro proposal (Sprint 38).")
else:
    lines.append("_No tool sequence repeated ≥3 detected._")

lines.extend([
    "",
    "## 📝 Proposed Actions (Owner Verdict Pending)",
    "",
    "1. [ ] Review failure patterns above",
    "2. [ ] Approve / edit / reject each pattern lesson",
    "3. [ ] Tag tool sequence candidates untuk Sprint 38 Tool Synthesis review",
    "",
    "## 🔒 Sanad Chain (Reflection Provenance)",
    "",
    f"- Lesson lahir dari: cycle `{CYCLE_ID}` analyzing `{DATE}`",
    f"- Sources: activity_log, observations, ODOA report",
    f"- Owner approval: **PENDING**",
    f"- Future: Hafidz Ledger entry post-approval (Sprint 37)",
    "",
    "---",
    "",
    f"_Generated by sidix_reflect_day.sh @ {CYCLE_ID}_",
])

# Write lesson draft
with open(LESSON_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"[reflect] lesson draft written: {LESSON_FILE}")
print(f"[reflect] DONE — failures={len(failures)} tool_actions={len(tool_sequences)} repeated_patterns={len(repeated_failures)} repeated_sequences={len(repeated_seqs)}")
PYEOF

EXIT_CODE=$?
echo "[$TIMESTAMP] [$CYCLE_ID] SIDIX Reflection Cycle DONE (exit=$EXIT_CODE)"
exit $EXIT_CODE
