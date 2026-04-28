---
sanad_tier: primer
---

# 276 — Sanad Chain di SIDIX: Definisi, Implementasi, Cara Kerja

**Tanggal**: 2026-04-28 evening  
**Sprint**: 30 A1 (Continuity Manifest follow-up)  
**Trigger**: Sprint 28b E2E test temukan query *"apa itu sanad chain di SIDIX?"* return *"SIDIX tidak memiliki sanad chain"* — corpus gap padahal konsep ini CORE  
**Status**: Definition published (akan reindex untuk corpus inject Sprint 28a + hybrid retrieval Sprint 25)

---

## Apa itu Sanad di SIDIX

**🚨 PENTING — KOREKSI FRAMING (user clarification 2026-04-28 evening)**:

Sanad di SIDIX **BUKAN strict harfiah / citation chain rigid**. Yang dipakai
adalah **SPIRIT** dari pola tradisi keilmuan: cari ke akar sumber → cross-validate
multi-sumber → score relevance → output yang trusted. Inspirasi pola, bukan adopsi
literal.

Cite langsung note 248 line 87-94:
> *"Tradisi keilmuan Islam punya pattern engineering yang brilliant. Kita extract POLA, BUKAN doctrine.*  
> *Sanad sebagai METODE (bukan citation chain harfiah)*  
> *Cari ke akar dari segala sumber → cross-validate antar sumber → score sampai relevance ~1.0 sempurna → output validated"*

Sanad **wajib eksplisit hanya untuk** topik sensitif (fiqh/medis/data faktual/
historis/statistik/klaim sains). Untuk casual chat / coding / brainstorm /
konsep yang well-established → **skip**, kontekstual, bukan blanket (per pivot
2026-04-25 LIBERATION).

**Sanad sebagai SPIRIT, bukan ritual**:
- Spirit: traceability + cross-validation + integrity
- Bukan: religious citation chain copy-paste, bukan rigid mutawatir-counter

---

## Definisi Operasional

Sanad di SIDIX adalah **rantai validasi/atribusi sumber** untuk klaim apapun yang
SIDIX hasilkan **saat konteks butuh**. Tujuannya: setiap klaim faktual bisa
**ditelusuri** balik ke sumber, dan klaim dengan **multi-source agreement** dapat
skor confidence lebih tinggi.

Implementasi: chain-of-provenance + parallel consensus + tier-weighted ranking.

---

## Tiga Komponen Konkret

### 1. Sanad Tier (corpus weighting)

**File**: [`apps/brain_qa/brain_qa/sanad_ranking.py`](apps/brain_qa/brain_qa/sanad_ranking.py)

Setiap research note punya `sanad_tier` di YAML frontmatter:

```yaml
---
sanad_tier: primer | ulama | peer_review | aggregator | unknown
---
```

Bobot retrieval ranking:
- `primer` (1.5×) — sumber primer (kitab asli, paper, kode kanonik)
- `ulama` (1.3×) — chain ahli verifikasi (scholarly review)
- `peer_review` (1.2×) — published peer-reviewed
- `aggregator` (0.9×) — secondary aggregation (Wikipedia, blog summary)
- `unknown` (1.0×) — default

**Cara kerja**: BM25 score × tier weight = final ranking. Jadi corpus chunk yang
sumbernya primer di-prioritize dibanding aggregator saat retrieval.

```python
def apply_sanad_weight(sanad_tier: str, base_score: float) -> float:
    return base_score * SANAD_WEIGHTS.get(tier, 1.0)
```

### 2. Sanad Consensus (multi-source validation)

**File**: [`apps/brain_qa/brain_qa/sanad_orchestrator.py`](apps/brain_qa/brain_qa/sanad_orchestrator.py)  
**Spec**: research note 239

Saat user nanya hal faktual, SIDIX dispatch **paralel** ke N independent sources:
- Wikipedia (via `wiki_lookup_fast`)
- Web search (Brave / DDG / Wikipedia fallback via `_tool_web_search`)
- LLM consensus pool (multiple teachers, future: classroom_pairs)
- Internal corpus (BM25 + Dense hybrid retrieval)

Kemudian **filter by agreement**: claim yang muncul di ≥2 sumber independent
dapat confidence score lebih tinggi. Branches dengan tier:
- `primer` source = 0.85-1.0 weight
- `aggregator` = 0.7
- `LLM_consensus` = 0.75 (need ≥2 teachers agree)

Output: jawaban + sanad chain (which sources agreed) + confidence score.

### 3. Sanad Frontmatter (per-note provenance)

**Spec**: research note 141

Setiap research note di `brain/public/research_notes/` punya frontmatter yang
mendukung sanad chain integritas:

```yaml
---
sanad_tier: primer
sanad_sources:
  - "research note X (kalau compound)"
  - "code path file:line"
  - "user directive YYYY-MM-DD"
isnad: "claude_session_2026-04-28 → user_review → committed"
---
```

Di-validate saat reindex: notes tanpa sanad info dapat tier `unknown` (1.0×).

---

## Mengapa Sanad Penting di SIDIX (4 alasan)

