---
title: "Storage Layers: Ledger vs Distribution (Hafidz-inspired)"
version: "2026-04-15"
status: "active"
---

# Storage Layers — Ledger vs Distribution (Hafidz-inspired)

Dokumen ini menjawab kebingungan yang wajar:
> “Kalau kita sudah punya Hafidz Ledger, berarti masalah storage sudah selesai, kan?”

Jawabannya: **sebagian sudah**, tapi **belum semuanya**.

Kita membagi “storage” menjadi beberapa **layer** supaya desain kita tidak kontradiktif.

---

## 1) Integrity layer (Ledger) — sudah kita punya

**Ledger = bukti integritas & provenance (sanad teknis)**.

Apa yang ledger lakukan:
- Menghasilkan **Merkle snapshot root** dari corpus publik (tamper-evident).
- Menyimpan **append-only chain** (hash-chained) sehingga perubahan diam-diam bisa terdeteksi.
- Menyediakan jejak aksi publish via event log (published → snapshotted → reindexed/failed).

Apa yang ledger **tidak** lakukan:
- Tidak menyimpan data di banyak node.
- Tidak memastikan file bisa diambil saat node/server mati.
- Tidak melakukan replikasi/erasure coding.
- Tidak melakukan discovery: “CID ini ada di peer mana?”

Ringkasnya:
- **Ledger menjawab “apakah ini asli & versi yang sah?”**
- Bukan “di mana file ini tersimpan?” atau “apakah file ini selalu tersedia?”

---

## 2) Availability layer (Distribution) — ini yang belum, dan memang next

Kalau targetnya “server pusat mati tapi data tetap hidup”, kita butuh layer ketersediaan:

Komponen minimum:
- **CAS (Content-Addressed Storage)**: dokumen/chunk diberi ID berbasis hash (CID).
- **Redundancy**:
  - replication N× (paling simpel), atau
  - **erasure coding (k+m)** (lebih hemat; rekomendasi awal: **4+2**).
- **Locator / discovery**: mapping `CID -> lokasi peer` (bisa sederhana dulu).
- **Retriever**: ambil shard dari beberapa peer → reconstruct → verifikasi hash.

Ringkasnya:
- **Distribution menjawab “bagaimana data tetap tersedia?”**
- Ledger tetap dipakai untuk verifikasi: “yang kita ambil dari peer itu bener gak?”

---

## 3) Index layer (Search) — mulai lokal dulu

Ketersediaan data ≠ bisa dicari cepat.

MVP sekarang:
- Index lokal per user (BM25) untuk corpus publik.

Tahap lanjut (jika dibutuhkan):
- metadata/discovery terdistribusi (VecDHT/d-HNSW) — kompleks, jangan dipaksakan di MVP.

---

## 4) Compute layer — local-first, provider bisa hybrid

Compute layer adalah “otak” yang memakai data:
- Embedding + retrieval + answer synthesis.
- Bisa lokal atau hybrid provider, tapi tetap:
  - evidence-first
  - audit/status jelas
  - policy + guardrail konsisten

---

## Prinsip keputusan (biar konsisten)

- **Ledger** dulu untuk integritas: murah, jelas, dan langsung berguna untuk governance.
- **Distribution** bertahap: mulai dari “mirror/pin manual” sebelum P2P penuh.
- Jangan lompati discovery terdistribusi sebelum kebutuhan jelas.

---

## Checklist “storage sudah selesai” versi Mighan

Anggap “storage” selesai **kalau** semua ini ada:
- [x] Integrity: ledger snapshot + chain verify
- [ ] Availability: redundancy (replication / erasure coding)
- [ ] Retrieval: fetch/reconstruct + verify hash
- [ ] Discovery: minimal locator (bahkan kalau manual dulu)
- [ ] Policy: apa yang publik, apa yang privat, apa yang boleh direplikasi

