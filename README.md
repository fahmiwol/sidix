# SIDIX — Self-Hosted AI Agent Platform

<div align="center">

**Bahasa Indonesia · العربية · English**

*Agen AI serbaguna yang jujur, beretika, dan bisa kamu jalankan sendiri.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Stack: Self-Hosted](https://img.shields.io/badge/stack-self--hosted-green.svg)](#arsitektur)
[![Website](https://img.shields.io/badge/demo-sidixlab.com-blue.svg)](https://sidixlab.com)

</div>

---

## Apa itu SIDIX?

SIDIX adalah platform AI agent yang berjalan **sepenuhnya di lokal / server kamu sendiri** — tanpa bergantung pada API vendor (OpenAI, Claude, Gemini). Dibangun di atas **Epistemic Triad**:

- **Calibrate** — setiap jawaban berlabel jelas: `[FACT]` / `[OPINION]` / `[SPECULATION]` / `[UNKNOWN]`
- **Trace** — setiap klaim ada jejak sumbernya, bisa ditelusuri dan diaudit
- **Scrutinize** — jawaban melewati filter epistemologi sebelum sampai ke pengguna

> Mengapa tiga prinsip ini? Baca: [The Story Behind SIDIX's Epistemic Framework](docs/EPISTEMIC_FRAMEWORK.md)

### Kemampuan utama

| Fitur | Deskripsi |
|---|---|
| 🧠 **RAG berbasis BM25** | Cari dokumen dari corpus lokal, tanpa embedding API |
| 🔄 **ReAct Agent Loop** | Reason → Act → Observe → repeat hingga jawaban siap |
| 🌍 **Trilingual** | Bahasa Indonesia · Arabic · English (+ Javanese, Sundanese) |
| 🎯 **User Intelligence** | Deteksi bahasa, literasi, intent, konteks budaya otomatis |
| ⚖️ **Epistemology Engine** | Maqashid 5-axis, Sanad validator, Constitutional check (4 sifat Nabi) |
| 🛡️ **Safety Policy (G1)** | Anti-injection, anti-toksik, anti-PII, maqashid guard |
| 🔧 **Tool Whitelist** | Calculator, search corpus, Wikipedia fallback, sandbox workspace |
| 📊 **5 Persona** | MIGHAN (Kreatif), TOARD (Perencanaan), FACH (Akademik), HAYFAR (Teknis), INAN (Sederhana) |

---

## Quick Start (5 menit)

### Prasyarat
- Python 3.11+
- Node.js 18+ (untuk UI)
- 4GB RAM (8GB+ untuk inferensi model nyata)

### 1. Clone & install

```bash
git clone https://github.com/fahmiwol/sidix.git
cd sidix
pip install -r apps/brain_qa/requirements.txt
```

### 2. Build index

```bash
cd apps/brain_qa
python -m brain_qa index
```

### 3. Jalankan

```bash
# Backend API (port 8765)
python -m brain_qa serve

# UI (port 3000, terminal terpisah)
cd ../../SIDIX_USER_UI
npm install && npm run dev
```

### 4. Coba tanya

```bash
# CLI
python -m brain_qa ask "Apa itu RAG?"

# Atau buka browser: http://localhost:3000
```

> **Mode default**: Rule-based (tanpa GPU). Untuk inferensi model nyata (Qwen2.5-7B + LoRA adapter), lihat [docs/LAUNCH_V1.md](docs/LAUNCH_V1.md).

---

## Arsitektur

```
┌─────────────────────────────────────────────────────┐
│                   SIDIX_USER_UI                     │
│              (Vite + TypeScript, port 3000)         │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP / SSE
┌───────────────────▼─────────────────────────────────┐
│              SIDIX Inference Engine                  │
│         (FastAPI + Uvicorn, port 8765)               │
│                                                     │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────┐ │
│  │ ReAct    │  │ Epistemology│  │ User Intelligence│ │
│  │ Agent    │  │ Engine     │  │ Module          │ │
│  └────┬─────┘  └────────────┘  └─────────────────┘ │
│       │                                             │
│  ┌────▼──────────────────────────────────────────┐  │
│  │         Tool Registry + Permission Gate        │  │
│  │  search_corpus · calculator · wikipedia · ...  │  │
│  └────┬──────────────────────────────────────────┘  │
│       │                                             │
│  ┌────▼─────────────┐   ┌──────────────────────┐   │
│  │   BM25 Retriever  │   │  Local LLM (optional) │   │
│  │  brain/public/**  │   │  Qwen2.5-7B + LoRA   │   │
│  └──────────────────┘   └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Corpus Knowledge

SIDIX hadir dengan **50+ research notes** yang mencakup:

| Domain | Topik |
|---|---|
| 🤖 AI & ML | RAG, Transformer, Diffusion, LoRA, Fine-tuning |
| 💻 Coding | Python, FastAPI, JavaScript, React, DSA, System Design |
| 🌐 Web | Frontend (HTML/CSS/Vite), Backend, REST API, SQL |
| 📱 Mobile | Flutter, React Native |
| 🎮 Game Dev | Godot 4, Unity, Phaser.js |
| 🕌 Islamic | Epistemologi (sanad, maqashid, ijtihad), Quran preservation |
| 🗣️ Linguistik | Morfologi Indonesia, Arabic (Tajwid, Arud, Nahwu) |
| 🎨 Visual AI | Stable Diffusion, Flux, VLM, fotografi, desain grafis |

---

## Fine-tuned Model

Model SIDIX v1 tersedia di:

- **Dataset SFT**: [huggingface.co/datasets/mighan/sidix-sft-dataset](https://huggingface.co/datasets/mighan/sidix-sft-dataset) (713 Q&A trilingual)
- **Base**: Qwen2.5-7B-Instruct + QLoRA (r=16, 40M trainable params)
- **Training**: 84 menit di Kaggle T4 GPU

---

## Struktur Repo

```
sidix/
├── apps/
│   ├── brain_qa/          # Backend utama (FastAPI + ReAct + RAG)
│   │   └── brain_qa/      # Python package
│   └── vision/            # Vision AI endpoints (stub, WIP)
├── brain/
│   └── public/            # Knowledge corpus (research notes, principles, glossary)
│       ├── research_notes/ # 50+ synthesis notes
│       ├── coding/         # Roadmap topic files
│       ├── principles/     # SIDIX principles
│       └── glossary/       # Istilah teknis + Islam
├── SIDIX_USER_UI/          # Frontend (Vite + TypeScript)
├── docs/                   # Dokumentasi teknis lengkap
├── scripts/                # Utilitas (fetch corpus, benchmark, monitoring)
├── notebooks/              # Kaggle fine-tune notebook
└── jariyah-hub/            # Contoh deploy Ollama + Open WebUI
```

---

## Kontribusi

Kami menyambut kontribusi dari siapapun! Lihat [CONTRIBUTING.md](CONTRIBUTING.md) untuk panduan lengkap.

**Area kontribusi yang paling dibutuhkan:**

1. 📚 **Research notes baru** — tambah topik ke `brain/public/research_notes/`
2. 🧪 **Test cases** — tambah ke `tests/` atau `apps/brain_qa/tests/`
3. 🌐 **Terjemahan** — bantu corpus lebih multilingual
4. 🔧 **Tools baru** — tambah tool ke `agent_tools.py`
5. 🎨 **UI/UX** — improve `SIDIX_USER_UI/`
6. 📖 **Dokumentasi** — perbaiki atau tambah docs

---

## Roadmap

- [x] RAG + BM25 retriever
- [x] ReAct agent loop
- [x] Islamic Epistemology Engine (Maqashid + Sanad + Constitutional)
- [x] User Intelligence (bahasa / literasi / intent / budaya)
- [x] Fine-tune v1 (Qwen2.5-7B QLoRA)
- [x] 50+ research notes corpus
- [ ] GPU inference integration (Qwen2.5-7B + PeftModel)
- [ ] Docker deployment (VPS-ready)
- [ ] Fine-tune v2 (corpus diperluas)
- [ ] Vision AI (LLaVA / Qwen-VL caption pipeline)
- [ ] Streaming SSE fully wired ke epistemology
- [ ] Mobile app

---

## Lisensi

MIT License — bebas dipakai, dimodifikasi, dan didistribusikan. Lihat [LICENSE](LICENSE).

---

<div align="center">

*Dibangun dengan prinsip: sidq · sanad · tabayyun · ikhlas*

</div>
