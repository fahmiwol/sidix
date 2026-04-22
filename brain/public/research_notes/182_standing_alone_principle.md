---
id: 182
title: Standing Alone Principle — SIDIX Harus Mandiri, Bukan Bergantung AI Eksternal
tags: [architecture, standing-alone, multi_llm_router, ollama, self-hosting, independence]
date: 2026-04-21
---

# Standing Alone Principle — SIDIX Harus Mandiri

**[FACT]** — Sumber: arsitektur `multi_llm_router.py`, keputusan sesi 2026-04-21, visi NORTH_STAR.md.

---

## Masalah yang Ditemukan

Pada sesi 2026-04-21, ditemukan bahwa SIDIX memiliki **silent fallback** ke AI eksternal (Groq, Gemini) ketika Ollama crash akibat OOM (Out of Memory). Ini terjadi karena:

1. `multi_llm_router.py` memiliki hierarki: `Local Ollama → Groq → Gemini → Anthropic → Mock`
2. `GROQ_API_KEY` dan `GEMINI_API_KEY` aktif di VPS `.env`
3. Ketika Ollama runner crash → router otomatis turun ke Groq → SIDIX menjawab via LLM orang lain
4. User tidak tahu ini terjadi → melanggar prinsip transparansi dan kemandirian

**Dampak**: setiap kali VPS kekurangan RAM (7.8GB tanpa swap, Ollama butuh 4.7GB untuk sidix-lora:latest), SIDIX diam-diam menggunakan Groq/Gemini tanpa sepengetahuan user.

---

## Kenapa Ini Masalah Fundamental

**Standing Alone** adalah salah satu pilar inti SIDIX (lihat `docs/NORTH_STAR.md` + `docs/SIDIX_BIBLE.md`):

- SIDIX harus bisa berjalan TANPA internet, tanpa API eksternal, tanpa bergantung perusahaan lain
- Jika Groq/Gemini down, API key expire, atau kebijakan berubah → SIDIX tidak boleh terpengaruh
- Akurasi dan kepribadian SIDIX harus 100% dari model SIDIX sendiri (Qwen2.5-7B + LoRA adapter)
- Menggunakan LLM orang lain = hasil tidak bisa diklaim sebagai SIDIX, tidak bisa di-audit sanadnya

**Analogi**: jika pesawat mengklaim bisa terbang sendiri tapi diam-diam mengandalkan remote pilot orang lain saat ada gangguan — itu bukan pesawat otonom.

---

## Solusi yang Diimplementasikan (2026-04-21)

### 1. Nonaktifkan GROQ_API_KEY dan GEMINI_API_KEY di VPS `.env`
```bash
# Sebelum:
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...

# Sesudah:
# DISABLED_STANDALONE: GROQ_API_KEY=gsk_...
# DISABLED_STANDALONE: GEMINI_API_KEY=AIzaSy...
```

Sekarang jika Ollama crash → router mencoba Groq (gagal, no key) → Gemini (gagal) → Anthropic (jika aktif) → Mock. Mock artinya SIDIX return pesan "model tidak tersedia" — **jujur**, bukan diam-diam pakai LLM lain.

### 2. Tambah Swap 4GB untuk Cegah OOM
```bash
fallocate -l 4G /swapfile && chmod 600 /swapfile
mkswap /swapfile && swapon /swapfile
echo "/swapfile none swap sw 0 0" >> /etc/fstab
```

**Kenapa**: Ollama butuh 4.7GB untuk `sidix-lora:latest` (GGUF Q4_K_M quantized). VPS 7.8GB RAM juga harus menjalankan sidix-brain (FastAPI), 5+ PM2 processes lain, nginx, dan OS. Tanpa swap → OOM → Ollama crash → router fallback. Dengan 4GB swap → Ollama bisa survive memory pressure walau lebih lambat.

### 3. Hapus Model Duplikat `qwen2.5:7b`
```bash
ollama rm qwen2.5:7b
```

`qwen2.5:7b` (4.7GB) adalah base model tanpa LoRA adapter SIDIX. `sidix-lora:latest` sudah include base + adapter. Menyimpan keduanya = buang 4.7GB disk + RAM percuma. Setelah dihapus, Ollama hanya menyimpan: `sidix-lora:latest` (4.7GB) + `qwen2.5:1.5b` (986MB, untuk lightweight tasks).

---

## State VPS Setelah Fix

```
RAM: 7.8GB total, 5.0GB free, 1.8GB used
Swap: 4.0GB total, 0B used (baru)
Disk (Ollama models): sidix-lora:latest (4.7GB) + qwen2.5:1.5b (986MB) — hemat 4.7GB
LLM Router: Local Ollama → Mock (Groq/Gemini dinonaktifkan)
Health: model_mode=sidix_local, model_ready=true
```

---

## Implikasi Arsitektur ke Depan

### Yang BOLEH di multi_llm_router
- `Local Ollama → sidix-lora:latest` — ini model SIDIX sendiri ✅
- `Mock fallback` — jujur bilang tidak bisa, bukan tipu dengan LLM lain ✅
- `qwen2.5:1.5b` via Ollama — masih model terbuka (bukan API) ✅

### Yang TIDAK BOLEH (permanent rule)
- `GROQ_API_KEY` aktif di production → ❌ silent fallback ke LLM orang lain
- `GEMINI_API_KEY` aktif di production → ❌ idem
- `ANTHROPIC_API_KEY` untuk inference → ❌ idem
- Pengecualian: API key boleh aktif untuk **tools** non-inference (misal: Google Search API untuk web_search tool) — tapi BUKAN untuk LLM inference backbone

### Pengecualian yang Valid
- `ANTHROPIC_API_KEY` boleh aktif kalau hanya dipakai untuk `claude-code` CLI (developer tool), bukan untuk inference pipeline SIDIX
- External API boleh dipakai di tool calls (web_fetch, web_search) — tapi hasil tetap diproses oleh SIDIX model sendiri

---

## Keterbatasan Saat Ini

- `internal_mentor_pool: {ready: true, redundancy_level: 1}` masih muncul di `/health` — perlu audit apakah Anthropic key masih aktif sebagai mentor
- Jika Ollama runner crash DAN swap tidak cukup, SIDIX akan return error (mock response) — ini **benar secara prinsip** tapi perlu UX yang baik (pesan error yang informatif ke user)
- Monitor OOM lebih lanjut: jika sidix-lora:latest + sidix-brain + OS melebihi 7.8GB + 4GB swap → perlu upgrade RAM VPS atau quantize model lebih agresif (Q2_K)

---

## Kenapa Ini Berbeda dari "Ollama adalah External"

Ollama adalah **serving layer lokal**, bukan provider API eksternal:
- Berjalan di VPS SIDIX sendiri (`localhost:11434`)
- Model yang dijalankan adalah model SIDIX sendiri (`sidix-lora:latest` = Qwen2.5-7B + LoRA adapter SIDIX)
- Tidak ada data keluar ke server pihak ketiga
- Berbeda fundamental dengan Groq/Gemini yang:
  - Berjalan di infrastruktur perusahaan lain
  - Menggunakan model yang dikontrol pihak lain
  - Data user dikirim ke server eksternal
  - Subject to API policy changes, rate limits, costs

**Analoginya**: Ollama = mesin lokal. Groq/Gemini = kirim dokumen ke kantor lain untuk diproses.
