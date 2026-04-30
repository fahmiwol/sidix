# ADR-003 — Reed-Solomon 4+2 untuk Penyimpanan Corpus Terdistribusi

**Tanggal**: 2026-04-16
**Status**: Accepted
**Penulis**: Fahmi (solo founder, SIDIX/Mighan)
**Reviewer**: —

---

## Konteks

Corpus SIDIX (kitab turath, dokumen Markdown, Q&A pairs) perlu disimpan
secara andal untuk menghindari kehilangan data akibat kerusakan disk atau
kegagalan node dalam deployment multi-mesin.

Dua pendekatan utama untuk ketahanan data:
1. **Replikasi penuh** — simpan N salinan identik di N node
2. **Erasure coding** — encode data menjadi M shard, cukup K shard untuk rekonstruksi (K < M)

Constraint proyek:
- Infrastruktur target: 2-6 mesin (VPS/on-premise) dengan kapasitas terbatas
- Tidak ada akses ke layanan cloud object storage yang andal (offline-first)
- Tidak ingin bergantung pada library C/MSVC (Windows dev environment)
- Corpus diperkirakan tumbuh 1-10 GB dalam 2 tahun ke depan

## Keputusan

Gunakan **erasure coding Reed-Solomon 4+2** (4 data shard + 2 parity shard)
melalui library **reedsolo** (pure Python, tidak membutuhkan MSVC/C extension).

Konfigurasi:
- `k = 4` data shards
- `m = 2` parity shards (tahan kegagalan 2 shard sekaligus)
- Total overhead storage: 50% (6/4 = 1.5x ukuran asli)
- Library: `reedsolo >= 1.7.0` (PyPI, MIT license, pure Python)

## Konsekuensi

### Positif
- Tahan terhadap kegagalan hingga 2 node/disk secara bersamaan
- Overhead storage 50% (jauh lebih efisien dari replikasi 3x = 200% overhead)
- Pure Python — tidak membutuhkan compiler C atau MSVC di Windows
- Dapat dijalankan di environment offline tanpa dependensi eksternal
- Mudah diintegrasikan ke pipeline brain_qa yang sudah Python-based

### Negatif / Trade-off
- Rekonstruksi data membutuhkan komputasi ekstra (encoding/decoding)
- Latency baca/tulis lebih tinggi dibanding akses file langsung
- reedsolo (pure Python) lebih lambat dari implementasi C untuk file besar
  — dapat dimigrasikan ke `jerasure` atau `liberasurecode` jika butuh performa tinggi
- Perlu orchestration untuk mendistribusikan shard ke node yang berbeda

### Risiko
- Jika > 2 shard rusak bersamaan, data tidak dapat direkonstruksi
- Implementasi shard orchestration belum ada — perlu dikembangkan di Phase G3

## Alternatif yang Dipertimbangkan

### Opsi A: Replikasi penuh (3 salinan)
- **Pro**: Sederhana, tidak perlu encoding/decoding
- **Kontra**: Overhead 200% (3x ukuran), tidak efisien untuk corpus besar
- **Alasan ditolak**: Terlalu boros storage untuk corpus yang akan tumbuh

### Opsi B: RAID-6 (perangkat keras)
- **Pro**: Transparan ke aplikasi, performa tinggi
- **Kontra**: Butuh perangkat keras khusus, tidak portable ke VPS
- **Alasan ditolak**: Tidak sesuai dengan deployment target (VPS/software-only)

### Opsi C: MinIO dengan erasure coding bawaan
- **Pro**: Battle-tested, performa tinggi, UI tersedia
- **Kontra**: Dependensi besar, butuh infrastruktur tambahan, tidak sesuai single-machine dev
- **Alasan ditolak**: Over-engineering untuk scale saat ini; dapat dipertimbangkan ulang di G5+

### Opsi D: reedsolo dengan konfigurasi berbeda (6+3, 8+4)
- **Pro**: Lebih tahan kegagalan
- **Kontra**: Overhead lebih besar, shard lebih banyak dikelola
- **Alasan ditolak**: 4+2 sudah cukup untuk 6 node target; dapat dinaikkan di masa depan

## Referensi

- [reedsolo di PyPI](https://pypi.org/project/reedsolo/)
- [Reed-Solomon error correction (Wikipedia)](https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction)
- [Erasure Coding vs Replication — Facebook Engineering](https://engineering.fb.com/2014/09/25/core-infra/erasure-coding-for-production-systems/)

---

_ADR ini dibuat menggunakan template `docs/adr/ADR-template.md`._
