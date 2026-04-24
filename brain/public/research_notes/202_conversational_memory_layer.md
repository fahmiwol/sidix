# 202 — Conversational Memory Layer untuk SIDIX

**Tanggal:** 2026-04-24
**Agen:** Claude (Kimi Code CLI)
**Commit:** `a5fc9eb`

---

## Apa

Modul `memory_store.py` yang menyimpan session history dan user preferences secara persistent (SQLite) supaya SIDIX bisa:
1. Melanjutkan percakapan (conversation threading)
2. Ingat preferensi user (bahasa, persona, literacy, cultural frame)
3. Retrieve N turn terakhir untuk injection ke ReAct prompt sebagai konteks

## Mengapa

Sebelumnya `_sessions` hanya dictionary in-memory. Restart server = hilang semua history. User tidak bisa melanjutkan chat kemarin. Agent tidak punya "memori jangka panjang". Untuk menjadi "enak diajak ngobrol", SIDIX wajib ingat siapa yang ngobrol, bahasa apa, dan apa yang sudah dibicarakan.

## Bagaimana

### Arsitektur
- **Backend**: SQLite default (lightweight, zero-config), PostgreSQL-ready via `SIDIX_DB_URL`
- **Thread-local connection pool**: tiap thread punya conn sendiri, aman untuk FastAPI async workers
- **Schema 3 tabel**:
  - `conversations` — metadata thread (user_id, title, persona, language, literacy, cultural_frame)
  - `messages` — tiap turn Q/A (role, content, citations, confidence)
  - `user_profiles` — preferensi user yang persist antar session

### Context Injection
- `get_recent_context(conv_id, turns=6)` → ambil 6 turn terakhir (12 message: 6 user + 6 assistant)
- `_inject_conversation_context()` di `agent_react.py` format jadi:
  ```
  [KONTEKS PERCAKAPAN SEBELUMNYA]
  User: ...
  Assistant: ...
  [AKHIR KONTEKS]
  [PERTANYAAN SAAT INI]
  ...
  ```
- Non-breaking: kalau tidak ada conversation_id, auto-create thread baru

### API Endpoints Baru
- `GET /memory/conversations`
- `GET /memory/conversations/{id}/messages`
- `POST /memory/conversations/{id}/rename`
- `DELETE /memory/conversations/{id}`

## Contoh Nyata

User chat pertama:
```
User: "Halo, namaku Budi. Saya suka desain grafis."
→ SIDIX buat conversation_id: abc123, user_profile: {preferred_persona: AYMAN}
```

User chat keesokan hari dengan conversation_id yang sama:
```
User: "Bantu saya bikin logo untuk kopi shop."
→ SIDIX inject konteks sebelumnya → ngerti bahwa Budi suka desain grafis → jawaban lebih personal
```

## Keterbatasan
- SQLite tidak scalable untuk >10k concurrent writes. Upgrade ke PostgreSQL tinggal set env `SIDIX_DB_URL`.
- Context injection naif (N turn terakhir, bukan semantic retrieval dari memory). Next: RAG-style memory retrieval via embedding.
- Belum ada eviction policy selain umur 30 hari.

## Next Steps
- Wire `conversation_id` ke frontend (`SIDIX_USER_UI`) agar UI bisa tampilkan daftar chat history
- Implement memory RAG: embed conversation turns → vector search untuk retrieve relevan history
- Auto-summarize conversation untuk title generation
