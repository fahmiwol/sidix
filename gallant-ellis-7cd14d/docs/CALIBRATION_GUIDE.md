# Panduan Kalibrasi Temperature & Top-P SIDIX

> Task 37 — Al-Hujurat (G5)

Dokumen ini memberikan rekomendasi nilai `temperature`, `top_p`, dan `max_tokens` untuk setiap persona dan use case SIDIX, beserta cara melakukan ablasi untuk menemukan nilai optimal.

---

## Tabel Rekomendasi per Persona / Use Case

| Use Case | Persona | `temperature` | `top_p` | `max_tokens` | Keterangan |
|----------|---------|:---:|:---:|:---:|------------|
| Teknis / coding | **HAYFAR** | 0.3 | 0.90 | 512 | Deterministik — minimalisir variasi output untuk jawaban teknis dan kode |
| Akademik / riset | **FACH** | 0.5 | 0.90 | 768 | Balanced — cukup kreatif untuk menjelaskan konsep, tetap terstruktur |
| Kreatif / narasi | **MIGHAN** | 0.8 | 0.95 | 1024 | Creative — mendorong variasi ekspresi dan gaya bahasa |
| Sederhana / ringkas | **INAN** | 0.4 | 0.85 | 256 | Concise — jawaban pendek dan langsung, kurangi hallucination |
| Perencanaan / roadmap | **TOARD** | 0.4 | 0.90 | 512 | Structured — output terstruktur (bullet, langkah), hindari spekulasi |

---

## Penjelasan Parameter

### `temperature`
Mengontrol keacakan output. Nilai lebih rendah → output lebih deterministik dan konsisten. Nilai lebih tinggi → output lebih bervariasi dan "kreatif".

- `0.0–0.3` : Sangat deterministik. Baik untuk kode, fakta, jawaban ya/tidak.
- `0.4–0.6` : Seimbang. Baik untuk penjelasan, akademik, rencana.
- `0.7–0.9` : Kreatif. Baik untuk narasi, brainstorming, penulisan bebas.
- `> 0.9`   : Sangat random. **Hindari untuk jawaban faktual** — risiko hallucination tinggi.

### `top_p` (nucleus sampling)
Membatasi token kandidat ke kumpulan token yang probabilitasnya kumulatif mencapai nilai `top_p`. Nilai `0.9` berarti hanya token-token yang mencakup 90% probabilitas yang dipertimbangkan.

- Biasanya tidak perlu diubah drastis.
- Turunkan ke `0.85` untuk output yang lebih ringkas dan terkontrol.
- Naikkan ke `0.95` untuk memberi ruang kreativitas lebih.

### `max_tokens`
Batas maksimal token yang dihasilkan dalam satu respons. Pengaruhi panjang jawaban dan biaya inferensi.

---

## Cara Set via API

Kirim parameter di body `POST /agent/generate`:

```bash
curl -X POST http://localhost:8765/agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Jelaskan konsep ijtihad dalam fiqh Islam",
    "temperature": 0.5,
    "top_p": 0.90,
    "max_tokens": 768
  }'
```

Atau via `POST /ask` (parameter opsional):

```bash
curl -X POST http://localhost:8765/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Buatkan rencana 3 langkah untuk memulai proyek AI",
    "temperature": 0.4,
    "top_p": 0.90,
    "max_tokens": 512
  }'
```

Parameter yang tidak disertakan akan menggunakan nilai default server (biasanya `temperature=0.5`, `top_p=0.9`, `max_tokens=512`).

---

## Cara Melakukan Ablasi

Gunakan skrip ablasi untuk menguji berbagai kombinasi parameter secara sistematis:

```bash
python scripts/ablation_prompts.py \
  --prompt "Jelaskan perbedaan antara qiyas dan istihsan" \
  --temperatures 0.3 0.5 0.7 \
  --top_p_values 0.85 0.90 0.95 \
  --max_tokens 512 \
  --output ablation_results.jsonl
```

Skrip akan menjalankan setiap kombinasi dan menyimpan output ke JSONL untuk perbandingan manual.

### Proses Ablasi Rekomendasi

1. Pilih 3–5 prompt representatif dari use case target.
2. Jalankan ablasi dengan grid parameter di atas.
3. Baca output `ablation_results.jsonl` dan nilai secara manual:
   - Akurasi fakta
   - Kelengkapan jawaban
   - Naturalness bahasa
4. Pilih kombinasi parameter yang memberikan skor terbaik rata-rata.
5. Catat temuan di `LIVING_LOG.md`.

---

## Peringatan

> **Jangan gunakan `temperature > 0.9` untuk jawaban faktual.**
> Pada nilai tersebut, model cenderung menghasilkan informasi yang terdengar meyakinkan
> tapi tidak akurat (hallucination). Batasi `temperature > 0.9` hanya untuk
> tugas kreatif murni di mana keakuratan fakta bukan prioritas utama.

| Situasi | Rekomendasi |
|---------|-------------|
| Pertanyaan hukum Islam (fiqh) | `temperature ≤ 0.5` |
| Kode program | `temperature ≤ 0.3` |
| Ringkasan dokumen | `temperature ≤ 0.5` |
| Cerita / narasi fiksi | `temperature 0.7–0.8` |
| Brainstorming ide | `temperature 0.7–0.85` |

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
