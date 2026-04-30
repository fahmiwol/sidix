# Research Note 45 — Visual AI Generatif: Dari Diffusion hingga VLM Indonesia

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Sumber**: Peta Jalan Membangun AI Visual Generatif dari Nol hingga Produksi (Compass, 2026)
> **Relevance untuk SIDIX**: Tinggi — capability visual AI, dataset strategy, Indonesia opportunities
> **Tags**: diffusion, flux, sdxl, lora, vlm, controlnet, visual-ai, nusantara, dataset, vae, flow-matching

---

## 1. Fondasi Seni untuk AI — Vocabulary yang Harus Dikuasai

### 1.1 Tujuh Prinsip Desain Klasik (Harus Ada di Caption Dataset)

Model diffusion tidak "tahu" apa itu simetri kecuali dataset-nya berulang kali memasangkan gambar simetris dengan kata "symmetrical composition".

| Prinsip | Deskripsi | Keyword Prompt |
|---|---|---|
| **Komposisi** | Pengaturan elemen di frame | rule of thirds, golden ratio, leading lines |
| **Keseimbangan** | Simetri/asimetri visual | symmetrical, balanced, asymmetric |
| **Kontras** | Perbedaan nilai, warna, ukuran | high contrast, dramatic lighting |
| **Ritme** | Pengulangan elemen | repetitive pattern, rhythm |
| **Proporsi** | Hubungan ukuran antar elemen | golden ratio, monumental |
| **Penekanan** | Titik fokus utama | focal point, emphasis |
| **Kesatuan** | Koherensi keseluruhan | unified composition, cohesive |

### 1.2 Teori Warna untuk AI Dataset

**Color wheel**: primer, sekunder, tersier.
**Relasi**: complementary, analogous, triadic, split-complementary.
**Ruang warna**: HSV (segmentasi berbasis hue), LAB (perceptual uniformity — distance lebih akurat dari RGB), CMYK (cetak), YUV (kompresi video).

**Teknik ekstraksi palette untuk dataset**: K-means clustering di ruang LAB → 5 warna dominan → tambahkan ke caption sebagai `"palette: #A94442, #F5E6CA, ..."`.

**Filter kualitas LAION**: Aesthetic Predictor v2 (skor 1–10 berbasis CLIP embedding):
- Threshold ≥5.5 = "visually pleasing"
- Threshold ≥6.5 = premium subset
- Filter paling penting saat kurasi dataset 100k+ gambar

### 1.3 Aliran Seni Rupa yang Harus Ada di Corpus

Realisme, Impresionisme (sapuan kuas pecah, cahaya luar ruang), Ekspresionisme, Surealisme, Kubisme (multi-sudut pandang), Pop Art (flat color), Minimalism, Art Nouveau (ornamen organik), Bauhaus.

> **Pastikan WikiArt + BAM! (Behance Artistic Media)** tercakup sebelum training — tanpa itu prompt "in the style of Kandinsky" akan menghasilkan kebingungan.

### 1.4 Lighting Keyword untuk Controllability

Keyword yang terbukti di SDXL/Flux:
- `Rembrandt lighting` (segitiga pipi)
- `butterfly/paramount`, `split lighting`, `loop`, `broad/short`
- `rim light`, `golden hour`, `blue hour`, `overcast soft box`, `hard noon`
- `three-point lighting (key+fill+back)`

> **Insight**: Tambahkan lighting keyword saat re-captioning dataset foto → meningkatkan controllability inference secara signifikan.

### 1.5 AI Prompting Style — Vocabulary Terbukti

Bekerja di SDXL/Flux:
- `painterly, photorealistic, cel-shaded, watercolor, oil painting, ink sketch`
- `anime (Makoto Shinkai / Studio Ghibli), concept art (trending on ArtStation)`
- `isometric, pixel art, 8-bit`
- Color grading: `Kodak Portra film stock, Fuji Velvia, teal-orange cinematic`

---

## 2. Evolusi Arsitektur Generatif

### 2.1 Timeline Paradigma

