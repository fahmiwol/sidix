"""
threads_scheduler.py — SIDIX Autonomous Threads Agent.

Menjalankan siklus harian secara otomatis:
1. Harvest learning data dari keyword search & mentions
2. Post konten SIDIX harian (story + topik)
3. Monitor & catat mentions untuk learning
4. Reply cerdas ke mentions (optional)
5. Simpan semua data untuk fine-tuning corpus

Jadwal aman (tidak kena rate limit Meta):
  - Satu post per hari (posting window: jam 8 pagi WIB)
  - Harvest keyword: 4x per hari (interval 6 jam)
  - Cek mentions: setiap 3 jam
  - Total API call per hari: ~30-50 (sangat di bawah limit)

Cara pakai:
  from .threads_scheduler import run_daily_cycle, run_harvest_cycle
  run_daily_cycle()   # satu siklus lengkap
  run_harvest_cycle() # harvest saja tanpa posting
"""

from __future__ import annotations

import json
import os
import time
import datetime
from pathlib import Path
from typing import Optional


# ── Config ─────────────────────────────────────────────────────────────────────

# Path untuk state file (track sudah posting hari ini atau belum)
_STATE_FILE = Path(__file__).parent.parent.parent / ".data" / "threads_scheduler_state.json"

# Default keywords untuk monitoring (bisa diubah via /threads/scheduler/config)
DEFAULT_MONITOR_KEYWORDS = [
    "AI Indonesia",
    "LLM lokal",
    "kecerdasan buatan Indonesia",
    "AI open source",
    "machine learning Indonesia",
    "sidixlab",
    "Islam AI",
    "free AI agent",
    "AI generatif gratis",
    "belajar AI",
]

# Jam posting (WIB = UTC+7): default jam 8 pagi
POST_HOUR_UTC = int(os.getenv("SIDIX_POST_HOUR_UTC", "1"))  # 01:00 UTC = 08:00 WIB

# Auto-reply to mentions: True untuk aktif
AUTO_REPLY_MENTIONS = os.getenv("SIDIX_AUTO_REPLY_MENTIONS", "false").lower() == "true"

# Template reply ke mention
MENTION_REPLY_TEMPLATES = [
    "Terima kasih sudah mention SIDIX! 🙏 Kalau ada yang bisa kami bantu soal AI open source, langsung DM atau kunjungi sidixlab.com",
    "Hei @{username}, terima kasih! SIDIX selalu terbuka untuk diskusi soal AI lokal & epistemologi. Cek sidixlab.com ya 🧠",
    "Thanks sudah mention! SIDIX adalah free AI agent open source — gratis, lokal, bahasa Indonesia. sidixlab.com 💙",
]


# ── State Management ──────────────────────────────────────────────────────────

def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _today_str() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _is_posted_today() -> bool:
    state = _load_state()
    return state.get("last_post_date", "") == _today_str()


def _mark_posted(post_id: str, text: str) -> None:
    state = _load_state()
    state["last_post_date"] = _today_str()
    state["last_post_id"] = post_id
    state["last_post_text"] = text[:200]
    state["post_count"] = state.get("post_count", 0) + 1
    _save_state(state)


def get_scheduler_stats() -> dict:
    state = _load_state()
    return {
        "posted_today": _is_posted_today(),
        "last_post_date": state.get("last_post_date"),
        "last_post_id": state.get("last_post_id"),
        "total_posts": state.get("post_count", 0),
        "total_harvest": state.get("harvest_count", 0),
        "total_mentions_processed": state.get("mentions_processed", 0),
        "monitor_keywords": _load_config().get("keywords", DEFAULT_MONITOR_KEYWORDS),
        "auto_reply": AUTO_REPLY_MENTIONS,
        "post_hour_utc": POST_HOUR_UTC,
        "post_hour_wib": (POST_HOUR_UTC + 7) % 24,
    }


# ── Config Management ─────────────────────────────────────────────────────────

_CONFIG_FILE = Path(__file__).parent.parent.parent / ".data" / "threads_scheduler_config.json"


def _load_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"keywords": DEFAULT_MONITOR_KEYWORDS}


def update_config(keywords: list[str] | None = None, **kwargs) -> dict:
    """Update konfigurasi scheduler."""
    config = _load_config()
    if keywords is not None:
        config["keywords"] = keywords
    config.update(kwargs)
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


