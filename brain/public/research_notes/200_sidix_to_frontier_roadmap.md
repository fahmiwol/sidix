# 200 — Roadmap Teknis SIDIX: Dari v0.8 ke Model Frontier

**Tanggal**: 2026-04-24
**Status**: [OPINION] Gap analysis + rencana realistis berdasarkan resource yang tersedia
**Sanad**: Dibuat berdasarkan audit kapabilitas Note 157, pipeline Note 195, identitas Note 159, North Star docs/NORTH_STAR.md, dan literatur fine-tuning LLM 2024-2026.

---

## Konteks: Apa yang Dimaksud "Frontier" untuk SIDIX

"Frontier" bukan berarti setara GPT-5 atau Claude Opus dalam semua dimensi — itu tidak realistis dengan resource solo founder. Yang dimaksud di sini adalah SIDIX yang **frontier di niche-nya**:

1. **Frontier untuk Bahasa Indonesia + Islam**: SIDIX lebih baik dari model generalis di topik ini
2. **Frontier untuk epistemic honesty**: tidak ada model mainstream yang konsisten pakai 4-label + sanad
3. **Frontier untuk agentic local**: ReAct + 38 tools + self-hosted tanpa vendor dependency
4. **Frontier untuk standing alone**: inference tanpa panggil API luar

Ini adalah strategi "be the best at something specific" bukan "beat everyone on everything."

---

## Gap Analysis: Kondisi Sekarang vs Target

### Tabel Gap Komprehensif

| Capability | Frontier Model (Claude/GPT-4) | SIDIX Sekarang | Gap Level | Cara Tutup | Estimasi Effort |
|-----------|-------------------------------|----------------|-----------|------------|----------------|
| **Pre-training base** | Triliunan token own data | Qwen2.5-7B (sudah jalan) | ✅ Cukup | Fine-tune saja | Done |
| **SFT pairs volume** | 100K–1M+ HQ pairs | ~0 pairs (baru mulai) | BESAR | Jariyah + synthetic gen | 3 bulan |
| **SFT pairs quality** | Expert-curated | Belum ada | BESAR | Curation pipeline | 3 bulan |
| **RLHF/DPO alignment** | RLHF + Constitutional AI | Belum ada | BESAR | DPO dengan Jariyah | 3–6 bulan |
| **Context window** | 128K–1M token | 4K–8K efektif | SEDANG | Qwen2.5-72B nanti / flash attn | 6 bulan |
| **Reasoning (CoT)** | Systematic CoT built-in | Belum sistematis | SEDANG | Tambah CoT prompt + training | 1 bulan |
| **Tool use format** | Structured JSON strict | Ada tapi inconsistent | KECIL | Fix format + validate | 2 minggu |
| **Multimodal** | Vision + Audio native | Stub belum live | BESAR | Butuh GPU + CLIP/Whisper | 6–12 bulan |
| **Safety/alignment** | Constitutional AI penuh | 4-label epistemik parsial | SEDANG | Perluas 20 prinsip + CAI loop | 3–6 bulan |
| **Inference speed** | <1s per response | ~30s (7B CPU saat ini) | BESAR | Distilasi ke 1.5B GGUF | 2 bulan |
| **Knowledge freshness** | Real-time (web access) | Static corpus + LearnAgent | SEDANG | LearnAgent sudah ada, fix cron | 2 minggu |
| **Bahasa Indonesia** | Generalis, tidak optimal | Qwen2.5 decent + corpus SIDIX | SEDANG | SFT pairs ID-native | 3 bulan |
| **Islam/fiqh knowledge** | Ada tapi tidak mendalam | Research notes 150+ Islam | SEDANG | Jariyah pairs Islam-specific | 3 bulan |
| **Memory jangka panjang** | Terbatas pada context | Corpus search saja | SEDANG | pgvector + user memory | 3–4 bulan |
| **Self-improvement** | Tidak ada (static) | Growth loop konsep | SEDANG | LearnAgent + auto-LoRA aktifkan | 4 bulan |
| **Benchmark score** | MMLU >90%, HumanEval >85% | Belum diukur | UNKNOWN | Buat SIDIX-Eval dulu | 1 bulan |

### Analisis Gap Terbesar

**Gap #1: SFT Data (paling kritis saat ini)**
SIDIX belum punya satu pun Jariyah pair berkualitas yang sudah dipakai untuk fine-tuning. Tanpa ini, model hanya Qwen2.5 generalis yang berbicara Bahasa Indonesia — bukan SIDIX yang berkepribadian, jujur secara epistemik, dan kompeten di Islam.

