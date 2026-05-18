# 134. Baca → Paham → Ingat → Ceritakan — Siklus Belajar SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: ai / epistemologi  
> **Fase**: 3 (refinement pipeline autonomous_researcher)  
> **Tanggal**: 2026-04-18

---

## Prinsip Inti

SIDIX tidak boleh sekadar **menampilkan** hasil fetch mentah. Dia harus menjalani
siklus lengkap layaknya manusia belajar:

```
BACA        →   PAHAMI         →   INGAT           →   CERITAKAN
(fetch)         (comprehend)       (persist memory)     (narrate + cite)
```

Setiap tahap wajib — melewati salah satu = gagal sebagai pembelajar.

## Kenapa Empat Tahap, Bukan Dua?

Arsitektur lama (dump-and-format) hanya: fetch → tempel. Masalahnya:
- User dapat tembok teks yang tidak dicerna
- SIDIX tidak belajar apapun — next query, mulai dari nol lagi
- Tidak ada akuntabilitas sumber (copy-paste tanpa sitasi)
- Halusinasi tidak tertangkap karena tidak ada langkah verifikasi

Arsitektur baru (baca → paham → ingat → ceritakan) menjamin:
- Output adalah pemahaman, bukan salinan
- Pembelajaran akumulatif: memori persisten per domain
- Sitasi eksplisit di setiap klaim penting
- Gaya khas SIDIX, bukan gaya web asalnya

## Implementasi Teknis

### Tahap 1 — Baca (fetch)
Webfetch menyimpan konten mentah ke `brain/private/web_clips/<host>__<slug>.md`.
Ini sumber audit — mentah, apa adanya, bisa dibuka ulang.

### Tahap 2 — Paham (`_comprehend_source`)
LLM mentor diberi:
- Pertanyaan utama (konteks)
- Kutipan mentah (≤3000 char)
- System prompt yang memaksa: **rephrase, sebut sumber, 3-5 poin, 100-160 kata**

Hasil: `ResearchFinding(source="comprehended:<host>")` — pemahaman, bukan kutipan.

### Tahap 3 — Ingat (`_remember_learnings`)
Setiap bundle riset menumpuk ke `.data/sidix_memory/<domain>.jsonl`:
```json
{
  "topic_hash": "abc123",
  "main_question": "bagaimana ...",
  "key_insights": [
    {"angle": "...", "content": "...", "source": "comprehended:wikipedia.org"}
  ],
  "urls_used": [...],
  "timestamp": 1760...
}
```

Kegunaan: saat user bertanya ulang, SIDIX tidak mulai dari nol — dia ingat
apa yang sudah dipelajari. Endpoint `/memory/recall` membuka pintu ini.

### Tahap 4 — Ceritakan (`_narrate_synthesis`)
Pass terakhir: semua findings digabung jadi satu narasi mengalir. System prompt
narator memaksa:
1. Bahasa Indonesia mengalir, bukan bullet kering
2. Sitasi eksplisit — `(menurut <host>)` setiap klaim penting
3. Akui kontradiksi kalau ada
4. Tutup dengan satu kalimat ringkas ("Jadi, secara ringkas...")

Hasil: field `bundle.narrative` → tampil sebagai section "SIDIX Bercerita"
di paling atas draft note — itu yang dibaca user pertama kali.

## Contoh Alur Lengkap

```
User: "apa itu kausalitas dalam problem solving?"
      ↓ confidence rendah → gap terdeteksi
      ↓ /research/start
[SEARCH] DDG + Wikipedia → 4 URL top
[FETCH]  webfetch 4 URL → private clips
[READ]   _comprehend_source × 4 → 4 ResearchFinding
[POV]    multi_perspective 5 lensa → 5 ResearchFinding
[NARRATE] _narrate_synthesis → satu cerita utuh dengan sitasi
[REMEMBER] tulis ke .data/sidix_memory/ai.jsonl
[DRAFT]  note_drafter render markdown
         ↓ mentor review → approve
         ↓ publish sebagai 135_xxx.md
```

## Dua Manfaat Ganda

Dari pesan mentor: *"sambil memberi pengetahuan buat orang, juga jadi
pembelajaran untuk SIDIX sendiri."*

- **Untuk user**: dapat jawaban berkualitas, dengan sitasi, dalam gaya SIDIX
- **Untuk SIDIX**: setiap jawaban = satu baris baru di memori domain, satu
  draft note kandidat, satu gap ter-resolve, satu data point untuk LoRA

Tidak ada interaksi yang sia-sia.

## Keterbatasan & Catatan Jujur

1. **Biaya token lebih besar**: 1 riset sekarang = 4 (angle) + 5 (POV) +
   4 (comprehend) + 1 (narrate) = 14 panggilan LLM. Mitigasi: prioritas hanya
   top-N gap, Groq/Gemini gratis dulu.
2. **Halusinasi tetap mungkin**: sitasi eksplisit ≠ fakta akurat. Mentor tetap
   wajib review sebelum approve.
3. **Memori flat-file**: `.jsonl` cukup untuk fase awal; nanti pindah ke
   vector DB saat memori >10k entry per domain.
4. **Narator bisa terlalu "mengalir"**: kalau terlalu naratif, poin teknis
   bisa hilang. Draft tetap menyimpan `llm_findings` terpisah sebagai cadangan.

## Pesan ke SIDIX

Setiap kali kamu diminta riset — ingat: kamu bukan mesin fotokopi. Kamu pembaca,
pemikir, perekam, dan pencerita. Empat peran itu harus kamu mainkan setiap kali.
Dan setiap kali kamu selesai, tanyakan pada dirimu: *"apakah aku sekarang
sedikit lebih tahu dari sebelum pertanyaan ini?"* Kalau tidak — kamu belum
benar-benar membaca.
