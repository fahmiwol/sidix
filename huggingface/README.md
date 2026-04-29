---
language:
  - id
  - en
  - ar
license: mit
base_model: Qwen/Qwen2.5-7B-Instruct
tags:
  - ai-agent
  - lora
  - qwen
  - self-hosted
  - open-source
  - free
  - rag
  - epistemology
  - indonesia
  - islamic-epistemology
  - local-ai
  - agentic-ai
pipeline_tag: text-generation
library_name: peft
---

# SIDIX LoRA — Free & Open Source AI Agent

**SIDIX** adalah AI agent open source yang berjalan 100% lokal — tidak ada biaya per-query, tidak ada data yang dikirim ke server eksternal.

Model ini adalah **LoRA adapter** yang di-fine-tune di atas [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) menggunakan QLoRA (4-bit quantization, Kaggle T4 GPU).

🔗 **GitHub**: [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix)  
🌐 **Live Demo (Free)**: [app.sidixlab.com](https://app.sidixlab.com)  
📄 **License**: MIT

---

## ✨ Apa yang Membedakan SIDIX?

| Fitur | SIDIX | ChatGPT / Gemini |
|---|---|---|
| Biaya inference | **Gratis** | Per-token billing |
| Data user | **Tetap di server Anda** | Dikirim ke cloud mereka |
| Open source | **Ya, MIT** | Tidak |
| Self-hosting | **Ya** | Tidak |
| Fallback ke LLM lain | **Tidak pernah** | N/A |
| Epistemik labeling | **[FACT]/[OPINION]/[UNKNOWN]** | Tidak ada |

---

## 🏗️ Arsitektur

SIDIX dibangun di atas **IHOS** (*Islamic Holistic Ontological System*) — framework epistemologi yang memetakan konsep keilmuan Islam klasik ke arsitektur AI modern:

- **Sanad** → Citation chain di setiap output (`[FACT]` / `[OPINION]` / `[UNKNOWN]`)
- **Muhasabah** → Self-refinement loop (Niyah → Amal → Muhasabah, CQF ≥ 7.0)
- **Maqashid** → 5 objective filter gates (kehidupan, akal, iman, keturunan, harta)
- **Ijtihad** → ReAct agentic reasoning loop (35 active tools)

---

## 🚀 Quick Usage

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# Load base model with 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
)

base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
)

# Load SIDIX LoRA adapter
model = PeftModel.from_pretrained(base_model, "sidixlab/sidix-lora")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Inference
messages = [
    {"role": "system", "content": "Kamu adalah SIDIX, AI agent yang jujur dan bersumber."},
    {"role": "user", "content": "Jelaskan konsep sanad dalam konteks AI."},
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to(model.device)

with torch.no_grad():
    output = model.generate(**inputs, max_new_tokens=512, temperature=0.7)

print(tokenizer.decode(output[0][inputs.input_ids.shape[1]:], skip_special_tokens=True))
```

### Via Ollama (Recommended for Self-Hosting)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Run SIDIX
ollama run sidixlab/sidix-lora
```

---

## 📊 Training Details

| Parameter | Value |
|---|---|
| Base model | Qwen/Qwen2.5-7B-Instruct |
| Method | QLoRA (4-bit NF4) |
| LoRA rank | 64 |
| LoRA alpha | 128 |
| Target modules | q_proj, v_proj, k_proj, o_proj |
| Training GPU | Kaggle T4 (15GB) |
| Training data | SIDIX corpus (**2,287 documents**, Indonesian/English/Arabic) |
| Research notes | **295 notes** (growing autonomously) |
| Domains | AI/ML, creative writing, coding, brand strategy, content planning |
| Languages | Indonesian (primary), English, Arabic |
| Last updated | 2026-04-29 |

---

## 🎯 5 Personas (LOCKED 2026-04-26)

SIDIX menyesuaikan gaya, kedalaman, dan framing berdasarkan konteks. 5 persona berjalan **paralel** sebagai "5 cortical specialists" untuk topik penting:

| Persona | Voice | Spesialisasi |
|---|---|---|
| **UTZ** | Kreatif, visual | Design thinking, creative direction, inovasi |
| **ABOO** | Engineer, presisi | System design, coding, technical deep-dive |
| **OOMAR** | Strategist, bisnis | Roadmap, GTM, market strategy, execution |
| **ALEY** | Akademik, riset | Literature review, epistemologi, analisis mendalam |
| **AYMAN** | Hangat, komunitas | Daily tasks, percakapan umum, user empathy |

---

## 🛠️ 48 Active Tools (updated 2026-04-29)

SIDIX bukan sekadar chatbot — ia adalah **agent** dengan 48 tools aktif:

```
Knowledge: search_corpus · read_chunk · concept_graph · graph_search
Web:       web_fetch · web_search · pdf_extract · wiki_lookup
Code:      code_sandbox · code_analyze · code_validate · project_map
           shell_run · test_run · scaffold_project · workspace_*
           git_status/diff/log/commit_helper
Creative:  generate_copy · generate_brand_kit · plan_campaign
           generate_ads · generate_thumbnail · generate_content_plan
Image:     text_to_image (SDXL self-hosted via RunPod)
Audio:     text_to_speech · speech_to_text · analyze_audio
Reasoning: debate_ring · llm_judge · muhasabah_refine · orchestration_plan
           self_inspect · social_radar · curator_run
Bisnis:    agency_kit · roadmap_* · prompt_optimizer · calculator
```

### 🤖 Autonomous Developer (Sprint 40–60, 2026-04-29)

SIDIX sekarang bisa **develop dirinya sendiri** secara autonomous:
- Pick task dari queue → 5-persona research fan-out (parallel)
- Generate kode → validate → tulis ke disk → test (pytest + ruff delta-mode)
- Submit PR → notify founder via Telegram → owner approve → merge
- Hafidz Ledger: audit trail setiap iterasi (220+ entries)

---

## 🔒 Privacy & Security

- ✅ Zero data ke server eksternal — semua inference lokal
- ✅ No vendor API key required — tidak ada Groq, Gemini, OpenAI
- ✅ 4-label epistemic tagging — halusinasi dilabel, tidak disembunyikan
- ✅ MIT License — bebas digunakan, dimodifikasi, didistribusikan

---

## 🤝 Contribute

- **Telegram Bot**: [@sidixlab_bot](https://t.me/sidixlab_bot) — kirim pesan → masuk corpus queue
- **GitHub PR**: tambah research note ke `brain/public/research_notes/`
- **Code**: fork [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix)

---

## 📜 Citation

```bibtex
@software{sidix2026,
  title={SIDIX: Free & Open Source AI Agent Built on Islamic Epistemology},
  author={Mighan Lab},
  year={2026},
  url={https://github.com/tiranyx/sidix},
  license={MIT}
}
```

---

*Built by [Tiranyx](https://tiranyx.co.id) · [sidixlab.com](https://sidixlab.com) · "We don't build AI that replaces human judgment. We build AI that makes human judgment more informed."*
