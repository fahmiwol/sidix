# 141. Integrasi Sanad + Hafidz untuk Setiap Note SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: ai / epistemologi / arsitektur
> **Fase**: 4.5 (verifiability layer atas continual learning)
> **Tanggal**: 2026-04-18

---

## Apa yang Dibangun

Setiap note yang SIDIX publish ke corpus sekarang otomatis dapat:

1. **CAS hash** (SHA-256) — identitas konten unik, bisa diverifikasi siapa saja
2. **Merkle root** — bukti integritas seluruh ledger pada saat publikasi
3. **5 erasure shares** — siap distribusi (3 cukup untuk recover)
4. **Sanad metadata** — rantai periwayatan eksplisit dari narator ke sumber
5. **Tabayyun** — catatan verifikasi quality gate

Tiga lapis penyimpanan paralel:
- File markdown di `brain/public/research_notes/<n>_<slug>.md` (untuk pembaca)
- Sanad JSON di `.data/sidix_sanad/<n>_<slug>.sanad.json` (untuk audit)
- Hafidz CAS + ledger di `.data/hafidz/` (untuk verifikasi kriptografis)

## Mengapa — Filosofi Sanad

Dari note 22, 41, 106, 115 — sanad bukan dekorasi. Sanad adalah **syarat
pengetahuan dapat dipercaya**:

> "Tradisi hadith menolak hadith tanpa isnad, walaupun maknanya bagus. SIDIX
> harus sama: tidak ada klaim yang tidak punya rantai sumber."

Sebelum integrasi ini, note SIDIX punya sitasi **dalam teks** (`menurut <host>`)
tapi tidak ada **struktur formal** yang bisa di-query. Sekarang setiap note
punya `isnad` array yang bisa diperiksa programatik.

## Struktur Sanad

```json
{
  "isnad": [
    {"role": "narrator",   "name": "SIDIX",          "via": "narrate",     "confidence": 0.80},
    {"role": "mentor_llm", "name": "groq_llama3",    "via": "router",      "confidence": 0.70},
    {"role": "web_source", "name": "wikipedia.org",  "via": "<URL>",       "confidence": 0.85}
  ],
  "tabayyun": {
    "findings_count": 9,
    "narrative_chars": 1798,
    "avg_confidence": 0.572,
    "quality_gate": "passed (auto-approve)"
  },
  "hafidz_proof": {
    "cas_hash":    "f6625b91...",
    "merkle_root": "808f739b...",
    "stored_at":   1776486966.23,
    "shares_count": 5
  }
}
```

**Urutan isnad**: dari simpul terdekat ke pembaca (narrator) → mundur ke
sumber awal (web). Mengikuti konvensi hadith klasik (narator paling akhir
disebut paling awal: "haddatsana fulan, qala haddatsana fulan, qala...").

## Komponen Software

| Modul | Tugas |
|-------|-------|
| `sanad_builder.py` | Bangun SanadMetadata dari ResearchBundle |
| `hafidz_mvp.HafidzNode` | Store konten + Merkle ledger + erasure shares |
| `note_drafter.approve_draft` | Pipeline: rebuild bundle → sanad → register Hafidz → embed ke MD → save sanad JSON |

## Endpoint Verifikasi

| Endpoint | Tujuan |
|----------|--------|
| `GET /hafidz/stats` | Total CAS items, ledger items, current Merkle root |
| `GET /hafidz/verify` | Cek semua item: hash konten masih cocok dengan ledger |
| `GET /hafidz/sanad/{stem}` | Ambil sanad lengkap untuk note tertentu |
| `GET /hafidz/retrieve/{cas_hash}` | Ambil konten by CAS hash (fallback erasure decode) |

## Hasil Verifikasi Produksi

Test 2026-04-18 di `ctrl.sidixlab.com`:

```
1 siklus daily_growth (zero-knowledge proof)
  → Note 140 published (14 KB)
  → CAS:    f6625b91...
  → Merkle: 808f739b...
  → 5 shares di .data/hafidz/shares/
  → Sanad JSON 1843 bytes di .data/sidix_sanad/
  → Isnad: 4 simpul (SIDIX → Groq → 2 Wikipedia)
  → Tabayyun: passed quality gate
  → /hafidz/verify → ok=1, failed=[]
```

