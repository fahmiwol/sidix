# SIDIX Autonomous Night Plan

**Date enabled**: 2026-04-26
**Trigger**: User vision — *"sambil saya tidur SIDIX bisa terus kerja dan belajar... membuat sendiri riset baru, melakukan iterasi baru, mencoba hal-hal baru, mengeksekusi note menjadi script yang fungsional"*

## What SIDIX Does Every 2 Hours (Autonomous)

Script: `/opt/sidix/scripts/sidix_autonomous_night.sh`
Cron: `0 */2 * * *` (00:00, 02:00, 04:00, ..., 22:00 UTC)

### Phase 1: Daily Growth Cycle (7-fase)

Calls `brain_qa.daily_growth.run_daily_growth()`:

1. **SCAN**: knowledge_gap_detector — identify top-3 gaps where SIDIX has low confidence
2. **RISET**: autonomous_researcher — fetch from open data sources (arXiv, Wikipedia, MusicBrainz, GitHub, Quran corpus, etc — 50+ sources via LearnAgent)
3. **APPROVE** (SAFE MODE): drafts queued ke `.data/queue/notes_pending/`, **not auto-approved** — user must review
4. **TRAIN**: generates training pairs (JSONL) untuk LoRA retrain (Kaggle/RunPod nightly)
5. **SHARE** (DISABLED): Threads auto-post off untuk safety
6. **REMEMBER**: append entry ke `growth_cycles.jsonl`
7. **LOG**: structured JSON ke `autonomous_log.jsonl`

### Phase 2: Knowledge Gap Snapshot

Capture top-10 current gaps untuk visibility tomorrow morning.

### Phase 3: Corpus Stats

Snapshot `corpus_doc_count`, `notes_count`, `last_ingested` untuk trend tracking.

### Phase 4: Cache + Embedding Stats

Health check semantic cache + BGE-M3 status.

### Phase 5: Pending Drafts Review Reminder

Count + identify oldest pending draft so user knows priority.

## Output Locations (User Reads in Morning)

```
/opt/sidix/.data/autonomous_log.jsonl     # Per-cycle structured log
/opt/sidix/.data/growth_cycles.jsonl      # daily_growth report per cycle
/opt/sidix/.data/queue/notes_pending/*.md # Drafts awaiting review
/opt/sidix/.data/training_pairs/*.jsonl   # New training data for LoRA
```

## Quick Morning Checklist

```bash
# After waking up:
ssh sidix-vps

# 1. See what SIDIX did overnight
tail -50 /opt/sidix/.data/autonomous_log.jsonl | jq -c '.event'

# 2. Count drafts to review
ls /opt/sidix/.data/queue/notes_pending/ | wc -l

# 3. Read latest drafts
ls -lt /opt/sidix/.data/queue/notes_pending/ | head -10

# 4. Approve good drafts (move to brain/public/research_notes/)
mv /opt/sidix/.data/queue/notes_pending/<note>.md /opt/sidix/brain/public/research_notes/

# 5. Re-trigger LoRA retrain if many new training pairs
ls /opt/sidix/.data/training_pairs/ | wc -l
```

## Safety Constraints (Why NOT Fully Auto-Approve)

User vision: SIDIX self-learn. Reality: untuk tahap MVP, manual approval gate prevents:

- **Hallucination drift**: bad drafts could poison corpus → poison LoRA → cascade
- **Spam**: unbounded research could exhaust storage / GPU budget
- **BadStyle attack** (Vol 19): malicious patterns get flagged but not auto-rejected
- **Public-facing drift**: auto-published Threads could leak unverified claims

Safer path: AUTO-DRAFT, MANUAL-APPROVE for first 2-4 weeks. After confidence calibrated, gradually increase auto-approve threshold per domain.

## Auto-Approve Roadmap (Future)

| Phase | Auto-approve threshold |
|---|---|
| Vol 21-22 (now) | Manual review for ALL drafts |
| Vol 23 | Auto-approve if sanad consensus ≥ 0.9 + no contradiction in inventory |
| Vol 24 | Auto-approve casual/factual; manual for fiqh/medis |
| Vol 25 | Auto-approve if multiple shadow agents agree (≥3 independent confirmation) |
| Vol 26+ | Trust score per domain — high-trust domains fully auto |

## What's Missing for "Real" Autonomy (Vol 22+)

Tonight's setup = corpus growth + research notes drafts. Real autonomy adds:
- **Self-modification**: SIDIX writes/edits own code (sandboxed, requires PR review by Claude/user)
- **Auto-deploy gate**: passing tests trigger pm2 restart automatically
- **Self-rollback**: failed deployments auto-revert to last-known-good
- **Auto-bench**: SIDIX runs eval suite, posts results to growth log
- **Resource self-management**: scale RunPod workers based on demand prediction

These = Vol 27+ effort. Tonight's MVP = corpus growth only.

## Related Documents

- `docs/STATE_OF_SIDIX_2026-04-26.md` — current snapshot
- `docs/ROADMAP_VOL21-30.md` — sprint plan
- `brain/public/research_notes/239_sanad_consensus_vol21_spec.md` — architecture
- `scripts/sidix_autonomous_night.sh` — the actual script

## Verify Script is Running

```bash
# On VPS:
crontab -l | grep autonomous_night
# Should show: 0 */2 * * * /opt/sidix/scripts/sidix_autonomous_night.sh

# Check logs after first cycle (within 2 hours of enable):
tail -20 /opt/sidix/.data/autonomous_log.jsonl

# Manual trigger for testing:
bash /opt/sidix/scripts/sidix_autonomous_night.sh
```

## Final Note

This makes SIDIX *literally* work while user sleeps. Corpus grows, gaps fill,
training data accumulates. By morning, user has new drafts to review + cleaner
knowledge state. Compound learning starts tonight.
