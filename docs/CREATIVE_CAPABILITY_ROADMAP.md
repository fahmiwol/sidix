# SIDIX Creative Capability Roadmap
**Dibuat:** 2026-04-19 | **Status:** LIVING DOCUMENT — update setiap sprint

Direktif user (2026-04-19): SIDIX harus jago di akademik, creativity, programming, gaming, membuat aplikasi/website/game/3D/WebGL/Three.js, design content/foto, text-to-image, image-to-text, image-to-image, image-to-video, text-to-sound, TTS, photo/video editor, content marketing, periklanan, filter, style.

Prinsip standing-alone: semua kapabilitas pakai open-source model self-host. TIDAK ada vendor AI API.

---

## 🗺️ Peta 4 Stage

```
Baby (Q1–Q2 2026)   → Fondasi text + Python + PDF + web
Child (Q3 2026)     → Multimodal: image gen + vision + audio + skill library
Adolescent (Q4–Q1') → Self-evolving + code interpreter penuh + video gen
Adult (Q2' 2027+)   → Distributed + real-time collab + style engine
```

---

## 📚 Akademik & Research (Baby → Child)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Jawab pertanyaan akademik | RAG + ReAct + corpus | Baby | ✅ aktif | 18 tools, 1149 docs |
| Cari paper ilmiah | `web_search` + arXiv connector | Baby | ✅ aktif | DuckDuckGo + arXiv API |
| Baca & analisis PDF | `pdf_extract` (pdfplumber) | Baby | ✅ aktif | path-guard, workspace |
| Solve matematika | `math_solve` (SymPy) | Baby Sprint 2 | ⏳ T2.1 | LaTeX + step-by-step |
| Analisis data CSV | `data_analyze` (pandas) | Baby Sprint 2 | ⏳ T2.2 | natural language query |
| Visualisasi data | `plot_generate` (matplotlib) | Baby Sprint 2 | ⏳ T2.3 | bar/line/scatter/heatmap |
| Citation + sanad chain | sanad ranker + frontmatter | Baby | ✅ aktif (T1.2) | epistemic transparency |
| OCR gambar/scan | pytesseract self-host | Baby | ⏸ P1 | butuh install |
| Knowledge graph query | `concept_graph` (BrainSynthesizer) | Baby | ✅ aktif (T1.1) | BFS multi-hop |

---

## 💻 Programming & Coding (Baby → Child)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Jalankan Python snippet | `code_sandbox` (subprocess -I) | Baby | ✅ aktif | timeout 10s, no network |
| Multi-language executor | Docker sandbox (Python/JS/Rust/Go) | Child | ⏳ Sprint 4 | resource limit per container |
| Code review otomatis | ReAct + corpus (pattern matching) | Baby | ✅ parsial | via chat |
| Debug assistant | ReAct + web_fetch docs | Baby | ✅ aktif | via reasoning |
| Generate webapp/landing | LLM generative + template | Baby | ✅ parsial | tidak ada renderer |
| Preview HTML real-time | iframe sandbox / preview server | Child | ⏳ Sprint 3 | butuh sandbox infra |
| Bikin game (Pygame/Phaser) | code_sandbox + game template | Child | ⏳ Sprint 4 | Phaser.js template library |
| Three.js / WebGL scene | `threejs_gen` tool (LLM + template) | Child | ⏳ Sprint 4 | generate .js scene file |
| 3D render (Blender) | Blender Python API subprocess | Adolescent | ⏳ Sprint 6 | butuh Blender headless |

---

## 🎨 Gambar & Visual (Child → Adolescent)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Text-to-Image | SDXL / FLUX.1 self-host | Child Q3 | ⏳ Sprint 3 | butuh GPU server (R2 Antigravity) |
| Image-to-Text (caption) | Qwen2.5-VL / BLIP2 self-host | Child Q3 | ⏳ Sprint 3 | butuh GPU |
| Image-to-Image (ControlNet/IP-Adapter) | ComfyUI API self-host | Child Q3 | ⏳ Sprint 4 | setelah infra SDXL siap |
| Style transfer | ControlNet reference style | Child Q3 | ⏳ Sprint 4 | — |
| Filter foto (crop/resize/enhance) | PIL / OpenCV subprocess | Baby | ⏳ Sprint 2 ext | CPU, no GPU needed |
| Remove background | rembg self-host | Child | ⏳ Sprint 3 | onnx model, CPU OK |
| Face anonymization (privacy) | OpenCV detect + blur | Baby | ⏳ Sprint 2 | sesuai privacy policy |
| Design content (poster/banner) | LLM + SVG template gen | Child | ⏳ Sprint 4 | no Canva API |
| OCR gambar (image-to-text teks) | pytesseract | Baby | ⏳ P1 | CPU, easy install |

---

