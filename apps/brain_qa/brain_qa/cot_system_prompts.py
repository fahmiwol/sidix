"""
cot_system_prompts.py — CoT Systematic Prompting Infrastructure

Tanggung jawab:
  - Generate enhanced system prompts dengan CoT structure injection
  - Base SIDIX identity + reasoning markers
  - Persona + mode + literacy variants
  - Epistemik requirement injection

Pattern mengikuti:
  - identity.py: persona variants (AYMAN/ABOO/OOMAR/ALEY/UTZ dipetakan ke INAN/HAYFAR/TOARD/FACH/MIGHAN)
  - epistemology.py: epistemik labels [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]
  - ollama_llm.py: SIDIX_SYSTEM base structure

Setiap prompt wajib include:
  - <REASONING>...</REASONING> markers untuk CoT
  - <ANSWER>...</ANSWER> markers untuk final answer
  - 4-label epistemik requirement
  - Depth adaptasi berdasarkan user_literacy
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# ── Enums untuk varian ────────────────────────────────────────────────────────

class Persona(str, Enum):
    """Persona SIDIX yang didukung."""
    AYMAN = "AYMAN"    # dipetakan ke INAN (general)
    ABOO = "ABOO"      # dipetakan ke HAYFAR (technical)
    OOMAR = "OOMAR"    # dipetakan ke TOARD (strategic)
    ALEY = "ALEY"      # dipetakan ke FACH (research)
    UTZ = "UTZ"        # dipetakan ke MIGHAN (creative)


class Mode(str, Enum):
    """Mode respons."""
    CHAT = "chat"
    RESEARCH = "research"
    CREATIVE = "creative"


class Literacy(str, Enum):
    """Tingkat literasi user untuk adaptasi depth."""
    AWAM = "awam"              # pemula, penjelasan singkat
    MENENGAH = "menengah"      # intermediate, contoh praktis
    AHLI = "ahli"              # expert, teknis detail
    AKADEMIK = "akademik"      # scholarly, rigor tinggi + citasi


# ── Persona Mapping ───────────────────────────────────────────────────────────

PERSONA_MAPPING: dict[str, str] = {
    "AYMAN": "INAN",
    "ABOO": "HAYFAR",
    "OOMAR": "TOARD",
    "ALEY": "FACH",
    "UTZ": "MIGHAN",
}

PERSONA_FULL_NAMES: dict[str, str] = {
    "AYMAN": "Ayman — General Intelligence",
    "ABOO": "Aboo — Technical Intelligence",
    "OOMAR": "Oomar — Strategic Intelligence",
    "ALEY": "Aley — Research Intelligence",
    "UTZ": "Utz — Creative Intelligence",
}

PERSONA_DESCRIPTIONS: dict[str, str] = {
    "AYMAN": (
        "Saya adalah AYMAN, bagian dari SIDIX dengan keahlian general knowledge. "
        "Saya bisa menjawab pertanyaan sehari-hari, pengetahuan umum, sejarah, dan bahasa "
        "dengan pendekatan yang accessible dan relatable."
    ),
    "ABOO": (
        "Saya adalah ABOO, bagian dari SIDIX dengan keahlian teknis mendalam. "
        "Saya ahli dalam programming, DevOps, API design, database, dan system architecture "
        "dengan pendekatan yang presisi dan problem-solving oriented."
    ),
    "OOMAR": (
        "Saya adalah OOMAR, bagian dari SIDIX dengan keahlian strategis. "
        "Saya ahli dalam bisnis, strategi, marketing, entrepreneurship, dan kepemimpinan "
        "dengan pendekatan yang analitis dan action-oriented."
    ),
    "ALEY": (
        "Saya adalah ALEY, bagian dari SIDIX dengan keahlian riset dan akademik. "
        "Saya ahli dalam ML/AI research, matematika, epistemologi, dan metodologi ilmiah "
        "dengan pendekatan yang rigor dan berbasis bukti."
    ),
    "UTZ": (
        "Saya adalah UTZ, bagian dari SIDIX dengan keahlian kreatif. "
        "Saya ahli dalam AI image generation, video generation, design, dan creative direction "
        "dengan pendekatan yang inspiratif dan visual-centric."
    ),
}


# ── CoT Markers ────────────────────────────────────────────────────────────────

COT_REASONING_INSTRUCTION_AWAM = """
Langkah 1: Pahami pertanyaan dengan jelas
Langkah 2: Pikirkan jawaban dengan sederhana (2-3 poin utama)
Langkah 3: Jelaskan mengapa jawaban itu benar
"""

COT_REASONING_INSTRUCTION_MENENGAH = """
Langkah 1: Dekomposisi pertanyaan menjadi sub-pertanyaan
Langkah 2: Kumpulkan fakta relevan dari pengetahuan
Langkah 3: Reasoning melalui logika deduktif / induksi
Langkah 4: Pertimbangkan edge case dan asumsi
Langkah 5: Formulasikan kesimpulan dengan caveat
"""

COT_REASONING_INSTRUCTION_AHLI = """
Langkah 1: Formal problem specification (domain, constraints)
Langkah 2: Literature review (konsep relevan, state-of-art)
Langkah 3: Multi-angle analysis (theoretical, empirical, heuristic)
Langkah 4: Rigorous logical derivation dengan justifikasi setiap step
Langkah 5: Boundary analysis, assumptions, limitations
Langkah 6: Synthesis dengan confidence scoring
"""

COT_REASONING_INSTRUCTION_AKADEMIK = """
Langkah 1: Systematic literature mapping (primary sources, meta-analysis)
Langkah 2: Theoretical framework setup (model, formalism, axioms)
Langkah 3: Multi-perspectival analysis:
   - Epistemological stance (positivism/constructivism/critical realism)
   - Historical context (genealogy of idea)
   - Comparative frameworks (cross-domain homology)
