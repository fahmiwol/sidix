# ADR-001: Own-Stack Inference (No Default Vendor API)

**Status:** Accepted
**Date:** 2026-04-16
**Decider:** Fahmi (solo founder, SIDIX/Mighan)

## Konteks

Platform SIDIX membutuhkan kemampuan inferensi bahasa untuk menjawab pertanyaan,
menghasilkan teks, dan menjalankan ReAct agent loop. Ada dua pendekatan utama:

1. **Vendor API** — memanggil Claude API, OpenAI API, atau sejenisnya per-request
2. **Self-hosted inference** — menjalankan model sendiri di infrastruktur lokal/own-stack

Konteks tambahan:
- SIDIX dibangun sebagai "own-stack platform" dengan prinsip kedaulatan data
- Target pengguna adalah komunitas yang sensitif terhadap privasi dan biaya berulang
- Tim saat ini: 1 orang (solo founder), Kaggle Pro GPU tersedia untuk training
- Model Qwen2.5-7B tersedia sebagai base model open-source yang cocok

## Keputusan

Gunakan **self-hosted Qwen2.5-7B dengan QLoRA adapter** sebagai inference engine utama,
dijalankan melalui FastAPI endpoint lokal di port 8765.

Vendor API (Claude, OpenAI, dll.) **hanya boleh dipanggil jika user secara eksplisit
memintanya** — tidak pernah sebagai default atau fallback otomatis.

## Alasan

1. **Cost control**: Tidak ada biaya API per-token; scalable tanpa billing surprise
2. **Data sovereignty**: Pertanyaan user tidak dikirim ke server pihak ketiga
3. **Own-stack moat**: Diferensiasi kompetitif — SIDIX bisa di-deploy offline/on-premise
4. **Islamic epistemology alignment**: Transparansi penuh atas sumber inferensi sesuai
   prinsip sanad (rantai periwayatan yang dapat diverifikasi)
5. **Kaggle QLoRA feasibility**: Fine-tuning 7B model terbukti feasible di GPU consumer

## Konsekuensi

**Positif:**
- Zero recurring inference cost setelah deployment
- Full control atas model behavior dan persona
- Data tetap on-premise; sesuai regulasi privasi
- Dapat di-deploy di lingkungan air-gapped

**Negatif / Trade-off:**
- Setup lebih lambat: membutuhkan download adapter dan GPU untuk inferensi
- Kualitas awal lebih rendah dari GPT-4/Claude-3; butuh fine-tuning bertahap
- Maintenance beban lebih tinggi (update model, monitoring VRAM, dll.)
- CI/testing membutuhkan MockLLM untuk environment tanpa GPU

## Alternatif yang dipertimbangkan

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| Claude API (Anthropic) | Vendor lock-in, biaya per-token, data keluar dari server user |
| OpenAI API (GPT-4/GPT-4o) | Vendor lock-in, biaya, privasi, tidak sesuai prinsip own-stack |
| Groq / Together.ai | Tetap vendor-dependent, data meninggalkan server user |
| Ollama lokal (tanpa fine-tuning) | Feasible sebagai fallback, tapi tidak ada adaptasi domain Islami |

---
*ADR-001 — Projek Badar Task 62 (G4)*
