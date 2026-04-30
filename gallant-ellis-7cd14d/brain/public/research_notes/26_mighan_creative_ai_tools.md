# MIGHAN Creative AI Tools — Comprehensive Reference

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
*SIDIX Persona: MIGHAN — Creative Generalist*
*Last updated: 2026-04-16*

## Overview

MIGHAN adalah persona kreatif SIDIX yang menguasai ekosistem AI generatif secara menyeluruh:
image generation, video synthesis, music/audio creation, logo & vector design, dan creative workflow automation.
Referensi ini mencakup semua platform, tools, model, dan teknik relevan yang wajib dikuasai MIGHAN.

---

## 1. AI Image Generation

### 1.1 Midjourney
- **Tipe**: Cloud-based, Discord-native, subscription
- **Model terbaru**: Midjourney v7 (April 2026), v6.1
- **Keunggulan**: Aesthetic quality tertinggi, photorealism luar biasa, artistic coherence
- **Cara pakai**: `/imagine prompt` di Discord server Midjourney, atau midjourney.com (alpha)
- **Parameter penting**:
  - `--ar 16:9` — aspect ratio
  - `--stylize 100-1000` — level artistic styling
  - `--chaos 0-100` — variasi hasil
  - `--quality 0.25-2` — kualitas render
  - `--version 7` — versi model
  - `--no [elements]` — negative prompt
  - `--tile` — seamless pattern
  - `--seed [number]` — reproducible result
- **Prompt style**: descriptive noun phrases, no punctuation, style keywords di akhir
- **Harga**: $10-$120/bulan (Basic, Standard, Pro, Mega)

### 1.2 Leonardo AI (leonardo.ai)
- **Tipe**: Web platform, API tersedia
- **Model**: Leonardo Phoenix 1.0, Leonardo Diffusion XL, Leonardo Kino XL, Alchemy
- **Keunggulan**: Fine-tuned models, LoRA training, consistent characters, game assets
- **Fitur**:
  - **Alchemy**: enhanced pipeline dengan prompt refinement
  - **PhotoReal**: hyperrealistic photography
  - **Image Guidance**: control komposisi via reference image
  - **Character Consistency**: maintain karakter antar gambar
  - **Canvas**: inpainting & outpainting
  - **Motion**: animasi singkat dari gambar
- **Harga**: Free tier (150 token/hari), Apprentice ($12), Artisan ($30), Maestro ($60)

### 1.3 Stable Diffusion (Lokal & Cloud)
- **Tipe**: Open source, bisa self-hosted
- **Versi**: SDXL 1.0, SD 3.5 Large, SD 3.5 Medium
- **Platforms**: ComfyUI, AUTOMATIC1111, Forge WebUI
- **LoRA & Checkpoints**: Civitai.com — ribuan model community
- **Keunggulan**: Full control, offline, unlimited generation, custom training
- **ComfyUI**: node-based workflow, lebih powerful dari A1111
- **API**: via Stability AI API atau self-hosted

### 1.4 Dzine.ai (dzine.ai)
- **Tipe**: Web platform, style-focused
- **Keunggulan**: Konsistensi karakter, style presets, fast generation
- **Use case**: Karakter konsisten, komik strip, brand mascot
- **Fitur**: Face swap, style transfer, character LoRA

### 1.5 Adobe Firefly
- **Tipe**: Cloud, Adobe CC integration
- **Model**: Firefly Image 3, Firefly Vector
- **Keunggulan**: Commercially safe (trained on licensed content), Adobe ecosystem
- **Fitur**: Generative Fill (Photoshop), Text-to-Vector (Illustrator), Structure Reference
- **Harga**: Included di Adobe CC, atau standalone credits

### 1.6 DALL-E 3 (OpenAI)
- **Tipe**: API + ChatGPT Plus
- **Keunggulan**: Instruction-following terbaik, text rendering
- **API**: `POST /v1/images/generations` dengan model `dall-e-3`
- **Resolusi**: 1024x1024, 1024x1792, 1792x1024

### 1.7 Ideogram AI (ideogram.ai)
- **Tipe**: Web platform
- **Keunggulan**: **Text dalam gambar terbaik** di industri, typography integration
- **Model**: Ideogram 2.0, 2a
- **Use case**: Poster, thumbnail, text-heavy design, logo dengan text

### 1.8 Imagen (Google)
- **Tipe**: Google Cloud API + AI Studio
- **Model**: Imagen 4, Imagen 3
- **Keunggulan**: Photorealism, mematuhi prompts dengan akurat
- **API**: Via Google AI Studio (Gemini API) atau Vertex AI
- **Harga**: AI Studio ada free tier; Vertex AI berbayar

