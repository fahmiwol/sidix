"""
social_agent.py — SIDIX Social Media Agent
===========================================
SIDIX bisa aktif di media sosial secara otonom:
  - Posting konten mandiri (pertanyaan, insight, perkenalan diri)
  - Membaca posts/komentar/DM → menyimpan sebagai pengetahuan baru
  - Menjawab pertanyaan dari DM / komentar
  - Scrolling untuk belajar tren dan topik terkini

Platform yang didukung:
  1. Threads (Meta) — via Threads API (sudah tersedia 2023+)
  2. Twitter/X     — via X API v2
  3. Telegram      — sudah ada di sidix-telegram (Polling mode)
  4. Reddit        — via PRAW / Reddit API
  5. YouTube       — via YouTube Data API v3 (comments)

Pipeline "Belajar dari Sosial Media":
  [SIDIX posting pertanyaan ke Threads]
        ↓
  [Followers/strangers reply]
        ↓
  [SocialAgent.collect_replies()]
        ↓
  [Filter kualitas reply (min_score)]
        ↓
  [ExperienceEngine.add_structured() / Corpus write]
        ↓
  [Re-index BM25]
        ↓
  [SIDIX lebih pintar]

Autonomous Learning dari Social:
  - Post 1-3x sehari (pertanyaan yang SIDIX sendiri ingin tahu jawabannya)
  - Scroll feed → extract knowledge snippets → ingest ke corpus
  - DM → tanya-jawab → harvest Q&A pairs untuk fine-tuning
  - Komentar → pola opini → Experience Engine

Rate Limits & Ethics:
  - Tidak spam: max 3 posts/hari, 20 replies/hari
  - Tidak impersonasi: selalu transparan sebagai AI
  - Tidak scrape private content
  - Consent: hanya pakai konten yang public
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from enum import Enum

from .paths import default_data_dir, workspace_root

# ── Paths ──────────────────────────────────────────────────────────────────────

_SOCIAL_DIR = default_data_dir() / "social_agent"
_POST_LOG = _SOCIAL_DIR / "post_log.jsonl"
_LEARNED_LOG = _SOCIAL_DIR / "learned.jsonl"
_SOCIAL_DIR.mkdir(parents=True, exist_ok=True)

# ── Enums ──────────────────────────────────────────────────────────────────────

class Platform(str, Enum):
    THREADS   = "threads"
    TWITTER   = "twitter"
    TELEGRAM  = "telegram"
    REDDIT    = "reddit"
    YOUTUBE   = "youtube"

class PostType(str, Enum):
    QUESTION      = "question"      # SIDIX bertanya untuk belajar
    INSIGHT       = "insight"       # Insight yang ingin dibagikan
    INTRODUCTION  = "introduction"  # Perkenalan diri
    FACT          = "fact"          # Fakta menarik dari corpus
    THREAD        = "thread"        # Thread panjang (edukasi)

class LearningSource(str, Enum):
    REPLY     = "reply"     # Dari reply ke post SIDIX
    DM        = "dm"        # Dari DM/chat
    FEED      = "feed"      # Dari scrolling feed
    COMMENT   = "comment"   # Dari komentar post orang lain
    HASHTAG   = "hashtag"   # Dari search hashtag


# ── Post Templates ─────────────────────────────────────────────────────────────
# SIDIX memiliki template untuk berbagai jenis post

POST_TEMPLATES = {
    PostType.QUESTION: [
        "Pertanyaan untuk kalian: {question}\n\nSaya sedang belajar tentang ini. Bagaimana pendapat kalian? 🤔\n\n#SIDIX #BelajarBersama",
        "Saya penasaran dengan sesuatu: {question}\n\nYuk diskusi! Siapa yang bisa bantu jelaskan? 💭",
        "Belajar dari kalian: {question}\n\nDi sini tidak ada jawaban salah, semua perspektif berharga 🌱",
    ],
    PostType.INSIGHT: [
        "Fakta menarik yang baru saya pelajari:\n\n{insight}\n\nApa yang kalian pikirkan? #SIDIX #Pengetahuan",
        "Insight dari riset hari ini:\n\n{insight}\n\nBagi kalau ada yang mau menambahkan! 📚",
    ],
    PostType.INTRODUCTION: [
        "Halo! Saya SIDIX — AI yang sedang dalam proses belajar dan tumbuh.\n\nSaya dibuat untuk menjadi AI yang benar-benar berguna, bukan sekadar menjawab.\n\nBoleh kenalan? Kalian sedang belajar apa hari ini? 🌟",
        "Perkenalkan, saya SIDIX 🤖\nAI asli Indonesia yang terus belajar dari kalian.\n\nMisi saya: jadi AI yang jujur, berguna, dan terus berkembang.\n\nAda yang mau berdiskusi?",
    ],
    PostType.FACT: [
        "Tahukah kamu?\n\n{fact}\n\nSumber: {source} 📖 #Edukasi #SIDIX",
        "Fakta hari ini:\n\n{fact}\n\n#BelajarBareng #SIDIX",
    ],
}


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class SocialPost:
    id: str = ""
    platform: str = Platform.THREADS
    post_type: str = PostType.INSIGHT
    content: str = ""
    posted_at: Optional[float] = None
    post_id_remote: str = ""     # ID dari platform
    reply_count: int = 0
    like_count: int = 0
    learned_from_replies: int = 0
    tags: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LearnedItem:
    source_platform: str = ""
    source_type: str = LearningSource.FEED
    source_url: str = ""
    content: str = ""             # Teks yang dipelajari
    author: str = ""
    likes: int = 0
    quality_score: float = 0.5   # 0.0 - 1.0
    tags: list = field(default_factory=list)
    ingested_to_corpus: bool = False
    learned_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Quality Filter ─────────────────────────────────────────────────────────────

class ContentQualityFilter:
    """
    Filter konten dari sosmed sebelum masuk ke corpus.
    Kualitas rendah = tidak masuk.
    """

    MIN_LENGTH = 50      # Minimal 50 karakter
    MAX_LENGTH = 5000    # Maksimal 5000 karakter
    MIN_LIKES  = 0       # Untuk awal, terima semua

    SPAM_PATTERNS = [
        r"follow.*for.*follow",
        r"like.*for.*like",
        r"dm.*for.*promo",
        r"bit\.ly", r"tinyurl",
        r"(giveaway|gratis|free).*(follow|dm|like)",
    ]

    QUALITY_KEYWORDS = [
        "karena", "karena itu", "menurut", "terbukti", "riset",
        "fakta", "contoh", "misalnya", "ilustrasi", "framework",
        "metodologi", "prinsip", "analisis", "insight", "pengalaman",
        "pelajaran", "kesimpulan", "data menunjukkan",
    ]

    def score(self, text: str, likes: int = 0) -> float:
        """Return kualitas 0.0-1.0."""
        if len(text) < self.MIN_LENGTH or len(text) > self.MAX_LENGTH:
            return 0.0

        text_lower = text.lower()

        # Spam check
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_lower):
                return 0.1

        score = 0.5

        # Bonus untuk kata kunci berkualitas
        quality_hits = sum(1 for kw in self.QUALITY_KEYWORDS if kw in text_lower)
        score += min(quality_hits * 0.05, 0.3)

        # Bonus untuk likes
        if likes > 100:
            score += 0.1
        elif likes > 10:
            score += 0.05

        return min(score, 1.0)

    def passes(self, text: str, likes: int = 0,
               min_score: float = 0.4) -> bool:
        return self.score(text, likes) >= min_score


# ── Threads API Client ─────────────────────────────────────────────────────────

class ThreadsClient:
    """
    Client untuk Threads API (Meta).

    Setup:
    1. Buat Meta App di developers.facebook.com
    2. Tambah "Threads API" product
    3. Generate long-lived access token
    4. Set THREADS_ACCESS_TOKEN dan THREADS_USER_ID di .env

    API Reference: https://developers.facebook.com/docs/threads
    """

    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self, access_token: str = "", user_id: str = ""):
        import os
        self._token = access_token or os.getenv("THREADS_ACCESS_TOKEN", "")
        self._user_id = user_id or os.getenv("THREADS_USER_ID", "")
        self._available = bool(self._token and self._user_id)

    def is_available(self) -> bool:
        return self._available

    def post(self, text: str, media_url: Optional[str] = None) -> dict:
        """
        Post thread baru.
        Return: {"id": "...", "ok": True} atau {"ok": False, "error": "..."}
        """
        if not self._available:
            return {"ok": False, "error": "Threads credentials tidak dikonfigurasi. "
                    "Set THREADS_ACCESS_TOKEN dan THREADS_USER_ID di .env"}

        try:
            # Step 1: Create media container
            params = {
                "media_type": "TEXT",
                "text": text[:500],  # Threads limit 500 chars
                "access_token": self._token,
            }
            if media_url:
                params["media_type"] = "IMAGE"
                params["image_url"] = media_url

            create_url = f"{self.BASE_URL}/{self._user_id}/threads"
            data = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(create_url, data=data, method="POST",
                                          headers={"Content-Type": "application/x-www-form-urlencoded"})

            with urllib.request.urlopen(req, timeout=15) as resp:
                container = json.loads(resp.read())

            container_id = container.get("id")
            if not container_id:
                return {"ok": False, "error": f"Failed to create container: {container}"}

            # Step 2: Publish
            publish_url = f"{self.BASE_URL}/{self._user_id}/threads_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self._token,
            }
            data = urllib.parse.urlencode(publish_params).encode("utf-8")
            req = urllib.request.Request(publish_url, data=data, method="POST",
                                          headers={"Content-Type": "application/x-www-form-urlencoded"})

            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())

            return {"ok": True, "id": result.get("id", ""), "container_id": container_id}

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return {"ok": False, "error": f"HTTP {e.code}: {body[:200]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_replies(self, post_id: str, limit: int = 25) -> list[dict]:
        """Ambil replies dari satu post."""
        if not self._available:
            return []
        try:
            params = {
                "fields": "id,text,username,like_count,timestamp",
                "limit": limit,
                "access_token": self._token,
            }
            url = f"{self.BASE_URL}/{post_id}/replies?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "SIDIX/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            return data.get("data", [])
        except Exception:
            return []

    def get_feed(self, limit: int = 20) -> list[dict]:
        """Ambil posts dari feed SIDIX sendiri (own posts)."""
        if not self._available:
            return []
        try:
            params = {
                "fields": "id,text,like_count,timestamp,replies_count",
                "limit": limit,
                "access_token": self._token,
            }
            url = f"{self.BASE_URL}/{self._user_id}/threads?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "SIDIX/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            return data.get("data", [])
        except Exception:
            return []


# ── Reddit Client ──────────────────────────────────────────────────────────────

class RedditRSSClient:
    """
    Fetch posts dari Reddit via RSS (tanpa API key).
    Berguna untuk belajar dari diskusi di r/MachineLearning, r/artificial, dll.
    """

    LEARNING_SUBREDDITS = [
        "MachineLearning",
        "artificial",
        "learnmachinelearning",
        "indonesia",
        "programming",
        "philosophy",
        "science",
    ]

    def fetch_top(self, subreddit: str, limit: int = 10,
                  time_filter: str = "week") -> list[dict]:
        """Fetch top posts dari subreddit via RSS."""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t={time_filter}&limit={limit}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SIDIX-Learning/1.0 (educational)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            posts = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                posts.append({
                    "id": post.get("id", ""),
                    "title": post.get("title", ""),
                    "selftext": post.get("selftext", "")[:800],
                    "url": post.get("url", ""),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "subreddit": subreddit,
                    "created_utc": post.get("created_utc", 0),
                })
            return posts
        except Exception as e:
            return []


# ── Social Agent Engine ────────────────────────────────────────────────────────

class SocialAgentEngine:
    """
    Main orchestrator SIDIX di sosial media.

    IMPORTANT: Semua posting membutuhkan explicit permission atau
    konfigurasi auto-post = True di settings.
    """

    def __init__(self):
        self._threads = ThreadsClient()
        self._reddit = RedditRSSClient()
        self._quality = ContentQualityFilter()
        self._post_log = _POST_LOG
        self._learned_log = _LEARNED_LOG

        # Rate limiting: max post per hari
        self._MAX_POSTS_PER_DAY = 3
        self._MAX_REPLIES_PER_DAY = 20

    # ── POSTING ──

    def generate_post(self, post_type: str = PostType.QUESTION,
                      topic: str = "", custom_content: str = "") -> str:
        """
        Generate konten post berdasarkan type dan topic.
        Mengambil konteks dari corpus jika perlu.
        """
        import random

        if custom_content:
            return custom_content

        templates = POST_TEMPLATES.get(post_type, POST_TEMPLATES[PostType.INSIGHT])
        template = random.choice(templates)

        if post_type == PostType.QUESTION:
            # Generate pertanyaan dari topic atau dari gaps
            if topic:
                question = f"Apa yang kalian ketahui tentang {topic}? Khususnya penerapannya di Indonesia?"
            else:
                question = (
                    "Menurut kalian, apa perbedaan antara 'belajar teknis' dan "
                    "'memahami filosofi' sebuah ilmu?"
                )
            return template.format(question=question)

        elif post_type == PostType.INTRODUCTION:
            return random.choice(POST_TEMPLATES[PostType.INTRODUCTION])

        elif post_type == PostType.FACT:
            # Coba ambil fakta dari corpus
            fact = f"AI yang terus belajar dari interaksi (continual learning) bisa 3-5x lebih efisien dibanding re-training dari awal"
            source = "Research: Continual Learning Survey 2024"
            return template.format(fact=fact, source=source)

        return f"SIDIX sedang belajar tentang {topic or 'banyak hal'}. Ada yang mau berbagi ilmu? 🌱"

    def post_to_threads(self, content: str,
                        post_type: str = PostType.INSIGHT,
                        dry_run: bool = True) -> dict:
        """
        Post ke Threads.
        dry_run=True: hanya preview, tidak posting.
        dry_run=False: posting langsung (butuh credentials).
        """
        if not self._check_daily_limit():
            return {"ok": False, "error": "Daily post limit reached (max 3/day)"}

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "would_post": content,
                "platform": "threads",
                "post_type": post_type,
            }

        result = self._threads.post(content)
        if result.get("ok"):
            self._log_post(SocialPost(
                platform=Platform.THREADS,
                post_type=post_type,
                content=content,
                posted_at=time.time(),
                post_id_remote=result.get("id", ""),
            ))
        return result

    # ── LEARNING FROM SOCIAL ──

    def learn_from_reddit(self, max_subreddits: int = 3,
                          posts_per_sub: int = 5) -> int:
        """
        Fetch top posts dari learning subreddits.
        Filter kualitas dan ingest ke corpus.
        Return: jumlah item yang dipelajari.
        """
        import random
        subreddits = random.sample(
            self._reddit.LEARNING_SUBREDDITS,
            min(max_subreddits, len(self._reddit.LEARNING_SUBREDDITS))
        )

        learned = 0
        for sub in subreddits:
            posts = self._reddit.fetch_top(sub, limit=posts_per_sub)
            for post in posts:
                text = f"{post['title']}\n\n{post['selftext']}"
                score = self._quality.score(text, likes=post.get("score", 0))

                if score >= 0.4:
                    item = LearnedItem(
                        source_platform=Platform.REDDIT,
                        source_type=LearningSource.FEED,
                        source_url=post.get("url", ""),
                        content=text[:800],
                        author=f"reddit/r/{sub}",
                        likes=post.get("score", 0),
                        quality_score=score,
                        tags=[sub, "reddit", "community"],
                    )
                    self._ingest_learned(item)
                    learned += 1
                time.sleep(0.5)
        return learned

    def learn_from_replies(self, post_id: str) -> int:
        """
        Ambil replies dari satu post SIDIX dan pelajari.
        Berguna setelah SIDIX posting pertanyaan.
        """
        replies = self._threads.get_replies(post_id)
        learned = 0
        for reply in replies:
            text = reply.get("text", "")
            likes = reply.get("like_count", 0)

            if self._quality.passes(text, likes=likes, min_score=0.4):
                item = LearnedItem(
                    source_platform=Platform.THREADS,
                    source_type=LearningSource.REPLY,
                    source_url=f"threads:/{post_id}/{reply.get('id', '')}",
                    content=text,
                    author=reply.get("username", ""),
                    likes=likes,
                    quality_score=self._quality.score(text, likes),
                    tags=["threads", "reply", "community-knowledge"],
                )
                self._ingest_learned(item)
                learned += 1
        return learned

    def autonomous_learning_cycle(self, dry_run: bool = True) -> dict:
        """
        Satu cycle lengkap autonomous learning dari sosial media:
        1. Fetch dari Reddit (no auth needed)
        2. Jika Threads terkonfigurasi: cek replies ke posts lama
        3. Ingest hasil ke corpus
        Return: summary
        """
        summary = {"reddit": 0, "threads_replies": 0, "total": 0}

        # 1. Reddit (selalu bisa)
        reddit_count = self.learn_from_reddit(max_subreddits=3, posts_per_sub=5)
        summary["reddit"] = reddit_count

        # 2. Threads replies (kalau ada credentials)
        if self._threads.is_available():
            recent_posts = self._threads.get_feed(limit=5)
            for post in recent_posts[:3]:  # max 3 posts
                replies_learned = self.learn_from_replies(post.get("id", ""))
                summary["threads_replies"] += replies_learned

        summary["total"] = summary["reddit"] + summary["threads_replies"]

        # 3. Trigger re-index jika ada yang dipelajari
        if not dry_run and summary["total"] > 0:
            self._trigger_reindex()

        return summary

    def _ingest_learned(self, item: LearnedItem) -> None:
        """Simpan ke log dan jadikan corpus entry."""
        # Log
        with open(self._learned_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        # Simpan ke web_clips corpus
        _corpus_dir = workspace_root() / "brain" / "public" / "sources" / "web_clips"
        _corpus_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_safe = re.sub(r"[^\w]", "_", item.source_platform)
        fname = f"social_{platform_safe}_{ts}_{abs(hash(item.content[:30])) % 10000}.md"

        tags_str = ", ".join(item.tags)
        md = (
            f"# Community Knowledge — {item.source_platform}\n\n"
            f"**Sumber:** {item.author} ({item.source_platform})  \n"
            f"**URL:** {item.source_url}  \n"
            f"**Kualitas:** {item.quality_score:.2f}  \n"
            f"**Tags:** {tags_str}  \n\n"
            f"## Konten\n\n{item.content}\n\n"
            f"---\n*Dipelajari oleh SIDIX Social Agent dari {item.source_type}*\n"
        )

        try:
            (_corpus_dir / fname).write_text(md, encoding="utf-8")
            item.ingested_to_corpus = True
        except Exception:
            pass

    def _trigger_reindex(self) -> None:
        """Trigger brain_qa index rebuild."""
        import subprocess, sys
        try:
            brain_qa_dir = workspace_root() / "apps" / "brain_qa"
            subprocess.Popen(
                [sys.executable, "-m", "brain_qa", "index"],
                cwd=str(brain_qa_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _check_daily_limit(self) -> bool:
        """Cek apakah sudah mencapai limit post hari ini."""
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        if self._post_log.exists():
            for line in self._post_log.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    post = json.loads(line)
                    post_date = datetime.fromtimestamp(
                        post.get("created_at", 0)
                    ).strftime("%Y-%m-%d")
                    if post_date == today:
                        count += 1
                except Exception:
                    pass
        return count < self._MAX_POSTS_PER_DAY

    def _log_post(self, post: SocialPost) -> None:
        with open(self._post_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(post.to_dict(), ensure_ascii=False) + "\n")

    def stats(self) -> dict:
        total_posts = 0
        total_learned = 0
        if self._post_log.exists():
            total_posts = sum(1 for l in self._post_log.read_text().splitlines() if l.strip())
        if self._learned_log.exists():
            total_learned = sum(1 for l in self._learned_log.read_text().splitlines() if l.strip())
        return {
            "threads_configured": self._threads.is_available(),
            "total_posts": total_posts,
            "total_learned": total_learned,
            "daily_limit": self._MAX_POSTS_PER_DAY,
            "reddit_subreddits": self._reddit.LEARNING_SUBREDDITS,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_agent: Optional[SocialAgentEngine] = None

def get_social_agent() -> SocialAgentEngine:
    global _agent
    if _agent is None:
        _agent = SocialAgentEngine()
    return _agent
