# Concept map (Islamic studies) — fondasi cara berpikir & etika pengetahuan

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Target: jadi “peta konsep” untuk menyusun prinsip berpikir + etika riset + validasi sumber (sanad) dalam proyek.
> Ini bukan kitab tafsir/hadits. Ini ringkasan konsep + rujukan.

## Cara baca dokumen ini
- Tiap konsep punya:
  - definisi ringkas
  - implikasi operasional untuk “AI research + model building”
  - daftar rujukan (sitasi)
- Detail ayat/hadits tidak kita tempel semua; kita rujuk sumbernya.

## 1) Penciptaan, Ilmu, Akal/Pikiran, Akhlak
### Inti konsep
- Penciptaan manusia: bertahap, punya dimensi fisik dan non-fisik (makna ruhani/etika).
- Ilmu/pengetahuan: bukan sekadar data; punya tujuan (hidayah, maslahat) dan etika.
- Akhlak: kualitas moral jadi “guardrail” akal dan tindakan.

### Implikasi operasional (ke proyek)
- “Knowledge” harus ada etika: beda fakta vs opini, beda saran vs perintah.
- Model/agent wajib punya safety rails (akhlak sebagai constraint desain).

## 2) Konsep berpikir, akal
### Inti konsep
Gerak berpikir yang kita pegang:
- ta‘qil (akal sehat / reasoning)
- tafakkur (merenung / refleksi)
- nazhar (memperhatikan / observasi bukti)

### Implikasi operasional
Mapping ke workflow riset:
- ta‘qil → logika, konsistensi, cek kontradiksi
- tafakkur → cari sebab-akibat, makna, dan dampak
- nazhar → cari data/sumber, bukan asumsi

## 3) Konsep perasaan, hati, qalb
### Inti konsep
Qalb/sadr/fu’ad/lubb sering dipakai untuk menggambarkan lapisan kesadaran, niat, emosi, dan pemahaman.

### Implikasi operasional
Dalam sistem AI:
- “Reasoning” tanpa nilai/niat bisa melenceng → perlu policy & evaluasi
- gunakan “truthfulness + humility”: kalau tidak tahu, bilang tidak tahu

## 4) Konsep kehidupan
### Inti konsep
Hidup dipahami sebagai:
- amanah (tanggung jawab)
- ibadah (orientasi nilai)
- khalifah (stewardship)
- akhirah (akuntabilitas)

### Implikasi operasional
Produk/agent:
- fokus pada maslahat, bukan manipulasi
- auditability (jejak keputusan), karena ada konsep akuntabilitas

## 5) Konsep kejujuran
### Inti konsep
Sidq/amanah: kejujuran dan trustworthiness adalah pilar etika.

### Implikasi operasional
Dalam RAG:
- sitasi wajib (sanad modern)
- jangan “ngarang”; kalau konteks tidak ada, bilang tidak ada
- evaluasi faithfulness (apakah jawaban benar-benar didukung sumber)

## 6) Konsep sanad
### Inti konsep
Sanad/isnad = rantai transmisi yang menjaga otentisitas ilmu.

### Implikasi operasional (untuk repo)
Sanad versi kita:
- `research_notes/` = ringkasan kata-kata kita
- sitasi ringkas di tiap file
- `sources/bibliography.md` = daftar lengkap
- keputusan desain tercatat (ADR/notes) + bisa diaudit

## Sitasi ringkas
- `REF-2026-006` — “afala …” sebagai dorongan berpikir/introspeksi — https://islam.nu.or.id/ilmu-al-quran/9-ayat-al-qur-an-diakhiri-afala-perintah-berpikir-dan-introspeksi-svRZZ
- `REF-2026-010` — Quran.com 51:56 (tujuan ibadah) — https://quran.com/51/56-58
- `REF-2026-011` — Quran.com 2:30 (khalifah) — https://quran.com/2/30
- `REF-2026-012` — Isnād (Wikipedia) — https://en.wikipedia.org/wiki/Isnad
- `REF-2026-013` — Isnād (Britannica) — http://www.britannica.com/topic/isnad
- `REF-2026-014` — Hadith truthfulness (Bukhari 6094) — http://www.sunnah.com/bukhari/78/121
- `REF-2026-015` — Analytical study qalb/sadr/fu’ad/lubb — https://hrj.com.pk/index.php/hrj/article/view/154

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