### 1.9 Flux (Black Forest Labs)
- **Tipe**: Open-source + commercial API
- **Model**: FLUX.1 [dev], FLUX.1 [schnell] (cepat), FLUX.1 [pro]
- **Keunggulan**: Kualitas SOTA open-source, photorealism, diverse styles
- **Platform**: Replicate, fal.ai, Hugging Face, ComfyUI (local)
- **FLUX.1 Schnell**: 1-4 steps inference, sangat cepat

### 1.10 Banana.dev / Replicate
- **Banana**: Serverless GPU inference platform (deprecated, merged ke services lain)
- **Replicate (replicate.com)**: Jalankan ribuan model via API
  - `POST https://api.replicate.com/v1/predictions`
  - Models: FLUX, SDXL, Llama, Whisper, dll
  - Harga: per-second GPU usage

### 1.11 Kling AI
- **Tipe**: Web + API (Kuaishou)
- **Keunggulan**: Gambar realistis, character generation
- **Terintegrasi**: Video generation juga

---

## 2. AI Video Generation

### 2.1 Veo (Google)
- **Model**: Veo 3 (terbaru, April 2026), Veo 2
- **Keunggulan**: Video berkualitas sinematik, physics realism, Veo 3 dapat generate audio
- **Veo 3 features**: Text-to-video, image-to-video, audio generation (SFX + dialog)
- **Akses**: Google AI Studio (preview), Vertex AI, VideoFX
- **Resolusi**: Hingga 1080p, 60fps support
- **Durasi**: hingga 1 menit (Veo 2), Veo 3 lebih panjang

### 2.2 Seedance (ByteDance)
- **Tipe**: Video generation (ByteDance research)
- **Keunggulan**: Temporal consistency tinggi, karakter stabil antar frame
- **Model**: Seedance 1.0
- **Relevansi**: Sama lab dengan CapCut AI video tools

### 2.3 ByteDance AI Video
- **MagicVideo**: Text-to-video research model ByteDance
- **CapCut AI**: Consumer video editing + AI effects
- **DreamBooth Video**: Personalized video generation

### 2.4 Runway ML (runwayml.com)
- **Model**: Gen-3 Alpha, Gen-3 Alpha Turbo
- **Tipe**: Web + API
- **Fitur**:
  - Text-to-Video
  - Image-to-Video
  - Video-to-Video (style transfer)
  - Inpainting video
  - Act-One (character animation dari video reference)
- **Harga**: $15-$95/bulan

### 2.5 Kling AI (kling.kuaishou.com)
- **Tipe**: Web platform (Kuaishou)
- **Model**: Kling 1.6 Pro, Kling 2.0
- **Keunggulan**: Gerakan fisika realistis, wajah stabil, karakter konsisten
- **Durasi**: hingga 3 menit
- **Harga**: Credit-based

### 2.6 Pika Labs (pika.art)
- **Model**: Pika 2.1
- **Fitur**: Text-to-video, Image-to-video, Pika Effects (morphing, explode, melt)
- **Keunggulan**: Creative effects, cepat, mudah dipakai

### 2.7 Luma AI (lumalabs.ai)
- **Model**: Dream Machine 1.6
- **Keunggulan**: Kualitas cinematic, camera motion control
- **Fitur**: Text-to-video, Image-to-video, camera presets

### 2.8 Open Source Video Models
- **HunyuanVideo (Tencent)**: 13B parameter open-source, kualitas setara commercial
  - GitHub: Tencent/HunyuanVideo
  - Run: ComfyUI atau inference script
- **LTX Video (Lightricks)**: Fast, efisien, bisa run di consumer GPU
  - 8GB VRAM minimum, 30fps real-time capable
- **Open-Sora**: Community open-source video model
- **CogVideoX (Zhipu AI)**: Bilingual, good temporal consistency
- **Wan (Alibaba)**: Wan 2.1, enterprise-grade open model

### 2.9 Sora (OpenAI)
- **Status**: Tersedia di ChatGPT Plus/Pro
- **Keunggulan**: Pemahaman fisika terbaik, world model
- **Keterbatasan**: Tidak ada API publik, hanya via ChatGPT

### 2.10 MiniMax (Hailuo)
- **Model**: Hailuo AI video
- **Keunggulan**: Wajah realistis, gerakan halus
- **Akses**: hailuoai.com

---

## 3. AI Music & Audio Generation

### 3.1 Suno AI (suno.com)
- **Tipe**: Web platform, API tersedia
- **Model**: Suno v4 (April 2026)
- **Kemampuan**: Text-to-full-song (vokal + instrumen), berbagai genre
- **Fitur**:
  - Custom lyrics atau auto-generate
  - Style prompting: "upbeat electronic pop, female vocal"
  - Cover song dari lagu referensi
  - Extend song
  - Instrumental mode
- **Kualitas**: Radio-ready quality, natural vocal
- **Harga**: Free (5 lagu/hari), Pro ($8/bln), Premier ($24/bln)

