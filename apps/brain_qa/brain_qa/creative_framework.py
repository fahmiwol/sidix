"""
creative_framework.py — SIDIX Creative Agent Framework

Disarikan dari BG Maker Prompt Engineering (Tiranyx, Bogor) + Mighantect agency-pipeline.
Referensi: D:\\BG maker\\06_Prompt-Engineering.md, D:\\Mighan\\server\\agency-pipeline.js

5 frameworks yang dipakai (urutan wajib):
  1. Aaker Brand Identity System   — brand essence, core+extended identity
  2. Simon Sinek Golden Circle     — Why / How / What
  3. Marty Neumeier Onlyness       — "only X who Y in Z"
  4. Jungian 12 Archetypes         — primary 70% + secondary 30%
  5. Keller CBBE Pyramid           — Salience → Performance → Judgment → Resonance

5 aturan prompt (dari BG Maker Philosophy):
  a. Slots, not essays      — typed schema, bukan narasi
  b. One component per call — hindari generate semua sekaligus
  c. Divergence enforced    — 3 alt harus orthogonal archetype
  d. System cached, user small
  e. Structured output atau retry

Prinsip Creative Thinking (Bisnizy.com):
  - Suspend Judgment: Jangan menilai ide terlalu cepat (fokus kuantitas)
  - Question Reframing: Ubah masalah jadi pertanyaan "Bagaimana jika..."
  - Divergence: Hasilkan banyak ide sebelum sintesis
  - Sintesis: Hubungkan ide tak relevan jadi solusi orisinal
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# ── 12 Jungian Archetypes (Mark & Pearson) ────────────────────────────────────

ArchetypeName = Literal[
    # STABILITY quadrant
    "caregiver", "ruler", "creator",
    # BELONGING quadrant
    "jester", "everyman", "lover",
    # MASTERY quadrant
    "hero", "outlaw", "magician",
    # INDEPENDENCE quadrant
    "innocent", "sage", "explorer",
]

ARCHETYPES: dict[str, dict] = {
    "caregiver":  {"quadrant": "STABILITY",    "core_desire": "melindungi, membantu", "fear": "keegoisan", "voice": "hangat, nurturing, lembut"},
    "ruler":      {"quadrant": "STABILITY",    "core_desire": "kontrol, keteraturan", "fear": "chaos", "voice": "berwibawa, percaya diri, premium"},
    "creator":    {"quadrant": "STABILITY",    "core_desire": "membuat sesuatu abadi", "fear": "mediocrity", "voice": "artistik, ekspresif, inventif"},
    "jester":     {"quadrant": "BELONGING",   "core_desire": "kegembiraan, hidup ringan", "fear": "kebosanan", "voice": "lucu, playful, warm"},
    "everyman":   {"quadrant": "BELONGING",   "core_desire": "terhubung dengan semua", "fear": "dikucilkan", "voice": "relatable, honest, down-to-earth"},
    "lover":      {"quadrant": "BELONGING",   "core_desire": "keintiman, keindahan", "fear": "kesepian", "voice": "sensual, romantic, passionate"},
    "hero":       {"quadrant": "MASTERY",     "core_desire": "membuktikan nilai", "fear": "kelemahan", "voice": "bold, courageous, direct"},
    "outlaw":     {"quadrant": "MASTERY",     "core_desire": "revolusi, melanggar aturan", "fear": "status quo", "voice": "rebel, disruptive, raw"},
    "magician":   {"quadrant": "MASTERY",     "core_desire": "transformasi", "fear": "konsekuensi tak terduga", "voice": "visionary, mystical, transformative"},
    "innocent":   {"quadrant": "INDEPENDENCE","core_desire": "kebahagiaan, kesederhanaan", "fear": "dihukum", "voice": "optimis, tulus, murni"},
    "sage":       {"quadrant": "INDEPENDENCE","core_desire": "kebenaran, pemahaman", "fear": "ketidaktahuan", "voice": "thoughtful, authoritative, wise"},
    "explorer":   {"quadrant": "INDEPENDENCE","core_desire": "kebebasan, petualangan", "fear": "terperangkap", "voice": "adventurous, independent, curious"},
}


def opposite_quadrant(a: str, b: str) -> bool:
    """Cek apakah 2 archetype di kuadran berlawanan (terlarang kecuali sengaja tension)."""
    opposites = {"STABILITY": "MASTERY", "MASTERY": "STABILITY",
                 "BELONGING": "INDEPENDENCE", "INDEPENDENCE": "BELONGING"}
    qa = ARCHETYPES.get(a, {}).get("quadrant")
    qb = ARCHETYPES.get(b, {}).get("quadrant")
    return qa is not None and qb is not None and opposites.get(qa) == qb


# ── 7 Creative Use Cases (dari Mighan + BG Maker agency pipeline) ─────────────

@dataclass(frozen=True)
class CreativeTemplate:
    """Template siap pakai untuk use case kreatif harian agency."""
    name: str
    aspect_ratio: str
    width: int
    height: int
    style_prefix: str   # auto-append ke prompt user
    negative: str       # negative prompt
    default_archetype: ArchetypeName
    description: str


CREATIVE_TEMPLATES: dict[str, CreativeTemplate] = {
    "ig_feed": CreativeTemplate(
        name="IG Feed (square)",
        aspect_ratio="1:1", width=1024, height=1024,
        style_prefix="Instagram feed aesthetic, centered composition, clean background, social-media-optimized, vibrant colors",
        negative="cluttered, text-heavy, low resolution, watermark",
        default_archetype="everyman",
        description="Post square untuk IG feed, mudah dibaca thumbnail",
    ),
    "ig_story": CreativeTemplate(
        name="IG Story / Reels Cover",
        aspect_ratio="9:16", width=576, height=1024,
        style_prefix="vertical mobile-first, bold focal point, story-format, negative space for text overlay",
        negative="horizontal composition, watermark, cluttered",
        default_archetype="jester",
        description="Vertikal untuk Story / Reels cover / TikTok",
    ),
    "yt_thumbnail": CreativeTemplate(
        name="YouTube Thumbnail",
        aspect_ratio="16:9", width=1024, height=576,
        style_prefix="high-contrast thumbnail, eye-catching focal subject, bold composition, cinematic lighting",
        negative="subtle, muted colors, hard to read at small size",
        default_archetype="hero",
        description="Thumbnail YouTube — harus standout di grid",
    ),
    "poster_event": CreativeTemplate(
        name="Event Poster (A4)",
        aspect_ratio="A4 vertical", width=768, height=1024,
        style_prefix="event poster composition, headline-ready typography space, dynamic energy, eye-catching hierarchy",
        negative="flat, boring, low energy",
        default_archetype="ruler",
        description="Poster event A4 portrait",
    ),
    "product_shot": CreativeTemplate(
        name="Product Shot Studio",
        aspect_ratio="1:1", width=1024, height=1024,
        style_prefix="product photography, studio lighting, soft shadow, clean background, commercial-quality, sharp focus on product",
        negative="busy background, poor lighting, blurry",
        default_archetype="ruler",
        description="Produk shot siap upload e-commerce/marketplace",
    ),
    "food_shot": CreativeTemplate(
        name="Food Photography",
        aspect_ratio="1:1", width=1024, height=1024,
        style_prefix="food photography, overhead or 45-degree angle, natural warm lighting, appetizing detail, rustic or modern styling",
        negative="artificial color, greasy, unappealing angle",
        default_archetype="caregiver",
        description="Foto makanan/kuliner untuk menu / Instagram F&B",
    ),
    "banner_web": CreativeTemplate(
        name="Web Banner Hero",
        aspect_ratio="16:9 wide", width=1024, height=576,
        style_prefix="hero banner composition, wide landscape, negative space for headline overlay, professional premium aesthetic",
        negative="portrait orientation, too detailed to read text over",
        default_archetype="sage",
        description="Banner website hero section dengan ruang headline",
    ),
}


# ── Context-aware Style Hints (Nusantara-specific, dari brain_qa existing) ────

CONTEXT_HINTS: dict[str, str] = {
    # Islam / Religius
    "islam_masjid": "warm golden hour light, serene spiritual atmosphere, Islamic architectural detail, calligraphy element",
    # Tradisional
    "batik_tenun": "traditional Indonesian textile detail, rich natural dye colors, intricate pattern, cultural authenticity",
    "candi_heritage": "ancient stone carving texture, volcanic landscape backdrop, misty morning, weathered andesite, historical",
    "rumah_adat": "vernacular architecture, traditional wood craftsmanship, indigenous roof lines, cultural context",
    # Alam / Landscape
    "pantai_laut": "golden hour dramatic sky, tropical seascape, cinematic wide angle, turquoise water",
    "gunung_alam": "landscape photography, misty mountain layers, sunrise/sunset light, serene nature",
    "sawah_padi": "terraced rice field, lush green layers, Asian agricultural beauty, morning dew",
    # Kuliner
    "makanan": "food photography overhead shot, natural warm lighting, appetizing texture, rustic or modern plating",
    # Urban / Modern
    "kota_urban": "urban street photography, Jakarta/Bandung style, cinematic city mood, golden hour or blue hour",
    # People / Lifestyle
    "orang_keluarga": "candid lifestyle photography, natural expression, warm emotion, connection",
}


def detect_context(prompt: str) -> list[str]:
    """Deteksi konteks kultural/tematik dari prompt, return list of hint keys."""
    q = prompt.lower()
    matches = []
    rules = {
        "islam_masjid": ("masjid", "islam", "quran", "ramadhan", "idul", "kaligrafi", "arab", "muslim"),
        "batik_tenun": ("batik", "tenun", "songket", "ulos", "kain tradisional"),
        "candi_heritage": ("candi", "borobudur", "prambanan", "stupa", "penataran", "sukuh"),
        "rumah_adat": ("rumah gadang", "joglo", "tongkonan", "honai", "limas", "rumah adat"),
        "pantai_laut": ("pantai", "laut", "ombak", "sunset di pantai", "beach", "ocean", "sea"),
        "gunung_alam": ("gunung", "bromo", "merapi", "rinjani", "kawah", "pegunungan"),
        "sawah_padi": ("sawah", "padi", "tegalalang", "terasering", "rice field"),
        "makanan": ("makanan", "kuliner", "rendang", "nasi", "sate", "soto", "gudeg", "pempek", "bakso", "mie"),
        "kota_urban": ("jakarta", "bandung", "surabaya", "urban", "kota malam", "city skyline"),
        "orang_keluarga": ("keluarga", "anak", "lifestyle", "potret", "portrait", "orang"),
    }
    for key, kws in rules.items():
        if any(k in q for k in kws):
            matches.append(key)
    return matches


# ── Main: enhance prompt v2 (framework-aware) ─────────────────────────────────

def enhance_prompt_creative(
    user_prompt: str,
    template: str | None = None,
    archetype: ArchetypeName | None = None,
) -> dict:
    """
    Enhance user prompt pakai framework BG Maker + konteks Nusantara.

    Returns:
      {
        "enhanced_prompt": str,
        "negative_prompt": str,
        "width": int,
        "height": int,
        "detected_contexts": [str],
        "applied_archetype": str,
        "template_used": str,
      }
    """
    q = user_prompt.strip()

    # Strip leading creative verbs (biar subject yang ditonjolkan)
    verb_prefixes = (
        "bikin gambar ", "buat gambar ", "buatkan gambar ", "generate gambar ",
        "gambarkan ", "render gambar ", "lukiskan ", "bikin foto ", "buat foto ",
        "bikin ilustrasi ", "buat ilustrasi ", "generate image ", "create image ",
        "bikin poster ", "buat poster ", "bikin thumbnail ", "buat thumbnail ",
        "bikin konten ", "buat konten ",
        "bikin ", "buat ", "gambar ", "foto ", "ilustrasi ",
    )
    ql = q.lower()
    for v in verb_prefixes:
        if ql.startswith(v):
            q = q[len(v):].strip()
            break

    # Pilih template
    tpl_key = template or _infer_template(user_prompt)
    tpl = CREATIVE_TEMPLATES.get(tpl_key, CREATIVE_TEMPLATES["ig_feed"])

    # Pilih archetype (dari user override atau default template)
    arch_name = archetype or tpl.default_archetype
    arch = ARCHETYPES.get(arch_name, ARCHETYPES["everyman"])

    # Detect konteks kultural
    contexts = detect_context(user_prompt)
    context_hints = [CONTEXT_HINTS[c] for c in contexts if c in CONTEXT_HINTS]

    # Build enhanced prompt — layered
    parts = [q]
    parts.extend(context_hints)
    parts.append(tpl.style_prefix)
    parts.append(f"mood: {arch['voice']}")
    parts.append("professional photography, 4k high detail, cinematic composition, sharp focus")

    enhanced = ", ".join(parts)

    return {
        "enhanced_prompt": enhanced,
        "negative_prompt": tpl.negative,
        "width": tpl.width,
        "height": tpl.height,
        "detected_contexts": contexts,
        "applied_archetype": arch_name,
        "template_used": tpl_key,
    }


def _infer_template(prompt: str) -> str:
    """Infer template default dari keyword di prompt user."""
    q = prompt.lower()
    rules = [
        ("yt_thumbnail", ("thumbnail", "youtube", "yt ")),
        ("ig_story",    ("story", "reels", "tiktok", "9:16", "vertikal")),
        ("poster_event", ("poster", "event", "acara", "seminar")),
        ("product_shot", ("product", "produk", "katalog", "e-commerce", "marketplace")),
        ("food_shot",   ("makanan", "kuliner", "rendang", "nasi", "sate", "kopi", "minuman", "food")),
        ("banner_web",  ("banner", "hero", "website header", "landing")),
    ]
    for tpl, kws in rules:
        if any(k in q for k in kws):
            return tpl
    return "ig_feed"  # default


# ── Phase 2: Creative Thinking Principles (Bisnizy.com) ─────────────────────
271: 
272: def reframe_problem(problem: str) -> str:
273:     """Mengubah masalah statis menjadi pertanyaan terbuka 'Bagaimana jika...'."""
274:     p = problem.strip().lower()
275:     if p.startswith(("bagaimana", "mengapa", "apa")):
276:         return problem
277:     return f"Bagaimana jika kita melihat '{problem}' dari sudut pandang yang berbeda?"
278: 
279: def brainstorm_divergent_ideas(problem: str, n: int = 3) -> list[str]:
280:     """Simulasi menghasilkan banyak ide (kuantitas) tanpa penilaian awal."""
281:     # Placeholder untuk LLM call nanti, saat ini berbasis rule/template
282:     reframed = reframe_problem(problem)
283:     return [
284:         f"Opsi 1 (Konvensional): Solusi standar untuk '{problem}'",
285:         f"Opsi 2 (Out-of-the-box): {reframed} — dengan pendekatan radikal.",
286:         f"Opsi 3 (Sintesis): Gabungkan '{problem}' dengan elemen yang tak terduga."
287:     ]
288: 
289: # ── Divergence-3 Pattern (untuk future use: generate 3 orthogonal variants) ────

def suggest_divergent_archetypes(primary: ArchetypeName) -> list[ArchetypeName]:
    """
    Given primary archetype, suggest 2 others yang orthogonal (berbeda kuadran
    tapi bukan kuadran langsung berlawanan).
    Used untuk generate 3 alternatif yang strategically distinct.
    """
    q_primary = ARCHETYPES[primary]["quadrant"]
    # Ambil 2 archetype dari 2 kuadran adjacent berbeda (bukan opposite)
    suggestions = []
    seen_quadrants = {q_primary}
    for name, meta in ARCHETYPES.items():
        if name == primary:
            continue
        q = meta["quadrant"]
        if q in seen_quadrants:
            continue
        if opposite_quadrant(primary, name):
            continue
        suggestions.append(name)
        seen_quadrants.add(q)
        if len(suggestions) == 2:
            break
    return suggestions
