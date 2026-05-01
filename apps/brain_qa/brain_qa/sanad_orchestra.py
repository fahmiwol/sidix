"""
sanad_orchestra.py — Sanad Consensus Validation Engine (Sprint A)

Arsitektur:
  Sanad Orchestra = multi-source consensus validator untuk setiap output SIDIX.
  
  Flow:
    1. Extract claims dari answer (LLM-based + regex fallback)
    2. Verify each claim against sources (RAG + Web + Tools)
    3. Calculate consensus score (weighted by source reliability)
    4. Determine verdict: golden | pass | retry | fail
    5. Generate failure context untuk retry

  Integration:
    - Dipanggil oleh OmnyxDirector setelah synthesis
    - Hasil validation mempengaruhi Hafidz storage (golden vs lesson)

  Thresholds (relative, per query type):
    - simple factual (who/when/where): >= 0.92
    - analytical (how/why/comparison): >= 0.85
    - creative (opinion/design): >= 0.75
    - tool output (code/calc): >= 0.95

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger("sidix.sanad")


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class Claim:
    """A single factual claim extracted from an answer."""
    text: str
    confidence: float = 0.0  # extraction confidence
    verified: bool = False
    sources_supporting: list[str] = field(default_factory=list)
    sources_contradicting: list[str] = field(default_factory=list)
    verdict: str = "unverified"  # verified | unverified | contradicted


@dataclass
class ValidationResult:
    """Result from Sanad Orchestra validation."""
    consensus_score: float  # 0.0 - 1.0
    claims: list[Claim]
    verdict: str  # golden | pass | retry | fail
    metadata: dict  # per-claim details + summary
    failure_context: Optional[str] = None  # untuk retry bila verdict = retry/fail


# ── Thresholds ───────────────────────────────────────────────────────────

THRESHOLDS = {
    "simple": 0.92,
    "analytical": 0.85,
    "creative": 0.75,
    "tool_output": 0.95,
}


def get_threshold(complexity: str, tools_used: list[str]) -> float:
    """Get validation threshold based on query complexity and tools used."""
    # Tool output (code/calc) gets highest threshold
    if any(t in ("calculator", "code_sandbox") for t in tools_used):
        return THRESHOLDS["tool_output"]
    return THRESHOLDS.get(complexity, THRESHOLDS["analytical"])


# ── Claim Extraction ─────────────────────────────────────────────────────

CLAIM_EXTRACTION_PROMPT = """Kamu adalah Sanad Extractor — sistem ekstraksi klaim faktual dari teks.

Tugas:
1. Baca teks jawaban di bawah
2. Ekstrak SEMUA klaim faktual (bukan opini, bukan spekulasi)
3. Untuk setiap klaim, berikan confidence (0.0-1.0)

Format output (JSON):
{
  "claims": [
    {"text": "klaim faktual 1", "confidence": 0.95},
    {"text": "klaim faktual 2", "confidence": 0.80}
  ]
}

Rules:
- Klaim faktual = statement yang bisa diverifikasi secara objektif
- Skip opini, saran, pertanyaan retoris, meta-commentary
- Confidence tinggi untuk data konkret (nama, tanggal, angka)
- Confidence rendah untuk generalisasi atau inferensi

