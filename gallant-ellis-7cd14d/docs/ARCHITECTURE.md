# SIDIX — Architecture (high level)

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