### 3.2 Udio (udio.com)
- **Tipe**: Web platform
- **Model**: Udio v1.5
- **Keunggulan**: Genre diversity sangat luas, audio fidelity tinggi
- **Fitur**: Remix, extend, custom styling, instrumental/vocal
- **Keunikan**: Lebih banyak style options vs Suno

### 3.3 Meta MusicGen
- **Tipe**: Open source (Meta AI)
- **GitHub**: facebookresearch/audiocraft
- **Model**: musicgen-large, musicgen-melody (pakai referensi melodi)
- **Cara run**: Hugging Face Inference API atau lokal
- **Kelebihan**: Gratis, controllable, melody conditioning

### 3.4 Stable Audio (Stability AI)
- **Model**: Stable Audio 2.0
- **Tipe**: Web + API
- **Keunggulan**: Stereo audio, hingga 3 menit, precise timing control
- **Harga**: Free tier + paid

### 3.5 ElevenLabs
- **Fokus**: Text-to-Speech, Voice Cloning
- **Fitur**:
  - Voice cloning (instant dari 1 menit audio)
  - 29+ bahasa
  - Sound effects generation
  - AI dubbing video
- **API**: `POST /v1/text-to-speech/{voice_id}`
- **Harga**: Free (10k char/bln), Starter ($5), Creator ($22)

### 3.6 Bark (Suno/Open Source)
- **Tipe**: Open source TTS dengan ekspresivitas tinggi
- **GitHub**: suno-ai/bark
- **Kemampuan**: Laugh, gasp, cry, music, multilingual, natural prosody

---

## 4. Logo & Brand Design AI

### 4.1 Looka (looka.com)
- **Tipe**: AI logo generator
- **Proses**: Input nama brand + industri + preferensi warna → AI generate ratusan opsi
- **Output**: SVG, PNG, brand kit (business card, letterhead, social media)
- **Harga**: Logo $65 one-time, Brand Kit $96

### 4.2 Adobe Firefly — Text-to-Vector
- **Terintegrasi**: Adobe Illustrator
- **Kemampuan**: Generate vector illustration dari text prompt
- **Format output**: SVG (editable di Illustrator)

### 4.3 Recraft (recraft.ai)
- **Tipe**: Web platform, design-focused
- **Model**: Recraft V3 (SOTA untuk vector & design)
- **Keunggulan**: Vector native, konsistensi brand, icon generation
- **Fitur**: Brand kit, style lock, SVG export

### 4.4 Microsoft Designer
- **Tipe**: Web (designer.microsoft.com)
- **Integrasi**: DALL-E 3 + Copilot
- **Use case**: Social media post, logo, banner

### 4.5 LogoAI (logoai.com)
- **Fokus**: Logo generator + brand collateral
- **Output**: Editable SVG + PNG

---

## 5. Vector & Illustration AI

### 5.1 Vectorizer.AI
- **Fungsi**: Raster-to-vector conversion (bitmap → SVG)
- **Kualitas**: Terbaik di industri untuk auto-tracing
- **API**: tersedia

### 5.2 Adobe Illustrator AI Features
- **Generative Recolor**: Recolor vector dengan prompt
- **Text to Vector Graphic**: Generate vector dari deskripsi
- **Retype**: Identifikasi font dari gambar

### 5.3 Canva AI (Magic Studio)
- **Magic Design**: Generate design dari text
- **Magic Media**: Image + video generation (pakai Stable Diffusion)
- **Background Remover**: Otomatis
- **Magic Eraser**: Remove objects
- **Harga**: Canva Pro $15/bln

### 5.4 Khroma (khroma.co)
- **Fungsi**: AI color palette generator
- **Cara**: Training dari preferensi warna → generate infinite palettes

### 5.5 Fontjoy
- **Fungsi**: AI font pairing
- **Cara**: Generate kombinasi font harmonis

---

## 6. AI Image Editing & Enhancement

### 6.1 Remove.bg / Rembg (Open Source)
- **Fungsi**: Background removal otomatis
- **Open source**: danielgatis/rembg
- **API**: remove.bg API atau self-hosted rembg
- **Model**: BiRefNet (state-of-the-art accuracy)

### 6.2 Upscayl (Open Source)
- **Fungsi**: AI image upscaling (2x-16x)
- **Tipe**: Desktop app, open source
- **Model**: ESRGAN, RealESRGAN

### 6.3 Let's Enhance
- **Fungsi**: Upscaling + enhancement cloud
- **Output**: Hingga 16x upscale

### 6.4 Magnific AI
- **Fungsi**: Super-resolution + creative upscaling
- **Keunggulan**: Tambah detail kreatif saat upscaling (bukan sekadar interpolasi)

