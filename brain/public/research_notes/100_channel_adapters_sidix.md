# 100 — Channel Adapters SIDIX: Integrasi Semua Channel ke Brain QA

**Tag:** IMPL / DOC  
**Tanggal:** 2026-04-18  
**File implementasi:** `apps/brain_qa/brain_qa/channel_adapters.py`

---

## Ringkasan Kontribusi

Research note ini adalah **sintesis** dari 4 sumber analisis:
- `96_wa_api_gateway_pattern.md` — WA Meta + Baileys dual engine
- `97_bot_gateway_architecture.md` — Python FastAPI + RQ multi-agent
- `98_chatbot_agent_pattern.md` — Intent pipeline, rule engine, session
- `99_artifact_processing.md` — Media/file artifact handling

---

## Apa yang Dibangun

`channel_adapters.py` adalah **bridge layer** antara channel komunikasi eksternal (WhatsApp, Telegram, webhook generik) dan otak SIDIX (`brain_qa`).

```
WhatsApp ──────┐
Telegram ───── ┤ → GatewayRouter → sidix_fn (brain_qa) → reply → channel
HTTP Webhook ──┘
```

---

## Komponen Utama

### 1. Data Types

```python
@dataclass
class InboundMessage:
    channel: str        # "whatsapp" | "telegram" | "generic"
    sender_id: str      # phone E.164 atau chat_id
    text: str           # teks pesan
    message_id: str     # ID dari platform
    media_url: str      # URL atau file_id jika ada media
    media_type: str     # "image" | "document" | "audio" | "video" | ""
    raw_payload: dict   # payload asli (audit trail)
    timestamp: float    # unix timestamp

@dataclass
class OutboundMessage:
    channel: str
    recipient_id: str
    text: str
    buttons: list[dict] # quick reply buttons (TG inline keyboard)
    parse_mode: str     # "HTML" | "Markdown" untuk Telegram

@dataclass
class SendResult:
    ok: bool
    message_id: str
    error: str
    raw_response: dict
```

### 2. WAAdapter (WhatsApp)

```python
adapter = WAAdapter(engine="meta")  # atau "baileys" atau "none"

# Parse pesan masuk dari Meta webhook
inbound = adapter.parse_incoming(meta_webhook_payload)

# Format jawaban SIDIX untuk WA
outbound = adapter.format_message({"answer": "...", "sources": [...]})

# Kirim ke user
result = await adapter.send_reply("+628123", "Halo dari SIDIX!")

# Verifikasi webhook GET dari Meta
challenge = adapter.verify_webhook(mode, token, challenge)
```

### 3. TelegramAdapter

```python
adapter = TelegramAdapter(bot_token="1234:xxx")

# Parse update Telegram (message, callback_query, edited_message)
inbound = adapter.parse_incoming(telegram_update)

# Format jawaban dengan HTML support
outbound = adapter.format_message({"answer": "<b>Halo!</b>", "sources": [...]})

# Kirim pesan
result = await adapter.send_reply(chat_id, "Halo!", parse_mode="HTML")

# Jawab callback query (dismiss loading spinner di button)
await adapter.answer_callback(callback_query_id)
```

### 4. GatewayRouter — Inti Sistem

```python
router = GatewayRouter()
# Adapter WA, TG, generic sudah terdaftar otomatis

# Full pipeline dalam satu panggilan:
result = await router.route(
    channel="whatsapp",
    raw_payload=webhook_payload,
    sidix_fn=my_brain_qa_call,  # dipanggil dengan InboundMessage
)
# → {"ok": True, "answer": "...", "send_result": {...}}

# Statistik
print(router.get_adapters())
print(router.get_recent_log(20))
```

### 5. sidix_fn Interface

```python
# sidix_fn harus menerima InboundMessage dan return dict:
async def my_brain_qa_call(inbound: InboundMessage) -> dict:
    from brain_qa.query import ask
    answer = await ask(inbound.text)
    return {"answer": answer, "sources": [], "recipient_id": inbound.sender_id}

# Atau sync:
def my_sidix_call(inbound: InboundMessage) -> dict:
    return {"answer": "Baik!", "sources": []}
```

---

## Integrasi dengan FastAPI (Contoh)

```python
# Di agent_serve.py atau serve.py — tambahkan endpoint webhook:
from brain_qa.channel_adapters import get_router, InboundMessage

router = get_router()

@app.post("/webhook/whatsapp")
async def wa_webhook(payload: dict, background_tasks: BackgroundTasks):
    async def sidix_fn(inbound: InboundMessage) -> dict:
        from brain_qa.query import ask
        answer = await ask(inbound.text)
        return {"answer": answer, "recipient_id": inbound.sender_id}

    result = await router.route("whatsapp", payload, sidix_fn=sidix_fn)
    return {"ok": True}

@app.post("/webhook/telegram")
async def tg_webhook(payload: dict):
    async def sidix_fn(inbound: InboundMessage) -> dict:
        from brain_qa.query import ask
        answer = await ask(inbound.text)
        return {"answer": answer, "recipient_id": inbound.sender_id}

    result = await router.route("telegram", payload, sidix_fn=sidix_fn)
    return {"ok": True}

@app.get("/channels/stats")
async def channel_stats():
    from brain_qa.channel_adapters import get_channel_stats
    return get_channel_stats()
```

---

## Keputusan Desain

| Keputusan | Alasan |
|-----------|--------|
| Tidak ada vendor AI di adapter | Sesuai aturan SIDIX — semua AI via brain_qa lokal |
| try/except untuk httpx/requests | Modul dapat diimport tanpa dependencies wajib |
| BaseAdapter ABC | Mudah extend ke channel baru (Line, Slack, Discord) |
| Singleton GatewayRouter | State statistik konsisten, tidak buat ulang per request |
| InboundMessage dataclass frozen? No | Perlu fleksibel untuk enrichment (media download, dll) |
| DRY-RUN mode (engine="none") | Testing tanpa perlu API kredensial |

---

## Roadmap Ekstensi

1. **Download & process media** — wire `media_url` ke `apps/vision/` (gambar) dan `audio_capability.py` (suara)
2. **Session context** — simpan riwayat percakapan di Redis/Supabase agar SIDIX aware multi-turn
3. **Rate limiting** — per sender_id, cegah spam
4. **Retry logic** — jika send gagal, retry 3x dengan exponential backoff
5. **Webhook signature verification** — HMAC-SHA256 untuk keamanan webhook Meta
6. **Slack adapter** — tambah `SlackAdapter(BaseAdapter)` mengikuti pola yang sama
7. **Discord adapter** — idem

---

## Cara Import

```python
# Paling simpel
from brain_qa.channel_adapters import WAAdapter, TelegramAdapter, GatewayRouter

# Atau pakai convenience functions
from brain_qa.channel_adapters import get_router, get_channel_stats

router = get_router()
stats = get_channel_stats()
```

---

## Filosofi

> "Channel adalah pintu. SIDIX adalah otak. Adapter adalah penjemput tamu yang sopan."

Adapter tidak boleh mengandung logika bisnis atau AI — hanya normalisasi format. Semua kecerdasan ada di `brain_qa`.
