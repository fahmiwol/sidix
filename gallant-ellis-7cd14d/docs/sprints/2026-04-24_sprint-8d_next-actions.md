# Sprint 8d — Next Actions (2026-04-24)

**Status sebelumnya:** Sprint 8a ✅ · 8b ✅ · 8c ✅ · Merge ke main ✅ · Pushed ✅

---

## Deploy ke VPS (Manual — owner jalankan di server)

```bash
# Di VPS, masuk ke direktori project
cd /opt/sidix

# Pull latest main
git pull origin main

# Restart backend (brain_qa FastAPI)
pm2 restart sidix-brain

# Cek status
pm2 status
curl https://ctrl.sidixlab.com/health
```

Tidak perlu rebuild frontend — Sprint 8a/8b/8c adalah backend only.

---

## Sprint 8d — Prioritas (urut impact)

### 1. branch_manager.py — Multi-Tenant Agency (TINGGI)
**File:** `apps/brain_qa/brain_qa/branch_manager.py`

```python
@dataclass
class AgencyBranch:
    agency_id: str
    client_id: str
    persona: str
    corpus_filter: list[str]   # tag filter untuk RAG
    tool_whitelist: list[str]  # tools yang dibolehkan

class BranchManager:
    def get_branch(self, agency_id, client_id) -> AgencyBranch: ...
    def create_branch(self, ...) -> AgencyBranch: ...
    def list_branches(self, agency_id) -> list[AgencyBranch]: ...
```

Acceptance: request dengan `client_id` berbeda dapat corpus + tools yang berbeda.

---

### 2. Piper TTS — Install di VPS (TINGGI)

```bash
# Di VPS
pip install piper-tts
# Download voice model Indonesia
mkdir -p /opt/sidix/models/piper
cd /opt/sidix/models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/ariani/medium/id_ID-ariani-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/ariani/medium/id_ID-ariani-medium.onnx.json
```

Setelah install: TTS endpoint `POST /tts/synthesize` langsung aktif (bukan stub).

---

### 3. FLUX.1 — Opsi GPU (SEDANG)

Dua jalur:
- **A. Hybrid RunPod**: set `SIDIX_IMAGE_GEN_URL` ke RunPod endpoint (bayar per-jam)
- **B. Lokal GPU VPS**: upgrade VPS ke GPU node, install `diffusers torch`

Untuk sekarang: mock mode tetap berjalan, tidak blocking sprint lain.

---

### 4. PostgreSQL — Aktifkan DB Connection (SEDANG)

```bash
# Di VPS, set env var
echo "SIDIX_DB_URL=postgresql://user:pass@localhost:5432/sidix" >> /opt/sidix/apps/brain_qa/.env
pm2 restart sidix-brain
```

Schema sudah ada di `apps/brain_qa/brain_qa/db/schema.sql` — tinggal apply:
```bash
psql $SIDIX_DB_URL -f apps/brain_qa/brain_qa/db/schema.sql
```

---

### 5. Jariyah Pairs — Monitor & Export ke LoRA (SEDANG)

Setelah VPS di-deploy, training pairs akan terkumpul di `data/jariyah_pairs.jsonl`.
Ketika sudah 500+ pairs → export ke format LoRA JSONL → retrain adapter.

---

## Backlog (Sprint 9+)

- [ ] 3D pipeline: text_to_3d, image_to_3d, npc_generator (Research Note 184)
- [ ] sociometer (Sprint 7) — social media analytics agent
- [ ] Instagram scraping via Kimi Agent integration
- [ ] Tiranyx pilot — SIDIX Agency OS untuk client pertama
- [ ] PostgreSQL: migrate dari JSONL ke relational storage

---

## State Repo Saat Ini

Branch: `main` (sudah di-push, siap deploy)
Tests: 22 passed
Tools: 36 aktif
Endpoints baru: `/generate/image`, `/tts/synthesize`
