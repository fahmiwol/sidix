# Arsitektur (High-level)

## Target
Modular, bisa jalan lokal (laptop) dan bisa dipindah ke VPS. Semua komponen bisa “diganti” (model API vs lokal, vector db, tool runners).

## Komponen
- **UI Web**: chat, image, voice, agent runs, knowledge base.
- **API Server**: auth, sessions, storage metadata, routing request ke “AI Orchestrator”.
- **AI Orchestrator**:
  - LLM adapter (Anthropic/OpenAI/local)
  - Image adapter (local SD/FLUX bila ada GPU; atau provider API)
  - STT/TTS adapter
  - Agent runtime + tool permissions
  - RAG pipeline (chunk, embed, retrieve, cite)
- **Storage**
  - DB: SQLite (lokal) → Postgres (VPS)
  - Object/file: local disk → S3-compatible (opsional)
  - Vector: embedded local (awal) → Qdrant (opsional)

## Security & Safety
- Tool access **disabled by default**.
- Per agent run: user harus memilih tools yang boleh dipakai.
- Audit log untuk tool call.
- Secrets terenkripsi (API keys).

## Deployment (lokal)
Phase awal paling simpel:
- 1 proses API server + UI
- DB SQLite
- file storage di disk

Phase lanjut (VPS):
- Docker compose: app + postgres + (optional) qdrant

