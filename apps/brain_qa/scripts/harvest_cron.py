"""
harvest_cron.py — Auto-Harvest Cron Entry Point

CLI untuk auto-harvest yang dijalankan oleh cron setiap 6 jam.
Fetch trending topics → Wikipedia → generate notes → reindex BM25.

Usage:
    # Manual run
    cd /opt/sidix/apps/brain_qa
    python3 scripts/harvest_cron.py

    # Dengan custom topics
    python3 scripts/harvest_cron.py --topics "AI Indonesia,startup 2024"

    # Dry run (tidak save)
    python3 scripts/harvest_cron.py --dry-run

    # Via cron (tambah ke crontab):
    # 0 */6 * * * cd /opt/sidix/apps/brain_qa && python3 scripts/harvest_cron.py >> /var/log/sidix_harvest.log 2>&1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.auto_harvest import AutoHarvest


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SIDIX Auto-Harvest Cron")
    p.add_argument(
        "--topics",
        default="",
        help="Comma-separated list of topics to harvest (default: auto from Google Trends)",
    )
    p.add_argument(
        "--max-topics",
        type=int,
        default=5,
        help="Max topics to process per run (default: 5)",
    )
    p.add_argument(
        "--max-articles",
        type=int,
        default=2,
        help="Max Wikipedia articles per topic (default: 2)",
    )
    p.add_argument(
        "--backend-url",
        default="http://localhost:8765",
        help="Brain QA backend URL for reindex trigger",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print topics + articles without saving",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args()


async def run_harvest(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [harvest] %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    custom_topics = [t.strip() for t in args.topics.split(",") if t.strip()] if args.topics else None

    if args.dry_run:
        from brain_qa.auto_harvest import _fetch_google_trends_id, FALLBACK_TOPICS_ID, _wikipedia_search
        topics = custom_topics or _fetch_google_trends_id(args.max_topics) or FALLBACK_TOPICS_ID[:args.max_topics]
        print(f"[DRY RUN] Topics: {topics}")
        for topic in topics:
            articles = _wikipedia_search(topic, limit=args.max_articles)
            print(f"\nTopic: {topic} → {len(articles)} articles")
            for a in articles:
                print(f"  - {a['title']} ({len(a.get('text',''))} chars) {a['url'][:60]}")
        return

    harvester = AutoHarvest(
        backend_url=args.backend_url,
        max_topics=args.max_topics,
        max_articles_per_topic=args.max_articles,
    )
    stats = await harvester.run(topics=custom_topics)
    print(json.dumps(stats, indent=2))

    # Exit non-zero if no notes saved and there were errors
    if stats["notes_saved"] == 0 and stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_harvest(args))
