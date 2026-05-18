---
title: P4 Live QA — Conversation Memory + Web Direct Answer Fix
tags: [p4, live-qa, omnyx, memory, web-search, ux-regression]
date: 2026-05-02
sanad_tier: internal
---

# 313 — P4 Live QA: Memory + Web Direct Answer

## Konteks

P4 didahulukan sebelum P5 LoRA karena LoRA membutuhkan data interaksi produksi
yang benar. Live app adalah sumber kebenaran user experience, bukan hanya repo,
curl lokal, atau klaim deploy.

## Temuan QA Live

1. Query faktual sederhana `Berapa jarak rata-rata Bumi ke Matahari?` masih
   mengembalikan blok Wikipedia mentah, bukan jawaban singkat.
2. Conversation memory gagal pada preferensi baru:
   `nama saya Mighan dan warna favorit saya hijau zamrud` lalu
   `Apa warna favorit saya tadi?`.

## Root Cause

- Greeting detector memakai substring keyword `hi`, sehingga kata `hijau`
  salah diklasifikasikan sebagai sapaan.
- Simple factual path memakai web direct pass-through, tetapi belum memilih
  kalimat paling relevan dari bundle web yang berisi snippets + page text.
- Wikipedia fallback hanya mengembalikan title/snippet pendek saat Mojeek dan
  DDG gagal dari VPS, sehingga konteks untuk synthesis terlalu miskin.

## Fix

- `omnyx_direction.py`
  - tambah `personal_memory` fast-path untuk preferensi sederhana dalam konteks
    percakapan;
  - greeting regex dibatasi ke sapaan standalone;
  - tambah `_select_relevant_web_answer()` untuk memilih kalimat paling relevan.
- `mojeek_search.py`
  - Wikipedia fallback enrich result dengan intro extract API.

## Verifikasi Lokal

- `python -m pytest apps/brain_qa/tests/test_omnyx_live_regressions.py -q`
  → 3 passed.
- `python -m pytest apps/brain_qa/tests/test_conversation_memory.py apps/brain_qa/tests/test_memory_store.py apps/brain_qa/tests/test_omnyx_live_regressions.py -q`
  → 24 passed.
- `python -m py_compile apps/brain_qa/brain_qa/omnyx_direction.py apps/brain_qa/brain_qa/mojeek_search.py`
  → PASS.

## Lesson

String matching untuk UX-critical routing harus word-boundary aware. Untuk
simple direct answers, latency cepat tidak boleh mengorbankan relevansi: pilih
sentence evidence terbaik, bukan dump sumber mentah.
