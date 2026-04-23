# SIDIX — QA Review & Audit (rapi)

**Tanggal:** 2026-04-25  
**Sumber:** audit eksternal gabungan (ringkasan eksekutif + laporan 11 bagian)  
**Repo:** https://github.com/fahmiwol/sidix  
**Situs:** https://sidixlab.com · https://app.sidixlab.com  
**Versi referensi:** v0.7.4-dev (backend) · v1.0.4 (UI landing/app)

> Dokumen ini untuk perencanaan perbaikan. Beberapa perintah di bawah bersifat **ilustratif**; sesuaikan dengan struktur repo aktual sebelum dijalankan.

---

## Executive summary

| Aspek | Skor | Komentar singkat |
|-------|:----:|------------------|
| Konsep & visi (IHOS) | ⭐⭐⭐⭐⭐ | Visionary; diferensiasi kuat. |
| Landing page | ⭐⭐⭐⭐☆ | Profesional; perlu social proof & footer. |
| App UI | ⭐⭐⭐⭐☆ | Bersih; badge [FACT]/[OPINION] dan sanad kurang terekspos. |
| Struktur repo | ⭐⭐⭐☆☆ | Banyak duplikat folder / `.bat` di root. |
| Git hygiene | ⭐⭐⭐☆☆ | Pesan commit tidak seragam; pernah ada leak path (sudah ada commit perbaikan). |
| Testing | ⭐⭐☆☆☆ | Cakupan lemah; risiko regresi (mis. typo bridge). |
| Dokumentasi | ⭐⭐⭐⭐☆ | Kaya; agak terfragmentasi & banyak file di root. |
| **Ringkasan** | **~3,7/5** | Fondasi filosofis kuat; **tiga isu kritis** di bawah harus ditangani sebelum eksposur publik lebar (kontributor & developer). |

### Tiga isu kritis (utamakan)

1. **Repo berantakan** — Folder dengan spasi / nama tidak konsisten (`Agent_Instagram Scraping SIDIX/`, `Arsitektur jiwa dan Plugin/`, `Framework_bahasa_plugin_update/`), banyak `.bat` di root, duplikat `install-deps.bat` vs `install_deps.bat`. Kesan pertama untuk kontributor menurun meski kode inti solid.
2. **Testing tipis** — Coverage dan CI belum memadai; perubahan baru (mis. typo bridge) bisa rusak tanpa alarm. Pilar Jiwa perlu jejak tes yang jelas.
3. **Jejak personal & kebersihan git** — Ada riwayat commit terkait penghapusan path internal; perlu **audit berkala** (grep pola sensitif, conventional commits, pre-commit bila memungkinkan).

### Yang sudah kuat (jangan rusak arahnya)

- Positioning IHOS dan diferensiasi epistemik.  
- Filter Maqashid dan rantai sanad sebagai narasi produk.  
- Tema landing gelap + branding SIDIX.  
- Sistem persona (AYMAN / ABOO / OOMAR / ALEY / UTZ).

---

## 1. Critical issues (detail)

### 1.1 Struktur repo & root clutter

**Gejala:** Folder duplikat / eksperimen di root; ~9 file `.bat`; kemungkinan duplikat nama install.

**Dampak:** Clone lebih berat, onboarding membingungkan, kesan kurang rapi.

**Arah perbaikan (contoh — verifikasi path dulu):**

- Konsolidasi skrip Windows ke `scripts/windows/` (atau setara).  
- Satukan / hapus duplikat install; dokumentasikan satu jalur resmi.  
- Folder eksperimen: `archive/`, `docs/`, atau `.gitignore` + dokumen “tidak ikut rilis”.

### 1.2 Testing & CI

**Gejala:** Satu file tes terpusat di root (mis. sprint); folder `tests/` kurang jelas; typo bridge butuh tes regresi; pilar Jiwa tanpa unit test jelas.

**Dampak:** Deploy produksi berisiko; kontributor sulit memastikan tidak ada regresi.

**Arah perbaikan:**

- GitHub Actions (atau CI setara): pytest + lint pada PR.  
- Target bertahap untuk modul inti (`brain/`, `apps/brain_qa/`).  
- Tes integrasi ringkas: typo → normalisasi → respons.

### 1.3 Git, pesan commit, dan data sensitif

**Gejala:** Campur bahasa di commit; pernah ada perbaikan “path leak”.

**Dampak:** Risiko kebocoran path / identitas di sisa file; histori sulit dibaca.

**Arah perbaikan:**

- Audit: `grep` / pemindaian secret untuk pola path lokal, nama, dsb. (sesuaikan pola).  
- Standar: Conventional Commits (bahasa Inggris) untuk commit baru.  
- Pre-commit: lint + cek pola sensitif (opsional).

---

## 2. Landing page (sidixlab.com)

**Yang sudah baik:** Dark theme, tipografi hero, value prop self-hosted, CTA, roadmap, tiga pilar Calibrate/Trace/Scrutinize, responsif.

**Perlu polish:**

| Isu | Saran |
|-----|--------|
| Hook hero | Pertimbangkan social proof singkat (stars, kontributor) di atas fold. |
| Bukti sosial | Tampilkan metrik (dokumen, tools, persona) jika sudah akurat. |
| Roadmap | Tambah “Sedang dikerjakan” / “Berikutnya”, tidak hanya “Selesai”. |
| CTA “Train SIDIX” | Jika mengarah ke Telegram, ubah label atau arahkan ke docs / notebook training agar tidak misleading. |
| Footer | Privacy, Terms, kontak — untuk kepercayaan & compliance. |

---

## 3. App UI (app.sidixlab.com)

**Yang sudah baik:** Dark mode, selector persona, kartu kategori, indikator status, opsi korpus/fallback, pola input yang familiar.