# ── Core Cycles ───────────────────────────────────────────────────────────────

def run_daily_post(force: bool = False, dry_run: bool = False) -> dict:
    """
    Jalankan daily post SIDIX.
    force=True: post meskipun sudah posting hari ini
    dry_run=True: preview text tanpa benar-benar posting
    """
    from .threads_oauth import generate_daily_post, create_text_post, get_token

    if not get_token():
        return {"ok": False, "reason": "Threads belum terhubung. Setup via /threads/auth"}

    if _is_posted_today() and not force:
        state = _load_state()
        return {
            "ok": True,
            "skipped": True,
            "reason": "Sudah posting hari ini",
            "last_post_id": state.get("last_post_id"),
        }

    post_text = generate_daily_post()

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "text_preview": post_text,
            "char_count": len(post_text),
        }

    try:
        result = create_text_post(post_text)
        if result.get("ok"):
            _mark_posted(result.get("post_id", ""), post_text)
        return {
            "ok": True,
            "posted": True,
            "post_id": result.get("post_id"),
            "permalink": result.get("permalink"),
            "text": post_text[:100] + "...",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_harvest_cycle(keywords: list[str] | None = None, save: bool = True) -> dict:
    """
    Jalankan harvest siklus: keyword search + mentions → simpan untuk learning.
    Aman dijalankan 4x/hari.
    """
    from .threads_oauth import harvest_for_learning

    config = _load_config()
    kws = keywords or config.get("keywords", DEFAULT_MONITOR_KEYWORDS)

    result = harvest_for_learning(keywords=kws, save_to_corpus=save)

    # Update state
    state = _load_state()
    state["harvest_count"] = state.get("harvest_count", 0) + result.get("harvested", 0)
    state["last_harvest_at"] = datetime.datetime.utcnow().isoformat()
    _save_state(state)

    return result


def run_mention_monitor(auto_reply: bool = False, dry_run: bool = True) -> dict:
    """
    Monitor mentions @sidixlab. Opsional: auto-reply ke mentions baru.
    Default dry_run=True agar tidak spam.
    """
    from .threads_oauth import get_mentions, reply_to_post, get_token

    if not get_token():
        return {"ok": False, "reason": "Threads tidak terhubung"}

    state = _load_state()
    seen_ids = set(state.get("seen_mention_ids", []))
    mentions = get_mentions(limit=25)

    new_mentions = [m for m in mentions if m.get("id") and m["id"] not in seen_ids and "error" not in m]
    replied = []

    if auto_reply and not dry_run:
        for m in new_mentions[:3]:  # max 3 auto-reply per siklus
            username = m.get("username", "")
            idx = len(replied) % len(MENTION_REPLY_TEMPLATES)
            reply_text = MENTION_REPLY_TEMPLATES[idx].format(username=username)
            try:
                res = reply_to_post(m["id"], reply_text)
                replied.append({"mention_id": m["id"], "reply_id": res.get("post_id"), "ok": True})
            except Exception as e:
                replied.append({"mention_id": m["id"], "ok": False, "error": str(e)})
            time.sleep(2)  # jeda antar reply

    # Simpan semua mention IDs yang sudah dilihat
    all_ids = list(seen_ids | {m["id"] for m in new_mentions if m.get("id")})
    state["seen_mention_ids"] = all_ids[-500:]  # keep 500 terbaru
    state["mentions_processed"] = state.get("mentions_processed", 0) + len(new_mentions)
    state["last_mention_check"] = datetime.datetime.utcnow().isoformat()
    _save_state(state)

    return {
        "ok": True,
        "new_mentions": len(new_mentions),
        "mentions": new_mentions[:10],
        "auto_reply": auto_reply,
        "dry_run": dry_run,
        "replied": replied,
    }


def run_series_post(post_type: str, force: bool = False, dry_run: bool = False) -> dict:
    """
    Post salah satu bagian dari seri 3-post harian SIDIX.

    post_type: 'hook' | 'detail' | 'cta'
    force: posting meskipun sudah dipost hari ini
    dry_run: preview tanpa kirim

    Jadwal optimal (WIB):
      hook   → 08:00 (UTC 01:00)
      detail → 12:00 (UTC 05:00)
      cta    → 18:00 (UTC 11:00)
    """
    from .threads_oauth import create_text_post, get_token
    from .threads_series import get_today_series, mark_post_sent

    if post_type not in ("hook", "detail", "cta"):
        return {"ok": False, "error": f"post_type harus 'hook', 'detail', atau 'cta'. Got: {post_type}"}

    if not get_token():
        return {"ok": False, "reason": "Threads belum terhubung. Setup via /threads/auth"}

    series_data = get_today_series()
    post_text = series_data.get(post_type, "")

    if not post_text:
        return {"ok": False, "error": f"Teks '{post_type}' kosong untuk hari ini"}

    # Cek apakah sudah dipost hari ini
    already = series_data.get(f"{post_type}_posted", False)
    if already and not force:
        return {
            "ok": True,
            "skipped": True,
            "reason": f"'{post_type}' sudah dipost hari ini",
            "post_id": series_data.get(f"{post_type}_post_id"),
        }

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "post_type": post_type,
            "angle": series_data.get("angle"),
            "language": series_data.get("language"),
            "topic": series_data.get("topic"),
            "text_preview": post_text,
            "char_count": len(post_text),
        }

    try:
        result = create_text_post(post_text)
        if result.get("ok"):
            post_id = result.get("post_id", "")
            mark_post_sent(post_type, post_id)
            # Update scheduler state global juga
            state = _load_state()
            state["last_post_date"] = _today_str()
            state[f"last_{post_type}_post_id"] = post_id
            state["post_count"] = state.get("post_count", 0) + 1
            _save_state(state)
            return {
                "ok": True,
                "posted": True,
                "post_type": post_type,
                "angle": series_data.get("angle"),
                "language": series_data.get("language"),
                "topic": series_data.get("topic"),
                "post_id": post_id,
                "permalink": result.get("permalink"),
                "char_count": len(post_text),
            }
        else:
            return {"ok": False, "error": result.get("error", "Unknown error"), "post_type": post_type}
    except Exception as e:
        return {"ok": False, "error": str(e), "post_type": post_type}


