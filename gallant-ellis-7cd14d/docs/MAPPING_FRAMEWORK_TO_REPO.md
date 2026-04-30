# Pemetaan paket framework → struktur repo SIDIX

**Versi:** 1.0 · **Tujuan:** satu sumber kebenaran untuk agen & kontributor — *apa yang diimpor*, *ke mana*, *status implementasi*.

**Bahasa:** Indonesia (dokumen); kode tetap mengikuti konvensi repo (inggris untuk sumber kode).

---

## 1. Sumber bundel lokal

| Asal (workspace) | Isi | Catatan |
|------------------|-----|---------|
| `Framework_bahasa_plugin_update/sidix-cursor-brief/` | Brief Cursor: typo multibahasa, TYPO ID, Jiwa, Kimi, BRIEF master | Diimpor ke `brain/typo/`, `brain/jiwa/`, `docs/` |
| `Framework_bahasa_plugin_update/sidix-docs/` | Paket dokumen SocioMeter (strategi, PRD, ERD, …) | Diimpor ke `docs/sociometer/` |

Folder sumber **tidak** dihapus otomatis; bundel tetap bisa dipakai sebagai arsip lokal.

---

## 2. Peta file: brief → repo

| Artefak sumber | Path resmi di repo | Status |
|----------------|-------------------|--------|
| `MULTILINGUAL_TYPO_FRAMEWORK.md` | `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md` | Spesifikasi + kamus dalam dokumen; path kode dalam spec diarahkan ke `brain/typo/` |
| `TYPO_RESILIENT_FRAMEWORK.md` | `brain/typo/TYPO_RESILIENT_FRAMEWORK.md` | Spesifikasi 4-lapis Indonesia |
| `ARSITEKTUR_JIWA_SIDIX.md` | `brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md` | Blueprint pilar (korpus); runtime di `apps/brain_qa/brain_qa/jiwa/` |
| `KIMI_INTEGRATION_GUIDE.md` | `docs/KIMI_INTEGRATION_GUIDE.md` | Panduan integrasi host (opsional) |
| `BRIEF_SIDIX_SocioMeter.md` | `docs/BRIEF_SIDIX_SocioMeter.md` | Brief master untuk Cursor / orkestrasi tugas |
| `kimi-plugin/manifest.json` | `kimi-plugin/manifest.json` | Manifest plugin (8 skill); persona 5 |
| `kimi-plugin/sidix_skill.yaml` | `kimi-plugin/sidix_skill.yaml` | Skill YAML; **MCP default `false`** |

---

## 3. Peta SocioMeter: `docs/sociometer/`

| Path | Fungsi |
|------|--------|
| `strategi/01_STRATEGI_SOCIOMETER.md` | Strategi produk |
| `prd/02_PRD_SOCIOMETER.md` | PRD |
| `erd/03_ERD_SOCIOMETER.md` | Model data |
| `dokumentasi/04_DOKUMENTASI_SOCIOMETER.md` | Dokumentasi umum |
| `fitur/05_FITUR_SPECS_SOCIOMETER.md` | Spesifikasi fitur |
| `plan/06_IMPLEMENTATION_SOCIOMETER.md` | Rencana implementasi |
| `riset/07_RISET_SOCIOMETER.md` | Riset |
| `script/08_SCRIPT_MODULE_SOCIOMETER.md` | Modul skrip |
| `dokumentasi/09_VISI_SOCIAL_RADAR.md` | Visi Social Radar (jika ada di folder) |
| `CATATAN_PROGRES.md` | Catatan progres (jika dipelihara) |

Indeks manusia: **`docs/sociometer/README.md`**.

**Relasi ke kode:** endpoint / modul Social Radar yang sudah ada di repo (mis. `social_radar.py`, sprint 7) harus diselaraskan dengan dokumen ini secara bertahap — dokumen = utara produk; kode = verifikasi di `CHANGELOG` / `LIVING_LOG`.

---

## 4. Typo: spesifikasi vs kode berjalan

| Konsep (dokumen) | Implementasi saat ini | Celah / lanjut |
|------------------|----------------------|----------------|
| 5-layer universal + 1.150+ pola | `brain/typo/pipeline.py` (MVP: NFC, substitusi ringan, script hint) | Kurasi `locales/*.json`, modul detector/corrector sesuai spec |
| 4-layer Indonesia + semantic/confidence | Belum modul terpisah; sebagian perilaku ada di RAG/ReAct | Ekstraksi bertahap dari `TYPO_RESILIENT_FRAMEWORK.md` |
| Integrasi chat | `apps/brain_qa/brain_qa/typo_bridge.py` + `run_react` | Env `SIDIX_TYPO_PIPELINE` |

---

## 5. Jiwa: korpus vs runtime

| Pilar | Dokumen / korpus | Runtime produksi |
|-------|------------------|------------------|
| Nafs, Aql, Qalb | `brain/nafs/`, `brain/aql/`, `brain/qalb/` | Hook di `brain_qa.jiwa` |
| Ruh, Hayat, Ilm, Hikmah | `brain/{ruh,hayat,ilm,hikmah}/` + `ARSITEKTUR_JIWA_SIDIX.md` | Sebagian delegasi ke `learn_agent`, Hayat refine, dll. |

**Keputusan arsitektur:** hindari duplikasi logika tanpa tes; satukan impor atau dokumentasikan “sumber kebenaran” per subsistem.

---

## 6. Git & landing

| Artefak | Lokasi |
|---------|--------|
| Riwayat rilis | `CHANGELOG.md` (root), `docs/CHANGELOG.md` |
| Log agen | `docs/LIVING_LOG.md` |
| UI pengguna | `SIDIX_USER_UI/` (versi & “What’s new” bilingual) |
| Pintu masuk docs | `docs/00_START_HERE.md` |

Setelah perubahan dokumen bermakna: **commit** dengan pesan konvensional; **landing** mengikuti versi patch UI (`v1.0.x`) yang selaras dengan narasi rilis, bukan selalu sama dengan tag semver backend.

**Rilis sinkron (2026-04-25):** backend/docs **`v0.7.4-dev`**, landing **`v1.0.4`** — riwayat commit: `git log --oneline -5` pada `main` (paket fitur besar: *typo bridge*, *brain/typo*, *Jiwa korpus*, *jembatan sarang-tamu* — folder `kimi-plugin/`). Lihat `CHANGELOG.md` dan `docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_PLUGIN_ORBIT.md`.

---

## 7. Aturan tetap (ringkas)

- **Standing alone:** tidak ada API vendor wajib pada jalur inti typo/Jiwa.
- **Persona SIDIX:** AYMAN, ABOO, OOMAR, ALEY, UTZ.
- **Terminologi:** Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir.

---

_Dokumen ini harus diperbarui ketika bundel sumber berubah atau struktur repo dipindahkan._
