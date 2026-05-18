"""
reply_harvester.py — SIDIX Auto Reply Harvester
================================================

Tujuan:
  Otomatis membaca komentar/reply dari post SIDIX di Threads & Reddit,
  menyaring kualitas, menyimpan sebagai corpus markdown, dan
  mengkonversi menjadi Q&A pairs (Alpaca format) untuk fine-tuning.

Pipeline:
  [post SIDIX di Threads / Reddit]
        ↓
  [fetch_threads_replies / fetch_reddit_comments]
        ↓
  [quality_filter] — buang spam, ad, bot, pesan terlalu pendek, pure-URL
        ↓
  [convert_reply_to_corpus]  → brain/public/sources/social_replies/{platform}_{id}.md
        ↓
  [convert_to_qa_pair]       → .data/harvest/training_pairs/reply_alpaca_*.jsonl
        ↓
  [SIDIX ingest & retrain]

Prinsip:
  • Idempoten  — setiap reply_id disimpan di .data/harvest/replies_seen.json
  • Rate-limited— 1 req/2s Reddit, 1 req/s Threads, User-Agent jelas
  • No vendor AI— scraping murni HTTP (urllib)
  • Public only — Reddit .json publik, Threads Graph API (butuh token)

Usage:
  from brain_qa.reply_harvester import harvest_all_recent
  report = harvest_all_recent(hours=24)
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Optional

from .paths import default_data_dir, load_manifest_paths, workspace_root

logger = logging.getLogger("sidix.reply_harvester")

# ── Konstanta ──────────────────────────────────────────────────────────────────

USER_AGENT = "SIDIX-Harvester/1.0 (+https://sidixlab.com; belajar-dari-publik)"

THREADS_RATE_DELAY_S = 1.0   # 1 req/detik
REDDIT_RATE_DELAY_S  = 2.0   # 1 req/2 detik
HTTP_TIMEOUT_S       = 15

DEFAULT_BLACKLIST = [
    "spam", "buy now", "click here", "promo", "iklan", "judi",
    "slot", "bot reply", "bit.ly", "onlyfans", "porn",
]

# ── Paths ──────────────────────────────────────────────────────────────────────

_HARVEST_DIR        = default_data_dir() / "harvest"
_REPLIES_SEEN_FILE  = _HARVEST_DIR / "replies_seen.json"
_REPLIES_LOG_FILE   = _HARVEST_DIR / "replies_harvested.jsonl"
_QA_PAIRS_DIR       = _HARVEST_DIR / "training_pairs"
_POST_LOG_FILE      = default_data_dir() / "social_agent" / "post_log.jsonl"

try:
    _PUBLIC_ROOT = load_manifest_paths().public_markdown_root
except Exception:
    _PUBLIC_ROOT = workspace_root() / "brain" / "public"

_CORPUS_REPLIES_DIR = _PUBLIC_ROOT / "sources" / "social_replies"

_HARVEST_DIR.mkdir(parents=True, exist_ok=True)
_QA_PAIRS_DIR.mkdir(parents=True, exist_ok=True)
_CORPUS_REPLIES_DIR.mkdir(parents=True, exist_ok=True)


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Reply:
    """Satu reply/komentar publik yang berhasil di-harvest."""
    id: str                         # id unik (platform-prefixed)
    platform: str                   # "threads" | "reddit"
    post_id: str                    # id post SIDIX yang di-reply
    author: str
    text: str
    created_at: str                 # ISO8601
    score: int = 0                  # upvotes/likes jika ada
    url: str = ""                   # permalink ke reply
    parent_text: str = ""           # konten post asli (untuk Q&A context)
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Helpers ────────────────────────────────────────────────────────────────────

_URL_RE = re.compile(r"https?://\S+")


def _http_get_json(url: str, headers: Optional[dict] = None) -> Optional[dict]:
    """GET URL dan parse JSON. Return None jika error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"[reply_harvester] HTTP gagal: {url} — {e}")
        return None


def _load_seen() -> set[str]:
    if not _REPLIES_SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(_REPLIES_SEEN_FILE.read_text(encoding="utf-8"))
        return set(data.get("seen_ids", []))
    except Exception:
        return set()


