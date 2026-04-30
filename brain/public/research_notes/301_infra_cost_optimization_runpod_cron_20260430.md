---
title: Infra Cost Optimization — RunPod Tuning + Cron Diet
date: 2026-04-30
sprint: Sigma-4 Infra (Pre-Streaming)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: RunPod console screenshots + crontab -l VPS audit + memory/project_runpod_infra_state.md
---

# 301 — Infra Cost Optimization: RunPod + Cron Diet

## Konteks

Setelah Sigma-3 deploy, founder share RunPod console screenshot: 4 workers terdeploy (1 running + 1 idle + 2 initializing dengan tag "Extra"), balance $16.77 turun dari ~$24 dalam 3 hari.

Founder concern: *"saya udah terminate tapi ada lagi ada lagi"* — workers terus spawn meski di-terminate manual.

## Root Cause Analysis

### 1. RunPod default config terlalu permissive
- Max Workers = 3 (atau lebih) → unlimited spawn saat traffic tinggi
- Active Workers default → keep workers running terus
- FlashBoot mungkin OFF → cold-start 60-120s tiap spawn

### 2. Traffic source dari VPS sangat agresif
Audit `crontab -l` sidix-vps menemukan **8+ cron jobs high-frequency** yang panggil brain endpoint:

| Cron | Frekuensi | Calls/jam |
|---|---|---|
| `sidix_always_on.sh` | 15min | 4 |
| `sidix_worker.sh` | 15min | 4 |
| `sidix_aku_ingestor.sh` | 15min | 4 |
| `sidix_radar.sh` | 30min | 2 |
| `sidix_autodev_tick.sh` | 30min | 2 |
| `sidix_classroom.sh` | 1 hour | 1 |
| `dummy_agents.py` (jariyah) | 2x/day × 3 rounds | dispersed |

Total: **~17 calls/jam dari cron alone**. Setiap call panggil `_compose_final_answer` → `hybrid_generate` → RunPod inference → spawn worker.

### 3. Jariyah cron sudah counterproductive
`dummy_agents.py` awalnya didesain untuk **paksa brain warm** dengan dummy traffic. Setelah FlashBoot enabled (cold-start 2s), dummy jariyah jadi pure waste cost.

## Solusi Dua-Sisi

### Sisi A: RunPod Config (founder action)

| Setting | Old | New | Efek |
|---|---|---|---|
| Max Workers | 3 | **1** | Tidak ada extras |
| Active Workers | 1+ | **0** | Idle = $0 cost (scale-to-zero) |
| GPU count | 1 | 1 | OK |
| Idle timeout | default | **60s** | Cepat scale-down |
| Execution timeout | none | 600s | Cap runaway gen |
| **FlashBoot** | OFF | **ON** | **Cold-start 60-120s → 2s** |

FlashBoot adalah game-changer paling penting. Bridge antara "cost rendah saat idle" dengan "responsif saat traffic". Tanpa FlashBoot, scale-to-zero = 60s+ first-byte latency = unusable UX.

### Sisi B: Cron Diet (Claude action via SSH)

7 cron PAUSED via comment-out marker `# [SIGMA3-PAUSE 2026-04-30]`:
1. `*/15 * * * * sidix_always_on.sh` — observation loop, low yield
2. `4,19,34,49 * * * * sidix_worker.sh` — autonomous worker (queue empty)
3. `9,24,39,54 * * * * sidix_aku_ingestor.sh` — AKU ingest (bisa daily aja)
4. `7,37 * * * * sidix_radar.sh` — trend detection (bisa daily aja)
5. `*/30 * * * * sidix_autodev_tick.sh` — autonomous developer (queue empty)
6. `0 2 * * * dummy_agents.py` — jariyah dummy (counterproductive after FlashBoot)
7. `0 14 * * * dummy_agents.py` — jariyah dummy (counterproductive after FlashBoot)

6 cron tetap ACTIVE (foundational growth — DNA SIDIX):
1. `0 3 * * * /sidix/grow?top_n_gaps=3` — knowledge gap detector
2. `0 4 * * * /learn/run` — LearnAgent fetch corpus
3. `30 4 * * * /learn/process_queue` — process corpus baru
4. `30 5 * * MON /creative/prompt_optimize/all` — weekly optimizer
5. `0 4,9,14,19 * * * /agent/synthetic/batch n=5` — training signal generator
6. `0 23 * * * /agent/odoa` — daily reflection

