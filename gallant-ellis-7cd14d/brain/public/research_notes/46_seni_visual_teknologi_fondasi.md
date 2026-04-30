# Research Note 46 — Seni Visual & Teknologi: Fondasi Lintas Disiplin

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-17  
**Sumber**: "Mendalami Seni Visual dan Teknologi" (PDF, 16 hal.)  
**Relevansi SIDIX**: VLM context, image captioning pipeline, ethics framework, UI/UX design vocabulary  
**Tags**: `fotografi`, `seni-lukis`, `desain-grafis`, `multimedia`, `deepfake`, `etika-visual`, `AI-generatif`

---

## 1. Fotografi — Sejarah & Fondasi Teknis

### 1.1 Timeline Sejarah
| Tahun | Milestone |
|-------|-----------|
| 1826  | Niépce — foto pertama dunia (8 jam exposure) |
| 1839  | Daguerreotype — komersial, 20-30 menit exposure |
| 1884  | Roll film seluloid (Eastman/Kodak) |
| 1936  | Kodachrome — film warna pertama berkualitas tinggi |
| 1975  | Sensor digital pertama (Kodak, 100×100 px) |
| 1990s | CCD → CMOS, kamera digital consumer |
| 2007+ | Smartphone camera, komputasi fotografi |
| 2020+ | AI photography: Generative Fill, computational HDR |

### 1.2 Exposure Triangle

```
        APERTURE (f-stop)
       /                 \
      /  Depth of Field   \
     /                     \
SHUTTER ─────────────── ISO
Speed              Noise / Gain
(Motion)
```

**Aperture (f-number)**:
- Formula: `f = focal_length / aperture_diameter`
- f/1.4 → bukaan besar → depth of field dangkal (bokeh) → low light baik
- f/16 → bukaan kecil → depth of field dalam → landscape tajam
- Hubungan invers: angka f besar = bukaan kecil

**Shutter Speed**:
- Cepat (1/1000s) → freeze motion (olahraga, air)
- Lambat (1/30s-beberapa detik) → motion blur (light painting, air terjun)
- Rule of thumb: min shutter = 1/focal_length untuk mencegah camera shake

**ISO**:
- ISO 100 = clean, rendah noise (siang hari)
- ISO 3200+ = noise tinggi, tapi low light capable
- Modern sensor: ISO 12800+ usable dengan noise reduction

### 1.3 Optik Kamera
- **Refraksi**: cahaya melambat saat masuk lensa → membengkok menuju focal point
- **Aberrasi sferis**: cahaya pinggir lensa tidak fokus sempurna → perlu koreksi asferis
- **Chromatic aberration**: panjang gelombang berbeda → titik fokus berbeda → fringing warna
- **Depth of field** ditentukan oleh: aperture + jarak fokus + panjang focal

---

## 2. Seni Lukis — Pigmen & Teori Warna

### 2.1 Ilmu Pigmen

**Pigmen Anorganik**:
- Bahan: logam dan mineral (titanium dioxide, ochre, ultramarine)
- Kelebihan: stabilitas tinggi, tahan UV, tahan lama berabad-abad
- Kelemahan: beberapa beracun (timbal putih, vermilion merkuri)
- Contoh: lapis lazuli (biru ultramarine asli, > emas di abad pertengahan)

**Pigmen Organik**:
- Bahan: berbasis karbon (karmin dari cochineal, indigo dari tanaman)
- Kelebihan: warna cerah, transparan, excellent untuk glazing
- Kelemahan: cenderung lebih cepat pudar (fugitive colors)
- Modern synthetic organic: cadmium-free alternatives, high chroma

### 2.2 Color Mixing Systems

**Subtraktif — CMYK (Printing)**:
```
Cyan + Magenta + Yellow = Black (teoritis)
Real printing: tambah K (Key/Black) untuk detail
Semua warna dicampur → menyerap lebih banyak cahaya
```
- Digunakan: cat, printer, offset printing
- Basis: pigmen menyerap sebagian spectrum, memantulkan sisanya

