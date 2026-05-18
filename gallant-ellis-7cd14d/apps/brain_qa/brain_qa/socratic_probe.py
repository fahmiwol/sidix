"""
socratic_probe.py — Socratic Probe / Islamic Pedagogy Mode

Inspired by: Socratic method + Islamic pedagogy (tarbiyah / talqih).
SIDIX tidak langsung menjawab — tapi menanyakan pertanyaan klarifikasi
untuk membantu user menemukan jawaban sendiri.

Use case:
- User bertanya hal yang terlalu umum / ambigu
- User butuh pemahaman mendalam (bukan hanya jawaban)
- Mode pembelajaran aktif (active learning)

Jiwa Sprint 4 (Kimi) — 2026-04-25
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Probe Decision ───────────────────────────────────────────────────────────

class ProbeDecision(str, Enum):
    ANSWER_DIRECTLY = "answer"       # pertanyaan cukup jelas, jawab langsung
    CLARIFY_FIRST = "clarify"        # perlu klarifikasi sebelum jawab
    SOCRATIC_GUIDE = "socratic"      # mode socratic — tanya balik


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SocraticProbe:
    """Hasil analisis: apakah perlu probe, dan kalau ya, pertanyaan apa."""
    decision: ProbeDecision
    reason: str = ""
    clarifying_questions: list[str] = field(default_factory=list)
    suggested_angle: str = ""          # angle yang mungkin user cari
    confidence: float = 0.0            # confidence bahwa probe tepat


# ── Heuristic detectors ──────────────────────────────────────────────────────

# Pertanyaan yang terlalu umum / butuh klarifikasi
_VAGUE_PATTERNS = [
    (r"^\s*(apa|bagaimana|mengapa)\s+(itu|ini|mereka|hal tersebut)\s*\?*$", 0.7),
    (r"\bjelaskan\s+semuanya\b", 0.8),
    (r"\btolong\s+jelaskan\s+(tentang|mengenai)\s+\w+\b.*\b(secara|dari|sejarah)\s+(lengkap|detail|mendalam)", 0.6),
    (r"\bkenapa\b(?!\s+orang)", 0.4),  # standalone "kenapa" (but not "kenapa orang")
    (r"\bkenapa\s+orang\b", 0.5),
    (r"\bapa\s+pendapatmu\s+tentang\s+\w+\b", 0.4),
]

# Pertanyaan yang jawabannya sangat tergantung konteks
_CONTEXT_DEPENDENT = [
    (r"\b(baik|buruk|benar|salah|terbaik|terburuk)\b", 0.5),
    (r"\b(harus|wajib|sebaiknya|dianjurkan)\b", 0.5),
    (r"\b(rekomendasi|saran|nasihat)\b", 0.4),
]

# Pertanyaan yang cocok untuk Socratic method (learning questions)
_LEARNING_MARKERS = [
    (r"\b(mengapa|kenapa|why)\b.*\b(begitu|demikian|itu|seperti itu)\b", 0.6),
    (r"\b(bagaimana|how)\b.*\b(cara|proses|kerja|mechanism)\b", 0.5),
    (r"\b(apa|what)\b.*\b(beda|perbedaan|difference|distinction)\b", 0.5),
    (r"\b(apa|what)\b.*\b(arti|makna|meaning|significance)\b", 0.4),
]

# Pertanyaan yang jelas — tidak perlu probe
_CLEAR_PATTERNS = [
    (r"\b(berapa|how many|how much|what is the value)\b", -0.6),
    (r"\b(definisi|definition|arti kata)\b", -0.5),
    (r"\b(kode|code|syntax|error|deploy|fastapi|docker|javascript|python)\b.*\b(bagaimana|how|apa|what|cara)\b", -0.5),
    (r"\b(bagaimana|cara)\b.*\b(kode|code|deploy|fastapi|docker|javascript|python|vps|server)\b", -0.5),
    (r"\btranslate|terjemahkan|convert|konversi\b", -0.5),
]

# Jarak minimal karakter untuk pertanyaan yang "terlalu pendek"
_MIN_CHARS_FOR_CLEAR = 15


# ── Core function ────────────────────────────────────────────────────────────

def analyze_question(
    question: str,
    conversation_history: list[str] | None = None,
    persona: str = "AYMAN",
) -> SocraticProbe:
    """
    Analisis pertanyaan user: apakah perlu Socratic Probe?

    Returns SocraticProbe dengan decision + clarifying questions.
    """
    q = (question or "").strip()
    if not q:
        return SocraticProbe(
            decision=ProbeDecision.CLARIFY_FIRST,
            reason="Pertanyaan kosong",
            clarifying_questions=["Ada yang bisa saya bantu?"],
            confidence=1.0,
        )

    # Score accumulation
    score = 0.0
    reasons: list[str] = []

    q_lower = q.lower()

    # Check vague patterns
    for pattern, weight in _VAGUE_PATTERNS:
        if re.search(pattern, q_lower):
            score += weight
            reasons.append(f"vague_pattern: +{weight}")

    # Check context-dependent
    for pattern, weight in _CONTEXT_DEPENDENT:
        if re.search(pattern, q_lower):
            score += weight
            reasons.append(f"context_dependent: +{weight}")

    # Check learning markers (positive for socratic)
    for pattern, weight in _LEARNING_MARKERS:
        if re.search(pattern, q_lower):
            score += weight
            reasons.append(f"learning_marker: +{weight}")

    # Check clear patterns (negative for probe)
    for pattern, weight in _CLEAR_PATTERNS:
        if re.search(pattern, q_lower):
            score += weight
            reasons.append(f"clear_pattern: {weight}")

    # Too short = might need clarification
    if len(q) < _MIN_CHARS_FOR_CLEAR:
        score += 0.3
        reasons.append(f"too_short: +0.3")

    # Conversation depth — deeper conversation = less need to probe
    depth = len(conversation_history) if conversation_history else 0
    if depth >= 3:
        score -= 0.3
        reasons.append(f"deep_conversation: -0.3")

    # Persona-based adjustments
    # ALEY (researcher) and OOMAR (strategist) → more likely to probe for rigor
    if persona.upper() in ("ALEY", "OOMAR"):
        score += 0.2
        reasons.append(f"persona_rigor: +0.2")
    # AYMAN (general) and UTZ (creative) → less likely to probe, more direct
    elif persona.upper() in ("AYMAN", "UTZ"):
        score -= 0.2
        reasons.append(f"persona_casual: -0.2")

    # Normalize confidence
    confidence = min(1.0, max(0.0, abs(score) + 0.3))

    # Decision boundary
    if score >= 0.6:
        decision = ProbeDecision.SOCRATIC_GUIDE
        clarifying = _generate_socratic_questions(q, q_lower)
    elif score >= 0.3:
        decision = ProbeDecision.CLARIFY_FIRST
        clarifying = _generate_clarifying_questions(q, q_lower)
    else:
        decision = ProbeDecision.ANSWER_DIRECTLY
        clarifying = []

    reason_str = f"score={score:.2f}; " + "; ".join(reasons)

    return SocraticProbe(
        decision=decision,
        reason=reason_str,
        clarifying_questions=clarifying,
        suggested_angle=_infer_angle(q_lower),
        confidence=confidence,
    )


def _generate_socratic_questions(question: str, q_lower: str) -> list[str]:
    """Generate Socratic-style guiding questions."""
    questions: list[str] = []

    if re.search(r"\b(mengapa|kenapa|why)\b", q_lower):
        questions.append("Apa yang membuat kamu penasaran tentang hal ini?")
        questions.append("Apakah ada asumsi dasar yang perlu kita periksa bersama?")

    if "bagaimana" in q_lower or "how" in q_lower:
        questions.append("Dari sudut pandang mana kamu ingin memahami ini?")
        questions.append("Apa tujuan akhir yang ingin kamu capai?")

    if "apa" in q_lower or "what" in q_lower:
        questions.append("Apa yang sudah kamu ketahui tentang topik ini?")
        questions.append("Apa konteks atau situasi spesifik yang kamu hadapi?")

    if "perbedaan" in q_lower or "difference" in q_lower or "beda" in q_lower:
        questions.append("Apa persamaan dasar antara keduanya yang sudah kamu pahami?")
        questions.append("Dari dimensi mana kamu ingin membandingkan?")

    # Fallback generic socratic questions
    if not questions:
        questions = [
            "Bisa ceritakan lebih detail tentang apa yang kamu cari?",
            "Apa konteks atau tujuan di balik pertanyaan ini?",
        ]

    return questions[:3]


def _generate_clarifying_questions(question: str, q_lower: str) -> list[str]:
    """Generate simple clarifying questions."""
    questions: list[str] = []

    if len(question) < 20:
        questions.append("Bisa diperjelas maksud pertanyaanmu?")

    if re.search(r"\b(terbaik|terburuk|paling|best|worst)\b", q_lower):
        questions.append("Dari segi apa — kualitas, harga, durasi, atau yang lain?")

    if re.search(r"\b(harus|wajib|sebaiknya|should|must)\b", q_lower):
        questions.append("Untuk situasi atau konteks seperti apa?")

    if not questions:
        questions = [
            "Bisa berikan lebih banyak detail?",
            "Apa yang sudah kamu coba atau ketahui sejauh ini?",
        ]

    return questions[:2]


def _infer_angle(q_lower: str) -> str:
    """Infer what angle the user might be looking for."""
    if "teori" in q_lower or "theory" in q_lower:
        return "theoretical"
    if "praktis" in q_lower or "practical" in q_lower or "cara" in q_lower:
        return "practical"
    if "sejarah" in q_lower or "history" in q_lower:
        return "historical"
    if "contoh" in q_lower or "example" in q_lower:
        return "example-based"
    return "general"


# ── Convenience API ──────────────────────────────────────────────────────────

def should_probe(question: str, persona: str = "AYMAN") -> bool:
    """One-shot: should SIDIX ask clarifying question instead of answering?"""
    result = analyze_question(question, persona=persona)
    return result.decision != ProbeDecision.ANSWER_DIRECTLY


def get_probe_response(question: str, persona: str = "AYMAN") -> dict:
    """One-shot: get full probe result as dict for API."""
    result = analyze_question(question, persona=persona)
    return {
        "probe": result.decision.value,
        "reason": result.reason,
        "questions": result.clarifying_questions,
        "angle": result.suggested_angle,
        "confidence": round(result.confidence, 2),
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Socratic Probe Self-Test ===\n")

    test_cases = [
        ("Kenapa begitu?", "AYMAN"),
        ("Apa perbedaan antara AI dan ML?", "ALEY"),
        ("Bagaimana cara deploy FastAPI?", "ABOO"),
        ("Translate 'hello' ke Indonesia", "AYMAN"),
        ("Apa itu fotosintesis?", "UTZ"),
        ("Jelaskan semuanya tentang ekonomi Islam secara lengkap", "OOMAR"),
        ("Berapa 2+2?", "AYMAN"),
        ("Apa pendapatmu tentang politik?", "AYMAN"),
    ]

    for q, persona in test_cases:
        result = analyze_question(q, persona=persona)
        print(f"Q: {q}")
        print(f"  Persona: {persona} | Decision: {result.decision.value} | Confidence: {result.confidence:.2f}")
        if result.clarifying_questions:
            print(f"  Questions: {' | '.join(result.clarifying_questions)}")
        print()

    print("[OK] Self-test complete")