## 🎵 Audio & Suara (Child)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| TTS — SIDIX bicara | Piper self-host (CPU) | Baby P2 | ⏳ Sprint 3 | `audio_capability.py` siap |
| ASR — user kirim suara | whisper.cpp CPU-only | Baby P2 | ⏳ Sprint 3 | `audio_capability.py` siap |
| Music generation | AudioCraft/MusicGen self-host | Child | ⏳ Sprint 5 | butuh GPU / CPU slow |
| Tajwid + Qiraat audio | Quran audio API (open data) | Child | ⏳ Sprint 4 | connector Quran.com audio |
| Voice clone (creator mode) | Coqui XTTS self-host | Adolescent | ⏳ Sprint 6 | GPU preferred |
| Sound effects gen | AudioCraft sound-gen | Child | ⏳ Sprint 5 | sama dengan music gen |

---

## 🎬 Video (Adolescent)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Text-to-Video | CogVideoX / Open-Sora self-host | Adolescent Q4 | ⏳ Sprint 7 | butuh GPU A100+ |
| Image-to-Video | Stable Video Diffusion | Adolescent | ⏳ Sprint 7 | butuh GPU |
| Video editor (trim/cut/caption) | ffmpeg subprocess | Child | ⏳ Sprint 4 | CPU, no GPU |
| Auto-caption video | Whisper → SRT → ffmpeg burn | Child | ⏳ Sprint 4 | CPU pipeline |
| Video-to-Text (transcribe) | Whisper | Baby P2 | ⏳ Sprint 3 | sama dengan ASR |
| Content marketing video | template + ffmpeg + TTS | Child | ⏳ Sprint 5 | pipeline kombinasi |

---

## 📣 Marketing & Content (Baby → Child)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Posting Threads otomatis | `threads_autopost.py` | Baby | ✅ aktif | 40 endpoints live |
| Content calendar generation | LLM + workspace | Baby | ✅ parsial | via chat/generative |
| Copywriting iklan | LLM generative | Baby | ✅ aktif | persona MIGHAN |
| SEO analysis | web_fetch + keyword extract | Baby | ✅ parsial | note 150 |
| Social media analytics | web_fetch (public) | Child | ⏳ Sprint 4 | scrape public metrics |
| Hashtag research | web_search + trend parse | Baby | ✅ parsial | via web_search |
| A/B test content variants | LLM + template engine | Child | ⏳ Sprint 4 | — |
| Periklanan (ad copy multi-format) | LLM + persona router | Baby | ✅ aktif | via MIGHAN persona |

---

## 🎮 Gaming (Child → Adolescent)

| Kapabilitas | Tool | Stage | Status | Notes |
|-------------|------|-------|--------|-------|
| Pygame game generator | code_sandbox + template | Child | ⏳ Sprint 4 | Python game template |
| Phaser.js web game | LLM + Phaser.js template | Child | ⏳ Sprint 4 | JS, no backend needed |
| Unity C# script assist | LLM generative | Baby | ✅ parsial | text only, no run |
| Game asset prompt (sprite/bg) | SDXL + prompt enhance | Child | ⏳ Sprint 3 | post-T3.1 |
| Game level design | LLM + JSON level schema | Child | ⏳ Sprint 4 | — |

---

## 🔧 On-Demand Tools (Baby Sprint 2+)

| Tool | Input | Output | Stage | Status |
|------|-------|--------|-------|--------|
| `math_solve` | expr + operation | LaTeX + plain | Baby S2 | ⏳ T2.1 |
| `data_analyze` | CSV path + question | markdown table | Baby S2 | ⏳ T2.2 |
| `plot_generate` | data + kind | PNG path | Baby S2 | ⏳ T2.3 |
| `image_filter` | image path + ops | image path | Baby S2 ext | ⏳ Sprint 2 |
| `remove_bg` | image path | image path | Child S3 | ⏳ Sprint 3 |
| `image_caption` | image path | text | Child S3 | ⏳ Sprint 3 |
| `text_to_image` | prompt + style | image path | Child S3 | ⏳ Sprint 3 |
| `tts_generate` | text + voice | audio path | Baby P2 | ⏳ Sprint 3 |
| `transcribe` | audio path | text | Baby P2 | ⏳ Sprint 3 |
| `video_caption` | video path | SRT | Child S4 | ⏳ Sprint 4 |
| `music_gen` | prompt + duration | audio path | Child S5 | ⏳ Sprint 5 |

---

## 🚦 Decision Gates

- **Sprint 3 gate:** Tunggu R1-R4 Antigravity (GPU provider, SDXL vs FLUX, ComfyUI vs Diffusers) sebelum commit infra image gen.
- **Sprint 5 gate:** Music gen dan video gen butuh benchmark GPU cost → keputusan cloud vs on-premise.
- **Sprint 6 gate:** Voice clone dan full video pipeline → butuh legal review IP hak cipta suara.

---

## 📎 File Terkait

- `docs/agent_tasks/DELEGATION_REGISTRY.md` — tracking task per agent
- `docs/agent_tasks/SPRINT_1_CURSOR.md` — Sprint 1–2 task Cursor
- `docs/agent_tasks/SPRINT_1_ANTIGRAVITY.md` — research R1-R4
- `docs/SIDIX_ROADMAP_2026.md` — roadmap 4 stage full
- `brain/public/research_notes/165_sidix_creative_capability_expansion.md` — rationale + filosofi

Terakhir diupdate: 2026-04-19.
