# Next Tasks — 2026-04-20 (Handoff ke sesi berikut)

**Tanggal:** 2026-04-20
**Status beta:** image gen LIVE (auto-enhance, 97s per 512×512, gratis).
**User directive:** optimasi visibility + launch announcement.

---

## 🎯 Task 1: Optimasi GitHub Repo (public-facing)

**Repo:** `github.com/fahmiwol/sidix`

### 1.1 README.md Rewrite
Update README jadi killer landing page format:
- **Hero:** "SIDIX — AI Agent Asli Indonesia. Gratis. Bisa gambar. Paham Nusantara."
- **Badges:** License (MIT/Apache), Stars, Build status, Python 3.12+, CUDA 12.1
- **Value prop bullet (pain kompetitor):**
  - ❌ ChatGPT $20/bulan image limited
  - ❌ Midjourney $10/bulan prompt rumit
  - ❌ Canva $15/bulan generik
  - ✅ SIDIX gratis + paham Nusantara
- **Screenshot demo:** hasil image gen masjid/batik/kuliner
- **Quick start:** 3 langkah (clone + setup + run)
- **Architecture diagram:** 3-layer (LLM + RAG + Growth Loop) + Brain/Hands/Memory
- **Killer offers list** (link ke ADR-002)
- **Differensiator:** Epistemic transparency + Standing-alone + Cultural specialization
- **Roadmap tabel:** Baby (Q1-Q2) / Child (Q3) / Adolescent (Q4-Q1'27) / Adult (Q2'27+)
- **Contribute section:** link landing page #contributor

### 1.2 Repo Metadata
- Description: "AI agent asli Indonesia — gratis generate gambar, paham Nusantara, epistemic transparent"
- Topics: `ai-agent`, `indonesia`, `islamic-ai`, `image-generation`, `sdxl`, `self-hostable`, `rag`, `qwen`, `fastapi`
- Website: https://sidixlab.com
- Social preview image: buat branded 1280×640 pakai SIDIX logo + tagline

### 1.3 Files Tambahan
- `SECURITY.md` — disclosure policy (sudah ada? verify)
- `CONTRIBUTING.md` — cara ikut ngoding + research note
- `CODE_OF_CONDUCT.md` — rules interaksi
- `docs/assets/demo-image-gen.png` — sample output

### 1.4 GitHub Features Enable
- **Issues template:** Bug report, Feature request, Research note proposal
- **Discussions tab:** enable buat Q&A komunitas
- **Sponsors:** setup Trakteer/Saweria link di `.github/FUNDING.yml`
- **Releases:** tag `v0.1.0-beta` sekarang + changelog

**Estimasi effort:** 3-5 jam.

---

## 🎯 Task 2: Update Landing Page (sidixlab.com)

**Path VPS:** `/www/wwwroot/sidixlab.com/`
**Source repo:** `SIDIX_LANDING/`

### 2.1 Hero Section Update
- Headline: **"AI Agent Asli Indonesia. Gratis. Bisa Gambar."**
- Sub: "Bantu kerjaan kreatif harian — konten IG, poster, visual. Paham Nusantara (masjid, batik, candi, kuliner). Gratis selamanya."
- CTA primary: **"Coba Gratis"** → app.sidixlab.com
- CTA secondary: "Lihat Roadmap" → GitHub

### 2.2 Section Baru: "Dibuat untuk Kreatif"
3 card use case:
1. **Agency Creative** — "Bikin konten IG Ramadhan? Tulis 'ramadhan masjid golden hour' → SIDIX render dalam 90 detik."
2. **Content Creator** — "Butuh thumbnail YouTube? SIDIX bikin versi berbeda tanpa prompt panjang."
3. **UMKM / Bisnis Lokal** — "Product shot rendang, poster event, visual posting — semua gratis."

### 2.3 Section: "Demo Live"
Embed hasil generate (3-5 sample):
- Masjid Demak subuh
- Batik Parang close-up
- Pantai Bali sunset
- Rendang food photography
- Borobudur misty morning

Tiap sample tampil: **prompt user** → **hasil gambar** (before/after auto-enhance).

### 2.4 Section: "Killer Differentiators"
- ✅ **Gratis selamanya** (core tier)
- ✅ **Prompt pendek → hasil pro** (auto-enhance)
- ✅ **Paham Nusantara** (masjid demak, batik parang, rumah gadang, gudeg)
- ✅ **Epistemic transparent** (sanad chain + 4-label)
- ✅ **Self-hostable** (open source, tidak vendor lock)

### 2.5 Section: "Progress Live"
Tampil counter dari `/health`:
- Tools aktif: 19
- Corpus docs: 1182
- Model: Qwen2.5-7B + LoRA SIDIX
- GPU: RTX 3060 Laptop (komunitas bayar server nanti via Trakteer)

