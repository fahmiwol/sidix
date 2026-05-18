"""
startup-fetch.py — SIDIX Auto-Knowledge Fetcher

Dijalankan setiap startup Windows (via Task Scheduler).
Fetch artikel umum dari Wikipedia, ArXiv, tech news → simpan ke corpus → reindex.

Topics sesuai persona SIDIX:
- MIGHAN: AI image gen, video gen, music gen, design tools
- TOARD: AI planning, productivity, project management
- FACH: Machine learning, NLP, computer science
- HAYFAR: Python, API, backend, DevOps
- INAN: General tech news, AI news Indonesia

Cara jalankan:
  python startup-fetch.py
  python startup-fetch.py --topics "AI image generation" "video generation AI"
  python startup-fetch.py --dry-run   (preview tanpa save)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────

CORPUS_DIR = Path(__file__).parent / "brain" / "public" / "sources" / "web_clips"
INDEX_CMD_VENV = Path(__file__).parent / "apps" / "brain_qa" / ".venv" / "Scripts" / "python.exe"
INDEX_CMD_FALLBACK = "python"
INDEX_MODULE = "brain_qa"
INDEX_SUBDIR = Path(__file__).parent / "apps" / "brain_qa"

MAX_ARTICLES_PER_RUN = 15
MAX_CHARS_PER_ARTICLE = 8000
REQUEST_DELAY = 2.0  # seconds between requests
USER_AGENT = "SIDIX-KnowledgeFetcher/1.0 (educational; non-commercial)"

# ── Wikipedia topics sesuai persona SIDIX ────────────────────────────────────

TOPICS = {
    "AI_CORE": [
        "Artificial intelligence",
        "Large language model",
        "Retrieval-augmented generation",
        "Transformer (deep learning)",
        "Generative adversarial network",
        "Diffusion model",
        "Reinforcement learning from human feedback",
        "Prompt engineering",
    ],
    "MIGHAN_CREATIVE": [
        "Text-to-image model",
        "AI-generated art",
        "Stable Diffusion",
        "Midjourney (software)",
        "AI music generation",
        "Video generation AI",
        "Generative design",
        "Neural style transfer",
    ],
    "TOARD_PLANNING": [
        "AI planning",
        "Autonomous agent",
        "Multi-agent system",
        "Workflow automation",
        "Project management software",
        "Knowledge management",
    ],
    "FACH_ACADEMIC": [
        "Natural language processing",
        "Machine learning",
        "Deep learning",
        "Computer vision",
        "Information retrieval",
        "Semantic search",
    ],
    "HAYFAR_TECHNICAL": [
        "Application programming interface",
        "FastAPI",
        "Python (programming language)",
        "Docker (software)",
        "Microservices",
        "Vector database",
    ],
    "GENERAL_TECH": [
        "Artificial general intelligence",
        "OpenAI",
        "Anthropic",
        "Google DeepMind",
        "Open-source software",
        "Cloud computing",
    ],
}

# Flatten dengan semua topics
ALL_TOPICS = [t for group in TOPICS.values() for t in group]


# ── Wikipedia API ─────────────────────────────────────────────────────────────

def fetch_wikipedia(title: str, lang: str = "en") -> dict | None:
    """Fetch Wikipedia article summary via REST API."""
    title_encoded = title.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.request.quote(title_encoded)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return {
                    "title": data.get("title", title),
                    "description": data.get("description", ""),
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "lang": lang,
                    "source": "wikipedia",
                }
    except Exception as e:
        print(f"  ⚠ Wikipedia fetch failed: {title} → {e}")
    return None


def fetch_wikipedia_sections(title: str, lang: str = "en") -> str:
    """Fetch fuller Wikipedia article content (intro section only)."""
    title_encoded = title.replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = urllib.parse.urlencode({
        "action": "query",
        "prop": "extracts",
        "exintro": "1",
        "explaintext": "1",
        "titles": title,
        "format": "json",
        "exsentences": 30,
    })
    full_url = f"{url}?{params}"

    try:
        import urllib.parse
        req = urllib.request.Request(full_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                return page.get("extract", "")
    except Exception:
        pass
    return ""


# ── Markdown writer ───────────────────────────────────────────────────────────

def article_to_markdown(article: dict, full_text: str = "") -> str:
    """Convert fetched article to Markdown for corpus."""
    title = article.get("title", "Unknown")
    description = article.get("description", "")
    extract = full_text or article.get("extract", "")
    url = article.get("url", "")
    source = article.get("source", "web")
    today = datetime.date.today().isoformat()

    # Truncate
    if len(extract) > MAX_CHARS_PER_ARTICLE:
        extract = extract[:MAX_CHARS_PER_ARTICLE] + "\n\n[... truncated for corpus size ...]"

    md = f"""# {title}

