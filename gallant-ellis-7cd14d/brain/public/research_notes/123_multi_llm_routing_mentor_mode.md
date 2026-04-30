# 123 — Multi-LLM Routing: Mentor Mode untuk SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa
SIDIX didampingi beberapa "mentor" AI yang lebih besar. SIDIX mencoba jawab dulu.
Kalau tidak bisa, routing otomatis ke mentor. SIDIX SELALU belajar dari jawaban mentor.

## Filosofi "Mentor Mode"
```
SIDIX (junior)  →  mencoba jawab
                ↓ jika gagal/confidence rendah
Groq/Gemini/Anthropic (mentor)  →  memberikan jawaban
                ↓ selalu
qna_recorder  →  SIDIX menyimpan jawaban mentor sebagai training data
                ↓ otomatis
BM25 corpus / LoRA fine-tune  →  SIDIX makin pintar
```

User tidak tahu ada routing — SIDIX yang "berbicara", mentor di belakang layar.

## Provider Hierarchy

### 1. SIDIX Local (prioritas)
- **Ollama**: Qwen2.5-7B lokal, gratis, sangat cepat
- **LoRA Adapter**: fine-tuned dari training pairs

### 2. Groq — FREE Tier
- Model: `llama-3.1-8b-instant`
- Speed: **~350 token/detik** (tercepat dari semua cloud)
- Limit: 14,400 req/hari (free)
- Setup: `export GROQ_API_KEY=gsk_...`
- Daftar: https://console.groq.com

### 3. Google Gemini Flash — FREE Tier
- Model: `gemini-1.5-flash-latest`
- Limit: 1,000,000 token/hari (free!), 15 req/mnt
- Cocok untuk: reasoning, analisis panjang
- Setup: `export GEMINI_API_KEY=AIza...`
- Daftar: https://aistudio.google.com

### 4. Anthropic Haiku — CHEAP
- $0.25/1M input, $1.25/1M output
- Max: 600 token per jawaban (hemat)
- Setup: `export ANTHROPIC_API_KEY=sk-ant-...`

### 5. Anthropic Sonnet — SPONSORED tier
- $3/1M input, $15/1M output
- Hanya untuk user yang sudah top up
- Max: 1200 token per jawaban

## Cara SIDIX Belajar dari Mentor

```python
# Setiap jawaban mentor → rekam ke QnA pipeline
record_qna(
    question=prompt,
    answer=mentor_answer,
    session_id=f"mentor_{provider}_{timestamp}",
    model=f"groq_llama3",
    quality=3,  # baseline
)

# Jika mentor answer jauh lebih panjang dari SIDIX answer → quality=4
compare_and_learn(sidix_answer, mentor_answer, prompt, provider)
```

## File
- `apps/brain_qa/brain_qa/multi_llm_router.py`
- `apps/brain_qa/brain_qa/anthropic_llm.py` (diupdate: model_override param)
- Endpoints: `GET /llm/status`, `POST /llm/test`

## Setup VPS (minimal)

```bash
# Groq (gratis, prioritas karena tercepat)
echo "GROQ_API_KEY=gsk_xxx" >> /opt/sidix/apps/.env

# Gemini (gratis, 1M token/hari)
echo "GEMINI_API_KEY=AIzaXXX" >> /opt/sidix/apps/.env

# Install packages
cd /opt/sidix/apps
pip install groq google-generativeai
pm2 restart sidix-brain --update-env
```

## Contoh LLM Status Response
```json
{
  "providers": {
    "ollama":    {"available": false},
    "groq":      {"available": true, "model": "llama-3.1-8b-instant", "cost": "FREE"},
    "gemini":    {"available": true, "model": "gemini-1.5-flash-latest", "cost": "FREE (1M tok/day)"},
    "anthropic": {"available": true, "key_set": true, "model": "claude-3-haiku-20240307"}
  },
  "routing_order": ["ollama", "lora", "groq", "gemini", "anthropic_haiku", "mock"]
}
```

## Keterbatasan
- Groq free tier: 14,400 req/hari (cukup untuk awal)
- Gemini: rate limit 15 req/mnt (throttle jika ramai)
- Semua cloud provider butuh koneksi internet dari VPS
- Jawaban mentor tidak divalidasi secara epistemologi (belum ada validator di router)
- "Belajar dari mentor" baru level heuristik (panjang jawaban) — belum semantic quality score
