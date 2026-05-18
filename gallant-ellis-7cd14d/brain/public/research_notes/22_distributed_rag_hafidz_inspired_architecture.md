# Arsitektur RAG Terdistribusi “Hafidz-Inspired” (CAS + Merkle Log + Governance)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

Tujuan note ini: mengubah riset “Hafidz-inspired distributed RAG” menjadi **rencana arsitektur yang konsisten** dengan prinsip Mighan: **security-by-default, cost-aware, evidence-first, sanad/audit trail**.

> Batasan: ini **bukan** ajakan membuat blockchain publik atau token ekonomi. Fokusnya: **tamper-evident + distributed storage** yang ringan untuk solo founder.

## Ringkasan 10 baris
- Kita bisa membuat “blockchain-style integrity” tanpa consensus berat: **Content Addressed Storage (CAS) + Merkle append-only log**.
- Data disimpan tersebar (user devices), **diidentifikasi oleh hash** (CID) ala IPFS/Git.
- Integritas & provenance dijaga oleh **append-only verifiable log** (model Trillian) + signature.
- Ketersediaan dijaga dengan **replication** atau **erasure coding (4+2)** (hemat storage, tetap tahan 2 node mati).
- Search tidak harus terpusat: mulai dari **local index** (MVP), lalu naik ke **distributed discovery** (VecDHT/d-HNSW) bila komunitas besar.
- Governance wajib: bedakan **Data PR** vs **Plugin/Tool PR**; plugin default disabled + review + sandbox.
- Ini selaras dengan kebijakan sumber: ringkasan + link, tanpa copy-paste panjang.

## Problem statement
Keterbatasan utama: server terbatas, tapi ingin knowledge base tumbuh cepat dari komunitas, tetap:
- tahan node luring (availability)
- tahan manipulasi (tamper-evident)
- tidak membuka celah supply-chain (plugin aneh/ilegal)

## Keputusan desain (versi Mighan)

### Keputusan
- Kita memilih: **CAS + Merkle append-only log** sebagai “integrity layer”.
- Kita menunda: consensus blockchain + token economy.

### Alasan
- RAG tidak perlu menyelesaikan “double-spend” seperti uang kripto; yang kita butuhkan adalah **bukti integritas & provenance**.
- Consensus chain = biaya/latensi/operasional tinggi (overkill untuk MVP).

### Konsekuensi
- (+) Integritas bisa diverifikasi klien secara mandiri (skeptical clients).
- (+) Storage & bandwidth bisa dibebankan ke user nodes.
- (-) Discovery/search lintas node butuh desain bertahap (mulai lokal dulu).

## Arsitektur 4 lapis (minimum viable)

### 1) Data layer — Content Addressed Storage (CAS)
- Dokumen dipecah jadi chunks.
- Tiap chunk disimpan dengan **hash** sebagai ID (CID konsepnya).
- Node lain bisa menyimpan chunk yang sama (dedupe otomatis via hash).

Referensi:
- `REF-2026-053` (Iroh vs libp2p, konektivitas P2P)

### 2) Ledger layer — Tamper-evident append-only log (Merkle)
Kita simpan **event log** publik (append-only):
- publish/curate event
- mapping “document stable id” → “current CID”
- signature kontributor (Ed25519)

Klien bisa minta:
- inclusion proof
- consistency proof

Referensi:
- `REF-2026-052` (Trillian / transparency logs)

### 3) Index layer — Search & retrieval
MVP (sekarang):
- index lokal per user (`brain_qa index`) + BM25/dense sederhana.

Naik level (jika komunitas besar):
- discovery terdistribusi: node menyimpan ringkasan metadata/topik + routing berbasis “kedekatan semantik”.
- jangan mulai dari ini; implementasi P2P vector search kompleks dan rawan.

### 4) Compute layer — Embedding + generation (local-first)
MVP:
- embedding dibuat lokal (hemat biaya).
- generation bisa lokal; bila butuh kualitas, bisa memilih provider—tapi tetap dengan policy & audit log.

## Ketahanan data: replication vs erasure coding

Definisi ringkas:
- **Replication N×**: salin utuh ke N node (simple, boros storage).
- **Erasure coding (k+m)**: pecah jadi k data shards + m parity shards; cukup k shards untuk reconstruct.

Rekomendasi awal untuk komunitas kecil-menengah:
- **(4+2)**: overhead 1.5×, tahan 2 node mati, lebih hemat dibanding replication 3×.

Referensi:
- `REF-2026-054` (Ceph erasure coding overview)

## Governance: kontribusi cepat tapi aman

Kita harus mencegah “VSCode marketplace problem” (plugin jahat) dengan kebijakan:
- Data/corpus: cepat (Tier A)
- Tools/plugins/connectors: ketat (Tier B, manual review, default disabled, sandbox)

Dokumen repo:
- `docs/CONTRIBUTING.md`
- `brain/public/sources/CONTRIBUTION_POLICY.md`

## Blockchain vs “tamper-evident log” (agar tidak kontradiktif)

Blockchain (umum):
- ledger terdistribusi + consensus untuk state global. (`REF-2026-050`)

Yang kita butuhkan di MVP:
- **tamper-evident log** + signature + inclusion/consistency proof. (`REF-2026-052`)

Token/incentive:
- bukan keharusan MVP; bisa ditunda agar sistem tetap ringan. (`REF-2026-051`)

## Rencana implementasi bertahap (praktis)

Phase 1 (local-first, 1–3 bulan):
- rapikan corpus, governance, QA regression
- tambah “tamper-evident ledger” untuk publish events (append-only) + snapshot hash

Phase 2 (sync terdistribusi ringan, 4–8 bulan):
- mulai sinkronisasi chunks antar peer (small community)
- mulai erasure coding untuk durability

Phase 3 (distributed discovery + sandbox plugins, 9–12+ bulan):
- distributed routing untuk retrieval (kalau benar-benar dibutuhkan)
- plugin runtime pakai sandbox (mis. WASM) + allowlist

## Sitasi ringkas
- `REF-2026-050` — What is blockchain? — https://aws.amazon.com/id/what-is/blockchain/ — dipakai untuk: definisi blockchain & kenapa consensus itu overhead.
- `REF-2026-051` — Blockchain tokens explained — https://www.web3labs.com/blockchain-explained-what-are-blockchain-tokens — dipakai untuk: konteks token/incentive (opsional, bukan MVP).
- `REF-2026-052` — Trillian / Transparency.dev — https://transparency.dev/ — dipakai untuk: append-only verifiable log (Merkle proofs).
- `REF-2026-053` — Comparing Iroh & Libp2p — https://www.iroh.computer/blog/comparing-iroh-and-libp2p — dipakai untuk: P2P connectivity yang sederhana untuk local-first sync.
- `REF-2026-054` — Erasure code pools overview (Ceph) — https://docs.redhat.com/en/documentation/red_hat_ceph_storage/7/html/storage_strategies_guide/erasure-code-pools-overview_strategy — dipakai untuk: konsep erasure coding (k+m) vs replication.
