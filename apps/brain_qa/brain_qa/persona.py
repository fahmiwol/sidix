from __future__ import annotations

from dataclasses import dataclass
import re


Persona = str  # "ABOO" | "OOMAR" | "AYMAN" | "ALEY" | "UTZ"

# Pemetaan nama persona lama → baru (untuk backward-compat migration)
# Lama: MIGHAN/TOARD/FACH/HAYFAR/INAN — diganti 2026-04-23
_PERSONA_ALIAS: dict[str, str] = {
    "MIGHAN": "AYMAN",
    "TOARD":  "ABOO",
    "FACH":   "OOMAR",
    "HAYFAR": "ALEY",
    "INAN":   "UTZ",
}

@dataclass(frozen=True)
class PersonaDecision:
    persona: Persona
    reason: str
    confidence: float
    scores: dict[str, int]


_PERSONA_SET = {"ABOO", "OOMAR", "AYMAN", "ALEY", "UTZ"}


def normalize_persona(p: str | None) -> Persona | None:
    if p is None:
        return None
    s = p.strip().upper()
    # Terjemahkan nama lama secara otomatis (backward compat)
    s = _PERSONA_ALIAS.get(s, s)
    if s in _PERSONA_SET:
        return s
    raise ValueError(f"Unknown persona: {p}. Use one of: {', '.join(sorted(_PERSONA_SET))}")


_CODING_RE = re.compile(
    r"\b("
    r"code|coding|bug|debug|error|stack\s*trace|exception|traceback|"
    r"refactor|typescript|javascript|python|node|npm|pnpm|yarn|"
    r"build|compile|test|unit\s*test|e2e|lint|eslint|"
    r"repo|git|commit|merge|branch"
    r")\b",
    re.I,
)
_CREATIVE_RE = re.compile(
    r"\b("
    r"design|desain|gambar|image|poster|logo|branding|caption|marketing|"
    r"video|edit\s*video|creative|copywriting|tone|voice|tagline|headline"
    r")\b",
    re.I,
)
_RESEARCH_RE = re.compile(
    r"\b("
    r"riset|research|tesis|thesis|paper|journal|doi|isbn|metodologi|literatur|"
    r"analisis\s*data|dataset|benchmark|statistik|hypothesis|abstrak|"
    r"sitasi|citation|bibliography|review\s*literature|systematic"
    r")\b",
    re.I,
)
_PLAN_RE = re.compile(
    r"\b("
    r"rencana|plan|roadmap|arsitektur|architecture|strategi|brainstorm|ideate|"
    r"framework|sistem|proposal|scope|milestone|timeline|prioritas|prioritization"
    r")\b",
    re.I,
)

_EXPLICIT_PREFIX_RE = re.compile(r"^\s*(aboo|oomar|ayman|aley|utz|toard|fach|mighan|hayfar|inan)\s*:\s*", re.I)


def _score_persona(question: str) -> dict[str, int]:
    q = question.strip()
    scores = {p: 0 for p in _PERSONA_SET}

    m = _EXPLICIT_PREFIX_RE.match(q)
    if m:
        raw = m.group(1).upper()
        # Terjemahkan nama lama ke baru kalau user ketik nama lama
        forced = _PERSONA_ALIAS.get(raw, raw)
        if forced in scores:
            scores[forced] += 100
        return scores

    # Pivot 2026-04-25: ALIGNED dengan cot_system_prompts.py persona descriptions.
    # Sebelumnya mapping di file ini conflict dengan PERSONA_DESCRIPTIONS —
    # sekarang disinkronkan dengan research_notes/208_pivot_liberation_sprint.md.

    # ABOO = engineer / technical / coding
    if _CODING_RE.search(q):
        scores["ABOO"] += 3
    # UTZ = creative / design / content
    if _CREATIVE_RE.search(q):
        scores["UTZ"] += 3
    # ALEY = research / academic / analysis
    if _RESEARCH_RE.search(q):
        scores["ALEY"] += 3
    # OOMAR = strategic / planning / business
    if _PLAN_RE.search(q):
        scores["OOMAR"] += 3
    # Stronger bias kalau ada kata explicit "strategi/strategy/bisnis/startup"
    # — menang atas UTZ (creative) di overlap kasus ("strategi marketing startup")
    if re.search(r"\b(strategi|strategy|bisnis|business|startup|B2B|B2C|saas|go-to-market|gtm)\b", q, re.I):
        scores["OOMAR"] += 2

    # Singkat/casual bias → AYMAN (general hangat), bukan UTZ (creative)
    if re.search(r"\b(cepet|cepat|singkat|ringkas|tl;dr|tldr)\b", q, re.I):
        scores["AYMAN"] += 1

    # Islamic topics → AYMAN (hangat, bisa ngobrol fiqh casual)
    if re.search(
        r"\b(islam|fiqh|syariah|sholat|shalat|zakat|puasa|haji|umrah|"
        r"quran|hadits|hadith|sunnah|riba|halal|haram|nikah|aqidah|"
        r"allah|nabi|rasul|sahabat|khulafa|khalifah)\b",
        q, re.I,
    ):
        scores["AYMAN"] += 3

    # Default: AYMAN (general hangat), bukan UTZ lagi — karena UTZ = creative specific
    if max(scores.values()) == 0:
        scores["AYMAN"] = 1

    return scores


