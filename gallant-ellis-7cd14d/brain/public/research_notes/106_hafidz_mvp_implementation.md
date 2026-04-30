# 106 — Hafidz Framework MVP: CAS + Merkle + Erasure Coding

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Task:** Track M — implementasi Hafidz MVP  
**File terkait:** `apps/brain_qa/brain_qa/hafidz_mvp.py`  

---

## Apa Itu Hafidz Framework?

**Hafidz** = sistem penyimpanan knowledge terdistribusi yang terinspirasi dari tradisi hafalan Al-Qur'an.

Tiga sifat utama hafalan Qur'an menjadi tiga pilar teknis:

| Sifat Hafalan Qur'an | Pilar Teknis | Modul |
|----------------------|-------------|-------|
| **Tersebar** di ribuan hafidz seluruh dunia | Distribusi N shares | `ErasureCoder` |
| **Dapat diverifikasi** lewat sanad (rantai periwayatan) | Hash chain integritas | `MerkleLedger` |
| **Dapat direkonstruksi** dari quorum hafidz | Recover dari K shares | `ErasureCoder.decode()` |

---

## Komponen 1: Content-Addressed Storage (CAS)

### Apa Itu CAS?

CAS = sistem penyimpanan di mana **identitas item adalah hash kontennya sendiri**.

```
content → SHA-256 → "a1b2c3d4..." → dipakai sebagai nama file
```

**Properti penting:**
- Idempotent: simpan konten yang sama dua kali → hash yang sama, tidak ada duplikasi
- Tamper-evident: ubah konten 1 karakter → hash berubah total
- Content-addressable: tidak bisa "pindahkan" file tanpa hash baru

**Analogi Qur'an:** Setiap ayat diidentifikasi oleh teksnya sendiri. Tidak bisa ganti satu huruf tanpa orang lain tahu — karena hafidz lain akan mendeteksi perbedaannya.

**Contoh nyata:** Git object store menggunakan CAS (`.git/objects/ab/cdef...`).

### Implementasi

```python
cas = ContentAddressedStore(root=".data/hafidz/cas")
hash = cas.put("Bismillahirrahmanirrahim")  # returns sha256 hex
content = cas.get(hash)                     # returns original text
```

Struktur disk:
```
.data/hafidz/cas/
  a1/                    ← 2 char pertama hash
    b2c3d4e5f6...        ← sisa hash → isi = konten asli
```

---

## Komponen 2: Merkle Ledger

### Apa Itu Merkle Tree?

Struktur data pohon di mana:
- **Daun (leaf)**: hash dari setiap item individual
- **Node internal**: hash dari dua anak di bawahnya (pair hash)
- **Root**: satu hash yang merepresentasikan SELURUH tree

```
        [Root]
       /      \
  [Hash-AB]  [Hash-CD]
  /    \      /    \
[A]   [B]  [C]   [D]
```

**Properti penting:**
- Ubah satu item → root berubah total
- Bisa verify item tertentu tanpa download seluruh tree (Merkle proof)
- Dipakai di: Bitcoin, Git, IPFS, certificate transparency logs

**Analogi Sanad:** Setiap periwayat (hash) bisa ditelusuri kembali ke sumber (root), membuktikan rantai integritas tidak putus.

### Implementasi

```python
ledger = MerkleLedger(".data/hafidz/ledger.jsonl")
root = ledger.add_item(cas_hash, {"source": "quran", "juz": 1})
print(root)  # "a1b2c3..."
proof = ledger.get_proof(cas_hash)  # sibling hashes dari daun ke root
```

Ledger disimpan sebagai JSONL (append-only) — setiap baris = satu item.

---

## Komponen 3: Erasure Coding

### Apa Itu Erasure Coding?

Teknik encoding di mana data dibagi menjadi **N shares**, dan **K shares sudah cukup** untuk merekonstruksi data asli (K < N).

Jika K=3, N=5: kehilangan 2 shares manapun → masih bisa recover.

**Analogi Hafalan Qur'an:**
- N = 1000 hafidz di seluruh dunia memiliki hafalan lengkap
- K = 3 hafidz sudah cukup untuk reconstruct seluruh teks
- Musnahkan 997 hafidz → 3 yang tersisa bisa kembalikan Qur'an utuh