```
GAN (2014–2022)
  → Vanilla GAN (Goodfellow 2014) — adversarial game
  → DCGAN, ProgressiveGAN
  → StyleGAN 1/2/3 — AdaIN + disentangled latent
  → GigaGAN (2023) — revival, kalah traction

VAE Family
  → β-VAE (disentanglement)
  → VQ-VAE/VQ-VAE-2 — discrete codebook (fondasi DALL-E 1)
  → VAE 4-channel (SD1.5/XL) → VAE 16-channel (Flux) — fidelity lebih tinggi

Diffusion DDPM (2020)
  → Forward: menambahkan noise Gaussian T=1000 step
  → Reverse: U-Net prediksi noise ε
  → Loss: MSE(ε, ε_θ(x_t, t))
  → DDIM (deterministic, 20–50 step cukup)
  → Score-based SDE (kontinu, menyatukan DDPM + score matching)
  → EDM (noise scheduling + preconditioning yang lebih baik)

Flow Matching / Rectified Flow (2023–2026) — PARADIGMA BARU
  → Flow Matching: langsung melatih velocity v_θ(x_t,t) dari noise ke data
  → Rectified Flow: trajectory lebih "lurus" → SD3 dan Flux
  → Consistency Models: 1-step generation via distillation
  → CFG (Classifier-Free Guidance): inference = ε_uncond + w·(ε_cond − ε_uncond)
```

### 2.2 Trade-off Paradigma

| Paradigma | Kualitas | Diversitas | Training Stability | Inference Speed |
|---|---|---|---|---|
| GAN | Tinggi (narrow) | Rendah | Sulit (mode collapse) | Sangat cepat |
| VAE | Sedang | Tinggi | Mudah | Cepat |
| Autoregressive | Tinggi | Tinggi | Mudah | Sangat lambat |
| Diffusion DDPM | SOTA | Tinggi | Mudah | Lambat (50 step) |
| Flow Matching | **SOTA** | Tinggi | Mudah | **Cepat (5–20 step)** |

### 2.3 Latent Diffusion Model — Prinsip Dasar

Operasi diffusion **bukan** di pixel 512×512×3 (786k dim) tapi di **latent 64×64×4 (16k dim)** — **48× lebih hemat compute**.

```
Input prompt → CLIP text encoder → [text embeddings 77×768]
                                         ↓ cross-attention
Input image → VAE encoder → [latent z] → U-Net/DiT → predict ε/v
                                         ↓
                              [denoised ẑ_0] → VAE decoder → [image]
```

**MMDiT (SD3+)**: memproses token teks dan gambar dalam stream **setara** (bukan cross-attention searah) → prompt following dan text rendering jauh lebih baik.

---

## 3. Stable Diffusion & Flux — Versi dan Spesifikasi

| Versi | Params | Native Res | Text Encoder | Arsitektur | Lisensi |
|---|---|---|---|---|---|
| SD 1.5 | 860M | 512 | CLIP ViT-L/14 | UNet | CreativeML |
| SDXL 1.0 | 2.6B+6.6B | 1024 | CLIP-L + OpenCLIP-G | UNet dual | CreativeML++ |
| SD 3 Medium | 2B | 1024 | CLIP-L + CLIP-G + T5-XXL | **MMDiT + RF** | Stability Community |
| SD 3.5 Large | **8B** | 1024 | Triple encoder | MMDiT + RF | Stability Community |
| **Flux.1 schnell** | **12B** | 1024 | CLIP-L + T5-XXL | MMDiT + FM distilled | **Apache 2.0** ✓ |
| Flux.1 dev | 12B | 1024 | same | MMDiT + FM | Non-commercial |
| Flux 1.1 Pro Ultra | 12B | **4K** | same | MMDiT + FM | API-only |

**Samplers populer 2026**:

| Sampler | Step min | Kualitas | Catatan |
|---|---|---|---|
| DPM++ 2M Karras | 20–30 | Tinggi | Default ComfyUI SDXL |
| Euler a (ancestral) | 20–30 | Tinggi | Variasi besar, artistic |
| UniPC | 10–20 | Tinggi | Cepat dan stabil |
| LCM/Turbo/Lightning | 1–4 | Sedang-Tinggi | Real-time |

---

## 4. Fine-tuning Techniques

### 4.1 LoRA — Teknik Paling Penting

**LoRA (Low-Rank Adaptation)**: freeze W, tambahkan `ΔW = BA` dengan `B ∈ ℝ^(d×r), A ∈ ℝ^(r×d)`, `r << d`.

