# 310 — SIDIX Model Independence Path (Fase A→D)

**Tanggal**: 2026-04-30
**Konteks**: User question — "ini semua bisa dikembangin kan? tumbuh bareng SIDIX? nggak ketergantungan sama mereka?"
**Status**: LOCKED — strategy permanen sampai Fase D tercapai

---

## TL;DR

**YES — SIDIX bisa tumbuh punya model sendiri.** Semua model yang dipakai sekarang adalah open-source weights (FLUX.1 Apache 2.0, CogVideoX Apache 2.0, Mochi Apache 2.0, TripoSR MIT, Coqui-TTS MPL/MIT, Qwen2.5-7B Apache 2.0). Bobot tersimpan di VPS, bisa di-fork, fine-tune, distill, eventually replace.

**Pattern Linux**: pakai existing kernel (MINIX) → fork → modify → eventually own innovations. SIDIX jalan jalur ini.

---

## 4 Fase Path Long-term

### Fase A — SEKARANG (Q2 2026)
- **Action**: Pakai open-source models as-is.
- **Infra**: VPS Linux (CPU brain) + RunPod GPU serverless (sewa GPU bare-metal, BUKAN vendor API).
- **Models active**: Qwen2.5-7B + LoRA SIDIX (text), FLUX.1 (image), Coqui-TTS (audio), CogVideoX/SVD scaffold (video), TripoSR (3D).
- **Output**: production stack jalan.

### Fase B — 3-6 bulan (Q3-Q4 2026)
- **Action**: Fine-tune dengan dataset Indonesia/SEA.
- **Output**: SIDIX-Image v1, SIDIX-Voice v1 (Bahasa Indonesia native), SIDIX-Text LoRA tier-2.
- **Diferensiasi**: model lebih ngerti budaya lokal vs FLUX/Coqui vanilla.
- **Compute**: existing RunPod budget + nightly LoRA training pipeline.

### Fase C — 1 tahun (Q2 2027)
- **Action**: Distillation — train smaller model dari teacher Qwen/FLUX.
- **Output**: SIDIX-Image-Mini, SIDIX-Text-Mini bisa run di GPU murah / edge.
- **Manfaat**: lebih cepat, lebih murah, bisa distribute ke user end-device.

### Fase D — 2-3 tahun (2028+)
- **Action**: Research own architecture (kalau ada budget + tim).
- **Output**: SIDIX-original models, kontribusi balik ke open source.
- **Pre-condition**: revenue stream stable + ML research talent recruited.

---

## Yang BENAR Ketergantungan (Honest)

1. **GPU compute** — masih butuh GPU. Sewa RunPod (~$0.69/hour 4090) atau beli sendiri (RTX 4090 ~$1500). Inheren AI butuh compute.
2. **Original model knowledge** — bobot awal datang dari training Big Tech research. Tapi ini "knowledge transfer", bukan ketergantungan vendor — sama seperti Linus baca buku Tanenbaum sebelum tulis Linux.
3. **Updates upstream** — kalau Black Forest Labs rilis FLUX.2 better, kita perlu retrain LoRA. Tapi versi yang sudah download tetap jalan tanpa internet/API call.

## Yang TIDAK ketergantungan

- ❌ NO vendor API (OpenAI/Anthropic/Google/Stability) di pipeline inference
- ❌ NO rate limit dari pihak ketiga
- ❌ NO billing per-request ke vendor
- ❌ NO "service deprecated" risk dari vendor
- ✅ Bobot tersimpan local di VPS
- ✅ Bisa fine-tune kapan saja
- ✅ Bisa distill ke model lebih kecil
- ✅ Bisa modify arsitektur (lihat code mereka, fork, retrain)

---

## Implikasi Aturan Untuk Agent Lain

- ❌ JANGAN suggest pakai OpenAI DALL-E / Midjourney / ElevenLabs API untuk SIDIX inference path
- ❌ JANGAN suggest pakai Anthropic/Google API sebagai backbone reasoning
- ✅ BOLEH pakai vendor API untuk **research/screening one-off** (e.g., generate seed dataset untuk fine-tune SIDIX)
- ✅ BOLEH pakai vendor API di **agent dev tooling** (Claude Code, Cursor) — itu untuk dev process, BUKAN production pipeline SIDIX

## Refer

- `apps/brain_qa/brain_qa/video_gen_scaffold.py` — pattern wire pkrelaian RunPod video endpoint (Fase A → B path)
- `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md` — Phase 0-4 SIDIX bootstrap dirinya sendiri
- `docs/SIDIX_NORTH_STAR.md` — NO VENDOR API rule

---

**Author**: Fahmi Ghani — Mighan Lab / Tiranyx
**License**: MIT