**Perlu polish:**

| Isu | Saran |
|-----|--------|
| Indikator “3/3” | Tooltip atau label jelas (kuota / sesi / thread). |
| Sign in | Jelaskan manfaat vs anonim (khususnya self-hosted). |
| Versi | Tampilkan eksplisit mis. **UI v1.0.4 · Engine v0.7.4-dev** agar tidak membingungkan. |
| Umpan balik | Pertimbangkan thumbs up/down, laporan halusinasi, salin blok kode. |
| Kualitas respons | Tampilkan badge **[FACT] / [OPINION] / [UNKNOWN]** dan jejak **sanad** di UI — ini diferensiator. |
| CQF | Pertimbangkan menampilkan skor / indikator kualitas jika sudah ada di backend. |

---

## 4. Git & struktur cabang

- Tinjau jumlah cabang vs kebutuhan; pertimbangkan alur `main` + `feature/*` atau trunk + PR wajib.  
- Hindari commit samar seperti “Add files via upload” pada masa depan; gunakan pesan konvensional.

---

## 5. Dokumentasi

**Kuat:** README filosofis, CHANGELOG, CONTRIBUTING, SECURITY, AGENTS, handoff, panduan agen.

**Perbaikan:**

- Kurangi kepadatan root: pindahkan materi panjang ke `docs/` dengan indeks di README.  
- API: OpenAPI/Swagger untuk endpoint publik bila belum ada.  
- Diagram: Mermaid atau gambar arsitektur di `docs/`.

---

## 6. Keamanan (ringkas)

- Pertahankan MCP default off sesuai kebijakan.  
- Audit: kredensial keras, CORS, unggahan file, sanitasi input pada normalizer typo.  
- Dependabot / pembaruan dependensi bila memungkinkan.

---

## 7. Next steps (prioritas)

### P1 — minggu ini

| No | Tugas | Estimasi | Dampak |
|----|--------|----------|--------|
| 1 | Rapikan root: folder duplikat + `.bat` | ~2 jam | Tinggi |
| 2 | CI: pytest + lint | ~4 jam | Tinggi |
| 3 | Audit jejak personal / path | ~2 jam | Tinggi |
| 4 | Badge FACT/OPINION di UI | ~2 jam | Tinggi |
| 5 | Perbaiki CTA landing “Train” | ~0,5 jam | Sedang–tinggi |
| 6 | Dokumentasi API (OpenAPI) | ~4 jam | Tinggi |

### P2 — bulan ini

| No | Tugas | Estimasi | Dampak |
|----|--------|----------|--------|
| 7 | Tes untuk pilar Jiwa & typo bridge | ~2 hari | Tinggi |
| 8 | Pre-commit (lint + cek leak) | ~3 jam | Tinggi |
| 9 | Landing: social proof + footer | ~4–6 jam | Sedang |
| 10 | UI: salin / thumbs / laporan | ~4 jam | Sedang |

### P3–P4 — strategis

- Komunitas: Discussions, label `good-first-issue`, kanal obrolan (sesuai kebijakan proyek).  
- Eksposur: awesome-selfhosted, Product Hunt / forum teknis (sesuai kesiapan).  
- Konten: demo GIF/video, artikel “AI yang mengakui ketidaktahuan”.  
- Program mahasiswa / OSS (mis. GSoC) bila cocok.

---

## 8. Checklist dapat disalin (GitHub Issue)

```markdown
### Repo
- [ ] Konsolidasi `*.bat` ke `scripts/windows/` (atau setara)
- [ ] Rapikan aset root (svg, pdf) ke `assets/` / `docs/`
- [ ] Satukan / hapus duplikat skrip install
- [ ] Tinjau folder ber-spasi / eksperimen → archive atau docs

### CI & testing
- [ ] Workflow CI (pytest + lint)
- [ ] Tes regresi typo bridge
- [ ] Tes bertahap untuk modul Jiwa / orkestrasi
- [ ] Target coverage bertahap untuk inti

### Keamanan
- [ ] Audit secret / path / token
- [ ] Tinjau CORS & sanitasi input
- [ ] Dependabot atau jadwal bump deps

### Landing
- [ ] CTA “Train” selaras dengan tujuan (docs / notebook)
- [ ] Footer: Privacy, Terms, kontak
- [ ] Metrik / social proof (jika data valid)
- [ ] SEO title & meta

### App UI
- [ ] Badge FACT / OPINION / UNKNOWN
- [ ] Sanad / provenance terlihat
- [ ] Tooltip “3/3” & versi UI vs engine
- [ ] Onboarding pengguna baru

### Dokumentasi & komunitas
- [ ] OpenAPI untuk API publik
- [ ] Diagram arsitektur
- [ ] Template isu + Discussions (opsional)
```

---

## 9. Penutup

SIDIX menempatkan **kejujuran epistemik** sebagai produk, bukan sekadar gaya bahasa. Celah utama saat ini ada di **higiene repo**, **tes otomatis**, dan **eksposur diferensiator di UI** — bukan di visi inti.

**Kutipan untuk README (opsional):**

> *We don't build AI that knows everything. We build AI that knows what it knows, admits what it doesn't, and always tells you the difference.*

**Pesan untuk maintainer:**

> Setelah tiga isu kritis ditangani, kesan publik ke kontributor naik signifikan. Landing dan app sudah pada jalur baik; yang paling terlihat dari luar adalah kerapian repo dan hijau di CI. Membangun komunitas dan isu yang ramah kontributor akan membantu metrik GitHub selaras dengan kedalaman proyek.

---

*Review ini dimaksudkan untuk memperkuat SIDIX. Standing alone. Transparan. Jujur — selaras ethos proyek.*