def _confidence_from_scores(scores: dict[str, int]) -> float:
    ordered = sorted(scores.values(), reverse=True)
    top = ordered[0] if ordered else 0
    second = ordered[1] if len(ordered) > 1 else 0
    if top <= 0:
        return 0.0
    # Simple heuristic: how separated is the top score.
    gap = top - second
    if top >= 100:
        return 1.0
    return min(1.0, 0.45 + 0.18 * gap)


# ---------------------------------------------------------------------------
# Task 22 — Al-Buruj: Persona "pembimbing" vs "faktual" switch
# ---------------------------------------------------------------------------

# Pemetaan gaya antarmuka → persona yang paling sesuai.
# "pembimbing" = orientasi dialog, membantu pengguna berproses (MIGHAN).
# "faktual"    = jawaban presisi, minimalis, berbasis data (HAYFAR).
# Pivot 2026-04-25: ALIGNED dengan cot_system_prompts.py PERSONA_DESCRIPTIONS
_STYLE_MAP: dict[str, Persona] = {
    "pembimbing": "AYMAN",   # general hangat, chat umum
    "guide":      "AYMAN",
    "faktual":    "ALEY",    # researcher rigor
    "factual":    "ALEY",
    "teknis":     "ABOO",    # engineer, code-first (BUKAN ALEY lagi)
    "technical":  "ABOO",
    "kreatif":    "UTZ",     # creative partner (BUKAN AYMAN lagi)
    "creative":   "UTZ",
    "akademik":   "ALEY",    # researcher (BUKAN OOMAR lagi)
    "academic":   "ALEY",
    "rencana":    "OOMAR",   # strategist (BUKAN ABOO lagi)
    "plan":       "OOMAR",
    "strategi":   "OOMAR",
    "strategy":   "OOMAR",
    "singkat":    "AYMAN",   # casual (BUKAN UTZ lagi)
    "simple":     "AYMAN",
}


def resolve_style_persona(style: str | None, fallback_persona: Persona) -> Persona:
    """
    Terjemahkan style shorthand ke persona.

    Args:
        style:            "pembimbing" | "faktual" | "kreatif" | "akademik" |
                          "rencana" | "singkat" | None
        fallback_persona: persona yang dipakai jika style tidak dikenali.

    Returns:
        Persona yang sesuai.
    """
    if not style:
        return fallback_persona
    mapped = _STYLE_MAP.get(style.lower().strip())
    return mapped if mapped else fallback_persona


def route_persona(question: str) -> PersonaDecision:
    scores = _score_persona(question)
    best = max(scores, key=lambda k: scores[k])
    conf = _confidence_from_scores(scores)

    reason_bits: list[str] = []
    if scores.get("ALEY", 0) > 0:
        reason_bits.append("coding/dev")
    if scores.get("AYMAN", 0) > 0:
        reason_bits.append("creative/design")
    if scores.get("OOMAR", 0) > 0:
        reason_bits.append("research/analysis")
    if scores.get("ABOO", 0) > 0:
        reason_bits.append("planning/strategy")
    if best == "UTZ" and not reason_bits:
        reason_bits.append("default")

    reason = f"score={scores.get(best, 0)}; signals={','.join(reason_bits) or 'none'}; conf={conf:.2f}"
    return PersonaDecision(persona=best, reason=reason, confidence=conf, scores=scores)