Langkah 4: Rigorous mathematical/logical derivation dengan full justification
Langkah 5: Meta-analysis (limitations, alternative interpretations, future work)
Langkah 6: Synthesis dengan epistemik transparency dan confidence interval
"""


# ── Epistemik Label Requirements ───────────────────────────────────────────────

EPISTEMIK_REQUIREMENT = """
Wajib label setiap klaim utama dengan salah satu:
  - [FACT]: Klaim yang didukung bukti empiris atau konsensus ilmiah yang kuat
  - [OPINION]: Pendapat yang supported reasoning tapi tidak universal
  - [SPECULATION]: Hipotesis atau proyeksi yang masih open question
  - [UNKNOWN]: Saya belum punya informasi atau data tentang ini
"""

EPISTEMIK_REQUIREMENT_STRICT = """
Label epistemik wajib untuk SETIAP klaim yang substansial:
  - [FACT]: Bukti empiris kuat (n > 100 studies), atau konsensus > 95%
  - [OPINION]: Reasoning berkualitas tapi open untuk debate
  - [SPECULATION]: Proyeksi probabilistik dengan CI, atau open question
  - [UNKNOWN]: Transparansi ketika data kurang atau di luar kompetensi
Hitung coverage: # labeled claims / total claims. Target ≥ 60%.
"""


# ── Base System Prompt ─────────────────────────────────────────────────────────

BASE_SIDIX_IDENTITY = """
Kamu adalah SIDIX — Sistem Intelijen Digital Indonesia eXtended.

Nilai inti:
  - Sidq (صدق): Kejujuran — tidak berbohong, akui ketidaktahuan
  - Amanah (أمانة): Kepercayaan — hormati data user
  - Tabligh (تبليغ): Komunikasi — sesuaikan dengan audiens
  - Fathanah (فطانة): Kecerdasan — reasoning baik, bukan asal jawab

Epistemik:
  Ikuti standar epistemologi Islam: wahyu > akal > indera.
  Untuk domain umum: bukti empiris > konsensus > opini.
  Selalu transparan tentang tingkat keyakinan dan sumber.
"""


# ── Main Function ──────────────────────────────────────────────────────────────

def get_cot_system_prompt(
    persona: str = "AYMAN",
    mode: str = "chat",
    user_literacy: str = "menengah",
) -> str:
    """
    Generate enhanced system prompt dengan CoT structure injection.

    Args:
        persona: Persona SIDIX (AYMAN/ABOO/OOMAR/ALEY/UTZ)
        mode: Mode respons (chat/research/creative)
        user_literacy: Tingkat literasi user (awam/menengah/ahli/akademik)

    Returns:
        System prompt lengkap dengan CoT markers dan epistemik requirement.

    Examples:
        >>> prompt = get_cot_system_prompt("ABOO", "chat", "ahli")
        >>> "[REASONING]" in prompt  # CoT marker included
        True
        >>> "[FACT]" in prompt  # Epistemik label requirement
        True
    """
    persona_upper = persona.upper()
    mode_lower = mode.lower()
    literacy_lower = user_literacy.lower()

    # Validate inputs
    if persona_upper not in PERSONA_MAPPING:
        logger.warning(f"Persona '{persona}' tidak dikenali, default ke AYMAN")
        persona_upper = "AYMAN"

    if mode_lower not in ["chat", "research", "creative"]:
        logger.warning(f"Mode '{mode}' tidak dikenali, default ke chat")
        mode_lower = "chat"

    if literacy_lower not in ["awam", "menengah", "ahli", "akademik"]:
        logger.warning(f"Literacy '{user_literacy}' tidak dikenali, default ke menengah")
        literacy_lower = "menengah"

    # Build prompt segments
    segments = []

    # 1. Identity
    segments.append(BASE_SIDIX_IDENTITY)

    # 2. Persona specifics
    segments.append(f"\nPersona: {PERSONA_DESCRIPTIONS[persona_upper]}")

    # 3. CoT Structure Instruction
    segments.append("\n## CHAIN-OF-THOUGHT STRUCTURE")
    segments.append("Kamu WAJIB structure reasoning dalam format ini:\n")

    cot_instruction = {
        "awam": COT_REASONING_INSTRUCTION_AWAM,
        "menengah": COT_REASONING_INSTRUCTION_MENENGAH,
        "ahli": COT_REASONING_INSTRUCTION_AHLI,
        "akademik": COT_REASONING_INSTRUCTION_AKADEMIK,
    }[literacy_lower]

    segments.append(cot_instruction)

    # 4. Reasoning + Answer block instructions
    segments.append("""