def _save_seen(seen: set[str]) -> None:
    _REPLIES_SEEN_FILE.write_text(
        json.dumps({"seen_ids": sorted(seen), "updated_at": datetime.now(timezone.utc).isoformat()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _append_reply_log(reply: Reply) -> None:
    with open(_REPLIES_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(reply.to_dict(), ensure_ascii=False) + "\n")


def _safe_slug(value: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return slug[:max_len] or "unknown"


# ── Threads fetcher ────────────────────────────────────────────────────────────

def fetch_threads_replies(post_id: str, access_token: str) -> list[Reply]:
    """
    Ambil replies untuk sebuah post Threads via Graph API.
    Endpoint: GET https://graph.threads.net/v1.0/{post_id}/replies

    Return list Reply. Jika token kosong / error → return [].
    """
    if not post_id or not access_token:
        logger.info("[threads] post_id atau access_token kosong, skip")
        return []

    fields = "id,text,username,timestamp,permalink,root_post"
    params = urllib.parse.urlencode({
        "fields": fields,
        "access_token": access_token,
        "limit": 50,
    })
    url = f"https://graph.threads.net/v1.0/{post_id}/replies?{params}"

    data = _http_get_json(url)
    time.sleep(THREADS_RATE_DELAY_S)
    if not data:
        return []

    out: list[Reply] = []
    for item in data.get("data", []) or []:
        rid = str(item.get("id") or "")
        if not rid:
            continue
        text = (item.get("text") or "").strip()
        out.append(Reply(
            id=f"threads_{rid}",
            platform="threads",
            post_id=post_id,
            author=item.get("username") or "unknown",
            text=text,
            created_at=item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            url=item.get("permalink") or "",
            raw=item,
        ))
    logger.info(f"[threads] {len(out)} replies untuk post {post_id}")
    return out


# ── Reddit fetcher ─────────────────────────────────────────────────────────────

def fetch_reddit_comments(post_url: str) -> list[Reply]:
    """
    Scrape komentar publik Reddit via .json endpoint.
    Contoh input: https://www.reddit.com/r/IndonesiaTech/comments/abc123/judul/
    → otomatis append `.json`.

    Return flattened list[Reply] (tidak mempertahankan tree).
    """
    if not post_url:
        return []

    # Normalisasi URL
    clean_url = post_url.rstrip("/")
    if not clean_url.endswith(".json"):
        clean_url = clean_url + ".json"

    # Extract post_id dari URL (pattern /comments/<id>/)
    m = re.search(r"/comments/([a-z0-9]+)/", post_url)
    post_id = m.group(1) if m else _safe_slug(post_url, 20)

    data = _http_get_json(clean_url)
    time.sleep(REDDIT_RATE_DELAY_S)
    if not data or not isinstance(data, list) or len(data) < 2:
        return []

    # Root post untuk parent_text
    parent_text = ""
    try:
        root_children = data[0].get("data", {}).get("children", [])
        if root_children:
            rd = root_children[0].get("data", {})
            parent_text = (rd.get("title") or "") + "\n\n" + (rd.get("selftext") or "")
    except Exception:
        pass

    out: list[Reply] = []

    def walk(children: list) -> None:
        for ch in children or []:
            kind = ch.get("kind")
            d = ch.get("data", {})
            if kind != "t1":  # only comments
                continue
            rid = str(d.get("id") or "")
            body = (d.get("body") or "").strip()
            if not rid or not body or body == "[deleted]" or body == "[removed]":
                continue
            created = d.get("created_utc")
            ts_iso = datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else ""
            out.append(Reply(
                id=f"reddit_{rid}",
                platform="reddit",
                post_id=post_id,
                author=d.get("author") or "unknown",
                text=body,
                created_at=ts_iso,
                score=int(d.get("score") or 0),
                url=f"https://reddit.com{d.get('permalink','')}",
                parent_text=parent_text.strip(),
                raw={},  # raw dropped untuk hemat ruang
            ))
            replies = d.get("replies")
            if isinstance(replies, dict):
                walk(replies.get("data", {}).get("children", []))

    walk(data[1].get("data", {}).get("children", []))
    logger.info(f"[reddit] {len(out)} comments untuk {post_url}")
    return out


# ── Quality filter ─────────────────────────────────────────────────────────────

def quality_filter(reply: Reply,
                   min_length: int = 20,
                   blacklist: Optional[list[str]] = None) -> bool:
    """
    Return True jika reply layak disimpan.

    Rules:
      • len(text) >= min_length
      • bukan hanya URL
      • tidak mengandung kata blacklist (case-insensitive substring)
    """
    blacklist = [b.lower() for b in (blacklist if blacklist is not None else DEFAULT_BLACKLIST)]
    text = (reply.text or "").strip()
    if len(text) < min_length:
        return False

    # Strip URL, cek sisa teks
    text_wo_url = _URL_RE.sub("", text).strip()
    if len(text_wo_url) < min_length // 2:
        return False  # pure-URL spam

    low = text.lower()
    for kw in blacklist:
        if kw and kw in low:
            return False
    return True


# ── Converter ke corpus markdown ───────────────────────────────────────────────

def convert_reply_to_corpus(reply: Reply) -> Path:
    """
    Tulis reply sebagai markdown dengan frontmatter YAML.
    Lokasi: brain/public/sources/social_replies/{platform}_{id}.md

    Return Path file yang ditulis.
    """
    safe_id = _safe_slug(reply.id, 60)
    fname = f"{reply.platform}_{safe_id}.md"
    out_path = _CORPUS_REPLIES_DIR / fname

    # Frontmatter: hindari kutip ganda di dalam value
    author = (reply.author or "unknown").replace('"', "'")
    created = reply.created_at or datetime.now(timezone.utc).isoformat()

    frontmatter = (
        "---\n"
        f"source: social_reply\n"
        f"platform: {reply.platform}\n"
        f"reply_id: {reply.id}\n"
        f"post_id: {reply.post_id}\n"
        f"author: \"{author}\"\n"
        f"created_at: {created}\n"
        f"score: {reply.score}\n"
        f"url: {reply.url}\n"
        f"harvested_at: {datetime.now(timezone.utc).isoformat()}\n"
        "tags: [social_reply, community, " + reply.platform + "]\n"
        "---\n\n"
    )

    body_parts: list[str] = [f"# Reply dari @{author} ({reply.platform})\n"]
    if reply.parent_text:
        body_parts.append("## Konteks Post Asli\n")
        body_parts.append(f"> {reply.parent_text[:500].replace(chr(10), ' ')}\n")
    body_parts.append("## Isi Reply\n")
    body_parts.append(reply.text.strip() + "\n")

    out_path.write_text(frontmatter + "\n".join(body_parts), encoding="utf-8")
    return out_path


# ── Converter ke Q&A pair (Alpaca) ────────────────────────────────────────────

def convert_to_qa_pair(reply: Reply, original_post: str = "") -> dict:
    """
    Format Alpaca instruction-response.

    instruction  = post asli SIDIX (pertanyaan yang ditanyakan ke publik)
    input        = ""
    output       = reply dari user
    meta         = platform, author, score, url
    """
    instruction = (original_post or reply.parent_text or
                   f"Apa pendapat Anda tentang topik yang dibahas di {reply.platform}?").strip()
    return {
        "instruction": instruction,
        "input": "",
        "output": reply.text.strip(),
        "source": reply.platform,
        "author": reply.author,
        "reply_id": reply.id,
        "post_id": reply.post_id,
        "score": reply.score,
        "url": reply.url,
        "harvested_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Post-log reader (Threads + Reddit targets) ────────────────────────────────

def _iter_posts_recent(hours: int) -> Iterable[dict]:
    """Iterate entries di post_log.jsonl yang lebih baru dari `hours` terakhir."""
    if not _POST_LOG_FILE.exists():
        return
    cutoff = time.time() - hours * 3600
    for line in _POST_LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            post = json.loads(line)
            created = float(post.get("created_at") or 0)
            if created >= cutoff:
                yield post
        except Exception:
            continue


# ── Runner utama ───────────────────────────────────────────────────────────────

def harvest_all_recent(hours: int = 24,
                       threads_token: str = "",
                       extra_reddit_urls: Optional[list[str]] = None,
                       min_length: int = 20,
                       blacklist: Optional[list[str]] = None,
                       write_qa: bool = True) -> dict:
    """
    Jalankan harvest untuk semua post SIDIX dalam `hours` terakhir.

    Sumber target:
      • post_log.jsonl — field: platform, post_id_remote, content
      • extra_reddit_urls — list URL Reddit manual (misal reply ke thread orang lain)

    Flow:
      1. Baca post terakhir
      2. Fetch replies (rate-limited)
      3. Quality filter + idempoten (replies_seen.json)
      4. Tulis ke corpus markdown
      5. Append Q&A pairs ke training_pairs/reply_alpaca_{date}.jsonl
      6. Update replies_seen
    """
    import os

    threads_token = threads_token or os.getenv("THREADS_ACCESS_TOKEN", "")
    seen = _load_seen()
    new_seen = set(seen)

    stats = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "hours_window": hours,
        "posts_scanned": 0,
        "replies_fetched": 0,
        "replies_after_filter": 0,
        "replies_new": 0,
        "qa_pairs_written": 0,
        "corpus_files_written": 0,
        "by_platform": {"threads": 0, "reddit": 0},
        "errors": [],
    }

    qa_file = _QA_PAIRS_DIR / f"reply_alpaca_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
    qa_fh = open(qa_file, "a", encoding="utf-8") if write_qa else None

    def process_replies(replies: list[Reply], parent_post_text: str) -> None:
        for r in replies:
            stats["replies_fetched"] += 1
            if not quality_filter(r, min_length=min_length, blacklist=blacklist):
                continue
            stats["replies_after_filter"] += 1
            if r.id in new_seen:
                continue

            try:
                convert_reply_to_corpus(r)
                stats["corpus_files_written"] += 1
            except Exception as e:
                stats["errors"].append(f"corpus-write {r.id}: {e}")
                continue

            if qa_fh is not None:
                try:
                    qa = convert_to_qa_pair(r, original_post=parent_post_text)
                    qa_fh.write(json.dumps(qa, ensure_ascii=False) + "\n")
                    stats["qa_pairs_written"] += 1
                except Exception as e:
                    stats["errors"].append(f"qa-write {r.id}: {e}")

            _append_reply_log(r)
            new_seen.add(r.id)
            stats["replies_new"] += 1
            stats["by_platform"][r.platform] = stats["by_platform"].get(r.platform, 0) + 1

    # 1) Post dari post_log
    for post in _iter_posts_recent(hours):
        stats["posts_scanned"] += 1
        platform = post.get("platform") or ""
        remote_id = post.get("post_id_remote") or ""
        content = post.get("content") or ""
        if not remote_id:
            continue
        if platform == "threads":
            try:
                replies = fetch_threads_replies(remote_id, threads_token)
                process_replies(replies, content)
            except Exception as e:
                stats["errors"].append(f"threads {remote_id}: {e}")
        elif platform == "reddit":
            reddit_url = post.get("url") or post.get("permalink") or ""
            if not reddit_url:
                continue
            try:
                replies = fetch_reddit_comments(reddit_url)
                process_replies(replies, content)
            except Exception as e:
                stats["errors"].append(f"reddit {reddit_url}: {e}")

    # 2) Extra Reddit URLs (manual targeting)
    for url in (extra_reddit_urls or []):
        try:
            replies = fetch_reddit_comments(url)
            process_replies(replies, "")
        except Exception as e:
            stats["errors"].append(f"reddit-extra {url}: {e}")

    if qa_fh is not None:
        qa_fh.close()

    _save_seen(new_seen)
    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    stats["qa_file"] = str(qa_file) if write_qa else None
    logger.info(f"[reply_harvester] selesai: {stats}")
    return stats


# ── Stats ──────────────────────────────────────────────────────────────────────

def reply_stats() -> dict:
    """Hitung statistik reply yang pernah di-harvest."""
    total = 0
    by_platform: dict[str, int] = {}
    qa_pair_count = 0

    if _REPLIES_LOG_FILE.exists():
        for line in _REPLIES_LOG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                total += 1
                p = d.get("platform", "unknown")
                by_platform[p] = by_platform.get(p, 0) + 1
            except Exception:
                continue

    for qa_file in _QA_PAIRS_DIR.glob("reply_alpaca_*.jsonl"):
        try:
            qa_pair_count += sum(1 for l in qa_file.read_text(encoding="utf-8").splitlines() if l.strip())
        except Exception:
            continue

    seen = _load_seen()
    return {
        "total_replies_harvested": total,
        "by_platform": by_platform,
        "qa_pairs_total": qa_pair_count,
        "unique_reply_ids_seen": len(seen),
        "corpus_dir": str(_CORPUS_REPLIES_DIR),
        "replies_log": str(_REPLIES_LOG_FILE),
    }
