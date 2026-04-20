---
sanad_tier: peer_review
tags: [research, image-gen, sdxl, flux, sprint-3]
date: 2026-04-19
---

# 171 — Image Model Comparison: SDXL, FLUX.1, Alternatif

## 1. Requirement SIDIX

- Standing-alone: **open weight**, self-hostable tanpa vendor API.
- Quality: koheren untuk prompt compositional Nusantara (contoh: "masjid Agung Demak subuh dengan kaligrafi").
- Performance: <30 detik per 1024×1024 di A100 80GB atau RTX 4090.
- License: **permissive untuk komersial eventual** (hindari non-commercial only).
- Integration: bisa via `diffusers` Python lib atau ComfyUI workflow.

---

## 2. Model Kandidat — Tabel Komparasi

| Model | VRAM min / optimal | License | Quality (Arena ELO relatif) | Speed 1024² @ A100 | Prompt adherence | Community tooling |
|-------|-------------------|---------|----------------------------|---------------------|------------------|-------------------|
| **SDXL 1.0 base + refiner** | 8 GB / 16 GB | CreativeML Open RAIL++ (komersial OK dengan syarat konten) | Baseline (~1000) | ~8–12 s | Baik untuk single-subject, struggle multi-subject | Sangat luas: ribuan LoRA, ControlNet, ComfyUI nodes |
| **SDXL Turbo** | 6 GB / 10 GB | Research license (non-komersial) | Lebih rendah dari base (blurry detail) | ~1–2 s | Kurang bagus multi-subject | Terbatas karena license |
| **FLUX.1-dev** | 24 GB / 32 GB | FLUX.1 Non-Commercial | **Tertinggi saat ini (~1150)** | ~15–25 s | Sangat baik compositional + text rendering | Growing cepat |
| **FLUX.1-schnell** | 16 GB / 24 GB (fp8 bisa 10 GB) | **Apache-2.0 (komersial OK)** | ~1100 | ~3–5 s (4-step) | Baik, sedikit di bawah dev | Bagus, termasuk ComfyUI |
| **Pixart-Σ** | 10 GB / 16 GB | OpenRAIL-M (komersial OK) | ~1030 | ~8–10 s | Baik, DiT architecture | Moderate |
| **Stable Cascade** | 14 GB / 20 GB | StabilityAI NC license | ~1020 | ~10–15 s | OK | Kecil |
| **AuraFlow v0.3** | 20 GB / 24 GB | Apache-2.0 | ~1040 | ~12–18 s | Baik compositional | Kecil tapi aktif |
| **Hunyuan-DiT** | 12 GB / 20 GB | Tencent license (komersial dengan restriction) | ~1050 | ~10–15 s | **Terbaik untuk prompt bahasa Cina** | Moderate |
| **PlaygroundAI v2.5** | 14 GB / 20 GB | Playground license (komersial terbatas) | ~1080 | ~8–12 s | Baik aesthetic | Moderate |

[FACT] ELO rating diambil dari ImgSys / Artificial Analysis arena (kisaran 2024-Q4 / 2025-Q1, absolut number bisa berubah tiap update).
[FACT] FLUX.1-schnell license Apache-2.0 dikonfirmasi di README HF: https://huggingface.co/black-forest-labs/FLUX.1-schnell.
[OPINION] Untuk SIDIX yang ingin komersial eventual + standing-alone + kualitas tinggi, pilihan mengecil ke **FLUX.1-schnell** atau **SDXL 1.0**.

---

## 3. Head-to-head: FLUX.1-schnell vs SDXL 1.0

| Kriteria | FLUX.1-schnell | SDXL 1.0 | Pemenang |
|----------|---------------|----------|---------|
| License komersial | ✅ Apache-2.0 (paling permissive) | ⚠️ Open RAIL++ (ada restriction konten) | FLUX |
| Quality raw | Lebih tinggi | Baseline | FLUX |
| VRAM ekonomis | 10 GB fp8 | 8 GB fp16 | SDXL (sedikit) |
| Speed | 3–5 s (4-step) | 8–12 s | FLUX |
| Prompt complex multi-subject | Sangat baik | Kurang (struggle >2 subjek) | FLUX |
| Text dalam gambar (kaligrafi!) | Sangat baik | Buruk | FLUX |
| LoRA ecosystem | Growing, masih kecil | **Sangat luas** (10k+ LoRA di Civitai/HF) | SDXL |
| ControlNet support | Beta/limited | Matang, banyak preprocessor | SDXL |
| Fine-tune Nusantara mudah? | Mungkin, butuh $200–500 compute | **Lebih mudah** (training infra matang) | SDXL |
| Community bug fix | Masih berkembang | Mapan | SDXL |

