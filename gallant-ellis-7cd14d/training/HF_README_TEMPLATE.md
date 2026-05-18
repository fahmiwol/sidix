---
license: mit
base_model: Qwen/Qwen2.5-7B-Instruct
library_name: peft
tags:
  - sidix
  - persona
  - lora
  - indonesian
  - chat
  - assistant
  - dora
  - personality-adapter
language:
  - id
  - en
pipeline_tag: text-generation
---

# SIDIX Persona Adapter v1 — 5 Voice-Distinct Personas at Weight Level

> **Penemu Inovatif Kreatif Digital** — SIDIX is an autonomous, self-evolving AI agent project from [sidixlab.com](https://sidixlab.com).
> This adapter encodes 5 persona voices (UTZ · ABOO · OOMAR · ALEY · AYMAN) at the **weight level** — not prompt acting.

## Apa ini?

Sprint 13 LoRA adapter untuk Qwen2.5-7B-Instruct yang memberikan **5 voice persona distinct** kepada SIDIX. Bedanya dengan persona prompt-based: voice ini **tertanam di adapter weight**, bukan instruction following. Hard to replicate dengan system prompt.

Lahir dari mandate [SIDIX_NORTH_STAR](https://github.com/fahmiwol/sidix/blob/main/docs/SIDIX_NORTH_STAR.md): SIDIX = **Penemu Inovatif Kreatif Digital** — keluar dari pola sistematis AI Agent biasa.

## 5 Persona

| Persona | Karakter | Sample voice marker |
|---|---|---|
| **UTZ** | Creative director, visual-playful | "okeee jadi... metafora-nya gini..." |
| **ABOO** | Engineer praktis, sharp, fail-fast | "stop. data-nya mana? bottleneck-nya..." |
| **OOMAR** | Strategist, framework-driven | "saya breakdown pakai framework. trade-off..." |
| **ALEY** | Researcher methodical, curious | "actually itu menarik dari sudut hipotesis..." |
| **AYMAN** | Pendengar hangat, empathetic | "aku ngerti, kayak gini analogi-nya..." |

Cross-persona discrimination test (training data): gap voice_signature ≥0.43 semua persona — verified offline pre-training.

## Cara pakai

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

base = "Qwen/Qwen2.5-7B-Instruct"
adapter = "Tiranyx/sidix-dora-persona-v1"

tokenizer = AutoTokenizer.from_pretrained(base)
model = AutoModelForCausalLM.from_pretrained(base, torch_dtype="bfloat16", device_map="auto")
model = PeftModel.from_pretrained(model, adapter)

# Generate dengan voice persona-tagged training
messages = [{"role": "user", "content": "Bagaimana cara debug memory leak di Python?"}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
print(tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True))
```

## Training detail

- **Base**: Qwen/Qwen2.5-7B-Instruct
- **Adapter**: LoRA rank-16, target attention modules (`q_proj, k_proj, v_proj, o_proj`)
- **Trainable params**: 10M (0.13% of base)
- **Dataset**: 7,500 synthetic Q&A pairs (1,500/persona, signature_score gated ≥0.5)
- **Training**: 3 epoch, bf16, batch 1 × grad_accum 8, max_seq 512
- **GPU**: NVIDIA RTX A4000 16GB (RunPod COMMUNITY tier)
- **Methodology**: Alpaca-style format dengan persona tag di metadata (BUKAN di prompt) — adapter belajar voice tanpa cue eksplisit

## Sprint 13a / 13b roadmap

- **Sprint 13a (this release)**: plain LoRA — fits 16GB GPU, ships baseline
- **Sprint 13b (planned)**: pure DoRA (Weight-Decomposed LoRA, [Liu et al ICML 2024](https://arxiv.org/abs/2402.09353)) di 24GB GPU — expected +1-2% accuracy
- **Quality gate**: blind A/B test 50 prompts × 5 persona, target ≥80% voice_match

## Ecosystem SIDIX

- **Live UI**: https://app.sidixlab.com (chat dengan SIDIX langsung)
- **Landing**: https://sidixlab.com (filosofi + roadmap)
- **GitHub**: https://github.com/fahmiwol/sidix (full source MIT)
- **Stack**: brain_qa Python FastAPI + Vite TypeScript + LoRA self-hosted, no vendor API
- **Differentiators**: Hafidz Ledger (CAS+isnad chain), Tool Synthesis (Pencipta milestone), 4 Pilar (Decentralized Memory + Multi-Agent + Continuous Learning + Proactive)

## License

MIT — bebas dipakai komersial maupun non-komersial. Atribusi ke SIDIX project (link sidixlab.com) appreciated.

## Provenance

- Sprint 13 documentation: [research note 285-289](https://github.com/fahmiwol/sidix/tree/main/brain/public/research_notes)
- Training journal: 14 iterasi (3 marker tightening + 7 Kaggle abandoned + 4 RunPod) → ship LoRA baseline
- Artifact mirror policy: HF (primary) + Kaggle Models (multi-platform discovery)

---

*Built by [Mighan Lab](https://sidixlab.com) for the SIDIX autonomous AI agent ecosystem. Open contributions welcome.*
