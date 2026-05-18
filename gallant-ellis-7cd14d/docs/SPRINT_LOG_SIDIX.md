# Sprint log — SIDIX (±2 jam & sesi berikutnya)

**Rencana sprint (checklist):** [`SPRINT_SIDIX_2H.md`](SPRINT_SIDIX_2H.md)  
**Living log repo:** [`LIVING_LOG.md`](LIVING_LOG.md)

---

## Kerangka etos (singkat)

- **Ihos & turunan wajib** dijaga lewat **dokumentasi, sanad, dan eval** — bukan lewat klaim marketing.
- **“Kun fa-yakūn”** dalam praktik engineering = **putusan + eksekusi langkah berikutnya yang konkret** (satu endpoint hijau, satu tes, satu metrik), bukan menjanjikan model frontier sekelas Opus dalam 24 jam tanpa bukti.
- **Kecepatan “buraq”** yang jujur di sisi kita = pipeline **RAG + adapter + serve + UI** yang rapat dan terukur — bukan menabrak hukum komputasi atau data.
- Ayat **perubahan dari diri** (konteks Al-A‘lā / prinsip ta’alluh): arah stack berubah lewat **ritme sprint, log, dan koreksi** — isi baris **Hasil** di bawah setiap sesi.

---

## Cara pakai file ini

1. Tiap sesi sprint, isi blok **Sesi** (tanggal, waktu mulai/selesai opsional).
2. Untuk setiap baris A1–C3: **`[ ]` → `[x]`** bila selesai; tulis **Hasil** (pass/fail, curl ringkas, error satu baris).
3. Setelah sesi: **satu** bullet di `LIVING_LOG.md` dengan tag `TEST:` / `DOC:` merujuk file ini.

---

## Sesi template (salin untuk sprint berikutnya)

```markdown
### Sesi YYYY-MM-DD — judul singkat

| Waktu (opsional) | Mulai: __:__ | Selesai: __:__ |
|------------------|-------------|----------------|

| ID | Tugas | Status | Hasil / eviden |
|----|--------|--------|------------------|
| A1 | `serve` + `GET /health` → `model_ready` | [ ] | |
| A2 | `POST /agent/generate` | [ ] | |
| A3 | `POST /ask` + persona | [ ] | |
| B1 | UI dev + `VITE_BRAIN_QA_URL` | [ ] | |
| B2 | `agentGenerate()` di `api.ts` | [ ] | |
| B3 | Settings → Tes generate | [ ] | |
| C1 | Enter vs Shift+Enter (regresi) | [ ] | |
| C2 | Status bar ← `model_mode` `/health` | [ ] | |
| C3 | Update `LIVING_LOG.md` | [ ] | |

**Blocker:**  
**Next sprint:**
```

---

## Sesi 2026-04-18 — pembukaan log + dokumen sprint

| Waktu | Mulai: — | Selesai: — |
|-------|------------|------------|

| ID | Tugas | Status | Hasil / eviden |
|----|--------|--------|------------------|
| — | Dibuat `SPRINT_SIDIX_2H.md` + research note PDF path | [x] | Lihat `LIVING_LOG.md` § 2026-04-18 |
| — | Dibuat `SPRINT_LOG_SIDIX.md` (file ini) | [x] | — |
| A1 | `serve` + `GET /health` → `model_ready` | [ ] | *(isi setelah dijalankan di mesin)* |
| A2 | `POST /agent/generate` | [ ] | |
| A3 | `POST /ask` + persona | [ ] | |
| B1 | UI dev + `VITE_BRAIN_QA_URL` | [ ] | |
| B2 | `agentGenerate()` di `api.ts` | [x] | `SIDIX_USER_UI/src/api.ts` — timeout 300s |
| B3 | Settings → Tes generate | [x] | Tab Model: tombol + meta `mode/model/duration_ms` |
| C1 | Enter vs Shift+Enter | [x] | Enter = kirim; Shift+Enter = baris baru (perilaku textarea) |
| C2 | Status bar ← `/health` | [x] | `formatStatusLine`: dok + `model_mode` + LoRA/mock |
| C3 | `LIVING_LOG` untuk sesi eksekusi penuh | [x] | Entri 2026-04-15 (sprint lanjutan) |

**Blocker:** *(mis. bitsandbytes di Windows, VRAM, deps)*  

**Next sprint:** centang A1–A3 dulu; lalu B2–B3.

---

### Sesi 2026-04-15 — otomasi pra-luncur v1 (agen, user AFK)

| Waktu | Mulai: — | Selesai: — |
|-------|------------|------------|

| ID | Tugas | Status | Hasil / eviden |
|----|--------|--------|------------------|
| G0 | Golden smoke + `pytest tests/` | [x] | 3/3 OK; 53 passed |
| G0b | `npm run build` `SIDIX_USER_UI` | [x] | Vite build ~12s, exit 0 |
| A1 | `serve` + `/health` `model_ready` | [ ] | Butuh bobot di mesin |
| A2 | `POST /agent/generate` non-mock | [ ] | Tergantung G2 STATUS |

**Blocker:** bobot `adapter_model.safetensors` belum di repo lokal agen.

**Next sprint:** operator salin adapter; lalu A1–A3 manual; tetap dalam gate `STATUS_TODAY.md` § Pre-rilis v1.

---

## Indeks sesi (append ringkas)

| Tanggal | Fokus | Ringkasan hasil |
|---------|--------|------------------|
| 2026-04-15 | UI + pra-luncur v1 | `agentGenerate` + status bar + tab Model; golden + pytest + `npm run build`; STATUS § Pre-rilis v1 |
| 2026-04-18 | Pembukaan log + wiring dokumen | Log + checklist; eksekusi A–C menunggu mesin |

*Baris baru ditambahkan ke tabel ini setiap sesi yang menyelesaikan minimal satu blok A/B/C.*
