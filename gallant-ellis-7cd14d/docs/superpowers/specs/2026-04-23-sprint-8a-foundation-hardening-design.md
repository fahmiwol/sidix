# Spec — Sprint 8a: Foundation Hardening (al‑Amin + Jariyah)

**Tanggal**: 2026-04-23  
**Status**: Draft (menunggu review founder)  
**SSOT aturan**: `docs/AGENTS_MANDATORY_SOP.md`  
**Tujuan sprint**: membuat SIDIX lebih **al‑Amin** (andal) dan lebih **Jariyah** (belajar kontinu) tanpa menambah ketergantungan vendor API.

---

## 1) Latar belakang & masalah yang diselesaikan

SIDIX sudah punya pondasi agent loop + modul-modul “Jiwa” dan “Typo resilience”, tapi wiring end-to-end belum konsisten untuk:

- **Input quality**: typo/abrev Indonesia perlu dinormalisasi sebelum retrieval + reasoning.
- **Output quality**: persona & tone perlu distabilkan sebagai lapisan Nafs (tanpa merusak label epistemik).
- **Feedback → learning**: feedback user harus jadi training pairs yang rapi, anonim, dan bisa dipakai untuk siklus belajar.
- **Multi-client**: Agency OS butuh konteks per klien (branch) sebagai fondasi.

---

## 2) Scope Sprint 8a (apa yang dikerjakan)

Sprint 8a fokus pada 4 wiring utama:

1) **Typo wire (pre-processing)**  
2) **Nafs wire (post-processing)**  
3) **Jariyah v3 (feedback capture → training pairs)**  
4) **Branch basic (multi-client context injection)**

> Catatan: sprint ini tidak menambah fitur generatif baru (image/video/audio). Itu Sprint 8b.

---

## 3) Non-goals (yang sengaja tidak dikerjakan)

- Tidak membuat UI Agency OS baru (Sprint 8c).
- Tidak membuat orkestrasi Raudah v2 paralel (Sprint 8d).
- Tidak menambah integrasi platform/host sebagai dependensi default. Integrasi hanya **opsional**.
- Tidak memasukkan secrets / tokens ke repo (SOP).

---

## 4) Prinsip desain & guardrails (SOP)

- **Standing alone default**: jalur utama tidak mengandalkan model API pihak ketiga.
- **Kompatibilitas boleh disebut**: publik boleh menyebut “SIDIX kompatibel dengan platform X” sebagai informasi tutorial, tapi:
  - tidak boleh framing “meniru/dibuat oleh platform X”
  - tidak boleh jadi requirement default
- **Tidak bocor path lokal / server paths / secrets** ke artefak publik.
- **Persona resmi**: AYMAN, ABOO, OOMAR, ALEY, UTZ.
- **Terminologi kanonis**: Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir.

---

## 5) Arsitektur target (aliran data)

### 5.1 Aliran request (high level)

1. **User query masuk**
2. **Typo normalization** → menghasilkan `normalized_query` + `corrections`
3. **Retrieval + ReAct loop** memakai `normalized_query`
4. **LLM output** (raw)
5. **Nafs orchestration** (tone/persona blending) tanpa merusak label epistemik
6. **Response keluar**
7. **Feedback (opsional)** ditangkap sebagai training pair (Jariyah)

### 5.2 Kontrak data minimal

- `original_query`: string asli dari user (untuk audit internal)
- `normalized_query`: string yang dipakai untuk retrieval/caching
- `final_answer`: jawaban final setelah Nafs layer
- `persona`: salah satu 5 persona resmi
- `session_id`: anon identifier (tanpa email/nama)

---

## 6) Komponen yang diubah/ditambah

### 6.1 Typo wire (pre-processing)

**Intent**: meningkatkan akurasi retrieval & routing ketika user mengetik informal/typo.

- **Input**: `query: str`
- **Output**: `{ normalized_query: str, corrections: list }`
- **Rule**: normalization tidak boleh “mengarang” atau mengubah makna jika query sudah benar.

**Acceptance criteria**
- Normalisasi terjadi sebelum retrieval & agent reasoning.
- Ada log/telemetry ringan bila ada koreksi (tanpa menyimpan PII).

### 6.2 Nafs wire (post-processing)

**Intent**: memaku persona/tone agar jawaban konsisten dan terasa “berjiwa”, tapi tetap jujur epistemik.

**Aturan penting**
- Jika output diawali label epistemik `[FACT]`/`[OPINION]`/`[SPECULATION]`/`[UNKNOWN]`, label itu **harus tetap di depan**.
- Tidak menambah klaim faktual baru pada tahap blending.

**Acceptance criteria**
- AYMAN vs ABOO terasa berbeda untuk prompt yang sama.
- Label epistemik tidak hilang/bergeser.

### 6.3 Jariyah v3 (feedback capture)

**Intent**: menjadikan thumbs up/down sebagai data belajar.

**Data format (JSONL)**
- Satu baris per event.
- Minimal fields: `query`, `response`, `rating`, `persona`, `timestamp`, `session_id`.

**Privasi**
- Tidak menyimpan email/nama/nomor telepon.
- `session_id` anonim.

**Acceptance criteria**
- Klik feedback → append JSONL event.
- JSON per line valid (bisa `json.loads`).

### 6.4 Branch basic (multi-client context)

**Intent**: fondasi Agency OS: setiap klien punya guidelines + persona preferences.

**Kontrak minimal**
- `branch.slug`, `branch.name`
- `branch.brand_guidelines` (dict)
- `branch.active_personas` (list)

**Acceptance criteria**
- Branch bisa dibuat & diambil.
- Context injection menambahkan guidelines ke prompt (tanpa bocor secrets).

---

## 7) Test plan (verifikasi)

Minimal coverage Sprint 8a:

- **Typo wiring test**: input typo → normalized query expected; input normal → unchanged.
- **Nafs wiring test**: label epistemik tetap; persona style berubah.
- **Jariyah capture test**: feedback event tersimpan; JSONL valid.
- **Branch manager test**: create/get/list + inject context.

---

## 8) Risiko & mitigasi

- **Risiko**: typo normalization terlalu agresif → salah makna.  
  **Mitigasi**: default “conservative”; hanya apply perubahan yang high-confidence.

- **Risiko**: Nafs blending merusak epistemic labels.  
  **Mitigasi**: parsing label & reattach label sebagai prefix final.

- **Risiko**: feedback capture menyimpan PII.  
  **Mitigasi**: schema ketat; drop field yang berpotensi PII.

---

## 9) Definition of Done (Sprint 8a)

Sprint 8a dianggap selesai jika:

- Wiring Typo + Nafs + Jariyah + Branch berjalan end-to-end.
- Test plan minimal di atas lulus.
- Dokumentasi pasca-task di-update: `docs/LIVING_LOG.md` + handoff terbaru + changelog (bila perlu).

