---
sanad_tier: primer
tags: [creative-agent, framework, prompt-engineering, bg-maker, mighan, archetypes]
date: 2026-04-20
---

# 167 — Creative Agent Framework (dari BG Maker + Mighantect)

## Konteks

[FACT] User directive 2026-04-20: SIDIX jadi **killer Creative AI Agent** — fokus bantu kerjaan agency kreatif harian. User menunjuk 2 folder referensi: `D:\BG maker\` (Tiranyx BG Maker spec) + `D:\Mighan\` (Mighantect 3D agency simulator).

Sprint 15-menit: ekstrak prinsip, framework, modul, tools yang bisa SIDIX adopsi supaya powerful sebagai creative agent.

---

## Temuan Utama

### 1. BG Maker — Prompt Engineering Architecture (`06_Prompt-Engineering.md`)

[FACT] 5 Prompt Philosophy Rules (Tiranyx BG Maker):
1. **Slots, not essays** — LLM return typed data, bukan narasi. Schema = framework baked in.
2. **One component per call** — jangan minta strategy+manifesto+logo+color sekali jalan.
3. **Divergence enforced** — 3 alt harus orthogonal archetype slot, bukan cosmetic variation.
4. **System cached, user small** — ~3000-token system prompt pakai Anthropic prompt cache.
5. **Structured output atau retry** — JSON schema validated (Zod). Invalid = repair prompt.

[FACT] 5 Framework yang dipakai (urutan wajib):
1. **Aaker Brand Identity** — Brand Essence + Core Identity + Extended Identity + 4 perspektif (Product/Org/Person/Symbol) + Value Prop (Functional/Emotional/Self-expressive)
2. **Simon Sinek Golden Circle** — Why → How → What (Why dari founder purpose, bukan product feature)
3. **Marty Neumeier Onlyness Statement** — "[BRAND] is the only [CAT] that [DIFF] for [CUST] in [MARKET] who want [MOT] during [TREND]". Wajib Competitor Swap Test.
4. **Jungian 12 Brand Archetypes** (Mark & Pearson) — primary 70% + secondary 30%, jangan pair opposite-quadrant.
5. **Keller CBBE Pyramid** — Salience → Performance/Imagery → Judgments/Feelings → Resonance.

[FACT] 13-call generation flow:
- 1 Master call (arhetype seeds) → 3 Strategy → 3 Manifesto → 3 Voice → 3 Visual → 3 Rationale
- Budget: ~$1.40-$1.60 per generation (text + image)
- Cached system prompt = 60% cost reduction input tokens

### 2. Mighantect 3D — Agency Pipeline (`server/agency-pipeline.js`)

[FACT] Flow: brief → strategy → copy → generate → backlog. Full orchestrator untuk simulasi agency kerja.

[FACT] 16 agen dengan HR persona di `config/agent-ledger.json`: voicePersona, npcPersona, portraitImagePrompt, preferredModels. Setiap agen punya ID + Nama + Role (CSO/CTO/CD/LeadDev/etc).

[FACT] Key server modules relevan untuk SIDIX:
- `microstock-metadata.js` — AI metadata generator (title, desc, keywords untuk Adobe Stock)
- `microstock-uploader.js` — SFTP/FTP uploader
- `innovation-agent.js` — Iris AI engine (research, ideation, sandbox, review)
- `youtube-agent.js` — YouTube bot: topic→script→TTS→thumbnail→ffmpeg→upload
- `buzzer-engine.js` — polling engine eksekusi backlog via API / Playwright
- `content-backlog.js` — antrian aksi sosmed + microstock

### 3. 12 Archetype Motivational Quadrants

```
STABILITY       BELONGING       MASTERY         INDEPENDENCE
├─ Caregiver    ├─ Jester       ├─ Hero          ├─ Innocent
├─ Ruler        ├─ Everyman     ├─ Outlaw        ├─ Sage
└─ Creator      └─ Lover        └─ Magician      └─ Explorer
```

Aturan: never pair opposite quadrants (Stability+Mastery, Belonging+Independence) kecuali tension sengaja sebagai concept.

---

## Adopsi ke SIDIX (IMPL commit ini)

### Modul Baru: `apps/brain_qa/brain_qa/creative_framework.py`

Fitur:
1. **12 archetype registry** — nama, quadrant, core_desire, fear, voice tone
2. **`opposite_quadrant(a, b)` helper** — cek orthogonality
3. **7 CreativeTemplate** — IG Feed, IG Story, YT Thumbnail, Poster Event, Product Shot, Food Shot, Web Banner. Masing-masing punya aspect_ratio/width/height/style_prefix/negative/default_archetype.
4. **`detect_context()`** — 10 kategori kultural Nusantara (islam_masjid, batik_tenun, candi_heritage, rumah_adat, pantai_laut, gunung_alam, sawah_padi, makanan, kota_urban, orang_keluarga) dengan keyword rules.
5. **`enhance_prompt_creative()`** — main API: strip verbs → infer template → apply archetype → detect context → layer style hints → return dict dengan enhanced_prompt + negative + width + height + metadata.
6. **`suggest_divergent_archetypes()`** — future use: generate 3 orthogonal alt (BG Maker divergence pattern).

### Upgrade `agent_react.run_react()` fast-path

Ganti inline `_enhance_prompt` string concat → import `creative_framework.enhance_prompt_creative()`:
- Template auto-detected dari keyword (thumbnail/reels/poster/produk/kuliner/banner)
- Archetype applied dari template default (everyman untuk IG feed, hero untuk YT thumbnail, caregiver untuk food, dll)
- Width/height adaptive per template (clamped ke max 768 untuk fit 6GB VRAM)
- Context hints Nusantara 10 kategori (lebih kaya dari 5 kategori sebelumnya)

---

## Contoh Transformasi

**User prompt:** `"bikin thumbnail youtube tutorial masjid demak subuh"`

**Pre-framework (v1 simple):** `masjid demak subuh, warm golden hour light, serene spiritual atmosphere, Islamic architectural details, professional photography, 4k, cinematic, sharp focus`

**Post-framework (v2 framework-aware):**
```
template: yt_thumbnail (ratio 16:9, 1024x576)
archetype: hero (MASTERY quadrant, voice: bold courageous direct)
detected_contexts: [islam_masjid]
enhanced_prompt: thumbnail youtube tutorial masjid demak subuh,
  warm golden hour light, serene spiritual atmosphere, Islamic
  architectural detail, calligraphy element,
  high-contrast thumbnail, eye-catching focal subject, bold composition,
  cinematic lighting,
  mood: bold, courageous, direct,
  professional photography, 4k high detail, cinematic composition, sharp focus
