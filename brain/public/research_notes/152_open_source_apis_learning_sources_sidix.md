# 152. Open-Source & Public APIs — Sumber Belajar SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: data-acquisition / learning-pipeline / corpus-expansion
> **Status**: `[FACT]` (API verified available) + `[OPINION]` (prioritas)
> **Tanggal**: 2026-04-19

---

## Tujuan

SIDIX harus bisa **belajar mandiri** dari sumber-sumber berkualitas di internet,
seperti manusia membaca buku, menonton video, mendengar musik, dan melihat karya
seni. Setiap domain knowledge yang masuk → diproses jadi research note →
masuk corpus → SIDIX makin pintar.

Pipeline: **Fetch API → Parse → Chunk → Embed → Index → Research Note**

---

## KATEGORI A: VISUAL & DESAIN

### A1. Pinterest API
- **URL**: https://developers.pinterest.com/docs/api/v5/
- **Auth**: OAuth 2.0 (App + User token)
- **Limit**: 1,000 req/day (free tier)
- **Endpoint penting**:
  - `GET /v5/boards/{board_id}/pins` → ambil pin dari board
  - `GET /v5/search/pins` → search visual content
  - `GET /v5/pins/{pin_id}` → detail pin + metadata
- **Yang dipelajari SIDIX**: Tren visual desain, komposisi warna, tipografi populer
- **SIDIX integration**: Fetch 50 pin/day → extract title + description → corpus

### A2. Behance API
- **URL**: https://www.behance.net/dev/api/endpoints
- **Auth**: API Key (free developer account)
- **Endpoint penting**:
  - `GET /v2/projects?q={query}` → search proyek desain
  - `GET /v2/projects/{project_id}` → detail karya
  - `GET /v2/users/{user}/projects` → karya desainer tertentu
- **Yang dipelajari**: UX/UI design patterns, portfolio structure, creative process
- **SIDIX integration**: Weekly fetch trending Creative Fields → summarize ke note

### A3. Unsplash API
- **URL**: https://unsplash.com/developers
- **Auth**: Access Key (50 req/hour free)
- **Endpoint**: `GET /photos/random?query={topic}` → foto berkualitas tinggi + metadata
- **Yang dipelajari**: Komposisi foto, tema visual populer, alt-text writing
- **Note**: Free tier memadai untuk corpus building

### A4. Pexels API
- **URL**: https://www.pexels.com/api/
- **Auth**: API Key (gratis)
- **Limit**: 200 req/hour, 20,000/month
- **Yang dipelajari**: Video + foto stock, tren visual, keyword mapping visual

### A5. Wikimedia Commons API
- **URL**: https://commons.wikimedia.org/w/api.php
- **Auth**: None (public domain)
- **Endpoint**: `action=query&list=search&srsearch={query}`
- **Yang dipelajari**: Historical images, scientific diagrams, educational visuals
- **Best value**: Zero rate limit untuk academic content