Efek: model tidak mengenali dirinya sebagai SIDIX, tidak konsisten pakai 4-label, tidak punya "karakter" yang membedakan dari ChatGPT.

**Gap #2: Alignment / DPO**
Bahkan dengan SFT yang baik, tanpa alignment SIDIX bisa hallucinate dengan percaya diri, bisa tidak konsisten dalam nilai. DPO adalah teknologi yang sekarang sudah mature dan accessible — tidak ada alasan untuk tidak implementasi.

**Gap #3: Inference Speed**
30 detik per response = product tidak usable. Pengguna akan pergi setelah 10 detik. Distilasi ke 1.5B GGUF adalah solusi jangka pendek yang sudah punya pipeline (Note 195).

**Gap #4: Multimodal**
User expect bisa kirim gambar ke AI. Ini gap strategis yang visible. Butuh GPU — masuk Phase 3.

---

## Phase Roadmap: Realistis dengan Resource Solo Founder

### Phase 0 — Foundation Fix (SEKARANG — 2 minggu)

Sebelum apapun, perbaiki hal-hal yang broken:

**P0.1: Fix LearnAgent Cron**
LearnAgent sudah ada tapi cron tidak jalan karena env var token missing. Fix ini → corpus tumbuh otomatis tiap hari.
```bash
# VPS: cek PM2
pm2 logs sidix-brain | grep learn
# Fix: pastikan OPENAI_API_KEY (atau equiv) tersedia di env
```

**P0.2: Structured Tool Call Format**
Format tool call SIDIX saat ini bergantung regex parsing. Standardize ke JSON:
```python
# agent_react.py: pastikan model generate dalam format ini
{
  "thought": "Saya perlu mencari informasi terkini...",
  "action": "web_search",
  "action_input": {"query": "harga emas Indonesia April 2026"}
}
```

**P0.3: Enable Flash Attention di Training**
Tambah `attn_implementation="flash_attention_2"` ke QLoRA training script → kurangi OOM error di Kaggle T4.

**P0.4: SIDIX-Eval Baseline**
Buat 100 pertanyaan evaluasi: 40% umum (pengetahuan, reasoning), 40% Islam/Indonesia, 20% coding/math. Jalankan evaluasi saat ini → baseline score. Semua improvement selanjutnya diukur terhadap ini.

---

### Phase 1 — Foundation Quality (sekarang — 3 bulan)

**Tujuan**: SIDIX yang bisa dipakai dan punya identitas.

#### P1.1: Kumpulkan 500 Jariyah Pairs

Format setiap pair:
```json
{
  "messages": [
    {"role": "system", "content": "Kamu adalah SIDIX..."},
    {"role": "user", "content": "<pertanyaan>"},
    {"role": "assistant", "content": "<jawaban dengan 4-label + sanad>"}
  ],
  "metadata": {
    "domain": "islam_fiqh",
    "difficulty": "medium",
    "source": "manual_jariyah",
    "rating": 5
  }
}
```

Sumber pairs:
- **Manual (paling berkualitas)**: tulis langsung 50-100 pairs untuk domain paling kritis (fiqh, akidah, bahasa Indonesia, coding Python)
- **Synthetic generation**: gunakan DeepSeek API ($2/1000 pairs) → generate 400+ pairs dari research notes SIDIX sebagai konteks
  ```python
  # prompt ke DeepSeek:
  # "Berdasarkan materi berikut: [konten note], buat 5 pertanyaan-jawaban 
  #  dalam gaya SIDIX (pakai label epistemik, sertakan sanad)"
  ```
- **Corpus-derived**: ambil konten research notes → buat Q&A otomatis → manual review

Strategi distribusi domain:
```
Islam/fiqh/akidah: 150 pairs (30%)
Bahasa Indonesia/sastra/budaya: 100 pairs (20%)  
Science/math/logika: 100 pairs (20%)
Coding/engineering: 75 pairs (15%)
Sejarah/geografi Indonesia: 75 pairs (15%)
```

#### P1.2: SFT Training Pertama

```python
# Environment: Kaggle T4 (16GB VRAM gratis 30h/minggu)
# Model: Qwen2.5-1.5B-Instruct (bukan 7B dulu — lebih cepat iterate)
# Method: QLoRA, r=16, alpha=32, target_modules all linear

from trl import SFTTrainer
from peft import LoraConfig

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=jariyah_dataset,
    peft_config=lora_config,
    max_seq_length=2048,
    dataset_text_field="text",
)
```

