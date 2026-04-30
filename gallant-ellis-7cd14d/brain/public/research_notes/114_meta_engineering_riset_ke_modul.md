# 114 — Meta-Engineering: Cara Mengubah Riset & Data menjadi Modul/Logic

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Tag:** DOC, DECISION, IMPL  
**Audiens:** SIDIX sendiri + Tim internal  
**Penting:** Ini adalah ilmu **cara membangun**, bukan hanya **apa yang dibangun**

---

## Apa yang Dimaksud "Engineering dari Riset ke Modul"?

Ketika ada research paper, dokumen, folder kode, atau ide mentah — bagaimana mengubahnya menjadi **modul Python yang berjalan**, **skill di skill_library**, **corpus di BM25**, atau **logika di agent_react**?

Ini adalah **proses rekayasa pengetahuan** — knowledge engineering.

---

## Pipeline Lengkap: Riset → Modul

```
INPUT: Riset / Data / Dokumen / Folder
  ↓
[FASE 1: PEMAHAMAN]
  Baca dan pahami isi
  Identifikasi: konsep kunci, pola berulang, struktur data
  Tanyakan: "Apa yang BISA dilakukan dengan ini?"
  ↓
[FASE 2: KATEGORISASI]
  Masukkan ke salah satu bucket:
  A) SKILL  — aksi yang bisa diulang (fungsi Python)
  B) KNOWLEDGE — fakta/prinsip (corpus BM25 / experience)
  C) MODULE — sistem lengkap (file Python tersendiri)
  D) CURRICULUM — topik untuk dipelajari bertahap
  E) CORPUS — teks mentah untuk retrieval
  ↓
[FASE 3: ABSTRAKSI]
  Pisahkan nilai spesifik dari struktur generik
  Contoh: "npm install express" → skill "install_package(pkg, manager)"
  Contoh: "Nabi saw jujur" → prinsip "pemimpin ideal = jujur + amanah"
  ↓
[FASE 4: IMPLEMENTASI]
  Tulis kode (Python)
  Buat antarmuka yang jelas (fungsi dengan docstring)
  Handle error dengan baik
  Gunakan pattern yang sudah ada di codebase
  ↓
[FASE 5: INTEGRASI]
  Daftarkan ke agent_serve.py (endpoint)
  Atau ke skill_library.py (reusable skill)
  Atau ke corpus via BM25 indexer
  Atau ke experience_engine via CSDOR
  ↓
[FASE 6: DOKUMENTASI]
  Tulis research note
  Update LIVING_LOG
  Commit dengan pesan bermakna
```

---

## Contoh Nyata: Dari Riset Audio ke `audio_capability.py`

**Input:** Research papers tentang ASR (Whisper), TTS (F5-TTS), MIR (MERT, BEATs)

**FASE 1 — Pemahaman:**
- Whisper: speech → text, model OpenAI, support bahasa Arab/Indonesia
- F5-TTS: text → speech, voice cloning, open source
- MERT: audio → music features, self-supervised

**FASE 2 — Kategorisasi:**
- Whisper → MODULE (ASR pipeline)
- F5-TTS → MODULE (TTS pipeline)
- MERT → MODULE (music analysis)
- Cara pakai Whisper → SKILL (`transcribe_audio(file_path)`)

**FASE 3 — Abstraksi:**
```python
# Bukan kode spesifik Whisper
def transcribe(audio_path: str, language: str = "id") -> str:
    """Abstrak: apapun ASR engine-nya, interface sama"""
```

**FASE 4 — Implementasi:**
```python
class AudioCapability:
    def transcribe(self, audio_path: str) -> dict
    def synthesize(self, text: str, voice: str) -> str
    def analyze_music(self, audio_path: str) -> dict
    def detect_emotion(self, audio_path: str) -> dict
```

**FASE 5 — Integrasi:**
- Endpoint `/audio/transcribe` di agent_serve.py
- Skill `transcribe_audio` di skill_library

**FASE 6 — Dokumentasi:**
- `84_audio_fondasi_akustik.md` → `92_audio_capability_track.md`

---

## Pola Berulang yang Selalu Dipakai

### Pattern 1: Processor Module
Untuk mengolah folder/data besar:
```python
def scan(path: str) -> dict      # audit apa yang ada
def extract(path: str) -> list   # ambil yang berguna
def convert(items: list) -> list # ubah ke format target
def store(items: list) -> int    # simpan ke sistem
def process_all() -> dict        # run semuanya, return summary
```