**Aplikasi nyata:**
- RAID disk storage (RAID-5, RAID-6)
- Erasure codes di Facebook f4 (cold storage)
- IPFS (Filecoin erasure coding)
- Telegram distributed storage

### Implementasi MVP (XOR-based)

MVP ini menggunakan XOR parity sederhana (bukan Reed-Solomon penuh):

```
Data: "Bismillahirrahmanirrahim" (K=3, N=5)
→ Data chunks: [chunk0, chunk1]          (K-1=2 data shares)
→ Parity: chunk0 XOR chunk1             (1 parity share)
→ Redundan: [copy chunk0, copy chunk1]  (N-K=2 redundan shares)
```

Recovery: jika 1 data chunk hilang, XOR dengan parity untuk recover.

```python
ec = ErasureCoder()
shares = ec.encode("Bismillahirrahmanirrahim", n_shares=5, k_required=3)
# shares = [str(JSON), str(JSON), str(JSON), str(JSON), str(JSON)]

# Reconstruct dari subset (ambil shares 0, 1, 2 saja)
recovered = ec.decode(shares[:3])
assert recovered == "Bismillahirrahmanirrahim"
```

**Keterbatasan MVP:** Hanya bisa recover 1 share yang hilang via XOR. Reed-Solomon bisa recover hingga (N-K) shares. Untuk produksi, upgrade ke `isa-l` atau `pyeclib`.

---

## Komponen 4: HafidzNode

Orchestrator yang mengintegrasikan ketiga komponen:

```python
node = HafidzNode(".data/hafidz")

# Store
result = node.store("Bismillahirrahmanirrahim", {"source": "quran"})
# result = {cas_hash, merkle_root, shares, stored_at}

# Retrieve
text = node.retrieve(result["cas_hash"])

# Verify
integrity = node.verify_integrity()
# {total: N, ok: N, failed: [], root: "..."}

# Stats
stats = node.get_stats()
# {cas_items: N, ledger_items: N, merkle_root: "...", total_shares: N*5}
```

---

## Endpoint API (Roadmap)

Endpoint yang bisa didaftarkan ke `serve.py`:

```python
# POST /hafidz/store
# Body: {"content": "...", "metadata": {...}}
# Response: {cas_hash, merkle_root, stored_at, shares_count}

# GET /hafidz/retrieve/{hash}
# Response: {success, cas_hash, content}

# GET /hafidz/verify
# Response: {total, ok, failed, root}

# GET /hafidz/stats
# Response: {cas_items, ledger_items, merkle_root, total_shares}
```

---

## Roadmap Menuju P2P

Fase MVP saat ini: **single node, local disk**.

| Fase | Perubahan | Teknologi |
|------|-----------|-----------|
| MVP (sekarang) | Local disk CAS + Merkle + Erasure | Python stdlib |
| P2P Beta | Ganti disk CAS dengan IPFS block store | `ipfshttpclient` |
| P2P Full | Distribusi shares ke multiple HafidzNode | `libp2p` atau custom gossip |
| Consensus | Merkle root consensus antar peers | Raft atau simple majority vote |

Filosofi: **mulai lokal, terbukti benar, baru distribusi.** Sama seperti hafidz yang hafal dulu sendirian sebelum mengajarkan ke murid.

---

## Perbandingan dengan Sistem Lain

| Sistem | CAS | Merkle | Erasure | Analogi |
|--------|-----|--------|---------|---------|
| Git | SHA-1 | Tree object | Tidak | Version control |
| Bitcoin | SHA-256 | Block header | Tidak | Transaksi keuangan |
| IPFS | SHA-256 | DAG | Ya (Filecoin) | Distributed storage |
| **Hafidz MVP** | SHA-256 | JSONL tree | XOR simple | **Hafalan Qur'an** |

---

## Nilai untuk SIDIX

Hafidz Framework memungkinkan SIDIX menyimpan knowledge dengan:
1. **Integritas terjamin**: setiap knowledge item punya hash unik, tidak bisa dimanipulasi
2. **Redundansi**: shares tersebar, tahan kehilangan sebagian node
3. **Audit trail**: Merkle ledger adalah rekaman append-only, tidak bisa dihapus
4. **Inspirasi etis**: arsitektur yang selaras dengan nilai Islamic preservation of knowledge
