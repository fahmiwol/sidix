# 158 — Closure Sprint 2026-04-19 + Handoff & Inventory

Tanggal: 2026-04-19
Tag: [FACT] state audit; [IMPL] 4 tool baru + 2 handoff doc; [DECISION] lock UI

## Ringkasan sprint hari ini

User menuntut dokumentasi komprehensif supaya sesi berikut tidak kehilangan konteks dan mengulang kerja. Hasilnya:

### Tools baru (4 total, semua standing-alone)
1. `web_fetch` — httpx + BeautifulSoup, strip HTML → teks bersih (commit `952a586`)
2. `code_sandbox` — Python subprocess `-I -B`, tempdir cwd, timeout 10s, pattern block (commit `952a586`)
3. `web_search` — DuckDuckGo HTML + own parser, resolve uddg redirect (commit `fddf66d`)
4. `pdf_extract` — pdfplumber own-stack, workspace path-traversal guard, page range support (commit `fddf66d`)

TOOL_REGISTRY tumbuh **13 → 17 tool**. `/health` live: `tools_available: 17`, `model_ready: true`, `models_loaded: 3`.

### Dokumentasi anti-amnesia
1. `docs/SIDIX_CAPABILITY_MAP.md` — SSoT kapabilitas (update ini, jangan buat baru)
2. `docs/HANDOFF_2026-04-19.md` — strategic (visi + 5 plans + mandate user)
3. `docs/INVENTORY_2026-04-19.md` — teknis detail (171 endpoint, 89 modul, 17 tool, 10 cron, 8 framework, path lengkap)
4. `CLAUDE.md` — UI LOCK section + deploy topology
5. `brain/public/research_notes/157_*.md` — audit lengkap rationale tools
6. `brain/public/research_notes/158_*.md` — file ini, closure

### Fix kritikal
- **Adapter symlink**: `/opt/sidix/apps/brain_qa/models/sidix-lora-adapter -> /opt/sidix/sidix-lora-adapter` → `model_ready=true`.
- **UI modal auto-muncul**: CSS `.contrib-modal-backdrop { display: flex }` dulu menang atas Tailwind `.hidden`. Fix pakai `:not(.hidden)` + `!important`.
- **Layout chatboard**: empty-state proportional di 100% zoom (logo kecil, spacing tighter).
- **Backend URL**: `.env` di `SIDIX_USER_UI/` diisi `VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com` — tanpa ini Vite bake default `localhost:8765`.

### Lock UI chatboard app.sidixlab.com
Struktur final dikunci: logo kecil + SIDIX title + tagline + 4 quick-prompt cards (Partner/Coding/Creative/Chill) + input + footer link ke sidixlab.com#contributor. Mobile nav 4 item (Chat/Tentang/Setting/SignIn). Ditulis di `CLAUDE.md`. Jangan ubah struktur tanpa izin eksplisit.

## State live server 2026-04-19

```
GET https://ctrl.sidixlab.com/health
{
  "model_ready": true,
  "models_loaded": 3,
  "tools_available": 17,
  "wikipedia_fallback_available": true,
  "internal_mentor_pool": { "ready": true, "redundancy_level": 3 },
  "engine_build": "0.1.0"
}

POST https://ctrl.sidixlab.com/agent/chat
  (field: question, persona, max_steps)
  → 200 OK, ~9s, jawab dengan sidq/sanad/tabayyun + epistemic_tier + maqashid_score

171 endpoint HTTP, 10 cron aktif, 6 persona, 89 modul Python.
```

## Prinsip yang di-lock oleh user

> "SIDIX harus standing alone — own modules, framework, tools sendiri, bukan API vendor AI."

Konsekuensi rule:
- ❌ Tidak pakai OpenAI, Anthropic, Gemini, DALL-E, Midjourney, Google Search API, Bing Search API
- ✅ Open data API publik OK (arXiv, Wikipedia, MusicBrainz, Quran.com, GitHub REST)
- ✅ Self-host model di server sendiri OK (Qwen + LoRA sudah jalan)
- ✅ Subprocess Python OK (code_sandbox)
- ✅ HTTP fetch HTML publik + parse sendiri OK (web_fetch, web_search DuckDuckGo)

## Gap yang masih terbuka (P2, butuh infra)

| Gap | Pendekatan | Blocker |
|---|---|---|
| Image generation | Self-host SDXL/FLUX | GPU VPS |
| Vision input | Self-host Qwen2.5-VL / InternVL | GPU VPS |
| ASR (user voice in) | whisper.cpp CPU-only | install + wire |
| TTS (SIDIX bicara) | Piper / Coqui XTTS self-host | install + wire |
| Cron LearnAgent | Pakai env var token yang benar | cek `.env` server |

## Keputusan untuk sesi berikut

Pilih 1 dari 5 plan di `HANDOFF_2026-04-19.md`:
- **Plan A**: Multi-channel social (X/LinkedIn/Reddit/Discord/Telegram/YouTube/Medium)
- **Plan B**: Learning sources Phase 2 (Spotify/Unsplash/Pexels/Papers With Code/Pinterest/HuggingFace)
- **Plan C**: Sub-agent architecture (6-8 agent + Orchestrator)
- **Plan D**: SEO lanjutan (RSS/JSON-LD Article/OG gen per note)
- **Plan E**: Capability parity (wire audio_capability, concept_graph; P2 GPU)

Default kalau ragu: **Plan E P1 concept_graph** (wire `brain_synthesizer` sebagai tool) — 1-2 jam, nambah capability epistemic-native yang tidak dimiliki vendor LLM.

## Sanad

- Code: commit `952a586` (web_fetch + code_sandbox), `fddf66d` (web_search + pdf_extract).
- Docs: `docs/HANDOFF_2026-04-19.md`, `docs/INVENTORY_2026-04-19.md`, `docs/SIDIX_CAPABILITY_MAP.md`, `CLAUDE.md` (UI LOCK section).
- Data source: `/health` dan `/openapi.json` dari `ctrl.sidixlab.com` live 2026-04-19.
- Previous note: `157_capability_audit_standing_alone_2026_04_19.md`.
