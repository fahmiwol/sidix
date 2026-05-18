# Rencana eksekusi — Mighan-brain-1 (hidup)

> **Tujuan**: satu halaman yang mengikat **status**, **prioritas**, dan **siapa menggerakkan apa** — agar komunitas, kontributor, dan agen tidak mulai dari nol setiap minggu.  
> **Cara pakai**: setelah satu *batch* kerja selesai, perbarui bagian **Sekarang** + checklist; catat detail uji/error di `docs/LIVING_LOG.md` (dengan tag).

---

## Sekarang (fokus 1–2 minggu)

| Item | Status | Catatan |
|------|--------|---------|
| Pintu masuk docs | Selesai | `00_START_HERE.md`, `STATUS_TODAY.md`, README/CONTRIBUTING/AGENTS. |
| MVP CLI `brain_qa` | Jalan | Index, ask, kurasi, ledger, storage, token — lihat `apps/brain_qa/README.md`. |
| Bukti storage end-to-end | **Belum** | Smoke `reconstruct-nodes` → file out + bandingkan hash/size dengan sumber. |
| Keputusan produk Phase 1 | **Selesai** | **UI dulu** — lihat `LIVING_LOG` tag `DECISION:` dan bagian “UI: user vs admin” di bawah. |
| Roadmap vs realita | **Belum** | Sesuaikan `06_roadmap.md` (checklist + fase) supaya selaras dengan yang sudah ada di repo + keputusan UI. |

---

## Fase A — Bukti & kepercayaan (prioritas tinggi)

**Tujuan**: “yang di dokumen” punya **bukti runnable** untuk lapisan storage + ledger.

1. **TEST: `reconstruct-nodes`**
   - Prasyarat: ada pack untuk satu `file_cid`, node sudah punya cukup shard (atau `recoverable: true` dari `storage audit`).
   - Jalankan: `python -m brain_qa storage reconstruct-nodes "<file_cid>" "<path_out>"` dari `apps/brain_qa`.
   - Verifikasi: hash file out = hash di manifest / ukuran sama; catat perintah + exit code di `LIVING_LOG` (`TEST:`).
2. **TEST: `ledger verify`** setelah perubahan korpus material (opsional tapi bagus sebagai ritual).
3. **OPS (opsional)**: jika target audit ketat `ok: true` — pack ulang dari file sumber atau restore shard, lalu `distribute` / `rebalance`; catat `FIX:` / `TEST:`.

**Butuh bantuan kamu bila**: path Windows berbeda, node folder dipindah, atau ingin `file_cid` lain sebagai contoh resmi — kirim path atau CID.

---

## Fase B — Keputusan arah (**selesai**)

**Keputusan (2026-04-15)**: **UI dulu** — bangun permukaan web untuk pengguna lebih dulu; `brain_qa` tetap jadi fondasi (bisa dipanggil sebagai subprocess/library/API tipis).

### UI: user vs admin — apakah dua *site*?

**Tidak wajib dua domain terpisah di MVP.** Pola yang disarankan:

| Lapisan | MVP (disarankan) | Fase lanjut (PRD Phase 2+) |
|---------|-------------------|-----------------------------|
| **User** | Satu app: chat + akses korpus/RAG + riwayat sederhana | Persona, workspace, fitur lengkap |
| **Admin** | **Minimal di app yang sama**: mis. route `/admin` atau tab “Pengaturan” — model API key lokal, toggle fitur eksperimen, lihat status index/ledger (read-only dulu) | Multi-user, RBAC, audit log operator, rate limit — sesuai persona P3 di PRD |

Jadi: **bukan otomatis “user site + admin site” dua produk**; bisa **satu codebase**, dua *area* (publik vs admin) dengan auth/role ketika multi-user hidup. Kalau nanti skala butuh, **pecah deploy** (subdomain admin) masih bisa tanpa rewrite total.

**Butuh bantuan kamu (opsional)**: preferensi branding (nama app), dan apakah MVP cukup **single-user** (tanpa login) seperti mode lokal PRD.

---

## Fase C — Dokumen selaras (setelah A + B)

1. **UPDATE**: `docs/06_roadmap.md` — tandai Phase 0/1 apa yang *sudah*; apa yang *masih*; hapus ilusi “hanya perancangan” jika tidak akurat.
2. **UPDATE**: `docs/STATUS_TODAY.md` — sinkronkan **Fase** / **Next** dengan rencana ini.
3. **DOC (opsional)**: satu subbagian di `00_START_HERE.md` “Ritual kontributor” (index → PR → ledger snapshot) — hanya jika kamu setuju supaya tidak gemuk.

**Butuh bantuan kamu**: tanggal atau milestone yang ingin dipakai di roadmap (mis. “April = fase A selesai”).

---

## Fase D — Produk besar (**UI dulu** — aktif)

- **Scaffold web**: sesuai `05_architecture.md` — satu proses API tipis + UI (stack dipilih tim; contoh umum: Next.js).
- **Chat MVP**: satu provider (API atau lokal), streaming bila mudah; **tool/agent gated** (default mati) sesuai PRD.
- **Integrasi `brain_qa`**: awalnya bisa `subprocess` ke `python -m brain_qa …` atau ekstrak library; evolusi ke HTTP internal.

Agen mulai dari spike kecil + dokumentasi di `LIVING_LOG` (`IMPL:` / `NOTE:`).

---

## Fase E — Komunitas (berkelanjutan)

- Tier A (korpus) vs Tier B (tool) — tetap ikut `CONTRIBUTING.md`.
- Setiap merge berarti: **CHANGELOG** (ringkas) + **LIVING_LOG** (detail uji bila perlu).

---

## Ringkasan: kapan perlu kamu?

| Situasi | Yang dibutuhkan dari kamu |
|---------|---------------------------|
| Pilih arah Phase 1 | **Selesai** — UI dulu (`LIVING_LOG` `DECISION:`). |
| Rekonstruksi / path | CID atau path file uji resmi di mesinmu. |
| Roadmap tanggal | Preferensi milestone (bulan / none). |
| Secret signing token | Jangan di chat; set lokal `MIGHAN_BRAIN_DATA_TOKEN_KEY`; agen hanya dokumentasikan nama var. |

Selebihnya agen bisa mengerjakan **A + D paralel** (bukti storage tidak harus menunggu UI), lalu **C** (roadmap) setelah spike UI punya bentuk jelas.
