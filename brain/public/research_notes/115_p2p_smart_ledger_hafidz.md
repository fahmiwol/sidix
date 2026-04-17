# 115 — P2P Smart Ledger & Hafidz: Distributed Knowledge Architecture

## Apa ini / What is it

**Hafidz** adalah arsitektur penyimpanan pengetahuan terdistribusi yang dibangun di atas tiga pilar:

1. **CAS (Content-Addressed Storage)** — setiap item pengetahuan diidentifikasi oleh hash SHA-256 dari kontennya, bukan oleh lokasinya. Dua node yang menyimpan konten identik akan menghasilkan hash yang sama, sehingga duplikasi dapat dideteksi secara otomatis.

2. **Merkle Ledger** — append-only log (format JSONL) di mana setiap entri baru menyertakan hash dari entri sebelumnya, membentuk rantai kriptografis (Merkle tree). Tidak ada satu entri pun yang dapat diubah tanpa mengubah seluruh rantai setelahnya.

3. **Erasure Coding (XOR N/K redundancy)** — setiap item pengetahuan dipecah menjadi `N` fragmen, di mana cukup `K` fragmen untuk merekonstruksi data asli. Ini berarti sistem dapat kehilangan hingga `N - K` node dan tetap dapat memulihkan data.

**P2P Smart Ledger** adalah lapisan jaringan di atas Hafidz: setiap node menyimpan subset fragmen, dan node-node ini bekerja sama tanpa server pusat untuk menjaga integritas dan ketersediaan kolektif corpus SIDIX.

---

## Mengapa penting / Why it matters

- **Ketahanan terhadap sensor** — tidak ada satu titik kegagalan atau kontrol. Pengetahuan tidak dapat dihapus oleh satu pihak.
- **Verifiability tanpa trust** — siapa pun dapat memverifikasi bahwa sebuah research note tidak diubah, cukup dengan menghitung hash-nya dan membandingkan dengan Merkle proof.
- **Scalability horizontal** — semakin banyak node bergabung, semakin tinggi redundansi dan kecepatan akses.
- **Ownership terdistribusi** — setiap kontributor secara kriptografis terhubung ke kontribusinya melalui CAS hash.

---

## Bagaimana cara kerja / How it works

### Alur kontribusi:

```
User submit research note (.md)
        │
        ▼
1. CAS Hash Generation
   hash = SHA-256(konten)
   → ID unik untuk setiap note
        │
        ▼
2. Append ke Merkle Ledger
   entry = {
     "id": hash,
     "prev_hash": hash_entry_sebelumnya,
     "timestamp": ISO8601,
     "author": pubkey_user,
     "topic": "115_p2p_smart_ledger",
     "size_bytes": 4096
   }
   → ditulis ke ledger.jsonl
        │
        ▼
3. Erasure Coding
   fragmen = erasure_encode(konten, N=10, K=6)
   → 10 fragmen dibuat, 6 cukup untuk rekonstruksi
        │
        ▼
4. Distribusi ke Peers
   → setiap peer mendapat 1-3 fragmen
   → DHT (Distributed Hash Table) mencatat siapa menyimpan apa
        │
        ▼
5. Smart Valuation
   nilai_kontribusi = f(uniqueness, citation_count, verifiability)
   → tercatat on-ledger, tidak bisa dimanipulasi retroaktif
```

### Verifikasi integritas:

```
Node A ingin verifikasi note #115:
1. Minta Merkle proof dari ledger
2. Hitung SHA-256(konten lokal)
3. Bandingkan dengan hash di ledger
4. Verifikasi rantai hash ke genesis block
→ Jika cocok: konten authentic dan tidak diubah
```

---

## Analogi Islamic / Islamic Parallel

| Konsep SIDIX | Konsep Islam | Penjelasan |
|---|---|---|
| **Erasure Coding** | **Mutawatir** | Hadith mutawatir = diriwayatkan oleh banyak sanad independen, mustahil semuanya bersepakat bohong. Erasure coding = data masih valid meskipun sebagian node hilang. |
| **Merkle Chain** | **Sanad Chain** | Sanad = rantai perawi dari Nabi ﷺ. Setiap perawi merujuk ke perawi sebelumnya. Merkle tree = setiap hash merujuk ke hash sebelumnya. Keduanya membuat manipulasi retroaktif terdeteksi. |
| **CAS Hash** | **Ijazah** | Ijazah = sertifikat otoritas keilmuan, unik per orang per kitab. CAS hash = sertifikat kriptografis unik per konten. Keduanya berfungsi sebagai bukti keaslian. |
| **Smart Valuation** | **Tingkat Perawi** | Ilmu Rijal menilai kualitas perawi (tsiqah, dla'if, dll). Smart valuation menilai kualitas kontribusi berdasarkan uniqueness dan citation. |

---

## Contoh nyata / Real examples

### Skenario 1: Research note tersebar di 10 node

```
Corpus SIDIX node A (Jakarta): fragmen 1, 3, 7
Corpus SIDIX node B (Surabaya): fragmen 2, 5, 8
Corpus SIDIX node C (Makassar): fragmen 4, 6, 9
Corpus SIDIX node D (Kuala Lumpur): fragmen 1, 10, 6
...

Jika node A dan B offline: C dan D masih punya 6 fragmen → rekonstruksi penuh.
```

### Skenario 2: Verifikasi research note

```python
import hashlib, json

def verify_note(content: str, ledger_entry: dict) -> bool:
    computed_hash = hashlib.sha256(content.encode()).hexdigest()
    return computed_hash == ledger_entry["id"]

# Jika True → konten tidak diubah sejak didaftarkan ke ledger
```

### Skenario 3: Smart Ledger entry

```jsonl
{"id":"a3f2b1...","prev_hash":"9d8c7e...","timestamp":"2026-04-18T05:00:00Z","author":"fahmi","topic":"115_p2p_smart_ledger","citations":0,"uniqueness_score":0.87}
{"id":"c1d4e5...","prev_hash":"a3f2b1...","timestamp":"2026-04-18T05:01:00Z","author":"community_member","topic":"116_self_learning","citations":2,"uniqueness_score":0.91}
```

---

## Keterbatasan / Limitations

1. **Bootstrapping problem** — jaringan P2P membutuhkan massa kritis node sebelum redundansi bermakna. Tahap awal, SIDIX VPS berperan sebagai "bootstrap node" terpusat.

2. **Sybil attack** — tanpa mekanisme identitas yang kuat, aktor jahat bisa membuat banyak node palsu. Solusi potensial: proof-of-work ringan atau staking sistem.

3. **Erasure code overhead** — encoding/decoding membutuhkan komputasi. Untuk corpus besar, ini harus diimplementasi secara async.

4. **Ledger growth** — append-only ledger tumbuh terus. Perlu mekanisme "checkpointing" atau snapshot berkala.

5. **Network partition** — jika jaringan terputus (split-brain), dua sub-jaringan bisa menerima kontribusi berbeda. Perlu consensus mechanism (PBFT lite atau Raft) untuk rekonsiliasi.

---

## Referensi / References

- `brain/public/research_notes/106_hafidz_mvp_implementation.md` — implementasi MVP Hafidz
- `brain/public/research_notes/113_decentralized_data_recall.md` — decentralized data recall
- Git Merkle trees: [Pro Git Book — Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- Erasure coding: Reed-Solomon codes, XOR-based (simpler), LRC (Azure)
- Islamic epistemology: `brain/public/research_notes/11_islamic_epistemology_wahyu_akal_indera.md`
- Ilm al-Rijal (ilmu perawi hadith): al-Dhahabi, "Mizan al-I'tidal"
