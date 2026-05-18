"""
SIDIX Telegram Bot — dengan Security Layer
───────────────────────────────────────────
Public mode: siapa saja bisa tanya & ngajarin SIDIX
Private mode: hanya user di ALLOWED list yang bisa akses

SECURITY:
  - Input sanitization (strip control chars, limit length)
  - Rate limiting per user (anti spam / injection flood)
  - JSON injection protection (tidak pernah eval input)
  - ALLOWED_USERS whitelist (opsional, bisa public)
  - Semua request ke SIDIX pakai timeout ketat
  - Log setiap request untuk audit

Commands:
  /tanya <pertanyaan>  → SIDIX jawab
  /simpan <catatan>    → simpan ke corpus
  /post <teks>         → posting ke Threads (ADMIN only)
  /status              → cek SIDIX (ADMIN only)
  (pesan biasa)        → SIDIX belajar otomatis
"""

import os
import re
import time
import hashlib
import logging
from collections import defaultdict
from dotenv import load_dotenv
import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
SIDIX_URL        = os.getenv("SIDIX_URL", "http://localhost:8765")
THREADS_TOKEN    = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_USER_ID  = os.getenv("THREADS_USER_ID", "")

# Whitelist admin (username telegram, tanpa @) — pisah koma
# Kosong = semua bisa akses fitur publik
_admin_raw = os.getenv("ADMIN_TELEGRAM_USERS", "")
ADMIN_USERS = {u.strip().lower() for u in _admin_raw.split(",") if u.strip()}

# Mode public: siapa saja bisa tanya & ngajarin
PUBLIC_MODE = os.getenv("PUBLIC_MODE", "true").lower() == "true"

# Rate limit: max N pesan per menit per user
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))

# Max panjang input yang diterima
MAX_INPUT_LEN = int(os.getenv("MAX_INPUT_LEN", "2000"))

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sidix_bot.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("sidix-bot")

# ──────────────────────────────────────────
# SECURITY: Rate Limiter
# ──────────────────────────────────────────
_rate_buckets: dict[int, list[float]] = defaultdict(list)

def is_rate_limited(user_id: int) -> bool:
    """True jika user sudah melebihi RATE_LIMIT_PER_MIN dalam 60 detik terakhir."""
    now = time.time()
    bucket = _rate_buckets[user_id]
    # Hapus timestamp yang sudah > 60 detik
    _rate_buckets[user_id] = [t for t in bucket if now - t < 60]
    if len(_rate_buckets[user_id]) >= RATE_LIMIT_PER_MIN:
        return True
    _rate_buckets[user_id].append(now)
    return False


# ──────────────────────────────────────────
# SECURITY: Input Sanitization
# ──────────────────────────────────────────
def sanitize(text: str) -> str:
    """
    Bersihkan input sebelum dikirim ke SIDIX atau mana pun.
    - Hapus control characters (null byte, escape seq, dll)
    - Potong ke MAX_INPUT_LEN
    - Strip whitespace berlebih
    """
    if not text:
        return ""
    # Hapus null bytes dan control chars kecuali newline & tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Hapus ANSI escape sequences
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    # Limit panjang
    text = text[:MAX_INPUT_LEN]
    # Strip whitespace berlebih di awal/akhir
    return text.strip()


def is_suspicious(text: str) -> bool:
    """Deteksi pola injection / eksploitasi umum."""
    patterns = [
        r"<script",          # XSS
        r"javascript:",      # XSS
        r"\{\{.*\}\}",       # template injection
        r"\$\{.*\}",         # JS template literal injection
        r"__import__",       # Python code injection
        r"eval\s*\(",        # eval injection
        r"exec\s*\(",        # exec injection
        r"subprocess",       # shell injection
        r"os\.system",       # shell injection
        r"DROP\s+TABLE",     # SQL injection
        r";\s*DELETE\s+FROM",# SQL injection
        r"UNION\s+SELECT",   # SQL injection
        r"../\.\.",          # path traversal
        r"etc/passwd",       # path traversal
    ]
    text_lower = text.lower()
    for p in patterns:
        if re.search(p, text_lower, re.IGNORECASE):
            return True
    return False


