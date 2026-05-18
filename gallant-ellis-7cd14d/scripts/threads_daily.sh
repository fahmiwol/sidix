#!/bin/bash
# SIDIX Threads daily cycle — dijalankan dari cron
# Fixed version: 2026-04-19 (escape chars sebelumnya broken)

BASE="http://localhost:8765"
LOG="/var/log/sidix_threads.log"

# Pastikan log file writable
touch "$LOG" 2>/dev/null || LOG="/tmp/sidix_threads.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

case "$1" in
  post)
    log "=== Daily post cycle start ==="
    RESULT=$(curl -s -X POST "$BASE/threads/scheduler/run" \
      -H 'Content-Type: application/json' \
      -d '{"dry_run":false}')
    log "post: $RESULT"
    ;;

  harvest)
    log "=== Harvest cycle start ==="
    RESULT=$(curl -s -X POST "$BASE/threads/scheduler/harvest" \
      -H 'Content-Type: application/json')
    log "harvest: $RESULT"
    ;;

  mentions)
    log "=== Mentions cycle start ==="
    RESULT=$(curl -s -X POST "$BASE/threads/scheduler/mentions" \
      -H 'Content-Type: application/json' \
      -d '{"dry_run":false}')
    log "mentions: $RESULT"
    ;;

  consume-queue)
    # NEW: consume growth_queue dari daily_growth pipeline
    log "=== Growth queue consume ==="
    RESULT=$(curl -s -X POST "$BASE/sidix/threads-queue/consume?max_posts=2&dry_run=false")
    log "consume-queue: $RESULT"
    ;;

  series-hook)
    log "=== Series hook (morning) ==="
    RESULT=$(curl -s -X POST "$BASE/threads/series/post/hook")
    log "series-hook: $RESULT"
    ;;

  series-detail)
    log "=== Series detail (afternoon) ==="
    RESULT=$(curl -s -X POST "$BASE/threads/series/post/detail")
    log "series-detail: $RESULT"
    ;;

  series-cta)
    log "=== Series CTA (evening) ==="
    RESULT=$(curl -s -X POST "$BASE/threads/series/post/cta")
    log "series-cta: $RESULT"
    ;;

  status)
    curl -s "$BASE/threads/scheduler/stats" | python3 -m json.tool 2>&1
    curl -s "$BASE/sidix/threads-queue/status" | python3 -m json.tool 2>&1
    ;;

  *)
    echo "Usage: $0 {post|harvest|mentions|consume-queue|series-hook|series-detail|series-cta|status}"
    exit 1
    ;;
esac
