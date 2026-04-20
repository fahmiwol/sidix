---
sanad_tier: primer
tags: [directive, creative-agent, roadmap, verticals, strategic]
date: 2026-04-20
---

# 168 — SIDIX Creative Verticals: 8 Domain yang Harus Dikuasai

## Konteks

[FACT] User directive 2026-04-20 (verbatim): "SIDIX harus jago di advertising, creative, seni, design, video, digital marketing, sosial media marketing, content marketing, content creation, automatic content creation, logo, foto, 3D maker, all about 3D."

[FACT] **KRITIKAL principle:** "SIDIX bukan directory atau search engine, SIDIX AI AGENT. Jangan nampilin dari corpus." — SIDIX WAJIB bertindak (generate/execute), bukan sekadar return search result. ReAct + generative layer primary, RAG tool untuk enrich konteks — bukan output utama.

---

## 🔥 8 Creative Vertical Domains (dari user)

### 1. Konten & Media Production
**Skills:** Copywriting, social media content, script video/reels/TikTok, desain visual sederhana

**AI Agent Targets:**
- **AI Content Planner** — auto ide + kalender konten 7/14/30 hari
- **AI Copywriter** — caption, headline, CTA (hook formulas: AIDA/PAS/FAB)
- **AI Script Generator** — video marketing 30s/60s/3min, hook-pain-solution-CTA

**Kenapa cocok:** pattern-based (hook/CTA/storytelling), data melimpah di corpus, demand tinggi.

**SIDIX current state:** ❌ belum ada agent khusus. MIGHAN persona kasar untuk copy. **Gap: need dedicated tools.**

---

### 2. Desain Grafis & Branding
**Skills:** Logo, feed IG, brand guideline, thumbnail

**AI Agent Targets:**
- **AI Brand Builder** — generate logo + palette + tone (Aaker/Sinek/Neumeier framework dari note 167)
- **AI Design Assistant** — auto layout feed/ads (grid 3-col/9-post cohesive)
- **AI Thumbnail Generator** — YT/Instagram cover with hook text overlay

**Value prop untuk agency user:** "Branding kit dalam 1 klik" — logo + palette + tipografi + voice tone + 5 mockup.

**SIDIX current state:** 🟡 image gen live (text_to_image). **Gap: logo vector (SVG), layout composer, brand guideline compiler.**

---

### 3. Video & Editing
**Skills:** Video ads, editing reels, subtitle, storyboard

**AI Agent Targets:**
- **AI Video Editor** — cut, subtitle (Whisper ASR), highlight detection
- **AI Storyboard Generator** — 6-12 frame storyboard dari script + SDXL image gen
- **AI Hook Finder** — analyze existing video, potong viral segment

**SIDIX current state:** ❌ belum ada video capability. **Gap: ffmpeg integration, Whisper self-host, Stable Video Diffusion (nanti).**

---

### 4. Marketing & Campaign Strategy
**Skills:** Campaign planning, funnel, ads strategy

**AI Agent Targets:**
- **AI Campaign Strategist** — brief → objective → audience → channel mix → timeline
- **AI Ads Generator** — FB/Google/TikTok ad copy + image var 3-5
- **AI Funnel Builder** — awareness → consideration → conversion → retention

**User note:** "ini powerful banget buat lo (agency billboard + campaign), bisa jadi **core product**."

**SIDIX current state:** 🟡 parsial via orchestration_plan tool. **Gap: dedicated campaign tool dengan framework AARRR/RACE.**

---

### 5. Produk & E-commerce Creative
**Skills:** Foto produk, deskripsi produk, packaging concept

**AI Agent Targets:**
- **AI Product Description Generator** — feature→benefit→emotion copy (amazon style + marketplace ID)
- **AI Product Photoshoot** — mockup + scene (SDXL + rembg + compositing)
- **AI Packaging Designer** — 3D render kotak/botol dengan desain

**SIDIX current state:** 🟡 image gen bisa foto produk dasar. **Gap: inpaint/background swap, 3D mockup, SEO-optimized copy.**

---

### 6. Entertainment & Character Creation
**Skills:** Maskot, karakter brand, story IP

**AI Agent Targets:**
- **AI Character Builder** — visual + personality + lore + sheet expressions
- **AI Story Generator** — dunia gaya game/web3 (nyambung ke Mighantect 3D concept)

**User note:** "ini nyambung ke project lo yang kayak Gather Town style."

**SIDIX current state:** ❌ belum ada. **Gap: character consistency (IP-Adapter), lore builder, expression sheet generator.**

---

### 7. Voice & Audio Creative
**Skills:** Voice over, podcast, jingle

**AI Agent Targets:**
- **AI Voice Narrator** — text → TTS multi-voice (Piper self-host)
- **AI Podcast Generator** — topic → script → TTS → mix dengan intro/outro
- **AI Voice Cloning** — 1 sample audio → TTS dengan suara itu (Coqui XTTS)

**SIDIX current state:** ❌ audio_capability.py stub ada. **Gap: wire jadi tool, install Piper/Whisper.**

---

### 8. Creative Writing & Storytelling
**Skills:** Artikel, novel, story brand

**AI Agent Targets:**
- **AI Story Writer** — 3-act structure, character arc, conflict escalation
- **AI Brand Story Generator** — founder story + origin + mission narrative
- **AI Script Drama/Series** — episodic structure, cliffhanger pattern

**SIDIX current state:** 🟡 generative LLM bisa draft kasar. **Gap: framework-based (Save the Cat / Hero Journey), long-form structure.**

---

## ⚙️ Framework Konversi Skill → Agent (Pattern Universal)