> {description}

**Source**: [{url}]({url})
**Fetched**: {today}
**Domain**: {source}

---

{extract}

---
*Auto-fetched by SIDIX startup-fetch.py — {today}*
"""
    return md


def slugify(title: str) -> str:
    """Convert title to safe filename."""
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-")
    return s[:80]


def get_filename(title: str, url: str) -> str:
    """Generate corpus filename matching existing convention."""
    slug = slugify(title)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    source_domain = "wikipedia"
    return f"{slug}-{source_domain}-{url_hash}.md"


# ── Main fetch loop ───────────────────────────────────────────────────────────

def run_fetch(topics: list[str], dry_run: bool = False, verbose: bool = True) -> int:
    """Fetch articles and save to corpus. Returns count of new articles."""
    import urllib.parse  # ensure available

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    # Existing files (avoid re-fetch)
    existing = {f.stem for f in CORPUS_DIR.glob("*.md")}

    fetched = 0
    skipped = 0
    today = datetime.date.today().isoformat()

    print(f"🔍 Fetching {len(topics)} topics → {CORPUS_DIR}")
    print(f"   Existing files: {len(list(CORPUS_DIR.glob('*.md')))}")
    print()

    for i, topic in enumerate(topics[:MAX_ARTICLES_PER_RUN]):
        if verbose:
            print(f"[{i+1}/{min(len(topics), MAX_ARTICLES_PER_RUN)}] {topic}...")

        article = fetch_wikipedia(topic)
        if not article:
            print(f"  ✗ Not found")
            continue

        # Check if already exists (by slug)
        slug = slugify(article["title"])
        already_fetched = any(slug in ex for ex in existing)

        if already_fetched:
            if verbose:
                print(f"  → Already in corpus, skip")
            skipped += 1
            time.sleep(0.5)
            continue

        # Get fuller content
        full_text = fetch_wikipedia_sections(topic)

        # Write to corpus
        md_content = article_to_markdown(article, full_text)
        filename = get_filename(article["title"], article["url"])
        filepath = CORPUS_DIR / filename

        if dry_run:
            print(f"  [DRY RUN] Would write: {filename}")
            print(f"  Preview: {md_content[:200]}...")
        else:
            filepath.write_text(md_content, encoding="utf-8")
            print(f"  ✓ Saved: {filename}")
            existing.add(slug)

        fetched += 1
        time.sleep(REQUEST_DELAY)

    print()
    print(f"✅ Done: {fetched} new, {skipped} skipped, {len(topics) - fetched - skipped} failed")
    return fetched


def run_reindex() -> None:
    """Trigger brain_qa index rebuild."""
    import subprocess

    python_exe = str(INDEX_CMD_VENV) if INDEX_CMD_VENV.exists() else INDEX_CMD_FALLBACK
    cwd = str(INDEX_SUBDIR)

    print(f"\n🔄 Reindexing corpus...")
    try:
        result = subprocess.run(
            [python_exe, "-m", INDEX_MODULE, "index"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("✅ Reindex complete!")
        else:
            print(f"⚠ Reindex exited {result.returncode}")
            if result.stderr:
                print(result.stderr[:500])
    except Exception as e:
        print(f"⚠ Reindex failed: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import urllib.parse  # late import for Windows compat

    parser = argparse.ArgumentParser(description="SIDIX Auto-Knowledge Fetcher")
    parser.add_argument(
        "--topics",
        nargs="*",
        help="Custom topics to fetch (overrides default list)",
    )
    parser.add_argument(
        "--category",
        choices=list(TOPICS.keys()) + ["ALL"],
        default="ALL",
        help="Fetch only topics from a specific persona category",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't save")
    parser.add_argument("--no-reindex", action="store_true", help="Skip reindex after fetch")
    parser.add_argument("--max", type=int, default=MAX_ARTICLES_PER_RUN, help="Max articles to fetch")
    args = parser.parse_args()

    global MAX_ARTICLES_PER_RUN
    MAX_ARTICLES_PER_RUN = args.max

    # Determine topics
    if args.topics:
        topics = args.topics
    elif args.category == "ALL":
        topics = ALL_TOPICS
    else:
        topics = TOPICS[args.category]

    print("=" * 60)
    print("  SIDIX Knowledge Fetcher — Auto-Startup")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    fetched = run_fetch(topics, dry_run=args.dry_run)

    if fetched > 0 and not args.dry_run and not args.no_reindex:
        run_reindex()
    elif fetched == 0:
        print("ℹ No new articles fetched, skipping reindex.")


if __name__ == "__main__":
    main()