**Evaluasi setelah SFT**: jalankan SIDIX-Eval → ukur improvement vs baseline.

#### P1.3: Distilasi 1.5B untuk VPS

Gunakan pipeline dari Note 195:
1. Qwen2.5-7B (teacher, di Kaggle) → generate responses untuk 10K prompts
2. Qwen2.5-1.5B (student) → SFT pada teacher responses
3. Export ke GGUF Q4_K_M → ~1GB, <5s per response di CPU

**Target**: latency <5 detik di VPS CPU saat ini. Ini mengubah SIDIX dari "terlalu lambat" menjadi "usable."

#### P1.4: CoT Prompting Sistematis

Tambah ke system prompt SIDIX:
```
Untuk pertanyaan yang memerlukan analisis mendalam atau perhitungan:
1. Uraikan pemikiranmu langkah demi langkah sebelum menjawab.
2. Gunakan format: "Mari kita pikirkan ini: [reasoning] → [kesimpulan]"
3. Verifikasi logika sebelum memberikan jawaban akhir.
```

---

### Phase 2 — Alignment dan Evaluasi (3–6 bulan)

**Tujuan**: SIDIX yang aligned dengan nilai Islam dan epistemic honesty secara konsisten.

#### P2.1: Constitutional AI SIDIX

Implementasi 20 prinsip konstitusi SIDIX (detail di Note 201 + `sidix_constitution.py`).

Pipeline critique-revise:
```python
def constitutional_ai_pipeline(prompt: str, response: str) -> str:
    """
    Jalankan critique-revise loop berdasarkan konstitusi SIDIX.
    Output: revised response yang lebih aligned.
    """
    critique = critique_response(response)  # Note 201
    if critique == "OK":
        return response
    revised = revise_response(response, critique)
    return revised
```

**Self-improvement dataset**: simpan semua (prompt, original, revised) → training data untuk DPO.

#### P2.2: DPO Training

Dari Constitutional AI pipeline, kita punya preference data:
```python
# Format DPO dataset
{
  "prompt": "<user question>",
  "chosen": "<revised response yang lebih aligned>",
  "rejected": "<original response sebelum revisi>"
}
```

Training DPO dengan `trl`:
```python
from trl import DPOTrainer, DPOConfig

dpo_config = DPOConfig(
    beta=0.1,           # temperature for DPO loss
    learning_rate=1e-6,
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
)

trainer = DPOTrainer(
    model=sft_model,      # model yang sudah di-SFT
    ref_model=ref_model,  # SFT model sebagai reference
    args=dpo_config,
    train_dataset=preference_dataset,
)
```

**Target setelah DPO**: pengurangan hallucination >50%, konsistensi 4-label >90%.

#### P2.3: Reward Model Sederhana (opsional)

Jika DPO kurang, build reward model:
```python
# Classifier kecil (BERT-based): input = (prompt + response) → score 0-10
# Training data: Jariyah pairs dengan rating manual
# Gunakan sebagai scoring function untuk response selection
```

#### P2.4: SIDIX-Benchmark Publik

Buat dan publikasikan benchmark evaluasi SIDIX:
- 200 pertanyaan dalam 10 kategori
- Include soal bahasa Indonesia asli, fiqh muamalah, matematika Indonesia, coding Python
- Automated scoring untuk sebagian besar, human review untuk subjective

Ini bisa jadi kontribusi komunitas + differensiator ("satu-satunya benchmark AI untuk konteks Indonesia-Islam").

---

### Phase 3 — Scale dan Multimodal (6–12 bulan)

**Tujuan**: SIDIX yang multimodal dan bisa handle task kompleks.

#### P3.1: Upgrade ke Qwen2.5-7B Full Fine-tune

Setelah punya 2000+ Jariyah pairs + preference data:
- RunPod A100 80GB: $1.5/jam
- Full fine-tune (bukan QLoRA): ~8-16 jam → $12-24
- Hasilnya: model 7B yang benar-benar SIDIX, bukan hanya Qwen+adapter tipis

**Cost estimate untuk seluruh Phase 3**:
```
SFT 7B (A100, 8h): $12
DPO 7B (A100, 4h): $6  
Iterasi (3×): $54
Total compute: ~$72 — sangat terjangkau
```

#### P3.2: Multimodal — Vision

