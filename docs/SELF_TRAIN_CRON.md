# Self-Train Fase 1 — Cron Documentation

## Weekly Corpus Curation

Jalankan automated corpus curation dan training data generation setiap minggu.

### Cron Schedule

```cron
# SIDIX Self-Train Fase 1 — weekly curation
0 3 * * 1 cd /opt/sidix && python scripts/corpus_to_training.py >> /var/log/sidix_training.log 2>&1
```

- **Schedule**: `0 3 * * 1` (Senin 03:00 UTC)
- **Script**: `scripts/corpus_to_training.py`
- **Output**: `brain/public/training_data/YYYY-MM-DD/corpus_pairs.jsonl`
- **Summary**: `brain/public/training_data/YYYY-MM-DD/_summary.json`
- **Log**: `/var/log/sidix_training.log`

### Minimum Target

- **100–300 pairs per week** dari corpus curation
- Threshold approval: **0.70**
- Threshold premium (untuk LoRA fine-tune): **0.85**

### Pipeline

1. Load corpus docs dari BM25 index + metadata
2. Score tiap dokumen:
   - relevance (BM25 percentile) × 25%
   - sanad_tier (T1=1.0, T2=0.8, T3=0.6, T4=0.3) × 20%
   - maqashid_score × 20%
   - dedupe_score × 15%
   - length_score × 10%
   - structure_score × 10%
3. Filter score ≥ 0.70 → approved pairs
4. Filter score ≥ 0.85 → premium pairs
5. Export ke JSONL instruction-tuning format

### Manual Trigger

```bash
# Via CLI
cd /opt/sidix && python scripts/corpus_to_training.py

# Via API (admin only)
curl -X POST https://ctrl.sidixlab.com/training/curate \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN" \
  -d '{"threshold": 0.70, "limit": 500}'
```

### Monitoring

- GET `/training/stats` — dashboard stats
- GET `/training/data/latest` — latest file info
