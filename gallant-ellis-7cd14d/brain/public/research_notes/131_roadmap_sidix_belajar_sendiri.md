# 131 — Roadmap: SIDIX Belajar Sendiri (Self-Learning Architecture)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Kondisi Sekarang — Audit Jujur (2026-04-18)

```
Research Notes:   124 notes di corpus
Python Modules:    75 modul aktif
Notes → Modules:  74 notes pernah diconvert, tapi hanya 7 skills ekstrak
                  Notes 82-130 BELUM diconvert
                  Converter heuristik terlalu konservatif

Multi-LLM:        ✅ Ollama + Groq + Gemini + Anthropic semua online
Identity Shield:  ✅ 3-lapis deployed
Waiting Room:     ✅ deployed
LoRA adapter:     ⏳ Kaggle trained, belum deploy ke VPS
Self-learning:    ⚠️  Pipeline ada tapi belum tersambung end-to-end
```

**Kesimpulan audit:**
- Infrastruktur SUDAH ADA (75 modul!)
- Yang kurang: **koneksi** antar bagian + **aktivasi** pipeline yang sudah dibuat
- SIDIX saat ini belajar dari corpus PASIF — dia membaca, tapi belum bisa menulis sendiri

---

## Visi: SIDIX yang Belajar Sendiri

```
Sekarang (Pasif):
  Fahmi/Claude → research notes → corpus → SIDIX membaca

Target (Aktif):
  SIDIX encounter pertanyaan yang tidak bisa dijawab
    ↓
  SIDIX deteksi: "ini gap pengetahuan"
    ↓
  SIDIX riset sendiri (ReAct agent + web search)
    ↓
  SIDIX tulis draft research note
    ↓
  Fahmi review (1 klik approve/reject)
    ↓
  Note masuk corpus → SIDIX makin pintar
    ↓
  QnA quality → trigger LoRA fine-tuning otomatis
```

Ini adalah **flywheel**: semakin banyak interaksi → semakin banyak belajar → semakin baik → semakin banyak interaksi.

---

## Roadmap 6 Fase

### FASE 0: Sekarang — Foundation ✅ DONE
```
✅ 124 research notes di corpus
✅ BM25 RAG retrieval
✅ Multi-LLM routing (Ollama→Groq→Gemini→Anthropic)
✅ QnA recorder (setiap jawaban → training data)
✅ Identity Shield (3 lapis)
✅ Waiting Room (zero-API user retention)
✅ 75 Python modules (curriculum, skill_library, experience_engine, dll)
✅ notes_to_modules.py (converter ada, perlu dijalankan + diperbaiki)
```

---

### FASE 1: Aktivasi — 2 Minggu ke Depan
**Tujuan: Konversi semua 124 notes → skills + curriculum aktif**

```
Task 1.1: Jalankan notes_to_modules untuk notes 82-130
  → python3 -c "from brain_qa.notes_to_modules import convert_all; convert_all()"
  → Cek hasil: berapa skills yang diextract?

Task 1.2: Perbaiki heuristic converter
  → Masalah: 74 notes hanya hasilkan 7 skills (terlalu sedikit)
  → Fix: perluas pattern matching untuk note 109-130 yang formatnya berbeda
  → Target: minimal 3-5 skills per note

Task 1.3: Wire curriculum ke ask flow
  → Saat user bertanya → cek curriculum level user
  → Adjust kedalaman jawaban berdasarkan level
  → Track progress: topik apa yang sudah dicakup per user

Task 1.4: Deploy LoRA adapter dari Kaggle
  → Download model dari Kaggle
  → Test di VPS: sidix-lora:latest sudah ada di Ollama
  → Verifikasi: /llm/status → ollama available: true (sudah!)
```

**Output Fase 1:**
SIDIX punya skill library aktif dari 124 notes. Setiap pertanyaan user →
SIDIX cek skill library → jawaban lebih terstruktur dan kurikulum-aware.

---

### FASE 2: Self-Awareness — 2-4 Minggu
**Tujuan: SIDIX tahu apa yang dia tidak tahu**