**CLIP + LLaVA pattern**:
```
[Image] → CLIP Encoder → Image Embeddings
                                ↓
[Text Prompt] → Tokenizer → Text Embeddings → [Concat] → LLM → Response
```

Tools yang tersedia:
- `Qwen2-VL`: Alibaba sudah release vision variant → bisa langsung fine-tune
- `LLaVA-1.6`: open-source, dapat dilatih dengan dataset custom

**SIDIX use case**: user kirim foto bangunan bersejarah Indonesia → SIDIX identifikasi dan jelaskan sejarahnya.

#### P3.3: Voice (TTS + STT)

Sudah ada stub di SIDIX. Implementasi:
- **STT**: `faster-whisper` (CPU-friendly, 6× lebih cepat dari Whisper original)
- **TTS**: Coqui TTS dengan model Bahasa Indonesia

Target: voice chat dalam Bahasa Indonesia yang natural.

#### P3.4: Persistent Memory (pgvector)

Saat ini SIDIX tidak ingat percakapan sebelumnya (tanpa context window). Implementasi:
```sql
-- PostgreSQL + pgvector extension
CREATE TABLE user_memories (
    id UUID PRIMARY KEY,
    user_id TEXT,  -- anonymized
    content TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP,
    importance FLOAT
);

-- Query: ambil memories paling relevan untuk context
SELECT content FROM user_memories
WHERE user_id = $1
ORDER BY embedding <-> query_embedding LIMIT 5;
```

---

### Phase 4 — Native Model (12–24 bulan)

**Tujuan**: SIDIX yang benar-benar native, tidak bergantung pada model asing.

#### P4.1: SIDIX-Native Tokenizer

Buat tokenizer yang dioptimalkan untuk:
- Bahasa Indonesia: kata-kata seperti "mempermasalahkan", "ketidakhadiran" harus 1 token
- Bahasa Arab: aksara Arab dengan harakat
- Jawa/Sunda/Minangkabau: bahasa daerah Nusantara

Menggunakan SentencePiece:
```python
import sentencepiece as spm

spm.SentencePieceTrainer.train(
    input='corpus_indonesia_arab.txt',
    model_prefix='sidix_tokenizer',
    vocab_size=65536,
    character_coverage=0.9999,  # untuk coverage karakter Arab
    model_type='bpe',
    pad_id=0, unk_id=1, bos_id=2, eos_id=3
)
```

#### P4.2: Continual Pre-training

Tidak pre-train dari scratch, tapi **continual pre-training**:
- Ambil Qwen2.5-7B
- Lanjutkan pre-training dengan corpus Indonesia besar (Common Crawl ID, Wikipedia ID, buku)
- Budget: ~100 GPU-hours (≈ $150 di A100)

Ini jauh lebih feasible dari full pre-training ($1.3M) tapi memberikan signifikan improvement untuk Bahasa Indonesia.

#### P4.3: Constitutional AI Penuh

Setelah punya banyak data dan compute:
- Automated critique-revise-train loop berjalan setiap minggu
- SIDIX menilai dan merevisi outputnya sendiri
- Distribusi knowledge ke model baru via preference learning

---

## Resource Planning: Realistis dan Akurat

### Compute Budget

| Task | Platform | Jam | Biaya | Frekuensi |
|------|----------|-----|-------|-----------|
| SFT 1.5B (QLoRA) | Kaggle T4 | 2h | Gratis | Per 100 pairs baru |
| SFT 7B (QLoRA) | Kaggle T4 | 8h | Gratis | Per 500 pairs |
| DPO 1.5B | Kaggle T4 | 1h | Gratis | Bulanan |
| DPO 7B | RunPod A100 | 4h | $6 | Per quarter |
| Full fine-tune 7B | RunPod A100 | 8h | $12 | Per 6 bulan |
| GGUF export | Kaggle CPU | 1h | Gratis | Setiap release |

**Budget total Phase 1 (3 bulan)**: ~$0 (semua Kaggle gratis)
**Budget total Phase 2 (6 bulan)**: ~$30 (beberapa run di RunPod)
**Budget total Phase 3 (12 bulan)**: ~$200 (lebih banyak RunPod + multimodal training)

### Data Budget

| Sumber | Volume | Biaya | Kualitas |
|--------|--------|-------|---------|
| Manual Jariyah pairs | 50-100 pairs | Waktu saja | Sangat Tinggi |
| Synthetic (DeepSeek API) | 10K pairs | $20 | Tinggi |
| Corpus-derived Q&A | 5K pairs | $5 API | Sedang |
| Constitutional AI revisions | 50K+ pairs | Compute saja | Tinggi |