# ──────────────────────────────────────────
# Access control
# ──────────────────────────────────────────
def is_admin(update: Update) -> bool:
    username = (update.effective_user.username or "").lower()
    return username in ADMIN_USERS

def can_access(update: Update) -> bool:
    """Public mode: semua bisa. Private mode: hanya admin."""
    if PUBLIC_MODE:
        return True
    return is_admin(update)

def user_label(update: Update) -> str:
    u = update.effective_user
    return f"@{u.username or 'anon'} (id:{u.id})"


# ──────────────────────────────────────────
# SIDIX API calls — semua pakai timeout ketat
# ──────────────────────────────────────────
def sidix_capture(topic: str, content: str, source: str = "telegram") -> bool:
    try:
        r = requests.post(
            f"{SIDIX_URL}/corpus/capture",
            json={
                "topic":   topic,
                "content": content,   # sudah di-sanitize sebelum masuk sini
                "source":  source,
                "project": "SIDIX",
            },
            timeout=8,
        )
        data = r.json()
        return bool(data.get("ok") or data.get("id") or data.get("status"))
    except Exception as e:
        log.warning(f"sidix_capture error: {e}")
        return False


def sidix_query(question: str) -> str:
    try:
        r = requests.post(
            f"{SIDIX_URL}/agent/chat",
            json={
                "question": question,          # field name sesuai ChatRequest schema
                "allow_web_fallback": True,
                "simple_mode": False,          # false = jawaban lebih natural, tanpa template kaku
            },
            timeout=120,                       # 7b butuh waktu lebih
        )
        data = r.json()
        return (
            data.get("reply") or
            data.get("response") or
            data.get("answer") or
            "⚠ Tidak ada jawaban dari SIDIX."
        )
    except Exception as e:
        log.warning(f"sidix_query error: {e}")
        return f"⚠ SIDIX tidak bisa dihubungi saat ini."


def sidix_status() -> dict:
    try:
        r = requests.get(f"{SIDIX_URL}/health", timeout=5)
        return r.json()
    except Exception:
        return {}


def post_to_threads(text: str) -> tuple[bool, str]:
    """Return (sukses, pesan error)."""
    if not THREADS_TOKEN or not THREADS_USER_ID:
        return False, "THREADS_TOKEN / THREADS_USER_ID belum diset di .env"
    try:
        r1 = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads",
            params={"media_type": "TEXT", "text": text, "access_token": THREADS_TOKEN},
            timeout=12,
        )
        creation_id = r1.json().get("id")
        if not creation_id:
            err = r1.json().get("error", {}).get("message", "unknown")
            return False, f"Step 1 gagal: {err}"

        r2 = requests.post(
            f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish",
            params={"creation_id": creation_id, "access_token": THREADS_TOKEN},
            timeout=12,
        )
        post_id = r2.json().get("id")
        if post_id:
            return True, post_id
        err = r2.json().get("error", {}).get("message", "unknown")
        return False, f"Step 2 gagal: {err}"
    except Exception as e:
        return False, str(e)


# ──────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not can_access(update):
        return
    mode = "🌐 Public" if PUBLIC_MODE else "🔒 Private"
    await update.message.reply_text(
        f"🧠 *SIDIX Bot* — {mode}\n\n"
        "Kirim pesan apa saja → SIDIX belajar\n\n"
        "*Commands:*\n"
        "/tanya pertanyaan → SIDIX jawab\n"
        "/simpan catatan → simpan ke corpus\n"
        + ("/post teks → posting ke Threads _(admin)_\n" if is_admin(update) else "")
        + ("/status → cek SIDIX _(admin)_\n" if is_admin(update) else ""),
        parse_mode="Markdown"
    )


