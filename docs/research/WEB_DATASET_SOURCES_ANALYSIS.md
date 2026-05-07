# Riset & Analisis: Sumber Dataset Gambar untuk Training SIDIX

> **Research Note #319** — Web Dataset Source Analysis  
> **Tanggal:** 2026-05-08  
> **Agen:** Kimi (partner SIDIX)  
> **Status:** COMPLETE — implementasi + dokumentasi  

---

## 1. Ringkasan Eksekutif

Bos meminta riset sumber dataset gambar dari web (Shutterstock, microstock, Instagram, Adobe Stock, Canva). Setelah riset mendalam, **kesimpulan keras**: scraping konten komersial = **pelanggaran hak cipta + Terms of Service** dengan risiko litigasi tinggi. SIDIX tidak akan mengimplementasikan scraper untuk sumber komersial.

Sebagai gantinya, SIDIX mengimplementasikan **Web Dataset Collector** untuk sumber **legal dan ethical**:
- Unsplash API (free commercial use)
- Pexels API (free commercial use)
- Wikimedia Commons (CC-licensed)
- LAION-5B metadata reference (open dataset, metadata-only)

---

## 2. Analisis Legal per Sumber

### 2.1 Sumber BERBAHAYA (Ditolak)

| Sumber | Risiko | Bukti Legal | Rekomendasi |
|--------|--------|-------------|-------------|
| **Shutterstock** | Copyright infringement + ToS violation | Getty vs Stability AI (2025) landmark case; Shutterstock Contributor Fund shows awareness | ❌ Jangan scrape. Beli license kalau butuh. |
| **Adobe Stock** | Copyright infringement + ToS violation | Adobe Firefly explicitly trained "on content we have permission to use" | ❌ Jangan scrape. Adobe punya Contributor Fund. |
| **Getty Images** | Copyright infringement + ToS violation | Getty vs Stability AI (2025); Getty launched lawsuit vs AI companies | ❌ Jangan scrape. Getty punya licensing program. |
| **Canva** | Proprietary content + ToS violation | Canva ToS prohibits scraping; content includes third-party licensed material | ❌ Jangan scrape. |
| **Instagram** | ToS Meta violation + potential CFAA | Meta ToS explicit prohibits automated scraping; bisa kena IP ban + legal action | ❌ Jangan scrape. Public API (Graph API) punya strict rate limits. |
| **Microstock lain** | Copyright infringement + ToS violation | Semua platform stock photo menjual license, bukan ownership | ❌ Jangan scrape. |

### 2.2 Basis Legal (2025-2026)

1. **US Copyright Office Report (May 9, 2025)**: "Unauthorized copying of copyrighted works, even if publicly accessible, may constitute infringement." [^1]
2. **Getty vs Stability AI (2025)**: Getty sued Stability AI for scraping 12M+ images. Case heightened awareness and pressured governments to reform copyright law around AI training. [^2]
3. **Bartz v. Anthropic PBC (June 23, 2025)**: Fair use defense may be available where works used as training data were **lawfully acquired**. [^3]
4. **Kadrey v. Meta Platforms (June 25, 2025)**: Similar fair use analysis for LLM training data. [^3]
5. **Shutterstock Contributor Fund**: Shutterstock launched first-of-its-kind fund compensating contributors whose works are used to develop AI. [^4]

> **Key insight**: "Fair use" untuk training data masih dalam litigation. Tidak ada blanket exception. Safest path = gunakan content yang **explicitly free to use** atau **lawfully licensed**.

### 2.3 Sumber AMAN (Diimplementasikan)

| Sumber | Lisensi | Batasan | Implementasi |
|--------|---------|---------|--------------|
| **Unsplash API** | Unsplash License — free for commercial use, attribution appreciated | 50 req/hour free tier | ✅ `search_unsplash()` + `get_unsplash_photo()` |
| **Pexels API** | Pexels License — free to use and modify, no attribution | 200 req/hour, 20k/month free tier | ✅ `search_pexels()` |
| **Wikimedia Commons** | CC0 / CC-BY / CC-BY-SA (varies per file) | No API key needed | ✅ `search_wikimedia()` + `get_wikimedia_file_info()` |
| **LAION-5B** | CC-BY 4.0 (metadata only) | Metadata only, no images distributed | ✅ `get_laion_info()` — reference + metadata pointers |
| **Poly Haven** | CC0 | HDR environment maps & 3D textures | 📋 Future: direct download via URL |

---

## 3. Analisis DNA Dataset (Karakteristik Training Data)