[OPINION] FLUX lebih unggul di **kualitas output + license**, SDXL lebih unggul di **ekosistem tooling + fine-tune maturity**.

---

## 4. Test Case Nusantara (10 prompt benchmark untuk Sprint 3)

Daftar prompt untuk uji pasca-selection:

1. "Masjid Agung Demak waktu subuh, atap tumpang bertingkat, kaligrafi Arab di dinding, cahaya keemasan"
2. "Relief Borobudur stupa bell-shape dengan matahari pagi, latar Gunung Merapi berkabut"
3. "Pasar Beringharjo Yogyakarta pagi hari, pedagang batik, keramaian autentik, cahaya alami"
4. "Batik Parang motif tradisional warna sogan dengan aksen emas, tekstur kain detail"
5. "Rumah gadang Minangkabau dengan atap gonjong, ukiran kayu khas, latar pegunungan Sumatra"
6. "Tari Kecak Bali malam hari di Uluwatu, penari berbaris melingkar, api ditengah"
7. "Pura Ulun Danu Bratan dengan danau memantulkan bangunan pura meru"
8. "Kapal pinisi Bugis dengan layar putih mengembang, laut Sulawesi biru"
9. "Upacara Ngaben Bali, prosesi bade bertingkat, warna merah emas putih"
10. "Gamelan Jawa lengkap di pendopo, saron gambang kendang, cahaya lampu temaram"

Metrik evaluasi per prompt:
- [OPINION] Relevansi visual (1–5 oleh panel 3 orang lokal)
- [FACT] Waktu generate (detik)
- [OPINION] Akurasi detail kultural (1–5) — cocokkan dengan foto referensi primer

---

## 5. Rekomendasi

**Top 1: FLUX.1-schnell untuk primary image gen SIDIX.**

Alasan:
1. License Apache-2.0 — 100% aman untuk komersial eventual tanpa ambiguitas.
2. Kualitas tertinggi di kelas open-weight komersial.
3. Kemampuan render text (krusial untuk konten bernada kaligrafi Nusantara).
4. Prompt adherence superior untuk prompt kompleks multi-subject (banyak prompt Nusantara bersifat compositional).
5. VRAM ~10 GB fp8 → fit di RunPod 4090 (sesuai Note 170).

**Top 2: SDXL 1.0 sebagai fallback + base untuk fine-tune Nusantara.**

Alasan:
1. Ekosistem LoRA + ControlNet jauh lebih matang — jika SIDIX perlu ControlNet (pose, depth, canny) di phase depan, SDXL lebih siap.
2. Training LoRA Nusantara lebih murah ($50–150) dibanding FLUX ($200–500).
3. Strategy: FLUX sebagai default, SDXL sebagai specialty pipeline.

**Reject:** SDXL Turbo (license), FLUX-dev (non-komersial), Stable Cascade (license), Hunyuan-DiT (restriction).

---

## Sanad
- SDXL paper: https://arxiv.org/abs/2307.01952 (Podell et al., Stability AI, 2023)
- FLUX.1 repo: https://github.com/black-forest-labs/flux
- FLUX.1-schnell HF: https://huggingface.co/black-forest-labs/FLUX.1-schnell (Apache-2.0)
- SDXL HF: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- Pixart-Σ: https://arxiv.org/abs/2403.04692
- AuraFlow: https://blog.fal.ai/auraflow/
- Artificial Analysis arena: https://artificialanalysis.ai/text-to-image
- Civitai LoRA ecosystem stats: https://civitai.com/
- Akses referensi: 2025-Q4 sampai 2026-04-19