**Total data budget Phase 1**: $25

### VPS Requirements

Model saat ini (7B): tidak bisa inference di CPU dengan latency acceptable.

Setelah Phase 1 distilasi (1.5B GGUF Q4_K_M):
```
RAM: 2GB (bukan 16GB)
CPU: cukup 4 cores
Latency: 3-5 detik per response (acceptable)
```

VPS saat ini sudah cukup untuk model yang didistilasi.

---

## Metrik Keberhasilan Per Phase

### Phase 1 (setelah 3 bulan)

| Metrik | Baseline | Target |
|--------|---------|--------|
| Latency inference | ~30s | <5s |
| Jariyah pairs | 0 | 500+ |
| SIDIX-Eval score | TBD | +20% dari baseline |
| 4-label consistency | <30% | >70% |
| Identitas SIDIX konsisten | Tidak | Ya |

### Phase 2 (setelah 6 bulan)

| Metrik | Phase 1 | Target |
|--------|---------|--------|
| Hallucination rate | Tinggi | Turun 50% |
| DPO preference score | Belum ada | >70% vs non-aligned |
| Benchmark Indonesia | Belum ada | Launch publik |
| RLAIF loop | Belum ada | Jalan otomatis |

### Phase 3 (setelah 12 bulan)

| Metrik | Phase 2 | Target |
|--------|---------|--------|
| Image understanding | Tidak ada | Basic captioning/VQA |
| Voice interface | Stub | Fungsional ID |
| Memory persistence | Tidak ada | Recall >80% |
| Concurrent users | 1 | 10+ |

---

## Risiko dan Mitigasi

### Risiko 1: Kaggle T4 tidak cukup untuk model yang ingin dilatih

**Mitigasi**: selalu dimulai dari 1.5B (bukan 7B). Kaggle T4 bisa handle 1.5B QLoRA dengan mudah. Ketika butuh 7B penuh, gunakan RunPod ($12 per run) — itu budget yang sangat kecil.

### Risiko 2: Data Jariyah tidak berkualitas → model memburuk

**Mitigasi**: implementasi data quality filter sebelum training:
```python
def quality_check(pair: dict) -> bool:
    response = pair["messages"][-1]["content"]
    checks = [
        len(response) >= 100,  # tidak terlalu pendek
        len(response) <= 3000,  # tidak terlalu panjang
        any(label in response for label in ["[FACT]", "[OPINION]", "[SPEC"]),  # ada label epistemik
        not response.count("saya tidak tahu") > 3,  # tidak over-hedge
    ]
    return all(checks)
```

### Risiko 3: DPO training tidak stabil

**Mitigasi**: mulai dengan β=0.1 (conservative). Monitor KL-divergence selama training. Jika diverge, naikkan β. TRL library sudah punya banyak safeguard.

### Risiko 4: Competitor meluncurkan model Indonesia yang lebih baik

**Mitigasi**: SIDIX tidak menang di pure capability (parameter count) — menang di:
- Epistemic honesty (tidak ada yang konsisten seperti ini)
- Islam + Nusantara native (tidak ada yang dalam seperti ini)
- Self-hosted (privasi — ini differensiator yang tidak bisa ditiru cloud provider)
- Community ownership (roadmap terbuka, kontributor)

### Risiko 5: Solo founder burnout

**Mitigasi**: setiap phase hanya 2-3 task prioritas. Tidak perlu semua fitur sekarang. MVP yang berjalan > feature-rich yang tidak selesai. Roadmap ini bisa dikerjakan part-time.

---

## Urutan Prioritas Eksekusi (Next 30 Hari)

1. **Minggu 1**: Fix LearnAgent cron + structured tool call format + SIDIX-Eval 100 pertanyaan
2. **Minggu 2**: Mulai kumpulkan 50 Jariyah pairs manual (domain: Islam fiqh + bahasa Indonesia)
3. **Minggu 3**: Setup Kaggle notebook untuk QLoRA training + jalankan first training run (1.5B, 50 pairs)
4. **Minggu 4**: Evaluasi model pertama vs baseline + pipeline synthetic data generation (DeepSeek API)

Hasil yang diharapkan setelah 30 hari: SIDIX pertama yang punya identitas dan bisa menjawab dengan 4-label secara lebih konsisten. Latency masih lambat (butuh distilasi di bulan 2), tapi identity sudah ada.