### 3.1 Metrik DNA

| Dimensi | Definisi | Threshold Baik untuk LoRA |
|---------|----------|---------------------------|
| **Resolution** | % gambar >= 1024x1024 | >= 50% |
| **Caption Coverage** | % entri dengan deskripsi/tag | >= 60% |
| **Author Diversity** | % unique authors | >= 30% |
| **Aspect Ratio** | Distribusi landscape/portrait/square | Balanced |
| **License Clarity** | % dengan lisensi yang jelas | 100% |
| **Source Diversity** | Jumlah sumber berbeda | >= 3 |

### 3.2 DNA per Sumber

#### Unsplash
- **Volume**: 5M+ photos
- **Resolution**: Tinggi (kebanyakan 4000x3000+)
- **Caption**: Moderate (title + alt_description, tidak selalu detail)
- **Style**: Fotografi profesional, western-centric, portrait & landscape
- **Bias risk**: Fotografer profesional dominan = style homogenization risk
- **LoRA suitability**: ⭐⭐⭐⭐⭐ (excellent for photorealistic LoRA)

#### Pexels
- **Volume**: Jutaan photos
- **Resolution**: Mixed (ada yang low-res, ada yang high-res)
- **Caption**: Baik (alt text tersedia)
- **Style**: Lebih diverse dari Unsplash, lebih banyak stock-style
- **Bias risk**: Stock-style dominance
- **LoRA suitability**: ⭐⭐⭐⭐ (good for general-purpose)

#### Wikimedia Commons
- **Volume**: 100M+ files
- **Resolution**: Sangat mixed (historical photos, maps, diagrams)
- **Caption**: Variable quality (depends on uploader)
- **Style**: Sangat diverse (historical, scientific, geographic, art)
- **Bias risk**: Western encyclopedic bias
- **LoRA suitability**: ⭐⭐⭐ (great for niche domains: historical, scientific, art)

#### LAION-5B
- **Volume**: 5.85B image-text pairs
- **Resolution**: Mixed (subset LAION-High-Resolution = 170M @ >=1024px)
- **Caption**: Web-scraped alt text = noisy but large scale
- **Style**: Mirror of the web = extremely diverse but biased
- **Bias risk**: Tinggi — documented gender, race, western bias [^5]
- **LoRA suitability**: ⭐⭐⭐⭐⭐ (scale matters; use with filtering)

### 3.3 LAION-Aesthetics Bias Warning

Research by Taylor et al. (2026) menemukan:
- LAION Aesthetics Predictor (LAP) **disproportionally filters in images with captions mentioning women**
- **Filters out images mentioning men or LGBTQ+ people**
- Rates realistic images of landscapes, cityscapes, and portraits from **western and Japanese artists** most highly
- LAP reinforces **imperial and male gazes** found within western art history [^5]

> **Rekomendasi**: Jangan pakai LAION-Aesthetics sebagai single filter. Combine dengan custom filtering berdasarkan domain need.

---

## 4. Implementasi SIDIX

### 4.1 Module Baru: `dataset_web_collector.py`

| Function | Sumber | API Key | Endpoint |
|----------|--------|---------|----------|
| `search_unsplash()` | Unsplash | UNSPLASH_ACCESS_KEY | `/dataset/web/unsplash` |
| `search_pexels()` | Pexels | PEXELS_API_KEY | `/dataset/web/pexels` |
| `search_wikimedia()` | Wikimedia Commons | None | `/dataset/web/wikimedia` |
| `get_wikimedia_file_info()` | Wikimedia Commons | None | `/dataset/web/wikimedia/file` |
| `get_laion_info()` | LAION-5B (reference) | None | `/dataset/laion` |
| `search_all()` | All sources | Mixed | `/dataset/web/search` |
| `analyze_dataset_dna()` | Analysis | None | `/dataset/dna` |

### 4.2 Tools Baru (agent_tools.py)

| Tool | Deskripsi | Permission |
|------|-----------|------------|
| `search_unsplash` | Cari foto gratis dari Unsplash | open |
| `search_pexels` | Cari foto gratis dari Pexels | open |
| `search_wikimedia` | Cari media CC-licensed dari Wikimedia | open |
| `search_dataset_web` | Cari cross-source (Unsplash+Pexels+Wikimedia) | open |
| `analyze_dataset_dna` | Analisis karakteristik dataset untuk LoRA | open |
| `get_laion_info` | Info LAION-5B + download pointers | open |

**Total tools: 50 → 56 (+6)**

