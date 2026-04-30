# Jiwa Sprint — Kimi Lane (2026-04-25)

## Konsep
Claude = **Otak** (logika, reasoning, response hygiene, follow-up detection, deploy).  
Kimi = **Jiwa** (taste, emosi, kreativitas naratif, aksi eksekusi).

Sprint ini mengisi gap "jiwa" SIDIX: taste learning, empati emosional, kreativitas dalam, dan aksi audio.

---

## Phase 1: Persona Voice Calibration Engine 🎯 Taste
**File:** `apps/brain_qa/brain_qa/persona_voice_calibration.py`

**Tujuan:** SIDIX belajar preferensi taste user terhadap voice/tone per persona.

**Dimensi kalibrasi:**
- `warmth` (dingin → hangat)
- `formality` (santai → formal)
- `depth` (ringkas → mendalam)
- `humor` (serius → jenaka)
- `religiosity` (sekuler → religius)
- `nusantara_flavor` (netral → kuat lokal)

**Sumber signal:**
1. Explicit feedback: "kurang formal", "terlalu panjang", "lebih santai dong"
2. Implicit: thumbs up/down pada response
3. Jariyah pairs: CQF tinggi + thumbs_up = voice diterima

**Output:** `VoiceProfile` per `(user_id, persona)` → modifier dict yang di-inject ke response blend.

---

## Phase 2: Emotional Tone Engine 🎭 Empati
**File:** `apps/brain_qa/brain_qa/emotional_tone_engine.py`

**Tujuan:** Deteksi emosi user dari teks + adaptasi tone respons.

**Deteksi (rule-based, ID+EN):**
- Valence: positive / negative / neutral
- Arousal: calm / moderate / excited
- Spesifik: frustrated, angry, sad, anxious, excited, grateful, curious

**Adaptasi:**
- User marah/frustrasi → tone tenang, pendek, solusi-fokus
- User sedih → tone hangat, empati, supportif
- User excited → tone energik, elaboratif
- User grateful → tone humble, menerima

---

## Phase 3: Creative Writing Engine ✍️ Naratif Dalam
**File:** `apps/brain_qa/brain_qa/creative_writing.py`

**Tujuan:** Kreativitas melampaui marketing copy — ke ranah seni naratif.

**Format yang didukung:**
- `short_story` — cerpen dengan narrative arc
- `poetry` — puisi dengan meter & rima heuristic
- `screenplay_scene` — adegan dengan format standar (INT./EXT., dialog, action)
- `worldbuilding_lore` — lore document untuk worldbuilding
- `character_profile` — profil karakter dengan depth

**Fitur:**
- Narrative arc guidance: setup → conflict → climax → resolution
- Voice consistency check terhadap persona
- CQF integration untuk quality gate

---

## Phase 4: Wire Audio Tools 🔊 Aksi
**File:** `apps/brain_qa/brain_qa/agent_tools.py` (modify)

**Tujuan:** Audio capability yang sudah ada (TTS, ASR, MIR) di-expose ke ReAct TOOL_REGISTRY.

**Tools baru di-register:**
- `text_to_speech` — Coqui-TTS / pyttsx3
- `speech_to_text` — faster-whisper
- `analyze_audio` — librosa MIR (pitch, tempo, spectral)

---

## Validasi & Log
- Setiap phase: test file di `apps/brain_qa/tests/`
- Semua test: isolated, nggak perlu BM25/server nyala
- Smoke test bisa jalan via `python -m pytest tests/test_jiwa_*.py -v`
- Catat ke `docs/LIVING_LOG.md` per phase

---

## Anti-Bentrok dengan Claude
| Agen | File Locked | Jangan Sentuh |
|------|-------------|---------------|
| Claude | `agent_react.py` | — |
| Kimi | `persona_voice_calibration.py`, `emotional_tone_engine.py`, `creative_writing.py` | `agent_react.py` |
| Bersama | `agent_tools.py` (append only), `LIVING_LOG.md` (append only) | Hapus/edit existing |
