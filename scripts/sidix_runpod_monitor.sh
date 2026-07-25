#!/bin/bash
# Poll RunPod training status setiap 10 min
POD_SSH_HOST="87.197.146.56"
POD_SSH_PORT="40982"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOG="/opt/sidix/.data/runpod_monitor.log"
BREADCRUMB="/opt/sidix/.data/runpod_training_state.json"

# Test SSH + check PID
RESULT=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p $POD_SSH_PORT root@$POD_SSH_HOST "ps -p 331 > /dev/null && echo ALIVE || echo DEAD; tail -5 /workspace/train.log 2>/dev/null | head -3" 2>&1)
ALIVE=$(echo "$RESULT" | head -1)
TAIL=$(echo "$RESULT" | tail -3 | tr "\n" " " | head -c 300)

echo "[$TS] alive=$ALIVE tail_preview=\"$TAIL\"" >> "$LOG"
cat > "$BREADCRUMB" <<JSON
{"ts":"$TS","alive":"$ALIVE","tail":"$TAIL"}
JSON
