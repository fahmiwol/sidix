---
id: 181
title: Sprint 6 — Flywheel L1 Aktif + Signature Fix + Cron Optimizer
tags: [sprint6, flywheel, prompt_optimizer, brand_builder, content_planner, cron, self-evolution]
date: 2026-04-21
---

# Sprint 6 — Flywheel L1 Aktif + Signature Fix + Cron Optimizer

**[FACT]** — Sumber: kode Sprint 5-6 (`muhasabah_loop.py`, `prompt_optimizer.py`, `brand_builder.py`, `content_planner.py`, `agent_serve.py`).

---

## Apa yang Diimplementasikan

### 1. Flywheel L1 Aktif — `muhasabah_loop.py`

**Sebelumnya**: `run_muhasabah_loop()` menjalankan quality gate dan mereturn `passed: True` tapi tidak memberi tahu `prompt_optimizer` bahwa ada output yang bagus.

**Sesudahnya**: saat `gate["total"] >= min_score` (default 7.0), loop otomatis memanggil `log_accepted_output()` sebelum return:

```python
if gate["total"] >= float(min_score):
    try:
        from .prompt_optimizer import log_accepted_output
        log_accepted_output(
            agent=domain,
            prompt_params={"brief": brief},
            output_text=current,
            score=gate["total"],
            domain=domain,
        )
    except Exception:
        pass  # non-blocking
    return {"ok": True, "passed": True, ...}
```

**Kenapa penting**: `prompt_optimizer.py` (Sprint 5) sudah siap belajar dari accepted outputs yang dikumpulkan di `.data/accepted_outputs.jsonl`, tapi selama ini tidak ada yang mengisinya secara otomatis. Dengan patch ini, setiap output yang lolos muhasabah langsung masuk ke log → setelah 20 accepted outputs terkumpul, `optimize_prompt()` bisa dijalankan dan membuat prompt template yang lebih baik.

**Arsitektur flywheel**:
```
generate_fn(brief)
  → quality_gate() ← CQF scoring
  → [jika skor ≥ 7.0] log_accepted_output()  ← BARU
  → .data/accepted_outputs.jsonl              ← feed
  → optimize_prompt() (cron Senin 04:00 UTC) ← belajar
  → template baru → generate_fn lebih pintar ← loop
```

---

### 2. Signature Fix — `target_audience` Parameter

**Problem**: Sprint 4 membangun `generate_brand_kit()` dan `generate_content_plan()` tanpa parameter `target_audience`. Tapi `prompt_optimizer._BASE_PROMPTS` menyertakan `{target_audience}` di template `brand_builder` dan `content_planner`. Saat optimizer mencoba evaluasi template baru dengan params nyata dari pipeline, ini menyebabkan `KeyError: 'target_audience'`.

**Fix**:

| File | Perubahan |
|------|-----------|
| `brand_builder.py` | Tambah `target_audience: str = ""` → default `audiens {niche} Indonesia` |
| `content_planner.py` | Tambah `target_audience: str = ""` → default `audiens {niche} Indonesia` |
| `agent_tools.py` | `_tool_generate_brand_kit` pass `target_audience` dari args |
| `agent_tools.py` | `_tool_generate_content_plan` pass `target_audience` dari args |
| `agent_tools.py` | ToolSpec params diupdate untuk kedua tool |

**Backward compatible**: parameter opsional dengan default yang sensible → caller lama tidak perlu diubah.

---

### 3. Cron Weekly Endpoint — `agent_serve.py`

Tiga endpoint baru di bawah tag `Creative`:

| Endpoint | Method | Auth | Fungsi |
|----------|--------|------|--------|
| `/creative/prompt_optimize/all` | POST | Admin | Jalankan `optimize_all_agents()` — cocok untuk cron |
| `/creative/prompt_optimize/{agent}` | POST | Admin | Optimalkan satu agent spesifik |
| `/creative/prompt_optimize/stats` | GET | Public | Baca statistik run terakhir |

**Cron setup di VPS**:
```cron
# Senin 04:00 UTC — weekly prompt optimization
0 4 * * MON curl -s -X POST https://ctrl.sidixlab.com/creative/prompt_optimize/all \
  -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN" >> /var/log/sidix/prompt_optimize.log 2>&1
```

---

## Kenapa Urutan Ini Benar

1. **Flywheel tidak ada artinya tanpa data** — patch muhasabah_loop mengisi `.data/accepted_outputs.jsonl` secara otomatis dari production traffic.
2. **Optimizer tidak bisa belajar dengan parameter salah** — signature fix mencegah `KeyError` saat evaluasi template baru.
3. **Cron endpoint menyambungkan loop** — data terkumpul selama seminggu → Senin optimizer jalan → template baru aktif → output minggu depan lebih baik.

---

## Keterbatasan

- `min_score = 7.0` di muhasabah_loop adalah hardcoded threshold. Jika `MIN_SAMPLES_TO_OPTIMIZE = 20` belum tercapai, optimizer belum jalan (perlu `force=True` di endpoint).
- `prompt_params` yang dicatat hanya `{"brief": brief}` — belum capture semua parameter domain-specific (topic, channel, dll). Sprint 7 bisa extend schema ini.
- Cron endpoint memerlukan `BRAIN_QA_ADMIN_TOKEN` di env VPS. Tanpa ini endpoint return 403.
