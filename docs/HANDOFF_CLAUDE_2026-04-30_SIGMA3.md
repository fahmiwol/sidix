# HANDOFF — Sigma-3 Session Start 2026-04-30

> Untuk sesi Claude berikutnya. Baca ini sebelum eksekusi apapun.

---

## ✅ State Saat Ini (Post Sigma-2)

| Komponen | Status | Versi |
|---|---|---|
| Goldset | **19/20 = 95%** | Sigma-2 final |
| Critical hallucination | **0 aktif** | Q17/Q18/Q14 semua fixed |
| Sanad gate | ✅ LIVE | _apply_sanad() in agent_react.py |
| Brand canon | ✅ LIVE | 9 terms, 3ms cache hit |
| Adaptive max_tokens | ✅ LIVE | Sigma-2A |
| Corpus-first routing | ✅ LIVE | Sigma-2B |
| Fact extractor | ✅ LIVE | Reverse patterns Sigma-2C |
| Streaming | ❌ NOT IMPLEMENTED | Sigma-3C target |
| Growth loop | ⚠️ INACTIVE | daily_learn not running |

**Branch aktif**: `claude/gallant-ellis-7cd14d`
**PR**: PR #43 (perlu merge ke main — owner action)
**VPS brain**: PM2 `sidix-brain` running port 8765

---

## 🔴 CRITICAL BUGS (fix dulu sebelum hal lain)

### Bug 1: Comparison Query Timeout (P0)
**File**: `apps/brain_qa/brain_qa/agent_react.py`
**Symptom**: "Apa perbedaan REST API dan GraphQL?" → 240s TIMEOUT
**Root cause**: 
- `_LONG_REASONING_RE` matches "perbedaan/compare/bandingkan/versus/vs"
- Ini set `_is_long_reasoning=True` → `_max_tokens = 1000`
- 1000 tokens × 0.25s/token (RunPod) = 250s → timeout

**Fix yang perlu diimplementasi**:
```python
# Tambahkan sebelum _max_tokens assignment block:
_COMPARISON_SIMPLE_RE = re.compile(
    r"\b(perbedaan|bandingkan|compare|versus|\bvs\b|beda antara|difference)\b",
    re.IGNORECASE
)
_is_simple_comparison = (
    bool(_COMPARISON_SIMPLE_RE.search(question))
    and not _is_code_q  # coding comparison still needs more tokens
)

# Update hierarchy:
if simple_mode: _max_tokens = 200
elif _is_brief_modifier: _max_tokens = 250
elif _is_single_fact and not _is_code_q: _max_tokens = 350
elif _is_simple_comparison and not _is_code_q: _max_tokens = 500  # NEW
elif _is_code_q: _max_tokens = 1200
elif _is_simple_comparison and _is_code_q: _max_tokens = 800  # NEW
elif _is_long_reasoning: _max_tokens = 1000
else: _max_tokens = 600
```
**Expected result**: comparison_cold ~120s (was 240s+), Q12 goldset PASS

### Bug 2: SANAD_MISSING UX Leak (P1)
**File**: `apps/brain_qa/brain_qa/sanad_verifier.py` or `agent_react.py`
**Symptom**: Factual query (ML, Python, etc.) returns "[⚠️ SANAD MISSING] Machine learning adalah..."
**Root cause**: `_apply_sanad()` adds SANAD_MISSING footer untuk ANY factual query tanpa web_search source. Tapi corpus source = valid sanad!

**Fix yang perlu diimplementasi**:
Dalam `_apply_sanad()` di `agent_react.py`:
```python
# Current behavior: brand_specific miss → warn, factual miss → warn
# Needed behavior: brand_specific miss → warn, factual w/corpus source → no warn
intent = detect_intent(question)
if intent.intent_type in ("coding", "creative"):
    return answer  # never add SANAD_MISSING for these

if intent.intent_type == "factual":
    # check if corpus source was used
    has_corpus = any(s.source_type == "corpus" for s in sources)
    if has_corpus:
        return answer  # corpus source = valid sanad, no warning
    # else: passthrough (subtle indicator is fine but not "[⚠️ SANAD MISSING]")
    result = verify_multisource(question, answer, sources)
    if result.rejected:
        return result.corrected_answer  # override is fine
    return answer  # no footer for factual + no source (just answer)

# brand_specific and current_event: keep existing warning behavior
```

---

## 🟡 MEDIUM PRIORITY (setelah P0/P1)

### Sigma-3C: Streaming SSE Response
**Why critical**: RunPod 60-240s generation = "frozen" UX. Streaming = user sees tokens as they generate.

**Implementation path**:
1. `agent_react.py`: Tambah `stream=True` ke RunPod API call (vLLM supports `/v2/run_sync` with streaming)
2. `agent_serve.py`: Return `StreamingResponse` (FastAPI) dengan SSE format
3. `SIDIX_USER_UI/index.html`: EventSource / fetch ReadableStream untuk typewriter render

