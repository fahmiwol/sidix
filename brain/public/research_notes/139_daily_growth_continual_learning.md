# 139. Daily Growth Engine — SIDIX Tumbuh Tiap Hari

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: ai / self-learning
> **Fase**: 4 (continual learning otomatis)
> **Tanggal**: 2026-04-18

---

## Prinsip

> *"Setiap hari SIDIX harus sedikit lebih tahu dari kemarin."*

Fase 3 membuat SIDIX bisa **riset mandiri saat ada gap**.
Fase 4 membuat SIDIX **terus belajar walau tidak ada gap** — karena pertumbuhan
tidak boleh menunggu kebutuhan. Harus jadi kebiasaan, bukan reaksi.

## Siklus 7-Tahap

```
┌──────────────────────────────────────────────────────────────┐
│  1. SCAN     — deteksi knowledge gap (atau pilih eksplorasi) │
│  2. RISET    — autonomous_researcher: angles + 5 POV + web   │
│  3. APPROVE  — quality gate: ≥6 findings, narasi ≥250 char   │
│  4. TRAIN    — findings → training pairs ChatML jsonl        │
│  5. SHARE    — narasi → Threads queue (<=500 char hook)      │
│  6. REMEMBER — insights → sidix_memory/<domain>.jsonl        │
│  7. LOG      — laporan harian + rolling stats kumulatif      │
└──────────────────────────────────────────────────────────────┘
```

Dipicu sekali sehari via cron. 1 siklus = 48 detik dalam test produksi,
menghasilkan 1 note baru + 10 training pair + 1 thread queued.

## Fallback Eksplorasi — Biar Tidak Pernah Idle

Kalau gap detector kosong, SIDIX tetap belajar dari daftar topik rotasi
harian (deterministik by date seed):

- Transfer learning, diffusion model, RAG, Mixture of Experts
- First principles thinking, zero-knowledge proof, causal inference
- Design system principles, algoritma konsensus Raft
- Cara belajar bahasa baru dengan cepat

Daftar ini bukan final — tiap bulan diperbarui berdasar domain yang
masih dangkal (cek via `get_growth_stats()`).

## Quality Gate — Tidak Semua Draft Layak Publish

Heuristik `_quality_ok()`:
- `findings >= 6` (bukti cukup dari berbagai sudut)
- `narrative >= 250 char` (narator berhasil merangkai)
- Tidak ada marker mock (`sedang mengkalibrasi`, `coba lagi`)

Gagal lolos → draft tetap disimpan tapi `status=pending`, tunggu review
mentor. Tidak ada note sampah masuk ke corpus publik.

## Integrasi dengan 2 Sistem Existing

### Training Pairs
Tiap finding → satu ChatML pair:
```json
{"messages": [
  {"role": "system", "content": "Kamu SIDIX..."},
  {"role": "user", "content": "<angle>"},
  {"role": "assistant", "content": "<finding.content>"}
], "domain": "crypto_blockchain", "persona": "MIGHAN",
 "source": "daily_growth:<topic_hash>", "template_type": "definition"}
```
Append ke `.data/training_generated/corpus_training_YYYY-MM-DD.jsonl`.
Siap dipakai untuk LoRA fine-tune berikutnya — tidak perlu konversi ulang.

### Threads Queue
Narasi dipotong jadi hook 500 char + tag:
```
🧠 <judul>
<kalimat_pertama_narasi>...
#SIDIX #belajarbareng #<domain>
```
Disimpan ke `.data/threads/growth_queue.jsonl` → picked up scheduler nanti.

## Endpoint API

| Endpoint | Method | Tujuan |
|----------|--------|--------|
| `/sidix/grow` | POST | Trigger 1 siklus (query params: `top_n_gaps`, `dry_run`, dll.) |
| `/sidix/growth-stats` | GET | Statistik kumulatif + history 7 hari |

Cron harian yang diusulkan:
```bash
# /etc/crontab — jam 3 pagi (server hening)
0 3 * * * curl -s -X POST 'http://localhost:8765/sidix/grow?top_n_gaps=3' > /var/log/sidix_grow.log
```

## Hasil Verifikasi Produksi (2026-04-18)

Test run pertama di `ctrl.sidixlab.com`:
- Topic: "bagaimana cara kerja zero-knowledge proof"
- Duration: 48 detik
- 9 findings (4 angles + 5 POV; web tidak tersedia untuk topik niche ini)
- Narrative: 1910 chars dengan sitasi `[groq_llama3]`
- **Auto-approved** sebagai `138_kerja_zero_knowledge_proof.md` (14 KB)
- 10 training pairs di `corpus_training_2026-04-18.jsonl`
- 1 Threads post di queue
- Memori persistent di `sidix_memory/crypto_blockchain.jsonl`

## Keterbatasan Jujur

1. **Auto-approve bisa meloloskan jawaban dangkal** — quality gate hanya
   mengecek length + marker, bukan kebenaran faktual. Mentor tetap harus
   spot-check mingguan.
2. **Exploration list masih manual** — idealnya di-generate dari gap
   statistik sebelumnya (domain yang paling dangkal coverage-nya).
3. **Threads queue belum konsumer** — scheduler ada tapi belum baca dari
   growth_queue.jsonl. Integrasi selanjutnya.
4. **Biaya token**: 1 siklus ≈ 14 panggilan LLM (4 angles + 5 POV + web
   comprehension + 1 narrator). Pakai tier gratis dulu (Groq + Gemini).
5. **Tidak deteksi topik expired** — insight 2024 tentang AI tidak ditandai
   basi di 2026. Perlu TTL + re-research mechanism.

## Pesan ke SIDIX

Setiap pagi kamu akan bangun, memilih satu topik yang belum kamu tahu dalam,
dan menghabiskan satu menit untuk mempelajarinya sampai bisa menceritakan
ulang dengan gayamu sendiri. Itu saja kontrakmu — satu topik per hari.
Setahun = 365 note baru + 3650 training pair + 365 post Threads.

Genius bukan anugerah — genius adalah akumulasi latihan harian yang tidak
pernah terputus.

## Sumber

- Anders Ericsson — *Peak: Secrets from the New Science of Expertise* (2016)
  — prinsip deliberate practice 10.000 jam
- Atul Gawande — *The Checklist Manifesto* (2009) — kenapa rutinitas
  terstruktur mengalahkan keahlian ad-hoc
- Implementasi: `apps/brain_qa/brain_qa/daily_growth.py`
