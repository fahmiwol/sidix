# SIDIX Creative Agent Taxonomy

**SSoT** untuk **10 vertical creative domain** + AI agent yang akan dibangun.
Dokumen ini TIDAK ada detail teknis — itu di research note 168 + 169. Ini index + status tracker.

**Last update:** 2026-04-21 (extended 8→10 domain per adopsi riset user, note 169)

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
| `generate_content_plan` | niche, durasi, channel | kalender JSON + posting plan | ✅ LIVE (beta Sprint 4) |
| `generate_copy` | topic, formula (AIDA/PAS/FAB), channel | 3 varian caption | ✅ LIVE (beta Sprint 4) |
| `generate_video_script` | topic, duration (30s/60s/3min), hook style | script hook-pain-solution-CTA | ⏳ P1 |

### 2. Desain Grafis & Branding
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `generate_brand_kit` | business name, niche, vibe | markdown (palette+tone+archetype) + logo prompt | ✅ LIVE (beta Sprint 4) |
| `text_to_image` | prompt | PNG via SDXL | ✅ LIVE |
| `generate_thumbnail` | title, style | YT/IG thumbnail PNG dengan text overlay | ✅ LIVE (beta Sprint 4) |
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
| `plan_campaign` | brief (budget/goal/audience) | strategy (AARRR funnel + channel mix + timeline) | ✅ LIVE (beta Sprint 4) |
| `generate_ads` | product, platform (FB/Google/TikTok) | 3-5 ad copy + image prompts | ✅ LIVE (beta Sprint 4) |
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

### 9. 🔮 3D Modeling (extension dari riset user — note 169)
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `text_to_3d` | prompt | .glb/.obj mesh (via Hunyuan3D / Sloyd) | ⏳ P2 |
| `image_to_3d` | reference image | mesh dengan texture | ⏳ P2 |
| `procedural_3d` | parameters | parametric mesh (Blender Python API) | ⏳ P2 |
| `asset_3d_manager` | — | registry + tag + search untuk aset 3D | ⏳ P3 |

### 10. 🎮 Gaming AI (extension dari riset user — note 169)
| Agent | Input | Output | Status |
|-------|-------|--------|--------|
| `npc_generator` | personality, role, lore | NPC sheet + dialogue tree | ⏳ P2 |
| `level_designer` | gameplay goal, genre | map grid + obstacles + objectives | ⏳ P3 |
| `game_assets` | art style, list items | sprite sheets + icons set | ⏳ P3 |
| `world_generator` | genre, biome | biome/quest/faction bible | ⏳ P3 |

---

## 🎚️ Quality + Iteration Protocol (dari note 169 adopsi riset user)

### CQF Quality Gate (Creative Quality Framework)

Setiap agent output wajib lewat quality scoring:

| Dimension | Weight | Min for delivery |
|-----------|--------|------------------|
| Relevance | 25% | 7.0 |
| Quality | 25% | 7.0 |
| Creativity | 20% | 6.5 |
| Brand Alignment | 15% | 6.5 |
| Actionability | 15% | 7.0 |
| **Total weighted** | 100% | **≥ 7.0** |

### Iteration Protocol (4-round)

Agent yang flag `needs_iteration = true` wajib:
1. **Round 1 GENERATE** — 3-5 variants, fast model, threshold 5.0
2. **Round 2 EVALUATE** — LLM-as-Judge pilih top 2, identify weakness
3. **Round 3 REFINE** — polish, heavy model, threshold 7.0
4. **Round 4 ENHANCE** (premium) — threshold 8.5

### Debate Ring Pairings (multi-agent consensus)

| Creator | Critic | Konteks |
|---------|--------|---------|
| Copywriter | Campaign Strategist | Tone fit audience? |
| Brand Builder | Design Assistant | Palette fit archetype? |
| Script Generator | Hook Finder | Opening cukup catchy? |
| Product Description | Marketing Ads | Copy converts? |
| Character Builder | Story Writer | Persona konsisten dengan lore? |

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

## 📊 Status Dashboard (updated 2026-04-21)

| Status | Count |
|--------|-------|
| ✅ LIVE | 7 (text_to_image + 6 P0 sprint 4) |
| ⏳ P0 (Sprint 4) | 0 |
| ⏳ P1 (Sprint 5) | 8 |
| ⏳ P2 (Sprint 6) | 14 (9 + 5 dari 3D/Gaming) |
| ⏳ P3 (Sprint 7+) | 8 (4 + 4 dari 3D/Gaming/video) |
| **Total target** | **37 agent** (naik dari 28 setelah adopsi riset user) |

---

## 🔗 Related Docs

- [Note 168](../brain/public/research_notes/168_sidix_creative_verticals_8_domains.md) — detail per vertical
- [Note 167](../brain/public/research_notes/167_creative_agent_framework_bg_maker_mighan.md) — framework sumber (BG Maker + Mighan)
- [Note 165](../brain/public/research_notes/165_sidix_creative_capability_expansion.md) — creative capability directive awal
- [ADR-002](decisions/ADR_002_killer_offer_strategy.md) — 5 killer offer
- [CREATIVE_CAPABILITY_ROADMAP.md](CREATIVE_CAPABILITY_ROADMAP.md) — 30+ capabilities per 4-stage
- [SIDIX_CAPABILITY_MAP.md](SIDIX_CAPABILITY_MAP.md) — SSoT kapabilitas teknis