**Target modules** untuk SDXL: `to_q, to_k, to_v, to_out.0` (cross-attention) + `ff.net.*`.
**Target modules** untuk Flux: `single_transformer_blocks.*.linear*` + `transformer_blocks.*.attn.*`.

**Rank guide**:
- Style LoRA: rank 16–32 cukup
- Karakter kompleks: rank 64–128
- Concept: rank 32–64

### 4.2 DreamBooth + LoRA

Full fine-tune UNet + class-preservation loss. 5–20 gambar subjek + class prior images. Kombinasi **DreamBooth + LoRA** = standar 2026.

### 4.3 ControlNet

Membekukan UNet asli + melatih salinan encoder dengan "zero convolutions" untuk kondisi tambahan.

**Varian standar**: Canny, Depth, OpenPose, Segmentation, Scribble, Lineart, Normal map, Tile (upscaling), Inpaint, IP2P.

**ControlNet untuk Flux**: Depth, Canny tersedia 2024–2025, kualitas masih berkembang.

### 4.4 IP-Adapter

"Image prompting" — encode gambar referensi via CLIP image encoder → inject ke cross-attention. Berguna untuk **brand style transfer** tanpa training.

Varian: IP-Adapter-Plus (fidelity tinggi), IP-Adapter-FaceID (identity preservation portrait).

### 4.5 PEFT Modern

| Teknik | Ukuran | Notes |
|---|---|---|
| **QLoRA** | Sangat kecil | LoRA + 4-bit NF4 — Flux 12B LoRA di 16GB VRAM |
| **DoRA** | Kecil | Weight-Decomposed — akurasi dekat full fine-tune |
| LoHa, LoKr | Kecil | Hadamard/Kronecker — parameter lebih sedikit |

### 4.6 Tools Fine-tuning

| Tool | Best for | Min VRAM |
|---|---|---|
| **Kohya_ss / sd-scripts** | SD1.5/SDXL LoRA, DreamBooth | 8GB (SD1.5), 12GB (SDXL) |
| **AI Toolkit (Ostris)** | Flux LoRA | 12GB (Flux FP8) |
| **SimpleTuner** | Full FT SDXL/SD3/Flux | 24GB |
| OneTrainer | SD1.5/XL/Flux | 12GB |

---

## 5. Dataset Visual — Strategi Kurasi

### 5.1 Dataset Kanon

**Pretraining skala besar**:
- LAION-5B (5.85B pasangan, Re-LAION cleaned 2024)
- COYO-700M (Kakao Brain, 747M pasangan)
- DataComp-1B (1.4B, filtered dari 12.8B)
- CC3M, CC12M (Google Conceptual Captions)
- PD12M (12M public domain, license-clean)

**Art/Aesthetic**:
- WikiArt (~81k lukisan, 27 gaya, 1119 artis)
- LAION-Aesthetic (600k, score ≥6.5)
- BAM! (Behance, 65M, 2.5M labeled)

**Face**: FFHQ (70k @ 1024²), CelebA-HQ (30k).

### 5.2 Auto-Captioning Pipeline 2026

**Hierarki kualitas**:
1. **BLIP-2** — cepat, caption pendek (100% dataset, baseline)
2. **Florence-2 / CogVLM** — caption terstruktur
3. **InternVL-2.5 / LLaVA-NeXT** — caption panjang kualitas tinggi (top 20%)
4. **GPT-4o / Claude Opus** — caption paling kaya, $0.01–0.03/gambar (eval set 1%)

> **Key insight**: Dataset 100k gambar dengan caption GPT-4V/InternVL3-rewritten sering **mengungguli 1M gambar dengan alt-text mentah** — quality data > scale.

**Biaya untuk 1M gambar**: ~$200–500 (strategi hybrid).

### 5.3 Quality Filtering Pipeline

```
Raw dataset
  → CLIP score ≥ 0.28 (cosine similarity image-text)
  → Aesthetic score v2 ≥ 5.5 (LAION predictor)
  → NSFW filter (SD safety checker + LAION NSFW)
  → Watermark detection
  → OCR filter (skip gambar dominan teks, kecuali typography dataset)
  → Dedup: pHash threshold 5 bit + CLIP embedding cosine > 0.95
  → Fastdup library (gabungkan semua)
```

### 5.4 Checklist Dataset 100k Gambar

