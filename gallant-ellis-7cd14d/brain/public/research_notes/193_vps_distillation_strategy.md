# 193_vps_distillation_strategy.md

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
# VPS Distillation Strategy — SIDIX Standing Alone

## Apa
Strategi melatih model distilasi SIDIX langsung di VPS CPU + Kaggle T4 GPU (gratis),
tanpa tergantung cloud API komersial untuk inference.

## Mengapa
SIDIX harus Standing Alone — tidak ada vendor cloud API di inference pipeline.
Model 7B terlalu besar untuk CPU inference real-time (>30s/token).
Solusi: distilasi ke model lebih kecil (0.5B-3B) yang bisa jalan di CPU dengan latency wajar.

## Arsitektur Pipeline
1. Teacher model: Qwen2.5-7B (SIDIX LoRA adapter)
2. Student model: Qwen2.5-0.5B → 1.5B → 3B (progressive scaling)
3. Synthetic data: DeepSeek API (~$2/1000 sample) untuk generate Q&A pairs
4. Training: QLoRA di Kaggle T4 (free 30h/minggu) atau CPU (GPTQ 4-bit)
5. Export: GGUF → Ollama modelfile → deploy ke VPS

## Progressive Scaling Roadmap
- v0.8 (sekarang): 7B LoRA, CPU inference ~30s
- v0.9 (3 bulan): Distilasi ke 1.5B, CPU <5s
- v1.0 (6 bulan): Distilasi ke 3B + RAG hybrid, <3s
- v1.5 (12 bulan): Full agentic, multi-modal
- v2.0 (24 bulan): SIDIX-Native architecture

## Keterbatasan
- Kaggle T4 limit: 30h/minggu, session max 12h
- Model kecil = capacity lebih rendah — perlu curated training data
- Distilasi bukan magic: teacher yang bagus = student yang bagus

## Referensi
- VPS Training Guide (internal doc, 2026-04-24)
- Sprint 8a/8b/8c/8d implementation