### 1. Anti-halusinasi struktural

LLM sendiri bisa generate confident-sounding claims tanpa basis. Sanad memaksa
**setiap klaim faktual** harus ada source-linked. Kalau tidak ada source agreement,
sistem return *"saya tidak yakin"* atau lakukan tool call (web_search) dulu.

Contoh real: Sprint 28a bug — query "SIDIX adalah apa?" sebelumnya bypass corpus
→ LLM jawab "komunitas pertanian sustainable" (halusinasi). Setelah Sprint 28a
inject corpus snippet (basis sanad), jawaban grounded jadi "mesin inferensi lokal
pakai ReAct, BM25, tools".

### 2. Multi-source agreement = confidence

Sanad consensus pattern (note 239): claim yang muncul di Wikipedia + Brave web +
corpus = 3-source agreement = high confidence. Claim yang cuma muncul di 1 LLM
output = low confidence, perlu tabayyun.

### 3. Tier-weighted retrieval = sumber primer prioritized

`apply_sanad_weight()` di hybrid search bikin chunk dari sumber primer outrank
aggregator. Jadi user dapat citation paling otoritatif duluan, bukan blog summary
yang mungkin error rambat.

### 4. Provenance untuk sanad-itu-sendiri (rekursif)

Note 141 spec: setiap research note punya `sanad_tier` + `sanad_sources` di YAML.
Jadi corpus growth juga **terdokumentasi sumbernya** — sanad chain untuk sanad
chain. Future hafidz ledger (note 141) akan add cryptographic Merkle proof di
atas ini.

---

## Implementasi Status (per 2026-04-28)

| Komponen | Status | Code path |
|----------|--------|-----------|
| Sanad tier weighting di BM25 ranking | LIVE | `sanad_ranking.py` |
| Sanad tier di hybrid retrieval (Sprint 25 BM25+Dense) | LIVE | `query.py` apply_sanad_weight |
| Sanad consensus orchestrator (parallel branches) | LIVE | `sanad_orchestrator.py` + `/ask/stream` |
| Sanad frontmatter di research notes | PARTIAL | banyak note belum punya, baseline `unknown` |
| Hafidz ledger Merkle integration | PLANNED | spec note 141, code belum |
| Tabayyun quality gate | PLANNED | konsep di note 248, gate belum eksplisit |

---

## Compound dengan Sprint Lain

**Compound dengan**:
- Sprint 25 hybrid retrieval — sanad weight applied in `query.py`
- Sprint 27c paraphrase eval — measured +6% Hit@5 with sanad tier weighting active
- Sprint 28a simple-tier corpus inject — BM25 top-1 with sanad weighting → grounded answer

**Akan compound dengan**:
- Sprint 30+ Hafidz ledger — Merkle proof on top of sanad chain
- Sprint 31+ AKU inventory — sanad metadata per AKU
- Sprint 32+ Skill cloning — preserve source agent's epistemic honesty (sanad-of-skill)

---

## Cara Cek Sanad di Praktek

Pertanyaan ke SIDIX: *"Apa sanad untuk klaim ini?"* (atau langsung lihat citations).

Dalam response `/ask`, lihat:
- `citations[]` — list URL/source yang di-quote
- `_complexity_tier` — kalau `standard`/`deep`, full sanad orchestrator dipakai
- Untuk corpus citations: snippet + filename, `sanad_tier` ter-encode di weighting

Untuk note di corpus, baca YAML frontmatter:
```bash
head -10 brain/public/research_notes/<n>_*.md
```

---

## Hard Rule Compliance (note 248)

- ❌ "Drop sanad chain" → ✓ TIDAK dilanggar (sanad LIVE di 3 layer)
- ❌ "Trivialize spiritual aspects" → ✓ Frame sanad sebagai METHOD, bukan adopsi religius
- ❌ "Klaim spiritual entity" → ✓ SIDIX tidak claim spiritual, sanad murni epistemic discipline

---

## Files Referenced

- `apps/brain_qa/brain_qa/sanad_ranking.py` — tier weights + frontmatter parser
- `apps/brain_qa/brain_qa/sanad_orchestrator.py` — parallel branch consensus
- `apps/brain_qa/brain_qa/query.py` — apply_sanad_weight di retrieval pipeline
- `apps/brain_qa/brain_qa/agent_serve.py` `/ask/stream` — sanad orchestrator wired
- research note 141 — Hafidz integration spec (planned)
- research note 239 — Sanad Vol21 consensus algorithm spec
- research note 248 line 85 — sanad as METHOD (LOCK)
- `docs/SIDIX_CONTINUITY_MANIFEST.md` section 2.1 + 2.15 — concept registry

---

## Untuk Reindex (action item)

Setelah note ini commit, run:
```bash
# VPS:
cd /opt/sidix && python -m brain_qa index
# verify:
curl -s -X POST http://localhost:8765/ask \
  -d '{"question":"apa itu sanad chain di SIDIX?","persona":"ABOO"}' | jq '.answer'
```

Expected: jawaban mention "rantai validasi/atribusi sumber" + "primer/ulama/aggregator tier" + "consensus paralel multi-source".
