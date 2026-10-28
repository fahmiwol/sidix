"""
creative_writing.py — Creative Writing Engine

Kreativitas melampaui marketing copy — ke ranah seni naratif.
Modul ini berperan sebagai "creative director": merancang struktur,
narrative arc, voice, pacing, dan estetika karya kreatif.

Format yang didukung:
- short_story: cerpen dengan narrative arc lengkap
- poetry: puisi dengan form, theme, imagery guidance
- screenplay_scene: adegan dengan format standar
- worldbuilding_lore: dokumen lore untuk worldbuilding
- character_profile: profil karakter dengan depth

Integrasi:
- Persona voice dari persona.py / nafs.py
- CQF scorer dari creative_quality.py (opsional)
- Emotional tone dari emotional_tone_engine.py (opsional)

Pivot 2026-04-25 — Jiwa Sprint Phase 3 (Kimi lane)
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Enums ────────────────────────────────────────────────────────────────────

class CreativeForm(str, Enum):
    SHORT_STORY = "short_story"
    POETRY = "poetry"
    SCREENPLAY_SCENE = "screenplay_scene"
    WORLDBUILDING_LORE = "worldbuilding_lore"
    CHARACTER_PROFILE = "character_profile"


class PoetryForm(str, Enum):
    FREE_VERSE = "free_verse"
    HAIKU = "haiku"
    PANTUN = "pantun"
    SONNET = "sonnet"
    GHAZAL = "ghazal"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class NarrativeArc:
    """Classic narrative arc untuk short story / scene."""

    setup: str
    inciting_incident: str
    rising_action: str
    climax: str
    falling_action: str
    resolution: str


@dataclass
class PoetrySpec:
    """Spesifikasi untuk puisi."""

    form: PoetryForm
    lines_target: int
    rhyme_scheme: str  # e.g. "ABAB", "AABB", "free"
    meter_hint: str  # e.g. "iambic_pentameter", "syllable_5_7_5", "free"
    theme: str
    mood: str
    imagery_domains: list[str]  # e.g. ["nature", "light", "water"]


@dataclass
class SceneBeat:
    """Satu beat dalam screenplay scene."""

    beat_type: str  # action | dialogue | transition
    description: str
    emotional_shift: str = ""  # e.g. "tension rises", "relief"


@dataclass
class ScreenplaySpec:
    """Spesifikasi screenplay scene."""

    scene_heading: str  # INT. LOCATION - TIME
    scene_objective: str
    emotional_arc: list[str]  # e.g. ["calm", "tension", "climax", "resolution"]
    beats: list[SceneBeat] = field(default_factory=list)


@dataclass
class LoreCategory:
    """Kategori lore untuk worldbuilding."""

    category: str  # geography | history | culture | magic_system | politics | religion
    title: str
    summary: str
    key_elements: list[str]
    consistency_notes: list[str] = field(default_factory=list)


@dataclass
class CharacterArchetype:
    """Archetype karakter dengan depth."""

    name: str
    archetype: str  # e.g. "The Orphan", "The Warrior", "The Caregiver"
    motivation: str
    internal_conflict: str
    flaw: str
    growth_arc: str
    relationships: list[dict[str, str]] = field(default_factory=list)
    voice_quirks: list[str] = field(default_factory=list)


@dataclass
class CreativeBrief:
    """Brief lengkap untuk satu karya kreatif."""

    form: CreativeForm
    title: str
    theme: str
    tone: str
    target_audience: str
    persona_voice: str
    narrative_arc: NarrativeArc | None = None
    poetry_spec: PoetrySpec | None = None
    screenplay_spec: ScreenplaySpec | None = None
    lore_categories: list[LoreCategory] = field(default_factory=list)
    character_profile: CharacterArchetype | None = None
    creative_notes: list[str] = field(default_factory=list)
    cqf_score: float = 0.0


# ── Persona voice mapping ────────────────────────────────────────────────────

_PERSONA_VOICE_NOTES: dict[str, str] = {
    "ABOO": "Voice: casual, tech-savvy, uses Indonesian slang naturally. Warm but concise. Loves analogies from everyday life. Occasional humor.",
    "OOMAR": "Voice: formal, scholarly, deep. Uses classical references and precise terminology. Respects tradition. Measured pacing.",
    "AYMAN": "Voice: professional, analytical, structured. Clear bullet points and frameworks. Slightly distant but helpful.",
    "ALEY": "Voice: warm, empathetic, nurturing. Uses gentle metaphors. Focuses on feelings and human connection.",
    "UTZ": "Voice: energetic, enthusiastic, youth-oriented. Uses contemporary references. Fast-paced, punchy.",
}


# ── Theme generator ──────────────────────────────────────────────────────────

_THEMES_POOL = [
    "redemption", "loss", "identity", "courage", "betrayal", "love", "grief",
    "ambition", "forgiveness", "transformation", "home", "freedom", "duty",
    "hope", "isolation", "memory", "tradition_vs_modernity", "faith", "justice",
]

_MOODS_POOL = [
    "melancholic", "nostalgic", "tense", "serene", "chaotic", "intimate",
    "mysterious", "triumphant", "bittersweet", "eerie", "warm", "lonely",
]

_IMAGERY_POOL = [
    "nature", "light", "water", "fire", "shadow", "sky", "earth", "wind",
    "city", "village", "mountain", "sea", "forest", "desert", "rain", "stars",
]

_CHARACTER_ARCHETYPES_POOL = [
    "The Orphan", "The Warrior", "The Caregiver", "The Seeker", "The Rebel",
    "The Ruler", "The Jester", "The Sage", "The Creator", "The Lover",
    "The Destroyer", "The Magician",
]


# ── Engine ───────────────────────────────────────────────────────────────────

class CreativeWritingEngine:
    """Creative director untuk karya naratif."""

    def __init__(self, persona: str = "UTZ"):
        self.persona = persona.upper()
        self.voice_note = _PERSONA_VOICE_NOTES.get(self.persona, "")

    def generate(
        self,
        form: CreativeForm,
        prompt: str,
        title: str = "",
        target_audience: str = "general",
        extra_context: dict[str, Any] | None = None,
    ) -> CreativeBrief:
        """Generate creative brief berdasarkan form dan prompt."""
        ctx = extra_context or {}
        theme = ctx.get("theme", self._extract_theme(prompt))
        tone = ctx.get("tone", self._infer_tone(prompt))

        brief = CreativeBrief(
            form=form,
            title=title or self._generate_title(prompt, form),
            theme=theme,
            tone=tone,
            target_audience=target_audience,
            persona_voice=self.voice_note,
        )

        if form == CreativeForm.SHORT_STORY:
            brief.narrative_arc = self._build_narrative_arc(prompt, theme, tone)
            brief.creative_notes = self._story_notes(prompt, theme)
        elif form == CreativeForm.POETRY:
            brief.poetry_spec = self._build_poetry_spec(prompt, theme, tone, ctx)
            brief.creative_notes = self._poetry_notes(prompt, theme)
        elif form == CreativeForm.SCREENPLAY_SCENE:
            brief.screenplay_spec = self._build_screenplay_spec(prompt, theme, tone, ctx)
            brief.creative_notes = self._screenplay_notes(prompt)
        elif form == CreativeForm.WORLDBUILDING_LORE:
            brief.lore_categories = self._build_lore_categories(prompt, theme, ctx)
            brief.creative_notes = self._lore_notes(prompt)
        elif form == CreativeForm.CHARACTER_PROFILE:
            brief.character_profile = self._build_character_profile(prompt, ctx)
            brief.creative_notes = self._character_notes(prompt)

        # Optional CQF scoring
        brief.cqf_score = self._estimate_cqf(brief)
        return brief

    # ── Helpers: extraction & inference ──────────────────────────────────────

    def _extract_theme(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        # ID → EN theme mapping
        id_to_en = {
            "cinta": "love", "kasih": "love", "sayang": "love",
            "pengorbanan": "redemption", "korban": "redemption",
            "kehilangan": "loss", "hilang": "loss",
            "keberanian": "courage", "berani": "courage",
            "pengkhianatan": "betrayal", "khianat": "betrayal",
            "kesedihan": "grief", "sedih": "grief",
            "ambisi": "ambition",
            "pengampunan": "forgiveness", "maaf": "forgiveness",
            "transformasi": "transformation", "ubah": "transformation",
            "kebebasan": "freedom", "bebas": "freedom",
            "tanggung jawab": "duty", "kewajiban": "duty",
            "harapan": "hope",
            "kesendirian": "isolation", "sendiri": "isolation",
            "memori": "memory", "kenangan": "memory",
            "tradisi": "tradition_vs_modernity",
            "iman": "faith",
            "keadilan": "justice",
        }
        for id_word, en_theme in id_to_en.items():
            if id_word in prompt_lower:
                return en_theme
        for theme in _THEMES_POOL:
            if theme.replace("_", " ") in prompt_lower or theme in prompt_lower:
                return theme
        return random.choice(_THEMES_POOL)

    def _infer_tone(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["sedih", "tragis", "dark", "melancholic", "sad"]):
            return "melancholic"
        if any(w in prompt_lower for w in ["lucu", "komedi", "funny", "humor", "light"]):
            return "humorous"
        if any(w in prompt_lower for w in ["seram", "horor", "thriller", "scary", "tense"]):
            return "tense"
        if any(w in prompt_lower for w in ["hangat", "warm", "sweet", "gentle"]):
            return "warm"
        return "neutral"

    def _generate_title(self, prompt: str, form: CreativeForm) -> str:
        words = re.findall(r"\b\w{4,}\b", prompt.lower())
        if words:
            seed = random.choice(words[:5]).capitalize()
            if form == CreativeForm.POETRY:
                return f"Untitled: {seed}"
            if form == CreativeForm.SHORT_STORY:
                return f"Cerita {seed}"
            if form == CreativeForm.SCREENPLAY_SCENE:
                return f"Scene: {seed}"
            if form == CreativeForm.WORLDBUILDING_LORE:
                return f"Lore: {seed}"
            if form == CreativeForm.CHARACTER_PROFILE:
                return f"Profile: {seed}"
        return "Untitled"

    # ── Short Story ──────────────────────────────────────────────────────────

    def _build_narrative_arc(self, prompt: str, theme: str, tone: str) -> NarrativeArc:
        return NarrativeArc(
            setup=f"Perkenalkan dunia dan karakter utama. Tone: {tone}. Seed dari prompt: {prompt[:60]}...",
            inciting_incident=f"Event yang mengubah status quo. Terkait theme: {theme}.",
            rising_action=f"Konflik memuncak. Karakter menghadapi rintangan yang terkait {theme}.",
            climax=f"Momen penentuan. Konflik internal + external bertemu.",
            falling_action=f"Konsekuensi dari keputusan klimaks. Transisi emosional.",
            resolution=f"Penutup yang resonan dengan theme {theme}. Tone: {tone}.",
        )

    def _story_notes(self, prompt: str, theme: str) -> list[str]:
        return [
            f"Theme: {theme}. Pastikan setiap scene menguatkan theme ini.",
            f"Persona voice: {self.persona}. Sesuaikan bahasa dan referensi.",
            "Gunakan 'show don't tell' untuk emosi karakter.",
            "Pacing: mulai lambat, naik ke klimaks, turun ke resolution.",
        ]

    # ── Poetry ───────────────────────────────────────────────────────────────

    def _build_poetry_spec(
        self, prompt: str, theme: str, tone: str, ctx: dict[str, Any]
    ) -> PoetrySpec:
        form_hint = ctx.get("poetry_form", "")
        pform = self._detect_poetry_form(form_hint, prompt)

        lines_map = {
            PoetryForm.HAIKU: 3,
            PoetryForm.PANTUN: 4,
            PoetryForm.SONNET: 14,
            PoetryForm.GHAZAL: 10,
            PoetryForm.FREE_VERSE: 12,
        }

        rhyme_map = {
            PoetryForm.HAIKU: "free",
            PoetryForm.PANTUN: "AABB",
            PoetryForm.SONNET: "ABAB CDCD EFEF GG",
            PoetryForm.GHAZAL: "aa ba ca da",
            PoetryForm.FREE_VERSE: "free",
        }

        meter_map = {
            PoetryForm.HAIKU: "syllable_5_7_5",
            PoetryForm.PANTUN: "syllable_8_8_8_8",
            PoetryForm.SONNET: "iambic_pentameter",
            PoetryForm.GHAZAL: "couplet_refrain",
            PoetryForm.FREE_VERSE: "free",
        }

        return PoetrySpec(
            form=pform,
            lines_target=lines_map[pform],
            rhyme_scheme=rhyme_map[pform],
            meter_hint=meter_map[pform],
            theme=theme,
            mood=random.choice(_MOODS_POOL),
            imagery_domains=random.sample(_IMAGERY_POOL, k=min(3, len(_IMAGERY_POOL))),
        )

    def _detect_poetry_form(self, hint: str, prompt: str) -> PoetryForm:
        prompt_lower = (hint + " " + prompt).lower()
        if "haiku" in prompt_lower:
            return PoetryForm.HAIKU
        if "pantun" in prompt_lower:
            return PoetryForm.PANTUN
        if "sonnet" in prompt_lower:
            return PoetryForm.SONNET
        if "ghazal" in prompt_lower or "gazal" in prompt_lower:
            return PoetryForm.GHAZAL
        return PoetryForm.FREE_VERSE

    def _poetry_notes(self, prompt: str, theme: str) -> list[str]:
        return [
            f"Theme: {theme}. Gunakan imagery konkret, jangan abstrak murni.",
            f"Persona voice: {self.persona}. Sesuaikan register bahasa.",
            "Perhatikan irama dan bunyi (assonansi, konsonansi) walau free verse.",
            "Judul puisi harus bekerja keras — bisa kontras atau reinforcement.",
        ]

    # ── Screenplay ───────────────────────────────────────────────────────────

    def _build_screenplay_spec(
        self, prompt: str, theme: str, tone: str, ctx: dict[str, Any]
    ) -> ScreenplaySpec:
        location = ctx.get("location", "UNKNOWN LOCATION")
        time = ctx.get("time", "DAY")
        heading = f"{ctx.get('int_ext', 'INT.')}. {location.upper()} - {time.upper()}"
        # Normalize double dot
        heading = heading.replace("INT..", "INT.").replace("EXT..", "EXT.")

        beats = [
            SceneBeat("action", "Establish setting and character position."),
            SceneBeat("dialogue", "Opening line that hooks.", "engagement"),
            SceneBeat("action", "Physical or environmental reaction."),
            SceneBeat("dialogue", "Turning point line.", "tension rises"),
            SceneBeat("action", "Climax moment — decision or revelation."),
            SceneBeat("dialogue", "Closing line with resonance.", "resolution"),
        ]

        return ScreenplaySpec(
            scene_heading=heading,
            scene_objective=f"Explore {theme} through conflict and choice.",
            emotional_arc=["calm", "engagement", "tension", "climax", "resolution"],
            beats=beats,
        )

    def _screenplay_notes(self, prompt: str) -> list[str]:
        return [
            f"Persona voice: {self.persona}. Dialogue harus terdengar natural untuk persona ini.",
            "Setiap scene harus punya objective — apa yang berubah setelah scene ini?",
            "Show emotion through action, bukan dialogue eksplisit.",
            "Format standar: SCENE HEADING, ACTION (italic), CHARACTER NAME, DIALOGUE.",
        ]

    # ── Worldbuilding ────────────────────────────────────────────────────────

    def _build_lore_categories(
        self, prompt: str, theme: str, ctx: dict[str, Any]
    ) -> list[LoreCategory]:
        categories = ctx.get("lore_categories", ["geography", "culture", "history"])
        result = []
        for cat in categories:
            result.append(
                LoreCategory(
                    category=cat,
                    title=f"{cat.replace('_', ' ').title()}",
                    summary=f"Overview of {cat} in this world. Theme: {theme}.",
                    key_elements=[f"Element A of {cat}", f"Element B of {cat}"],
                    consistency_notes=[f"Must align with theme {theme}"],
                )
            )
        return result

    def _lore_notes(self, prompt: str) -> list[str]:
        return [
            f"Persona voice: {self.persona}. Sesuaikan kedalaman detail.",
            "Lore harus punya 'sense of history' — sesuatu yang terjadi SEBELUM cerita utama.",
            "Buat 1-2 kontradiksi atau misteri yang belum terpecahkan.",
            "Consistency checklist: geography, timeline, naming convention.",
        ]

    # ── Character Profile ────────────────────────────────────────────────────

    def _build_character_profile(
        self, prompt: str, ctx: dict[str, Any]
    ) -> CharacterArchetype:
        name = ctx.get("name", "Unnamed")
        archetype = ctx.get("archetype", random.choice(_CHARACTER_ARCHETYPES_POOL))
        return CharacterArchetype(
            name=name,
            archetype=archetype,
            motivation=ctx.get("motivation", f"To find meaning through {self._extract_theme(prompt)}"),
            internal_conflict=ctx.get("internal_conflict", "Desire vs. duty"),
            flaw=ctx.get("flaw", "Overthinks consequences"),
            growth_arc=ctx.get("growth_arc", "From isolation to connection"),
            relationships=ctx.get("relationships", []),
            voice_quirks=ctx.get("voice_quirks", []),
        )

    def _character_notes(self, prompt: str) -> list[str]:
        return [
            f"Persona voice: {self.persona}. Karakter harus punya 'tanda tangan' verbal.",
            "Flaw harus terkait motivation — bukan random quirk.",
            "Growth arc: karakter harus berbeda di akhir vs awal.",
            "Voice quirks: 2-3 pola bahasa unik (repetitive word, sentence structure, reference).",
        ]

    # ── CQF estimation ───────────────────────────────────────────────────────

    def _estimate_cqf(self, brief: CreativeBrief) -> float:
        """Heuristic CQF estimation untuk brief."""
        score = 0.5
        if brief.narrative_arc and all([
            brief.narrative_arc.setup,
            brief.narrative_arc.climax,
            brief.narrative_arc.resolution,
        ]):
            score += 0.15
        if brief.creative_notes:
            score += 0.1
        if brief.theme and brief.theme != "neutral":
            score += 0.1
        if brief.persona_voice:
            score += 0.1
        return min(1.0, round(score, 2))


# ── Convenience ──────────────────────────────────────────────────────────────

def generate_creative_brief(
    form: str,
    prompt: str,
    persona: str = "UTZ",
    title: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot API untuk generate creative brief → dict."""
    engine = CreativeWritingEngine(persona=persona)
    brief = engine.generate(
        form=CreativeForm(form),
        prompt=prompt,
        title=title,
        extra_context=kwargs,
    )
    return _brief_to_dict(brief)


