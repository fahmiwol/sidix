#!/bin/bash
# cleanup_generated_files.sh — Sprint Storage Hygiene
#
# Hapus generated files (image/audio/video/3d) yang lebih dari N hari.
# Default 7 hari. Storage tidak meledak dari user testing image gen.
#
# Cron entry:
#   0 3 * * * /opt/sidix/scripts/cleanup_generated_files.sh >> /var/log/sidix/cleanup.log 2>&1

set -u
DAYS="${SIDIX_CLEANUP_DAYS:-7}"
DRY_RUN="${SIDIX_CLEANUP_DRY_RUN:-0}"

LOG_DIR="/opt/sidix/.data"
mkdir -p "$LOG_DIR"

DIRS=(
  "/opt/sidix/generated_images"
  "/opt/sidix/generated_audio"
  "/opt/sidix/generated_videos"
  "/opt/sidix/generated_3d"
  "/opt/sidix/tts_out"
)

TS=$(date -Iseconds)
TOTAL_DELETED=0
TOTAL_BYTES_FREED=0

for dir in "${DIRS[@]}"; do
  if [ ! -d "$dir" ]; then continue; fi

  # Find files older than DAYS
  if [ "$DRY_RUN" = "1" ]; then
    # Just count
    count=$(find "$dir" -type f -mtime +$DAYS 2>/dev/null | wc -l)
    bytes=$(find "$dir" -type f -mtime +$DAYS -exec du -cb {} + 2>/dev/null | tail -1 | awk '{print $1}')
    bytes=${bytes:-0}
    echo "[$TS] DRY_RUN $dir: would delete $count files ($bytes bytes)"
  else
    # Capture stats then delete
    count=$(find "$dir" -type f -mtime +$DAYS 2>/dev/null | wc -l)
    bytes=$(find "$dir" -type f -mtime +$DAYS -exec du -cb {} + 2>/dev/null | tail -1 | awk '{print $1}')
    bytes=${bytes:-0}
    find "$dir" -type f -mtime +$DAYS -delete 2>/dev/null
    TOTAL_DELETED=$((TOTAL_DELETED + count))
    TOTAL_BYTES_FREED=$((TOTAL_BYTES_FREED + bytes))
    echo "[$TS] $dir: deleted $count files (~${bytes} bytes)"
  fi
done

if [ "$DRY_RUN" != "1" ]; then
  echo "[$TS] TOTAL: deleted $TOTAL_DELETED files, freed ${TOTAL_BYTES_FREED} bytes (~$((TOTAL_BYTES_FREED / 1024 / 1024)) MB)"
  echo "{\"timestamp\":\"$TS\",\"deleted\":$TOTAL_DELETED,\"bytes_freed\":$TOTAL_BYTES_FREED,\"days\":$DAYS}" >> "$LOG_DIR/cleanup_history.jsonl"
fi

exit 0
