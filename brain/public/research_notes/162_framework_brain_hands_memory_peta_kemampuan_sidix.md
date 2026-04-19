---
sanad_tier: primer
---

# 162 — Framework Brain/Hands/Memory + Peta Kemampuan SIDIX

Tanggal: 2026-04-19
Tag: [DECISION] framework arsitektural; [REFERENCE] peta kemampuan 10 item; [INTEGRATE] vision+PRD+roadmap

Sumber: hasil diskusi arsitektural dengan user 2026-04-19 — membongkar mitos "satu model monster" dan menetapkan framework modular orkestrasi.

---

## 1. Mitos yang dibongkar dulu

**GPT/Gemini/Claude bukan satu model tunggal yang bisa segalanya.**

Yang kamu lihat sebagai "GPT serbaguna" sebenarnya adalah **orkestrator**:
- LLM teks (otak) memutuskan kapan panggil tool/model mana.
- Untuk gambar: panggil DALL-E (diffusion terpisah).
- Untuk matematika kompleks: panggil Python interpreter.
- Untuk info terbaru: panggil web search.
- Untuk video: panggil Sora (model terpisah).
- Untuk coding serius: sering route ke model coding khusus.

**Kabar baik untuk SIDIX:** tidak perlu satu model monster. Kita butuh **satu LLM otak yang cukup pintar untuk orkestrasi + kumpulan tool/model spesialis**.

---

## 2. Framework arsitektural: Brain + Hands + Memory

Analogi tubuh manusia, cocok dengan filosofi IHOS:

### Brain (LLM inti)
- **Baby stage:** Qwen2.5-7B + LoRA SIDIX (sudah live).
- **Fungsi:** bukan "tahu segalanya", tapi "paham bahasa, bisa reasoning, tahu kapan panggil siapa".
- **Analog IHOS:** akal — tidak menyimpan semua ilmu, tapi memproses dan menyimpulkan.

### Hands (Tools)
- Kumpulan kapabilitas eksternal yang brain bisa panggil.
- Per 2026-04-19: 17 tool aktif (search_corpus, web_fetch, web_search, code_sandbox, pdf_extract, calculator, workspace_*, roadmap_*, dll.).
- **Analog IHOS:** alat validasi — seperti sanad, brain tidak klaim langsung "saya tahu", tapi merujuk ke sumber/alat yang valid.
- **Roadmap**: diffusion image-gen (SDXL/FLUX), VLM (Qwen-VL), ASR/TTS (Whisper/Piper), code executor advanced, video pipeline (ffmpeg + image seq), template system untuk UI gen.

### Memory (RAG + GraphRAG + Skill Library)
- **RAG existing:** BM25 corpus (`query.py`), 157+ research notes.
- **GraphRAG roadmap:** knowledge graph entitas + relasi (beda dengan RAG polos: bisa multi-hop reasoning). Cocok untuk **epistemologi berbasis sanad** — relasi antar sumber eksplisit.
- **Skill library roadmap:** skill persistent à la Voyager — pola tool-call + prompt + contoh tersimpan dan di-reuse.
- **Analog IHOS:** hifdz terstruktur — memori yang bisa diakses dengan sanad jelas, bukan pasif.

---

## 3. Peta 10 kemampuan SIDIX × Cara implementasi × Tahap roadmap

| # | Kemampuan | Pendekatan | Tahap |
|---|---|---|---|
| 1 | Jawab pertanyaan + kasih ide | Native LLM + GraphRAG + sistem prompt IHOS | **Baby** (bulan 1–3) — **sudah aktif 2026-04-19** |
| 2 | Bikin gambar | Tool `generate_image` → Stable Diffusion XL / FLUX.1 self-host + **image prompt enhancer Nusantara** | **Baby → Child** (bulan 3–6, butuh GPU 8–16GB VRAM) |
| 3 | Coding dasar | Native LLM + `code_sandbox` sandbox Python | **Baby** (bulan 2–4) — **sudah aktif (code_sandbox live)** |
| 4 | Coding serius | Router ke **Qwen2.5-Coder** (7B/14B/32B) atau DeepSeek-Coder-V2 sebagai specialist agent di skill library | **Child** (bulan 6–12) |
| 5 | Bikin aplikasi/interface UI | Code gen multi-file + **template system** (React/Next.js/Laravel/Vite starter) | **Child** (bulan 9–15) |
| 6 | Bikin game 2D | Orkestrasi: kode (Phaser.js/Godot) + sprite via diffusion + musik via MusicGen | **Child+** (bulan 12+) |
| 7 | Hitung matematika serius | Tool `python_executor` dalam Docker sandbox (**jangan mengandalkan LLM** — halusinasi di angka besar) | **Baby** (bulan 2) — partial (code_sandbox sudah, perlu wrapping math) |
| 8 | Video sederhana (80% konten viral) | Storyboard + image-sequence + TTS narasi + **ffmpeg stitch** | **Baby → Child** (bulan 6–9) |
| 9 | Video generation asli | Tool: HunyuanVideo / Mochi 1 / CogVideoX / LTX Video — butuh **A100/H100** | **Adolescent+** (tahun 2) |
| 10 | Pengetahuan umum + real-time | **3 lapis**: bobot model (weak) + RAG/GraphRAG+sanad (kuat) + web search dengan sanad-ranking (real-time) | **Baby** (bulan 1–6) — lapis 1 & 3 sudah, lapis 2 (GraphRAG) roadmap |

---

## 4. Prinsip penting (LOCK)

