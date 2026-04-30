#!/bin/bash
# daily_synthesis.sh — Synthesize today's SIDIX state into 1-paragraph snapshot
# Cron: 22:00 daily
# Output: .data/daily_state/YYYY-MM-DD.md

set -e

cd /opt/sidix

TODAY=$(date +%Y-%m-%d)
OUT_DIR=".data/daily_state"
mkdir -p "$OUT_DIR"

# Count today sessions
SESSION_COUNT=$(find .data/sessions -name "session_*.json" -newermt "$TODAY 00:00" 2>/dev/null | wc -l)

# Count critique flags
CRITIQUE_FILE=".data/critique/critique_$TODAY.json"
HALU_COUNT=0
DRIFT_COUNT=0
if [ -f "$CRITIQUE_FILE" ]; then
    HALU_COUNT=$(python3 -c "import json; d=json.load(open('$CRITIQUE_FILE')); print(len(d.get('halu_flags',[])))" 2>/dev/null || echo 0)
    DRIFT_COUNT=$(python3 -c "import json; d=json.load(open('$CRITIQUE_FILE')); print(len(d.get('persona_drift_flags',[])))" 2>/dev/null || echo 0)
fi

# Count corpus docs
CORPUS_COUNT=$(find brain/public -name "*.md" 2>/dev/null | wc -l)

# Git status
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

cat << EOF > "$OUT_DIR/$TODAY.md"
# SIDIX Daily State — $TODAY

- **Sessions today**: $SESSION_COUNT
- **Corpus docs**: $CORPUS_COUNT
- **Critique halu flags**: $HALU_COUNT
- **Critique drift flags**: $DRIFT_COUNT
- **Git**: $GIT_BRANCH @ $GIT_COMMIT
- **VPS uptime**: $(uptime -p 2>/dev/null || echo "N/A")

## Synthesis

SIDIX operated $SESSION_COUNT sessions today across persona fanout.
$(if [ "$HALU_COUNT" -gt 0 ]; then echo "⚠️ $HALU_COUNT halu flags detected — review needed."; else echo "✅ No halu flags."; fi)
$(if [ "$DRIFT_COUNT" -gt 0 ]; then echo "⚠️ $DRIFT_COUNT persona drift flags — alignment review needed."; else echo "✅ No persona drift."; fi)

*Auto-generated at $(date -Iseconds)*
EOF

echo "[daily_synthesis] written $OUT_DIR/$TODAY.md"