### A6. Google Arts & Culture API (via Web Scraping / JSON-LD)
- Tidak ada API publik resmi → scrape via artsandculture.google.com (robots.txt izin)
- Alternatif: **Rijksmuseum API** (https://data.rijksmuseum.nl/object-metadata/api/)
  - Free, 10,000 req/day
  - Dataset seni dunia berlisensi open
- **Yang dipelajari**: Art history, painting analysis, cultural visual heritage

### A7. OpenGameArt API / itch.io
- **OpenGameArt**: https://opengameart.org/ (free assets, CC license)
- **itch.io API**: https://itch.io/docs/api/overview → public game jam data
- **Yang dipelajari**: Game art, pixel art, concept art methodology

### A8. Spline 3D (tidak ada API publik)
- **Alternatif**: Fetch public Spline scenes via URL → parse description + metadata
- **Sumber belajar**: docs.spline.design → corpus topik 3D web design

### A9. Sketchfab API
- **URL**: https://sketchfab.com/developers/data-api
- **Auth**: OAuth 2.0
- **Endpoint**: `GET /v3/models?q={query}` → 3D model + metadata
- **Yang dipelajari**: 3D modeling terminology, polygon count, texture workflow
- **Limit**: 100 req/min

### A10. Blender Manual (official, open)
- **URL**: https://docs.blender.org/manual/en/latest/
- **Scraping**: OK (CC-BY-SA 4.0)
- **Yang dipelajari**: 3D modeling, rigging, animation, rendering principles
- **Format**: RST → convert ke Markdown → chunk → corpus

### A11. Font Awesome / Google Fonts API
- **Google Fonts**: `GET https://www.googleapis.com/webfonts/v1/webfonts`
- **Yang dipelajari**: Typography, font pairing, readability principles

### A12. Microstock (Shutterstock / Adobe Stock)
- **Shutterstock API**: https://api-reference.shutterstock.com/ (baca metadata)
- **Adobe Stock API**: https://developer.adobe.com/stock/
- **Yang dipelajari**: Commercial stock photography taxonomy, keywording strategy
- **Note**: Hanya ambil metadata (judul, keyword, kategori) — bukan gambar aktual

### A13. Google Lens / Vision API
- **Google Cloud Vision API**: https://cloud.google.com/vision/docs
- **Free**: 1,000 units/month
- **Kemampuan**: Label detection, OCR, landmark recognition, logo detection
- **SIDIX integration**: Submit gambar → dapatkan label → pelajari visual-semantic mapping

### A14. Canva (tidak ada public API)
- **Alternatif belajar**: Canva Design School blog + YouTube channel (CC content)
- **URL**: https://www.canva.com/learn/design/ — free educational articles
- **Parse**: Article text → corpus SIDIX tentang design principles

### A15. Figma Plugin API / Community File API
- **URL**: https://www.figma.com/developers/api
- **Auth**: Personal Access Token (gratis)
- **Endpoint**: `GET /v1/files/{file_key}` → akses Figma community files
- **Yang dipelajari**: Component structure, design system, prototyping patterns

---

## KATEGORI B: AUDIO & MUSIK

### B1. Spotify Web API
- **URL**: https://developer.spotify.com/documentation/web-api
- **Auth**: OAuth 2.0 (Client Credentials untuk non-user data)
- **Limit**: Rate limit lenient untuk audio features
- **Endpoint penting**:
  - `GET /v1/search?q={query}&type=track` → search lagu
  - `GET /v1/audio-features/{id}` → fitur audio (tempo, key, energy, valence)
  - `GET /v1/audio-analysis/{id}` → segment-level analysis
  - `GET /v1/browse/categories` → kategori musik
- **Yang dipelajari**: Music theory (tempo, key, mode), genre taxonomy, mood mapping
- **SIDIX integration**: Fetch audio features 100 lagu/genre → pelajari pola emosi-musik

### B2. SoundCloud API
- **URL**: https://developers.soundcloud.com/docs/api/reference
- **Auth**: Client ID (registrasi app)
- **Endpoint**:
  - `GET /tracks?q={query}` → search track
  - `GET /tracks/{id}` → metadata + waveform data
  - `GET /users/{id}/tracks` → artist catalog
- **Yang dipelajari**: Indie music scene, electronic music production, waveform patterns

### B3. MusicBrainz API (open music database)
- **URL**: https://musicbrainz.org/doc/MusicBrainz_API
- **Auth**: None (public domain data)
- **Limit**: 1 req/second (polite)
- **Endpoint**:
  - `GET /artist?query={name}` → artist metadata
  - `GET /release?query={album}` → album data
  - `GET /recording?query={title}` → recording info
- **Yang dipelajari**: Music history, artist relations, genre evolution, discography
- **Best value**: Free, comprehensive, CC0 license

### B4. Last.fm API
- **URL**: https://www.last.fm/api
- **Auth**: API Key (gratis)
- **Endpoint**:
  - `artist.getSimilar` → rekomendasi artis serupa
  - `tag.getTopTracks` → top track per genre tag
  - `chart.getTopArtists` → tren global
- **Yang dipelajari**: Music recommendation patterns, tag-based genre taxonomy

### B5. OpenAI Whisper (audio → text)
- **Perlu diklarifikasi**: Whisper bukan API eksterna vendor tapi **open-source model**
- **Repo**: https://github.com/openai/whisper (MIT License)
- **SIDIX integration**: Transkripsi audio → teks → corpus
- **Use case**: Transkripsi podcast belajar, ceramah, tutorial video

### B6. Free Music Archive (FMA)
- **URL**: https://freemusicarchive.org/ 
- **API**: https://freemusicarchive.org/api/
- **License**: Creative Commons
- **Yang dipelajari**: Genre metadata, track descriptions, artist bios

### B7. Jamendo API
- **URL**: https://developer.jamendo.com/v3.0
- **Auth**: Client ID (gratis)
- **Konten**: 600,000+ lagu berlisensi Creative Commons
- **Yang dipelajari**: Music production metadata, mood tags, instrumentation

### B8. Bandcamp (tidak ada public API)
- **Alternatif**: Parse Bandcamp Daily articles (editorial, gratis akses)
  - URL: https://daily.bandcamp.com/
  - **Yang dipelajari**: Music criticism, underground scene, indie label ecosystem

### B9. JOOX / Resso / NetEase (regional, Asia)
- **Catatan**: Tidak ada public API tersedia untuk developer
- **Alternatif**: Scrape public playlist pages (cek robots.txt per platform)
- **Lebih baik**: Gunakan MusicBrainz/Spotify untuk metadata Asia populer

### B10. Audio Feature Extraction (Open-source)
- **librosa** (Python): Ekstraksi MFCC, pitch, tempo dari audio file
- **Essentia** (by Music Technology Group): Audio analysis library open-source
- **SIDIX integration**: Proses audio yang diunduh → ekstrak fitur → pelajari pola

---

## KATEGORI C: CODING & ENGINEERING

### C1. GitHub API (sudah ada di corpus)
- **URL**: https://docs.github.com/en/rest
- **Auth**: Token (5,000 req/hour authenticated)
- **Endpoint baru yang perlu**:
  - `GET /trending` → repo trending (via scrape, tidak ada endpoint resmi)
  - `GET /repos/{owner}/{repo}/readme` → baca README
  - `GET /search/code?q={query}` → search code snippet
  - `GET /repos/{owner}/{repo}/topics` → topik teknologi
- **Yang dipelajari**: Best practices dari open-source terpopuler

### C2. HuggingFace API (sudah ada di corpus)
- **URL**: https://huggingface.co/docs/api-inference
- **Endpoint baru**:
  - `GET /api/models?filter={task}` → daftar model per task
  - `GET /api/datasets?filter={domain}` → dataset publik
  - `GET /api/papers` → research paper terbaru
- **Yang dipelajari**: State-of-the-art ML models, dataset taxonomy, paper abstracts

### C3. roadmap.sh (sudah ada di corpus)
- **Source**: https://github.com/kamranahmedse/developer-roadmap
- **Format**: Markdown + JSON roadmap data (CC BY-SA 4.0)
- **Tambahan belum di-fetch**: `ai-data-scientist`, `mlops`, `cyber-security`,
  `blockchain`, `game-developer`, `ux-design`, `product-manager`
- **Script update**: `scripts/fetch_roadmap_updates.sh`

### C4. DevDocs API / Docs.rs
- **URL**: https://devdocs.io/ (free, open-source)
- **Fetch**: Semua dokumentasi framework populer dalam format JSON
- **Yang dipelajari**: FastAPI, React, Django, Go stdlib, Rust, etc.

### C5. Stack Overflow Data Dump
- **URL**: https://archive.org/details/stackexchange
- **License**: CC BY-SA 4.0
- **Format**: XML dump (besar — perlu filtering)
- **Yang dipelajari**: Common errors & solutions, Q&A patterns, programming debates

### C6. MDN Web Docs API / Scrape
- **URL**: https://developer.mozilla.org/en-US/docs/
- **Fetch**: Fetch halaman spesifik (HTML/Fetch API, CSS Grid, etc.)
- **License**: CC BY-SA 2.5
- **Yang dipelajari**: Web standards, browser APIs, accessibility

### C7. Papers With Code API
- **URL**: https://paperswithcode.com/api/v1/
- **Auth**: None (public)
- **Endpoint**:
  - `GET /api/v1/papers?` → search paper + code links
  - `GET /api/v1/methods/` → ML method taxonomy
  - `GET /api/v1/benchmarks/` → benchmark leaderboard
- **Yang dipelajari**: ML research trends, SOTA metrics, new architectures

### C8. arXiv API
- **URL**: https://arxiv.org/help/api/
- **Auth**: None (open access)
- **Endpoint**: `GET http://export.arxiv.org/api/query?search_query=ti:{topic}`
- **Limit**: Polite 3 req/second
- **Yang dipelajari**: Cutting-edge research (cs.AI, cs.CL, cs.CV, cs.LG)

### C9. Wikipedia / Wikidata API
- **URL**: https://www.mediawiki.org/wiki/API:Main_page
- **Auth**: None
- **Best endpoints**:
  - `action=query&prop=extracts&exintro=1&titles={article}` → article summary
  - `action=query&list=search&srsearch={query}` → search
- **Yang dipelajari**: Factual knowledge base semua domain

### C10. CommonCrawl (web-scale corpus)
- **URL**: https://commoncrawl.org/
- **License**: Open dataset (CC)
- **Yang dipelajari**: Bahasa natural dari seluruh web
- **Note**: Dataset sangat besar (petabyte) → perlu filter subset Indonesia + Arab

---

## KATEGORI D: PENGETAHUAN ISLAMI & ILMU TRADISIONAL

### D1. Quran.com API
- **URL**: https://api.quran.com/documentation
- **Auth**: None (open)
- **Endpoint**:
  - `GET /v4/verses/by_chapter/{chapter_number}`
  - `GET /v4/search?q={query}` → semantic search Quran
  - `GET /v4/tafsirs` → daftar tafsir tersedia
- **Yang dipelajari**: Teks Quran, terjemahan, tafsir, word-level metadata

### D2. Sunnah.com API
- **URL**: https://sunnah.com/developers (coming soon)
- **Alternatif**: https://hadith.inpsites.co/ (Hadith API JSON, gratis)
- **Yang dipelajari**: Hadith collections (Bukhari, Muslim, Abu Dawud, dll)

### D3. Perseus Digital Library (classical texts)
- **URL**: http://www.perseus.tufts.edu/hopper/
- **API**: Perseus API + CTS protocol
- **Yang dipelajari**: Classical Arabic, Greek philosophy, historical linguistics

### D4. Internet Archive API
- **URL**: https://archive.org/developers/internetarchive/
- **Auth**: None untuk baca
- **Yang dipelajari**: Historical books, old scientific papers, cultural heritage

---

## KATEGORI E: DATA DUNIA & SAINS

### E1. Open-Meteo (cuaca, gratis)
- **URL**: https://open-meteo.com/en/docs
- **Yang dipelajari**: Weather patterns, climate data, scientific forecasting

### E2. OpenStreetMap / Nominatim API
- **URL**: https://nominatim.org/release-docs/latest/api/
- **Yang dipelajari**: Geographic knowledge, place names, spatial reasoning

### E3. World Bank Open Data API
- **URL**: https://datahelpdesk.worldbank.org/knowledgebase/topics/125589
- **Yang dipelajari**: Economic indicators, development data, global statistics

### E4. NASA Open APIs
- **URL**: https://api.nasa.gov/
- **Auth**: API Key (gratis)
- **Endpoints**:
  - APOD (Astronomy Picture of Day)
  - Mars Rover Photos
  - NASA Image and Video Library
- **Yang dipelajari**: Space science, astronomy, earth observation

### E5. FRED Economic Data (Federal Reserve)
- **URL**: https://fred.stlouisfed.org/docs/api/fred/
- **Auth**: API Key (gratis)
- **Yang dipelajari**: Macroeconomics, financial indicators, time series analysis

---

## Implementasi Crawler Pipeline

```python
# apps/brain_qa/brain_qa/learn_agent.py (rencana)

class LearnAgent:
    """
    Autonomous learning sub-agent yang fetch data dari berbagai sumber.
    
    Loop:
    1. Pick source dari learning_queue
    2. Fetch via API / scrape (respectful rate limit)
    3. Parse + clean + chunk
    4. Check duplikasi vs existing corpus (cosine sim > 0.85 → skip)
    5. Generate research note otomatis
    6. Update corpus index
    7. Log ke LIVING_LOG
    """
    
    SOURCES = {
        "visual": ["pinterest", "behance", "unsplash", "sketchfab"],
        "audio": ["spotify", "musicbrainz", "lastfm", "fma"],
        "code": ["github", "huggingface", "arxiv", "papers_with_code"],
        "islamic": ["quran_com", "hadith_api", "internet_archive"],
        "science": ["nasa", "world_bank", "wikipedia"],
    }
    
    def run_daily_fetch(self, domain: str = "all"):
        """Jalankan fetch harian per domain."""
    
    def parse_and_chunk(self, raw: str, source_id: str) -> list[dict]:
        """Parse konten mentah → chunk 1200 char dengan overlap."""
    
    def is_duplicate(self, chunk: str) -> bool:
        """BM25 + cosine sim check vs existing corpus."""
    
    def auto_research_note(self, chunks: list, source: str) -> str:
        """Generate research note markdown dari chunks."""
```

---

## Prioritas Implementasi

| Prioritas | Source | Alasan |
|-----------|--------|--------|
| 🔴 P1 | arXiv API | Research terbaru, free, critical untuk epistemic |
| 🔴 P1 | Wikipedia API | Knowledge base terluas, free |
| 🟠 P2 | MusicBrainz | Free, comprehensive, CC0 |
| 🟠 P2 | GitHub trending | Coding currency |
| 🟠 P2 | Quran.com API | Core epistemic source |
| 🟡 P3 | Spotify audio features | Unique ML angle |
| 🟡 P3 | Unsplash/Pexels | Visual corpus |
| 🟡 P3 | Papers With Code | ML benchmark tracking |
| 🟢 P4 | Sketchfab/Blender docs | 3D domain |
| 🟢 P4 | NASA APIs | Science enrichment |

---

## Keterbatasan Jujur

1. **Rate limits** — semua API punya batas; perlu exponential backoff + antrian
2. **License compliance** — cek lisensi sebelum train (CC-BY: OK, NC: perlu review)
3. **Quality filtering** — tidak semua konten berkualitas; perlu confidence score
4. **Storage** — audio/gambar besar; simpan metadata saja, bukan binary
5. **Legal grey area** — beberapa platform larang scraping di ToS meski data publik

---

## Sumber Referensi

- Semua URL API di atas adalah publik dan terverifikasi available per 2026
- License summary: CC0 > CC-BY > CC-BY-SA (semua OK untuk non-commercial)
- robots.txt wajib dicek sebelum scraping