### 4.3 Endpoints Baru (agent_serve.py)

| Endpoint | Method | Body | Response |
|----------|--------|------|----------|
| `/dataset/web/unsplash` | POST | `{query, per_page, orientation}` | `{ok, total, photos, license_note}` |
| `/dataset/web/pexels` | POST | `{query, per_page, orientation, color}` | `{ok, total, photos, license_note}` |
| `/dataset/web/wikimedia` | POST | `{query, limit, file_type}` | `{ok, total, files, license_note}` |
| `/dataset/web/wikimedia/file` | POST | `{title}` | `{ok, image_url, license, artist}` |
| `/dataset/web/search` | POST | `{query, sources, per_source}` | `{ok, results, total_items, legal_summary}` |
| `/dataset/dna` | POST | `{entries}` | `{ok, quality_score, caption_coverage, diversity_score, lora_suitability}` |
| `/dataset/laion` | GET | — | `{ok, subsets, download, caveats}` |

---

## 5. Rekomendasi untuk Bos

### 5.1 Untuk Training LoRA Character (NPC SIDIX)

**Best approach**: Combine sumber dengan data lokal

```
Dataset composition untuk LoRA character:
├── 40% — Local assets (Mighan-Web NPC portraits, Mighan-3D sprites)
│         → Highest quality, domain-specific, no legal risk
├── 30% — Unsplash (portrait photography, character references)
│         → High resolution, professional lighting
├── 20% — Pexels (diverse portrait styles)
│         → More variety than Unsplash
└── 10% — Wikimedia Commons (historical portrait art)
          → Artistic style diversity
```

**LAION-5B**: Gunakan hanya untuk **pre-training base model**, bukan untuk LoRA fine-tune character-specific. LAION terlalu noisy untuk LoRA yang butuh konsistensi tinggi.

### 5.2 Untuk Training LoRA Style (Design SIDIX)

```
Dataset composition untuk LoRA style:
├── 50% — Local assets (Mighan-3D design-studio, Mighan-Web UI)
│         → Domain-specific style consistency
├── 25% — Unsplash (design, architecture, product photography)
├── 15% — Wikimedia Commons (art history, graphic design)
└── 10% — Pexels (stock design elements)
```

### 5.3 API Key Setup

| Key | Dapatkan di | Free Tier |
|-----|-------------|-----------|
| `UNSPLASH_ACCESS_KEY` | https://unsplash.com/developers | 50 req/hour |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ | 200 req/hour |

> **Catatan**: API key bisa di-set sebagai environment variable atau di `.env` file. Module sudah include fallback instructions kalau key belum di-set.

### 5.4 Workflow Rekomendasi

1. **Step 1**: Search Unsplash/Pexels untuk reference images
2. **Step 2**: Download images yang cocok (manual atau via tool)
3. **Step 3**: Combine dengan local assets via `collect_dataset`
4. **Step 4**: Run `analyze_dataset_dna` untuk cek kualitas
5. **Step 5**: Export ke JSONL untuk training pipeline
6. **Step 6**: Train LoRA di RunPod dengan `mighan-media-worker`

---

## 6. Referensi

[^1]: US Copyright Office, "Copyright and Artificial Intelligence: Part 3 — Generative AI Training" (May 9, 2025). https://www.copyright.gov/ai/

[^2]: Getty Images vs Stability AI, High Court of Justice (2025). Landmark case on AI training data scraping.

[^3]: Bartz v. Anthropic PBC, No. 3:24-cv-05417-WHA (N.D. Cal. June 23, 2025); Kadrey v. Meta Platforms, No. 3:23-cv-03417-VC (N.D. Cal. June 25, 2025).

[^4]: Shutterstock Contributor Fund announcement (2022-2023). https://www.shutterstock.com/business/generative-ai

[^5]: Jordan Taylor et al., "The Algorithmic Gaze of Image Quality Assessment: An Audit and Trace Ethnography of the LAION-Aesthetics Predictor" (arXiv:2601.09896, 2026).

[^6]: LAION-5B: An open large-scale dataset for training next generation image-text models. NeurIPS 2022 Datasets and Benchmarks. https://laion.ai/blog/laion-5b/

[^7]: Legal 500 — UK & US Artificial Intelligence Guides (2025-2026). Data scraping legality analysis.

---

## 7. Changelog

| Tanggal | Versi | Perubahan |
|---------|-------|-----------|
| 2026-05-08 | v1.0 | Riset awal + implementasi dataset_web_collector.py + 6 tools + 7 endpoints |
