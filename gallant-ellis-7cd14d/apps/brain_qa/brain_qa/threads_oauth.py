"""
threads_oauth.py — Threads (Meta) OAuth 2.0 + FULL API integration untuk SIDIX.

Flow OAuth:
1. User → GET /threads/auth → redirect ke Meta OAuth
2. Meta → GET /threads/callback?code=XXX → tukar code → simpan token
3. SIDIX → POST /threads/post → post konten ke Threads

Permissions yang digunakan (semuanya):
  threads_basic              — profil, read posts
  threads_content_publish    — buat & publish post/reply
  threads_read_replies       — baca replies ke post kita
  threads_manage_replies     — hide/unhide reply
  threads_manage_insights    — metrics views, likes, reach
  threads_manage_mentions    — notifikasi mention @sidixlab
  threads_keyword_search     — search teks di Threads
  threads_profile_discovery  — discover profil lain
  threads_share_to_instagram — share ke IG (future)

Environment variables:
  THREADS_APP_ID
  THREADS_APP_SECRET
  THREADS_REDIRECT_URI     (default: https://ctrl.sidixlab.com/threads/callback)
  THREADS_API_BASE         (default: https://graph.threads.net/v1.0)

Token disimpan di: .data/threads_token.json
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional


# ── Config ─────────────────────────────────────────────────────────────────────

APP_ID = os.getenv("THREADS_APP_ID", "")
APP_SECRET = os.getenv("THREADS_APP_SECRET", "")
REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI", "https://ctrl.sidixlab.com/threads/callback")
API_BASE = os.getenv("THREADS_API_BASE", "https://graph.threads.net/v1.0")

# ALL scopes — gunakan seluruh kapabilitas
SCOPES = (
    "threads_basic,"
    "threads_content_publish,"
    "threads_read_replies,"
    "threads_manage_replies,"
    "threads_manage_insights,"
    "threads_manage_mentions,"
    "threads_keyword_search,"
    "threads_profile_discovery"
)

# Token storage
_TOKEN_FILE = Path(__file__).parent.parent.parent / ".data" / "threads_token.json"

# Alert threshold — warn ketika sisa < 7 hari
TOKEN_ALERT_DAYS = 7


# ── Token Storage ──────────────────────────────────────────────────────────────

def _load_token() -> dict:
    """Load token dari file. Return {} jika tidak ada."""
    if _TOKEN_FILE.exists():
        try:
            return json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_token(data: dict) -> None:
    """Simpan token ke file."""
    _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_token() -> Optional[str]:
    """Return access_token jika ada dan belum expired."""
    data = _load_token()
    if not data:
        return None
    access_token = data.get("access_token")
    expires_at = data.get("expires_at", 0)
    if not access_token:
        return None
    if expires_at and time.time() > expires_at:
        return None  # expired
    return access_token


def get_token_info() -> dict:
    """Return info token lengkap + alert status."""
    data = _load_token()
    if not data:
        return {"connected": False}
    expires_at = data.get("expires_at", 0)
    remaining_days = max(0, int((expires_at - time.time()) / 86400)) if expires_at else None
    has_expired = bool(expires_at and time.time() > expires_at)
    alert = (
        "expired" if has_expired
        else "warning" if (remaining_days is not None and remaining_days < TOKEN_ALERT_DAYS)
        else "ok"
    )
    return {
        "connected": bool(data.get("access_token")) and not has_expired,
        "user_id": data.get("user_id"),
        "username": data.get("username"),
        "expires_at": expires_at,
        "remaining_days": remaining_days,
        "has_expired": has_expired,
        "alert": alert,
        "alert_message": (
            "⚠️ Token Threads SUDAH EXPIRED! Hubungkan ulang via /threads/auth" if has_expired
            else f"⚠️ Token Threads akan expire dalam {remaining_days} hari. Segera reconnect!" if alert == "warning"
            else None
        ),
        "reconnect_url": f"/threads/auth" if alert in ("expired", "warning") else None,
    }


def _api_get(path: str, params: dict | None = None) -> dict:
    """Helper GET ke Threads Graph API."""
    import urllib.request
    import urllib.parse
    token = get_token()
    if not token:
        raise ValueError("Token tidak tersedia atau expired")
    all_params = {"access_token": token}
    if params:
        all_params.update(params)
    url = f"{API_BASE}/{path.lstrip('/')}?{urllib.parse.urlencode(all_params)}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read())


def _api_post(path: str, payload: dict) -> dict:
    """Helper POST ke Threads Graph API."""
    import urllib.request
    import urllib.parse
    token = get_token()
    if not token:
        raise ValueError("Token tidak tersedia atau expired")
    payload["access_token"] = token
    data = urllib.parse.urlencode(payload).encode()
    url = f"{API_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── OAuth Flow ─────────────────────────────────────────────────────────────────

def build_auth_url(state: str = "sidix_oauth") -> str:
    """Generate URL untuk redirect user ke Meta OAuth."""
    import urllib.parse
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
    }
    base = "https://threads.net/oauth/authorize"
    return base + "?" + urllib.parse.urlencode(params)


def exchange_code(code: str) -> dict:
    """
    Tukar authorization code → short-lived token → long-lived token.
    Return: {"access_token": ..., "user_id": ..., "expires_at": ...}
    """
    import urllib.request
    import urllib.parse

    # Step 1: Exchange code → short-lived token
    token_url = "https://graph.threads.net/oauth/access_token"
    payload = urllib.parse.urlencode({
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }).encode()

    req = urllib.request.Request(token_url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        short_data = json.loads(resp.read())

    short_token = short_data.get("access_token")
    user_id = short_data.get("user_id")
    if not short_token:
        raise ValueError(f"Tidak dapat short-lived token: {short_data}")

    # Step 2: Exchange → long-lived token (60 hari)
    ll_url = (
        f"{API_BASE}/access_token"
        f"?grant_type=th_exchange_token"
        f"&client_secret={APP_SECRET}"
        f"&access_token={short_token}"
    )
    req2 = urllib.request.Request(ll_url)
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        ll_data = json.loads(resp2.read())

    long_token = ll_data.get("access_token", short_token)
    expires_in = ll_data.get("expires_in", 60 * 86400)

    # Fetch username
    username = _fetch_username(long_token, user_id)

    token_record = {
        "access_token": long_token,
        "user_id": user_id,
        "username": username,
        "obtained_at": int(time.time()),
        "expires_at": int(time.time()) + expires_in,
        "expires_in": expires_in,
    }
    _save_token(token_record)
    return token_record


def _fetch_username(access_token: str, user_id: str) -> str:
    """Fetch @username dari Threads API."""
    import urllib.request
    url = f"{API_BASE}/{user_id}?fields=username&access_token={access_token}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("username", "")
    except Exception:
        return ""


# ── Publishing ─────────────────────────────────────────────────────────────────

def create_text_post(text: str, reply_to_id: str | None = None, access_token: Optional[str] = None) -> dict:
    """
    Buat post atau reply teks di Threads.
    reply_to_id: ID post yang ingin dibalas (threads_manage_replies)
    Return: {"ok": True, "post_id": "...", "permalink": "..."}
    """
    import urllib.request
    import urllib.parse

    token = access_token or get_token()
    if not token:
        raise ValueError("Tidak ada access token Threads. Hubungkan akun dulu via /threads/auth")

    token_data = _load_token()
    user_id = token_data.get("user_id")
    if not user_id:
        raise ValueError("user_id tidak ditemukan di token storage")

    # Step 1: Create media container
    create_url = f"{API_BASE}/{user_id}/threads"
    container_payload: dict = {
        "media_type": "TEXT",
        "text": text,
        "access_token": token,
    }
    if reply_to_id:
        container_payload["reply_to_id"] = reply_to_id

    payload = urllib.parse.urlencode(container_payload).encode()
    req = urllib.request.Request(create_url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        container = json.loads(resp.read())

    container_id = container.get("id")
    if not container_id:
        raise ValueError(f"Gagal create container: {container}")

    # Step 2: Publish
    publish_url = f"{API_BASE}/{user_id}/threads_publish"
    pub_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": token,
    }).encode()

    req2 = urllib.request.Request(publish_url, data=pub_payload, method="POST")
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        pub_data = json.loads(resp2.read())

    post_id = pub_data.get("id", "")
    username = token_data.get("username", "")
    permalink = f"https://www.threads.net/@{username}/post/{post_id}" if username and post_id else ""

    return {
        "ok": True,
        "post_id": post_id,
        "permalink": permalink,
        "is_reply": bool(reply_to_id),
    }


def reply_to_post(post_id: str, text: str) -> dict:
    """Balas ke sebuah post Threads (threads_manage_replies)."""
    return create_text_post(text=text, reply_to_id=post_id)


# ── Reading ────────────────────────────────────────────────────────────────────

def get_recent_posts(limit: int = 10) -> list[dict]:
    """Ambil posts terbaru dari akun Threads (threads_basic)."""
    try:
        token_data = _load_token()
        user_id = token_data.get("user_id", "me")
        data = _api_get(
            f"{user_id}/threads",
            params={"fields": "id,text,timestamp,permalink,media_type,like_count,reply_count", "limit": limit},
        )
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


def get_replies(post_id: str, limit: int = 20) -> list[dict]:
    """Ambil replies ke sebuah post (threads_read_replies)."""
    try:
        data = _api_get(
            f"{post_id}/replies",
            params={"fields": "id,text,timestamp,username,permalink,like_count", "limit": limit},
        )
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


def get_conversation(post_id: str) -> list[dict]:
    """Ambil full conversation thread (threads_read_replies)."""
    try:
        data = _api_get(
            f"{post_id}/conversation",
            params={"fields": "id,text,timestamp,username,permalink,like_count"},
        )
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


# ── Moderation ─────────────────────────────────────────────────────────────────

def hide_reply(reply_id: str, hide: bool = True) -> dict:
    """Sembunyikan atau tampilkan reply (threads_manage_replies)."""
    try:
        result = _api_post(f"{reply_id}/manage_reply", {"hide": str(hide).lower()})
        return {"ok": True, "result": result, "hidden": hide}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Insights / Analytics ───────────────────────────────────────────────────────

def get_account_insights(
    metrics: list[str] | None = None,
    period: str = "day",
    since: int | None = None,
    until: int | None = None,
) -> dict:
    """
    Ambil insights akun Threads (threads_manage_insights).
    Metrics: views, likes, replies, reposts, quotes, followers_count, follower_demographics
    Period: day, week, days_28, month, lifetime
    """
    token_data = _load_token()
    user_id = token_data.get("user_id", "me")
    m = ",".join(metrics or ["views", "likes", "replies", "reposts", "quotes", "followers_count"])
    params: dict = {"metric": m, "period": period}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    try:
        data = _api_get(f"{user_id}/threads_insights", params=params)
        return {"ok": True, "data": data.get("data", []), "period": period}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_post_insights(post_id: str, metrics: list[str] | None = None) -> dict:
    """Ambil insights per-post (threads_manage_insights)."""
    m = ",".join(metrics or ["views", "likes", "replies", "reposts", "quotes"])
    try:
        data = _api_get(f"{post_id}/insights", params={"metric": m})
        return {"ok": True, "post_id": post_id, "data": data.get("data", [])}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Mentions ───────────────────────────────────────────────────────────────────

def get_mentions(limit: int = 20) -> list[dict]:
    """
    Ambil post yang mention @sidixlab (threads_manage_mentions).
    Returns list posts yang menyebut akun kita.
    """
    token_data = _load_token()
    user_id = token_data.get("user_id", "me")
    try:
        data = _api_get(
            f"{user_id}/mentions",
            params={"fields": "id,text,timestamp,username,permalink", "limit": limit},
        )
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


# ── Keyword & Discovery Search ─────────────────────────────────────────────────

def keyword_search(keyword: str, limit: int = 25) -> list[dict]:
    """
    Cari post Threads berdasarkan kata kunci (threads_keyword_search).
    Berguna untuk discovery topik, kompetitor, tren.
    """
    try:
        data = _api_get(
            "keyword_search",
            params={
                "q": keyword,
                "fields": "id,text,timestamp,username,permalink,like_count,reply_count",
                "limit": limit,
            },
        )
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


def hashtag_search(tag: str, limit: int = 25) -> list[dict]:
    """
    Cari post dengan hashtag tertentu (threads_keyword_search).
    tag: tanpa '#', misal 'AIIndonesia'
    """
    return keyword_search(f"#{tag}", limit=limit)


def discover_trending(keywords: list[str] | None = None) -> dict:
    """
    Discover trending konten di topik SIDIX.
    Default keywords: AI Indonesia, LLM lokal, Quran AI, dll.
    """
    default_kw = [
        "AI Indonesia",
        "LLM lokal",
        "kecerdasan buatan",
        "sidixlab",
        "Islam AI",
        "machine learning Indonesia",
    ]
    kws = keywords or default_kw
    results: dict[str, list] = {}
    for kw in kws:
        posts = keyword_search(kw, limit=10)
        results[kw] = [p for p in posts if "error" not in p]
    return {
        "ok": True,
        "keywords_searched": kws,
        "results": results,
        "total_posts": sum(len(v) for v in results.values()),
    }


# ── Learning Harvester ─────────────────────────────────────────────────────────

def harvest_for_learning(
    keywords: list[str] | None = None,
    save_to_corpus: bool = True,
) -> dict:
    """
    Harvest konten Threads untuk dijadikan learning data SIDIX.
    Menggunakan keyword_search + mentions + replies untuk mengumpulkan data.
    """
    import datetime

    trending = discover_trending(keywords)
    mentions = get_mentions(limit=20)
    recent = get_recent_posts(limit=10)

    # Ekstrak teks unik untuk learning
    learning_items: list[dict] = []

    for kw, posts in trending.get("results", {}).items():
        for p in posts:
            if p.get("text"):
                learning_items.append({
                    "source": f"threads_keyword:{kw}",
                    "text": p["text"],
                    "timestamp": p.get("timestamp", ""),
                    "username": p.get("username", ""),
                    "permalink": p.get("permalink", ""),
                    "harvested_at": datetime.datetime.utcnow().isoformat(),
                })

    for m in mentions:
        if m.get("text") and "error" not in m:
            learning_items.append({
                "source": "threads_mention",
                "text": m["text"],
                "timestamp": m.get("timestamp", ""),
                "username": m.get("username", ""),
                "permalink": m.get("permalink", ""),
                "harvested_at": datetime.datetime.utcnow().isoformat(),
            })

    if save_to_corpus and learning_items:
        _save_learning_to_corpus(learning_items)

    return {
        "ok": True,
        "harvested": len(learning_items),
        "from_keywords": sum(len(v) for v in trending.get("results", {}).values()),
        "from_mentions": len([m for m in mentions if "error" not in m]),
        "from_recent": len(recent),
        "learning_items": learning_items[:5],  # preview saja
    }


def _save_learning_to_corpus(items: list[dict]) -> None:
    """Simpan harvested posts ke corpus SIDIX untuk learning."""
    import datetime
    out_dir = _TOKEN_FILE.parent / "threads_harvest"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.utcnow().strftime("%Y%m%d")
    out_file = out_dir / f"threads_harvest_{date_str}.jsonl"
    with open(out_file, "a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ── Auto-post Content Generator ────────────────────────────────────────────────

# Template cerita SIDIX — bilingual (ID+EN), mengundang, dengan keywords & ajakan follow
SIDIX_STORY_TEMPLATES = [
    # 0. Perkenalan (Indonesia)
    (
        "Kenalan yuk sama SIDIX 👋\n\n"
        "SIDIX adalah #FreeAIAgent open source buatan Indonesia — belajar dari riset nyata, "
        "bukan dari vendor cloud asing. Semua inferensi jalan lokal, privasi terjaga.\n\n"
        "Topik hari ini: {topic}\n\n"
        "Follow @sidixlab untuk update harian!\n"
        "🔗 sidixlab.com\n\n"
        "#AIOpenSource #LearningAI #AIIndonesia"
    ),
    # 1. Meet SIDIX (English)
    (
        "Meet SIDIX — a free, open-source AI agent built in Indonesia 🌏\n\n"
        "Today we're learning about: {topic}\n\n"
        "No OpenAI API. No Google Cloud. 100% local inference.\n"
        "Built on Islamic epistemology meets modern AI — a unique approach.\n\n"
        "Follow @sidixlab for daily AI insights!\n"
        "🔗 sidixlab.com\n\n"
        "#FreeAIAgent #AIOpenSource #LearningAI #OpenSourceAI"
    ),
    # 2. Update riset (Indonesia)
    (
        "📚 Riset SIDIX hari ini:\n\n"
        "{topic}\n\n"
        "SIDIX dibangun di atas epistemologi Islam modern — "
        "memadukan Nazhar (observasi), Amal (aksi), dan Taqyim (evaluasi).\n\n"
        "Open source. Gratis. Bahasa Indonesia.\n"
        "Follow @sidixlab | sidixlab.com\n\n"
        "#AIOpenSource #FreeAIGenerative #LearningAI"
    ),
    # 3. Research update (English)
    (
        "📖 SIDIX Research Update:\n\n"
        "{topic}\n\n"
        "We build AI grounded in epistemological rigor — not just data volume.\n"
        "Free to use. Open source. Self-hosted. Sovereign.\n\n"
        "Follow @sidixlab for daily updates\n"
        "🔗 sidixlab.com\n\n"
        "#FreeAIGenerative #AIOpenSource #LearningAI #OpenSourceAI"
    ),
    # 4. Behind the scenes (Indonesia)
    (
        "🔬 Behind the scenes SIDIX:\n\n"
        "{topic}\n\n"
        "Tidak ada OpenAI API. Tidak ada Google Cloud.\n"
        "Semua berjalan di server sendiri — kedaulatan data bukan pilihan, tapi prinsip.\n\n"
        "Free AI generative agent, 100% open source.\n"
        "Coba: sidixlab.com | Follow @sidixlab\n\n"
        "#FreeAIAgent #AIOpenSource #LearningAI"
    ),
    # 5. Technical deep dive (English)
    (
        "🔬 How SIDIX works:\n\n"
        "{topic}\n\n"
        "ReAct agent loop → BM25 RAG → local Qwen2.5 inference → Islamic epistemology filter\n"
        "Zero third-party AI APIs. Your data stays on our servers.\n\n"
        "Free open-source AI agent for Indonesian & global communities.\n"
        "🔗 sidixlab.com | Follow @sidixlab\n\n"
        "#FreeAIAgent #AIOpenSource #OpenSourceAI #LearningAI"
    ),
    # 6. Undangan komunitas (Indonesia)
    (
        "🌐 Untuk para builder Indonesia:\n\n"
        "{topic}\n\n"
        "SIDIX butuh kontributor! Kalau kamu peduli:\n"
        "• #AIOpenSource yang nyata\n"
        "• #FreeAIGenerative untuk semua\n"
        "• AI berbahasa Indonesia\n"
        "• Learning AI bersama komunitas\n\n"
        "DM atau: sidixlab.com | Follow @sidixlab 🙏\n\n"
        "#FreeAIAgent #AIIndonesia"
    ),
    # 7. Global community invite (English)
    (
        "🌍 Building AI for underserved languages:\n\n"
        "{topic}\n\n"
        "SIDIX is proof that you don't need Big Tech to build serious AI.\n"
        "Indonesian. Islamic epistemology. Open source. Free.\n\n"
        "Join the movement 👉 Follow @sidixlab\n"
        "🔗 sidixlab.com\n\n"
        "#FreeAIAgent #AIOpenSource #OpenSourceAI #LearningAI"
    ),
    # 8. Refleksi (Indonesia)
    (
        "🤔 Renungan AI hari ini:\n\n"
        "{topic}\n\n"
        "Di SIDIX, AI yang baik dimulai dari pertanyaan yang jujur — "
        "bukan dari data terbanyak.\n\n"
        "Free AI agent. Open source. Lokal.\n"
        "Follow @sidixlab | sidixlab.com\n\n"
        "#LearningAI #FreeAIGenerative #AIOpenSource"
    ),
    # 9. Philosophy (English)
    (
        "💭 AI should serve people, not corporations.\n\n"
        "Today's SIDIX insight: {topic}\n\n"
        "We believe in:\n"
        "• Transparent AI (open source)\n"
        "• Free access (#FreeAIGenerative)\n"
        "• Local-first inference\n"
        "• Epistemological honesty\n\n"
        "Follow @sidixlab for more\n"
        "🔗 sidixlab.com\n\n"
        "#FreeAIAgent #AIOpenSource #LearningAI"
    ),
    # 10. Ajakan follow (Indonesia)
    (
        "👆 Follow @sidixlab kalau kamu:\n\n"
        "✅ Tertarik #AIOpenSource\n"
        "✅ Mau #FreeAIGenerative tanpa biaya API\n"
        "✅ Ingin #LearningAI dengan konteks Indonesia & Islam\n"
        "✅ Percaya AI harus transparan & berdaulat\n\n"
        "Hari ini SIDIX belajar: {topic}\n\n"
        "🔗 sidixlab.com — #FreeAIAgent untuk semua"
    ),
    # 11. Call to action (English)
    (
        "🚀 Follow @sidixlab if you:\n\n"
        "✅ Care about #AIOpenSource\n"
        "✅ Want #FreeAIGenerative without API costs\n"
        "✅ Believe in sovereign, local AI\n"
        "✅ Are curious about Islamic epistemology × modern AI\n\n"
        "Today SIDIX is exploring: {topic}\n\n"
        "🔗 sidixlab.com — #FreeAIAgent for everyone"
    ),
]

# Topik harian yang bisa dirotasi (bilingual)
SIDIX_DAILY_TOPICS = [
    # Indonesian topics
    "Cara kerja RAG (Retrieval-Augmented Generation) dalam konteks bahasa Indonesia",
    "Maqashid Syariah sebagai framework evaluasi etika AI — inovasi Indonesia",
    "Perbedaan antara LLM lokal dan cloud API untuk privasi data",
    "QLoRA fine-tuning: cara SIDIX belajar dari corpus riset sendiri",
    "Sanad knowledge sebagai sistem verifikasi sumber dalam AI Islam",
    "Mengapa AI harus berdaulat: kasus SIDIX Indonesia",
    "Distributed learning: konsep Hafidz Architecture SIDIX",
    "Bagaimana SIDIX mengevaluasi kepercayaan sebuah informasi (Yaqin Tier)",
    "Open source vs closed AI: kenapa transparansi itu prinsip, bukan pilihan",
    "ReAct agent: cara SIDIX berpikir langkah demi langkah",
    # English topics
    "How we built a free AI agent without using any cloud AI APIs",
    "RAG vs Fine-tuning: when to use each for domain-specific AI",
    "Islamic epistemology in AI: a principled approach to knowledge validation",
    "Local-first AI inference: privacy, sovereignty, and cost benefits",
    "Building an open-source LLM for Indonesian language: challenges & progress",
    "QCalEval: why general-purpose VLMs fail at specialized scientific tasks",
    "GalaxyDiT: 2.37x video diffusion speedup without retraining",
    "From Nazhar to Amal: how SIDIX connects observation to action",
    "Why the AI community needs more non-English open-source models",
    "Self-hosting your AI stack: lessons from SIDIX VPS deployment",
    "How we use BM25 + semantic search for Indonesian corpus retrieval",
    "Confidence-based AI responses: SIDIX's Yaqin (certainty) tiering system",
]


def generate_sidix_post(topic: str, template_idx: int = 0) -> str:
    """Generate post text dari template SIDIX yang dipilih."""
    idx = template_idx % len(SIDIX_STORY_TEMPLATES)
    return SIDIX_STORY_TEMPLATES[idx].format(topic=topic)


def generate_daily_post(day_offset: int = 0) -> str:
    """
    Generate post harian berdasarkan rotasi topik + template.
    Alternates bilingual: English topics pakai English templates, dan sebaliknya.
    Template genap (0,2,4,...) = Indonesia, ganjil (1,3,5,...) = English.
    """
    day = (int(time.time() // 86400) + day_offset)
    topic_idx = day % len(SIDIX_DAILY_TOPICS)
    topic = SIDIX_DAILY_TOPICS[topic_idx]

    # Topik 0-9 = Indonesia, 10+ = English; template: genap=ID, ganjil=EN
    is_english_topic = topic_idx >= 10
    if is_english_topic:
        # Pilih template ganjil (English)
        en_templates = [i for i in range(len(SIDIX_STORY_TEMPLATES)) if i % 2 == 1]
        template_idx = en_templates[day % len(en_templates)]
    else:
        # Pilih template genap (Indonesia)
        id_templates = [i for i in range(len(SIDIX_STORY_TEMPLATES)) if i % 2 == 0]
        template_idx = id_templates[day % len(id_templates)]

    return SIDIX_STORY_TEMPLATES[template_idx].format(topic=topic)


# ── Profile Info ───────────────────────────────────────────────────────────────

def get_profile(fields: str = "id,username,name,biography,profile_picture_url,followers_count,threads_count") -> dict:
    """Ambil info profil Threads (threads_basic + threads_profile_discovery)."""
    token_data = _load_token()
    user_id = token_data.get("user_id", "me")
    try:
        data = _api_get(f"{user_id}", params={"fields": fields})
        return {"ok": True, "profile": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
