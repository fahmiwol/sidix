# 124 — Waiting Room Engine: Zero-API User Retention saat Quota Habis

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa
Saat quota user habis, SIDIX tidak menampilkan pesan error kosong.
Sebaliknya, user masuk "Ruang Tunggu" interaktif — penuh aktivitas yang
**semuanya menjadi training data SIDIX** (zero-API, zero-quota consumption).

## Filosofi
```
Quota habis  →  bukan "coba lagi nanti"
             →  tapi "ayo main dulu, SIDIX belajar dari kamu"
```

User tetap engaged. SIDIX tetap belajar. Koneksi tidak terputus.

## Arsitektur

### Frontend: `SIDIX_USER_UI/src/waiting-room.ts`
- **Entry point**: `initWaitingRoom(lang, quotaInfo)` — dipanggil dari `onQuotaLimit` di main.ts
- **Satu-kali inject**: `_wrInitialized` flag mencegah HTML di-inject dua kali
- **Tab system**: Quiz | Tebak Gambar | Motivasi | Game | Tools | Gacha
- **Typewriter SIDIX**: Pesan dari backend, karakter per karakter tanpa API (delay 30ms/char)
- **Coin system**: `localStorage.sidix_gacha_coins` — earned dari quiz (+2) & image (+5)
- **Badge collection**: `localStorage.sidix_badges` — persistent across sessions

### Backend: `apps/brain_qa/brain_qa/waiting_room.py`
- **QUIZ_BANK**: 300+ soal, 9 kategori (sains, sejarah, islam, teknologi, dll)
- **QUOTE_BANK**: 150+ quotes (motivasi, islam, teknologi) — ID + EN
- **IMAGE_PROMPTS**: Wikimedia public domain images + text prompts
- **GACHA_REWARDS**: Rarity system (common 50% → legendary 1%)
- **`record_waiting_interaction()`**: Setiap jawaban → qna_recorder → SIDIX training data

### Endpoints (di `agent_serve.py`):
```
GET  /waiting-room/quiz              → 3 soal acak
GET  /waiting-room/quote             → 1 quote acak
GET  /waiting-room/image             → 1 image prompt
GET  /waiting-room/gacha/spin        → spin gacha (backend random)
GET  /waiting-room/sidix-message     → pesan typewriter SIDIX
GET  /waiting-room/tools             → daftar tools yang bisa dicoba
POST /waiting-room/learn             → record interaksi user → training data
GET  /waiting-room/stats             → stats waiting room hari ini
```

## Flow Lengkap

```
User send message
  ↓
Backend: check_quota()
  ↓ quota habis
SSE event: {type: "quota_limit", data: {...}}
  ↓
main.ts: onQuotaLimit → initWaitingRoom(LANG, info)
  ↓
waiting-room.ts: inject modal HTML → show modal
  → _startTypewriter(): fetch pesan SIDIX, ketik pelan-pelan
  → _loadQuiz(): fetch 3 soal, render kartu
    → user jawab → +2 koin → POST /waiting-room/learn (→ SIDIX belajar)
  → tab Gacha: spin dengan koin → reward + badge
  → tab Game: iframe bottle-flip.html (zero API, zero quota)
  → tab Tools: grid tool yang bisa dicoba user
```

## Coin & Gacha Economy
```
Earn:
  Quiz benar       → +2 koin
  Image describe   → +5 koin (lebih susah, lebih berharga)

Spend:
  Gacha spin       → -1 koin per spin

Rewards:
  Common (50%)     → "Semangat Belajar" badge
  Uncommon (30%)   → "Kurator Cerdas" badge
  Rare (15%)       → "Penjelajah Ilmu" badge
  Epic (4%)        → "Scholar SIDIX" badge + bonus +10 koin
  Legendary (1%)   → "Maestro Mighan" badge + bonus +50 koin + quota top-up hint
```

## Kenapa Semua Interaksi Jadi Training Data?
- Quiz: soal → jawaban user (benar/salah) → fakta penjelasan → konteks lengkap
- Image describe: prompt → deskripsi user → perspektif manusia tentang dunia visual
- Gacha: tidak ada training, tapi memotivasi user untuk bermain quiz lebih banyak

Format yang direkam ke qna_recorder:
```python
record_qna(
    question = f"[{interaction_type}] {question}",
    answer   = f"User: {user_answer} | Correct: {correct_answer}",
    session_id = f"waiting_{session_id}",
    model    = "waiting_room_human",
    quality  = 3 if user_benar else 2,
)
```

## Game: Bottle Flip
- File: `SIDIX_USER_UI/public/games/bottle-flip.html`
- Zero API, zero quota, pure browser game
- Ditampilkan via `<iframe>` di tab Game
- Source: lokal (sudah di-copy dari `D:\game\flip\files\bottle-flip-v2.1.html`)

## Integrasi ke main.ts
```typescript
// Sebelum:
onQuotaLimit: (info) => {
  showQuotaOverlay(info);  // overlay statis biasa
}

// Sesudah:
onQuotaLimit: (info) => {
  initWaitingRoom(LANG, info);  // waiting room interaktif
}
```

## Keterbatasan
- `_wrInitialized` flag artinya HTML hanya di-inject sekali per session — jika user reload, waiting room di-reinit ulang (OK, normal behavior)
- Gacha coins hilang jika localStorage dibersihkan (by design — tidak perlu server-side)
- Quiz bank di-serve dari Python memory (tidak perlu DB) — cukup untuk awal
- Image prompts Wikimedia: jika URL rusak, fallback ke text-only prompt
- Waiting room tidak mengurangi quota (by design) — semua zero-cost

## File
- `SIDIX_USER_UI/src/waiting-room.ts` — frontend module
- `SIDIX_USER_UI/src/main.ts` — `initWaitingRoom` dipanggil dari `onQuotaLimit`
- `apps/brain_qa/brain_qa/waiting_room.py` — backend data + recorder
- `apps/brain_qa/brain_qa/agent_serve.py` — endpoint `/waiting-room/*`
- `SIDIX_USER_UI/public/games/bottle-flip.html` — game lokal