> **Jangan jatuh cinta dengan ide "satu model besar yang bisa segalanya".** Itu jalan lab dengan budget miliaran dolar.

**Jalan SIDIX sebagai solo founder dengan filosofi IHOS:**

> **Modular orkestrasi dengan brain yang punya jati diri.**

Brain SIDIX tidak perlu lebih pintar dari GPT-5. Dia perlu lebih **punya karakter**:
- Cara reasoning mencerminkan IHOS.
- Knowledge base terkurasi dengan sanad.
- Tool bisa divalidasi publik karena open source.

**Keunggulan SIDIX:**
- ❌ BUKAN: skala parameter, speed inference, kualitas generik.
- ✅ ADALAH: **transparansi epistemologis + kedaulatan data + spesialisasi kultural**.

Tiga hal ini secara struktural tidak bisa ditawarkan big tech.

---

## 5. Implikasi ke roadmap

### Update SIDIX_ROADMAP_2026.md
Framework ini memperjelas stage existing:
- **Baby (Q1–Q2 2026)** = Brain solid + 3 lapis Memory + Hands dasar (tool existing).
- **Child (Q3 2026)** = ekspansi Hands (image/vision/audio/code specialist/template system).
- **Adolescent (Q4 2026 – Q1 2027)** = Brain belajar mandiri (SPIN/merging) + Memory graph aktif + Skill Library populated.
- **Adult (Q2 2027+)** = Hands + Brain + Memory terdistribusi (hafidz network).

### Update Vision/Misi (docs/01_vision_mission.md)
Ganti frase "orchestrator + RAG + fine-tune ringan" jadi lebih presisi: **Brain (LLM inti) + Hands (tool + model spesialis) + Memory (RAG + GraphRAG + Skill Library) dengan filosofi IHOS di setiap lapis.**

### Update PRD (docs/02_prd.md)
Tabel section 3 (peta 10 kemampuan) jadi **scope specification** — PRD fitur yang dijanjikan per-stage.

---

## 6. Diferensiasi yang sulit ditiru: image prompt enhancer Nusantara

Contoh kapabilitas unik yang saya highlight:

```
User: "Bikin gambar astronaut di Borobudur."

SIDIX Brain: parse intent → lookup knowledge base Nusantara (corpus notes
tentang relief candi, ornamen Buddhist, lansekap Magelang) → enrich prompt:

"Astronaut in spacesuit standing at Borobudur temple, Magelang, Central Java,
Indonesia. Volcanic mountains Merapi background, morning mist, ancient
Buddhist stupas with bell-shape, relief carvings of Boddhisattva, tropical
vegetation, soft golden hour lighting, photorealistic, wide shot, Nikon
D850 style"

→ kirim ke Stable Diffusion XL → gambar dengan konteks kultural kaya.
```

Ini tidak bisa dilakukan GPT/Claude/Gemini karena mereka tidak punya knowledge base kurasi manual tentang Nusantara yang terstruktur + sanad. SIDIX punya.

---

## 7. Mapping ke kode existing (per 2026-04-19)

| Framework layer | File kode |
|---|---|
| Brain | `apps/brain_qa/brain_qa/local_llm.py`, `agent_react.py`, persona router |
| Hands | `agent_tools.py` TOOL_REGISTRY + `webfetch.py` + `audio_capability.py` (registry, belum wired) + future `image_gen.py` + `vision_input.py` |
| Memory RAG | `query.py`, `indexer.py`, `read_chunk` tool, BM25 index |
| Memory GraphRAG (roadmap) | `brain_synthesizer.py` (CONCEPT_LEXICON → graph), `knowledge_graph_query.py` (stub) |
| Memory Skill Library (roadmap) | `skill_library.py`, `skill_builder.py`, `skill_modes.py` |

---

## 8. Dua arah aksi lanjutan (dari user)

**Jalur A — Prioritisasi**: pilih 3 kemampuan paling strategis untuk Baby stage SIDIX dengan "wow factor" tapi feasible dalam 3 bulan. Rancang urutan.

**Jalur B — Deep dive**: pilih 1 kemampuan dari 10 di atas, jabarkan sampai level stack teknis, urutan build, estimasi resource, branding IHOS.

Default rekomendasi saya: **Jalur A** — karena roadmap 2026 sudah ada (lihat `docs/SIDIX_ROADMAP_2026.md`), tinggal pilih 3 yang paling berdampak di Baby stage:

1. **Image gen + prompt enhancer Nusantara** (wow factor tinggi, feasible dengan GPU sewa/mitra).
2. **GraphRAG + sanad ranking** (differensiator epistemologis paling kuat).
3. **Python executor untuk matematika+data analysis** (utility tinggi, deps ringan).

Kalau user pilih Jalur B, sebut kemampuan nomor berapa dari tabel section 3.

---

## Sanad

- Diskusi konseptual: user chat 2026-04-19.
- Notes terkait: 161 (konsep AI/LLM + differentiator), 41 (self-evolving), 45-46 (visual AI), 116 (self-learning loop), 153 (sub-agent), 157 (capability audit).
- Paper/model referensi: Stable Diffusion XL (Podell et al. 2023), FLUX.1 (Black Forest Labs 2024), Qwen2.5-Coder (Alibaba 2024), DeepSeek-Coder-V2, HunyuanVideo (Tencent), Mochi 1 (Genmo), CogVideoX (Tsinghua), Voyager (Wang et al. 2023), GraphRAG (Microsoft 2024).
- Framework IHOS: `docs/SIDIX_BIBLE.md`, `brain/public/research_notes/41_sidix_self_evolving_distributed_architecture.md`.