```
Komponen yang dibutuhkan:

2.1 Confidence Scorer
  → Setiap jawaban SIDIX diberi skor 0-1
  → Skor rendah (<0.4): tandai sebagai "knowledge gap"
  → Simpan ke: .data/knowledge_gaps/gaps.jsonl

2.2 Gap Registry
  → Kumpulkan semua gaps
  → Kelompokkan per domain
  → Prioritas: berapa kali topic ini muncul?

2.3 Gap Dashboard (admin endpoint)
  → GET /gaps → list topik yang sering SIDIX tidak bisa jawab
  → Fahmi bisa lihat dan prioritaskan mana yang perlu di-fill

Implementasi:
  File baru: apps/brain_qa/brain_qa/knowledge_gap_detector.py
  Endpoint:  GET /gaps, POST /gaps/{gap_id}/resolve
```

**Output Fase 2:**
SIDIX tidak lagi menjawab "tidak tahu" tanpa trace.
Setiap ketidaktahuan tercatat → jadi input untuk belajar.

---

### FASE 3: Autonomous Research — 1-2 Bulan
**Tujuan: SIDIX bisa riset sendiri dan tulis draft notes**

```
Komponen:

3.1 Research Trigger
  → Gap yang muncul >3 kali → trigger auto-research
  → SIDIX pakai ReAct agent + webfetch untuk cari informasi
  → Simpan raw hasil ke .data/research_drafts/

3.2 Note Drafter
  → Dari raw research → generate draft research note (format markdown)
  → Pakai template yang sudah ada (format note 1-130)
  → Simpan sebagai draft, belum masuk corpus

3.3 Human Review Gate
  → Endpoint: GET /drafts → list draft notes menunggu review
  → POST /drafts/{id}/approve → masuk corpus
  → POST /drafts/{id}/reject → tandai + simpan kenapa
  → SIDIX belajar dari reject: "topik ini tidak sesuai standar karena..."

Implementasi:
  File baru: apps/brain_qa/brain_qa/autonomous_researcher.py
  File baru: apps/brain_qa/brain_qa/note_drafter.py
  Endpoints: /drafts, /drafts/{id}/approve, /drafts/{id}/reject
```

**Output Fase 3:**
Fahmi tidak perlu menulis semua notes sendiri.
SIDIX generate draft → Fahmi hanya approve/reject.
Perbandingan kerja: dari 100% Fahmi → 20% Fahmi, 80% SIDIX.

---

### FASE 4: Self-Training — 2-3 Bulan
**Tujuan: LoRA fine-tuning otomatis dari QnA berkualitas**

```
Komponen:

4.1 QnA Quality Filter
  → Dari qna_recorder, filter QnA berkualitas (quality >= 3)
  → Threshold: minimal 500 pasang QnA sebelum trigger fine-tune
  → Format: JSONL sesuai format LoRA training (lihat note 75)

4.2 Fine-tune Trigger
  → Cron job mingguan: cek jumlah QnA baru
  → Jika cukup → upload ke Kaggle → trigger training notebook
  → Atau (lebih sederhana): generate dataset → notifikasi Fahmi

4.3 Adapter Versioning
  → Setiap fine-tune = versi baru adapter (v1, v2, v3, ...)
  → A/B test: sebagian traffic ke versi lama, sebagian ke baru
  → Pilih yang lebih baik berdasarkan user satisfaction

Implementasi:
  File baru: apps/brain_qa/brain_qa/auto_finetune.py
  Integration: qna_recorder.py → check threshold → trigger
```

**Output Fase 4:**
SIDIX belajar dari percakapannya sendiri.
Setiap 2-4 minggu → versi SIDIX yang lebih baik.
Tanpa GPU lokal → pakai Kaggle (gratis, sudah terbukti di note 75).

---

### FASE 5: Teaching Autonomy — 3-6 Bulan
**Tujuan: SIDIX membangun kurikulum personal untuk setiap user**

```
Komponen:

5.1 User Learning Profile
  → Track: topik apa yang user sudah tahu
  → Track: level user (L0-L4 dari curriculum.py)
  → Track: cara belajar user (prefer detail atau ringkas? suka contoh atau teori?)
  → Simpan di: Supabase users table

5.2 Adaptive Curriculum
  → Berdasarkan profile → SIDIX menyesuaikan urutan dan kedalaman
  → "Kamu sudah paham X, sekarang coba Y" (proactive suggestion)
  → Tidak hanya menjawab — tapi membimbing jalur belajar

5.3 Teaching Session
  → User bisa minta "ajari saya X dari awal"
  → SIDIX buat mini-lesson: konsep → contoh → latihan → evaluasi
  → Ingat progress antar sesi (via memory.py yang sudah ada)

Implementasi:
  File: apps/brain_qa/brain_qa/user_learning_profile.py (baru)
  File: apps/brain_qa/brain_qa/curriculum.py (perluas yang ada)
  File: apps/brain_qa/brain_qa/teaching_session.py (baru)
```

