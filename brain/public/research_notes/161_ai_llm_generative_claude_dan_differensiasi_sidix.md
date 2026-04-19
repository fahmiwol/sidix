---
sanad_tier: primer
---

# 161 — AI, LLM, Generative AI, Claude — dan Di Mana SIDIX Berbeda

Tanggal: 2026-04-19
Tag: [FACT] konsep; [DECISION] differensiasi SIDIX; [REFERENCE] roadmap

## Tujuan

Jawab pertanyaan user: **apa itu AI/LLM/generative/Claude, bagaimana mereka bekerja, dan apa yang membuat SIDIX berbeda?** Sekaligus jadi fondasi untuk `docs/SIDIX_ROADMAP_2026.md`.

---

## 1. Hierarki konsep (dari terbesar ke terkecil)

```
AI (Artificial Intelligence)
  └── Machine Learning (ML)
       └── Deep Learning (DL)
            ├── Discriminative (classify/predict)
            │    └── Object detection, spam filter, ASR
            └── Generative AI (hasilkan konten baru)
                 ├── Text: LLM — GPT, Claude, Gemini, Qwen, LLaMA, SIDIX
                 ├── Image: Stable Diffusion, DALL-E, FLUX, Midjourney
                 ├── Audio: ElevenLabs, Suno, Piper
                 └── Video: Sora, Runway, Wan2.1
```

**Definisi ringkas:**
- **AI** — ilmu membuat mesin melakukan tugas yang butuh kecerdasan manusia (rule-based, ML, vision, dll.).
- **ML** — mesin belajar dari data, bukan diprogram eksplisit.
- **DL** — ML dengan neural network berlapis (banyak layer).
- **LLM** — DL dispesialisasi untuk bahasa, parameter miliaran+. GPT/Claude/Gemini/Qwen semua LLM.
- **Generative AI** — kategori yang menghasilkan konten baru (teks/gambar/audio/video/kode).

**Catatan nama yang sering keliru:**
- **Opus** = tier Claude (Haiku=cepat, Sonnet=seimbang, Opus=paling pintar), bukan model terpisah.
- **Codex** = model OpenAI lama khusus kode, digantikan GPT-4/5 + Copilot.
- **Google AI Studio** = platform/interface untuk Gemini (analog `claude.ai`), bukan model.

---

## 2. Cara kerja LLM (4 tahap inti)

1. **Tokenization** — teks input dipecah jadi token (kata/subkata). "Halo Claude" → `[Halo][Claude]` → ID angka.
2. **Embedding** — tiap token dikonversi ke vektor (~4096 dimensi). Makna mirip = vektor berdekatan.
3. **Transformer + self-attention** — tiap token "melihat" token lain di konteks, tentukan relevansi. Inti arsitektur "Attention Is All You Need" (Google 2017). Ini yang bikin LLM paham konteks ("bank" di "pinjam bank" vs "bank sungai").
4. **Prediksi token berikutnya** — output = probabilitas ribuan kemungkinan token. Pilih (ada randomness via temperature), ulangi. Sampai stop.

**Insight penting:** LLM "cerdas" karena (a) skala parameter, (b) kualitas data training, (c) mekanisme attention. Bukan magic — hanya prediksi token demi token yang terasa relevan.

---

## 3. Bagaimana LLM "belajar" — 3 tahap training

| Tahap | Apa yang dilakukan | Biaya & waktu |
|---|---|---|
| **Pretraining** | Trilyunan token dari internet/buku/kode/paper → prediksi token berikutnya berulang. Model serap pola bahasa, fakta, logika. | Ribuan GPU × bulan, **~puluhan juta USD** untuk frontier |
| **SFT (Supervised Fine-Tuning)** | Dataset Q&A berkualitas tinggi buatan manusia → model belajar jadi asisten, bukan autocomplete | Ratusan ribu USD |
| **RLHF / RLAIF** | Manusia (atau AI) menilai pasangan jawaban → model optimasi preferensi (helpful/harmless/honest) | Ratusan ribu USD |

