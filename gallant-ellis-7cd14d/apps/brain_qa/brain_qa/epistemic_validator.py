"""
epistemic_validator.py — Pemastian 4-Label Epistemik di Output SIDIX
=====================================================================

Konsep dari SIDIX_BIBLE.md (Pasal "4-Label Epistemic"):
  [FACT]        — ada sumber primer terverifikasi (sanad lengkap)
  [OPINION]     — reasoning dari fakta, diklaim sebagai pendapat
  [SPECULATION] — dugaan/hipotesis, ditandai jelas
  [UNKNOWN]     — jujur akui tidak tahu

Fungsi modul ini:
  1. validate_output(text) → score 0-1 + warnings (label coverage)
  2. inject_default_labels(text) → tambahkan label heuristik bila tidak ada
  3. extract_claims(text) → list claim + label-nya (untuk audit)

Filosofi: SIDIX harus terlihat JUJUR di setiap output. Lebih baik akui
[UNKNOWN] daripada halusinasi percaya diri.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from typing import Optional


# ── Detection Patterns ────────────────────────────────────────────────────────

_LABEL_PATTERN = re.compile(r"\[(FACT|OPINION|SPECULATION|UNKNOWN)\]", re.IGNORECASE)

# Heuristik kuat → kalau muncul tanpa label, kemungkinan SPECULATION
_SPECULATION_HINTS = [
    r"\bmungkin\b", r"\bsepertinya\b", r"\bbisa jadi\b", r"\bkayaknya\b",
    r"\bperhaps\b", r"\bmaybe\b", r"\blikely\b", r"\bdiduga\b", r"\bkira-kira\b",
]
_SPECULATION_RE = re.compile("|".join(_SPECULATION_HINTS), re.IGNORECASE)

# Heuristik kuat → kalau muncul, kemungkinan OPINION
_OPINION_HINTS = [
    r"\bmenurut saya\b", r"\bsaya rasa\b", r"\bsaya pikir\b", r"\bI think\b",
    r"\bmenurutku\b", r"\bsejauh yang saya tahu\b", r"\bdari sudut pandang\b",
    r"\bmenurut\s+(SIDIX|aku|kami)\b",
]
_OPINION_RE = re.compile("|".join(_OPINION_HINTS), re.IGNORECASE)

# Heuristik kuat → kalau muncul, kemungkinan FACT (claim faktual)
_FACT_HINTS = [
    r"\b(adalah|merupakan|disebut|didefinisikan)\b",
    r"\b(dipublikasikan|dirilis|ditemukan)\s+pada\b",
    r"\b(menurut|sumber)\s+\S+",
]
_FACT_RE = re.compile("|".join(_FACT_HINTS), re.IGNORECASE)

# Heuristik UNKNOWN
_UNKNOWN_HINTS = [
    r"\btidak tahu\b", r"\btidak yakin\b", r"\bbelum ada data\b",
    r"\bI don'?t know\b", r"\bSIDIX belum punya data\b",
    r"\bperlu riset lebih lanjut\b",
]
_UNKNOWN_RE = re.compile("|".join(_UNKNOWN_HINTS), re.IGNORECASE)


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class EpistemicReport:
    """Hasil validasi epistemik satu output."""
    has_any_label:   bool
    label_counts:    dict             # {FACT: n, OPINION: n, ...}
    coverage_ratio:  float            # paragraf yang punya label / total paragraf
    warnings:        list[str] = field(default_factory=list)
    suggestions:     list[str] = field(default_factory=list)
    auto_tagged:     bool = False
    score:           float = 0.0      # 0..1

    def to_dict(self) -> dict:
        return asdict(self)


# ── Public API ────────────────────────────────────────────────────────────────

def validate_output(text: str, strict: bool = False) -> EpistemicReport:
    """
    Validasi 4-label epistemik di teks output.

    Args:
        text: output text yang mau divalidasi
        strict: kalau True, paragraf tanpa label = warning
    """
    if not text or len(text.strip()) < 30:
        return EpistemicReport(
            has_any_label=False,
            label_counts={"FACT": 0, "OPINION": 0, "SPECULATION": 0, "UNKNOWN": 0},
            coverage_ratio=0.0,
            warnings=["text too short to validate"],
            score=0.5,
        )

    # Hitung label
    matches = _LABEL_PATTERN.findall(text)
    counts = {"FACT": 0, "OPINION": 0, "SPECULATION": 0, "UNKNOWN": 0}
    for m in matches:
        key = m.upper()
        counts[key] = counts.get(key, 0) + 1

    has_any = sum(counts.values()) > 0

    # Hitung coverage per paragraph
    paragraphs = [p for p in text.split("\n\n") if p.strip() and len(p) > 60]
    para_with_label = sum(1 for p in paragraphs if _LABEL_PATTERN.search(p))
    coverage = (para_with_label / max(1, len(paragraphs)))

    warnings: list[str] = []
    suggestions: list[str] = []

    if not has_any:
        warnings.append("output sama sekali tanpa label epistemik [FACT/OPINION/SPECULATION/UNKNOWN]")
        suggestions.append("tambahkan minimal 1 label per claim faktual atau opini")

    if strict and coverage < 0.5:
        warnings.append(f"coverage rendah: hanya {para_with_label}/{len(paragraphs)} paragraf punya label")

    # Cek hint tanpa label sekitarnya
    hint_warnings = _scan_unlabeled_hints(text)
    warnings.extend(hint_warnings)

    # Score: 0 (tidak ada label sama sekali) → 1 (semua paragraf punya label)
    score = 0.5 + 0.5 * coverage if has_any else 0.2

    return EpistemicReport(
        has_any_label=has_any,
        label_counts=counts,
        coverage_ratio=round(coverage, 3),
        warnings=warnings,
        suggestions=suggestions,
        score=round(score, 3),
    )


def inject_default_labels(text: str, default: str = "OPINION") -> tuple[str, bool]:
    """
    Tambahkan label default ke paragraf yang tidak punya label sama sekali.
    Heuristik: cek hint dulu — kalau ada hint OPINION/SPECULATION/UNKNOWN/FACT,
    pakai itu. Kalau tidak ada, pakai `default`.

    Returns: (modified_text, was_modified)
    """
    if not text or len(text.strip()) < 30:
        return text, False

    paragraphs = text.split("\n\n")
    modified = False
    out_paragraphs: list[str] = []

    for p in paragraphs:
        s = p.strip()
        if not s or len(s) < 60:
            out_paragraphs.append(p)
            continue
        if _LABEL_PATTERN.search(s):
            out_paragraphs.append(p)
            continue
        # Heuristik label
        if _UNKNOWN_RE.search(s):
            label = "UNKNOWN"
        elif _SPECULATION_RE.search(s):
            label = "SPECULATION"
        elif _OPINION_RE.search(s):
            label = "OPINION"
        elif _FACT_RE.search(s):
            label = "FACT"
        else:
            label = default
        # Tag di awal paragraf
        out_paragraphs.append(f"[{label}] {p}")
        modified = True

    return "\n\n".join(out_paragraphs), modified


def extract_claims(text: str) -> list[dict]:
    """
    Ekstrak setiap paragraf + label yang dipakai (untuk audit).
    Returns list of {paragraph_index, snippet, label, has_source_hint}
    """
    out: list[dict] = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for i, p in enumerate(paragraphs):
        m = _LABEL_PATTERN.search(p)
        label = m.group(1).upper() if m else None
        has_source = bool(re.search(r"\(menurut\s+\S+\)|\[(.*?:.*?)\]|sumber:|source:", p, re.IGNORECASE))
        out.append({
            "paragraph_index": i,
            "snippet": p[:200] + ("…" if len(p) > 200 else ""),
            "label": label,
            "has_source_hint": has_source,
        })
    return out


# ── Helpers ────────────────────────────────────────────────────────────────────

def _scan_unlabeled_hints(text: str) -> list[str]:
    """Cari hint yang harus punya label tapi tidak ada label di paragraf yang sama."""
    warnings: list[str] = []
    paragraphs = text.split("\n\n")
    for i, p in enumerate(paragraphs):
        if _LABEL_PATTERN.search(p):
            continue
        if _SPECULATION_RE.search(p):
            warnings.append(f"paragraf #{i+1} mengandung hint spekulasi tapi tidak ada label [SPECULATION]")
        if _OPINION_RE.search(p) and "saya" not in p.lower()[:20]:
            warnings.append(f"paragraf #{i+1} mengandung hint opini tapi tidak ada label [OPINION]")
        if _UNKNOWN_RE.search(p):
            warnings.append(f"paragraf #{i+1} mengandung hint ketidaktahuan tapi tidak ada label [UNKNOWN]")
    return warnings[:5]   # cap warning


# ── Prompt Snippet untuk Injeksi ke System Prompt ─────────────────────────────

EPISTEMIC_PROMPT_RULE = """
ATURAN EPISTEMIK WAJIB (4-LABEL):
Setiap claim di output kamu HARUS diberi salah satu label berikut di awal paragraf
atau di awal kalimat:
  [FACT]        — ada sumber yang bisa diverifikasi (sebut sumbernya)
  [OPINION]     — pendapat kamu sendiri / reasoning dari fakta
  [SPECULATION] — dugaan/hipotesis, belum ada bukti kuat
  [UNKNOWN]     — kamu tidak tahu / belum punya data cukup

Lebih baik tulis [UNKNOWN] daripada mengarang. Kalau tidak yakin, [SPECULATION].
Identitas SIDIX = Shiddiq (jujur) + Al-Amin (terpercaya) — ini tidak boleh kompromi.
"""