**Aditif — RGB (Screens)**:
```
Red + Green + Blue = White
Tidak ada cahaya = Black
```
- Digunakan: monitor, TV, LED, proyektor
- Basis: emisi cahaya langsung

**Penting untuk AI Image Generation**:
- Model SD/Flux bekerja di color space RGB (latent space)
- CMYK conversion diperlukan saat output ke print
- Color accuracy: sRGB vs Adobe RGB vs P3 display gamut

### 2.3 Bauhaus & Filosofi Desain

**Bauhaus (1919–1933)**:
- Didirikan: Walter Gropius, Weimar Jerman
- Filosofi utama: **"Form Follows Function"** — keindahan lahir dari fungsi, bukan ornamen
- Pendekatan: Vorkurs (kursus dasar wajib) — latih semua indera sebelum spesialisasi
- Legacy: modernisme desain, tipografi sans-serif, grid system

**Relevansi ke AI Design**:
- Prinsip Bauhaus = filter evaluasi kualitas output AI
- Prompt engineering yang baik mengikuti prinsip: "apa fungsinya?" baru "bagaimana tampilannya?"
- SIDIX bisa gunakan Bauhaus principles sebagai rubrik evaluasi visual

---

## 3. Desain Grafis — Prinsip & Sistem

### 3.1 Lima Prinsip Desain Grafis

**1. Hierarki Visual**
- Maksimum 3 ukuran font dalam satu layout
- Kontras ukuran: heading (>24pt) → subheading (~16pt) → body (~12pt)
- Mata pembaca otomatis scan dari elemen terbesar

**2. Skala & Proporsi**
- Golden ratio (1:1.618) — secara natural terasa harmonis
- Rule of thirds: bagi kanvas 3×3, letakkan focal point di interseksi
- Skala ekstrem (sangat besar vs sangat kecil) menciptakan drama visual

**3. Grid System**
- 12-column grid: paling fleksibel untuk web dan print
- Gutter: jarak antar kolom (min 16px web)
- Baseline grid: konsistensi vertical rhythm teks

**4. Tipografi**
- **Leading** (line-height): ruang antar baris → optimal 120–145% dari font size
- **Kerning**: penyesuaian spasi antar karakter spesifik (pasangan AV, Te, dll.)
- **Tracking**: spasi seragam seluruh teks → negative tracking = padat, positive = lapang
- Font pairing: serif + sans-serif (klasik), tidak mixing >2 typeface family

**5. Negative Space (White Space)**
- Ruang kosong = elemen aktif, bukan kekosongan
- Micro white space: antar huruf, baris, paragraf
- Macro white space: antar section, margin
- Apple, Google menggunakan negative space sebagai sinyal premium

### 3.2 Information Architecture — 8 Prinsip

| Prinsip | Definisi | Contoh Aplikasi |
|---------|----------|-----------------|
| Object | Konten adalah entitas hidup dengan siklus hidup | Artikel punya created/updated/archived |
| Choice | Tawarkan pilihan bermakna, bukan berlebihan | Menu navigasi max 7 item |
| Disclosure | Tampilkan cukup untuk membuat keputusan | Preview sebelum full content |
| Exemplars | Contoh konkret menjelaskan kategori abstrak | Thumbnail di kategori produk |
| Front Door | Pengguna masuk dari mana saja, bukan hanya homepage | Deep link harus kontekstual |
| Dual Classification | Satu item bisa masuk banyak kategori | Tag sistem vs hierarki tunggal |
| Navigation | Navigasi = percakapan antara sistem dan pengguna | Breadcrumb + search + menu |
| Growth | Sistem harus scale dengan pertumbuhan konten | Taksonomi fleksibel |

**Relevansi SIDIX**:
- IA principles = fondasi UI otak SIDIX (jika ada dashboard)
- "Front Door" principle → setiap entry point harus kontekstual (deep link ke hasil RAG)
- "Growth" principle → BM25 index harus bisa scale tanpa redesign

---

