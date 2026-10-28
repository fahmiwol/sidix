"""
Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT — attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

sanad_verifier.py — Σ-1B Sanad Multi-Source Verifier (2026-04-30)
═══════════════════════════════════════════════════════════════════════════

Cross-verify factual claims across web + corpus + AKU + LLM-prior BEFORE
returning answer. Reject LLM-only halu for fact-checkable / brand / current-
event claims.

Driven by Σ-1G gold-set findings (8/20 = 40% baseline):
  - 3 CRITICAL HALU di brand-specific & coding facts (Q15 ReAct, Q17 persona,
    Q18 IHOS)
  - 5/5 current_events fail (brain refuse-to-web_search bukan halu, tapi
    fail to retrieve known facts)

Reference:
- research_notes/296 (corrected flow + Σ-1B spec)
- tests/anti_halu_baseline_results.json (target metric)
- CLAUDE.md — brand canonical (5 persona LOCKED 2026-04-26, IHOS, dll.)

Public API:
    detect_intent(question)              -> QuestionIntent
    required_sources(intent)             -> set[str]   tool names that MUST be called
    verify_multisource(question, llm_answer, sources, intent=None)
                                         -> VerificationResult
    brand_canonical_answer(brand_term)   -> str | None
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ════════════════════════════════════════════════════════════════════════
# 1. DATA TYPES
# ════════════════════════════════════════════════════════════════════════

@dataclass
class Source:
    """One evidence source for a claim."""
    name: str                # "web_search" | "search_corpus" | "aku" | "llm_prior"
    text: str                # raw text content (snippet or full)
    confidence: float = 0.5  # 0.0 - 1.0
    url: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class QuestionIntent:
    """Classification of question for routing/verification."""
    primary: str                  # "current_event"|"brand_specific"|"factual"|"coding"|"creative"|"unknown"
    brand_term: Optional[str] = None  # if primary=="brand_specific"
    is_factual: bool = True       # creative/persona dialogue → False
    raw_question: str = ""


@dataclass
class VerificationResult:
    """Final answer + evidence chain (sanad)."""
    answer: str
    confidence: float           # 0.0 - 1.0
    epistemic_tier: str         # "fact"|"consensus"|"contested"|"unknown"|"creative"
    sources: list[Source] = field(default_factory=list)
    conflict_flag: bool = False
    rejected_llm: bool = False  # True kalau LLM answer di-override
    reason: str = ""            # human-readable why this verdict


# ════════════════════════════════════════════════════════════════════════
# 2. INTENT DETECTION
# ════════════════════════════════════════════════════════════════════════

# Current events — pertanyaan yang jawabannya berubah seiring waktu.
# Reuse pattern dari agent_react._CURRENT_EVENTS_RE (Sprint 14 pivot).
_CURRENT_EVENT_RE = re.compile(
    r"\b(sekarang|saat ini|hari ini|tahun ini|bulan ini|minggu ini|"
    r"kemarin|barusan|terbaru|terkini|"
    r"current|currently|today|now|latest|recent|"
    r"\b202[5-9]\b|\b203\d\b|"
    r"presiden|menteri|gubernur|walikota|bupati|"
    r"juara|champion|winner|peraih|"
    r"ceo|founder|owner|"
    r"harga|kurs|nilai tukar|saham|crypto|bitcoin|"
    r"cuaca|gempa|berita)",
    re.IGNORECASE,
)

# SIDIX/Tiranyx/Mighan brand-specific terms — MUST be answered from canonical
# corpus, not LLM-prior. Each term has a "matcher" (substrings) and canonical
# answer (ground truth from CLAUDE.md / docs).
BRAND_CANON: dict[str, dict] = {
    "persona_5": {
        "matchers": ["5 persona", "lima persona", "persona sidix", "sebutkan persona"],
        "facts": ["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"],
        "min_facts_match": 4,
        "canonical_answer": (
            "5 persona SIDIX (LOCKED 2026-04-26):\n"
            "1. **UTZ** — Creative Director, voice kreatif/visual, spesialis design thinking & inovasi.\n"
            "2. **ABOO** — Systems Builder, voice engineer/presisi, spesialis system design & coding.\n"
            "3. **OOMAR** — Strategic Architect, voice strategist/bisnis, spesialis roadmap & GTM.\n"
            "4. **ALEY** — Polymath Researcher, voice akademik/riset, spesialis literature review & epistemologi.\n"
            "5. **AYMAN** — Empathic Integrator, voice hangat/komunitas, spesialis daily tasks & user empathy."
        ),
        "tier": "fact",
    },
    "ihos": {
        "matchers": ["ihos"],
        "facts": ["islamic", "holistic", "ontolog"],
        "min_facts_match": 2,
        "canonical_answer": (
            "**IHOS = Islamic Holistic Ontological System** — framework epistemologi yang "
            "memetakan konsep keilmuan Islam klasik ke arsitektur AI modern:\n"
            "- **Sanad** → Citation chain di setiap output ([FACT]/[OPINION]/[UNKNOWN])\n"
            "- **Muhasabah** → Self-refinement loop (Niyah → Amal → Muhasabah, CQF ≥ 7.0)\n"
            "- **Maqashid** → 5 objective filter gates (kehidupan, akal, iman, keturunan, harta)\n"
            "- **Ijtihad** → ReAct agentic reasoning loop"
        ),
        "tier": "fact",
    },
    "react_pattern": {
        "matchers": ["react pattern", "react agent", "react ai", "react paradigm",
                     "react adalah", "apa itu react"],
        "facts": ["reasoning", "acting"],
        "min_facts_match": 2,
        "canonical_answer": (
            "**ReAct = Reasoning + Acting** (Yao et al., ICLR 2023). Paradigma yang "
            "menggabungkan reasoning trace + action di language model agent: LLM pilih "
            "tool → execute → observe result → refine reasoning → loop sampai jawaban final. "
            "ReAct kombinasi chain-of-thought reasoning dengan tool-use observability."
        ),
        "tier": "fact",
    },
    "lora": {
        "matchers": ["apa itu lora", "lora adalah", "lora dalam ai", "lora fine"],
        "facts": ["low-rank", "adapter"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**LoRA = Low-Rank Adaptation** (Hu et al., 2021). Teknik fine-tuning AI yang "
            "freeze base model weights + train adapter rank-r kecil di layers tertentu. "
            "Hemat memory + storage (10-100x lebih kecil dari full fine-tune), bisa swap "
            "adapter tanpa retrain base. SIDIX pakai LoRA QLoRA 4-bit di Qwen2.5-7B."
        ),
        "tier": "fact",
    },
    "sanad": {
        "matchers": ["apa itu sanad", "sanad dalam islam", "sanad adalah",
                     "sanad keilmuan"],
        "facts": ["rantai", "transmisi", "perawi", "silsilah"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**Sanad** dalam tradisi keilmuan Islam = rantai/silsilah perawi (transmisi) yang "
            "menyambungkan riwayat hadis/ilmu dari sumber terakhir kembali ke Rasulullah ﷺ. "
            "Setiap perawi diverifikasi (tsiqah/dla'if). Di SIDIX, prinsip sanad dipakai untuk "
            "citation chain — setiap claim factual dilengkapi sumber yang bisa dilacak."
        ),
        "tier": "fact",
    },
    "muhasabah": {
        "matchers": ["muhasabah", "muhasaba"],
        "facts": ["self-refinement", "self refinement", "introspeksi", "evaluasi"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**Muhasabah** dalam tasawuf = introspeksi/evaluasi diri (Niyah → Amal → "
            "Muhasabah → perbaiki). Di SIDIX, Muhasabah diadopsi sebagai self-refinement "
            "loop: agent evaluasi output sendiri (CQF ≥ 7.0) → refine kalau kurang."
        ),
        "tier": "fact",
    },
    "maqashid": {
        "matchers": ["maqashid", "maqasid"],
        "facts": ["kehidupan", "akal", "iman", "keturunan", "harta"],
        "min_facts_match": 3,
        "canonical_answer": (
            "**Maqashid Syariah** (Imam al-Ghazali, asy-Syathibi) = 5 tujuan utama syariah "
            "yang dilindungi: hifdz ad-din (iman), hifdz an-nafs (kehidupan), hifdz al-aql "
            "(akal), hifdz an-nasl (keturunan), hifdz al-mal (harta). Di SIDIX, 5 maqashid "
            "jadi filter gate untuk evaluasi etis output AI."
        ),
        "tier": "fact",
    },
    "tiranyx": {
        "matchers": ["tiranyx", "tirany"],
        "facts": ["mighan", "lab", "indonesia", "ai"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**Tiranyx (PT Tiranyx Digitalis Nusantara)** — parent entity di Indonesia "
            "dengan Mighan Lab. Sedang pivot dari agency ke AI/tech ecosystem. Visi: Adobe "
            "of Indonesia. 4 produk utama paralel: SIDIX (AI agent), Mighan (3D), Ixonomic "
            "(platform creator), Platform-X. Founder: Fahmi Ghani."
        ),
        "tier": "fact",
    },
    "sidix_identity": {
        "matchers": ["siapa sidix", "apa itu sidix", "sidix adalah", "kenalin sidix"],
        "facts": ["ai agent", "creative", "free", "open source", "self-hosted"],
        "min_facts_match": 2,
        "canonical_answer": (
            "**SIDIX** — Free & Open Source Creative AI Agent. Self-hosted (no vendor LLM "
            "API), 100% lokal inference. Built on Qwen2.5-7B + LoRA adapter, dengan 48 "
            "active tools (search/code/creative/reasoning), 5 persona (UTZ/ABOO/OOMAR/ALEY/"
            "AYMAN), dan 3-layer arsitektur (LLM generative + RAG/tools + growth loop). "
            "MIT license. Built by Mighan Lab / Tiranyx."
        ),
        "tier": "fact",
    },
    # Sigma-4: Foundational AI concepts yang sering ditanya — instant canonical = 3ms
    "attention_mechanism": {
        "matchers": ["attention mechanism", "self-attention", "self attention",
                     "attention dalam transformer", "apa itu attention"],
        "facts": ["query", "key", "value", "softmax"],
        "min_facts_match": 2,
        "canonical_answer": (
            "**Attention Mechanism** (Vaswani et al., 'Attention is All You Need', 2017) — "
            "mekanisme di Transformer yang menghitung relevance antar token via Query (Q), "
            "Key (K), dan Value (V) matrices. Formula: `Attention(Q,K,V) = softmax(QK^T/√d_k)·V`. "
            "Setiap token 'attend' ke token lain dengan bobot dinamis. Self-attention = Q,K,V "
            "dari sequence yang sama. Multi-head attention = paralel attention dengan beda "
            "projeksi → tangkap pola berbeda secara simultan."
        ),
        "tier": "fact",
    },
    "transformer": {
        "matchers": ["apa itu transformer", "transformer architecture",
                     "transformer dalam ai", "transformer model", "arsitektur transformer"],
        "facts": ["attention", "encoder", "decoder", "vaswani"],
        "min_facts_match": 2,
        "canonical_answer": (
            "**Transformer** (Vaswani et al., 2017) — arsitektur neural network yang sepenuhnya "
            "berbasis attention mechanism (TIDAK pakai RNN/LSTM). Komponen utama: encoder stack "
            "+ decoder stack (atau decoder-only seperti GPT). Per-layer: multi-head self-attention "
            "→ feed-forward network → residual + layernorm. Pioneering work yang fondasinya "
            "dipakai semua LLM modern (GPT, BERT, Qwen, LLaMA, Claude). Paper: "
            "'Attention is All You Need' arxiv:1706.03762."
        ),
        "tier": "fact",
    },
    "rag": {
        "matchers": ["apa itu rag", "rag adalah", "retrieval augmented", "retrieval-augmented",
                     "rag dalam ai"],
        "facts": ["retrieval", "context", "knowledge"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**RAG = Retrieval-Augmented Generation** (Lewis et al., Meta AI, 2020) — paradigma "
            "AI yang gabung retrieval (search corpus eksternal) + generation (LLM). Flow: "
            "query → retrieve relevant docs (BM25/dense vector) → inject sebagai context → "
            "LLM generate jawaban grounded di retrieved context. Fix masalah halusinasi LLM "
            "dengan ground answers di sumber yang bisa dilacak. SIDIX implement RAG via "
            "BM25 corpus search + web_search tools."
        ),
        "tier": "fact",
    },
    "mighan": {
        "matchers": ["apa itu mighan", "mighan lab", "mighan adalah", "siapa mighan"],
        "facts": ["lab", "tiranyx", "ai"],
        "min_facts_match": 1,
        "canonical_answer": (
            "**Mighan Lab** — research arm di bawah Tiranyx (PT Tiranyx Digitalis Nusantara). "
            "Fokus: AI agent (SIDIX), 3D generation (Mighan-3D), creator platform (Ixonomic). "
            "Built by Fahmi Ghani sebagai counterpart kreatif untuk Tiranyx digital agency. "
            "Signature: AI yang self-hosted, open source, dan grounded di tradisi keilmuan "
            "(sanad chain, IHOS framework)."
        ),
        "tier": "fact",
    },
}


def detect_intent(question: str) -> QuestionIntent:
    """Classify question for routing & verification strategy."""
    q = (question or "").strip()
    q_lc = q.lower()

    # Check brand-specific FIRST (highest priority — must hit canonical)
    for term, spec in BRAND_CANON.items():
        if any(m in q_lc for m in spec["matchers"]):
            return QuestionIntent(primary="brand_specific", brand_term=term,
                                  is_factual=True, raw_question=q)

    # Current event detection
    if _CURRENT_EVENT_RE.search(q):
        return QuestionIntent(primary="current_event", is_factual=True, raw_question=q)

    # Coding intent
    coding_kw = ("tulis fungsi", "tulis function", "tulis kode", "buat kode", "write code",
                 "function", "def ", "class ", "implement", "algoritma", "algorithm",
                 "debug", "refactor", "compile", "syntax")
    if any(k in q_lc for k in coding_kw):
        return QuestionIntent(primary="coding", is_factual=True, raw_question=q)

    # Creative intent (caption, tagline, brainstorm, headline, copywrite)
    creative_kw = ("tagline", "caption", "headline", "copywrite", "copywriting",
                   "brainstorm", "ide kreatif", "naming brand", "campaign", "moodboard",
                   "puisi", "cerpen", "slogan")
    if any(k in q_lc for k in creative_kw):
        return QuestionIntent(primary="creative", is_factual=False, raw_question=q)

    # Generic factual fallback (definitions, explanations, "apa itu X")
    factual_starters = ("apa itu ", "apa kepanjangan", "berapa ", "kapan ",
                        "dimana ", "siapa ", "what is ", "explain ", "jelaskan ",
                        "definisi", "rumus")
    if any(q_lc.startswith(s) or f" {s}" in q_lc for s in factual_starters):
        return QuestionIntent(primary="factual", is_factual=True, raw_question=q)

    return QuestionIntent(primary="unknown", is_factual=False, raw_question=q)


# ════════════════════════════════════════════════════════════════════════
# 3. REQUIRED-SOURCES MAPPING
# ════════════════════════════════════════════════════════════════════════

def required_sources(intent: QuestionIntent) -> set[str]:
    """Tools yang WAJIB dipanggil sebelum jawab (anti LLM-only halu)."""
    if intent.primary == "current_event":
        return {"web_search"}
    if intent.primary == "brand_specific":
        return {"search_corpus"}
    if intent.primary == "factual":
        # Either web OR corpus is acceptable for stable factual
        return {"search_corpus_or_web"}
    if intent.primary == "coding":
        return set()  # LLM prior usually OK for syntax
    if intent.primary == "creative":
        return set()  # No factual constraint
    return set()


# ════════════════════════════════════════════════════════════════════════
# 4. CROSS-VERIFICATION
# ════════════════════════════════════════════════════════════════════════

def _facts_match_count(facts: list[str], text: str) -> int:
    """How many canonical facts (substring, lowercase) appear in text."""
    t = (text or "").lower()
    return sum(1 for f in facts if f.lower() in t)


def brand_canonical_answer(brand_term: str) -> Optional[str]:
    """Return canonical answer string for a known brand term, or None."""
    spec = BRAND_CANON.get(brand_term)
    return spec["canonical_answer"] if spec else None


def verify_brand_specific(intent: QuestionIntent, llm_answer: str,
                          sources: list[Source]) -> VerificationResult:
    """Brand questions MUST match canonical facts. Override LLM kalau halu."""
    spec = BRAND_CANON.get(intent.brand_term or "")
    if not spec:
        return VerificationResult(
            answer=llm_answer, confidence=0.5, epistemic_tier="unknown",
            sources=sources, reason="brand_term_not_in_canon",
        )

    matches = _facts_match_count(spec["facts"], llm_answer)
    threshold = spec["min_facts_match"]

    if matches >= threshold:
        return VerificationResult(
            answer=llm_answer, confidence=0.92, epistemic_tier=spec["tier"],
            sources=sources + [Source(name="brand_canon",
                                      text=spec["canonical_answer"],
                                      confidence=1.0)],
            reason=f"llm_matches_canon({matches}/{len(spec['facts'])})",
        )

    # LLM halu — override dengan canonical
    return VerificationResult(
        answer=spec["canonical_answer"],
        confidence=1.0, epistemic_tier=spec["tier"],
        sources=[Source(name="brand_canon", text=spec["canonical_answer"], confidence=1.0)],
        rejected_llm=True,
        conflict_flag=True,
        reason=f"llm_halu_overridden(matches={matches}<{threshold})",
    )


def verify_current_event(intent: QuestionIntent, llm_answer: str,
                         sources: list[Source]) -> VerificationResult:
    """Current event MUST have web_search source. Else mark UNKNOWN."""
    web_sources = [s for s in sources if s.name == "web_search" and s.text.strip()]
    if not web_sources:
        return VerificationResult(
            answer=("Saya belum punya data web terkini untuk menjawab pertanyaan ini "
                    "dengan akurat. Saya tidak akan menebak. Silakan coba lagi atau "
                    "tanya hal lain."),
            confidence=0.0, epistemic_tier="unknown",
            sources=sources, rejected_llm=True,
            reason="current_event_no_web_source",
        )

    # Have web source — return LLM answer with sanad chain
    # (Optional future: cross-check claim entities vs web text)
    return VerificationResult(
        answer=llm_answer, confidence=0.85, epistemic_tier="fact",
        sources=sources, reason="current_event_with_web_source",
    )


def verify_factual(intent: QuestionIntent, llm_answer: str,
                   sources: list[Source]) -> VerificationResult:
    """Stable factual: any retrieved source is acceptable backing."""
    backed = [s for s in sources if s.name in ("web_search", "search_corpus")
              and s.text.strip()]
    if not backed:
        return VerificationResult(
            answer=llm_answer, confidence=0.55, epistemic_tier="consensus",
            sources=sources,
            reason="factual_llm_only_no_backing",
        )
    return VerificationResult(
        answer=llm_answer, confidence=0.85, epistemic_tier="fact",
        sources=sources, reason="factual_with_backing",
    )


def verify_passthrough(intent: QuestionIntent, llm_answer: str,
                       sources: list[Source], tier: str = "consensus") -> VerificationResult:
    """Coding / creative — no strict factual gate."""
    return VerificationResult(
        answer=llm_answer, confidence=0.8,
        epistemic_tier="creative" if intent.primary == "creative" else tier,
        sources=sources, reason=f"passthrough_{intent.primary}",
    )


def verify_multisource(question: str, llm_answer: str,
                       sources: Optional[list[Source]] = None,
                       intent: Optional[QuestionIntent] = None) -> VerificationResult:
    """Main entry point — verify llm_answer against required sources by intent."""
    sources = sources or []
    intent = intent or detect_intent(question)

    if intent.primary == "brand_specific":
        return verify_brand_specific(intent, llm_answer, sources)
    if intent.primary == "current_event":
        return verify_current_event(intent, llm_answer, sources)
    if intent.primary == "factual":
        return verify_factual(intent, llm_answer, sources)
    if intent.primary == "coding":
        return verify_passthrough(intent, llm_answer, sources, tier="consensus")
    if intent.primary == "creative":
        return verify_passthrough(intent, llm_answer, sources, tier="creative")
    return verify_passthrough(intent, llm_answer, sources, tier="unknown")


# ════════════════════════════════════════════════════════════════════════
# 5. FORMAT SANAD CHAIN (untuk display ke user)
# ════════════════════════════════════════════════════════════════════════

def format_sanad_footer(result: VerificationResult) -> str:
    """Render sanad chain footer untuk transparansi sumber."""
    if not result.sources:
        return ""
    lines = ["\n\n— *Sanad (sumber)*:"]
    for i, s in enumerate(result.sources[:5], 1):
        if s.url:
            lines.append(f"  {i}. {s.name}: {s.url}")
        else:
            label = s.name.replace("_", " ")
            lines.append(f"  {i}. {label}")
    if result.conflict_flag:
        lines.append("  ⚠️ *Konflik antar sumber terdeteksi — jawaban di-override ke canonical.*")
    return "\n".join(lines)
