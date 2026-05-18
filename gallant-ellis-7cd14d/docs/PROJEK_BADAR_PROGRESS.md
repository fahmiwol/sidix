# Projek Badar — kemajuan batch

**Kontrak tujuan:** batch A, B, dan C bersama-sama harus mendekatkan produk ke **G1–G5** dan etos **Al-Amin** — lihat `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md` (peta goal ↔ bukti, definisi selesai, koordinasi antar-agen).

| Batch | File | Jumlah | Catatan |
|-------|------|--------|---------|
| A (Cursor) | `docs/PROJEK_BADAR_BATCH_CURSOR_50.md` | 50 | # kerja 1–50 |
| B (Claude) | `docs/PROJEK_BADAR_BATCH_CLAUDE_54.md` | 54 | # kerja 51–104 |
| C (sisa) | `docs/PROJEK_BADAR_BATCH_SISA_10.md` | 10 | # kerja 105–114 |

**Aturan:** centang `[x]` hanya setelah ada artefak + entri `docs/LIVING_LOG.md` (boleh ringkas per klaster tugas).

## Batch A — Cursor (# kerja 1–50)

Gunakan tabel di `PROJEK_BADAR_BATCH_CURSOR_50.md` sebagai sumber kebenaran.

- [x] **G1 cluster (#1–27)** — QA endpoint, fallback web Wikipedia, rantai simpulan berlabel, rate limit, korpus RAG reindex, multi-turn sesi, prompt injection guard, sanad UI, bahasa natural detect, kartu "tidak tahu", export JSON PII-redacted, FAQ statis, ringkas berita web, deteksi ujaran kejam, mode corpus-only, feedback 👍/👎. Lihat `LIVING_LOG` 2026-04-15 s.d. 2026-04-17.
  - **Baru (2026-04-17)**: Task 17 `label_answer_type()` fakta/opini/spekulasi — `g1_policy.py`. Task 22 `resolve_style_persona()` pembimbing/faktual — `persona.py`. Task 26 `resolve_output_language()` multibahasa — `g1_policy.py`. Task 27 `aggregate_confidence_score()` numerik — `g1_policy.py` + `agent_react.py`.
- [x] **G5 cluster (#28–50)** — golden set + eval, observabilitas trace ID, versi model + hash di /health, quota harian anon. Docs: profil inferensi, release checklist, runbook insiden, DR, restore backup, calibration guide (semua di `docs/`).
  - **Baru (2026-04-17)**: Task 36 pin model version `docker-compose.example.yml`. Task 40 `/agent/canary` + `/agent/canary/activate` — `agent_serve.py`. Task 49 security headers middleware — `agent_serve.py`. Task 50 `/agent/bluegreen` + `/agent/bluegreen/switch` — `agent_serve.py`. Scripts: `benchmark_latency.py`, `ablation_prompts.py`, `load_test.py`, `disk_alarm.py`, `log_rotation.py`, `synthetic_monitor.py`, `profile_request.py`. Module: `token_cost.py`.

## Batch B — Claude (# kerja 51–104)

- [x] **G4 cluster (#51–71)** — 21 tugas tooling: gen_script, mini-app template, linter+pre-commit, snippet coding, CLI backup/export/gpu-status, scaffold API, mock LLM, docker inference package, env validator, lint-docs, git-tag, lockfile check, seed demo, migrate-rag, contoh plugin. Lihat `LIVING_LOG` 2026-04-17.
- [x] **G2 cluster (#72–93)** — 22 tugas image gen pipeline: text-to-image API + antrian, preset visual, NSFW filter, LoRA adapter, batch render, thumbnail, prompt A/B, watermark, color grading, img2img, policy validator, resolusi max, style transfer, seed reproducible, gallery, rate limit job, HDR, tile tekstur, inpainting stub, poster layout, sticker pack, line art. Lihat `LIVING_LOG` 2026-04-17.
- [x] **G3 cluster (#94–104)** — 11 tugas vision: caption/OCR upload, klasifikasi gambar, endpoint vision (resize/normalize), similarity gambar-teks, bounding box, deteksi wajah/objek, table extract, flowchart OCR, side-by-side analisis, confidence display, low-light detect. Lihat `LIVING_LOG` 2026-04-17.

## Batch C — sisa (# kerja 105–114)

- [x] **G3 cluster (#105–114)** — 10 tugas vision lanjutan: icon/logo detect, PDF caption pipeline, pose estimation, image compare, sketch-to-svg, chart reader, image quality score, slide reader, street sign OCR, screenshot detect. Lihat `LIVING_LOG` 2026-04-17.

---

**Status keseluruhan: 114/114 tugas punya artefak di repo.**
G1 ✅ G2 ✅ G3 ✅ G4 ✅ G5 ✅ — North Star Al-Amin tercapai di level artefak.
Aktivasi penuh (GPU inference, OCR nyata) mengikuti roadmap setelah Kaggle fine-tune selesai.
