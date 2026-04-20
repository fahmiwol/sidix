# SIDIX Creative Agent Taxonomy

**SSoT** untuk 8 vertical creative domain + AI agent yang akan dibangun.
Dokumen ini TIDAK ada detail teknis — itu di research note 168. Ini index + status tracker.

**Last update:** 2026-04-20

---

## ⚠️ Principle (WAJIB DIINGAT)

**SIDIX = AI AGENT, bukan Search Engine / Directory.**

- User minta GENERATE → SIDIX generate konten/copy/image/video, bukan kasih lihat hasil search corpus
- Corpus/RAG = context enrichment INTERNAL (tool, bukan output)
- Expected: "Ini caption IG-nya: [3 varian]", NOT "Berdasarkan corpus note X tentang copywriting..."

---

## 🗂️ 8 Vertical Domain × Agent Map

### 1. Konten & Media Production
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `generate_content_plan` | niche, durasi, channel | kalender JSON + posting plan | ⏳ P0 |
| `generate_copy` | topic, formula (AIDA/PAS/FAB), channel | 3 varian caption | ⏳ P0 |
| `generate_video_script` | topic, duration (30s/60s/3min), hook style | script hook-pain-solution-CTA | ⏳ P1 |

### 2. Desain Grafis & Branding
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `generate_brand_kit` | business name, niche, vibe | markdown (palette+tone+archetype) + logo prompt | ⏳ P0 |
| `text_to_image` | prompt | PNG via SDXL | ✅ LIVE |
| `generate_thumbnail` | title, style | YT/IG thumbnail PNG dengan text overlay | ⏳ P0 |
| `generate_feed_cohesive` | theme, n_posts | N images cohesive grid | ⏳ P1 |

### 3. Video & Editing
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `generate_storyboard` | script | 6-12 frame images + caption per frame | ⏳ P2 |
| `auto_subtitle` | video URL/path | SRT file | ⏳ P2 |
| `hook_finder` | video transcript | timestamp viral-segment suggestions | ⏳ P3 |
| `text_to_video` | prompt, duration | MP4 (via Stable Video Diffusion) | ⏳ P3 |

### 4. Marketing & Campaign Strategy
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `plan_campaign` | brief (budget/goal/audience) | strategy (AARRR funnel + channel mix + timeline) | ⏳ P0 |
| `generate_ads` | product, platform (FB/Google/TikTok) | 3-5 ad copy + image prompts | ⏳ P0 |
| `build_funnel` | product, target audience | awareness→consideration→conversion→retention stages | ⏳ P1 |

### 5. Produk & E-commerce
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `product_description` | product info, marketplace | SEO copy (Shopee/Tokped style) | ⏳ P1 |
| `product_photoshoot` | product image + scene description | composited image mockup | ⏳ P1 |
| `packaging_concept` | product, dimension | 3D mockup render | ⏳ P2 |

### 6. Entertainment & Character Creation
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `build_character` | brand, personality traits | character sheet (visual + lore + expressions) | ⏳ P2 |
| `generate_story_world` | genre, setting | world-building bible (places/characters/rules) | ⏳ P2 |

### 7. Voice & Audio Creative
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `text_to_speech` | text, voice style | MP3/WAV via Piper | ⏳ P2 |
| `generate_podcast_script` | topic, duration | multi-speaker script | ⏳ P2 |
| `voice_clone` | sample audio + text | cloned TTS output (Coqui XTTS) | ⏳ P3 |

### 8. Creative Writing & Storytelling
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `write_brand_story` | brand history, values | origin narrative 500-1000 kata | ⏳ P1 |
| `write_article` | topic, angle, length | long-form article with SEO | ⏳ P1 |
| `write_script_drama` | logline, genre | 3-act script outline | ⏳ P2 |

---

## 🎁 Agency Kit (one-click bundle) — TARGET SPRINT 5

User input: business name + niche + target audience

SIDIX output (1 click):
1. **Brand Kit:** name rationale + archetype + palette + tipografi + voice tone + manifesto
2. **Logo:** 3 varian (archetype orthogonal) + preview mockup
3. **Konten starter:** 10 caption IG + 5 thread X + 3 script Reels
4. **Campaign plan:** 30-hari calendar + channel mix + ad copy
5. **Visual set:** 9 IG post cohesive + 3 thumbnail + 1 hero banner

**Value prop:** "Branding agency 2 minggu, jadi 2 menit."

---

## 📊 Status Dashboard

| Status | Count |
|--------|-------|
| ✅ LIVE | 1 (text_to_image) |
| ⏳ P0 (Sprint 4) | 6 |
| ⏳ P1 (Sprint 5) | 8 |
| ⏳ P2 (Sprint 6) | 9 |
| ⏳ P3 (Sprint 7+) | 4 |
| **Total target** | **28 agent** |

---

## 🔗 Related Docs

- [Note 168](../brain/public/research_notes/168_sidix_creative_verticals_8_domains.md) — detail per vertical
- [Note 167](../brain/public/research_notes/167_creative_agent_framework_bg_maker_mighan.md) — framework sumber (BG Maker + Mighan)
- [Note 165](../brain/public/research_notes/165_sidix_creative_capability_expansion.md) — creative capability directive awal
- [ADR-002](decisions/ADR_002_killer_offer_strategy.md) — 5 killer offer
- [CREATIVE_CAPABILITY_ROADMAP.md](CREATIVE_CAPABILITY_ROADMAP.md) — 30+ capabilities per 4-stage
- [SIDIX_CAPABILITY_MAP.md](SIDIX_CAPABILITY_MAP.md) — SSoT kapabilitas teknis