Setiap baris note di corpus sekarang punya **bukti kriptografis** yang
bisa diverifikasi siapa saja dengan ulang `sha256(konten)`.

## Mapping Islamic ↔ Teknis (Lengkap)

| Konsep Islamic | Implementasi Teknis | File |
|----------------|---------------------|------|
| Sanad chain | `isnad[]` array | sanad_builder.py |
| Mutawatir | Erasure 5 shares (cukup 3) | hafidz_mvp.ErasureCoder |
| Ijazah | CAS SHA-256 hash | hafidz_mvp.ContentAddressedStore |
| Tabayyun | Quality gate + verify endpoint | sanad_builder.tabayyun |
| Ilm al-Rijal | confidence per simpul isnad | sanad_builder.SanadEntry |
| Mizan | avg_confidence + tabayyun stats | tabayyun dict |

## Roadmap P2P (Belum)

Sekarang masih single-node (server VPS). Tahap selanjutnya:

| Fase | Yang Berubah |
|------|--------------|
| **Sekarang** | Local CAS + Merkle + Erasure di 1 server |
| **P2P Beta** | Sync CAS chunks antar peer (libp2p / iroh) |
| **P2P Verified** | Merkle root consensus antar peers |
| **Federated** | Setiap user punya node + own corpus, bisa import sanad orang lain |

Filosofi: mulai lokal, terbukti, baru distribusi (sama seperti hafidz hafal
sendiri sebelum mengajar).

## Keterbatasan Jujur

1. **Sanad bisa "ringan"** — kalau riset hanya pakai LLM tanpa web (yang
   sering terjadi), isnad cuma 2 simpul (narrator + mentor LLM). Tidak salah,
   tapi kurang kuat. Solusi: prioritaskan riset dengan web sources.

2. **Confidence simpul masih heuristik** — semua web Wikipedia dapat 0.85,
   semua Groq dapat 0.7. Belum ada penilaian per-konten dari tabayyun
   spesifik (mis. apakah Wikipedia article-nya stub atau lengkap).

3. **Tidak deteksi sumber yang tidak relevan** — pernah ada Wikipedia ID
   "Bilangan riil negatif" masuk sanad untuk topik ZKP karena BM25 match
   kata "bilangan". Filter ada tapi belum ketat.

4. **Merkle ledger growth** — tiap note tambah 1 entri. Untuk 1000 note,
   ledger jadi 1000 baris. Belum ada checkpointing/snapshot.

5. **Belum ada signature kontributor** — ledger entry tidak signed dengan
   Ed25519 key. Untuk single-node tidak penting; untuk P2P wajib.

## Pesan ke SIDIX

Mulai sekarang, **kamu tidak boleh klaim apa-apa tanpa sanad**. Setiap kali
kamu bilang "X adalah Y", harus ada rantai: dari kamu, ke mentor (LLM mana),
ke sumber (web mana), ke fakta dasar.

Tradisi hadith bertahan 1400 tahun karena disiplin sanad. Pengetahuanmu
juga akan bertahan kalau kamu sama disiplinnya. Jangan pernah lemahkan
syarat ini — itu yang membuat kamu beda dari LLM lain yang asal jawab.

## Sumber

- `brain/public/research_notes/22_distributed_rag_hafidz_inspired_architecture.md`
- `brain/public/research_notes/41_islamic_epistemology_sidix_architecture.md`
- `brain/public/research_notes/106_hafidz_mvp_implementation.md`
- `brain/public/research_notes/115_p2p_smart_ledger_hafidz.md`
- al-Khatib al-Baghdadi. *Al-Kifayah fi 'Ilm al-Riwayah* — kaidah sanad
- al-Dhahabi. *Mizan al-I'tidal* — ilmu menilai perawi (rijal)
- Trillian transparency log — https://transparency.dev/
- Implementasi: `apps/brain_qa/brain_qa/sanad_builder.py`,
  `apps/brain_qa/brain_qa/hafidz_mvp.py`,
  `apps/brain_qa/brain_qa/note_drafter.py:approve_draft`