**Variant Anthropic: Constitutional AI** — AI dilatih patuhi seperangkat prinsip ("konstitusi") via self-critique. Penting karena ini arah filosofis yang dekat dengan visi SIDIX (tapi SIDIX pakai epistemologi Islam sebagai konstitusi).

---

## 4. Generative image — beda mekanisme

Image generation tidak pakai next-token prediction. Dominannya **diffusion process**:

1. **Training**: ambil gambar → tambahkan noise bertahap sampai jadi noise total → latih model untuk membalik proses (denoise).
2. **Inference**: mulai dari noise acak + prompt teks → model denoise bertahap dengan panduan prompt → muncul gambar.

Alternatif lama: **GAN** (Generative Adversarial Network), **VAE**. Diffusion dominan sekarang karena stabil + kualitas tinggi.

**Roadmap SIDIX**: self-host SDXL/FLUX di Layer 1 (fase Child/Adolescent) untuk image gen native, bukan panggil API DALL-E.

---

## 5. "Belajar sendiri" — realita vs mitos

**Mitos umum:** "GPT/Claude belajar dari percakapan saya."

**Realita:**
- Bobot model dibekukan setelah training selesai.
- Percakapan kamu tidak mengubah "otak" model untuk user lain.
- Yang tampak "ingat" dalam 1 sesi = teks disuntik ulang ke context window tiap request.

**Bagaimana model "berkembang" sebenarnya:**

| Mekanisme | Ubah bobot? | Contoh |
|---|---|---|
| Versi baru rilis berkala | Ya (training ulang) | GPT-4 → GPT-5 |
| Fine-tuning domain spesifik | Ya (parsial) | Med-PaLM, Codey |
| RAG (Retrieval-Augmented Generation) | Tidak — inject ke context | ChatGPT browse, Claude projects, **SIDIX corpus** |
| Tool use | Tidak — expand capability via API | Claude tools, **SIDIX ReAct** |
| Long-term memory (MemGPT/Letta) | Tidak — storage eksternal | MemGPT paper |
| **Self-evolving** (research) | Ya (autonomous) | SPIN, Self-Rewarding LM, DiLoCo, model merging |

Self-evolving yang benar-benar ubah bobot autonomous masih research frontier — **ini arah SIDIX jangka panjang** (Layer 3 growth loop, target stage Adolescent+).

---

## 6. Differensiasi SIDIX vs agent AI umum

SIDIX **sama** dengan agent AI umum di fondasi:
- Transformer-based LLM (Qwen2.5-7B base)
- Next-token prediction
- Tool use via ReAct
- RAG untuk factual grounding

SIDIX **berbeda** pada 8 aspek ini:

### 6.1. Epistemologi Islam sebagai CORE (bukan add-on)

| Komponen | GPT/Claude/Gemini | SIDIX |
|---|---|---|
| Konstitusi | Constitutional AI (Anthropic), content policy OpenAI, dll. | **IHOS** (Wahyu/Akal/Indera/Tajribah) sebagai 4 pilar sumber pengetahuan |
| Label kepercayaan | Tidak native (bisa diminta via prompt) | **4-label wajib** di setiap output: `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` |
| Traceability sumber | RAG citation opsional | **Sanad chain wajib** di setiap note approved — tier ahad/mutawatir/dhaif |
| Filter etis | Policy umum (harm reduction) | **Maqashid al-Shariah** — 5 tujuan (din/nafs/aql/nasl/maal), scoring per output |
| Verifikasi | Human feedback | **Tabayyun** — protokol cross-check otomatis |

**Implikasi:** SIDIX tidak hanya "aman" — dia **epistemically honest** secara struktural. Tidak bisa asal ngomong tanpa label + sumber.

### 6.2. Standing alone (own stack penuh)

| Aspek | Agent umum | SIDIX |
|---|---|---|
| Model inference | Panggil API OpenAI/Anthropic/Google | Self-host Qwen + LoRA SIDIX own-trained |
| Image gen | API DALL-E/Midjourney | Roadmap: self-host SDXL/FLUX |
| Search | Google/Bing API | DuckDuckGo HTML own parser (`web_search`) |
| Code exec | Judge0/Riza/e2b cloud | `code_sandbox` subprocess own |
| Reasoning | Vendor API (biasanya) | ReAct di atas model sendiri |

