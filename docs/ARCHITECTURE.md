# SIDIX — Architecture (high level)

> **Archive notice / Catatan arsip:** SIDIX was discontinued on 16 Sep 2026. This document is kept as research history and may describe features that no longer run. / SIDIX dihentikan 16 Sep 2026; dokumen ini disimpan sebagai arsip riset.


Dokumen ini merangkum arsitektur SIDIX secara ringkas untuk onboarding kontributor.

## Diagram (Mermaid)

```mermaid
flowchart TD
  UI[SIDIX_USER_UI (Vite/TS)] -->|HTTP| API[brain_qa FastAPI]
  API -->|ReAct loop| AGENT[Agent Runtime]
  AGENT -->|retrieve| CORPUS[brain/public corpus (MD)]
  AGENT -->|sanad| CITE[Citations / Sanad]
  AGENT -->|tools| TOOLS[Tool registry (local)]
  API -->|index| INDEX[BM25 index + chunks.jsonl]

  CORPUS --> INDEX
  UI -->|stream tokens + meta| API
```

## Catatan

- **Standing alone**: jalur utama tidak bergantung pada API vendor.
- **Sanad**: jawaban idealnya menyertakan rujukan (chip sitasi di UI).
- **Verifikasi**: gunakan label epistemik (mis. `[FACT]`, `[OPINION]`, `[UNKNOWN]`) sebagai guardrail.

