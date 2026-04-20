# 159 — Identitas SIDIX: 3-Layer Architecture (LLM Generative + RAG + Growth)

Tanggal: 2026-04-19
Tag: [FACT] arsitektur existing; [DECISION] lock identitas anti-misinterpretasi

## Konteks

User menegaskan saat review closure sprint: *"tapi kita bukan cuma mengandalkan pengetahuan corpus kan? kita tetep LLM yang tumbuh dan generative sampai jadi AI Agent."*

Catatan ini mengunci identitas SIDIX supaya agent/sesi berikut tidak salah desain (misalnya menganggap SIDIX = RAG retrieval only, atau menambah tool sebagai pengganti generative model).

## SIDIX adalah 3-layer system

### Layer 1 — LLM generative (otak / core)

**Tanggung jawab:** generate teks/jawaban via prediksi token.

**Komponen:**
- Base model: `Qwen/Qwen2.5-7B-Instruct` (via Hugging Face hub).
- LoRA adapter: `/opt/sidix/sidix-lora-adapter/` (own fine-tuned — dataset SFT custom).
- Runtime: `apps/brain_qa/brain_qa/local_llm.py` → `generate_sidix(prompt, system, max_tokens, temperature)`.
- Quantization: 4-bit NF4 via `BitsAndBytesConfig` (kalau `bitsandbytes` tersedia), fallback fp16.

**Signifikansi:**
- Jawaban HASIL PREDIKSI MODEL, bukan copy-paste corpus.
- Bahkan kalau corpus kosong / search_corpus tidak dipanggil, SIDIX TETAP bisa menjawab dari bobot LoRA + base Qwen — karena ini **LLM generatif**, bukan search engine.
- Style + persona (MIGHAN/TOARD/FACH/HAYFAR/INAN) disampaikan via LoRA dan prompt template.

### Layer 2 — RAG + agent tools (sensory + reasoning)

**Tanggung jawab:** memperkaya konteks generative dengan data live/factual supaya output akurat + terverifikasi (sanad).

**Komponen:**
- RAG via BM25: `search_corpus`, `read_chunk`, `list_sources`. Index di `.data/index/`.
- Agent tools (17 aktif per 2026-04-19): `calculator`, `search_web_wikipedia`, `web_fetch`, `web_search`, `code_sandbox`, `pdf_extract`, `workspace_list/read/write`, `roadmap_*`, `orchestration_plan`.
- ReAct loop: `apps/brain_qa/brain_qa/agent_react.py` — LLM memilih tool → eksekusi → observation → lanjut generate.
- Permission gate di `agent_tools.py` — audit log hash-chain untuk traceability.

**Signifikansi:**
- Loop ReAct yang mengubah SIDIX dari "chatbot" jadi "AI AGENT" — bisa planning multi-step, pakai tool, refine jawaban.
- RAG bukan inti, tapi **pendukung generative**: menyuntikkan FAKTA bertanda `[FACT]` dengan sanad supaya halusinasi turun.
- Tool baru = tambah kapabilitas sensory/motorik agent. Tidak pernah menggantikan LLM.

### Layer 3 — Growth loop (tumbuh autonomous)

**Tanggung jawab:** SIDIX makin pintar seiring waktu tanpa intervensi manual.

**Komponen:**
- Input baru: `learn_agent.py` + 5 connector (arXiv/Wikipedia/MusicBrainz/GitHub/Quran) — fetch ilmu publik harian.
- Gap detection: `knowledge_gap_detector.py` — cari domain dengan confidence rendah.
- Research auto: `autonomous_researcher.py` + `note_drafter.py` → draft research note → approve → `brain/public/research_notes/`.
- Dataset training: `corpus_to_training.py` → JSONL pair.
- Retrain: `auto_lora.py` → trigger Kaggle/GPU training → adapter baru.
- Deploy: replace `/opt/sidix/sidix-lora-adapter/` → `pm2 restart sidix-brain`.
- Logging: `daily_growth.py` 7-fase (SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG).
- Cron: `0 3 * * * curl POST /sidix/grow?top_n_gaps=3` di VPS.

**Signifikansi:**
- Bukan snapshot model statis. SIDIX adalah **makhluk yang belajar**.
- Tiap kuartal, adapter SIDIX lebih baik dari kuartal sebelumnya. Growth compounding.
- Ini fondasi klaim "standing alone" — SIDIX tidak tergantung vendor karena adapter sendiri, training sendiri, data sendiri.

## Salah kaprah yang dihindari

| Salah | Benar |
|---|---|
| "SIDIX cuma RAG" | Layer 1 (generative LLM) adalah intinya. RAG hanya layer 2. |
| "Kalau corpus kosong SIDIX tidak bisa jawab" | Tetap bisa, via bobot LoRA + base Qwen. |
| "Tools menggantikan LLM" | Tools augment; LLM tetap yang reasoning + generate. |
| "SIDIX chatbot biasa" | ReAct loop + multi-step planning = agent, bukan chatbot. |
| "Model SIDIX statis" | Growth loop retrain LoRA periodik — makhluk hidup. |
| "Nambah tool sudah cukup untuk parity GPT" | Tidak. Parity butuh multimodal (layer 1 expanded, bukan tool). |

## Implikasi untuk desain fitur ke depan

1. **Nambah tool (web/code/pdf/audio/image API)** → augment layer 2. Tidak mengubah identitas.
2. **Nambah connector (fetch sumber baru)** → feed layer 3 growth loop.
3. **Image gen / VLM / ASR / TTS** → butuh nambah MODEL di layer 1 (self-host SDXL, Qwen-VL, Whisper, Piper). Ini yang memberi parity dengan GPT/Gemini/Claude multimodal.
4. **Self-evolving** (note 41) — ekstensi layer 3: DiLoCo decentralized training, model merging (DARE/TIES), SPIN.

## Evaluasi kualitas SIDIX

Audit yang benar mengevaluasi **output generatif**, bukan precision RAG:
- Test set pertanyaan dengan `expected_archetype` + `expected_epistemic_tier`.
- Bandingkan jawaban SIDIX vs golden answer — similarity + fact-check.
- Maqashid passes rate, orchestration correctness, persona consistency.
- Lihat `vision_tracker.py` + `/research/*` endpoints untuk metrik per-pillar.

## Sanad

- Kode Layer 1: `apps/brain_qa/brain_qa/local_llm.py`.
- Kode Layer 2: `apps/brain_qa/brain_qa/agent_tools.py`, `agent_react.py`, `agent_serve.py`.
- Kode Layer 3: `learn_agent.py`, `daily_growth.py`, `auto_lora.py`, `corpus_to_training.py`, `knowledge_gap_detector.py`, `autonomous_researcher.py`.
- Referensi user: chat 2026-04-19 — "kita tetep LLM yg tumbuh dan generative sampai jadi AI Agent".
- Related notes: 41 (self-evolving architecture), 116 (self-learning loop), 131 (roadmap belajar sendiri), 133 (transfer pengalaman agent), 157 (capability audit), 158 (closure sprint).