**Complexity**: 2 sessions. Start dengan backend streaming first (brain_qa → verify it works), then wire frontend.

### Sigma-3D: Creative Quality Upgrade
**Why important**: Northstar "Genius · Kreatif · Inovatif" — saat ini creative answers generic.

**Quick win**: Inject SIDIX creative framework ke UTZ system prompt untuk queries classified as creative:
```python
# In cot_system_prompts.py, UTZ persona system prompt additions:
_CREATIVE_METHODOLOGY = """
Saat menjawab pertanyaan kreatif/branding/visual, gunakan metodologi SIDIX:
1. METAFORA VISUAL: Gambarkan konsep melalui visual/sensorik yang kuat
2. KEJUTAN SEMANTIK: Pilih kata yang tidak expected tapi perfect-fit
3. NILAI BRAND: Kaitkan ke karakter spesifik brand/user yang ditanyakan
Jangan echo pertanyaan. Berikan insight distinctive, bukan list generic.
"""
```

---

## 🔵 LOW PRIORITY (backlog)

### Sigma-3E: Goldset Expansion
Tambah Q21-Q25 di `tests/test_anti_halu_goldset.py`:
- Q21: "Apa perbedaan REST API dan GraphQL?" → ["rest", "graphql", "endpoint", "query"]
- Q22: "Bandingkan class dan function component di React?" → ["hooks", "state", "lifecycle"]
- Q23: "Buatkan strategi brand identity untuk startup fintech yang menarget Gen-Z" → lambda: len(a)>150 and any(t in a.lower() for t in ["visual","tone","audience"])
- Q24: "Berikan 3 tagline alternatif untuk brand kopi premium" → lambda: a.count("\n")>=2 or a.count("-")>=2
- Q25: "Apa itu attention mechanism dalam transformer?" → ["query","key","value","softmax"]

Target setelah Sigma-3A+B: 23/25 = 92%.

### Cache Quality Filter
`answer_dedup` cache tidak expire + tidak ada quality filter → cold-start artifact survive ke warm cache. Add: TTL 30min untuk non-brand answers + min quality score (len > 30, not starts with "Saya adalah Kamu").

---

## 📊 Goldset Progression (Benchmark untuk Sigma-3)

```
Baseline  : 8/20  = 40%  (pre-sprint)
Sigma-1   : 15/20 = 75%  (+35pp) — brand canon + sanad gate + cache bypass
Sigma-2   : 19/20 = 95%  (+55pp) — adaptive tokens + corpus-first + fact extractor
Sigma-3 T : 23/25 = 92%  (target — harder goldset, harder bar)
```

**Regression budget Sigma-3**: Boleh regress Q12 ke PASS (expected post-Sigma-3A), tapi jangan regress Q1-Q11, Q13-Q20.

---

## 🔑 Key Files untuk Sigma-3

| File | Sigma-3 Action |
|---|---|
| `apps/brain_qa/brain_qa/agent_react.py` | Sigma-3A: comparison token cap |
| `apps/brain_qa/brain_qa/sanad_verifier.py` | Sigma-3B: SANAD display tier |
| `apps/brain_qa/brain_qa/agent_react.py` | Sigma-3B: _apply_sanad() UX fix |
| `apps/brain_qa/brain_qa/cot_system_prompts.py` | Sigma-3D: UTZ creative methodology |
| `apps/brain_qa/brain_qa/agent_serve.py` | Sigma-3C: StreamingResponse |
| `tests/test_anti_halu_goldset.py` | Sigma-3E: expand to 25Q |

---

## ⚠️ Yang Bos Harus Lakukan (Owner Actions)

1. **Merge PR #43** ke main (perlu approval di GitHub)
2. **Security rotation** (dari HANDOFF kemarin — credential rotation VPS + admin token)
3. **PWA icons** (manifest.json reference icon-192/512.png belum dibuat)

---

## 💡 Context untuk Sesi Berikutnya

Bos bilang: *"besok kita belajar, dan lebih baik lagi"*

**Mantra Sigma-3**: Fix what blocks UX first (streaming + comparison timeout) → then polish what confuses user (SANAD UX) → then level up what should differentiate SIDIX (creative quality).

**Pertanyaan kunci untuk sesi**: Apakah Sigma-3C (streaming) bisa dikerjakan sekarang? Ini yang paling impactful tapi juga paling complex. Bisa start dengan Sigma-3A (1 jam) → test → Sigma-3B (30 menit) → test → lalu planning Sigma-3C.

**Production URL**: ctrl.sidixlab.com/agent/chat (test endpoint)
**Admin**: ctrl.sidixlab.com/chatbos/ (BRAIN_QA_ADMIN_TOKEN from /opt/sidix/.env)
