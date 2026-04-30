# Visi, Misi, Nilai (update 2026-04-19)

## Ringkasan
SIDIX adalah **AI agent generative standing-alone** dengan arsitektur modular **Brain + Hands + Memory**, difondasi epistemologi Islam (IHOS, Sanad, Tabayyun, Maqashid) untuk menghasilkan AI yang **jujur, terverifikasi, dan tumbuh mandiri**.

## Visi
Membuat **AI workspace open-source** yang setara produk AI modern multimodal (GPT/Claude/Gemini) **tetapi** dengan 3 keunggulan struktural yang tidak bisa ditiru big tech:
- **Transparansi epistemologis** — 4-label `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` wajib + sanad chain di setiap klaim.
- **Kedaulatan data** — own stack penuh (Qwen+LoRA sendiri, tool sendiri, corpus sendiri, infrastruktur VPS/GPU sendiri — tidak tergantung vendor AI).
- **Spesialisasi kultural** — Nusantara + Islam native (bukan sekadar multilingual translate).

Sekaligus bisa dijalankan lokal/VPS murah, transparan, dan dikembangkan bersama komunitas.

## Arsitektur Brain + Hands + Memory (LOCK)

Analogi tubuh manusia selaras IHOS:

### Brain (LLM inti)
Qwen2.5-7B + LoRA SIDIX. Fungsi: **paham bahasa, bisa reasoning, tahu kapan panggil siapa** — bukan "tahu segalanya". Analog dengan *akal* di IHOS.

### Hands (Tools + model spesialis)
Kapabilitas eksternal yang brain panggil via ReAct:
- Text agent tools: search_corpus, web_fetch, web_search, code_sandbox, pdf_extract, calculator, workspace_*, roadmap_* (17 aktif per 2026-04-19).
- Model spesialis (roadmap): Stable Diffusion XL / FLUX (image), Qwen2.5-VL (vision), Qwen2.5-Coder (coding serius), Whisper.cpp (ASR), Piper (TTS), ffmpeg+image-sequence (video ringan), HunyuanVideo/Mochi (video asli, P2 GPU).
- Analog dengan *sanad* — brain tidak klaim langsung, tapi merujuk alat/sumber valid.

### Memory
Tiga lapis selaras *hifdz* terstruktur:
1. **RAG (BM25)** — corpus lokal terkurasi dengan sanad (157+ research notes).
2. **GraphRAG** (roadmap) — knowledge graph entitas + relasi untuk multi-hop reasoning dan ranking berbasis sanad.
3. **Skill Library** (roadmap à la Voyager) — pola tool-call + prompt + contoh tersimpan + di-reuse.

## Misi
- Menyediakan UI chat yang fokus pada tools yang benar-benar bisa dipakai (bukan cuma chat teks) — chat + image + voice + agent workflow + code execution, SEMUA via own stack.
- Menyediakan agent platform dengan audit log + permission gate + sandbox eksekusi.
- Menyediakan memori knowledge base ter-kurasi (corpus + graph + sanad) agar SIDIX bisa "belajar" tanpa halusinasi.
- Menyediakan integrasi model yang fleksibel **tetapi default self-hosted** (Ollama/llama.cpp + SDXL/FLUX + Qwen2.5-VL + Whisper/Piper). Vendor AI API tidak dipakai di inference pipeline.
- Menumbuhkan model mandiri lewat LearnAgent harian + auto_lora retrain (growth loop Layer 3).

## Nilai / Prinsip
- **Standing alone** — own modules/framework/tools, bukan API vendor AI.
- **Modular** — tiap kapabilitas adalah plugin (model, tool, memory, UI).
- **Epistemic integrity** — 4-label + sanad + maqashid + tabayyun wajib di output.
- **Security-by-default** — akses file/terminal/browser selalu gated + tercatat (hash-chain audit log).
- **Cost-aware** — pengguna bisa pilih mode hemat (CPU-only) atau kualitas tinggi (GPU).
- **Open collaboration** — kontribusi mudah, issue/PR template, roadmap publik di `docs/SIDIX_ROADMAP_2026.md`.
- **Kedaulatan data** — corpus dan model di infrastruktur yang dikuasai.

## Batasan realistis
- **Latih LLM dari nol bukan target.** Target: pakai base model open (Qwen) + LoRA fine-tune own + orchestrator agent + RAG/GraphRAG + tool use.
- **Self-improving autonomous** dibatasi dengan guardrail: validation test set + rollback criteria + human approval untuk code change core (detail di `docs/DEVELOPMENT_RULES.md` Part B).
- **Parity multimodal vs GPT/Claude/Gemini** dijadwalkan di **Child stage Q3 2026** (roadmap 4 stage di `docs/SIDIX_ROADMAP_2026.md`).
- **Scale parameter frontier (100B+)** bukan target — kalah di sini, menang di karakter + epistemic integrity + kedaulatan.

## Dokumen terkait

- `docs/SIDIX_ROADMAP_2026.md` — 4 stage × sprint 2 minggu.
- `docs/DEVELOPMENT_RULES.md` — aturan mengikat agent + SIDIX self-dev.
- `docs/SIDIX_CAPABILITY_MAP.md` — SSoT kapabilitas current.
- `brain/public/research_notes/161_*.md` — konsep AI/LLM + 8 differensiator SIDIX.
- `brain/public/research_notes/162_*.md` — framework Brain+Hands+Memory + peta 10 kemampuan.
- `CLAUDE.md` — section IDENTITAS SIDIX (3-layer: LLM generative + RAG + growth loop).