Dari user:
```
1. Ambil skill kreatif
   ↓
2. Breakdown jadi step (riset → ide → copy → visual → posting)
   ↓
3. Automate tiap step pakai AI
   ↓
= AI Agent
```

**Implementasi SIDIX:**
- Tiap vertical punya **pipeline modular** (step functions)
- Step bisa dipakai lintas vertical (research step sama di content planner & campaign strategist)
- Orchestrator otomatis pilih pipeline sesuai intent user

---

## 🗺️ Priority Matrix (Impact vs Effort)

| Vertical | Impact | Effort | Priority | Target Sprint |
|----------|--------|--------|----------|---------------|
| 1 Konten (copy + planner) | 🔥🔥🔥 | Low (LLM-only) | **P0** | Sprint 4 |
| 2 Desain (logo/brand/thumbnail) | 🔥🔥🔥 | Medium (image gen) | **P0** | Sprint 4-5 |
| 4 Campaign Strategy | 🔥🔥🔥 | Low (LLM + template) | **P0** | Sprint 4 |
| 5 Product Creative | 🔥🔥 | Medium (image + copy) | **P1** | Sprint 5 |
| 8 Creative Writing | 🔥🔥 | Low (LLM + framework) | **P1** | Sprint 5 |
| 6 Character/IP | 🔥🔥 | Medium-High (IP-Adapter) | **P2** | Sprint 6 |
| 7 Voice/Audio | 🔥 | Medium (Piper+Whisper) | **P2** | Sprint 6 |
| 3 Video | 🔥🔥 | High (ffmpeg+SVD) | **P3** | Sprint 7+ |

**Quick wins (Sprint 4, 2 minggu):** Content Planner + Copywriter + Campaign Strategist + Brand Builder MVP.

**Killer moment (Sprint 5):** Agency Kit satu-klik (brief → brand + 5 konten + campaign plan + ad copy).

---

## 🚫 Anti-Pattern (WAJIB DIHINDARI)

[OPINION strongly held by user directive]:
- ❌ SIDIX return "hasil search corpus" untuk query kreatif → SIDIX BUKAN search engine
- ❌ SIDIX balikin "lihat note X" tanpa eksekusi → SIDIX bukan directory
- ❌ Jawaban dimulai "[KONTEKS DARI KNOWLEDGE BASE SIDIX]" untuk query kreatif

[FACT] Expected behavior:
- ✅ User minta copy IG → SIDIX GENERATE 3-5 varian caption siap post
- ✅ User minta logo → SIDIX GENERATE image file + palette
- ✅ User minta campaign plan → SIDIX GENERATE markdown brief + timeline
- ✅ Corpus/RAG dipakai INTERNAL untuk enrich framework knowledge, tidak di-show mentah

---

## 📐 Arsitektur Tool yang Diusulkan

```
apps/brain_qa/brain_qa/creative/
├── __init__.py
├── content_planner.py       # AI Content Planner
├── copywriter.py            # AI Copywriter (caption/headline/CTA)
├── script_generator.py      # AI Script video
├── brand_builder.py         # AI Brand Kit (logo+palette+tone)
├── thumbnail_generator.py   # AI YT/IG thumbnail
├── campaign_strategist.py   # AI Campaign Planner
├── ads_generator.py         # FB/Google/TikTok ads
├── product_description.py   # E-commerce copy
├── product_photoshoot.py    # Mockup + scene
├── character_builder.py     # Maskot/karakter
├── story_writer.py          # Novel/script/article
└── voice_narrator.py        # TTS wrapper
```

Tiap file punya:
- `generate()` — main API yang return structured output
- Framework reference (Aaker/Sinek/AIDA/PAS/Save-the-Cat/etc)
- Format template (JSON schema)
- Integration dengan image_gen atau TTS sesuai kebutuhan

---

## 🎯 Next Concrete Actions (urutan eksekusi)

**Sprint 4 Week 1:**
1. Build `copywriter.py` — 3 formula (AIDA, PAS, FAB), 3 output per call (caption IG, thread X, hook TikTok)
2. Build `content_planner.py` — input: niche + durasi → output: kalender 7/14 hari
3. Register sebagai tool: `generate_copy`, `plan_content_calendar`

**Sprint 4 Week 2:**
4. Build `campaign_strategist.py` — brief → strategi (AARRR funnel + channel mix)
5. Build `brand_builder.py` — name/niche → brand kit markdown + logo prompt + palette hex
6. Register tools + UI card di frontend

**Sprint 5:** vertical #5 (e-commerce), #8 (writing), finalize Agency Kit one-click.

---

## 🧠 Prinsip Desain Tool Kreatif

Dari BG Maker + Mighan lessons (note 167):
1. **Slots, not essays** — output structured JSON, bukan narasi panjang
2. **One component per call** — copy saja, visual saja, jangan campur
3. **Divergence 3-alt** — selalu return 3 opsi archetype berbeda
4. **Nusantara-aware** — default cultural context (halal, B.Indonesia, palet nasional)
5. **Framework explicit** — selalu disclose "ini pakai AIDA / Save the Cat / Aaker" biar user edukasi

---

## Sanad

- User directive 2026-04-20 (verbatim Threads-friendly list 8 domain)
- Note 167 — Creative framework BG Maker + Mighan
- Note 165 — Creative capability expansion directive
- Note 166 — SIDIX persona + framework Brain+Hands+Memory
- `docs/CREATIVE_CAPABILITY_ROADMAP.md` — roadmap 30+ capabilities
- `docs/decisions/ADR_002_killer_offer_strategy.md` — killer offer untuk beta