### 2.6 Section: Contributor (pindah dari app ke landing)
- "Gabung Kontributor" CTA dari app.sidixlab.com redirect ke `sidixlab.com#contributor`
- Form sederhana: nama + email + skill (riset / coding / design / translator / community)

### 2.7 SEO + Social
- Meta title: "SIDIX - AI Agent Indonesia Gratis Bisa Gambar"
- OG image branded 1200×630
- Twitter card
- JSON-LD schema: Organization + Product
- Sitemap + robots.txt update

**Estimasi effort:** 4-6 jam.

**Deploy:** `git pull` di VPS + sync ke `/www/wwwroot/sidixlab.com/` (remember: landing static, bukan PM2).

---

## 🎯 Task 3: Posting Threads — Beta Launch Announcement

**Platform:** Threads (`@sidixlab`), nanti scale ke X, LinkedIn, IG.

### 3.1 Launch Post (main)
**Format:** hook + demo + CTA

**Draft:**
```
Baru aja rilis SIDIX beta — AI agent asli Indonesia.

Gratis generate gambar profesional, paham konteks Nusantara.

Contoh: tulis "bikin gambar masjid demak subuh" → 90 detik nanti
dapat hasil siap posting.

[ATTACH 4 GAMBAR]
- Masjid Demak subuh
- Batik Parang detail
- Borobudur misty morning
- Rendang food shot

Coba gratis → app.sidixlab.com
Source + roadmap → github.com/fahmiwol/sidix

Dibikin solo + 3 AI agent (Claude, Cursor, Antigravity) buat bantu
coding. Masih beta, feedback welcome 🙏

#AI #Indonesia #IndieDev #OpenSource #GenerativeAI
```

### 3.2 Threads Series (5 post, schedule 1/hari)
1. **Hook:** Launch announcement (main post above)
2. **Behind the scene:** "Kenapa bikin AI sendiri? ChatGPT mahal, Midjourney belajar prompt rumit, semua generik ga paham kita."
3. **Demo deep:** Before/after auto-enhance — user prompt 3 kata vs hasil SDXL
4. **Differensiator:** "Yang beda dari SIDIX: epistemic transparency (sanad chain), paham Nusantara, gratis selamanya, self-hostable."
5. **Roadmap + Ajak kontribusi:** "Beta sekarang. Q3 tambah vision + audio. Q4 self-evolving. Butuh kontributor riset + dev + designer."

### 3.3 Asset Prepare
- 4-8 sample image hasil SIDIX (re-generate dengan prompt quality)
- Screen recording 60 detik demo (Loom/OBS)
- Logo SIDIX 1200×630 branded
- GIF before/after prompt enhance

### 3.4 Tracking
- Monitor engagement rate + viral coefficient
- Reply ke setiap komentar dalam 1 jam (manual atau SIDIX auto-reply tier)
- Tag 10 akun AI Indonesia + kreator untuk signal boost

**Estimasi effort:** 2-3 jam prepare + 15 menit/hari posting.

---

## 📊 Success Metrics Post-Launch

Track harian di `/metrics` dashboard:

| Metric | Target 1 minggu | Target 1 bulan |
|--------|-----------------|----------------|
| Threads impression | 10K | 100K |
| Landing page visit | 500 | 5K |
| GitHub stars | 20 | 200 |
| Signup app | 50 | 500 |
| Daily Active Users | 10 | 100 |
| Image gen/day | 100 | 1000 |
| Retention D7 | 20% | 30% |

Kalau di bawah target → iterate narasi + demo, jangan nambah fitur.

---

## 🔄 Urutan Eksekusi yang Disarankan

**Hari 1 (sore/malam):** Task 2 landing page — karena landing page = pintu masuk, perlu updated dulu sebelum drive traffic.

**Hari 2 pagi:** Task 1 GitHub README — untuk developer audience.

**Hari 2 siang:** Task 3 prepare asset Threads (generate 8 sample image berkualitas).

**Hari 2 sore:** Post Threads #1 launch.

**Hari 3-7:** Post Threads #2-5 (1 per hari).

---

## 🛡️ Pre-Launch Checklist Wajib Cek

- [ ] Laptop SDXL server stabil 24 jam (uji 10 request berurutan)
- [ ] ngrok URL tidak expired
- [ ] VPS brain response < 5s untuk text (non-image)
- [ ] Rate limit guest naik sementara 30/day (sudah done)
- [ ] `/generated/{hash}.png` endpoint serve publik OK
- [ ] Frontend UI image render + loading indicator live
- [ ] Laptop jangan sleep (power plan → never sleep saat live)
- [ ] Home/office WiFi stabil (ngrok butuh koneksi)

---

**Dibuat:** 2026-04-20 oleh Claude
**Untuk:** sesi berikutnya (kemungkinan Fahmi + Claude lanjut)