1. Define scope niche spesifik (target 100k setelah filter)
2. Source raw 500k–2M sebelum filter
3. Dedup phase 1: MD5 exact → pHash near-duplicate
4. Quality filter: ≥512px, aesthetic ≥5.0, CLIP ≥0.27, no NSFW
5. Caption pipeline: BLIP-2 → InternVL-2.5 top 30%
6. Translate caption ID jika dibutuhkan (NLLB-3.3B)
7. Aspect ratio bucketing: resize+crop center
8. Latent pre-encoding → hemat 30–50% training time
9. Shard ke WebDataset (1000 gambar/tar)
10. Version di HF Hub private / DVC

---

## 6. Vision-Language Models (VLM)

### 6.1 Landscape 2026

| Tier | Model | Notes |
|---|---|---|
| Proprietary frontier | GPT-4o, Claude Opus, Gemini Pro | MMMU ~80–85%, tidak bisa fine-tune |
| **Open-source terbaik** | InternVL3/3.5, Qwen2.5-VL | MMMU >70%, fine-tuneable |
| Efficient open | MiniCPM-V 4.5 | 8B, mengalahkan Qwen2.5-VL-72B di OpenCompass |

### 6.2 Top 3 Rekomendasi untuk Tim Indonesia

1. **Qwen2.5-VL-7B** (Apache 2.0)
   - DocVQA 95.7%, multilingual termasuk ID
   - RTX 3090 cukup untuk inference
   - Ekosistem LLaMA-Factory/ms-swift matang

2. **InternVL3-8B** (MIT)
   - Native multimodal pretraining
   - V2PE high-res, multi-image support

3. **MiniCPM-V 4.5** (Apache 2.0)
   - 8B tapi mengalahkan Qwen2.5-VL-72B di OpenCompass
   - Efisien untuk edge/mobile

**Benchmark referensi VLM**: MMMU (reasoning), DocVQA, ChartQA, OCRBench, MMBench.

### 6.3 Design-Specific VLM Tasks

| Task | Model Terbaik |
|---|---|
| Layout generation | PosterLlama, LayoutPrompter (training-free) |
| Design2Code | Qwen2.5-VL + ScreenCoder pipeline |
| SVG/Vector | StarVector, SVGDreamer |
| Chart understanding | MatCha, DePlot, ChartLlama |
| Typography | FontDiffuser |

---

## 7. SOTA Image Generation 2026

| Model | License | Open? | Kekuatan |
|---|---|---|---|
| DALL·E 3 | Proprietary | ✗ | GPT integration |
| Midjourney v7 | Proprietary | ✗ | Aesthetics terbaik |
| SD 3.5 Large (8B) | Community | ✓ | Open-source prompt adherence |
| **Flux.1 schnell** | **Apache 2.0** | **✓ komersial** | **Free + fast (4-step)** |
| Flux.1 dev | Non-commercial | ✓ | Quality mendekati MJ |
| Ideogram 3.0 | Proprietary | ✗ | **Text rendering terbaik** |
| Recraft V3 | Proprietary | ✗ | Vector & logo |
| HiDream-I1 | Open | ✓ | New challenger 2025 |
| PixArt-Σ | Open | ✓ | 4K budget-efficient |

**Rekomendasi Indonesia budget terbatas**:
- Eksperimen cepat → **Flux.1-schnell** (Apache 2.0, boleh komersial) + LoRA custom
- Typography (Bahasa Indonesia banyak teks) → Flux > SD 3.5 > Ideogram
- Riset akademik → PixArt-Σ atau Lumina-Next (cost-effective training)

---

## 8. RLHF untuk Gambar

| Method | Win-rate | Notes |
|---|---|---|
| **Diffusion-DPO** | 69% vs SDXL base | DPO diterapkan ke diffusion |
| **DDPO** | — | Policy gradient untuk diffusion |
| SPO, Curriculum-DPO | — | Iteratif |

**Evaluasi otomatis**: FID (~20–30 SDXL COCO), KID, CLIPScore (0.27–0.32 SOTA), HPSv2, PickScore, ImageReward, GenEval/T2I-CompBench.

---

## 9. Infrastruktur & Biaya

### 9.1 GPU Tier

