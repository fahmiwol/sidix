#!/bin/bash
# Poll Kaggle kernel status setiap 15 menit, log ke .data/kaggle_monitor.log
# Kalau status berubah dari RUNNING → COMPLETE/ERROR, write breadcrumb file
# yang bisa di-detect agent next session.
KERNEL="mighan/sidix-dora-persona-train-v1"
LOG="/opt/sidix/.data/kaggle_monitor.log"
BREADCRUMB="/opt/sidix/.data/kaggle_kernel_state.json"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
STATUS=$(kaggle kernels status "$KERNEL" 2>&1 | grep -oE "Kernel.*Status\.[A-Z]+" | grep -oE "[A-Z]+$" || echo "UNKNOWN")
echo "[$TS] kernel=$KERNEL status=$STATUS" >> "$LOG"
cat > "$BREADCRUMB" <<EOF
{"kernel":"$KERNEL","status":"$STATUS","last_check":"$TS"}
EOF
