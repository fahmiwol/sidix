# Definisi “selesai rilis” — Projek Badar / SIDIX (G1)

Dokumen ini memenuhi checklist batch **# kerja 1** (*Al-Fatihah*): charter ringkas + definisi **done** + acuan healthcheck.

## Apa artinya “selesai” untuk satu modul checklist

Satu baris di `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` dianggap **selesai** bila:

1. **Artefak** — ada perubahan kode, skrip, konfigurasi, atau dokumen operasional yang bisa diaudit di repo.
2. **Goal** — baris tersebut memang melayani **G1–G5** yang tercantum di kolom Goal; bukan pekerjaan mengambang.
3. **Bukti** — minimal satu dari: hasil perintah uji/smoke, entri `docs/LIVING_LOG.md` dengan tag wajib, atau PR/commit message yang merujuk baris / # kerja.
4. **Own-stack** — tidak mengganti default inference dengan API vendor tanpa instruksi eksplisit pemilik repo (`AGENTS.md`).

## Healthcheck layanan (SIDIX Inference Engine)

Endpoint **`GET /health`** pada `brain_qa.agent_serve` (port default **8765**) harus mengembalikan JSON yang memuat setidaknya:

| Field | Arti |
|--------|------|
| `status` | `"ok"` bila proses hidup. |
| `model_ready` | Adapter LoRA + bobot tersedia untuk inferensi lokal. |
| `model_mode` | `"local_lora"` \| `"mock"`. |
| `corpus_doc_count` atau setara | Indikator indeks (mis. jumlah baris chunk / dokumen). |
| `tools_available` | Jumlah tool terdaftar untuk agen. |

**Operator:** `curl -s http://127.0.0.1:8765/health` atau dari UI SIDIX status bar.

## Yang bukan “selesai”

- Hanya mengubah teks di issue tracker tanpa repo.
- Mencentang checklist tanpa bukti uji atau tanpa artefak.
- Mengandalkan API inference pihak ketiga sebagai **default** arsitektur tanpa label POC dan tanpa perintah eksplisit.

## Tautan

- Master 114: `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md`
- Penyelarasan goal: `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md`
- Internal backbone / narasi: `docs/PROJEK_BADAR_INTERNAL_BACKBONE.md`