| GPU | VRAM | BF16 TFLOPS | Cloud/jam | Harga beli |
|---|---|---|---|---|
| RTX 4090 | 24GB | 165 | $0.35–0.70 | $1,600–2,000 |
| L40S | 48GB | 362 | $0.79–1.55 | $8,000–10,000 |
| A100 80GB | 80GB | 312 | $1.29–3.27 | $15,000–20,000 |
| H100 80GB | 80GB | 989 | $1.99–4.76 | $30,000–40,000 |
| MI300X (AMD) | 192GB | 1,307 | $2.50–3.49 | $15,000–20,000 |

**Termurah**: Vast.ai RTX 4090 $0.30–0.50/h, RunPod Community $0.39–0.44.

### 9.2 Biaya Training Konkret

| Skenario | Biaya |
|---|---|
| LoRA SD1.5 RTX 4090 (1–5 jam) | $1–5 |
| LoRA SDXL RTX 4090 (2–6 jam) | $3–15 |
| LoRA Flux dev RTX 4090 (3–12 jam) | $8–40 |
| DreamBooth SDXL full UNet | $15–60 |
| Sony micro-budget 1.16B DiT (8×H100, 2.6 hari) | **~$1,890** |
| SDXL from scratch | ~$1–2M |

### 9.3 Serving Stack

- **ComfyUI API** — workflow-driven, fleksibel, production-ready
- **vLLM/SGLang** — untuk model berbasis transformer
- **Fal.ai / Replicate / Modal** — serverless, scale-to-zero untuk startup
- **TensorRT FP8** — 40% latency reduction SDXL (NVIDIA only)

---

## 10. Peluang Indonesia — Niche Vertikal

| Domain | Pasar | Potensi |
|---|---|---|
| **E-commerce product photography** | 20M seller Tokopedia/Shopee | Freemium Rp 50k–500k/bulan |
| **UMKM marketing IG/TikTok** | 64M UMKM Indonesia | Partnership Kredivo/KoinWorks |
| **Batik digital co-creation** | Pengrajin batik | Generator + manual partnership |
| **Konten halal/muslim** | 230M Muslim Indonesia | Kaligrafi Arab-Latin-Jawi, interior masjid |
| **Real estate rendering** | Rumah adat modern, villa Bali | — |
| **Ilustrasi buku K-12** | Kurikulum Merdeka | Kualitas internasional |

### Visual Style Nusantara — Prioritas Dataset

| Domain | Sumber | Legal |
|---|---|---|
| **Batik** (Pekalongan, Solo, Yogya, Madura, Lasem) | Museum Tekstil Jakarta, BBKB Yogya | Kolaborasi > scraping |
| **Wayang** (kulit, golek, beber) | Museum Wayang, dalang | Hati-hati hak kontemporer |
| **Ornamen** (Jepara, Toraja, Bali, Dayak, Asmat) | BPK, buku etnografi | Mostly public domain |
| **Rumah adat** | Kemenparekraf, Wikimedia | Legal aman |
| **Kuliner Indonesia** | GoFood/GrabFood API | Benchmark vs Unsplash-food |

---

## 11. Implikasi untuk SIDIX

### Caption Bahasa Indonesia untuk SIDIX
```
Pipeline caption ID untuk dataset visual:
1. Generate dengan InternVL-2.5 (prompt dalam Bahasa Indonesia)
2. Post-edit dengan Merak/SahabatAI
3. Human annotator via Dicoding (Rp 500–2000/caption)
4. Synthetic augmentation CapsFusion-style
```

### SIDIX sebagai Design Assistant
- SIDIX sudah tahu prinsip desain (research note ini) → bisa jadi **design consultant**
- Mampu mereview komposisi, warna, tipografi, layout
- Bisa generate caption untuk gambar via pipeline VLM
- Mampu menjelaskan teknik fotografi (segitiga eksposur, lighting setup)

### VLM Integration untuk SIDIX
- Qwen2.5-VL-7B = kandidat untuk SIDIX Vision capability
- Apache 2.0 → boleh komersial tanpa masalah lisensi
- DocVQA 95.7% → sangat baik untuk dokumen Indonesia

### Indonesia Peluang = SIDIX Positioning
- Tidak ada AI yang focus pada visual Nusantara + Islamic aesthetic
- SIDIX bisa jadi bridge: bahasa natural ID → generate visual Nusantara
- Corpus batik, wayang, ornamen → bisa jadi unique training data moat

---

*Research Note 45 | SIDIX Knowledge Corpus | Sumber: Visual AI Generatif Blueprint (Compass, 2026)*