negative_prompt: subtle, muted colors, hard to read at small size
width: 768, height: 576 (clamped dari 1024)
```

Quality improvement: ratio tepat untuk YouTube, archetype tone cocok thumbnail (bold/courageous), negative prompt spesifik.

---

## Selanjutnya (future sprint)

1. **Divergence-3 pattern** — endpoint `/generate_variants` yang pakai `suggest_divergent_archetypes()` → 3 versi gambar dengan archetype berbeda (IG agency test A/B/C).
2. **Tier-1 frameworks expand** — tambahkan Aaker/Sinek/Neumeier untuk use case brand strategy (tidak hanya gambar).
3. **Agency pipeline port** — adopsi `agency-pipeline.js` flow brief→strategy→copy→image→backlog jadi SIDIX tool.
4. **Microstock metadata tool** — adopsi `microstock-metadata.js` jadi SIDIX tool `generate_stock_metadata`.
5. **Agent ledger persona** — upgrade 5 persona SIDIX (MIGHAN/TOARD/FACH/HAYFAR/INAN) dengan voicePersona + portraitImagePrompt seperti Mighantect 16 agen.

---

## Sanad

- `D:\BG maker\06_Prompt-Engineering.md` (Tiranyx internal) — 5 prompt philosophy + 5 framework
- `D:\BG maker\01_PRD_BG-Maker.md` (53KB) — product vision
- `D:\Mighan\CLAUDE.md` — Mighantect 3D memory + 16 agent registry
- Mark & Pearson, "The Hero and the Outlaw" (2001) — 12 Archetypes
- Keller, "Strategic Brand Management" — CBBE Pyramid
- David Aaker, "Building Strong Brands" — Brand Identity System
- Simon Sinek, "Start With Why" — Golden Circle
- Marty Neumeier, "Zag" — Onlyness Statement