def preview_today_series(day: int | None = None) -> dict:
    """Preview semua 3 post series hari ini tanpa mengirim."""
    from .threads_series import get_today_series, generate_series
    series = get_today_series() if day is None else generate_series(day)
    return {
        "ok": True,
        "angle": series.get("angle"),
        "language": series.get("language"),
        "topic": series.get("topic"),
        "hook": {
            "text": series.get("hook", ""),
            "char_count": len(series.get("hook", "")),
            "posted": series.get("hook_posted", False),
        },
        "detail": {
            "text": series.get("detail", ""),
            "char_count": len(series.get("detail", "")),
            "posted": series.get("detail_posted", False),
        },
        "cta": {
            "text": series.get("cta", ""),
            "char_count": len(series.get("cta", "")),
            "posted": series.get("cta_posted", False),
        },
    }


def run_daily_cycle(dry_run: bool = False) -> dict:
    """
    Siklus lengkap harian SIDIX Threads Agent:
    1. Harvest keyword search
    2. Monitor mentions
    3. Daily post (jika belum)
    4. Simpan stats

    Aman: cek kondisi sebelum tiap aksi.
    """
    results: dict = {
        "cycle_at": datetime.datetime.utcnow().isoformat(),
        "dry_run": dry_run,
    }

    # Step 1: Harvest
    try:
        harvest_result = run_harvest_cycle()
        results["harvest"] = {
            "ok": harvest_result.get("ok"),
            "harvested": harvest_result.get("harvested", 0),
        }
    except Exception as e:
        results["harvest"] = {"ok": False, "error": str(e)}

    # Step 2: Mentions
    try:
        mention_result = run_mention_monitor(
            auto_reply=AUTO_REPLY_MENTIONS,
            dry_run=dry_run,
        )
        results["mentions"] = {
            "ok": mention_result.get("ok"),
            "new_mentions": mention_result.get("new_mentions", 0),
        }
    except Exception as e:
        results["mentions"] = {"ok": False, "error": str(e)}

    # Step 3: Post
    try:
        post_result = run_daily_post(dry_run=dry_run)
        results["post"] = post_result
    except Exception as e:
        results["post"] = {"ok": False, "error": str(e)}

    return results
