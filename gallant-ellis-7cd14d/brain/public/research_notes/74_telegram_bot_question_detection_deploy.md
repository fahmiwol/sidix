# 74 — Telegram Bot: Deteksi Pertanyaan & Deploy Pipeline

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Tag:** IMPL, FIX, DECISION

---

## Apa

Perbaikan Telegram bot SIDIX (@sidixlab_bot) agar bisa:
1. Membedakan pertanyaan vs pernyataan
2. Menjawab pertanyaan via LLM (bukan hanya menyimpan ke corpus)
3. Terhubung ke brain_qa dengan benar

## Bug yang Ditemukan dan Diperbaiki

### Bug 1 — Bot selalu simpan, tidak pernah jawab
**Sebab:** `handle_text()` selalu memanggil `sidix_capture()`.
**Fix:** Tambah fungsi `_is_question()` — jika pertanyaan → `sidix_query()`, jika pernyataan → `sidix_capture()`.

### Bug 2 — Kata tanya di akhir kalimat tidak terdeteksi
**Sebab:** Check `" berapa "` butuh spasi kiri DAN kanan. "1 tambah 1 berapa" tidak punya spasi setelah "berapa".
**Fix:** Gunakan regex word-boundary `\bberapa\b`.

```python
import re as _re
for w in question_words:
    if _re.search(r'\b' + _re.escape(w) + r'\b', t):
        return True
```

### Bug 3 — API field name salah
**Sebab:** Bot mengirim `{"message": question}` tapi `ChatRequest` schema expect `{"question": question}`.
**Fix:** Update `sidix_query()` payload.

### Bug 4 — Port salah di .env
**Sebab:** `SIDIX_URL=http://127.0.0.1:8766` tapi brain_qa jalan di port `8765`.
**Fix:** `sed -i 's|SIDIX_URL=.*|SIDIX_URL=http://127.0.0.1:8765|'`

### Bug 5 — PM2 tidak load .env baru
**Sebab:** `pm2 restart` tidak reload env secara default.
**Fix:** Selalu gunakan `pm2 restart <name> --update-env`.

## Logika Deteksi Pertanyaan

```python
def _is_question(text):
    t = text.lower().strip()
    if "?" in t: return True
    
    question_words = ("apa", "siapa", "berapa", "kenapa", "bagaimana",
                      "kapan", "dimana", "bisakah", "apakah",
                      "what", "who", "how", "why", "when", "where")
    for w in question_words:
        if re.search(r'\b' + re.escape(w) + r'\b', t):
            return True
    
    # Kalimat pendek (≤6 kata) tanpa tanda baca → tanya
    if len(t.split()) <= 6 and not any(c in t for c in [".", "!", ","]):
        return True
    
    return False
```

## Deploy Pipeline

Setiap perubahan kode → deploy ke VPS:
```bash
# Di lokal:
git add . && git commit -m "..." && git push origin main

# Di VPS:
cd /tmp/sidix && git pull origin main
pm2 restart sidix-telegram --update-env
pm2 restart sidix-brain --update-env
```

## Landing Page Deploy

Landing page (`SIDIX_LANDING/index.html`) tidak di-serve langsung dari `/tmp/sidix/`.
Nginx serve dari `/www/wwwroot/sidixlab.com/`.

Deploy script: `/tmp/sidix/deploy-landing.sh`
```bash
cp /tmp/sidix/SIDIX_LANDING/index.html /www/wwwroot/sidixlab.com/index.html
```

**Selalu jalankan ini setiap ada perubahan landing page!**

## Donate Links

- Ko-fi (international): https://ko-fi.com/sidix
- Trakteer (Indonesia): https://trakteer.id/Sidix_AI
- GitHub Sponsors: https://github.com/sponsors/fahmiwol
- Telegram bot: https://t.me/sidixlab_bot

## PM2 Process List

| Name | Port | Fungsi |
|------|------|--------|
| sidix-brain | 8765 | FastAPI brain_qa |
| sidix-gateway | 8766 | Gateway/proxy |
| sidix-telegram | — | Telegram bot polling |