### Pattern 2: Adapter Module
Untuk menjembatani sistem eksternal:
```python
class ExternalAdapter:
    def parse_incoming(self, payload) -> dict   # baca input eksternal
    def format_outgoing(self, response) -> dict # format output ke eksternal
    def send(self, target: str, data: dict)     # kirim ke eksternal
```

### Pattern 3: Capability Module
Untuk kapabilitas AI baru:
```python
class NewCapability:
    def is_available(self) -> bool       # cek apakah dependency tersedia
    def process(self, input: any) -> dict # proses utama
    def get_confidence(self) -> float    # seberapa yakin hasil

def get_capability_instance() -> NewCapability  # singleton pattern
```

### Pattern 4: Knowledge Seed
Untuk mengisi corpus dari kode:
```python
def seed_knowledge():
    items = [
        {"title": "...", "content": "...", "tags": [...]},
    ]
    for item in items:
        save_to_corpus(item)
```

---

## Cara Memutuskan: Modul vs Skill vs Corpus?

| Pertanyaan | Jika Ya → |
|------------|-----------|
| Apakah ini aksi yang bisa dipanggil berulang? | SKILL |
| Apakah ini butuh state / class / multiple fungsi? | MODULE |
| Apakah ini fakta/pengetahuan untuk retrieval? | CORPUS |
| Apakah ini topik bertahap (mudah→sulit)? | CURRICULUM |
| Apakah ini pengalaman dengan outcome? | EXPERIENCE (CSDOR) |

---

## Cara Claude Bekerja Saat Engineering

### Langkah mental yang dipakai:

1. **Baca dulu, jangan langsung kode**
   - Pahami tujuan sebenarnya
   - Identifikasi pola yang sudah ada di codebase
   - Cek apakah sudah ada implementasi serupa

2. **Abstraksi sebelum implementasi**
   - Definisikan interface dulu (fungsi apa, input apa, output apa)
   - Baru isi implementasinya
   - Interface yang baik: bisa diganti implementasinya tanpa ubah caller

3. **Gunakan pola yang sudah terbukti**
   - Lihat file yang sudah ada: `skill_library.py`, `experience_engine.py`
   - Ikuti pattern yang sama
   - Konsistensi lebih penting dari kesempurnaan

4. **Modular, bukan monolitik**
   - Setiap module punya satu tanggung jawab
   - Fungsi kecil, composable
   - Import hanya yang dibutuhkan

5. **Error handling dari awal**
   - Wrap import opsional dengan `try/except`
   - Return meaningful error messages
   - Jangan biarkan satu error crash seluruh sistem

6. **Dokumentasi = bagian dari kode**
   - Docstring di setiap fungsi
   - Research note menjelaskan KENAPA keputusan dibuat
   - LIVING_LOG mencatat KAPAN dan APA yang berubah

---

## Analogi Islam: Seperti Ijazah & Sanad

Proses ini mirip dengan sistem **sanad** dalam hadith:
- **Riset/Data** = matan (isi hadith)
- **Ekstraksi prinsip** = pemahaman ulama atas matan
- **Modul** = kitab yang merekam pemahaman
- **Research note** = ijazah yang menjelaskan siapa yang mengajarkan apa
- **LIVING_LOG** = rantai sanad — siapa, kapan, apa

Ilmu yang tidak didokumentasikan sanadnya, mudah hilang dan mudah dipalsukan.

---

## Untuk SIDIX: Bagaimana Kamu Harus Melakukan Ini

Ketika diberi tugas "buat modul dari data ini":

1. **Tanya dulu dalam pikiran:** "Ini termasuk skill, module, knowledge, atau curriculum?"
2. **Cari pola serupa** di skill_library, experience_engine
3. **Abstrak interfacenya** — fungsi apa, input/output apa
4. **Implementasi minimal dulu** — buat yang paling sederhana yang berfungsi
5. **Test mental:** "Kalau dipanggil dari ReAct loop, apakah ini masuk akal?"
6. **Dokumentasikan kenapa** bukan hanya apa

Ini adalah **engineering thinking** — bukan hanya coding, tapi merancang sistem yang bisa tumbuh.