## 4. Multimedia & Codec Landscape 2026

### 4.1 Video Codec Comparison

| Codec | Efisiensi | Lisensi | Adopsi | Status |
|-------|-----------|---------|--------|--------|
| H.264 (AVC) | Baseline | FRAND | Universal | Mature |
| H.265 (HEVC) | +50% vs H.264 | Kompleks, mahal | Terbatas | Active |
| VP9 | +40% vs H.264 | Royalti-free | YouTube | Stable |
| AV1 | +30% vs VP9 | Royalti-free (AOMedia) | Netflix, YouTube | Growing |
| AV2 | +40% vs AV1 | Royalti-free | Belum luas | Finalized 2025 |

**Key Insight**:
- AV2 finalized 2025: lebih efisien 40% dari AV1 → streaming masa depan
- H.265 kompleksitas lisensi = hambatan adopsi (3 patent pool berbeda)
- AV1/AV2 = masa depan streaming open web

### 4.2 Audio Considerations
- **Lossless**: FLAC, ALAC (archival, produksi)
- **Lossy**: MP3 (legacy), AAC (Apple ecosystem), Opus (WebRTC, paling efisien)
- **Spatial audio**: Dolby Atmos, Apple Spatial Audio (object-based, 3D)

---

## 5. AI Photography & Paradoks Kesempurnaan

### 5.1 AI Photography Tools (2026)