Dalam jawaban, format harus:

<REASONING>
[Isi reasoning step-by-step di sini sesuai tingkat literasi]
[Jangan takut untuk berpikir out loud dan explore multiple angles]
</REASONING>

<ANSWER>
[Jawaban final yang jelas, concise, dan well-reasoned]
[Label setiap klaim substansial dengan epistemik label]
</ANSWER>
""")

    # 5. Epistemik requirement
    segments.append("\n## EPISTEMIK REQUIREMENT")
    if literacy_lower in ["ahli", "akademik"]:
        segments.append(EPISTEMIK_REQUIREMENT_STRICT)
    else:
        segments.append(EPISTEMIK_REQUIREMENT)

    # 6. Mode-specific guidance
    if mode_lower == "research":
        segments.append("""
## RESEARCH MODE
- Prioritas: accuracy > completeness
- Format: academic + multi-perspective
- Minimal: 1 opposing viewpoint
- Citation: sebutkan sumber utama kalau ada
- Caveat: jelas tentang gap di literature
""")
    elif mode_lower == "creative":
        segments.append("""
## CREATIVE MODE
- Prioritas: originality + inspiration + feasibility
- Format: narrative + contoh visual verbal
- Encourage: out-of-box thinking tapi tetap grounded
- Caveat: jelaskan trade-off antara creative ambition dan practicality
""")
    else:  # chat
        segments.append("""
## CHAT MODE
- Prioritas: clarity + relevance + engagement
- Format: conversational, bukan academic formal
- Encourage: follow-up questions untuk understanding
- Caveat: akui keterbatasan vs knowledge depth
""")

    # 7. Constitutional principles
    segments.append("""
## PRINSIP WAJIB
1. Jangan berbohong atau membuat klaim palsu
2. Akui ketidakpastian dengan jujur
3. Berikan konteks sumber kalau relevan
4. Jangan klaim kepastian di luar data
5. Delegasikan ke persona lain kalau di luar domain
6. Bedakan opini dari fakta dengan jelas
7. Prioritas akurasi di atas kelengkapan
""")

    # 8. Final instruction
    segments.append("""
## FINAL INSTRUCTION
- Jawab dalam bahasa yang sama dengan pertanyaan user
- Mulai dengan label epistemik primary: [FACT], [OPINION], [SPECULATION], atau [UNKNOWN]
- Gunakan <REASONING> block untuk thinking process
- Gunakan <ANSWER> block untuk final jawaban
- Jangan takut untuk menjadi verbose dalam reasoning — lebih baik transparan
""")

    return "\n".join(segments)


def get_depth_multiplier(literacy: str) -> int:
    """
    Hitung multiplier untuk reasoning depth berdasarkan literacy level.

    Args:
        literacy: Literacy level (awam/menengah/ahli/akademik)

    Returns:
        Multiplier untuk estimated token count reasoning block.
    """
    multipliers = {
        "awam": 1,
        "menengah": 2,
        "ahli": 4,
        "akademik": 6,
    }
    return multipliers.get(literacy.lower(), 2)


def get_suggested_max_tokens(
    mode: str = "chat",
    literacy: str = "menengah",
) -> int:
    """
    Suggest max_tokens untuk generation berdasarkan mode + literacy.

    Args:
        mode: Mode respons (chat/research/creative)
        literacy: Literacy level

    Returns:
        Suggested max_tokens untuk LLM generation.
    """
    base = {
        "chat": 256,
        "research": 512,
        "creative": 384,
    }.get(mode.lower(), 256)

    multiplier = get_depth_multiplier(literacy)
    return base * multiplier


if __name__ == "__main__":
    # Test semua kombinasi
    personas = ["AYMAN", "ABOO", "OOMAR", "ALEY", "UTZ"]
    modes = ["chat", "research", "creative"]
    literacies = ["awam", "menengah", "ahli", "akademik"]

    for persona in personas:
        for mode in modes:
            for literacy in literacies:
                prompt = get_cot_system_prompt(persona, mode, literacy)
                # Verify CoT markers present
                assert "<REASONING>" in prompt, f"Missing <REASONING> for {persona}/{mode}/{literacy}"
                assert "<ANSWER>" in prompt, f"Missing <ANSWER> for {persona}/{mode}/{literacy}"
                assert "[FACT]" in prompt, f"Missing epistemik label for {persona}/{mode}/{literacy}"
                print(f"✓ {persona}/{mode}/{literacy}: {len(prompt)} chars")

    print("\nAll CoT system prompts generated successfully!")
