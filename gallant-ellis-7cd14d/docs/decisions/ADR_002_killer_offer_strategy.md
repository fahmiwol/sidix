# ADR-002 — Killer Offer Strategy untuk Beta Launch

**Status:** Approved (user directive 2026-04-20)
**Konteks:** SIDIX butuh killer differentiator supaya user mau coba di awal, bukan sekadar "AI lain".

---

## User Directive (verbatim)

> "Kita perlu killer agent AI, atau killer offers, yang biar jadi alesan orang pake SIDIX di awal:
> - Gratis generate gambar, hasilnya relevan
> - Bisa dipake buat bantu kerjaan sehari-hari agency kreatif (bikin konten, dll)
> - Bisa bikin gambar-to-video
> - Punya macam-macam skill gambar sekelas GPT, tanpa perlu nulis prompt panjang"

---

## Strategic Keputusan

### Killer Offer #1: GRATIS image gen high-quality
- Tagline: **"SDXL profesional, gratis selamanya untuk kreatif Indonesia"**
- Unfair advantage: kompetitor (ChatGPT Plus, Midjourney) bayar USD 20/bulan. SIDIX = Rp 0.
- Infrastructure cost ditanggung SIDIX (laptop GPU + ngrok free tier, nanti RunPod subsidi).

### Killer Offer #2: Prompt Pendek → Output Bagus (Auto-enhance)
- User agency kreatif ga punya waktu nulis prompt 200-kata.
- SIDIX otomatis **enhance prompt** pendek user → prompt SDXL detail.
- Contoh:
  - User: "konten ramadhan masjid"
  - SIDIX enhance: "serene mosque at iftar time, warm golden hour light, Arabic calligraphy architecture, crescent moon visible, inviting spiritual atmosphere, professional photography, 4k detail, cinematic composition"
- Result: hasil gambar langsung production-ready tanpa user perlu belajar prompt engineering.

### Killer Offer #3: Agency Creative Kit
- Template prompt untuk use case sehari-hari:
  - **Konten IG feed** (1:1 square, aesthetic)
  - **Konten Story/Reels cover** (9:16 vertical)
  - **Thumbnail YouTube** (16:9)
  - **Poster event** (A4 vertical)
  - **Product shot** (1:1, studio lighting)
- User pilih kategori → SIDIX auto-apply template + dimensi + style.

### Killer Offer #4: Image-to-Video (Future Sprint 5)
- Setelah image gen stabil, tambah text-to-video atau image-to-video.
- Open source options: AnimateDiff, CogVideoX, Stable Video Diffusion.
- Butuh GPU lebih besar (cloud RunPod A100 ~Rp 50k/run).

### Killer Offer #5: Multi-Skill Gambar (Future Sprint 4-5)
Fitur setara GPT-4o image tools:
- **Style transfer** (foto user → jadi anime/lukisan)
- **Inpainting** (edit bagian gambar — e.g. ganti background)
- **Outpainting** (extend gambar ke luar frame)
- **Upscale** (low-res → high-res)
- **Remove background** (rembg self-host)
- **Face restoration** (CodeFormer self-host)
- **Character consistency** (IP-Adapter untuk karakter tetap sama lintas gambar)

Semua open-source, self-hostable. **Tidak ada di ChatGPT free tier.**

---

## Prioritisasi Execution

| Offer | Effort | Impact | Timeline |
|-------|--------|--------|----------|
| #1 Gratis image gen | ✅ DONE | 🔥🔥🔥 | Live sekarang |
| #2 Auto-enhance prompt | 1-2 hari | 🔥🔥🔥 | **This week** |
| #3 Creative Kit templates | 3-5 hari | 🔥🔥 | **Next week** |
| #4 Image-to-Video | 3-4 minggu | 🔥🔥 | Sprint 5 |
| #5 Multi-skill (inpaint/style/upscale) | 4-6 minggu | 🔥🔥🔥 | Sprint 5-6 |

**Start:** #2 Auto-enhance (quick win, immediate UX upgrade).

---

## Narasi Marketing (untuk landing page + Threads)

**"SIDIX — AI agent asli Indonesia. Gratis. Bisa gambar. Bisa ngerti Nusantara."**

Pain points kompetitor:
- ❌ ChatGPT Plus: $20/bulan, image limited
- ❌ Midjourney: $10/bulan, belajar prompt rumit
- ❌ Canva Magic: $15/bulan, kualitas limited
- ❌ Generik, ga paham konteks kultural Nusantara

Value prop SIDIX:
- ✅ Gratis selamanya (core tier)
- ✅ Prompt pendek → hasil pro (auto-enhance)
- ✅ Template agency (IG/reels/poster siap pakai)
- ✅ Paham masjid demak, batik parang, rumah gadang, gudeg
- ✅ Epistemic transparan (sanad chain di tiap jawaban)

---

## Self-Train Roadmap Tetap (per ADR draft sebelumnya)

Killer offer != ganti autonomy. Self-train tetap critical tapi **setelah beta validated**.

Urutan eksekusi:
1. **Sekarang (Sprint 3 akhir):** Killer offer #2 auto-enhance
2. **Minggu depan (Sprint 4):** Creative Kit templates + Fase 1 data pipeline self-train
3. **Sprint 5 (bulan depan):** Multi-skill gambar (inpaint/style/upscale) + Fase 2 auto-retrain Kaggle
4. **Sprint 6-7:** Image-to-video + Fase 3 A/B test adapter

Rationale: **breadth features dulu (attract user) → depth autonomy (retain + improve).**

---

## Success Metrics (track weekly)

- Daily Active Users (target: 100 dalam 1 bulan beta)
- Image gen per user per minggu (target: >5 = engaged)
- Retention 7-day (target: >30%)
- Threads mention + share rate (viral coefficient)

Kalau metric di bawah target → prompt engineering narasi + quality model, bukan tambah fitur baru.

---

**Pembuat:** Claude (coordinator), user Fahmi (direction)
**Review:** weekly Sprint retrospective
