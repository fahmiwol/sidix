#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_radar.sh — Phase 1 MVP: 3-channel mention listener
# ─────────────────────────────────────────────────────────────────────────────
# Polls Google News + Reddit + GitHub every 30 min for "SIDIX" mentions.
# Mode: LISTEN-ONLY. Logs to .data/radar_mentions.jsonl
# Vol 27a Phase 1 — see brain/public/research_notes/245_*.md
# ─────────────────────────────────────────────────────────────────────────────

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
RADAR_LOG="$LOG_DIR/radar_mentions.jsonl"

mkdir -p "$LOG_DIR"

CYCLE_ID="rad-$(date +%s)"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TIMESTAMP] [$CYCLE_ID] SIDIX Radar tick"

# Pass log file + cycle ID as ENV (no heredoc substitution issues)
SIDIX_RADAR_LOG="$RADAR_LOG" SIDIX_CYCLE_ID="$CYCLE_ID" \
  PYTHONPATH="$SIDIX_PATH/apps/brain_qa" python3 - <<'PYEOF'
import json, os, urllib.request, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime, timezone

LOG_FILE = os.environ["SIDIX_RADAR_LOG"]
CYCLE_ID = os.environ["SIDIX_CYCLE_ID"]
HEADERS = {"User-Agent": "SIDIX-Radar/1.0 (https://sidixlab.com)"}

def log_mention(channel, url, title, snippet=""):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "cycle_id": CYCLE_ID,
        "channel": channel,
        "url": url,
        "title": (title or "")[:300],
        "snippet": (snippet or "")[:500],
        "sentiment": "unknown",
        "intent": "unclassified",
        "is_about_us": None,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  [{channel}] {title[:120]}")

# Channel 1: Google News RSS
try:
    url = "https://news.google.com/rss/search?q=%22SIDIX%22+OR+%22sidixlab%22&hl=id&gl=ID"
    req = urllib.request.Request(url, headers=HEADERS)
    body = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="ignore")
    items = ET.fromstring(body).findall(".//item")[:10]
    hits = 0
    for item in items:
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link") or "").strip()
        desc  = (item.findtext("description") or "").strip()
        if "sidix" in (title + desc).lower():
            log_mention("google_news", link, title, desc[:300])
            hits += 1
    print(f"google_news: {len(items)} checked, {hits} matched")
except Exception as e:
    print(f"google_news error: {e}")

# Channel 2: Reddit public search
try:
    url = "https://www.reddit.com/search.json?q=SIDIX&sort=new&limit=10"
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
    posts = data.get("data", {}).get("children", [])
    hits = 0
    for p in posts[:10]:
        d = p.get("data", {})
        title = d.get("title", "")
        if "sidix" in title.lower():
            log_mention("reddit",
                        "https://reddit.com" + d.get("permalink", ""),
                        title, (d.get("selftext","") or "")[:300])
            hits += 1
    print(f"reddit: {len(posts)} checked, {hits} matched")
except Exception as e:
    print(f"reddit error: {e}")

# Channel 3: GitHub code search
try:
    url = "https://api.github.com/search/code?q=SIDIX+language:md&per_page=10"
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
    items = data.get("items", [])
    hits = 0
    for item in items[:10]:
        repo = item.get("repository", {}).get("full_name", "?")
        # skip own repo
        if "fahmiwol/sidix" in repo or "tiranyx" in repo.lower():
            continue
        log_mention("github", item.get("html_url",""),
                    f"{repo}: {item.get('path','?')}", "")
        hits += 1
    print(f"github: {len(items)} checked, {hits} matched (own repo filtered)")
except urllib.error.HTTPError as e:
    if e.code == 403:
        print("github: rate-limited (OK, auth-less endpoint)")
    else:
        print(f"github HTTPError: {e}")
except Exception as e:
    print(f"github error: {e}")

print(f"radar tick {CYCLE_ID} done")
PYEOF

COUNT=$(wc -l < "$RADAR_LOG" 2>/dev/null || echo 0)
echo "[$TIMESTAMP] [$CYCLE_ID] radar done. Total mentions logged ever: $COUNT"
