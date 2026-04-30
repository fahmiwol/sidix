# Closed-Loop Learning — Feedback User sebagai Data Training SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Visi

Setiap interaksi user dengan SIDIX adalah peluang belajar.
Bukan hanya "laporan masalah" — tapi **sinyal untuk evolusi sistem**.

```
User pakai SIDIX
    ↓
User kirim feedback (bug / saran / fitur)
    ↓
Tersimpan di Supabase (feedback table)
    ↓
Admin review di ctrl.sidixlab.com
    ↓
Feedback berkualitas → dikonversi ke:
    ├── Research note baru (knowledge gap)
    ├── Bug fix (kode diperbaiki)
    ├── Feature ticket (roadmap)
    └── QA pair (data fine-tuning)
    ↓
Commit ke repo → brain_qa re-index
    ↓
SIDIX lebih pintar
    ↓
User pakai SIDIX (loop ulang)
```

---

## Tipe Feedback dan Cara Pengolahannya

### 🐛 Bug
**Input:** "SIDIX jawab salah tentang X"
**Proses:**
1. Cek corpus — apakah ada dokumen tentang X?
2. Kalau tidak ada → tulis research note tentang X
3. Kalau ada tapi salah → perbaiki dokumen
4. Re-index → SIDIX sekarang jawab benar

### 💡 Saran
**Input:** "Alangkah bagusnya kalau SIDIX bisa Y"
**Proses:**
1. Apakah Y adalah knowledge gap? → tambah ke corpus
2. Apakah Y adalah fitur UI? → tambah ke backlog frontend
3. Apakah Y adalah kemampuan reasoning? → catat di roadmap model

### ✨ Fitur
**Input:** "Saya mau SIDIX bisa Z"
**Proses:**
1. Evaluasi: apakah Z bisa diselesaikan dengan corpus saja?
2. Apakah Z butuh tool baru?
3. Apakah Z butuh persona baru?
4. Apakah Z butuh fine-tuning?

---

## Arsitektur Data Flow

```
[Supabase: feedback table]
    ↓ (nightly atau on-demand)
[Script: export_feedback.py]
    ↓
[brain/public/feedback_learning/YYYY-MM-DD_tipe_slug.md]
    ↓
[brain_qa: python3 -m brain_qa index]
    ↓
[SIDIX corpus: feedback terindeks]
    ↓
[SIDIX bisa menjawab: "Apa yang paling sering diminta user?"]
```

---

## Format File Feedback yang Dikonversi

```markdown
# Feedback #[id] — [tipe]: [ringkasan]

**Tipe:** bug | saran | fitur
**Tanggal:** YYYY-MM-DD
**Status:** reviewed | incorporated

## Isi Feedback
[pesan asli dari user]

## Analisis
[apa yang diminta, apa yang perlu diubah]

## Tindakan yang Diambil
[research note baru / bug fix / fitur ditambah / tidak diambil + alasan]
```

---

## Script Export Feedback (direncanakan)

```python
# tools/export_feedback.py
# Fetch feedback dari Supabase, konversi ke corpus files

import os
import json
from supabase import create_client
from datetime import datetime
from pathlib import Path

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SECRET_KEY"]  # service key — backend only

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def export_approved_feedback():
    result = supabase.table("feedback") \
        .select("*") \
        .eq("status", "in_progress") \
        .execute()

    for fb in result.data:
        slug = fb["message"][:40].lower().replace(" ", "_").replace("?", "")
        filename = f"{fb['created_at'][:10]}_{fb['type']}_{slug}.md"
        path = Path("brain/public/feedback_learning") / filename

        content = f"""# Feedback: {fb['type'].title()} — {fb['message'][:60]}

**Tipe:** {fb['type']}
**Tanggal:** {fb['created_at'][:10]}
**ID:** {fb['id']}

## Isi Feedback
{fb['message']}

## Status
{fb['status']}
"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✓ Exported: {filename}")

if __name__ == "__main__":
    export_approved_feedback()
    print("Re-index...")
    os.system("python3 -m brain_qa index")
```

---

## Admin Workflow di ctrl.sidixlab.com (roadmap)

```
Admin buka ctrl.sidixlab.com → Feedback Panel
    │
    ├── Tab: Open (belum direview)
    │     → Lihat semua feedback baru
    │     → Klik "Review"
    │
    ├── Tab: In Progress (sedang diproses)
    │     → Tandai: "Jadikan research note"
    │     → Tandai: "Masukkan ke training data"
    │     → Tandai: "Tidak relevan" (tutup)
    │
    └── Tab: Closed (selesai)
          → Archive
```

---

## Implikasi Jangka Panjang: SIDIX yang Self-Improving

### Siklus pendek (sekarang, manual):
```
Feedback → Admin review → Manual tulis research note → Commit → Re-index
```

### Siklus menengah (3-6 bulan):
```
Feedback → Script klasifikasi → Semi-auto generate note → Admin approve → Commit → Re-index
```

### Siklus panjang (visi):
```
Feedback → SIDIX analisis sendiri → Identifikasi knowledge gap → 
Generate note draft → Admin approve → Fine-tune adapter → 
SIDIX lebih akurat
```

---

## Hubungan dengan Arsitektur Epistemic SIDIX

Dalam framework IHOS (Integrative Holistic Ontological System):
- **Nazhar** (observasi) = user kirim feedback → SIDIX mengamati kebutuhan nyata
- **Amal** (tindakan) = feedback diproses → corpus diperbarui
- **Ishlah** (perbaikan berkelanjutan) = loop ini tidak berhenti — selalu ada feedback baru

Feedback bukan gangguan. Feedback adalah **mekanisme koreksi diri** sistem.
Tanpa feedback loop, sistem berkembang dalam kekosongan, terputus dari realitas user.