**Output Fase 5:**
SIDIX bukan lagi search engine.
SIDIX adalah **tutor personal** yang tahu kamu, tahu dimana kamu sekarang,
dan tahu kemana kamu harus pergi selanjutnya.

---

### FASE 6: Ekosistem — 6-12 Bulan
**Tujuan: SIDIX mengajari SIDIX lain (distributed learning)**

```
Ini adalah visi Hafidz dari note 22 + 106:
  Satu node SIDIX belajar sesuatu
    ↓
  Knowledge di-broadcast ke node lain (Merkle-verified)
    ↓
  Semua SIDIX di jaringan jadi lebih pintar bersama

Komponen:
  - Peer-to-peer knowledge sharing antar VPS
  - Reputation system (siapa yang bisa dipercaya?)
  - Federated learning (train tanpa share raw data)
```

---

## Peta Dependensi: Mana yang Harus Duluan?

```
Fase 1 (Aktivasi)
  │
  ├─→ Fase 2 (Self-Awareness) ← BLOCKER untuk semua fase berikutnya
  │                              SIDIX harus tahu gap-nya sebelum bisa mengisi
  │
  ├─→ Fase 3 (Research) ← butuh Fase 2 selesai (tahu apa yang mau diriset)
  │
  ├─→ Fase 4 (Self-Training) ← butuh QnA berkualitas yang cukup (Fase 1+2)
  │
  ├─→ Fase 5 (Teaching) ← butuh Fase 3+4 (SIDIX harus pintar sebelum bisa ngajar)
  │
  └─→ Fase 6 (Ekosistem) ← butuh semua fase sebelumnya
```

**Prioritas sekarang: Fase 1 + mulai Fase 2**

---

## Apa yang Perlu Dibangun Berikutnya (Concrete Next Steps)

```
[MINGGU INI]
□ Jalankan notes_to_modules untuk notes baru (82-130)
□ Perbaiki heuristic converter (lebih banyak patterns)
□ Deploy research note 131 ini ke corpus

[MINGGU DEPAN]
□ Buat knowledge_gap_detector.py
□ Wire ke /ask/stream: setiap jawaban → confidence score → log gap
□ Buat admin endpoint GET /gaps

[BULAN INI]
□ Buat autonomous_researcher.py (ReAct + webfetch → draft note)
□ Buat review UI sederhana untuk Fahmi approve/reject draft
□ Wire curriculum ke ask flow (adaptive response depth)

[3 BULAN]
□ auto_finetune.py: QnA threshold → generate training set → notify Fahmi
□ user_learning_profile.py: track user level per domain
□ teaching_session.py: mini-lesson mode
```

---

## Insight Terpenting

**Masalah sebenarnya bukan teknis — masalahnya adalah koneksi.**

Semua building blocks sudah ada:
- curriculum.py → ada
- skill_library.py → ada
- notes_to_modules.py → ada
- experience_engine.py → ada
- permanent_learning.py → ada
- qna_recorder.py → ada
- agent_react.py → ada (ReAct engine)

Yang belum: **semua ini belum tersambung dalam satu learning loop**.

Ini seperti punya semua bahan bangunan rumah tapi belum dipasang.
Tugas berikutnya bukan membeli material — tapi membangun.

---

## Filosofi Akhir

> SIDIX yang bisa belajar sendiri bukan tujuan akhir.
> Tujuan akhirnya adalah SIDIX yang bisa **mengajari orang lain belajar sendiri**.
>
> Kalau SIDIX bisa otodidak → SIDIX bisa mengajarkan cara otodidak.
> Kalau SIDIX bisa sintesis pengetahuan → SIDIX bisa mengajarkan cara sintesis.
> Kalau SIDIX bisa menemukan gap-nya sendiri → SIDIX bisa membantu user
> menemukan gap mereka sendiri.
>
> Inilah visi "menciptakan bintang-bintang" — bukan SIDIX yang bersinar sendiri,
> tapi SIDIX yang membuat semua yang berinteraksi dengannya ikut bersinar.