Teks jawaban:
{answer}
"""


def _extract_claims_regex(answer: str) -> list[Claim]:
    """Fallback claim extraction using regex heuristics."""
    claims = []
    
    # Pattern: named entities (capitalized sequences)
    entity_pattern = r'[A-Z][a-zA-Z\s]{2,50}(?:\s+[A-Z][a-zA-Z]+){0,3}'
    entities = re.findall(entity_pattern, answer)
    
    # Pattern: dates
    date_pattern = r'\b\d{1,2}\s+(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember|\d{1,2})\s+\d{4}\b'
    dates = re.findall(date_pattern, answer, re.I)
    
    # Pattern: numbers with units
    number_pattern = r'\b\d{1,3}(?:[.,]\d+)?\s*(?:juta|miliar|ribu|persen|%|kg|meter|km|tahun|bulan)\b'
    numbers = re.findall(number_pattern, answer, re.I)
    
    # Sentences containing entities
    sentences = re.split(r'(?<=[.!?])\s+', answer)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20 or len(sent) > 300:
            continue
        # Check if sentence contains verifiable content
        has_entity = any(e in sent for e in entities[:10])
        has_date = any(d in sent for d in dates[:5])
        has_number = any(n in sent for n in numbers[:5])
        if has_entity or has_date or has_number:
            claims.append(Claim(text=sent, confidence=0.6))
    
    return claims[:10]  # limit to top 10


async def _extract_claims_llm(answer: str) -> list[Claim]:
    """Extract claims using LLM."""
    try:
        import asyncio
        from .ollama_llm import ollama_generate
        prompt = CLAIM_EXTRACTION_PROMPT.format(answer=answer[:3000])
        response, _mode = await asyncio.to_thread(
            ollama_generate, prompt, system="", model="qwen2.5:1.5b", max_tokens=800, temperature=0.1
        )
        
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                claims = []
                for c in data.get("claims", []):
                    claims.append(Claim(
                        text=c.get("text", ""),
                        confidence=c.get("confidence", 0.5)
                    ))
                return claims
            except json.JSONDecodeError as e:
                log.debug("[sanad] JSON parse failed: %s", e)
    except Exception as e:
        log.warning("[sanad] LLM claim extraction failed: %s", e)
    
    return []


async def extract_claims(answer: str) -> list[Claim]:
    """Extract claims from answer (LLM + regex fallback)."""
    claims = await _extract_claims_llm(answer)
    if not claims:
        claims = _extract_claims_regex(answer)
    log.info("[sanad] Extracted %d claims", len(claims))
    return claims


# ── Claim Verification ───────────────────────────────────────────────────

async def _verify_claim_corpus(claim: Claim, query: str) -> bool:
    """Verify claim against local corpus."""
    try:
        from .corpus_search import search as corpus_search
        results = corpus_search(claim.text[:100], top_k=3)
        if results and len(results) > 0:
            # Check if corpus supports the claim
            for r in results:
                content = str(r).lower()
                claim_keywords = set(re.findall(r'\w{3,}', claim.text.lower()))
                matched = sum(1 for kw in claim_keywords if kw in content)
                if matched >= len(claim_keywords) * 0.5:
                    claim.sources_supporting.append("corpus")
                    return True
    except Exception as e:
        log.debug("[sanad] Corpus verification failed: %s", e)
    return False


async def _verify_claim_web(claim: Claim, query: str) -> bool:
    """Verify claim against web search."""
    try:
        from .mojeek_search import mojeek_search_async
        hits = await mojeek_search_async(claim.text[:100], max_results=3)
        if hits and len(hits) > 0:
            claim.sources_supporting.append("web")
            return True
    except Exception as e:
        log.debug("[sanad] Web verification failed: %s", e)
    return False


async def _verify_claim_tools(claim: Claim, tools_used: list[str], tool_outputs: list[dict]) -> bool:
    """Verify claim against tool outputs."""
    if not tool_outputs:
        return False
    
    claim_text_lower = claim.text.lower()
    for i, output in enumerate(tool_outputs):
        if not output:
            continue
        output_str = json.dumps(output, default=str).lower()
        # Check if claim is supported by tool output
        claim_keywords = set(re.findall(r'\w{3,}', claim_text_lower))
        matched = sum(1 for kw in claim_keywords if kw in output_str)
        if matched >= len(claim_keywords) * 0.3:
            tool_name = tools_used[i] if i < len(tools_used) else f"tool_{i}"
            claim.sources_supporting.append(tool_name)
            return True
    return False


async def verify_claim(
    claim: Claim,
    query: str,
    sources: dict[str, Any],
    tools_used: list[str],
    tool_outputs: list[dict],
) -> Claim:
    """Verify a single claim against all available sources."""
    # Corpus verification
    corpus_result = sources.get("corpus")
    if corpus_result:
        await _verify_claim_corpus(claim, query)
    
    # Web verification
    web_result = sources.get("web")
    if web_result:
        await _verify_claim_web(claim, query)
    
    # Tool verification
    if tools_used and tool_outputs:
        await _verify_claim_tools(claim, tools_used, tool_outputs)
    
    # Determine verdict
    if len(claim.sources_supporting) >= 2:
        claim.verified = True
        claim.verdict = "verified"
    elif len(claim.sources_supporting) == 1:
        claim.verified = True
        claim.verdict = "partial"
    else:
        claim.verified = False
        claim.verdict = "unverified"
    
    return claim


# ── Consensus Calculation ────────────────────────────────────────────────

def calculate_consensus(claims: list[Claim]) -> float:
    """Calculate overall consensus score from claims."""
    if not claims:
        return 0.5  # neutral if no claims extracted
    
    total_weight = 0.0
    total_score = 0.0
    
    for claim in claims:
        # Weight by extraction confidence
        weight = claim.confidence
        
        # Score based on verification
        if claim.verdict == "verified":
            score = 1.0
        elif claim.verdict == "partial":
            score = 0.6
        elif claim.verdict == "unverified":
            score = 0.2
        else:
            score = 0.0
        
        total_score += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.5
    
    return total_score / total_weight


def determine_verdict(consensus_score: float, threshold: float, claims: list[Claim]) -> str:
    """Determine validation verdict."""
    if consensus_score >= threshold + 0.05:
        return "golden"
    elif consensus_score >= threshold:
        return "pass"
    elif consensus_score >= threshold * 0.7:
        return "retry"
    else:
        return "fail"


def generate_failure_context(claims: list[Claim], consensus_score: float, threshold: float) -> str:
    """Generate context for retry/fail cases."""
    unverified = [c for c in claims if c.verdict in ("unverified", "contradicted")]
    if not unverified:
        return f"Consensus score {consensus_score:.2f} below threshold {threshold:.2f}. General quality issue."
    
    lines = [f"Consensus score {consensus_score:.2f} below threshold {threshold:.2f}. Unverified claims:"]
    for c in unverified[:5]:
        lines.append(f"  - \"{c.text[:100]}...\" (confidence: {c.confidence:.2f})")
    
    return "\n".join(lines)


# ── Sanad Orchestra ──────────────────────────────────────────────────────

class SanadOrchestra:
    """Multi-source consensus validation for SIDIX outputs."""
    
    def __init__(self):
        self.stats = {"validations": 0, "golden": 0, "pass": 0, "retry": 0, "fail": 0}
    
    async def validate(
        self,
        answer: str,
        query: str,
        sources: dict[str, Any],
        persona: str,
        tools_used: list[str],
        tool_outputs: list[dict],
        complexity: str = "analytical",
    ) -> ValidationResult:
        """Validate an answer against all available sources.
        
        Args:
            answer: The generated answer to validate
            query: Original user query
            sources: Dict of source results (corpus, web, dense, persona, tools)
            persona: Persona that generated the answer
            tools_used: List of tool names used
            tool_outputs: List of tool output dicts
            complexity: Query complexity (simple/analytical/creative)
        
        Returns:
            ValidationResult with consensus score, claims, and verdict
        """
        log.info("[sanad] Starting validation for query: %r", query[:60])
        
        # Step 1: Extract claims
        claims = await extract_claims(answer)
        
        # Step 2: Verify each claim
        verified_claims = []
        for claim in claims:
            verified = await verify_claim(claim, query, sources, tools_used, tool_outputs)
            verified_claims.append(verified)
        
        # Step 3: Calculate consensus
        consensus_score = calculate_consensus(verified_claims)
        
        # Step 4: Determine threshold and verdict
        threshold = get_threshold(complexity, tools_used)
        verdict = determine_verdict(consensus_score, threshold, verified_claims)
        
        # Step 5: Generate failure context if needed
        failure_context = None
        if verdict in ("retry", "fail"):
            failure_context = generate_failure_context(verified_claims, consensus_score, threshold)
        
        # Update stats
        self.stats["validations"] += 1
        self.stats[verdict] = self.stats.get(verdict, 0) + 1
        
        log.info(
            "[sanad] Validation complete: score=%.2f threshold=%.2f verdict=%s claims=%d",
            consensus_score, threshold, verdict, len(claims),
        )
        
        return ValidationResult(
            consensus_score=consensus_score,
            claims=verified_claims,
            verdict=verdict,
            metadata={
                "threshold": threshold,
                "complexity": complexity,
                "tools_used": tools_used,
                "persona": persona,
                "n_claims": len(claims),
                "n_verified": sum(1 for c in verified_claims if c.verdict == "verified"),
                "n_partial": sum(1 for c in verified_claims if c.verdict == "partial"),
                "n_unverified": sum(1 for c in verified_claims if c.verdict == "unverified"),
            },
            failure_context=failure_context,
        )
    
    def get_stats(self) -> dict:
        """Return validation statistics."""
        total = self.stats["validations"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "golden_rate": self.stats["golden"] / total,
            "pass_rate": self.stats["pass"] / total,
            "retry_rate": self.stats["retry"] / total,
            "fail_rate": self.stats["fail"] / total,
        }


# ── Public API ───────────────────────────────────────────────────────────

async def validate_answer(
    answer: str,
    query: str,
    sources: dict[str, Any],
    persona: str = "UTZ",
    tools_used: list[str] = None,
    tool_outputs: list[dict] = None,
    complexity: str = "analytical",
) -> ValidationResult:
    """Convenience function for one-off validation."""
    orchestra = SanadOrchestra()
    return await orchestra.validate(
        answer=answer,
        query=query,
        sources=sources,
        persona=persona,
        tools_used=tools_used or [],
        tool_outputs=tool_outputs or [],
        complexity=complexity,
    )
