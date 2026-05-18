# Riset: SIDIX Spark — Ethical Dataset Curator (Adobe Firefly Approach)

> **Research Note #322** — SIDIX Spark Ethical Dataset Curation  
> **Tanggal:** 2026-05-08  
> **Agen:** Kimi (partner SIDIX)  
> **Status:** COMPLETE — implementasi + dokumentasi  

---

## 1. Ringkasan: Pinterest & Muse/Spark

Bos meminta:
1. Fetch dari Pinterest atau situs gambar lainnya
2. Pelajari Muse by Meta (Spark MSL)
3. Buat versi SIDIX sendiri (adobe-like source)

### 1.1 Pinterest = DITOLAK ❌

Setelah riset mendalam:
- **Pinterest ToS** eksplisit melarang scraping: "You may not access or use Pinterest for any purpose other than your own personal use"
- Content di Pinterest = user-generated, tidak selalu free to use
- Pinners grant Pinterest license, tapi **TIDAK** memberi license ke pihak ketiga untuk AI training
- Reddit vs Perplexity (2025): scraping dengan bypass rate limits = DMCA Section 1201 violation
- Meta v. Bright Data (2023-2024): contract-based claims viable even when CFAA claims fail

**Rekomendasi: Jangan scrape Pinterest.** Gunakan alternatives legal.

### 1.2 Muse by Meta (Spark MSL)

- **Muse Spark** = proprietary LLM dari Meta Superintelligence Labs (MSL), dipimpin Alexandr Wang (ex-Scale AI CEO)
- Dibuild dari ground-up, bukan dari Llama family
- Closed source, available via Meta AI app dan meta.ai
- Key features: Thought Compression, Contemplating Mode (multi-agent), Health AI
- Natively multimodal: voice, text, image inputs
- Private API preview untuk select partners
- Plans to open-source future versions

**Relevansi untuk SIDIX:**
- Multi-agent orchestration → Voyager P3 (tool composition) sudah partially implemented
- Thought compression → bisa diadopsi untuk efficient reasoning
- Health AI → niche yang bisa diterapkan di domain Indonesia

### 1.3 Adobe Firefly Approach = DIADOPSI ✅

Adobe Firefly = masterclass dalam ethical AI:
- Training HANYA pada licensed content (Adobe Stock) + public domain
- **"Every piece of content we train on is something that we have acquired the license of"** — Ely Greenfield, Adobe CTO
- Commercially safe — IP indemnification untuk enterprise
- Content Credentials (C2PA) — digital provenance
- Custom Models — enterprise train on own brand assets

**SIDIX Spark = Adobe Firefly approach untuk SIDIX:**
- Licensed-Only Pipeline
- Content Credentials (C2PA-like)
- Bias Audit
- Provenance Tracking

---

## 2. Implementasi SIDIX Spark

### 2.1 Module: `dataset_spark_curation.py`

| Function | Fungsi |
|----------|--------|
| `validate_license()` | Validate license per entry (whitelist/blacklist) |
| `create_content_credential()` | Create C2PA-like manifest per asset |
| `verify_content_credential()` | Verify manifest integrity (HMAC) |
| `audit_bias()` | Audit gender/western/professional bias |
| `curate_ethical_dataset()` | Main pipeline: validate → audit → credential → export |
| `generate_provenance_report()` | Compliance report untuk audit |
| `get_pinterest_warning()` | Educational warning untuk Pinterest |

### 2.2 Whitelist Licenses

- `agency_owned` — Google Drive agency assets
- `cc0`, `cc-by`, `cc-by-sa` — Wikimedia, Unsplash, Pexels
- `unsplash_license`, `pexels_license`
- `public_domain`
- `self_generated` — RunPod output

### 2.3 Blacklist Sources

- `pinterest`, `instagram`, `tumblr`, `deviantart`, `artstation`
- `behance`, `dribbble`, `facebook`, `twitter`, `x`

### 2.4 Content Credentials (C2PA-like)

Setiap asset punya manifest:
```json
{
  "asset_id": "sha256[:16]",
  "source": "unsplash",
  "license": "unsplash_license",
  "acquisition_date": "2026-05-08T...",
  "curator_agent": "sidix-spark",
  "provenance_hash": "sha256_full",
  "bias_audit": {...},
  "quality_score": {...},
  "hmac_signature": "tamper_evident"
}
```

### 2.5 Bias Audit Metrics

| Metric | Definition | Good Threshold |
|--------|-----------|----------------|
| Gender Balance | Distribution male/female/neutral | >= 60/100 |
| Western Content | % with western keywords | <= 70% |
| Professional Content | % studio/commercial | <= 80% |
| Overall Bias Score | Composite score | >= 70/100 |

---

## 3. Tools & Endpoints

### 5 Tools Baru (Total: 70 → **75**)

| Tool | Deskripsi |
|------|-----------|
| `spark_curate` | Ethical dataset curation pipeline |
| `spark_validate` | License validator per entry |
| `spark_bias` | Bias audit |
| `spark_pinterest_warn` | Pinterest warning |
| `spark_provenance` | Provenance report |

### 5 Endpoints Baru

| Endpoint | Method |
|----------|--------|
| `/spark/curate` | POST |
| `/spark/validate` | POST |
| `/spark/bias` | POST |
| `/spark/pinterest` | GET |
| `/spark/provenance` | POST |

---

## 4. Workflow Rekomendasi

```
Step 1: Collect raw data
  ├── Google Drive (agency assets) → agency_owned
  ├── Unsplash API → unsplash_license
  ├── Pexels API → pexels_license
  ├── Wikimedia Commons → cc-by / cc0
  └── RunPod generation → self_generated

Step 2: spark_curate(entries)
  ├── validate_license() per entry
  ├── reject blacklisted sources
  ├── audit_bias() on accepted
  ├── create_content_credential() per entry
  └── export curated.jsonl

Step 3: spark_provenance(credentials)
  └── Generate compliance report

Step 4: Train LoRA / Fine-tune
  └── Ethically curated, bias-aware, provenance-tracked
```

---

## 5. Referensi

1. Adobe Firefly: https://www.adobe.com/products/firefly.html
2. Adobe AI Ethics: https://www.adobe.com/ai/overview/firefly/gen-ai-approach.html
3. C2PA Standard: https://c2pa.org/
4. Meta Muse Spark: https://about.fb.com/news/2026/04/introducing-muse-spark-meta-superintelligence-labs/
5. Pinterest ToS: https://policy.pinterest.com/en/terms-of-service
6. Reddit vs Perplexity (2025): DMCA Section 1201 claims
7. PromptCloud Scraping Legal Guide 2026: https://www.promptcloud.com/blog/is-web-scraping-legal/

---

## 6. Changelog

| Tanggal | Versi | Perubahan |
|---------|-------|-----------|
| 2026-05-08 | v1.0 | Riset + implementasi SIDIX Spark + 5 tools + 5 endpoints |