Backup: `/opt/sidix/.data/crontab_backup_20260430_132013.txt`

## Cost Projection

### Pre-optimization (estimasi)
- Cron traffic: 17 calls/jam × 24h = 408 calls/hari
- Active workers terus jalan (cron tiap 15 min trigger spawn)
- FlashBoot OFF → setiap idle-spin-up = 60-120s GPU billable
- Estimated: $3-5/hari burn = balance habis dalam ~4-7 hari

### Post-optimization
- Cron traffic: 6 calls/HARI (mostly daily/weekly)
- Active = 0, Idle timeout 60s → workers scale to 0 saat tidak ada traffic
- FlashBoot ON → cold-start 2s (negligible cost)
- Estimated: <$1/hari burn = balance $16.77 tahan ~17-30 hari

## Pelajaran (Pendekatan Pikir Bos × Asisten)

### 1. Cron design: "DNA vs Lemak"

**DNA cron** = bikin SIDIX TUMBUH (corpus growth, training signal, reflection). Ini investasi compound, tidak boleh dimatikan walau biaya.

**Lemak cron** = bikin SIDIX SIBUK tanpa hasil compound (observation loops, dummy traffic, queue checks pada queue kosong). Ini operating overhead yang harus minimum.

Anti-pattern: high-frequency observation/queue-check cron pada queue yang biasanya kosong = expensive null operation.

### 2. FlashBoot mengubah optimasi

Sebelum FlashBoot: rational design = "keep workers warm dengan dummy traffic".
Setelah FlashBoot: rational design = "scale to zero, FlashBoot handle cold-start".

Setiap kali ada feature baru di infra layer, RE-AUDIT desain yang lama. Pattern yang dulu optimal bisa jadi anti-pattern sekarang.

### 3. Trust-based delegation

Founder bilang: *"saya nggak tau, ngggak ngerti... kamu pikirin sebagai asisten saya"*. Ini moment untuk bertanggung jawab penuh atas keputusan teknikal — bukan minta-minta approval untuk setiap baris.

Kontrak: aku ambil keputusan + jelaskan reasoning + reversible (cron di-COMMENT bukan delete). Founder tahu pattern, bisa correct nanti kalau salah.

## Verification Plan (Next Session)

1. Cek balance RunPod 24 jam dari sekarang — expected drop rate ~$1/hari (vs $3-5/hari sebelumnya).
2. Cek pm2 logs untuk confirm tidak ada `[RunPod] empty/unparseable response: IN_QUEUE` (FlashBoot harusnya eliminate ini).
3. Run goldset re-test — expected complete dalam ~20 menit (bukan stuck di Q6 kemarin).
4. Verify cron yang paused tidak break anything — check logs di `/var/log/sidix/*.log`.

## Sigma-4 Real Plan (Updated)

Sigma-4A streaming SSE — DEFER ke sesi berikutnya. Reason: dengan FlashBoot 2s + token gen ~150s untuk 600 tokens, perceived first-byte latency masih bisa diterima tanpa streaming. Streaming jadi nice-to-have bukan must-have.

New Sigma-4 priority:
1. **4-1**: Verify cost stabilization (pasif, 24 jam wait)
2. **4-2**: Re-run 25Q goldset untuk validate Sigma-3 changes (target 22-23/25 = 88-92%)
3. **4-3**: (jika cost OK) re-enable selective cron — `sidix_classroom.sh` dengan freq dikurangi (1 hour → 4 jam)
4. **4-4**: Streaming SSE (sekarang lower priority)

## Referensi
- deploy-scripts/warmup_runpod_v2.sh — real inference warmup (alternative kalau Active=0 tidak cukup)
- VPS crontab backup: /opt/sidix/.data/crontab_backup_20260430_132013.txt
- Memory: project_runpod_infra_state.md (dari 2026-04-27)
- Research note 299 — production review yang trigger Sigma-3
- Research note 300 — Sigma-3 implementation
