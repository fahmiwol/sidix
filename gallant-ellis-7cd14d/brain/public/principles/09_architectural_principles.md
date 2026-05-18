# Prinsip Arsitektur — Mighan

> Prinsip-prinsip desain sistem yang diterapkan di semua proyek Mighan.

## 1 — Modular & pluggable

- Setiap kemampuan adalah "plugin": model, tool, memory, UI.
- Komponen bisa diganti tanpa mengubah keseluruhan sistem.
- Inter-komponen berkomunikasi lewat interface yang jelas (API/contract).
- **Contoh**: Model adapter bisa diganti dari Claude ke Ollama tanpa ubah UI.

## 2 — Security by default

- Akses file, terminal, dan browser **selalu gated** dan tercatat.
- Tools off by default — butuh izin eksplisit.
- Secrets (API keys) selalu terenkripsi.
- Audit log untuk setiap tool call.
- **Filosofi**: "Aman dulu, baru ngebut."

## 3 — Cost-aware

- Pengguna selalu tahu estimasi biaya sebelum aksi.
- Ada budget cap dan token limit.
- Mode hemat (model lokal) vs mode kualitas (API).
- Caching untuk menghindari request ulang yang tidak perlu.

## 4 — Data-driven & stateless logic

- Konfigurasi = data, bukan hardcode.
- Logika bisnis sebisa mungkin stateless.
- State disimpan di database/storage, bukan di memori proses.

## 5 — Incremental delivery

- Mulai dari MVP yang jalan, lalu iterasi.
- Jangan over-engineer di awal — bangun yang dibutuhkan sekarang.
- Roadmap berbasis fase yang realistis.

## 6 — Observability

- Log yang berguna (bukan spam).
- Tracing untuk agent runs.
- Cost visibility per request/run.

## Anti-pattern

- ❌ Hardcode konfigurasi yang seharusnya dinamis.
- ❌ Install dependensi besar tanpa justifikasi.
- ❌ Skip audit log untuk alasan "nanti aja".
- ❌ Auto-deploy tanpa review.
