# Sprint ±2 jam — SIDIX “enak dipakai” (bukan parity penuh Cursor/Claude)

**Sprint log (isi hasil tiap sesi):** [`SPRINT_LOG_SIDIX.md`](SPRINT_LOG_SIDIX.md)

**Tujuan realistis:** satu alur **chat + korpus (RAG)** + **satu tombol/endpoint cek generate lokal** jalan mulus di mesin kamu, dengan **health** yang jujur (`model_ready`). Parity penuh (multi-tab, Composer, codebase agent, plugin) **bukan** scope 2 jam — dipecah sprint berikutnya.

## Prasyarat (5 menit)

1. Adapter **flat**: `apps/brain_qa/models/sidix-lora-adapter/` berisi `adapter_config.json` + **`adapter_model.safetensors`**.
2. Python deps inference (sesuai GPU/Windows): `torch`, `transformers`, `peft`, `accelerate`; untuk 4-bit: `bitsandbytes` (sering lebih mulus di WSL/Linux).
3. Dari `apps/brain_qa`: `pip install -r requirements.txt` lalu deps inference di atas.

## Blok 0–30 menit — Bukti backend

| # | Tugas | Cek |
|---|--------|-----|
| A1 | `python -m brain_qa serve` (port 8765) | `GET /health` → `model_ready: true` jika bobot ada |
| A2 | `POST /agent/generate` dengan JSON kecil | Respons **bukan** template mock panjang; atau error load yang jelas |
| A3 | `POST /ask` + persona | Masih RAG + ReAct seperti sebelumnya |

## Blok 30–90 menit — UI seperti “satu panel chat”

| # | Tugas | Catatan |
|---|--------|---------|
| B1 | `npm run dev` di `SIDIX_USER_UI`, `VITE_BRAIN_QA_URL` ke 8765 | Sudah ada Enter-to-send (tanpa Shift) |
| B2 | Tambah `agentGenerate()` di `src/api.ts` → `POST /agent/generate` | Untuk tes model langsung tanpa RAG |
| B3 | Di Settings → tab Model: tombol **“Tes generate”** (prompt pendek) + tampilkan `mode` + `duration_ms` | UX mirip “cek model hidup” |

## Blok 90–120 menit — Polish minimal “daily driver”

| # | Tugas | Catatan |
|---|--------|---------|
| C1 | **Shift+Enter** = baris baru (textarea); Enter = kirim — sudah? pastikan tidak regresi | |
| C2 | Status bar: tampilkan `model_mode` dari `/health` (mock vs local_lora) | User tahu sedang pakai apa |
| C3 | Catat hasil di `docs/LIVING_LOG.md` (`TEST:` + perintah + pass/fail) | |

## Setelah sprint (backlog “mirip Cursor/Claude”)

- Multi-chat / session list + rename tab.
- Stream token dari `/agent/generate` (bukan hanya ReAct lalu stream jawaban).
- Tool palette + @file (butuh integrasi workspace).
- Eval harness + logging usage lokal.

Lihat juga: `docs/10_execution_plan.md`, `docs/HANDOFF-2026-04-17.md`.