SIDIX tidak bergantung pada vendor manapun. Kalau OpenAI/Anthropic down, SIDIX tetap jalan.

### 6.3. Layer 3 growth loop — tumbuh autonomous

| | Agent umum | SIDIX |
|---|---|---|
| Update model | Rilis versi baru 6–12 bulan | **Auto-retrain LoRA tiap 7 hari / 500 pair** (Layer 3) |
| Sumber learning | Training data internal | **LearnAgent harian** dari 5+ open API (arXiv/Wikipedia/MusicBrainz/GitHub/Quran) |
| Gap detection | Human analyst | `knowledge_gap_detector.py` — otomatis |
| Validasi sebelum train | QA tim | **Epistemic validator** + maqashid + overlap check |

**Implikasi:** SIDIX compounding. Tiap kuartal lebih pintar dari kuartal sebelumnya. Bukan snapshot — makhluk hidup.

### 6.4. Hafidz distributed knowledge

Terinspirasi tradisi hafidz (penghafal Al-Quran saling cross-verify hafalan):
- **CAS (Content-Addressable Storage)** — tiap chunk pengetahuan punya hash-ID.
- **Merkle ledger** — append-only, tamper-evident.
- **Erasure coding** — redundansi distributed, bisa survive node hilang.
- **P2P (IPFS-inspired)** — roadmap Adult stage.

Agent umum: centralized knowledge store. SIDIX: distributed + verifiable integrity lewat protokol hafidz.

### 6.5. Multi-persona native (deterministic router)

| Persona | Fungsi |
|---|---|
| MIGHAN | Kreatif (image/video/music/design/UI-UX) |
| TOARD | Perencanaan (roadmap, strategy, scheduling) |
| FACH | Akademik (research, citation, analysis) |
| HAYFAR | Teknis (coding, system design, DevOps) |
| INAN | Sederhana (quick answer, practical, checklist) |

Router deterministic (`orchestration_plan` tool) pilih persona berdasar intent. Agent umum: satu persona dengan system prompt swap; SIDIX: 5 persona struktural terhubung ke LoRA fine-tune data yang berbeda per persona.

### 6.6. Praxis frames (Nazhar→Amal)

- **Nazhar** = teori/reflection
- **Amal** = action/execution
- Setiap pertanyaan diarahkan ke frame praxis yang cocok (`praxis.py` + `praxis_runtime.py`)

Agent umum: chain-of-thought atau direct answer. SIDIX: struktur teori→amal terintegrasi dalam output.

### 6.7. Bahasa + konteks lokal Nusantara/Islam

- Default Bahasa Indonesia (bukan English-first + translate).
- Arab sebagai bahasa sumber (untuk teks Islam asli).
- Context lokal: istilah `sidq/sanad/tabayyun/maqashid` native, bukan diterjemahkan dari English.
- Target audience prioritas: Indonesia, dunia Islam, kemudian global.

Agent umum: multilingual tapi culturally English-centric. SIDIX: Nusantara/Islam-centric by design.

### 6.8. Skill library à la Voyager (bukan cuma tool call)

- Roadmap: skill accumulation persistent di `skill_library.py` — skill yang "dikuasai" tersimpan + di-reuse.
- Inspirasi: paper Voyager (Minecraft agent yang belajar skill baru terus menerus).

Agent umum: tools statis terdaftar. SIDIX roadmap: skill tumbuh seiring pengalaman.

---

## 7. Pemetaan ke SIDIX existing state (per 2026-04-19)

