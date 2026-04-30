# M5 Fine-tune Prep — Format Data & Pipeline

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Kategori: fine-tuning, lora, m5, sidix
> Status: draft rencana (belum dieksekusi)
> Target: Qwen2.5-7B via LoRA, platform Google Colab Pro+

---

## 1. Posisi M5 dalam Roadmap

```
Brain Pack (Markdown) → RAG pipeline (M1–M4) → Fine-tune prep (M5)
                                                         ↓
                                             QA pairs + memory cards
                                             → instruction format
                                             → SFT Qwen2.5-7B via LoRA
```

M5 bukan pre-training dari nol. Ini SFT (Supervised Fine-Tuning) menggunakan brain pack sebagai data alignment.

---

## 2. Format Instruction Data (ChatML — Qwen2.5 default)

Qwen2.5 menggunakan format **ChatML** untuk instruction tuning:

```
<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
{ideal_answer}
<|im_end|>
```

### System prompt untuk SIDIX

```
Kamu adalah SIDIX, AI yang dibangun di atas prinsip kejujuran (sidq), sitasi (sanad), 
dan verifikasi (tabayyun). Untuk setiap pertanyaan:
1. Jawab berdasarkan fakta yang bisa kamu verifikasi
2. Bedakan antara fakta, interpretasi, dan hipotesis
3. Sebutkan sumber jika tersedia
4. Akui keterbatasan jika tidak tahu
5. Gunakan Bahasa Indonesia yang jelas dan ringkas
```

---

## 3. Konversi QA Pairs → Training Data

Format file sumber: `brain/datasets/qa_pairs.jsonl`
```json
{"id":"qa-001","question":"...","ideal_answer":"...","rubric":"...","tags":[...]}
```

Script konversi (target output: `brain/datasets/finetune_sft.jsonl`):
```python
import json

SYSTEM_PROMPT = """Kamu adalah SIDIX, AI yang dibangun di atas prinsip kejujuran (sidq), 
sitasi (sanad), dan verifikasi (tabayyun). Jawab berdasarkan fakta, bedakan fakta vs hipotesis, 
sebutkan sumber jika ada, dan akui keterbatasan jika tidak tahu."""

def qa_to_chatml(qa):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": qa["question"]},
            {"role": "assistant", "content": qa["ideal_answer"]}
        ],
        "source_id": qa["id"],
        "tags": qa.get("tags", [])
    }

with open("brain/datasets/qa_pairs.jsonl") as f:
    qa_pairs = [json.loads(l) for l in f if l.strip()]

with open("brain/datasets/finetune_sft.jsonl", "w") as f:
    for qa in qa_pairs:
        f.write(json.dumps(qa_to_chatml(qa), ensure_ascii=False) + "\n")

print(f"Converted {len(qa_pairs)} QA pairs to ChatML format")
```

---

## 4. Konversi Memory Cards → Training Data

Memory cards bisa jadi "few-shot examples" dalam system prompt atau training data tersendiri.

Format target (memory cards sebagai alignment data):
```json
{
  "messages": [
    {"role": "system", "content": "Kamu adalah SIDIX..."},
    {"role": "user", "content": "Apa prinsip utama dalam menjawab pertanyaan?"},
    {"role": "assistant", "content": "[konten memory card principle-001 + ihos-002 dll]"}
  ]
}
```

---

## 5. Target Dataset M5

| Sumber | Jumlah saat ini | Target M5 |
|--------|----------------|-----------|
| QA pairs (qa_pairs.jsonl) | 20 pairs | 100–200 pairs |
| Memory cards converted | 0 | 50–100 samples |
| Corpus-derived Q&A | 0 | 200–300 samples |
| **Total SFT dataset** | **~20** | **500+ samples** |

**Cara generate corpus-derived Q&A**: dari setiap chunk di corpus, generate pertanyaan yang jawabannya ada di chunk tersebut → otomatisasi dengan LLM. Ini akan jauh meningkatkan volume tanpa manual labeling.

---

## 6. LoRA Hyperparameter Awal (Qwen2.5-7B)

```python
# Konfigurasi LoRA yang direkomendasikan untuk 7B model
lora_config = {
    "r": 16,                    # rank — mulai rendah, naikkan jika loss tidak konvergen
    "lora_alpha": 32,           # biasanya 2×r
    "target_modules": [         # modul yang akan di-LoRA
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    "lora_dropout": 0.1,
    "bias": "none",
    "task_type": "CAUSAL_LM"
}

training_config = {
    "num_epochs": 3,
    "batch_size": 4,            # dengan gradient accumulation steps = 4 → effective batch = 16
    "learning_rate": 2e-4,
    "max_seq_length": 2048,
    "warmup_ratio": 0.03,
    "lr_scheduler": "cosine"
}
```

Platform: **Google Colab Pro+ (A100 40GB)** — cukup untuk 7B LoRA dengan 4-bit quantization (QLoRA).

---

## 7. Tools yang Diperlukan

```bash
pip install transformers==4.40.0
pip install peft==0.10.0          # LoRA/PEFT
pip install trl==0.8.6            # SFT Trainer
pip install bitsandbytes          # 4-bit quantization (QLoRA)
pip install datasets              # Hugging Face datasets
pip install accelerate            # multi-GPU / Colab A100
pip install wandb                 # experiment tracking (opsional)
```

---

## 8. Evaluasi Setelah Fine-tune

1. **QA pairs regression**: jalankan qa_pairs.jsonl terhadap model fine-tuned → bandingkan hit@k dengan base model
2. **Perplexity**: ukur perplexity pada held-out set dari brain pack
3. **Manual review**: 20–50 jawaban manual dari Fahmi → apakah sudah align dengan IHOS?
4. **SIDIX benchmark custom**: pertanyaan Bahasa Indonesia, pertanyaan Islamic epistemology, pertanyaan teknis — 3 domain diferensiasi

---

## 9. Kapan M5 Dijalankan?

**Prasyarat**:
- [ ] M4 selesai (retrieval quality dipastikan baik)
- [ ] QA pairs ≥ 100 (saat ini: 20, target: 100+)
- [ ] Corpus-derived Q&A ≥ 200 (auto-generated dari chunks)
- [ ] Google Colab Pro+ aktif (untuk A100)

**Estimasi**: bisa dimulai setelah corpus mencapai ~500 samples total.
