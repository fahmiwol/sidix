# Sumber belajar coding untuk SIDIX (kurasi cepat)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Tujuan: daftar sumber **legal** dan **high-signal** untuk meningkatkan kemampuan coding + problem solving SIDIX.
> Fokus: materi yang bisa diindeks, dataset/problem yang bisa dilatih, dan repos yang punya struktur bagus.

## Catatan legal/operasional

- **Codecademy** adalah platform berbayar/freemium. Kita bisa menautkan katalognya, tetapi **tidak** aman untuk “download konten kursus” secara otomatis tanpa izin eksplisit dari pemilik konten.
- `roadmap.sh` memiliki konten publik dan **repo GitHub resmi**; sebagian konten tersedia lewat endpoint publik untuk roadmaps.
- Untuk “explore seluruh GitHub”, pendekatan yang realistis adalah: pakai **kurasi repository** + **problem set** yang memang open, bukan scrape massal.

---

## 1) roadmap.sh (roadmap + data yang bisa diambil)

Situs utama: https://roadmap.sh/  
Repo resmi: https://github.com/kamranahmedse/developer-roadmap

Yang bisa dipakai:

- Roadmap frontmatter + metadata (markdown) di repo, contoh:
  - `frontend`: https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps/frontend/frontend.md
  - `backend`: https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps/backend/backend.md
  - `python`: https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps/python/python.md
- Endpoint roadmap JSON resmi (publik) yang bisa dipakai sebagai “data”:
  - `https://roadmap.sh/api/v1-official-roadmap/frontend`
  - `https://roadmap.sh/api/v1-official-roadmap/backend`
  - `https://roadmap.sh/api/v1-official-roadmap/python`

Rekomendasi penggunaan untuk SIDIX:

1. Simpan roadmap JSON sebagai **kurikulum berbentuk graph** (nodes/edges).
2. Turunkan menjadi task kecil: “buat proyek mini” + “soal latihan” per node.
3. Gunakan roadmap sebagai **rubrik evaluasi**: apakah SIDIX mampu menjawab/implement tiap node.

---

## 2) Codecademy (kurikulum interaktif; link saja)

Katalog/entry:

- https://www.codecademy.com/learn
- https://www.codecademy.com/catalog

Rekomendasi pemakaian untuk SIDIX:

- Jadikan sebagai **daftar topik**, bukan dataset.
- Ambil “nama course / path” sebagai label skill (mis. *Learn Python 3*, *Code Foundations*), lalu cari sumber open untuk materi yang setara.

---

## 3) GitHub — algoritma, data structures, dan referensi implementasi

High-signal repos (open-source):

- TheAlgorithms (multi-bahasa): https://github.com/TheAlgorithms
  - Java: https://github.com/TheAlgorithms/Java
  - Python: https://github.com/TheAlgorithms/Python
  - Penjelasan algoritma: https://github.com/TheAlgorithms/Algorithms-Explanation
- Awesome competitive programming: https://github.com/lnishan/awesome-competitive-programming
- Awesome algorithms: https://github.com/tayllan/awesome-algorithms

Cara pakai untuk SIDIX:

- Gunakan sebagai **corpus “referensi jawaban benar”** (implementasi + penjelasan).
- Ambil pattern untuk SFT: prompt “implement X” → target solusi; prompt “jelaskan kompleksitas” → target analisis.

---

## 4) Problem set (latihan pemecahan masalah)

Catatan: banyak platform (LeetCode dsb.) punya konten proprietary; prioritasnya yang:
1) punya statement problem publik, 2) punya editorial/solusi open, 3) bisa diunduh/diindeks.

Pilihan aman (berbasis kurasi GitHub di atas):

- Gunakan daftar “practice sites” di `awesome-competitive-programming` untuk memilih subset yang benar-benar open.

---

## 5) Integrasi ke pipeline SIDIX (yang “ngena”)

Minimal yang efektif untuk “SIDIX jago coding” biasanya butuh 3 hal:

1. **Kurikulum** (roadmap graph) → urutan skill.
2. **Latihan** (problem set) → kemampuan implementasi + debugging.
3. **Evaluasi** (rubrik + golden) → bisa diuji otomatis di repo.

Dokumen internal repo yang sudah sejalan:

- `brain/public/research_notes/33_coding_python_comprehensive.md`
- `brain/public/research_notes/34_coding_backend_web_development.md`
- `brain/public/research_notes/35_coding_data_structures_algorithms.md`

