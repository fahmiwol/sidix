# 185 — Raudah Protocol v0.1: روضة المعرفة — Orkestrasi Multi-Agen Paralel

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-23
**Sanad:** [OPINION] — adaptasi konsep orkestrasi paralel ke dalam framework IHOS + identitas SIDIX
**Tags:** raudah, multi-agent, orchestration, parallel, ihos, specialist

---

## Apa & Etimologi Nama

**Raudah** (الروضة / ar-Rawdah) = taman, kebun.

Dalam tradisi Islam, **al-Rawdah al-Syarifah** adalah ruang antara mimbar dan
makam Nabi Muhammad ﷺ di Masjid Nabawi — disebut dalam hadits shahih sebagai
*"taman dari taman-taman surga"* (HR. Bukhari no. 1195, Muslim no. 1391).

SIDIX memilih nama ini sebagai metafora:
> Raudah adalah **ruang di mana para specialist berkumpul, berembug, dan menghasilkan
> pengetahuan yang terpercaya, terjustifikasi, dan bernilai** — seperti majelis ulama
> di sebuah taman hikmah.

Bukan "swarm" (kawanan serangga) — karena SIDIX bukan tentang kecepatan brute force.
SIDIX tentang **kebenaran yang terverifikasi dan kebijaksanaan yang bermakna**.

---

## Mengapa Raudah (Bukan Arsitektur Lain)

Kimi K2.6 merekomendasikan **Agent Swarm** (hingga 300 sub-agent paralel).
Kita mengadopsi konsep paralel-nya, tapi dengan perbedaan fundamental:

| Aspek         | Sistem Sejenis       | SIDIX Raudah             |
|---------------|----------------------|--------------------------|
| Metafora      | Kawanan (Swarm)      | Taman Hikmah (Raudah)    |
| Backbone LLM  | Vendor API           | Ollama local (no vendor) |
| Guardrail     | Tidak ada            | IHOS Maqashid check      |
| Verifikasi    | Self-report          | Sanad Validator Specialist|
| Konflik       | Majority vote        | Ijtihad Resolver         |
| Identitas     | Netral/barat         | Nusantara-Islam native   |

---

## Arsitektur

```
Task User
    │
    ▼
RaudahOrchestrator.urai_task()   ← Qiyas: analogikan → subtask
    │
    ├── IHOS Guardrail (Maqashid check)
    │       ↓ GAGAL → return alasan
    │       ↓ LULUS → lanjut
    │
    ├── kelompok_paralel = [[task1, task2, ...], ...]
    │
    ▼
asyncio.gather(*[Specialist.jalankan(task) for task in kelompok])
    │
    ├── Specialist.peneliti    → [FAKTA]/[OPINI] + sumber
    ├── Specialist.analis      → pro/kontra sistematis
    ├── Specialist.penulis     → draft konten Bahasa Indonesia
    ├── Specialist.perekayasa  → kode bersih + dokumentasi
    └── Specialist.verifikator → Sanad check per klaim
    │
    ▼
RaudahOrchestrator.agregasi()    ← Ijma': sintesis konsensus
    │
    ▼
RaudahResult.jawaban_final
```

---

## Konsep IHOS dalam Raudah

| Konsep IHOS     | Lapisan SIDIX BIBLE | Implementasi Raudah               |
|-----------------|---------------------|-----------------------------------|
| Qiyas (analogi) | AKAL                | Urai task → subtask analogis      |
| Ijma' (konsensus)| QALB               | Agregasi = sintesis spesialis     |
| Ijtihad (ijtihad)| AKAL + NAFS        | Mediasi konflik via Maqashid score|
| Sanad (rantai)  | AL-AMIN             | Verifikator specialist cek sumber |
| Maqashid        | QALB                | IHOS Guardrail sebelum spawn      |
| Tafakkur        | Cognitive mode      | Orchestrator reflection + agregasi|

---

## Penggunaan

```python
import asyncio
from brain.raudah.core import run_raudah

# Research task
hasil = asyncio.run(run_raudah(
    "Riset dan bandingkan 5 model wakaf produktif yang berhasil di Asia Tenggara"
))
print(hasil.jawaban_final)
print(f"Specialist: {len(hasil.hasil_spesialis)}, Durasi: {hasil.durasi_s}s")

# Creative task  
hasil = asyncio.run(run_raudah(
    "Buat kampanye media sosial UMKM kopi lokal, target generasi muda muslim Indonesia"
))
```

---

## Roadmap Raudah

```
v0.1 (sekarang)  : skeleton, heuristik rule-based, asyncio flat-parallel
v0.2             : TaskGraph DAG + dependency tracking (B tidak mulai sebelum A selesai)
v0.3             : GraphRAG sebagai tool Specialist Peneliti
v0.4             : Reward signal log ke SQLite (groundwork RL)
v0.5             : Ijtihad Conflict Resolution (spesialis konflik → Maqashid mediasi)
v1.0             : Orchestrator belajar dari reward (PARL-inspired, local training)
```

---

## Keterbatasan v0.1

1. Dekomposisi masih heuristik (regex) — belum LLM-based
2. Semua task paralel datar, belum ada dependency graph
3. Context sharding manual (800 char) — belum adaptive per task complexity
4. Agregasi Ollama menambah latency sekitar 15-30 detik
5. Belum ada persistence log per sesi Raudah

---

## File

- `brain/raudah/__init__.py`
- `brain/raudah/core.py`

---

## Referensi

- Hadits Raudah: Bukhari no. 1195, Muslim no. 1391
- Analisis sistem sejenis: dokumen riset kolaborator eksternal (Apr 2026)
- docs/SIDIX_BIBLE.md — Pilar Mandiri + IHOS cognitive layers
- docs/MASTER_ROADMAP_2026-2027.md §Sprint 7+
