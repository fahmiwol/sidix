#!/usr/bin/env bash
# sidix_autodev_tick.sh — Cron wrapper for autonomous developer tick()
# Sprint 40 E2E — Schedule: */30 * * * * /opt/sidix/scripts/sidix_autodev_tick.sh
#
# Sets up environment then calls brain_qa autodev tick.
# Logs to /var/log/sidix_autodev.log (rotate via logrotate).
#
# Install cron:
#   crontab -e
#   */30 * * * * /opt/sidix/scripts/sidix_autodev_tick.sh >> /var/log/sidix_autodev.log 2>&1

set -euo pipefail

SIDIX_ROOT="${SIDIX_ROOT:-/opt/sidix}"
LOG_TAG="[sidix_autodev]"

echo "$LOG_TAG tick start — $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Load env if .env exists
if [ -f "$SIDIX_ROOT/.env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$SIDIX_ROOT/.env" | grep -v '^$' | xargs)
fi

# Default to real writes in production
export AUTODEV_DRY_RUN="${AUTODEV_DRY_RUN:-0}"
export SIDIX_DATA_DIR="${SIDIX_DATA_DIR:-/opt/sidix/.data}"

cd "$SIDIX_ROOT"

# Activate venv if present (same as start_brain.sh)
if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

# brain_qa is not installed as a pip package — set PYTHONPATH explicitly
export PYTHONPATH="$SIDIX_ROOT/apps/brain_qa:${PYTHONPATH:-}"

python3 -m brain_qa autodev tick \
    --repo-root "$SIDIX_ROOT" \
    2>&1 || echo "$LOG_TAG tick exit $?"

echo "$LOG_TAG tick done — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
