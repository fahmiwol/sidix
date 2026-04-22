# `brain_qa` (MVP Brain Q&A)

Tujuan: jalanin Q&A berbasis **Markdown** di `brain/public/` secara lokal, dengan output:

- **Top sumber** (kutipan/rujukan) yang dipakai untuk menjawab
- Jawaban ringkas berbasis potongan teks tersebut (offline, tanpa API)

> Defaultnya **read-only**: hanya membaca `brain/public/` dan menulis index ke `apps/brain_qa/.data/`.

## Setup (Windows)

```powershell
cd "D:\MIGHAN Model\apps\brain_qa"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## QA ringan (golden + pytest root)

Dari **akar repo** `D:\MIGHAN Model` (venv tetap di `apps/brain_qa/.venv`):

```powershell
python apps/brain_qa/scripts/run_golden_smoke.py
apps\brain_qa\.venv\Scripts\python.exe -m pytest tests\ -q
```

`requirements-dev.txt` memuat `pytest` untuk suite di folder `tests/` (bukan hanya paket `brain_qa`).

## 1) Index Markdown

```powershell
python -m brain_qa index
```

Ini akan membuat index lokal di `apps/brain_qa/.data/`.

## 2) Tanya

```powershell
python -m brain_qa ask "apa itu maqasid dan gimana dipakai di Decision Engine?"
```

### Persona (router + template)

Default: auto-route berdasarkan kata kunci.

```powershell
python -m brain_qa ask "buat roadmap 2 minggu untuk mighan-brain-1" --persona TOARD
python -m brain_qa ask "ringkas dan analisis referensi untuk bab tesis" --persona FACH
python -m brain_qa ask "debug error ModuleNotFoundError di Windows" --persona HAYFAR
```

Kamu juga bisa pakai prefix:

```powershell
python -m brain_qa ask "TOARD: bikin rencana 7 hari"
```

### Autosuggest / Auto-escalate

Default: kalau confidence routing rendah, output akan menampilkan **saran switch persona**.

```powershell
python -m brain_qa ask "jelasin perbedaan wahyu akal indera" --k 2
```

Non-interactive auto-escalate (mirip “auto”, tapi langsung pindah persona):

```powershell
python -m brain_qa ask "jelasin perbedaan wahyu akal indera" --auto-escalate --k 2
```

Matikan saran switch:

```powershell
python -m brain_qa ask "jelasin perbedaan wahyu akal indera" --no-suggest-switch --k 2
```

## Settings (persist defaults untuk UI / CLI)

`brain_qa` bisa menyimpan default settings di:

- `apps/brain_qa/.data/settings.json`

CLI flags tetap **override** settings.json. Buat file settings (sekali):

```powershell
python -m brain_qa settings --init
python -m brain_qa settings --show
```

Contoh set default (non-interactive):

```powershell
python -m brain_qa settings --set-persona auto --set-autosuggest on --set-auto-escalate off
python -m brain_qa settings --set-k 4 --set-max-snippet-chars 450 --set-validate-profile hadith
```

## QA sanity check (anti kontradiksi)

Validasi cepat file `brain/datasets/qa_pairs.jsonl`:

```powershell
python -m brain_qa qa
```

Mode ketat + scan kontradiksi (heuristik):

```powershell
python -m brain_qa qa --strict --contradiction-scan
```

Exit code:

- `0` = OK
- `2` = ada duplikat ID atau entry invalid

## Ledger (Hafidz-style tamper-evident snapshots)

Ledger ini membuat **snapshot Merkle root** dari seluruh `.md` di corpus publik (root diambil dari `brain/manifest.json`), lalu menyimpannya sebagai **append-only chain** di:

- `apps/brain_qa/.data/ledger/snapshots.jsonl`

Cek status:

```powershell
python -m brain_qa ledger status
```

Buat snapshot baru (misalnya setelah publish atau perubahan corpus):

```powershell
python -m brain_qa ledger snapshot
```

Verifikasi:

- chain hash antar snapshot valid (tamper-evident)
- root snapshot terbaru sama dengan corpus saat ini

```powershell
python -m brain_qa ledger verify
```

## Storage (MVP): CID manifest + manual mirror

Ini adalah langkah awal menuju “availability layer” (server mati tapi data tetap bisa hidup di banyak node).
MVP ini belum P2P penuh—baru:

- hitung **CID** (`sha256:...`)
- simpan ke **manifest** lokal
- **verify** hash kapan pun
- **export** untuk mirror/pin manual ke folder lain (mis. disk eksternal / sync tool)

Status:

```powershell
python -m brain_qa storage status
```

Register file (buat CID + masuk manifest):

```powershell
python -m brain_qa storage add "D:\MIGHAN Model\brain\public\principles\11_storage_layers_ledger_vs_distribution.md"
```

Verify:

```powershell
python -m brain_qa storage verify "sha256:<hash>"
```

Export/mirror manual:

```powershell
python -m brain_qa storage export "sha256:<hash>" "D:\MIGHAN Model\.data\mirrors"
```

### Erasure coding (Hafidz advanced) — 4+2 pack & reconstruct

Ini membuktikan konsep “2 node mati tetap bisa reconstruct”.

Pack (buat 6 shard: 4 data + 2 parity):

```powershell
python -m brain_qa storage pack "D:\MIGHAN Model\brain\public\principles\11_storage_layers_ledger_vs_distribution.md"
```

Hasilnya tersimpan di `apps/brain_qa/.data/storage/packs/<cid>/` + `pack_manifest.json`.

Reconstruct dari pack (cukup ada 4 shard):

```powershell
python -m brain_qa storage reconstruct "D:\MIGHAN Model\apps\brain_qa\.data\storage\packs\<cid>" "D:\MIGHAN Model\apps\brain_qa\.data\reconstructed\rebuild.md"
```

### Phase 2 (simulasi komunitas terbatas): nodes + distribute + reconstruct-nodes

Kita bisa mensimulasikan “peer nodes” sebagai folder lokal.

Daftarkan node:

```powershell
python -m brain_qa storage node add nodeA "D:\MIGHAN Model\apps\brain_qa\.data\nodes\nodeA"
python -m brain_qa storage node add nodeB "D:\MIGHAN Model\apps\brain_qa\.data\nodes\nodeB"
python -m brain_qa storage node list
```

Distribusikan shard pack ke nodes (round-robin) + catat locator:

```powershell
python -m brain_qa storage distribute "sha256:<file_hash>" nodeA nodeB
```

Reconstruct dari nodes (walau shard lokal hilang/offline, selama masih <=2 shard hilang total):

```powershell
python -m brain_qa storage reconstruct-nodes "sha256:<file_hash>" "D:\MIGHAN Model\apps\brain_qa\.data\reconstructed\rebuild_from_nodes.md"
```

Audit (cek shard hilang + integritas hash shard vs `shard_cid`):

```powershell
python -m brain_qa storage audit "sha256:<file_hash>"
```

Catatan interpretasi output:

- `ok: true` artinya **semua shard ada** dan hash shard cocok dengan `shard_cid` (audit ketat).
- `recoverable: true` artinya masih ada **`good_shard_count` ≥ 4** shard yang valid (RS 4+2), sehingga reconstruct masih realistis — meskipun `ok` bisa tetap `false` kalau ada shard yang benar-benar belum tersebar ke semua lokasi yang kamu harapkan.

Rebalance / repair (salin shard yang belum ada di satu node, dari sumber lain yang masih hidup):

```powershell
python -m brain_qa storage rebalance "sha256:<file_hash>" nodeA
```

### DataToken MVP (governance ringan, bukan “coin economy”)

Registry append-only:

- `apps/brain_qa/.data/tokens/data_tokens.jsonl`

Opsional signing (disarankan untuk lingkungan kecil yang sudah punya secret management):

```powershell
$env:MIGHAN_BRAIN_DATA_TOKEN_KEY="ganti-dengan-secret-panjang-acak"
python -m brain_qa token issue "sha256:<file_hash>"
python -m brain_qa token list --tail 20
python -m brain_qa token verify --tail 20
```

## 3) Record mode (log Q/A)

```powershell
python -m brain_qa ask "apa itu sanad?" --record
```

Output akan ditambah ke:

- `apps/brain_qa/.data/records.jsonl`

## 4) Fetch web → simpan jadi knowledge clip (private)

```powershell
python -m brain_qa fetch "https://plato.stanford.edu/entries/mulla-sadra/"
```

File hasilnya disimpan ke:

- `brain/private/web_clips/`

> Setelah fetch, kalau kamu mau itu ikut “dibaca” oleh RAG, kamu bisa **copy/pindahkan versi yang aman** ke `brain/public/` (atau kita bikin mode index yang juga baca private—tapi defaultnya tidak).

## 5) Curation queue (private → draft publik)

Tujuan: clips hasil `fetch` masuk antrian, lalu kamu generate **draft** (ringkas + sanad) untuk dipindah ke `brain/public/`.

List semua clip private:

```powershell
python -m brain_qa curate list
```

Sync: tambahkan semua clip private yang belum ada di queue:

```powershell
python -m brain_qa curate sync
```

List queue:

```powershell
python -m brain_qa curate list --queue
```

Buat draft dari 1 clip (kategori: `general` / `tech` / `creative`):

```powershell
python -m brain_qa curate draft "D:\MIGHAN Model\brain\private\web_clips\cloud.google.com__apa-itu-kecerdasan-buatan-ai-google-cloud.md" --category general
```

Draft akan dibuat di `apps/brain_qa/.data/curation_drafts/`.

Publish (explicit) ke `brain/public/sources/web_clips/`:

```powershell
python -m brain_qa curate publish "D:\MIGHAN Model\apps\brain_qa\.data\curation_drafts\draft__cloud-google-com-apa-itu-kecerdasan-buatan-ai-google-cloud.md"
```

Catatan: `curate publish` akan otomatis membuat **ledger snapshot** (Merkle root) setelah publish sukses.
Auto `index` juga bisa diaktifkan via settings:

```powershell
python -m brain_qa settings --set-auto-reindex on
```

## 6) Validate: Text (profile-based)

Mode ini **bukan fatwa**. Ini hanya verifikasi (verification only) apakah sebuah teks *muncul / mirip* dengan yang sudah ada di knowledge library (corpus) + menampilkan kandidat + sitasi. Butuh human-in-the-loop untuk penetapan hukum yang sensitif.

Label keluaran yang didukung: `matched`, `partial`, `not_found`, `conflict_suspected`, `popular_snippet_suspected`.

**Contoh 1: Validasi konsep umum**

```powershell
python -m brain_qa validate text "Artificial intelligence is intelligence demonstrated by machines"
```

**Contoh 2: Validasi teks khusus hadits**

```powershell
python -m brain_qa validate text "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ" --profile hadith
```

**Contoh 3: Menangani alias lama (backwards compatible)**

```powershell
python -m brain_qa validate hadith "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ" --k 3
```

Arabic “exact-ish” matching (default ON):

- menghapus harakat/diacritics
- menyamakan varian huruf umum (mis. أ/إ/آ → ا)

Matikan normalisasi Arab:

```powershell
python -m brain_qa validate text "..." --profile hadith --no-arabic-normalize
```

Deteksi “potongan populer” (kutipan pendek yang match di banyak tempat):

- `--popular-max-tokens` (default 20)
- `--popular-min-strong` (default 3)

## Catatan

- Kalau kamu menambah/mengubah Markdown, jalankan `index` lagi.
