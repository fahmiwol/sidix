# ADR ringkas — DataToken MVP + operasi storage (audit/rebalance) untuk komunitas terbatas

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Status
**Accepted (MVP lokal)** — implementasi awal ada di `apps/brain_qa` sebagai tooling operasional, bukan protokol jaringan.

## Konteks
Kita sudah punya dua lapisan yang saling melengkapi:
- **Integrity / tamper-evidence**: ledger snapshot Merkle (`brain_qa ledger`) untuk corpus publik.
- **Availability**: CID + pack erasure coding 4+2 + distribusi shard ke “node folder” + `locator.json`.

Yang masih kurang untuk posture *public with conditions* pada komunitas kecil:
- cara **mencatat keputusan kurasi** yang mengikat ke artefak tertentu (mis. `file_cid`), tanpa harus membangun ekonomi token.

## Keputusan
### 1) `storage audit` + `storage rebalance`
- `audit` wajib jadi ritual sebelum publish/mirror besar: mengecek shard hilang dan **hash shard** vs `shard_cid`.
- Interpretasi `audit` (MVP):
  - `ok: true` = **audit ketat**: semua shard bytes bisa ditemukan + cocok dengan `shard_cid`.
  - `recoverable: true` = masih ada **>= 4 shard valid** (RS 4+2) sehingga reconstruct masih realistis, meskipun redundancy belum “penuh”.
- `rebalance` adalah perbaikan praktis di lingkungan kecil: **salin ulang shard** ke node yang kekurangan dari sumber yang masih ada.

### 2) DataToken MVP = append-only registry + signature opsional
- Simpan token sebagai JSON Lines: `apps/brain_qa/.data/tokens/data_tokens.jsonl`.
- Field minimum: `token_id`, `file_cid`, `version`, `status`, `issuer`, `created_at`.
- Signature opsional: HMAC-SHA256 atas canonical JSON field minimum, kunci dari env `MIGHAN_BRAIN_DATA_TOKEN_KEY`.

## Non-goals (sengaja tidak dilakukan sekarang)
- Token transferabel, staking, mining, marketplace, atau “on-chain consensus”.
- Otomasi jaringan P2P (DHT, gossip, payment channel).

## Konsekuensi
- (+) Operasi data jadi lebih aman secara prosedural: audit sebelum andalkan redundancy.
- (+) “Approved artifact” bisa dirujuk dengan token_id + verifikasi signature (jika kunci diset).
- (-) Ini **bukan** bukti otoritas multi-pihak; itu butuh trust model/keys terpisah (mis. banyak signer, atau policy terpusat yang eksplisit).

## Implikasi berikutnya (bila komunitas tumbuh)
- Multi-signer approvals + role policy.
- Bundle “release manifest” yang merujuk: `file_cid` + `ledger snapshot` + `token_id`.