async def cmd_tanya(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not can_access(update):
        return
    uid = update.effective_user.id
    if is_rate_limited(uid):
        await update.message.reply_text("⏳ Terlalu cepat, tunggu sebentar ya.")
        return

    raw = " ".join(ctx.args)
    question = sanitize(raw)

    if not question:
        await update.message.reply_text("Tulis pertanyaan setelah /tanya\nContoh: `/tanya Apa itu RAG?`", parse_mode="Markdown")
        return

    if is_suspicious(question):
        log.warning(f"Suspicious input dari {user_label(update)}: {question[:100]}")
        await update.message.reply_text("⚠ Input tidak diizinkan.")
        return

    log.info(f"/tanya dari {user_label(update)}: {question[:80]}")
    msg = await update.message.reply_text("🔍 Tanya SIDIX...")
    jawaban = sidix_query(question)

    # Potong kalau terlalu panjang untuk Telegram (max 4096 char)
    if len(jawaban) > 4000:
        jawaban = jawaban[:4000] + "\n\n_(terpotong)_"

    await msg.edit_text(f"🧠 *SIDIX:*\n{jawaban}", parse_mode="Markdown")

    # Rekam pasangan tanya-jawab ke corpus
    sidix_capture(
        topic="tanya-jawab-publik",
        content=f"Q: {question}\nA: {jawaban}",
        source="telegram-public" if PUBLIC_MODE else "telegram-admin"
    )


async def cmd_simpan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not can_access(update):
        return
    uid = update.effective_user.id
    if is_rate_limited(uid):
        await update.message.reply_text("⏳ Terlalu cepat, tunggu sebentar ya.")
        return

    raw = " ".join(ctx.args)
    catatan = sanitize(raw)

    if not catatan:
        await update.message.reply_text("Tulis catatan setelah /simpan")
        return

    if is_suspicious(catatan):
        log.warning(f"Suspicious /simpan dari {user_label(update)}: {catatan[:100]}")
        await update.message.reply_text("⚠ Input tidak diizinkan.")
        return

    log.info(f"/simpan dari {user_label(update)}: {catatan[:60]}")
    ok = sidix_capture(topic="telegram-manual", content=catatan)
    if ok:
        await update.message.reply_text("✅ Tersimpan ke SIDIX!\n📚 _Sidix, ikut belajar yah dari pojokan_ ✓", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠ Gagal simpan — SIDIX offline?")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🔒 Hanya admin.")
        return
    data = sidix_status()
    if data:
        teks = (
            f"✅ *SIDIX Online*\n"
            f"Dokumen: `{data.get('documents', data.get('doc_count', '?'))}`\n"
            f"Status: `{data.get('status', 'ok')}`\n"
            f"URL: `{SIDIX_URL}`"
        )
    else:
        teks = f"⚠ *SIDIX Offline*\nURL: `{SIDIX_URL}`"
    await update.message.reply_text(teks, parse_mode="Markdown")


async def cmd_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🔒 Hanya admin yang bisa posting ke Threads.")
        return

    raw = " ".join(ctx.args)
    teks = sanitize(raw)

    if not teks:
        await update.message.reply_text("Tulis teks setelah /post\nContoh: `/post Halo dari SIDIX!`", parse_mode="Markdown")
        return

    if is_suspicious(teks):
        await update.message.reply_text("⚠ Input tidak diizinkan.")
        return

    if len(teks) > 500:
        await update.message.reply_text("⚠ Teks terlalu panjang (max 500 karakter untuk Threads).")
        return

    msg = await update.message.reply_text("📤 Posting ke Threads...")
    ok, info = post_to_threads(teks)
    if ok:
        await msg.edit_text(f"✅ Posted ke Threads! ID: `{info}`", parse_mode="Markdown")
        sidix_capture(topic="threads-post", content=f"Konten diposting ke Threads: {teks}")
        log.info(f"Threads post sukses oleh {user_label(update)}: {teks[:80]}")
    else:
        await msg.edit_text(f"⚠ Gagal posting: {info}")
        log.warning(f"Threads post gagal: {info}")


def _is_question(text: str) -> bool:
    """
    Deteksi apakah teks adalah pertanyaan yang butuh jawaban.

    Fix v2: kata tanya di akhir kalimat sekarang terdeteksi
    (pakai startswith + ' {w}' — tidak butuh spasi setelah kata).
    """
    import re as _re
    t = text.lower().strip()

    # Tanda tanya — paling pasti
    if "?" in t:
        return True

    # Kata tanya Indonesia/Inggris — cek pakai word-boundary regex
    question_words = (
        "apa", "siapa", "berapa", "kenapa", "mengapa", "bagaimana",
        "kapan", "dimana", "di mana", "kemana", "bisakah", "apakah",
        "bolehkah", "tolong", "jelaskan", "ceritakan", "sebutkan",
        "gimana", "emang", "emangnya", "maksudnya",
        "what", "who", "how", "why", "when", "where", "which",
        "can you", "tell me", "explain", "describe",
    )
    for w in question_words:
        # Cek dengan word boundary supaya "apa" tidak match "kapan" dll
        if _re.search(r'\b' + _re.escape(w) + r'\b', t):
            return True

    # Kalimat pendek (<= 6 kata) tanpa tanda baca pernyataan → tanya
    words = t.split()
    if len(words) <= 6 and not any(c in t for c in [".", "!", ","]):
        return True

    return False


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Pesan biasa → SIDIX jawab JIKA pertanyaan, sekaligus belajar.
    Kalau bukan pertanyaan → SIDIX simpan sebagai knowledge.
    """
    if not can_access(update):
        return
    uid = update.effective_user.id
    if is_rate_limited(uid):
        return

    raw = update.message.text or ""
    teks = sanitize(raw)

    if not teks or teks.startswith("/"):
        return

    if is_suspicious(teks):
        log.warning(f"Suspicious message dari {user_label(update)}: {teks[:100]}")
        await update.message.reply_text("⚠ Pesan ini tidak bisa diproses.")
        return

    log.info(f"Message dari {user_label(update)}: {teks[:60]}")

    # ── SIDIX menjawab kalau pertanyaan ──────────────────────────────────────
    if _is_question(teks):
        msg = await update.message.reply_text("🔍 Tanya SIDIX...", quote=True)
        jawaban = sidix_query(teks)
        if len(jawaban) > 4000:
            jawaban = jawaban[:4000] + "\n\n_(terpotong)_"

        # Simpan juga ke corpus (pasangan Q&A)
        sidix_capture(
            topic="tanya-jawab-telegram",
            content=f"Q: {teks}\nA: {jawaban}",
            source="telegram-public"
        )
        await msg.edit_text(f"🧠 *SIDIX:*\n{jawaban}", parse_mode="Markdown")

    # ── SIDIX belajar dari statement / pernyataan ────────────────────────────
    else:
        ok = sidix_capture(topic="telegram-input", content=teks)
        if ok:
            await update.message.reply_text(
                "📚 *Sidix, ikut belajar yah dari pojokan* ✓",
                parse_mode="Markdown",
                quote=True
            )
        else:
            await update.message.reply_text(
                "⚠ SIDIX offline, pesan tidak tersimpan\n"
                "_Coba lagi nanti atau /tanya untuk bertanya_",
                parse_mode="Markdown",
                quote=True
            )


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.error(f"Exception: {ctx.error}", exc_info=ctx.error)


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────
def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN tidak ditemukan di .env")
        return

    # Python 3.10+ tidak auto-create event loop — harus explicit
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("tanya",  cmd_tanya))
    app.add_handler(CommandHandler("simpan", cmd_simpan))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("post",   cmd_post))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    log.info(f"🤖 SIDIX Telegram Bot jalan — SIDIX: {SIDIX_URL} | Public: {PUBLIC_MODE}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
