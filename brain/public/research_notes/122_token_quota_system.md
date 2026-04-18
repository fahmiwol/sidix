# 122 — Token Quota System: Monetisasi & Sustainability SIDIX

## Apa
Sistem pembatasan penggunaan harian berbasis tier untuk menjaga sustainability biaya API.
Setiap user punya limit pesan per hari, dengan opsi upgrade.

## Mengapa
- Anthropic API bukan gratis sepenuhnya — perlu kontrol agar tidak boros
- User yang mau lebih bisa top up → revenue sederhana untuk keberlanjutan proyek
- Tier berbeda = model berbeda → hemat biaya secara proporsional

## Arsitektur

### Tier System
```
guest     → 3 pesan/hari   (IP-based, tanpa login)       → Haiku
free      → 10 pesan/hari  (Supabase user_id)             → Haiku
sponsored → 100 pesan/hari (top up via Trakteer/Saweria)  → Sonnet
admin     → 9999 (unlimited)                               → Sonnet
```

### Flow Request
```
Request → check_quota(user_id, ip) → ok? → proses chat
                                   → limit! → return quota_limit event → UI overlay
                                   
Setelah selesai → record_usage(tokens_in, tokens_out, model, session_id)
Response menyertakan: {used, limit, remaining, tier}
```

### Storage
- **Harian**: `.data/quota/quota_YYYY-MM-DD.json`
- **Key per user**: `user:{user_id}` atau `ip:{sha256[:16]}`  
- **Sponsored list**: `.data/sponsored_users.json`
- Untuk prod scale → ganti ke Supabase `usage_logs` table

## File
- `apps/brain_qa/brain_qa/token_quota.py` — core quota engine
- Endpoints: `GET /quota/status`, `GET /quota/stats`, `POST /quota/sponsor/{user_id}`

## SSE Event: quota_limit
```json
{
  "type": "quota_limit",
  "tier": "guest",
  "used": 3,
  "limit": 3,
  "remaining": 0,
  "reset_at": "2026-04-19T00:00:00Z",
  "topup_url": "https://trakteer.id/sidixlab",
  "message": "Kamu sudah menggunakan semua 3 pesan gratis..."
}
```

## UI Response
- Quota badge di header: `3/10` (tersisa/limit)
- Warna: hijau → kuning (≤2) → merah (0)
- Overlay muncul saat limit: pilihan Tunggu / Login (+10/hari) / Top Up (100/hari + Sonnet)
- Tombol: Top Up via Trakteer, Hubungi Admin WA

## Monetisasi Model
- **Free**: 10 pesan/hari → cukup untuk preview
- **Top Up**: manual (Trakteer) → admin konfirmasi → `/quota/sponsor/{user_id}`
- **Futur**: Mighanomic coin → automated

## Keterbatasan
- Storage lokal (JSON) → tidak sync antar multiple server instances
- Manual verification → perlu automasi dengan webhook Trakteer/Midtrans
- IP-based untuk guest → tidak sempurna (VPN bypass)