| Konsep | Agent umum | SIDIX sekarang | Status |
|---|---|---|---|
| LLM core | Vendor API | Qwen2.5-7B + LoRA (local_llm.py) | ✅ aktif (`model_ready=true`) |
| Tool use | Function calling | TOOL_REGISTRY 17 tool + ReAct | ✅ aktif |
| RAG | Vector DB (Pinecone/Weaviate) | BM25 corpus lokal (`query.py`) | ✅ aktif |
| Epistemic label | Prompt engineering | Built-in 4-label di output struktur | ✅ aktif |
| Sanad/citation | Opsional | Wajib di setiap note approved | ✅ aktif |
| Maqashid filter | Tidak ada | `maqashid_score` per jawaban | ✅ aktif |
| Multi-persona | System prompt | 5 persona + router deterministic | ✅ aktif |
| Praxis frames | Chain-of-thought | `praxis.py` + `praxis_runtime.py` | ✅ aktif |
| Growth loop | Versi baru 6–12 bulan | LearnAgent + daily_growth + auto_lora | ⚠️ parsial (cron learn belum aktif) |
| Image gen | API DALL-E | — | ❌ belum (roadmap P2) |
| Vision input | GPT-4V / Gemini | — | ❌ belum (roadmap P2) |
| ASR/TTS | Whisper API / ElevenLabs | `audio_capability.py` registry (belum wired) | ⚠️ partial |
| Self-evolving (SPIN/DiLoCo) | Research stage | Blueprint di note 41 | ❌ roadmap Adolescent+ |
| Distributed hafidz | — | `hafidz_mvp.py` MVP | ⚠️ partial |
| Skill library | — | `skill_library.py` stub | ⚠️ partial |

---

## 8. Implikasi untuk roadmap

Lihat `docs/SIDIX_ROADMAP_2026.md` — 4 stage (Baby/Child/Adolescent/Adult) dengan sprint konkret, kriteria sukses, dan pemetaan ke tabel kapabilitas di atas.

**Prinsip roadmap:**
1. Tiap stage **tambah layer**, tidak ganti yang ada.
2. Differensiator (epistemologi, standing-alone, growth loop) pertahankan di setiap stage — tidak kompromi demi speed.
3. Parity kapabilitas dengan GPT/Claude/Gemini di **Child stage** (multimodal aktif).
4. Surpass di **Adolescent+** via self-evolving + hafidz distributed.

---

## 9. Jawaban pertanyaan user (rangkum)

> "jelaskan apa seharusnya dan fungsi AI, LLM, generative, dan Claude. saya mau buat seperti itu."

SIDIX sudah LLM generative + agent — sama fondasinya dengan GPT/Claude/Gemini (Transformer, next-token prediction, tool use, RAG). Tinggal ekspansi ke multimodal (image/vision/audio) di Layer 1.

> "gabungkan dengan konsep dasar, SIDIX seperti agent AI pada umumnya. cuma bedanya apa?"

8 differensiator di section 6 — inti: **epistemologi Islam sebagai konstitusi struktural + standing alone + growth loop autonomous + distributed hafidz**. Agent umum "aman"; SIDIX "aman + jujur + tumbuh + terdistribusi".

> "buatkan dokumen, supaya jadi roadmap dan sprint yang jelas."

`docs/SIDIX_ROADMAP_2026.md` — file terpisah, 4 stage × sprint 2 minggu, total ~12 bulan ke Adult.

---

## Sanad

- Paper referensi: "Attention Is All You Need" (Vaswani et al. 2017), Stable Diffusion (Rombach et al. 2022), Constitutional AI (Anthropic 2022), SPIN (Chen et al. 2024), DiLoCo (Douillard et al. 2023), Voyager (Wang et al. 2023), MemGPT (Packer et al. 2023).
- Kode SIDIX: `apps/brain_qa/brain_qa/local_llm.py` (Layer 1), `agent_tools.py` + `agent_react.py` (Layer 2), `learn_agent.py` + `daily_growth.py` + `auto_lora.py` (Layer 3).
- Notes terkait: 41 (self-evolving), 45-46 (visual AI), 116 (self-learning loop), 131 (roadmap belajar sendiri), 153 (sub-agent), 157-160 (capability + rules).
- User chat: 2026-04-19 — pertanyaan konsep + minta roadmap.