def _brief_to_dict(brief: CreativeBrief) -> dict[str, Any]:
    """Serialize CreativeBrief ke dict."""
    d: dict[str, Any] = {
        "form": brief.form.value,
        "title": brief.title,
        "theme": brief.theme,
        "tone": brief.tone,
        "target_audience": brief.target_audience,
        "persona_voice": brief.persona_voice,
        "creative_notes": brief.creative_notes,
        "cqf_score": brief.cqf_score,
    }
    if brief.narrative_arc:
        d["narrative_arc"] = {
            "setup": brief.narrative_arc.setup,
            "inciting_incident": brief.narrative_arc.inciting_incident,
            "rising_action": brief.narrative_arc.rising_action,
            "climax": brief.narrative_arc.climax,
            "falling_action": brief.narrative_arc.falling_action,
            "resolution": brief.narrative_arc.resolution,
        }
    if brief.poetry_spec:
        d["poetry_spec"] = {
            "form": brief.poetry_spec.form.value,
            "lines_target": brief.poetry_spec.lines_target,
            "rhyme_scheme": brief.poetry_spec.rhyme_scheme,
            "meter_hint": brief.poetry_spec.meter_hint,
            "theme": brief.poetry_spec.theme,
            "mood": brief.poetry_spec.mood,
            "imagery_domains": brief.poetry_spec.imagery_domains,
        }
    if brief.screenplay_spec:
        d["screenplay_spec"] = {
            "scene_heading": brief.screenplay_spec.scene_heading,
            "scene_objective": brief.screenplay_spec.scene_objective,
            "emotional_arc": brief.screenplay_spec.emotional_arc,
            "beats": [
                {"type": b.beat_type, "description": b.description, "emotional_shift": b.emotional_shift}
                for b in brief.screenplay_spec.beats
            ],
        }
    if brief.lore_categories:
        d["lore_categories"] = [
            {
                "category": lc.category,
                "title": lc.title,
                "summary": lc.summary,
                "key_elements": lc.key_elements,
                "consistency_notes": lc.consistency_notes,
            }
            for lc in brief.lore_categories
        ]
    if brief.character_profile:
        d["character_profile"] = {
            "name": brief.character_profile.name,
            "archetype": brief.character_profile.archetype,
            "motivation": brief.character_profile.motivation,
            "internal_conflict": brief.character_profile.internal_conflict,
            "flaw": brief.character_profile.flaw,
            "growth_arc": brief.character_profile.growth_arc,
            "relationships": brief.character_profile.relationships,
            "voice_quirks": brief.character_profile.voice_quirks,
        }
    return d


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = CreativeWritingEngine(persona="ABOO")

    print("=== Creative Writing Engine Self-Test ===\n")

    # Test 1: Short story
    brief1 = engine.generate(
        form=CreativeForm.SHORT_STORY,
        prompt="cerita tentang anak yang kehilangan rumah dan menemukan keluarga baru",
        title="Rumah di Ujung Jalan",
    )
    print(f"[1] Short Story: {brief1.title}")
    print(f"    Theme: {brief1.theme}, Tone: {brief1.tone}")
    print(f"    Arc has setup: {bool(brief1.narrative_arc and brief1.narrative_arc.setup)}")
    print(f"    CQF: {brief1.cqf_score}")
    print()

    # Test 2: Poetry
    brief2 = engine.generate(
        form=CreativeForm.POETRY,
        prompt="puisi tentang senja di kampung halaman",
        extra_context={"poetry_form": "pantun"},
    )
    print(f"[2] Poetry: {brief2.title}")
    print(f"    Form: {brief2.poetry_spec.form.value if brief2.poetry_spec else 'N/A'}")
    print(f"    Lines: {brief2.poetry_spec.lines_target if brief2.poetry_spec else 'N/A'}")
    print(f"    CQF: {brief2.cqf_score}")
    print()

    # Test 3: Screenplay
    brief3 = engine.generate(
        form=CreativeForm.SCREENPLAY_SCENE,
        prompt="adegan pertemuan pertama dua saudara yang terpisah 20 tahun",
        extra_context={"location": "Rumah Tua", "time": "Night", "int_ext": "INT."},
    )
    print(f"[3] Screenplay: {brief3.title}")
    print(f"    Heading: {brief3.screenplay_spec.scene_heading if brief3.screenplay_spec else 'N/A'}")
    print(f"    Beats: {len(brief3.screenplay_spec.beats) if brief3.screenplay_spec else 0}")
    print(f"    CQF: {brief3.cqf_score}")
    print()

    # Test 4: Worldbuilding
    brief4 = engine.generate(
        form=CreativeForm.WORLDBUILDING_LORE,
        prompt="dunia di mana manusia bisa berkomunikasi dengan hewan melalui mimpi",
    )
    print(f"[4] Worldbuilding: {brief4.title}")
    print(f"    Categories: {len(brief4.lore_categories)}")
    print(f"    CQF: {brief4.cqf_score}")
    print()

    # Test 5: Character
    brief5 = engine.generate(
        form=CreativeForm.CHARACTER_PROFILE,
        prompt="karakter perempuan petani yang punya rahasia besar",
        extra_context={"name": "Siti Aminah", "archetype": "The Caregiver"},
    )
    print(f"[5] Character: {brief5.character_profile.name if brief5.character_profile else 'N/A'}")
    print(f"    Archetype: {brief5.character_profile.archetype if brief5.character_profile else 'N/A'}")
    print(f"    CQF: {brief5.cqf_score}")
    print()

    # Test 6: Dict serialization
    d = _brief_to_dict(brief1)
    assert "narrative_arc" in d
    assert d["form"] == "short_story"
    print("[6] Dict serialization: OK")
    print()

    # Test 7: Convenience API
    d2 = generate_creative_brief("poetry", "haiku tentang salju", persona="OOMAR")
    assert d2["form"] == "poetry"
    assert d2["poetry_spec"]["form"] == "haiku"
    print("[7] Convenience API: OK")
    print()

    print("[OK] All self-tests passed")
