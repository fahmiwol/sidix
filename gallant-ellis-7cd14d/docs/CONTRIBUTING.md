# Contributing — Mighan-brain-1

**Baru di repo?** Baca dulu [`docs/00_START_HERE.md`](00_START_HERE.md) (prolog + peta baca) dan [`docs/STATUS_TODAY.md`](STATUS_TODAY.md) (fokus terkini).

Tujuan kontribusi di repo ini: **membantu corpus makin kaya** dengan cara yang **aman, terbukti asal-usulnya (sanad/provenance), dan patuh lisensi**.

Repo ini bersifat open-source. Namun, tidak semua kontribusi punya tingkat risiko yang sama. Karena itu, kontribusi dibagi menjadi dua jalur:

## 1) Contribution tiers

### Tier A — **Data / Corpus PR (lebih aman, diprioritaskan)**
Kontribusi ke konten publik yang di-index oleh `brain_qa`:
- `brain/public/**` (research notes, principles, glossary, sources, web_clips)

**Syarat minimum**:
- Ada **sumber** (URL / bibliografi / referensi)
- Ada **lisensi/provenance** yang jelas (atau setidaknya tidak melanggar hak cipta)
- Ringkasan pakai kata-kata sendiri (hindari copy-paste panjang)
- Tidak ada PII/secrets (token, email pribadi, nomor, dsb)

**Review**: bisa semi-otomatis (rules + checklist) dan cepat.

### Tier B — **Tools / Plugins / Connectors PR (berisiko, manual review)**
Kontribusi yang bisa menambah kemampuan eksekusi (network, tool calls, connectors):
- `brain/plugins/**`
- perubahan pada `apps/brain_qa/**` yang menambah tool/connector baru

**Default policy**:
- **Disabled by default**
- **Manual review wajib**
- Manifest plugin harus mendeklarasikan permission/capabilities (lihat `docs/plugins_skills_connectors.md`)

## 2) Lisensi & provenance (wajib)

Poin minimal yang harus selalu jelas:
- **Apa sumbernya?** (URL, judul, tanggal bila ada)
- **Lisensinya apa?** (mis. CC BY-SA, vendor docs, paper arXiv)
- **Konten yang dimasukkan** harus berbentuk **ringkasan**, bukan salinan panjang dari materi berlisensi tertutup.

Lihat juga:
- `brain/public/sources/00_source_policy.md`
- `brain/public/sources/CONTRIBUTION_POLICY.md`

## 3) Curation workflow (untuk web clips)

Pipeline standar:
1) `fetch` → simpan ke `brain/private/web_clips/` (private)
2) `curate draft` → hasil draft di `apps/brain_qa/.data/curation_drafts/`
3) Edit manual (ringkas, pastikan lisensi aman)
4) `curate publish` → baru masuk `brain/public/sources/web_clips/`
5) `index` → agar terbaca oleh `brain_qa`

Catatan:
- `brain/private/**` tidak boleh dipublish/di-commit.
- Kalau sumber berpotensi 403 / paywall, cukup simpan **ringkasan** + **link**.

## 4) Aturan keamanan (non-negotiable)

- **No secrets**: jangan commit API keys/credential/config sensitif.
- **No PII**: jangan commit data pribadi pengguna/klien.
- **No malware / illegal hooks**: plugin/connector yang mencoba akses ilegal akan ditolak dan diblok.
- **Auditability**: perubahan besar harus punya alasan dan jejak sumber.

## 5) Style konten (agar retrieval bagus)

- **1 file = 1 topik**
- Heading jelas (`#`, `##`, `###`)
- Gunakan bullet ringkas + definisi yang eksplisit
- Bedakan **fakta** vs **interpretasi** vs **hipotesis**

## 6) Review checklist (singkat)

Untuk Tier A (corpus):
- [ ] Ada sumber + lisensi/provenance
- [ ] Ringkasan sendiri (tanpa copy panjang)
- [ ] Tidak ada PII/secrets
- [ ] Struktur rapi (heading + 1 topik)

Untuk Tier B (plugin/tool):
- [ ] Manifest `plugin.json` lengkap + permission jelas
- [ ] Default disabled
- [ ] Tidak ada credential di repo
- [ ] Tool usage sesuai allowlist/policy