### 6.5 Adobe Photoshop AI
- **Generative Fill**: Inpaint/extend via text prompt
- **Remove Tool**: AI-powered object removal
- **Neural Filters**: Style transfer, aging, expression change

---

## 7. 3D AI Tools

### 7.1 Luma AI (3D)
- **NeRF to 3D**: Capture objek nyata → 3D model
- **Genie**: Text-to-3D model generation

### 7.2 Meshy (meshy.ai)
- **Fungsi**: Text-to-3D, Image-to-3D
- **Output**: GLB, FBX, OBJ, STL
- **Use case**: Game assets, product visualization

### 7.3 Tripo3D (tripo3d.ai)
- **Fungsi**: AI 3D model generation
- **Kualitas**: Production-ready game assets

### 7.4 Shap-E (OpenAI)
- **Tipe**: Open source
- **GitHub**: openai/shap-e
- **Output**: NeRF + mesh

---

## 8. Workflow & Prompt Engineering untuk MIGHAN

### 8.1 Prompt Structure Universal
```
[Subject] + [Style/Medium] + [Lighting] + [Composition] + [Color] + [Technical]
```

Contoh:
```
a confident entrepreneur in a modern office,
cinematic photography style, golden hour lighting,
rule of thirds composition, warm amber tones,
shot on Canon R5, 85mm f/1.4, 8K UHD
```

### 8.2 Style Keywords Berguna
- **Photography**: cinematic, editorial, studio photography, candid, documentary
- **Art styles**: concept art, digital painting, oil painting, watercolor, vector art, flat design
- **Lighting**: golden hour, blue hour, rembrandt lighting, studio lighting, volumetric
- **Moods**: ethereal, gritty, minimalist, maximalist, cyberpunk, cottagecore

### 8.3 Platform Comparison Quick Reference

| Platform | Best For | Speed | Price | API |
|----------|----------|-------|-------|-----|
| Midjourney v7 | Artistic quality | Slow-Med | $10-120/mo | No |
| Flux.1 Pro | Photorealism | Fast | Pay-per-use | Yes |
| Ideogram 2.0 | Text in image | Fast | Free+paid | Yes |
| DALL-E 3 | Instruction following | Med | Per-token | Yes |
| Firefly | Commercial safe | Med | CC included | Yes |
| SDXL local | Full control | Depends | Free | Yes |
| Suno v4 | Full songs | Med | Free-$24/mo | Yes |
| Udio | Music diversity | Med | Free-paid | No |
| Veo 3 | Cinematic video | Slow | AI Studio | Yes |
| Kling 2.0 | Physical realism | Med | Credit | Yes |

### 8.4 Creative Brief to Output Workflow
```
1. Brief → Identify media type (image/video/music/design)
2. Choose platform berdasarkan:
   - Budget (ada free tier?)
   - Quality requirement
   - Commercial license?
   - API needed?
3. Generate → Iterate dengan variations
4. Post-process: upscale, background remove, edit
5. Export format yang tepat: PNG (raster), SVG (vector), MP4 (video), WAV/MP3 (audio)
```

---

## 9. Emerging AI Creative Tools 2026

### 9.1 AI Video Tools Terbaru
- **Sora (OpenAI)**: World-model video, physics simulation
- **Veo 3 (Google)**: Audio+video generation sekaligus
- **Wan 2.1 (Alibaba)**: Open-source enterprise video
- **Seedance 1.0 (ByteDance)**: Character consistency focus

### 9.2 AI Music Terbaru
- **Suno v4**: Real-time music generation
- **YuE (open source)**: Full song generation open-source
- **AudioCraft (Meta)**: Sound design + music

### 9.3 Multi-modal Generation
- **GPT-4o Native**: Gambar + text dalam satu model
- **Gemini 2.0 Flash**: Multimodal generation
- **Claude 3.5 Sonnet**: Vision understanding (belum bisa generate gambar)

---

## 10. Lisensi & Penggunaan Komersial

| Platform | Commercial OK? | Attribution? | NFT/Resell? |
|----------|----------------|--------------|-------------|
| Midjourney Pro+ | ✅ Ya | Tidak perlu | ✅ Ya |
| Adobe Firefly | ✅ Ya (IP protected) | Tidak | ✅ Ya |
| DALL-E 3 | ✅ Ya | Tidak | Tanya OpenAI |
| Stable Diffusion | ✅ (check model license) | Varies | Varies |
| Flux.1 Dev | ⚠️ Non-commercial | - | No |
| Flux.1 Pro | ✅ Ya | Tidak | Ya |
| Suno Pro+ | ✅ Ya | Tidak | Ya |
| Udio | Check TOS | - | - |

---

*Source: Platform official docs, community research — diverifikasi April 2026*
*SIDIX MIGHAN corpus — creative AI domain knowledge*