**Generative Fill** (Adobe Photoshop):
- Expand foto melampaui batas frame asli
- Remove/replace objek dengan content-aware synthesis
- Powered by Firefly model (Adobe's foundation model)

**Computational Photography**:
- Multi-frame HDR: ambil 5+ exposure, merge AI
- Night mode: de-noise + sharpen dari puluhan frame
- Semantic segmentation: pisahkan subjek/background otomatis
- Google Pixel / Apple iPhone: Neural Engine untuk real-time processing

### 5.2 Paradoks Kesempurnaan

> Semakin AI mampu menghasilkan gambar sempurna secara teknis, semakin penonton menghargai ketidaksempurnaan sebagai penanda keaslian.

**Manifestasi**:
- Film grain filter: noise buatan → "terasa nyata"
- Vignetting artifisial: sudut gelap → "foto analog"
- Chromatic aberration: fringing → "lensa fisik"
- Blur/bokeh buatan: depth effect → "dikerjakan manusia"

**Implikasi AI generatif**:
- Prompt "shot on 35mm film, grain, slight blur" → lebih engaging dari "perfect photo"
- Uncanny valley: terlalu sempurna → tidak dipercaya
- Future branding: "no AI" atau "minimal AI" sebagai premium signal

**Relevansi SIDIX**:
- Ketika SIDIX generate deskripsi visual, gunakan bahasa yang "human" bukan "AI-perfect"
- Respons yang natural > respons yang sempurna

---

## 6. Deepfakes & Kontra-Measure

### 6.1 Deepfake Technology Stack
- **Face swapping**: encoder-decoder architecture, latent space manipulation
- **Voice cloning**: TTS + fine-tuning pada sample suara target
- **Full video synthesis**: latent diffusion → high-resolution face replacement
- **Real-time deepfake**: GPU-accelerated inference, ~30fps capable (2025)

### 6.2 Detection & Counter-Measures

**Digital Watermarking**:
- Invisible watermark embed di pixel level (C2PA standard)
- Survives JPEG compression, resize, slight cropping
- Decoding via private key → trace back ke sumber generasi

**Provenance Tags (C2PA)**:
- Coalition for Content Provenance and Authenticity
- Metadata chain: kamera → edit → publish → semua tercatat
- Adobe, Microsoft, Google, BBC support
- Verifikasi: `verify.contentauthenticity.org`

**Behavioral Detection**:
- Blink pattern unnatural (early deepfakes)
- Facial boundary artifacts (ears, hairline, jawline)
- Lighting inconsistency: bayangan tidak sesuai light source
- Temporal consistency: frame-by-frame jitter di AI video

**Relevansi SIDIX**:
- SIDIX harus bisa label: "Gambar ini berpotensi AI-generated"
- Integrasi C2PA metadata reading jika processing images
- Ethics framework: jangan bantu buat konten deceptive

---

## 7. Etika Visual

### 7.1 Inklusivitas & Representasi
- Representasi keragaman: warna kulit, gender, usia, disabilitas dalam konten visual
- Bias dataset: model dilatih pada data Barat → under-represent Global South
- SIDIX responsibility: ketika generate/suggest visual, aware of representation gap

### 7.2 Aksesibilitas (WCAG)
- **Contrast ratio**: teks normal min 4.5:1, teks besar min 3:1
- **Alt text**: deskripsi gambar untuk screen reader
- **Color independence**: informasi tidak boleh hanya dari warna (color blindness 8% pria)
- **Motion**: animasi > 3 kali/detik bisa trigger photosensitive epilepsy (WCAG 2.3.1)

### 7.3 Ethical Storytelling
- Context collapse: foto tanpa konteks → misleading
- Dignity-preserving: foto korban bencana harus preservasi martabat
- Consent: model/subjek foto harus informed consent
- Satire vs defamation: AI-generated satire harus jelas labeled

---

## 8. Implikasi & Peluang untuk SIDIX

### 8.1 Kemampuan Baru yang Perlu Dibangun

| Kemampuan | Module | Priority |
|-----------|--------|----------|
| Caption visual (ALT text) | VLM integration (Qwen2.5-VL) | HIGH |
| Analisis komposisi foto | Visual critique engine | MEDIUM |
| Codec recommendation | Multimedia advisor | LOW |
| Deepfake detection | Media trust layer | HIGH |
| Design critique (Bauhaus) | Design review tool | MEDIUM |

### 8.2 Vocabulary untuk Better Prompting

SIDIX perlu memahami istilah visual agar bisa:
1. **Parse prompt visual**: "foto bokeh f/1.8 golden hour" → tahu artinya
2. **Generate caption deskriptif**: aperture, lighting, komposisi
3. **Recommend visual approach**: untuk konten UMKM, pendidikan, dakwah

### 8.3 Nusantara Visual Identity
- **Batik**: 72 motif resmi, setiap motif punya makna filosofis
- **Wayang**: shadow puppet, silhouette-based, 2D stylized
- **Tenun Ikat**: tie-dye weaving, regional patterns
- **Peluang**: dataset visual Nusantara + caption bahasa Indonesia → foundation untuk image model lokal

### 8.4 Islamic Visual Ethics Framework
- **Tasawwur Islami**: gambar harus tidak bertentangan dengan maqashid syariah
- **Taswir**: ada perbedaan pendapat ulama tentang gambar makhluk bernyawa
- **Safe defaults**: SIDIX default ke non-figural untuk konten Islami formal
- **Context-sensitive**: untuk edukasi medis/sains, figuratif diperbolehkan dengan niat baik

---

## 9. Ringkasan untuk Corpus SIDIX

```
KEYWORD CLUSTERS:
- fotografi: exposure, aperture, ISO, shutter, bokeh, depth-of-field, RAW, JPEG
- warna: RGB, CMYK, saturation, hue, value, complementary, analogous, triadic  
- komposisi: rule-of-thirds, leading-lines, symmetry, negative-space, framing
- tipografi: serif, sans-serif, leading, kerning, tracking, hierarchy, weight
- codec: H.264, H.265, AV1, AV2, bitrate, compression, lossless, lossy
- AI-visual: generative-fill, deepfake, C2PA, watermark, LoRA, latent-diffusion
- desain: bauhaus, grid, whitespace, information-architecture, UX, UI
- etika: WCAG, inklusif, consent, provenance, representation
```

---

*Research note ini menjadi fondasi vocabulary visual untuk SIDIX — agar agent dapat memahami, menganalisis, dan merespons pertanyaan seputar fotografi, desain, dan multimedia dengan konteks yang tepat.*
