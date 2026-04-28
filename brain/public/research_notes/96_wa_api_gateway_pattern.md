# 96 — Pola WA API Gateway: Webhook, Format Pesan, Dual Engine

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** IMPL / DOC  
**Tanggal:** 2026-04-18  
**Sumber analisis:** `D:\WA API GATeway\cosmic-architect-os` (NestJS + TypeScript)

---

## Apa Ini?

WhatsApp API Gateway adalah lapisan perantara antara platform WhatsApp dan logika bisnis/AI backend. Ia menerima pesan masuk (inbound) via webhook, memprosesnya, dan mengirim balik jawaban (outbound) ke user WhatsApp.

---

## Arsitektur yang Ditemukan

```
WhatsApp User
    │ (pesan teks/media)
    ▼
[Meta Cloud API / Baileys WebSocket]
    │ webhook POST / event "messages.upsert"
    ▼
WA Gateway (NestJS)
    ├── MetaWebhookController   → POST /webhooks/meta
    ├── BaileysService          → @whiskeysockets/baileys socket
    └── MessagePipelineService  → normalize → intent → action → reply
    │
    ▼
DB (Prisma + PostgreSQL)  ←→  Redis (BullMQ queue)
```

### Dua Engine yang Didukung

| Engine | Protokol | Keunggulan | Kelemahan |
|--------|----------|------------|-----------|
| **Meta Cloud API** | HTTPS webhook resmi | Stabil, TOS-compliant, mendukung media rich | Butuh Meta Business Verified |
| **Baileys** | WebSocket non-resmi (@whiskeysockets) | Gratis, tidak perlu verifikasi Meta | Risk ban, sesi via QR |

Config: `WA_ENGINE=meta|baileys|none` di `.env`

---

## Format Pesan

### Inbound — Meta Cloud API
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "628123456789",
          "id": "wamid.HBgL...",
          "type": "text",
          "text": {"body": "halo SIDIX"}
        }]
      }
    }]
  }]
}
```

### Outbound — Meta Graph API
```json
POST https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages
Authorization: Bearer {ACCESS_TOKEN}

{
  "messaging_product": "whatsapp",
  "to": "628123456789",
  "type": "text",
  "text": {
    "preview_url": false,
    "body": "Halo! Ini jawaban dari SIDIX."
  }
}
```

### Inbound — Baileys
Baileys menggunakan event socket `messages.upsert`. Field kunci:
- `msg.key.remoteJid` → `628XXX@s.whatsapp.net` (JID)
- `msg.message.conversation` → teks pesan
- `msg.message.extendedTextMessage.text` → teks dengan mention/quote

---

## Normalisasi Nomor Telepon

Pattern konsisten yang ditemukan di `common/phone.util.ts`:
1. Hapus karakter non-digit
2. Tambah `+` di depan (format E.164)
3. Hapus `@s.whatsapp.net` dari JID Baileys

```typescript
// canonicalPhone("628123456789") → "+628123456789"
// canonicalPhone("628123@s.whatsapp.net") → "+628123"
```

---

## Webhook Verification (Meta)

Meta mengirim GET request pertama untuk verifikasi:
```
GET /webhooks/meta?hub.mode=subscribe&hub.verify_token=XXX&hub.challenge=YYY
```
Server harus menjawab dengan `hub.challenge` jika token cocok.

---

## Intent Detection Pipeline

Ditemukan di `message-pipeline.service.ts`:
1. **Rule Engine** (`rule-engine.service.ts`) → coba match regex/keyword dulu
2. **OpenRouter** (jika rule tidak match)
3. **Gemini** (fallback)
4. **Gemma** (fallback terakhir)

IntentName yang ada: `produksi | penjualan | cek_stok | unknown`

---

## Keterbatasan

- Baileys bisa kena ban dari WhatsApp kapan saja
- Meta API butuh approval bisnis + biaya per pesan (conversation-based pricing)
- Rate limit Meta: 1000 pesan/detik per phone number (kelas bisnis)
- Media (gambar/dokumen) perlu didownload dulu dari URL sementara Meta (expire 5 hari)

---

## Relevansi untuk SIDIX

SIDIX `channel_adapters.py` mengadopsi:
- Dual-engine pattern (meta/baileys/none)
- Normalisasi nomor E.164
- Parse payload Meta yang sama persis
- Webhook verify helper

**File implementasi:** `apps/brain_qa/brain_qa/channel_adapters.py` → class `WAAdapter`
