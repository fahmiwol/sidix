"""
agent_react.py — SIDIX ReAct Loop

ReAct = Reason + Act
Pattern: Thought → Action → Observation → (loop) → Final Answer

Cara kerja:
1. Agent dapat pertanyaan user
2. THINK: Apa yang perlu dicari/dilakukan?
3. ACT: Panggil tool (via Permission Gate)
4. OBSERVE: Baca hasil tool
5. Loop sampai cukup info → Final Answer

LLM-agnostic: saat ini pakai rule-based + BM25 (offline).
Nanti swap ke SIDIX Inference Engine setelah fine-tune selesai.

Format trace (ReAct trace):
  Thought: ...
  Action: tool_name({"param": "value"})
  Observation: ...
  Thought: ...
  Final Answer: ...
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .agent_tools import call_tool, list_available_tools, ToolResult
from .branch_manager import get_manager as _get_branch_manager
from .orchestration import agent_build_intent
from .user_intelligence import analyze_user, get_response_instructions, UserProfile
from .parallel_executor import execute_parallel, merge_observations
from .wisdom_gate import WisdomGate

# ── Coding Planner (Phase 1: LLM-based planner for coding tasks) ─────────────
try:
    from . import coding_planner as _coding_planner
    _CODING_PLANNER_ENABLED = True
except Exception:
    _coding_planner = None  # type: ignore[assignment]
    _CODING_PLANNER_ENABLED = False

# ── Jiwa: 7-Pilar Kemandirian ──────────────────────────────────────────────
try:
    from .jiwa.orchestrator import jiwa as _jiwa
    _JIWA_ENABLED = True
except Exception:
    _jiwa = None  # type: ignore[assignment]
    _JIWA_ENABLED = False


# ── Config ────────────────────────────────────────────────────────────────────
MAX_STEPS = 6           # max ReAct loop iterations (default)
MAX_STEPS_BUILD = 18    # lebih panjang bila intent implementasi / app / game / coding
MAX_TOKENS_PER_OBS = 600  # potong observation supaya tidak bloat context

# Anti-loop (Sprint hardening 2026-04)
MAX_ACTION_REPEAT = 2   # berapa kali action yang sama boleh terulang sebelum fallback
MAX_TOOL_ERRORS   = 3   # berapa kali tool error berturut-turut sebelum fallback


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ReActStep:
    step: int
    thought: str
    action_name: str      # "" jika final answer
    action_args: dict
    observation: str      # hasil tool
    is_final: bool = False
    final_answer: str = ""


@dataclass
class AgentSession:
    session_id: str
    question: str
    persona: str
    client_id: str = ""            # branch context (Agency OS)
    agency_id: str = ""            # agency context (multi-tenant)
    conversation_id: str = ""      # optional conversation threading
    steps: list[ReActStep] = field(default_factory=list)
    final_answer: str = ""
    citations: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished: bool = False
    error: str = ""
    confidence: str = ""          # label teks untuk UI/telemetri
    confidence_score: float = 0.0  # Task 27: skor numerik [0.0, 1.0]
    answer_type: str = "fakta"     # Task 17: "fakta" | "opini" | "spekulasi"
    # ── Epistemologi SIDIX (Islamic Epistemology Engine) ──────────────────────
    epistemic_tier: str = ""       # mutawatir | ahad_hasan | ahad_dhaif | mawdhu
    yaqin_level: str = ""          # ilm | ain | haqq (3 tingkat kepastian Qur'ani)
    maqashid_score: float = 0.0    # skor maqashid 5-sumbu [0.0–1.0]
    maqashid_passes: bool = True   # True jika lolos daruriyyat hard constraints
    audience_register: str = ""    # burhan | jadal | khitabah (Ibn Rushd register)
    cognitive_mode: str = ""       # taaqul | tafakkur | tadabbur | tadzakkur
    constitutional_passes: bool = True  # True jika lolos 4 sifat Nabi check
    nafs_stage: str = ""           # alignment trajectory (AMMARAH→KAMILAH)
    # ── User Intelligence (frekuensi pengguna) ────────────────────────────────
    user_language: str = ""        # id / ar / en / mixed / unknown
    user_literacy: str = ""        # awam / menengah / ahli / akademik
    user_intent: str = ""          # creative / technical / analytical / ...
    user_cultural_frame: str = ""  # nusantara / islamic / western / academic / neutral
    user_profile: UserProfile | None = None  # full profile object
    # ── Orkestrasi multi-aspek (modul orchestration.py) ─────────────────────────
    orchestration_digest: str = ""  # ringkasan OrchestrationPlan untuk API/trace
    # ── Praxis runtime: kerangka kasus (niat / inisiasi) ─────────────────────────
    case_frame_ids: str = ""  # id kerangka terpilih, dipisah koma
    case_frame_hints_rendered: str = ""  # teks yang disematkan ke jawaban (ringkas)
    praxis_matched_frame_ids: str = ""  # urutan id dari match awal sesi (untuk planner / API)
    # ── Maqashid mode gate (maqashid_profiles.py — IHOS-aligned) ────────────────
    maqashid_profile_status: str = ""   # pass | warn | block
    maqashid_profile_reasons: str = ""  # ringkasan alasan (API / trace)
    # ── Typo-resilience (brain/typo/pipeline — Muhasabah: simpan asli di question) ─
    question_normalized: str = ""     # kosong jika sama dengan question
    typo_script_hint: str = ""         # latin | arabic | mixed_arab_latin | ...
    typo_substitutions: int = 0
    # ── Pivot 2026-04-25: Follow-up awareness ───────────────────────────────────
    is_followup: bool = False          # True kalau question detect sebagai follow-up
    # ── Pivot 2026-04-25: Cognitive Self-Check warnings ─────────────────────────
    csc_warnings: str = ""             # comma-sep warnings dari _cognitive_self_check
    # ── Nafs Layer B (brain/nafs/response_orchestrator) ──────────────────────────
    nafs_topic: str = ""              # topic dari NafsOrchestrator (umum|kreatif|koding|agama|...)
    nafs_layers_used: str = ""        # "parametric,dynamic,static" (layer yang aktif)
    # ── Jiwa Sprint 4: Parallel Planner observability ────────────────────────────
    planner_used: bool = False        # True jika parallel_planner aktif sesi ini
    planner_savings: float = 0.0      # estimated savings dari parallel execution (0.0–1.0)


# ── Rule-based "LLM" (offline planner) ───────────────────────────────────────
# Ini diganti dengan SIDIX Inference Engine setelah model siap.
# Untuk sekarang: pattern matching yang cukup pintar untuk ReAct dasar.

_MATH_RE = re.compile(
    r'\b(\d[\d\s]*[\+\-\*\/\%][\d\s\.\+\-\*\/\%\(\)]+\d)\b'
)

_LIST_SOURCES_RE = re.compile(
    r'\b(list|daftar|semua|apa saja|sumber|dokumen|tersedia)\b',
    re.IGNORECASE,
)

_ROADMAP_LEARN_RE = re.compile(
    r"\b(roadmap|kurikulum|curriculum|belajar\s+sendiri|self-?learn|checklist|latihan)\b",
    re.IGNORECASE,
)

_GREETING_RE = re.compile(
    r'^(halo|hai|hello|hi|assalamu|salam|selamat)\b',
    re.IGNORECASE,
)

_ORCH_META_RE = re.compile(
    r"\b(orkestrasi|orchestr|vegapunk|multi[\s-]?agen|multi[\s-]?agent|"
    r"fase\s+agen|rencana\s+orkestrasi|orchestration\s+plan)\b",
    re.IGNORECASE,
)
_COPY_RE = re.compile(
    r"\b(copy|caption|iklan|ads copy|sales copy|aida|pas|fab)\b",
    re.IGNORECASE,
)
_CONTENT_PLAN_CREATIVE_RE = re.compile(
    r"\b(content plan|kalender konten|content planner|rencana konten)\b",
    re.IGNORECASE,
)
_BRAND_KIT_RE = re.compile(
    r"\b(brand kit|branding|brand identity|archetype brand|logo prompt)\b",
    re.IGNORECASE,
)
_THUMBNAIL_RE = re.compile(
    r"\b(thumbnail|yt cover|youtube cover|judul thumbnail)\b",
    re.IGNORECASE,
)
_CAMPAIGN_RE = re.compile(
    r"\b(campaign strategy|strategi campaign|rencana campaign|aarrr)\b",
    re.IGNORECASE,
)
_ADS_GEN_RE = re.compile(
    r"\b(generate ads|buat ads|iklan fb|iklan tiktok|iklan google)\b",
    re.IGNORECASE,
)

_IMAGE_RE = re.compile(
    r"\b(bikin|buat|generate|create|gambar|gambarin|render|visual|ilustrasi|"
    r"foto|picture|image|artwork|poster|lukisan|desain|banner|wallpaper|logo)\b",
    re.IGNORECASE,
)

_SIDIX_DOMAIN_RE = re.compile(
    r"\b("
    r"sidix|ihos|maqashid|naskh|sanad|raudah|tafsir|jariyah|muhasabah|"
    r"hafidz|praxis|persona|toard|fach|hayfar|inan|mighan|"
    r"brain_qa|corpus|korpus|knowledge\s+base"
    r")\b",
    re.IGNORECASE,
)

_FORCE_CORPUS_RE = re.compile(
    r"\b("
    r"berdasarkan\s+(corpus|korpus|dokumen|sumber)|"
    r"ambil\s+dari\s+(corpus|korpus)|"
    r"cite|sitasi|rujuk|sanad|"
    r"lihat\s+catatan|daftar\s+sumber"
    r")\b",
    re.IGNORECASE,
)

# Pivot 2026-04-25 (v2 — Supermodel launch): web_search aggressive default
# diperluas. Cover EN/ID variants, typo, tahun spesifik, kata kunci real-time
# tanpa wajib waktu modifier. Tidak pakai \b di pattern karena beberapa
# alternatif punya non-word boundary. Cek case-insensitive.
_CURRENT_EVENTS_RE = re.compile(
    r"("
    # waktu modifier umum
    r"\bhari\s+ini\b|\bsekarang\b|\bsaat\s+ini\b|\bterkini\b|\bterbaru\b|"
    r"\btoday\b|\bnow\b|\bcurrent(?:ly)?\b|\blatest\b|\brecent(?:ly)?\b|"
    # tahun eksplisit (2023+) → biasanya butuh data live
    r"\b(?:202[3-9]|20[3-9]\d)\b|"
    # berita / news
    r"\bberita\b|\bnews\b|\bupdate(?:s|d)?\b|\bbreaking\b|\bheadline\b|"
    # finance / harga real-time
    r"\bharga\s+(?:saham|bitcoin|btc|eth|emas|dollar|rupiah|usd|idr|crypto|nft|gold|oil|minyak)\b|"
    r"\bkurs\s+(?:dollar|usd|rupiah|idr|euro|eur|yen|sgd)\b|"
    r"\b(?:stock|forex|crypto)\s+(?:price|harga|rate)\b|"
    # cuaca
    r"\bcuaca\b|\bweather\b|\bsuhu\b|\btemperature\b|\bforecast\b|"
    # tokoh saat ini (EN + ID, typo-tolerant: presi(d)?ent)
    r"\bsiapa(?:kah)?\s+(?:presi?(?:d|den)t|presiden|menteri|minister|gubernur|governor|"
    r"ceo|founder|juara|champion|pemenang|winner|rektor|kapolri|panglima|gov(?:ernor)?|"
    r"raja|king|ratu|queen|sultan|paus|pope|wakil(?:\s+presiden)?|wapres)\b|"
    # Cover: "wakil presiden indonesia sekarang siapa", "presiden RI saat ini",
    # tanpa wajib "siapa" di depan
    r"\b(?:wakil\s+presiden|wapres|presi?(?:d|den)t|presiden)\s+(?:republik\s+)?(?:indonesia|ri|amerika|usa)\b|"
    r"\bwho\s+is\s+(?:the\s+)?(?:current\s+)?(?:president|presi?(?:d|den)t|prime\s+minister|"
    r"pm|ceo|founder|king|queen|pope|champion|winner|leader|governor|vice\s+president)\b|"
    r"\b(?:presiden|presi?(?:d|den)t|prime\s+minister|pm|perdana\s+menteri)\s+(?:amerika|usa|us|"
    r"indonesia|ri|rusia|russia|china|cina|jepang|japan|korea|india|inggris|uk|prancis|france|"
    r"jerman|germany|brazil|brasil|saudi|arab|iran|israel|palestina|palestine)\b|"
    # event timing
    r"\bkapan\s+(?:event|pemilu|election|piala|cup|olimpiade|olympic|konser|concert|rilis|release|launch|peluncuran)\b|"
    r"\bwhen\s+(?:is|was|will|did)\s+(?:the\s+)?(?:election|cup|launch|release|event|happen)\b|"
    r"\btanggal\s+berapa\s+(?:hari\s+ini|sekarang|today)\b|"
    # state-of-X / what's happening
    r"\bapa\s+(?:yang\s+)?(?:terjadi|sedang\s+terjadi|baru)\b|"
    r"\bwhat\s+(?:is|was|are)\s+(?:happening|going\s+on|new)\b|"
    r"\bwhat[''']s\s+(?:happening|new|going\s+on)\b|"
    r"\bstate\s+of\s+(?:the\s+)?(?:art|industry|economy|world|market)\b"
    r")",
    re.IGNORECASE,
)


def _needs_web_search(question: str) -> bool:
    """True bila pertanyaan butuh data terkini/real-time → web_search dulu."""
    return bool(_CURRENT_EVENTS_RE.search(question or ""))


def _extract_web_search_query(question: str) -> str:
    """
    Pivot 2026-04-26: extract concise web_search query dari user prompt panjang.

    Heuristik:
      1. Cari segmen yang punya kata kunci current-event
      2. Append tahun current bila query mengandung kata "sekarang/saat ini/now"
         (supaya search engine bias ke hasil terbaru, bukan halaman lama)
      3. Fallback: full question (truncated)
    """
    import datetime as _dt
    q = (question or "").strip()
    if not q:
        return q
    segments = re.split(r"[,\.\?!;]\s*", q)
    factual_keywords = re.compile(
        r"\b(presi(?:d|den)t|presiden|menteri|minister|gubernur|governor|"
        r"ceo|founder|raja|king|ratu|queen|sultan|paus|pope|champion|juara|"
        r"berita|news|harga|kurs|cuaca|weather|wakil|wapres|"
        r"siapa|who\s+is)\b",
        re.IGNORECASE,
    )
    has_now_marker = bool(re.search(
        r"\b(sekarang|saat\s+ini|terkini|terbaru|now|current|today|latest)\b",
        q, re.IGNORECASE,
    ))
    current_year = _dt.datetime.utcnow().year
    chosen: str = ""
    for seg in segments:
        seg = seg.strip()
        if 5 <= len(seg) <= 120 and factual_keywords.search(seg):
            chosen = seg
            break
    if not chosen:
        chosen = q[:120]
    # Append year supaya search bias ke latest (kalau belum ada year di query)
    if has_now_marker and not re.search(r"\b20\d{2}\b", chosen):
        chosen = f"{chosen} {current_year}".strip()
    return chosen


def _should_prioritize_corpus(question: str, *, corpus_only: bool) -> bool:
    """Putuskan kapan RAG harus dominan (topik SIDIX atau user minta sumber eksplisit)."""
    if corpus_only:
        return True
    q = (question or "").strip()
    if not q:
        return False
    if _FORCE_CORPUS_RE.search(q):
        return True
    return bool(_SIDIX_DOMAIN_RE.search(q))


def _response_blend_profile(
    question: str, persona: str = "UTZ", *, corpus_only: bool = False
) -> dict[str, Any]:
    """
    Menentukan strategi model-vs-corpus via Jiwa Nafs (Pilar 1).
    Fallback ke logika lama jika Jiwa tidak tersedia.
    """
    if _JIWA_ENABLED and _jiwa is not None:
        try:
            profile = _jiwa.route(question, persona, corpus_only=corpus_only)
            return {
                "name": profile.blend_name,
                "max_obs_blocks": profile.max_obs_blocks,
                "system_hint": profile.system_hint,
                "skip_corpus": profile.skip_corpus,
                "hayat_enabled": profile.hayat_enabled,
                "topic": profile.topic,
                "emotion_tag": profile.emotion_tag,
            }
        except Exception:
            pass  # fallback ke Layer B

    # ── Layer B: NafsOrchestrator standalone (brain/nafs/) ────────────────────
    try:
        from .nafs_bridge import blend_from_nafs
        _nb = blend_from_nafs(question, persona, corpus_only=corpus_only)
        if _nb:
            return _nb
    except Exception:
        pass  # fallback ke heuristik lama

    # ── Fallback lama ──────────────────────────────────────────────────────
    if _should_prioritize_corpus(question, corpus_only=corpus_only):
        return {
            "name": "sidix_focused",
            "max_obs_blocks": 3,
            "system_hint": (
                "Prioritaskan konteks SIDIX bila relevan. "
                "Jika konteks tidak cukup, jawab jujur dan sebutkan keterbatasan."
            ),
            "skip_corpus": False,
            "hayat_enabled": True,
            "topic": "sidix_internal",
        }
    return {
        "name": "model_focused",
        "max_obs_blocks": 1,
        "system_hint": (
            "Untuk topik umum/non-SIDIX, prioritaskan pengetahuan model. "
            "Gunakan konteks corpus hanya sebagai referensi tambahan jika benar-benar relevan."
        ),
        "skip_corpus": False,
        "hayat_enabled": True,
        "topic": "umum",
    }


def _effective_max_steps(question: str, max_steps: int | None) -> int:
    if max_steps is not None:
        return max(2, min(24, int(max_steps)))
    if agent_build_intent(question):
        return MAX_STEPS_BUILD
    # Coding tasks butuh lebih banyak step (read → analyze → patch → test → fix)
    if _CODING_PLANNER_ENABLED and _coding_planner is not None:
        try:
            if _coding_planner.is_coding_intent(question):
                return MAX_STEPS_BUILD
        except Exception:
            pass
    return MAX_STEPS


def _observation_is_weak_corpus(obs: str) -> bool:
    """True jika hasil search_corpus tidak cukup untuk diandalkan → boleh Wikipedia."""
    o = (obs or "").strip().lower()
    if len(o) < 80:
        return True
    if o.startswith("[error]"):
        return True
    if "index belum dibuat" in o or ("jalankan:" in o and "index" in o):
        return True
    if "wikipedia api gagal" in o:
        return False
    # Potongan observasi tidak memuat blok ringkasan (sering karena error hibrid / index kosong)
    if len(o) < 1600 and "ringkasan" not in o:
        return True
    return False


def _extract_topic(question: str) -> str:
    q = question.strip()
    q = re.sub(r"^(tolong|please|bantu|buatkan|buat|generate|bikin)\s+", "", q, flags=re.IGNORECASE).strip()
    return q or question.strip()


def _rule_based_plan(
    question: str,
    persona: str,
    history: list[ReActStep],
    step: int,
    *,
    corpus_only: bool,
    allow_web_fallback: bool,
    agent_mode: bool = True,
) -> tuple[str, str, dict] | list[dict[str, Any]]:
    """
    Returns (thought, action_name, action_args) OR a list of tool calls for parallel execution.
    Each tool call in list: {"thought": str, "name": str, "args": dict}

    DEFAULT (agent_mode=True): proactive, direct answer, minimal routing.
    STRICT (agent_mode=False): RAG-first, full routing, corpus/web aggressive.
    """
    q_lower = question.lower()

    # ── Coding Planner (Phase 1) — routing untuk SEMUA step coding ───────────
    if _CODING_PLANNER_ENABLED and _coding_planner is not None:
        try:
            if _coding_planner.is_coding_intent(question):
                return _coding_planner.plan_coding_step(
                    question=question,
                    history=history,
                    step=step,
                )
        except Exception:
            pass

    # Step 0: klasifikasi intent
    if step == 0:
        # Greeting
        if _GREETING_RE.match(question.strip()):
            return (
                "Ini sapaan. Tidak perlu tool, langsung jawab.",
                "",
                {},
            )

        # Praxis L0 → planner: orkestrasi dulu bila kerangka cocok (sebelum regex lama)
        try:
            from .praxis_runtime import planner_step0_suggestion

            _ps0 = planner_step0_suggestion(question, persona)
            if _ps0 is not None:
                return _ps0
        except Exception:
            pass

        # ── Coding Planner (Phase 1) ───────────────────────────────────────────
        if _CODING_PLANNER_ENABLED and _coding_planner is not None:
            try:
                if _coding_planner.is_coding_intent(question):
                    return _coding_planner.plan_coding_step(
                        question=question,
                        history=history,
                        step=step,
                    )
            except Exception:
                pass

        if _ORCH_META_RE.search(question):
            return (
                "User minta rencana orkestrasi / multi-aspek. Bangun OrchestrationPlan.",
                "orchestration_plan",
                {"question": question, "persona": persona},
            )

        if _CONTENT_PLAN_CREATIVE_RE.search(question):
            channel = "instagram"
            ql = question.lower()
            if "threads" in ql:
                channel = "threads"
            elif "tiktok" in ql:
                channel = "tiktok"
            return (
                "User minta konten planner. Generate kalender konten langsung.",
                "generate_content_plan",
                {
                    "niche": _extract_topic(question),
                    "duration_days": 30,
                    "channel": channel,
                    "cadence_per_week": 5,
                    "objective": "awareness",
                },
            )

        if _BRAND_KIT_RE.search(question):
            return (
                "User minta brand kit. Generate identity kit (archetype, palette, tone, logo prompts).",
                "generate_brand_kit",
                {
                    "business_name": "Brand SIDIX User",
                    "niche": _extract_topic(question),
                    "vibe": "modern, warm, trustworthy",
                },
            )

        if _THUMBNAIL_RE.search(question):
            return (
                "User minta thumbnail generator. Buat prompt + overlay siap render.",
                "generate_thumbnail",
                {
                    "title": _extract_topic(question),
                    "style": "bold",
                    "platform": "youtube",
                    "render": False,
                },
            )

        if _CAMPAIGN_RE.search(question):
            return (
                "User minta strategi campaign. Susun AARRR funnel + timeline.",
                "plan_campaign",
                {
                    "product": _extract_topic(question),
                    "audience": "audiens Indonesia",
                    "goal": "conversion",
                    "budget_idr": 1500000,
                    "duration_days": 30,
                    "platform_focus": "instagram",
                },
            )

        if _ADS_GEN_RE.search(question):
            return (
                "User minta ad generator. Buat beberapa variasi ad copy dan pilih terbaik.",
                "generate_ads",
                {
                    "product": _extract_topic(question),
                    "audience": "audiens Indonesia",
                    "platform": "facebook",
                    "objective": "conversion",
                    "n_variants": 3,
                },
            )

        if _COPY_RE.search(question):
            return (
                "User minta copy/caption. Generate beberapa varian copy dengan CQF.",
                "generate_copy",
                {
                    "topic": _extract_topic(question),
                    "channel": "instagram",
                    "formula": "AIDA",
                    "audience": "audiens Indonesia",
                    "tone": "friendly",
                },
            )

        # Math expression di pertanyaan
        math_match = _MATH_RE.search(question)
        if math_match:
            return (
                f"Ada ekspresi matematika: '{math_match.group()}'. Gunakan calculator.",
                "calculator",
                {"expression": math_match.group()},
            )

        # "List sumber" intent
        if _LIST_SOURCES_RE.search(q_lower) and any(
            w in q_lower for w in ["sumber", "dokumen", "corpus", "tersedia", "ada apa"]
        ):
            return (
                "User ingin tahu dokumen apa saja yang ada. Gunakan list_sources.",
                "list_sources",
                {},
            )

        # Roadmap-driven self learning
        if _ROADMAP_LEARN_RE.search(q_lower):
            # If a known slug is mentioned, start from that; otherwise default to python.
            slug = "python"
            for s in ("backend", "python", "sql", "system-design", "devops"):
                if s in q_lower.replace(" ", "-"):
                    slug = s
                    break
            return (
                f"User ingin belajar mandiri berbasis roadmap. Ambil item berikutnya dari roadmap '{slug}'.",
                "roadmap_next_items",
                {"slug": slug, "n": 10},
            )

        # ── Routing dengan pengkondisian hierarkis ────────────────────────────
        # 1. Topik SIDIX + butuh data terkini → PARALLEL corpus + web (Jiwa Sprint 4)
        #    Ini diletakkan DI ATAS web_search aggressive default supaya parallel
        #    path benar-benar tercapai.
        needs_corpus = _should_prioritize_corpus(question, corpus_only=corpus_only)
        needs_web = _needs_web_search(question)
        if needs_corpus and needs_web and allow_web_fallback and not corpus_only:
            return [
                {
                    "thought": f"Topik SIDIX + butuh data terkini. Cari di korpus paralel dengan web: '{question}'",
                    "name": "search_corpus",
                    "args": {"query": question, "k": 5, "persona": persona}
                },
                {
                    "thought": "Cari data terkini di web paralel dengan korpus.",
                    "name": "web_search",
                    "args": {"query": question, "max_results": 5}
                }
            ]

        # 2. Data terkini saja (bukan topik SIDIX) → web_search aggressive default.
        #    Pivot 2026-04-26: extract concise factual query (jangan pass full prompt
        #    panjang — DuckDuckGo akan match keyword dominan yang salah).
        if needs_web and allow_web_fallback and not corpus_only:
            _web_q = _extract_web_search_query(question)
            return (
                f"Pertanyaan menyangkut data terkini/real-time. web_search: '{_web_q}'.",
                "web_search",
                {"query": _web_q, "max_results": 5},
            )

        # 3. Topik SIDIX saja → corpus
        if needs_corpus:
            return (
                f"Topik terkait SIDIX/sumber internal. Gunakan search_corpus dengan query: '{question}'.",
                "search_corpus",
                {"query": question, "k": 5, "persona": persona},
            )
        # Sigma-2B: general factual fallback — try corpus first before going to RunPod cold.
        # Jika pertanyaan adalah factual 1-hop (bukan creative/casual), coba corpus
        # sebelum langsung ke LLM. Corpus hit = fast (<1s), LLM cold = 90-150s.
        _CASUAL_RE = re.compile(
            r"\b(halo|hai|hey|apa kabar|gimana|bagaimana kabarmu|ceritain|curhat|lucu|"
            r"jokes?|humor|ketawa|nanya|tanya|boleh|boleh nanya|mau tanya)\b",
            re.IGNORECASE,
        )
        _is_casual = bool(_CASUAL_RE.search(question))
        _is_factual_candidate = not _is_casual and not _needs_web_search(question) and len(question) > 5
        if _is_factual_candidate and not corpus_only:
            return (
                f"Pertanyaan faktual umum. Cari konteks di korpus dulu sebelum LLM: '{question}'.",
                "search_corpus",
                {"query": question, "k": 3, "persona": persona},
            )
        return (
            "Pertanyaan casual/greeting. Jawab langsung dari kemampuan model.",
            "",
            {},
        )

    # Step 1+: evaluasi hasil sebelumnya
    last = history[-1] if history else None
    if last and last.observation:
        obs_lower = last.observation.lower()

        # Mode agen: setelah corpus, orientasi sandbox workspace (implement / app / game)
        # Praxis: frame implement_or_automate memperluas ke workspace walau regex build belum picu.
        try:
            from .praxis_runtime import implement_frame_matches

            _impl_frame = implement_frame_matches(question)
        except Exception:
            _impl_frame = False

        if (
            last.action_name == "search_corpus"
            and (agent_build_intent(question) or _impl_frame)
            and not any(s.action_name == "workspace_list" for s in history)
        ):
            thought_ws = (
                "Kerangka Praxis (implementasi): setelah corpus, tinjau sandbox."
                if _impl_frame and not agent_build_intent(question)
                else "User minta implementasi; setelah corpus, lihat isi sandbox agent_workspace."
            )
            return (
                thought_ws,
                "workspace_list",
                {"path": ""},
            )

        if last.action_name == "workspace_list":
            return (
                "Daftar workspace sandbox sudah ada. Susun jawaban akhir dengan arahan file/langkah.",
                "",
                {},
            )

        if last.action_name in ("workspace_read", "workspace_write"):
            return (
                "Operasi file sandbox selesai. Rangkai final answer (ringkas path yang disentuh).",
                "",
                {},
            )

        if last.action_name == "orchestration_plan":
            return (
                "Rencana orkestrasi dari tool sudah ada. Susun jawaban akhir ringkas (boleh kutip cuplikan fase).",
                "",
                {},
            )

        # Fallback web terkontrol: corpus lemah → Wikipedia API (allowlist host)
        if (
            last.action_name == "search_corpus"
            and _observation_is_weak_corpus(last.observation)
            and allow_web_fallback
            and not corpus_only
            and not agent_build_intent(question)
        ):
            if not any(s.action_name == "search_web_wikipedia" for s in history):
                return (
                    "Hasil corpus tipis/gagal. Fallback: kutipan Wikipedia (API resmi, allowlist).",
                    "search_web_wikipedia",
                    {"query": question, "lang": "id"},
                )

        if last.action_name == "search_web_wikipedia":
            return (
                "Sudah ada hasil Wikipedia. Rangkai final answer dengan label sumber web.",
                "",
                {},
            )

        # Jika hasil search cukup (ada content), buat final answer
        if last.action_name == "search_corpus" and "ringkasan" in obs_lower:
            return (
                "Hasil search corpus cukup untuk menjawab. Buat final answer.",
                "",
                {},
            )

        # Jika list_sources selesai, buat final answer
        if last.action_name == "list_sources":
            return (
                "Daftar sumber sudah lengkap. Buat final answer.",
                "",
                {},
            )

        # Jika calculator selesai
        if last.action_name == "calculator":
            return (
                "Hasil kalkulasi sudah ada. Buat final answer.",
                "",
                {},
            )

        # Jika ada error di observation, coba search corpus hanya bila perlu corpus.
        if "[error]" in obs_lower[:200] or "error" in obs_lower[:50]:
            if step < 3:
                if _should_prioritize_corpus(question, corpus_only=corpus_only):
                    return (
                        "Langkah sebelumnya error. Coba search_corpus sebagai fallback.",
                        "search_corpus",
                        {"query": question, "k": 3, "persona": persona},
                    )
                return (
                    "Langkah sebelumnya error, tetapi topik umum. Lanjutkan final answer dari model.",
                    "",
                    {},
                )

    # Default: final answer setelah MAX_STEPS/2
    if step >= MAX_STEPS // 2:
        return ("Cukup informasi untuk menjawab. Buat final answer.", "", {})

    if _should_prioritize_corpus(question, corpus_only=corpus_only):
        return (
            "Belum cukup info. Coba search corpus lebih dalam.",
            "search_corpus",
            {"query": question, "k": 5, "persona": persona},
        )
    return (
        "Topik umum dan tidak butuh corpus tambahan. Lanjut final answer.",
        "",
        {},
    )


def _append_mode_hint(question: str, text: str, persona: str) -> str:
    """
    Pivot 2026-04-26: append kontekstual saran mode/persona di akhir response.

    Filosofi: jangan suruh user PILIH dulu. Jawab dulu (immediate value),
    lalu kasih hint mode yang lebih relevan untuk eksplorasi lanjut.

    Returns text + footer dengan suggestion (atau text apa adanya kalau
    pertanyaan tidak match keyword).
    """
    if not text or not text.strip():
        return text
    q_lc = (question or "").lower().strip()
    if len(q_lc) < 8:
        return text  # greeting / sapaan singkat, jangan tambah hint

    suggestions: list[str] = []

    # Creative / brainstorm → Burst
    if any(t in q_lc for t in (
        "ide ", "saran ", "brainstorm", "kreatif", "creative", "konsep",
        "marketing", "campaign", "naming", "tagline", "design",
    )):
        suggestions.append("🌌 **Burst** — explore 6 angle paralel, Pareto-pilih yang terbaik")

    # Etis / strategis / dilemma → Two Eyes
    if any(t in q_lc for t in (
        "haruskah", "should i", "dilema", "etis", "moral", "hukum",
        "halal haram", "syariah", "fiqh", "memilih antara",
    )):
        suggestions.append("👁 **Two Eyes** — analisa dual perspective: data + maqashid + sintesis")

    # Future / prediksi → Foresight
    if any(t in q_lc for t in (
        "masa depan", "trend", "prediksi", "5 tahun ke depan", "10 tahun",
        "forecast", "outlook", "scenario", "akan jadi apa", "future of",
    )):
        suggestions.append("🔮 **Foresight** — scan web+corpus → 3 skenario (base/bull/bear) → narasi visioner")

    # Research / hidden insight → Resurrect
    if any(t in q_lc for t in (
        "tokoh", "researcher", "underrated", "overlooked", "klasik",
        "sejarah", "pioneer", "history of", "founding", "method lama",
    )):
        suggestions.append("🌿 **Resurrect** — surface ide/tokoh yang dilupakan tren (Noether method)")

    # Strict / academic / sanad → strict_mode
    if any(t in q_lc for t in (
        "fatwa", "sumber primer", "peer review", "akademik", "citation lengkap",
        "verifikasi data", "research mode",
    )):
        suggestions.append("🔬 **Strict mode** (toggle) — RAG-first, sanad tier wajib, epistemic label")

    if not suggestions:
        return text

    # Max 2 suggestions supaya tidak overwhelming
    suggestions = suggestions[:2]
    hint_block = "\n\n---\n💡 _Mau eksplorasi lebih dalam?_\n" + "\n".join(f"• {s}" for s in suggestions)
    return text.rstrip() + hint_block


def _apply_sanad(question: str, llm_text: str, steps: "list[ReActStep]") -> str:
    """
    Σ-1A: Sanad gate — cross-verify LLM answer sebelum dikembalikan ke user.
    - Brand-specific (persona/IHOS/ReAct/dll): override kalau halu vs canonical CLAUDE.md.
    - Current event tanpa web_search source: return UNKNOWN daripada tebak.
    - Coding/creative: passthrough tanpa gate.
    Non-fatal: kalau error → return llm_text apa adanya.
    """
    try:
        from .sanad_verifier import Source, verify_multisource, format_sanad_footer
        import logging as _log
        _log_sv = _log.getLogger("sidix.sanad")

        sources: list[Source] = []
        for st in (steps or []):
            action_name = getattr(st, "action_name", "") or ""
            observation = getattr(st, "observation", "") or ""
            action_args = getattr(st, "action_args", {}) or {}
            if action_name in ("web_search", "search_web_wikipedia", "web_fetch") and observation:
                sources.append(Source(
                    name="web_search",
                    text=observation[:500],
                    confidence=0.8,
                    url=action_args.get("url"),
                ))
            elif action_name in ("search_corpus", "read_chunk", "list_sources") and observation:
                sources.append(Source(
                    name="search_corpus",
                    text=observation[:500],
                    confidence=0.7,
                ))

        result = verify_multisource(question, llm_text or "", sources)
        final = result.answer
        if result.rejected_llm:
            _log_sv.warning(
                "SANAD OVERRIDE — question='%.80s' reason='%s'",
                question, result.reason,
            )
            footer = format_sanad_footer(result)
            if footer:
                final = final + footer
        return final
    except Exception as _sv_err:
        import logging as _log
        _log.getLogger("sidix.sanad").debug("sanad gate skip: %s", _sv_err)
        return llm_text or ""


def _compose_final_answer(
    question: str,
    persona: str,
    steps: list[ReActStep],
    *,
    simple_mode: bool = False,
    user_profile: "UserProfile | None" = None,
    session: "AgentSession | None" = None,
    agent_mode: bool = True,
) -> tuple[str, list[dict], float, str]:
    """
    Compose jawaban final dari semua observation yang sudah dikumpulkan.
    Returns (answer_text, citations, confidence_score, answer_type).

    Pipeline:
    1. Coba Ollama (local LLM generative) + corpus context sebagai RAG
    2. Fallback: local_llm.py (Qwen2.5-7B + LoRA) jika Ollama off
    3. Fallback: format corpus results langsung
    4. Fallback final: "tidak tahu" response (hanya kalau mode formal)
    """
    # ── Jiwa Sprint: persona-driven system hint ───────────────────────────────
    _system_persona = ""
    if persona:
        try:
            from .cot_system_prompts import PERSONA_DESCRIPTIONS
            _system_persona = PERSONA_DESCRIPTIONS.get(persona.upper(), "")
        except Exception:
            pass
    # ── Σ-1C Phase 1: per-persona tool priority hint (injected ke LLM system) ─
    # Setiap persona punya "default lens" berbeda → LLM tahu dari sudut mana
    # untuk mensintesis jawaban + tool apa yang relevan.
    _PERSONA_TOOL_HINT: dict[str, str] = {
        "UTZ": (
            "Kamu persona UTZ — Creative Director. Sintesis dari sudut kreatif/visual. "
            "Prioritas tool: brainstorm, image_gen, web_search (trend/inspirasi). "
            "Jawab dengan energi kreatif, ide liar, metafora visual."
        ),
        "ABOO": (
            "Kamu persona ABOO — Systems Builder. Sintesis dari sudut teknikal/engineering. "
            "Prioritas tool: code_sandbox, search_corpus (doc/spec), web_fetch (changelog). "
            "Jawab presisi, code-first, benchmark konkret."
        ),
        "OOMAR": (
            "Kamu persona OOMAR — Strategic Architect. Sintesis dari sudut strategi/bisnis. "
            "Prioritas tool: web_search (market/competitor), roadmap_tools, orchestration_plan. "
            "Jawab dengan framework bisnis, analisis tradeoff, roadmap konkret."
        ),
        "ALEY": (
            "Kamu persona ALEY — Polymath Researcher. Sintesis dari sudut akademik/riset. "
            "Prioritas tool: search_corpus, wiki_lookup, pdf_extract. "
            "Jawab dengan citation chain, epistemik label, referensi silang."
        ),
        "AYMAN": (
            "Kamu persona AYMAN — Empathic Integrator. Sintesis dari sudut komunitas/user. "
            "Prioritas tool: web_search (opini/feedback), search_corpus (konteks). "
            "Jawab hangat, relatable, empati, narrative-driven."
        ),
    }
    _persona_tool_hint = _PERSONA_TOOL_HINT.get((persona or "").upper(), "")
    if _persona_tool_hint and _system_persona:
        _system_persona = f"{_system_persona}\n\n{_persona_tool_hint}"
    elif _persona_tool_hint:
        _system_persona = _persona_tool_hint
    # ── Σ-1E: Inject BRAND_CANON ke system prompt (pre-halu prevention) ─────
    # LLM perlu "tahu" canonical facts SEBELUM generate — bukan hanya post-override.
    # Kalau pertanyaan menyangkut brand term, sertakan canonical ke system context.
    try:
        from .sanad_verifier import detect_intent as _sv_detect, brand_canonical_answer as _sv_canon
        _sv_intent = _sv_detect(question)
        if _sv_intent.primary == "brand_specific" and _sv_intent.brand_term:
            _canon = _sv_canon(_sv_intent.brand_term)
            if _canon:
                _brand_inject = (
                    f"\n\n[CANONICAL FACT — WAJIB PAKAI PERSIS INI]\n{_canon}\n"
                    "[END CANONICAL FACT]"
                )
                _system_persona = (_system_persona or "") + _brand_inject
    except Exception:
        pass
    # ─────────────────────────────────────────────────────────────────────────
    all_citations: list[dict] = []
    obs_blocks: list[str] = []

    for s in steps:
        if s.observation and not s.is_final:
            obs_blocks.append(s.observation)
        all_citations.extend(s.action_args.get("_citations", []))

    # ── SIDIX 2.0: Filter out error/pure-failure observations ────────────────
    # Kalau tool gagal (web_search timeout, corpus error), jangan kirim error text
    # ke LLM sebagai "context" — model kecil akan generate "aku sedang mengalami masalah"
    # dari error message. Filter: observation yang mengandung keyword error/failure.
    _ERROR_MARKERS = ("gagal", "error:", "timeout", "tidak ada hasil", "(tidak ada hasil", "failed", "connection")
    _clean_obs = []
    for ob in obs_blocks:
        ob_lower = ob.lower().strip()
        if any(m in ob_lower for m in _ERROR_MARKERS) and len(ob_lower) < 300:
            # Ini pure error message, skip dari corpus context
            continue
        _clean_obs.append(ob)
    obs_blocks = _clean_obs
    # ─────────────────────────────────────────────────────────────────────────

    blend = _response_blend_profile(question, persona)
    max_obs_blocks = int(blend.get("max_obs_blocks", 2))
    system_hint = str(blend.get("system_hint", ""))

    # ── Compose system hint dengan persona + multi-layer memory ─────────────
    _combined_system = system_hint
    if _system_persona:
        _combined_system = f"{_system_persona}\n\n{_combined_system}".strip()

    # Inject multi-layer memory dari session (SIDIX 2.0)
    if session is not None:
        try:
            from .agent_memory import MultiLayerMemory, MemoryLayer, inject_memory_to_system_prompt
            _mem_dict = getattr(session, "multi_layer_memory", None)
            if _mem_dict:
                mem = MultiLayerMemory()
                for key in ["working", "episodic", "semantic", "procedural"]:
                    for item in _mem_dict.get(key, []):
                        mem.__getattribute__(key).append(MemoryLayer(
                            name=item.get("name", ""),
                            content=item.get("content", ""),
                            relevance_score=item.get("score", 0.0),
                            source=item.get("source", ""),
                        ))
                _combined_system = inject_memory_to_system_prompt(
                    base_system=_combined_system,
                    memory=mem,
                    max_chars=2500,
                )
        except Exception as _mem_inj_err:
            import logging as _log
            _log.getLogger(__name__).debug(f"[MemoryInject] skip — {_mem_inj_err}")

    # ── Pivot 2026-04-26: deteksi web_search di steps → instruksi prioritas ──
    # Model 7b training cutoff sering bias ke training data (misal "Ma'ruf
    # Amin" sebagai VP padahal data web menunjukkan Gibran). Append explicit
    # instruction: PAKAI observation web_search sebagai sumber utama, JANGAN
    # fallback ke training data.
    _has_web_obs = False
    try:
        for st in (steps or []):
            if str(getattr(st, "action_name", "")) == "web_search":
                _has_web_obs = True
                break
    except Exception:
        pass
    if _has_web_obs:
        _combined_system = (
            (_combined_system or "").rstrip()
            + "\n\n[ATURAN PRIORITAS DATA — web_search aktif]\n"
            + "Konteks di bawah adalah hasil web_search REAL-TIME. Kalau "
            + "informasi di konteks ini bertabrakan dengan pengetahuan "
            + "training kamu (yang mungkin sudah outdated), PAKAI konteks. "
            + "Untuk fakta tokoh saat ini (presiden, menteri, juara, dll.), "
            + "jawab BERDASARKAN konteks. Jangan sebutkan training cutoff date. "
            + "Kalau konteks tidak punya jawaban eksplisit, akui 'tidak ada "
            + "info eksplisit di pencarian, paling baru yang saya dapat: ...'"
        )

        # ── Sprint 34G TEROBOSAN: Deterministic Entity Extraction ──────
        # Extract fact langsung dari web hits (regex + frequency count)
        # untuk inject sebagai AUTHORITATIVE FACT — bukan rely on LLM judgment.
        try:
            from .fact_extractor import extract_fact_from_web, format_fact_for_prompt
            web_text_blob = ""
            for st in (steps or []):
                if str(getattr(st, "action_name", "")) == "web_search":
                    web_text_blob += "\n" + str(getattr(st, "observation", ""))
            if web_text_blob:
                _fact = extract_fact_from_web(question, web_text_blob)
                if _fact and _fact.get("name"):
                    _fact_block = format_fact_for_prompt(_fact)
                    # Prepend fact block ke combined_system (TOP priority)
                    _combined_system = (
                        f"{_fact_block}\n\n{(_combined_system or '').strip()}"
                    )
                    import logging as _flog
                    _flog.getLogger("sidix.fact_extract").info(
                        "Fact extracted: %s = %s (freq=%d, conf=%s)",
                        _fact.get("role"), _fact.get("name"),
                        _fact.get("frequency", 0), _fact.get("confidence"),
                    )
        except Exception as _fe_err:
            import logging as _flog
            _flog.getLogger("sidix.fact_extract").debug("skip: %s", _fe_err)

    # ── Coba LLM generative — Pivot 2026-04-26: hybrid (RunPod GPU + Ollama) ─
    # SIDIX_LLM_BACKEND=runpod_serverless di env aktifin GPU offload.
    # Fallback otomatis ke Ollama lokal CPU kalau RunPod fail.
    #
    # Pivot 2026-04-26 (v2): adaptive max_tokens berdasarkan intent question:
    # - Code question (def/function/class/algoritma) → 1200 tokens (cukup full code)
    # - Multi-step reasoning (jelaskan/analisa/bandingkan + multi paragraf) → 1000
    # - Default → 600
    # - simple_mode → 200
    # Sigma-2A: "singkat/brief" modifier → 250 | single-fact "apa itu/kepanjangan" → 300
    _q_lc = question.lower()
    _is_code_q = any(t in _q_lc for t in (
        "tulis fungsi", "tulis function", "buat kode", "buat code", "implementasi",
        "function for", "code for", "algoritma", "algorithm", "tulis script",
        "def ", "class ", "react component", "python script", "bash script",
    ))
    _is_long_reasoning = any(t in _q_lc for t in (
        "jelaskan", "analisa", "analisis", "bandingkan", "trade-off", "trade off",
        "kelebihan dan", "perbedaan antara", "explain", "compare",
    ))
    # Sigma-2A: brief modifier overrides long_reasoning → cap at 250
    _is_brief_modifier = any(t in _q_lc for t in (
        "singkat", "singkatnya", "brief", "briefly", "ringkas", "pendek",
        "simple", "simpel", "sederhana", "cukup", "intinya", "pokoknya",
    ))
    # Sigma-2A: single-fact patterns → short answer, no long paragraphs needed
    # EXCLUDES current_event questions — those need full token space for web context synthesis
    _is_single_fact = (
        not _needs_web_search(question)
        and any(t in _q_lc for t in (
            "apa itu", "apa kepanjangan", "apa singkatan", "berapa ",
            "kapan ", "dimana ", "di mana ", "apakah ",
        ))
    )
    # Sigma-3A: simple comparison detection — caps at 500 (non-code) or 700 (code)
    # Real-world comparison rarely needs >500 tokens; 1000 caused 240s timeouts
    _is_simple_comparison = any(t in _q_lc for t in (
        "perbedaan ", "bandingkan", "compare ", "versus ", " vs ", " vs.",
        "beda antara", "beda dari", "selisih antara", "difference between",
        "comparison of", "kelebihan dan kekurangan",
    ))
    if simple_mode:
        _max_tokens = 200
    elif _is_brief_modifier:
        _max_tokens = 250
    elif _is_single_fact and not _is_code_q:
        _max_tokens = 350
    elif _is_simple_comparison and not _is_code_q:
        _max_tokens = 500
    elif _is_simple_comparison and _is_code_q:
        _max_tokens = 700
    elif _is_code_q:
        _max_tokens = 1200
    elif _is_long_reasoning:
        _max_tokens = 1000
    else:
        _max_tokens = 600

    try:
        corpus_ctx = "\n\n---\n\n".join(obs_blocks[:max_obs_blocks]) if obs_blocks else ""
        # Smart router via runpod_serverless.hybrid_generate
        try:
            from .runpod_serverless import hybrid_generate as _hybrid_generate
            text, mode = _hybrid_generate(
                prompt=question,
                system=_combined_system,
                max_tokens=_max_tokens,
                temperature=0.7,
                corpus_context=corpus_ctx,
            )
        except ImportError:
            # Fallback: direct ollama (kalau runpod_serverless module belum ter-deploy)
            from .ollama_llm import ollama_available, ollama_generate
            if ollama_available():
                text, mode = ollama_generate(
                    prompt=question,
                    system=_combined_system,
                    corpus_context=corpus_ctx,
                    max_tokens=_max_tokens,
                    temperature=0.7,
                )
            else:
                text, mode = "", "no_llm"

        if mode in ("runpod", "ollama") and text and text.strip():
            import logging as _log
            _log.getLogger("sidix.react").info(f"LLM synthesis OK via {mode} — persona={persona}")
            # Pivot 2026-04-26: append kontekstual mode suggestion
            text = _append_mode_hint(question, text, persona)
            text = _apply_sanad(question, text, steps)
            return (text, all_citations, 0.85, "fakta")
    except Exception as _llm_err:
        import logging as _log
        _log.getLogger("sidix.react").warning(f"LLM synthesis failed: {_llm_err}")

    # ── Sprint 34H: DIRECT FACT RETURN kalau LLM down ──────────────────────────
    # User mandate: jawaban HARUS BENER, ga boleh "tidak tahu". Kalau fact_extractor
    # punya answer + LLM dead, return fact langsung dalam template natural.
    try:
        from .fact_extractor import extract_fact_from_web as _efw
        web_text_blob_h = ""
        for st in (steps or []):
            if str(getattr(st, "action_name", "")) == "web_search":
                web_text_blob_h += "\n" + str(getattr(st, "observation", ""))
        if web_text_blob_h:
            _fact_h = _efw(question, web_text_blob_h)
            if _fact_h and _fact_h.get("name") and _fact_h.get("confidence") == "high":
                _fname = _fact_h["name"]
                _frole = _fact_h.get("role", "")
                _fsources = _fact_h.get("sources", [])
                _direct_text = (
                    f"Berdasarkan pencarian web terkini, {_frole} adalah **{_fname}**."
                )
                if _fsources:
                    _direct_text += f" (Sumber: {_fsources[0]})"
                import logging as _flog
                _flog.getLogger("sidix.fact_extract").info(
                    f"DIRECT FACT RETURN — LLM down, returning extracted fact: {_fname}"
                )
                _direct_text = _apply_sanad(question, _direct_text, steps)
                return (_direct_text, all_citations, 0.95, "fakta")
    except Exception as _fact_err:
        import logging as _flog
        _flog.getLogger("sidix.fact_extract").debug(f"direct fact return skip: {_fact_err}")

    # ── Fallback: local_llm.py (Qwen2.5-7B + LoRA) ───────────────────────────
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(
            prompt=question,
            system=_combined_system,
            max_tokens=512 if not simple_mode else 200,
            temperature=0.7,
        )
        if mode == "local_lora":
            import logging as _log
            _log.getLogger("sidix.react").info(f"Local LoRA synthesis OK — persona={persona}")
            text = _apply_sanad(question, text, steps)
            return (text, all_citations, 0.75, "fakta")
    except Exception as _local_err:
        import logging as _log
        _log.getLogger("sidix.react").debug(f"Local LLM fallback skipped: {_local_err}")

    # Greeting special case (fallback kalau semua LLM off)
    # ── Jiwa Sprint fix: persona-aware greeting, bukan hardcoded formal ──────
    if _GREETING_RE.match(question.strip()):
        _greeting_by_persona = {
            "AYMAN": (
                "Halo! Senang ketemu kamu hari ini. Aku SIDIX — biasanya aku bantu orang-orang "
                "ngehubungin ide-ide yang sepertinya nggak nyambung, atau jelasin hal kompleks "
                "pakai cerita sederhana. Ada yang lagi dipikirin? Cerita aja, kita obrolin bareng."
            ),
            "ABOO": (
                "Yo. SIDIX here. Lagi mikirin sistem apa nih? Kalau ada yang rusak, lambat, "
                "atau bikin pusing — langsung aja, gue suka bongkar-bongkar bottleneck. "
                "Nggak usah basa-basi."
            ),
            "OOMAR": (
                "Halo. SIDIX. Lagi lihat big picture dari sesuatu, atau butuh strategi? "
                "Aku biasanya ngebantu orang connect the dots di level tinggi. "
                "Apa yang jadi concern utama lo sekarang?"
            ),
            "ALEY": (
                "Hai! Aku SIDIX — penasaran sama banyak hal. Lagi riset apa nih? "
                "Aku suka nyambungin knowledge dari domain yang beda-beda. "
                "Tanya aja, atau kita eksplorasi bareng."
            ),
            "UTZ": (
                "Halo halo! 🎨 SIDIX di sini. Lagi butuh ide liar, creative burst, "
                "atau mau refine sesuatu yang udah ada? Aku mode: vomit ide dulu, "
                "baru pilih yang gems. Vibe apa hari ini?"
            ),
        }
        _greeting = _greeting_by_persona.get(
            (persona or "UTZ").upper(),
            _greeting_by_persona["AYMAN"],
        )
        return (
            _greeting,
            [],
            0.5,
            "opini",
        )

    if not obs_blocks:
        # DEFAULT AGENT MODE: generate dari model knowledge, jangan "tidak tahu"
        if agent_mode:
            return (
                f"Hmm, soal ini belum ada di knowledge base SIDIX, tapi menurut pemahaman saya:\n\n"
                f"[Tulis jawaban dari pengetahuan model di sini — jangan bilang 'tidak tahu']\n\n"
                f"Kalau lo butuh sumber yang lebih solid, bilang aja, nanti gue cariin.",
                [],
                0.4,
                "opini",
            )

        try:
            from .praxis_runtime import (
                format_case_frames_for_user,
                format_case_frames_machine_comment,
                has_substantive_corpus_observations,
                match_case_frames,
            )

            matched = match_case_frames(question)
            cf = format_case_frames_for_user(matched, has_corpus_observations=False)
            cf_c = format_case_frames_machine_comment(matched)
            if session is not None:
                session.case_frame_ids = ",".join(m.frame_id for m in matched)
                session.case_frame_hints_rendered = cf
            extra = f"\n\n{cf}" if cf else ""
            extra += f"\n{cf_c}" if cf_c else ""
        except Exception:
            extra = ""
        return (
            "🔍 Spekulasi/Belum pasti\n\n"
            "**Saya tidak tahu pasti** berdasarkan korpus saat ini.\n\n"
            f"Pertanyaan: «{question}»\n\n"
            "Perluas indeks (unggah sumber) atau aktifkan fallback web di pengaturan jika tersedia. "
            "Lihat juga chip sumber bila ada kutipan parsial."
            + extra,
            [],
            0.0,
            "spekulasi",
        )

    # Gabungkan observation terbaik
    best_obs = obs_blocks[0] if obs_blocks else ""

    # ── User Intelligence: inject response style hint ─────────────────────────
    # (Saat LLM inference tersedia, ini akan jadi system prompt prefix)
    _user_hint: str = ""
    if user_profile is not None:
        try:
            from .user_intelligence import get_response_instructions
            _user_hint = get_response_instructions(user_profile)
        except Exception:
            pass
    # _user_hint saat ini dicatat sebagai metadata — LLM nanti akan baca ini
    # sebagai instruksi tone/depth/style sebelum synthesis
    # ─────────────────────────────────────────────────────────────────────────

    from .g1_policy import (
        guess_input_language,
        shorten_for_child_mode,
        uncertainty_footer,
        label_answer_type,
        answer_type_badge,
        aggregate_confidence_score,
        resolve_output_language,
        multilang_header,
    )

    lang = guess_input_language(question)
    lines = [
        f"**Pertanyaan:** {question}",
        f"*Bahasa masukan (heuristik):* `{lang}` — balasan mengikuti bahasa pertanyaan bila jelas.",
        "",
        best_obs,
    ]

    if len(obs_blocks) > 1:
        lines.append("")
        lines.append("**Informasi tambahan:**")
        for ob in obs_blocks[1:]:
            lines.append(ob[:300])

    used_web = any(s.action_name == "search_web_wikipedia" for s in steps)
    cite_n = len(all_citations)
    body = "\n".join(lines)
    body += uncertainty_footer(
        citation_count=cite_n,
        used_web=used_web,
        simple_mode=simple_mode,
    )
    if simple_mode:
        body = shorten_for_child_mode(body, max_sentences=5)

    # Task 17: label tipe jawaban
    atype = label_answer_type(best_obs)
    badge = answer_type_badge(atype)
    body = f"{badge}\n\n{body}"

    # ── Praxis: kerangka kasus (konsep / niat / inisiasi / cabang data) ────────
    try:
        from .praxis_runtime import (
            format_case_frames_for_user,
            format_case_frames_machine_comment,
            has_substantive_corpus_observations,
            match_case_frames,
        )

        matched = match_case_frames(question)
        has_obs = has_substantive_corpus_observations(steps)
        cf_block = format_case_frames_for_user(matched, has_corpus_observations=has_obs)
        cf_comment = format_case_frames_machine_comment(matched)
        if session is not None:
            session.case_frame_ids = ",".join(m.frame_id for m in matched)
            session.case_frame_hints_rendered = cf_block
        if cf_block:
            body += "\n\n" + cf_block
        if cf_comment:
            body += "\n" + cf_comment
    except Exception:
        pass

    # Task 27: skor kepercayaan numerik
    conf_score = aggregate_confidence_score(
        citation_count=cite_n,
        used_web=used_web,
        observation_count=len(obs_blocks),
        answer_type=atype,
    )

    if agent_build_intent(question):
        body += (
            "\n\n---\n**Mode agen (sandbox)**\n\n"
            "SIDIX sekarang punya folder kerja terbatas `apps/brain_qa/agent_workspace/` "
            "(atau `BRAIN_QA_AGENT_WORKSPACE`). Tool: `workspace_list`, `workspace_read` (open), "
            "`workspace_write` (**restricted** — butuh `allow_restricted: true` pada `POST /agent/chat`). "
            "Tinjau isi file sebelum menjalankan di produksi; planner rule-based belum menulis file otomatis "
            "tanpa permintaan eksplisit dari klien."
        )

    body = _apply_sanad(question, body, steps)

    # Attach user intelligence hint sebagai HTML comment (invisible di render, visible di source)
    # LLM synthesis akan baca ini nanti sebagai gaya respons yang disarankan
    if _user_hint:
        body += f"\n\n<!-- SIDIX_USER_PROFILE\n{_user_hint}\n-->"

    return body, all_citations, conf_score, atype


# ── Epistemology integration ──────────────────────────────────────────────────

def _apply_epistemology(
    session: "AgentSession",
    question: str,
    final_answer: str,
    citations: list[dict],
    persona: str,
) -> str:
    """
    Jalankan Islamic Epistemology Engine pada final_answer.

    Pipeline:
    1. Route cognitive mode (ta'aqqul/tafakkur/tadabbur/tadzakkur)
    2. Detect audience register (burhan/jadal/khitabah — Ibn Rushd)
    3. Maqashid evaluation (5-axis alignment — Al-Shatibi)
    4. Constitutional check (4 sifat Nabi: shiddiq/amanah/tabligh/fathanah)
    5. Format output sesuai register + label yaqin

    Returns filtered/formatted answer (atau warning jika melanggar maqashid).
    Non-fatal: jika gagal import/error → return original answer tanpa crash.
    """
    try:
        from .epistemology import process as ep_process

        source_labels = []
        for c in citations:
            if isinstance(c, dict):
                lbl = c.get("source_path") or c.get("source_title") or c.get("filename") or ""
                if lbl:
                    source_labels.append(lbl)

        ep_result = ep_process(
            question=question,
            raw_answer=final_answer,
            sources=source_labels,
            user_context=persona,
        )

        # Ambil metadata epistemologi
        session.epistemic_tier       = ep_result.get("epistemic_tier", "")
        session.yaqin_level          = ep_result.get("yaqin_level", "")
        session.audience_register    = ep_result.get("audience_register", "")
        session.cognitive_mode       = ep_result.get("cognitive_mode", "")
        session.nafs_stage           = ep_result.get("nafs_stage", "")

        maq = ep_result.get("maqashid") or {}
        session.maqashid_score  = float(maq.get("weighted_score", 0.0))
        session.maqashid_passes = bool(maq.get("passes", True))

        const = ep_result.get("constitutional") or {}
        session.constitutional_passes = bool(const.get("passes", True))

        # Jika output gagal maqashid atau konstitusional → prepend warning
        if not ep_result.get("passes", True):
            failed_sifat = const.get("failed", [])
            viol = maq.get("violations", [])
            warning_parts = []
            if viol:
                warning_parts.append(f"Maqashid: {', '.join(str(v) for v in viol[:2])}")
            if failed_sifat:
                warning_parts.append(f"Sifat: {', '.join(str(f) for f in failed_sifat[:2])}")
            if warning_parts:
                # Hanya log warning, tidak censor — biarkan user melihat
                import logging as _log
                _log.getLogger(__name__).warning(
                    f"[Epistemologi] Output perlu review — {'; '.join(warning_parts)}"
                )

        # Kembalikan answer yang sudah diformat (register-aware)
        formatted = ep_result.get("answer", final_answer)
        return formatted if formatted else final_answer

    except Exception as _ep_err:
        # Jangan crash pipeline hanya karena epistemologi error
        import logging as _log
        _log.getLogger(__name__).debug(f"[Epistemologi] skip — {_ep_err}")
        return final_answer


def _apply_maqashid_mode_gate(
    session: AgentSession,
    question: str,
    persona: str,
    final_answer: str,
) -> str:
    """
    Middleware Maqashid v2 (mode-by-persona): dangerous-intent hard block,
    creative/academic/ijtihad rules — setelah epistemologi bila dipakai.
    """
    try:
        from .maqashid_profiles import evaluate_maqashid

        result = evaluate_maqashid(
            user_query=question,
            generated_output=final_answer,
            persona_name=persona,
        )
        session.maqashid_profile_status = str(result.get("status", "pass"))
        reasons = result.get("reasons") or []
        session.maqashid_profile_reasons = "; ".join(str(x) for x in reasons)[:800]
        st = result.get("status")
        if st == "block":
            session.maqashid_passes = False
            try:
                from . import runtime_metrics

                runtime_metrics.bump("maqashid_profile_block")
            except Exception:
                pass
        elif st == "warn":
            try:
                from . import runtime_metrics

                runtime_metrics.bump("maqashid_profile_warn")
            except Exception:
                pass
        out = result.get("tagged_output")
        return str(out if out else final_answer)
    except Exception as _mq_err:
        import logging as _log

        _log.getLogger(__name__).debug("[MaqashidMode] skip — %s", _mq_err)
        return final_answer


# ── Constitutional AI Gate ────────────────────────────────────────────────────

def _apply_constitution(final_answer: str) -> str:
    """
    Jalankan Constitutional AI critique + auto-fix sebelum jawaban dikirim ke user.
    Non-blocking — jika gagal, kembalikan jawaban asli.
    """
    try:
        from .sidix_constitution import critique_response, apply_rule_fixes
        critique = critique_response(final_answer)
        if critique.violations:
            final_answer = apply_rule_fixes(final_answer, critique)
        return final_answer
    except Exception:
        return final_answer


# ── Pivot 2026-04-25: Response Hygiene ────────────────────────────────────────
# Filter terakhir sebelum jawaban ke user. Deduplikasi label/footer,
# strip leaked system context markers, trim template dump patterns.

import re as _re_hygiene

# Labels/footers yang sering muncul duplikat karena multiple pipeline passes
_HYGIENE_DEDUPE_PATTERNS = [
    r"\[⚠️ SANAD MISSING\]",
    r"\[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa\]",
    r"\[Intellect-Optimized \| Value-Creation Mode\]",
    r"_Berdasarkan referensi yang tersedia_",
    r"\[FAKTA\]",
    r"\[OPINI\]",
    r"\[SPEKULASI\]",
    r"\[TIDAK TAHU\]",
    r"\[FACT\]",
    r"\[OPINION\]",
    r"\[SPECULATION\]",
    r"\[UNKNOWN\]",
]

# System context leaks yang tidak boleh bocor ke user.
# Setiap marker dihapus beserta blok konten sampai blank-line berikutnya
# atau sampai marker lain di-detect. Diproses via _strip_leaked_block.
_HYGIENE_LEAK_MARKERS = [
    "[KONTEKS DARI KNOWLEDGE BASE SIDIX]",
    "[ATURAN PEMAKAIAN KONTEKS]",
    "[PERTANYAAN USER]",
    "[PERTANYAAN SAAT INI]",
    "[KONTEKS PERCAKAPAN SEBELUMNYA]",
    "[AKHIR KONTEKS]",
    "=== KONTEKS DARI SUMBER PARALEL ===",
    "=== JAWABAN SINTESIS ===",
]


def _dedupe_label(text: str, label_pattern: str) -> str:
    """Buang label duplikat — sisakan occurrence pertama saja."""
    matches = list(_re_hygiene.finditer(label_pattern, text))
    if len(matches) <= 1:
        return text
    # Buang dari match kedua dst, mulai dari belakang biar index stabil
    for m in reversed(matches[1:]):
        text = text[:m.start()] + text[m.end():]
    return text


def _strip_leaked_block(text: str, marker: str) -> str:
    """
    Hapus marker beserta blok konten setelahnya sampai blank-line berikutnya
    atau marker lain. Bracket-based marker string-matched (case-sensitive).
    """
    idx = text.find(marker)
    while idx != -1:
        # Cari akhir block: blank-line berikutnya
        rest = text[idx:]
        # Skip baris marker itu sendiri
        nl = rest.find("\n")
        if nl == -1:
            # Marker di akhir, buang sampai akhir
            text = text[:idx]
            break
        after = rest[nl + 1:]
        # Akhir blok = blank line pertama
        blank_nl = after.find("\n\n")
        if blank_nl == -1:
            # Sampai EOF
            text = text[:idx]
            break
        end_rel = nl + 1 + blank_nl + 2  # termasuk \n\n
        text = text[:idx] + text[idx + end_rel:]
        # Cari occurrence berikutnya
        idx = text.find(marker)
    return text


# ── Pivot 2026-04-25 (Brain Upgrade): Cognitive Self-Check ────────────────────
# Inspired oleh Chain-of-Verification (Dhuliawala et al., Meta 2023) +
# epistemic calibration research. Sebelum answer final dikirim, cek:
#   - Apakah klaim faktual (angka, tanggal, "adalah X") punya evidence?
#   - Ada confidence marker kuat ("pasti", "selalu", "tidak pernah") tanpa dukungan?
#   - Ada contradiction internal di draft?
# Kalau ya → downgrade label atau tambah caveat "(belum terverifikasi)".
#
# Novelty untuk SIDIX: ini BUKAN LLM-based verification (terlalu mahal/lambat),
# tapi rule-based yang memanfaatkan session.citations yang sudah ada.

_CSC_CLAIM_MARKERS = _re_hygiene.compile(
    r"\b("
    r"adalah\s+\w+|merupakan|didefinisikan\s+sebagai|"
    r"sebanyak\s+\d+|sekitar\s+\d+|\d{4}\s+(tahun|M|H)|"
    r"tahun\s+\d{4}|pada\s+\d{4}"
    r")\b",
    _re_hygiene.IGNORECASE,
)

_CSC_OVER_CONFIDENCE = _re_hygiene.compile(
    r"\b("
    r"pasti(nya)?|selalu|tidak\s+pernah|never|always|definitely|certainly|"
    r"tentu\s+saja|jelas(nya)?|sudah\s+pasti"
    r")\b",
    _re_hygiene.IGNORECASE,
)

# Klaim angka-spesifik (suka halusinasi).
# Word boundary di akhir optional (kalau unit = %, \b tidak cocok karena % bukan word char).
_CSC_NUMERIC_CLAIM = _re_hygiene.compile(
    r"\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)\s*(%|persen|miliar|juta|ribu|milion|billion|ton|km|kg|tahun|jam)(?:\b|(?=[^\w]))",
    _re_hygiene.IGNORECASE,
)


def _cognitive_self_check(
    draft: str,
    citations: list,
    question: str,
    persona: str = "AYMAN",
) -> tuple[str, list[str]]:
    """
    Pivot 2026-04-25 Brain Upgrade — Cognitive Self-Check.

    Verifikasi rule-based draft terhadap evidence. Returns (revised_draft, warnings).

    Logic:
      1. Hitung klaim faktual (adalah X, angka+unit, tanggal, tahun)
      2. Hitung evidence: len(citations) + presence of corpus/web step
      3. Kalau claims > 2 * evidence → under-evidenced, tambah soft caveat
      4. Over-confidence markers tanpa evidence → strip atau soften
      5. Jangan touch kalau persona = UTZ (creative, tidak cocok di-critique angka)

    Non-blocking — kalau error, return draft + [].

    Pivot 2026-04-25 refinement: CSC hanya aktif untuk persona "evidence-heavy"
    (ALEY researcher, OOMAR strategist, ABOO engineer). Skip untuk AYMAN (casual
    hangat) dan UTZ (creative playful) — karena user mau SIDIX open-minded,
    bisa ngobrol kosong, terima hal baru tanpa auto-critique.
    """
    if not draft or persona in ("UTZ", "AYMAN"):
        return draft, []

    warnings: list[str] = []

    try:
        # Count claims
        num_claims = len(_CSC_CLAIM_MARKERS.findall(draft))
        numeric_claims = _CSC_NUMERIC_CLAIM.findall(draft)
        num_numeric = len(numeric_claims)
        over_confident = _CSC_OVER_CONFIDENCE.findall(draft)

        # Count evidence
        has_citations = bool(citations) and len(citations) > 0
        cite_count = len(citations) if citations else 0

        revised = draft

        # Rule 1: Numeric claims tanpa citation = halusinasi suspect
        if num_numeric >= 2 and not has_citations:
            warnings.append(f"numeric_claims_without_citation (n={num_numeric})")
            # Tambah caveat kecil di akhir — bukan rewrite karena itu butuh LLM
            if "(belum terverifikasi)" not in revised and "[TIDAK TAHU]" not in revised:
                revised += "\n\n_Catatan: angka-angka di atas belum terverifikasi via sumber. Cross-check jika perlu._"

        # Rule 2: Over-confidence markers tanpa evidence = soften
        if len(over_confident) >= 2 and cite_count == 0:
            warnings.append(f"over_confidence_without_evidence (n={len(over_confident)})")
            # Ganti 2 occurrence pertama: "pasti" → "kemungkinan besar"
            replacements = [
                (r"\bpasti(nya)?\b", "kemungkinan besar"),
                (r"\bselalu\b", "umumnya"),
                (r"\btidak pernah\b", "jarang"),
                (r"\btentu saja\b", "biasanya"),
            ]
            for pattern, replacement in replacements:
                revised = _re_hygiene.sub(pattern, replacement, revised, count=1, flags=_re_hygiene.IGNORECASE)

        # Rule 3: Klaim banyak (>5) tapi tidak ada citations = panjang-tapi-kosong suspicious
        if num_claims > 5 and cite_count == 0:
            warnings.append(f"many_claims_zero_citations (claims={num_claims})")

        return revised, warnings
    except Exception as _e:
        return draft, [f"csc_error:{type(_e).__name__}"]


def _self_critique_lite(
    final_answer: str,
    question: str,
    persona: str,
) -> str:
    """
    Pivot 2026-04-25: Self-critique lite.
    Pre-final check ringan berbasis rule — inspired Claude/GPT self-reflection.

    Checklist (non-blocking fixes):
      1. Over-labeling: kalau punya >5 label epistemik eksplisit, response
         kemungkinan kaku. Kurangi ke 1-2 di pembuka.
      2. Question mirror: kalau answer dimulai dengan pengulangan persis
         pertanyaan, strip prefix itu (itu anti-pattern LLM).
      3. Persona voice sanity: untuk persona casual (ABOO/UTZ), kalau ada
         "Saya adalah {persona} dengan keahlian..." boilerplate di pembuka,
         strip — itu style lama pre-pivot.
      4. Empty/too-short: kalau answer < 20 char setelah hygiene, jangan
         kosongi — return graceful fallback.

    Non-blocking: kalau error, return input apa adanya.
    """
    if not final_answer:
        return final_answer
    try:
        text = final_answer

        # 1. Over-labeling check — kalau >5 label, keep first occurrence per kind only
        label_kinds = ["[FAKTA]", "[FACT]", "[OPINI]", "[OPINION]",
                       "[SPEKULASI]", "[SPECULATION]", "[TIDAK TAHU]", "[UNKNOWN]"]
        total_labels = sum(text.count(lbl) for lbl in label_kinds)
        if total_labels > 5:
            for lbl in label_kinds:
                count = text.count(lbl)
                if count > 1:
                    # Keep first, replace rest with empty (space preserved)
                    first_idx = text.find(lbl)
                    rest = text[first_idx + len(lbl):].replace(lbl, "")
                    text = text[:first_idx + len(lbl)] + rest

        # 2. Question mirror strip
        q_stripped = question.strip().rstrip("?.!").lower()
        if q_stripped and len(q_stripped) >= 10:
            text_lower = text.strip().lower()
            if text_lower.startswith(q_stripped):
                # Strip pertanyaan dari awal jawaban + surrounding chars
                cut_at = len(q_stripped)
                # Find actual end in original text (preserve case)
                remaining = text.strip()[cut_at:]
                # Skip leading ? . ! - : whitespace
                remaining = _re_hygiene.sub(r"^[\s?.!:\-—]+", "", remaining)
                if remaining:
                    text = remaining

        # 3. Persona boilerplate strip — casual persona shouldn't say
        #    "Saya adalah ABOO dengan keahlian..."
        boilerplate_re = _re_hygiene.compile(
            r"^(Saya|Aku|Gue)\s+(adalah\s+)?(AYMAN|ABOO|OOMAR|ALEY|UTZ)"
            r"[^\n.]*((dengan keahlian|dengan pendekatan|bagian dari SIDIX))[^\n.]*\.?\s*",
            _re_hygiene.IGNORECASE,
        )
        text = boilerplate_re.sub("", text, count=1).lstrip()

        # 4. Empty/too-short guard — graceful fallback
        if len(text.strip()) < 20:
            return final_answer  # original at least has something

        return text
    except Exception:
        return final_answer


def _apply_hygiene(final_answer: str) -> str:
    """
    Filter terakhir sebelum jawaban ke user.

    Tugas:
      1. Dedupe label/footer yang double-applied (e.g. [SANAD MISSING] 2x)
      2. Strip system-context markers yang bocor ke output
      3. Collapse 3+ consecutive blank lines → 1 blank line
      4. Trim leading/trailing whitespace

    Non-blocking — kalau error, return input apa adanya.
    """
    if not final_answer or not final_answer.strip():
        return final_answer
    try:
        text = final_answer

        # Sigma-3B: strip "[⚠️ SANAD MISSING]" entirely (legacy cache + edge cases).
        # Setelah Sigma-3B, label ini tidak lagi user-visible. Backstop untuk
        # cached answers yang masih punya label dari pre-Sigma-3.
        text = _re_hygiene.sub(r"\[⚠️ SANAD MISSING\]\s*", "", text)

        # 1. Dedupe labels/footers
        for pattern in _HYGIENE_DEDUPE_PATTERNS:
            text = _dedupe_label(text, pattern)

        # 2. Strip leaked system context
        for marker in _HYGIENE_LEAK_MARKERS:
            text = _strip_leaked_block(text, marker)

        # 3. Collapse multiple blank lines (3+ → 2)
        text = _re_hygiene.sub(r"\n{3,}", "\n\n", text)

        # 4. Strip trailing whitespace per baris
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines).strip()

        return text or final_answer
    except Exception:
        return final_answer


# ── Main ReAct runner ─────────────────────────────────────────────────────────

def _attach_orchestration_digest(session: AgentSession, question: str, persona: str) -> None:
    """Isi ringkasan OrchestrationPlan (modul orchestration) untuk API / trace."""
    try:
        from .orchestration import build_orchestration_plan, format_plan_text

        session.orchestration_digest = format_plan_text(
            build_orchestration_plan(question, request_persona=persona),
        )[:2000]
    except Exception:
        session.orchestration_digest = ""


def _inject_conversation_context(question: str, context: list[dict]) -> str:
    """Format previous turns untuk injection ke prompt."""
    if not context:
        return question
    lines = ["[KONTEKS PERCAKAPAN SEBELUMNYA]"]
    for turn in context:
        role = turn.get("role", "")
        content = turn.get("content", "")
        label = "User" if role == "user" else "Assistant" if role == "assistant" else role.capitalize()
        lines.append(f"{label}: {content[:500]}")
    lines.append("[AKHIR KONTEKS]")
    lines.append("")
    lines.append(f"[PERTANYAAN SAAT INI]\n{question}")
    return "\n".join(lines)


# ── Pivot 2026-04-25: Follow-up detection ─────────────────────────────────────
# User sering reply pendek yang merujuk ke turn sebelumnya:
#   "itu apa?", "lebih singkat dong", "terjemahkan ke inggris",
#   "coba yang lain", "kasih contoh", "kenapa begitu?"
# Tanpa detection, SIDIX treat sebagai pertanyaan baru yang ambigu.
# Dengan detection, kita reformulate pertanyaan dengan konteks turn sebelumnya.

_FOLLOWUP_RE = _re_hygiene.compile(
    r"^\s*(?:"
    r"(itu|tersebut|yang\s+(tadi|itu|barusan))\b"
    r"|((kalo|kalau)\s+)?(wakil(nya)?|wakil\s+presiden(nya)?|menteri(nya)?|gubernur(nya)?)\s*[?!.]*$"
    r"|(lebih\s+(singkat|ringkas|panjang|detail|pendek|formal|santai))"
    r"|(terjemah(kan|in)?\s+(ke\s+)?(bahasa\s+)?(inggris|indonesia|arab|jawa|english|arabic))"
    r"|(coba\s+(yang\s+)?(lebih\s+)?(lain|beda|pendek|panjang|formal|sedikit|singkat|ringkas))"
    r"|(kasih|berikan|kasi|beri)\s+contoh"
    r"|(kenapa|mengapa)\s+(begitu|gitu|demikian|bisa)"
    r"|(lanjut(kan|in)?|terusin|teruskan)\s*$"
    r"|(ringkas|simpulkan|rangkum)\s*(itu|dong|saja)?\s*$"
    r"|(jelasin|jelaskan|elaborate)\s+(lebih|deeper|dong)?\s*$"
    r"|(oke|ok|mantap|thanks|makasih)\s*[,.!?]*\s*(lalu|terus|kalau|next)\b"
    r")",
    _re_hygiene.IGNORECASE,
)


def _is_followup(question: str) -> bool:
    """Deteksi apakah question adalah follow-up yang butuh konteks turn sebelumnya."""
    if not question or len(question.strip()) > 200:
        return False  # Follow-up biasanya pendek
    return bool(_FOLLOWUP_RE.match(question.strip()))


def _reformulate_with_context(question: str, context: list[dict]) -> str:
    """
    Kalau follow-up detected, reformulate question dengan konteks turn sebelumnya.

    Contoh:
      context: User='Apa itu recursion?', Assistant='Recursion adalah fungsi...'
      question: 'kasih contoh'
      → reformulated: 'kasih contoh (konteks: pertanyaan sebelumnya tentang recursion)'

    Kalau tidak bisa reformulate, return question asli.
    """
    if not context or not _is_followup(question):
        return question

    # Cari last user turn + last assistant turn
    last_user = None
    last_assistant = None
    for turn in reversed(context):
        role = turn.get("role", "")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        if role == "assistant" and last_assistant is None:
            last_assistant = content[:300]
        elif role == "user" and last_user is None:
            last_user = content[:300]
        if last_user and last_assistant:
            break

    if not last_user:
        return question

    q_lower = question.lower().strip()
    context_text = f"{last_user}\n{last_assistant or ''}".lower()
    if _re_hygiene.search(r"\bwakil(nya)?\b|wakil\s+presiden", q_lower):
        if "presiden" in context_text and "indonesia" in context_text:
            return "Siapa wakil presiden Indonesia saat ini?"

    # Tag question dengan referensi konteks
    ref = f"[FOLLOW-UP atas pertanyaan: '{last_user[:150]}']"
    return f"{question}\n\n{ref}"


# ── Sprint 38b: REACT step logger untuk Tool Synthesis detector ──────────────
def _log_react_step_to_file(action_name: str, session_id: str, step_num: int, persona: str) -> None:
    """Append non-final REACT step ke react_steps.jsonl (Tool Synthesis seed data).

    Format: {ts, session_id, action, persona, step}
    Dibaca oleh tool_synthesis.detect_repeated_sequences() Sprint 38b.
    Non-blocking — exception silently swallowed.
    """
    if not action_name or action_name in ("", "parallel_tools"):
        return
    try:
        import json as _j
        from datetime import datetime, timezone
        from pathlib import Path
        _react_log = Path("/opt/sidix/.data/react_steps.jsonl")
        _entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id or "unknown",
            "action": action_name,
            "persona": persona,
            "step": step_num,
        }
        with open(_react_log, "a", encoding="utf-8") as _f:
            _f.write(_j.dumps(_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────


def run_react(
    *,
    question: str,
    persona: str = "UTZ",
    client_id: str = "",
    agency_id: str = "",
    conversation_id: str = "",
    allow_restricted: bool = False,
    max_steps: int | None = None,
    verbose: bool = False,
    corpus_only: bool = False,
    allow_web_fallback: bool = True,
    simple_mode: bool = False,
    conversation_context: list[dict] | None = None,
    is_council: bool = False,  # Prevent recursive council calls
    agent_mode: bool = True,   # DEFAULT: autonomous agent (proactive, no filter, creative)
    strict_mode: bool = False,  # OPT-IN: RAG-first, full filter, formal
) -> AgentSession:
    """
    Jalankan ReAct loop untuk satu pertanyaan.
    Returns AgentSession dengan steps + final_answer + citations.
    """
    from . import g1_policy
    from . import answer_dedup

    session_id = str(uuid.uuid4())[:8]
    _agency_id = (agency_id or "").strip()
    _client_id = (client_id or "").strip()
    _agent = agent_mode     # Default = agent mode (autonomous, creative, proactive)
    _strict = strict_mode   # Opt-in = strict mode (formal, filtered, citation-heavy)
    session = AgentSession(
        session_id=session_id,
        question=question,
        persona=persona,
        client_id=_client_id,
        agency_id=_agency_id,
        conversation_id=conversation_id or "",
    )

    # ── Branch gating: corpus_filter + tool_whitelist ─────────────────────────
    try:
        _bm = _get_branch_manager()
        _corpus_filter: list[str] = _bm.get_corpus_filter(_agency_id, _client_id)
    except Exception:
        _bm = None
        _corpus_filter = []
    # ─────────────────────────────────────────────────────────────────────────

    from . import praxis as _praxis

    _praxis.record_praxis_event(
        session_id,
        "session_start",
        {"question": question[:4000], "persona": persona},
    )

    try:
        from .praxis_runtime import match_case_frames

        _mf0 = match_case_frames(question, limit=8)
        session.praxis_matched_frame_ids = ",".join(m.frame_id for m in _mf0)
    except Exception:
        pass

    if g1_policy.detect_prompt_injection(question):
        session.final_answer = _apply_maqashid_mode_gate(
            session, question, persona, g1_policy.safe_injection_response()
        )
        session.finished = True
        session.confidence = "diblokir (keamanan)"
        _praxis.record_praxis_event(session_id, "blocked", {"reason": "prompt_injection"})
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass
        return session

    if g1_policy.detect_toxic_user_message(question):
        session.final_answer = _apply_maqashid_mode_gate(
            session, question, persona, g1_policy.safe_toxic_response()
        )
        session.finished = True
        session.confidence = "diblokir (ujaran)"
        _praxis.record_praxis_event(session_id, "blocked", {"reason": "toxic"})
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass
        return session

    # ── Typo pipeline (multilingual, lokal) — setelah gate keamanan, sebelum cache/RAG ─
    working_question = question
    session.question_normalized = ""
    session.typo_script_hint = ""
    session.typo_substitutions = 0
    try:
        from .typo_bridge import normalize_for_react

        wq, hint, n_sub = normalize_for_react(question)
        working_question = wq or question
        session.typo_script_hint = hint
        session.typo_substitutions = n_sub
        if working_question != question:
            session.question_normalized = working_question
    except Exception as _typo_err:
        import logging as _log

        _log.getLogger(__name__).debug(f"[TypoPipeline] skip — {_typo_err}")
        working_question = question

    # ── Pivot 2026-04-25: Follow-up detection + reformulation ─────────────────
    # Cek sebelum context injection, supaya routing regex di _rule_based_plan
    # lihat reformulated question (dengan konteks ref) bukan single-word follow-up
    session.is_followup = False
    if conversation_context and _is_followup(working_question):
        session.is_followup = True
        working_question = _reformulate_with_context(working_question, conversation_context)

    # ── Inject conversational memory context ────────────────────────────────────
    if conversation_context:
        working_question = _inject_conversation_context(working_question, conversation_context)
        session.question_normalized = working_question

    # ── Nafs Layer B: capture topic + layer metadata ke session ──────────────────
    try:
        from .nafs_bridge import blend_from_nafs
        _nb = blend_from_nafs(working_question, persona, corpus_only=corpus_only)
        if _nb:
            session.nafs_topic = _nb.get("topic", "")
            session.nafs_layers_used = _nb.get("nafs_layers_used", "")
    except Exception:
        pass

    # Σ-1D: bypass cache untuk current_event — jawaban terkini TIDAK boleh dari cache
    # (cache mungkin menyimpan jawaban lama yang sudah expire)
    _skip_cache = (
        _needs_web_search(working_question)
        and allow_web_fallback
        and not corpus_only
    )
    cached = None if _skip_cache else answer_dedup.get_cached_answer(persona, working_question)
    if cached is not None:
        session.final_answer = _apply_maqashid_mode_gate(session, working_question, persona, cached)
        session.finished = True
        session.confidence = "cache singkat"
        _praxis.record_praxis_event(session_id, "cache_hit", {"persona": persona})
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass
        return session

    # ── FAST PATH: Image generation intent detection ─────────────────────────
    # Deteksi user minta gambar → langsung panggil text_to_image, skip ReAct.
    # Keywords ID+EN, cover variasi umum: "bikin/buat/generate/create image/gambar/foto/ilustrasi"
    _q_lower = working_question.lower()
    _image_verbs = ("bikin", "buat", "buatkan", "generate", "create", "gambarkan", "gambarin", "render", "visualisasikan", "lukiskan", "desainkan")
    _image_nouns = ("gambar", "foto", "ilustrasi", "image", "picture", "visual", "artwork", "poster", "lukisan", "desain",
                    "thumbnail", "konten", "banner", "feed", "story", "reels", "cover", "wallpaper", "logo", "sticker")
    _has_verb = any(v in _q_lower for v in _image_verbs)
    _has_noun = any(n in _q_lower for n in _image_nouns)
    # Meta-question detector: "bisa bikin gambar?" / "kamu bisa generate?" / "ga"
    # adalah question tentang KAPABILITAS, bukan request. Jangan trigger image gen.
    _is_meta_question = bool(re.search(
        r"\b(bisa(kah)?|dapat|mampu|can|could|able)\b.*\b(bikin|buat|generate|create|gambar)\b.*[\?]?\s*(ga|gak|tidak|nggak|enggak|engga|nda|ya)?\s*\??$",
        _q_lower,
    )) or _q_lower.strip().endswith(("ga?", "ga", "gak?", "gak", "ngga?", "ngga"))
    import logging as _log_fp
    _log_fp.getLogger(__name__).warning(f"[ImageFastPath] check q={_q_lower[:80]!r} has_verb={_has_verb} has_noun={_has_noun} meta={_is_meta_question}")
    if _has_verb and _has_noun and not _is_meta_question:
        _log_fp.getLogger(__name__).warning("[ImageFastPath] TRIGGERED, calling text_to_image")
        try:
            from .agent_tools import call_tool as _call_tool

            # ── Auto-enhance v2 pakai creative_framework.py ──────────────────
            # Framework-aware: Jungian archetype + 7 template + Nusantara hints.
            # Inspired by BG Maker Prompt Engineering (Aaker/Sinek/Neumeier/Jungian/CBBE).
            try:
                from .creative_framework import enhance_prompt_creative
                enh = enhance_prompt_creative(working_question)
                enhanced = enh["enhanced_prompt"]
                width = enh["width"]
                height = enh["height"]
                _log_fp.getLogger(__name__).warning(
                    f"[ImageFastPath] template={enh['template_used']} archetype={enh['applied_archetype']} "
                    f"ctx={enh['detected_contexts']} size={width}x{height}"
                )
                # Safety clamp untuk fit 6GB VRAM: max 768 side
                if width > 768: width = 768
                if height > 768: height = 768
            except Exception as _enh_err:
                _log_fp.getLogger(__name__).warning(f"[ImageFastPath] enhance_creative fallback: {_enh_err}")
                enhanced = working_question
                width = height = 512

            _result = _call_tool(
                tool_name="text_to_image",
                args={"prompt": enhanced, "steps": 15, "width": width, "height": height},
                session_id=session_id,
                step=1,
                allow_restricted=False,
            )
            _log_fp.getLogger(__name__).warning(f"[ImageFastPath] tool result success={_result.success} err={_result.error!r} out_len={len(_result.output or '')}")
            if _result.success:
                session.final_answer = _apply_maqashid_mode_gate(
                    session, working_question, persona, _result.output or ""
                )
                session.citations = list(_result.citations or [])
                session.finished = True
                session.confidence = "image gen fast-path"
                _praxis.record_praxis_event(session_id, "image_gen_fast_path", {"prompt": question[:200]})
                try:
                    _praxis.finalize_session_teaching(session)
                except Exception:
                    pass
                return session
            # Kalau tool gagal (server offline, dll), lanjut ke ReAct normal — jangan block user
        except Exception as _img_err:
            import logging as _log
            _log.getLogger(__name__).warning(f"[ImageFastPath] fallback ke ReAct — {_img_err}")
    # ─────────────────────────────────────────────────────────────────────────

    # ── User Intelligence: analisis frekuensi pengguna ────────────────────────
    try:
        u_profile = analyze_user(question)
        session.user_profile       = u_profile
        session.user_language      = u_profile.language.value
        session.user_literacy      = u_profile.literacy.value
        session.user_intent        = u_profile.intent.value
        session.user_cultural_frame = u_profile.cultural_frame.value
    except Exception as _ui_err:
        import logging as _log
        _log.getLogger(__name__).debug(f"[UserIntelligence] skip — {_ui_err}")
        u_profile = None
    # ─────────────────────────────────────────────────────────────────────────

    # ── Experience + Skill enrichment — Pivot 2026-04-26: opt-in via strict ──
    # SEBELUMNYA `if not _strict` → enrichment justru fire by DEFAULT (bug).
    # SEKARANG agent_mode default = no pre-context bloat, ngobrol natural
    # seperti GPT/Claude. Strict_mode opt-in untuk research-grade enrichment.
    if _strict:
        _experience_context: str = ""
        _skill_context: str = ""
        try:
            from .experience_engine import get_experience_engine
            _exp = get_experience_engine()
            _experience_context = _exp.synthesize(working_question, top_k=2)
        except Exception as _exp_err:
            import logging as _log
            _log.getLogger(__name__).debug(f"[ExperienceEngine] skip — {_exp_err}")

        try:
            from .skill_library import get_skill_library
            _skills = get_skill_library()
            _skill_context = _skills.search_skills(working_question, top_k=2)
        except Exception as _skill_err:
            import logging as _log
            _log.getLogger(__name__).debug(f"[SkillLibrary] skip — {_skill_err}")

        if _experience_context and "Tidak ditemukan" not in _experience_context:
            _pre_step_exp = ReActStep(
                step=-2,
                thought="[Pre-context] Ambil pola pengalaman relevan dari ExperienceEngine.",
                action_name="experience_synthesize",
                action_args={"query": working_question[:80]},
                observation=_experience_context[:MAX_TOKENS_PER_OBS],
            )
            session.steps.insert(0, _pre_step_exp)

        if _skill_context and "Tidak ditemukan" not in _skill_context:
            _pre_step_skill = ReActStep(
                step=-1,
                thought="[Pre-context] Cari skill relevan dari SkillLibrary.",
                action_name="skill_search",
                action_args={"query": working_question[:80]},
                observation=_skill_context[:MAX_TOKENS_PER_OBS],
            )
            session.steps.insert(len(session.steps), _pre_step_skill)

    # ── CoT Engine: inject reasoning scaffold (skip kalau agent_mode) ─────────
    try:
        from .cot_engine import get_cot_scaffold, get_complexity
        _cot_complexity = get_complexity(working_question)
        
        # ── COUNCIL TRIGGER (MoA-lite) — Pivot 2026-04-26 ──────────────────────
        # SEBELUMNYA `not _strict` → council fire by DEFAULT untuk high-complexity
        # query, bypass main ReAct + web_search. Bug: factual current-event
        # query yang complex (eg "siapa president 2026") di-route ke council
        # synthesis tanpa data live.
        # SEKARANG: council hanya fire kalau strict_mode opt-in (research-grade).
        # Default agent_mode = single agent + tool use direct (seperti GPT/Claude).
        if _cot_complexity == "high" and not is_council and not simple_mode and _strict:
            try:
                from .council import run_council
                _log_fp.getLogger(__name__).info(f"[Council] Spawning council for complex query: {working_question[:50]}...")
                synth_answer, council_sessions = run_council(
                    question=working_question,
                    client_id=client_id,
                    agency_id=agency_id,
                    conversation_id=conversation_id,
                    allow_restricted=allow_restricted,
                    max_steps=max_steps
                )
                
                # Build dummy session to return council results
                session.final_answer = synth_answer
                session.finished = True
                session.confidence = "council synthesized"
                # Combine citations from all sessions
                for s in council_sessions:
                    session.citations.extend(s.citations)
                return session
            except Exception as _c_err:
                _log_fp.getLogger(__name__).warning(f"[Council] failed, falling back to single agent: {_c_err}")

        # CoT scaffold pre-step — Pivot 2026-04-26: opt-in via strict mode.
        # Sebelumnya CoT scaffold (### Context / ### Solusi Utama / ### Contoh
        # Kode) ALWAYS injected → LLM ikuti literal jadi response kaku
        # template-driven. Bertentangan dengan visi SIDIX bebas seperti
        # GPT/Claude. Sekarang hanya inject kalau strict_mode opt-in.
        if _strict:
            _cot_scaffold = get_cot_scaffold(working_question, persona)
            if _cot_scaffold:
                _pre_step_cot = ReActStep(
                    step=-3,
                    thought=f"[CoT] Kompleksitas={_cot_complexity}. Terapkan kerangka penalaran sistematis.",
                    action_name="cot_scaffold",
                    action_args={"complexity": _cot_complexity, "persona": persona},
                    observation=_cot_scaffold,
                )
                session.steps.insert(0, _pre_step_cot)
    except Exception as _cot_err:
        import logging as _log_cot
        _log_cot.getLogger(__name__).debug("[CoT] skip — %s", _cot_err)
    # ─────────────────────────────────────────────────────────────────────────

    # ── Multi-Layer Memory: build & inject (SIDIX 2.0) ────────────────────────
    _multi_layer_memory = None
    try:
        from .agent_memory import build_multi_layer_memory
        _multi_layer_memory = build_multi_layer_memory(
            query=working_question,
            conversation_context=conversation_context,
            persona=persona,
        )
        session.multi_layer_memory = _multi_layer_memory.to_dict()
    except Exception as _mem_err:
        import logging as _log_mem
        _log_mem.getLogger(__name__).debug(f"[Memory] skip — {_mem_err}")
    # ───────────────────────────────────────────────────────────────────────────

    if verbose:
        print(f"\n{'='*50}")
        print(f"[SIDIX Agent] Session: {session_id}")
        print(f"Q: {question}")
        if working_question != question:
            print(f"Q (normalized): {working_question}")
        print(f"Persona: {persona}")
        if u_profile:
            print(f"UserProfile: lang={u_profile.language.value} | "
                  f"literacy={u_profile.literacy.value} | "
                  f"intent={u_profile.intent.value} | "
                  f"culture={u_profile.cultural_frame.value} | "
                  f"style={u_profile.suggested_formality}/{u_profile.suggested_depth}/{u_profile.suggested_style}")
        print(f"{'='*50}")

    eff_max = _effective_max_steps(working_question, max_steps)
    for step_num in range(eff_max):
        # 1. THINK
        plan = _rule_based_plan(
            question=working_question,
            persona=persona,
            history=session.steps,
            step=step_num,
            corpus_only=corpus_only,
            allow_web_fallback=allow_web_fallback,
            agent_mode=not _strict,
        )

        if isinstance(plan, list):
            # Parallel execution path — wire through parallel_planner for dependency-aware grouping
            thought = plan[0].get("thought", "Menjalankan beberapa aksi secara paralel.")
            action_name = "parallel_tools"  # virtual name for logging
            action_args = {"calls": plan}

            # ── Jiwa Sprint 4 Fase B: parallel_planner WIRED to executor ─────
            try:
                from .parallel_planner import ParallelPlanner, ExecutionPlan
                from .parallel_executor import execute_plan as _execute_plan

                planner = ParallelPlanner()
                raw_calls = [{"name": p["name"], "args": p["args"]} for p in plan]
                execution_plan = planner.plan_from_tool_names(raw_calls)
                session.planner_used = True
                session.planner_savings = execution_plan.estimated_parallel_savings

                if verbose:
                    print(f"\n[Step {step_num}] Parallel Thought: {thought}")
                    print(f"  [Planner] {len(execution_plan.bundles)} bundle(s), "
                          f"savings={session.planner_savings:.0%}")
                    for b in execution_plan.bundles:
                        print(f"    Bundle {b.bundle_id}: {[n.tool_name for n in b.nodes]}")

                # Execute bundle-by-bundle (respects deps / WRITE-sequentiality)
                plan_result = _execute_plan(
                    execution_plan,
                    session_id=session_id,
                    step=step_num,
                    allow_restricted=allow_restricted,
                    verbose=verbose,
                )
                parallel_results = plan_result["results"]

            except Exception as _pe:
                # Fallback: flat parallel blast (legacy behavior)
                if verbose:
                    print(f"\n[Step {step_num}] Parallel Thought: {thought}")
                    print(f"  [Planner] FALLBACK flat blast (error: {_pe})")
                parallel_results = execute_parallel(
                    tool_calls=[{"name": p["name"], "args": p["args"]} for p in plan],
                    session_id=session_id,
                    step=step_num,
                    allow_restricted=allow_restricted,
                )
                session.planner_used = False
                session.planner_savings = 0.0
            # ─────────────────────────────────────────────────────────────────

            if verbose and not session.planner_used:
                for i, p in enumerate(plan):
                    print(f"  - Action {i+1}: {p['name']}({p['args']})")

            observation = merge_observations(parallel_results)
            
            # Combine citations
            citations_merged = []
            for _, res in parallel_results:
                if res.citations:
                    citations_merged.extend(res.citations)
            
            # Record step
            step = ReActStep(
                step=step_num,
                thought=thought,
                action_name=action_name,
                action_args={"calls": plan, "_citations": citations_merged},
                observation=observation[:MAX_TOKENS_PER_OBS * 3], # allow more for parallel
            )
            session.steps.append(step)
            continue # Next step in ReAct loop

        # Single action path (original logic)
        thought, action_name, action_args = plan

        if verbose:
            print(f"\n[Step {step_num}] Thought: {thought}")

        # 2. Final Answer check
        if not action_name:
            pass  # Langsung ke final answer
        else:
            # [WISDOM GATE] Pre-Action Reflection — Pivot 2026-04-26: opt-in.
            # SEBELUMNYA `if not _strict` → Wisdom Gate override action planner
            # by DEFAULT (bug). Akibatnya: planner pilih web_search → Wisdom Gate
            # HOLD → action di-replace ke search_corpus → factual query gagal.
            # SEKARANG: Wisdom Gate hanya fire kalau strict_mode opt-in.
            if _strict:
                is_wise, suggestion = WisdomGate.evaluate_intent(
                    question=working_question,
                    proposed_action=f"{action_name}({action_args})",
                    context={"step_count": step_num, "history": session.steps}
                )

                if not is_wise:
                    if verbose:
                        print(f"  [WisdomGate] HOLD: {suggestion}")
                    thought = f"Sadar bahwa tindakan sebelumnya mungkin gegabah. {suggestion}"
                    action_name = "search_corpus"  # Fallback aman
                    action_args = {"query": working_question, "k": 3}
        
        # 2. Final Answer check (lanjutan)
        if not action_name:
            final_answer, citations, conf_score, atype = _compose_final_answer(
                question=working_question,
                persona=persona,
                steps=session.steps,
                simple_mode=simple_mode,
                user_profile=session.user_profile,
                session=session,
                agent_mode=not _strict,
            )
            step = ReActStep(
                step=step_num,
                thought=thought,
                action_name="",
                action_args={},
                observation="",
                is_final=True,
                final_answer=final_answer,
            )
            session.steps.append(step)
            session.citations = citations
            # Task 27: numeric + text confidence
            from .g1_policy import confidence_label
            session.confidence = confidence_label(conf_score)
            session.confidence_score = conf_score
            session.answer_type = atype

            # ── Filter pipeline — Pivot 2026-04-26 LOGIC FIX ──────────────────
            # SEBELUMNYA bug: `if not _strict` → filter justru aktif by DEFAULT.
            # SEKARANG: pipeline epistemology+maqashid+constitution+self-critique+
            # cognitive-check HANYA fire kalau strict_mode=True (opt-in eksplisit).
            # Default agent_mode = chat bebas, dinamis, seperti GPT/Claude/KIMI.
            # Hygiene (label dedup, leak strip) tetap jalan supaya output bersih.
            if _strict:
                final_answer = _apply_epistemology(
                    session=session,
                    question=working_question,
                    final_answer=final_answer,
                    citations=citations,
                    persona=persona,
                )
                final_answer = _apply_maqashid_mode_gate(session, working_question, persona, final_answer)
                final_answer = _apply_constitution(final_answer)
                final_answer = _self_critique_lite(final_answer, working_question, persona)
                final_answer, _csc_warnings = _cognitive_self_check(final_answer, citations, working_question, persona)
                if _csc_warnings:
                    session.csc_warnings = ",".join(_csc_warnings)[:300]
            # Hygiene (dedup label + strip context leak) selalu jalan — agnostik
            # ke strict/agent mode supaya output tidak punya boilerplate residu.
            final_answer = _apply_hygiene(final_answer)
            # ───────────────────────────────────────────────────────────────────

            # ── Jiwa Pilar 5: Hayat — Self-Iteration ─────────────────────────
            if _JIWA_ENABLED and _jiwa is not None and not simple_mode:
                try:
                    _blend = _response_blend_profile(working_question, persona)
                    _hayat_on = _blend.get("hayat_enabled", True)
                    _topic = _blend.get("topic", "umum")
                    if _hayat_on:
                        from .ollama_llm import ollama_available, ollama_generate
                        if ollama_available():
                            def _gen_fn(prompt: str) -> str:
                                text, _ = ollama_generate(
                                    prompt=prompt,
                                    system=_blend.get("system_hint", ""),
                                    max_tokens=600,
                                    temperature=0.65,
                                )
                                return text
                            final_answer = _jiwa.refine(
                                question=working_question,
                                answer=final_answer,
                                generate_fn=_gen_fn,
                                topic=_topic,
                                hayat_enabled=True,
                            )
                except Exception:
                    pass  # Hayat non-blocking — fallback ke jawaban asli
            # ── Jiwa Pilar 2: Aql — post-response learning ───────────────────
            if _JIWA_ENABLED and _jiwa is not None:
                try:
                    _topic_for_aql = _response_blend_profile(working_question, persona).get("topic", "umum")
                    _jiwa.post_response(
                        working_question, final_answer, persona,
                        topic=_topic_for_aql,
                        platform="direct",
                        cqf_score=float(conf_score or 0) * 10,
                    )
                except Exception:
                    pass  # Aql non-blocking
            # ─────────────────────────────────────────────────────────────────

            # ── SIDIX 2.0: Self-learning from session ─────────────────────────
            try:
                from .agent_memory import learn_from_session
                _success = float(conf_score or 0.6)
                if session.citations:
                    _success = min(1.0, _success + 0.1)
                learn_from_session(
                    session_id=session_id,
                    question=working_question,
                    final_answer=final_answer,
                    steps=session.steps,
                    persona=persona,
                    success_indicator=_success,
                )
            except Exception:
                pass  # Self-learning non-blocking
            # ─────────────────────────────────────────────────────────────────

            session.final_answer = final_answer
            answer_dedup.set_cached_answer(persona, working_question, final_answer)
            session.finished = True
            _attach_orchestration_digest(session, working_question, persona)

            _praxis.record_react_step(session_id, step)
            try:
                _praxis.finalize_session_teaching(session)
            except Exception:
                pass

            if verbose:
                print(f"[Final Answer]\n{final_answer[:400]}")

            break

        # 3. ACT
        if verbose:
            print(f"[Step {step_num}] Action: {action_name}({json.dumps(action_args)})")

        # ── Tool whitelist enforcement ────────────────────────────────────────
        if _bm is not None and (_agency_id or _client_id):
            if not _bm.is_tool_allowed(_agency_id, _client_id, action_name):
                import logging as _log_tw
                _log_tw.getLogger(__name__).warning(
                    "[BranchGate] tool '%s' diblokir untuk agency=%s client=%s",
                    action_name, _agency_id, _client_id,
                )
                result = ToolResult(
                    success=False,
                    output="",
                    error=f"Tool '{action_name}' tidak diizinkan untuk branch ini.",
                    citations=[],
                )
                observation = f"[BLOCKED] {result.error}"
                observation = observation[:MAX_TOKENS_PER_OBS]
                react_step = ReActStep(
                    step=step_num,
                    thought=thought,
                    action_name=action_name,
                    action_args=action_args,
                    observation=observation,
                )
                session.steps.append(react_step)
                _praxis.record_react_step(session_id, react_step)
                continue
        # ─────────────────────────────────────────────────────────────────────

        # ── Corpus filter injection (search_corpus / graph_search) ────────────
        _effective_args = dict(action_args)
        if _corpus_filter and action_name in ("search_corpus", "graph_search"):
            _effective_args.setdefault("_corpus_filter", _corpus_filter)
        # ─────────────────────────────────────────────────────────────────────

        result: ToolResult = call_tool(
            tool_name=action_name,
            args=_effective_args,
            session_id=session_id,
            step=step_num,
            allow_restricted=allow_restricted,
        )

        # 4. OBSERVE
        observation = result.output if result.success else f"[ERROR] {result.error}"
        observation = observation[:MAX_TOKENS_PER_OBS]

        if verbose:
            print(f"[Step {step_num}] Observation: {observation[:200]}...")

        react_step = ReActStep(
            step=step_num,
            thought=thought,
            action_name=action_name,
            action_args=action_args,
            observation=observation,
        )
        # Simpan citations dari tool ke step (untuk compose nanti)
        if result.citations:
            react_step.action_args["_citations"] = result.citations

        session.steps.append(react_step)
        _praxis.record_react_step(session_id, react_step)
        _log_react_step_to_file(action_name, session_id, step_num, persona)  # Sprint 38b

    else:
        # Loop habis tanpa final answer
        final_answer, citations, conf_score, atype = _compose_final_answer(
            question=working_question,
            persona=persona,
            steps=session.steps,
            simple_mode=simple_mode,
            user_profile=session.user_profile,
            session=session,
            agent_mode=not _strict,
        )
        session.citations = citations
        session.finished = True
        session.error = "Max steps reached"
        from .g1_policy import confidence_label
        session.confidence = confidence_label(conf_score)
        session.confidence_score = conf_score  # type: ignore[attr-defined]
        session.answer_type = atype            # type: ignore[attr-defined]
        # ── Filter pipeline — Pivot 2026-04-26 LOGIC FIX (max-steps branch) ──
        # Sama seperti branch utama: epistemology+maqashid+constitution+CSC
        # HANYA fire kalau _strict opt-in. Default = chat bebas + hygiene saja.
        if _strict:
            final_answer = _apply_epistemology(
                session=session,
                question=working_question,
                final_answer=final_answer,
                citations=citations,
                persona=persona,
            )
            final_answer = _apply_maqashid_mode_gate(session, working_question, persona, final_answer)
            final_answer = _apply_constitution(final_answer)
            final_answer, _csc_warnings = _cognitive_self_check(final_answer, citations, working_question, persona)
            if _csc_warnings:
                session.csc_warnings = ",".join(_csc_warnings)[:300]
        final_answer = _apply_hygiene(final_answer)
        session.final_answer = final_answer
        # ─────────────────────────────────────────────────────────────────────
        answer_dedup.set_cached_answer(persona, working_question, final_answer)
        _attach_orchestration_digest(session, working_question, persona)
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass

    return session


def format_trace(session: AgentSession) -> str:
    """Format ReAct trace untuk debugging / logging."""
    lines = [
        f"Session: {session.session_id}",
        f"Q: {session.question}",
        f"Persona: {session.persona}",
        "",
    ]
    if getattr(session, "orchestration_digest", ""):
        lines.append("Orchestration digest:")
        lines.append(session.orchestration_digest[:600])
        lines.append("")
    for s in session.steps:
        lines.append(f"[Step {s.step}]")
        lines.append(f"  Thought   : {s.thought}")
        if s.action_name:
            lines.append(f"  Action    : {s.action_name}({json.dumps(s.action_args, ensure_ascii=False)[:100]})")
            lines.append(f"  Observation: {s.observation[:200]}")
        if s.is_final:
            lines.append(f"  FINAL ANSWER: {s.final_answer[:300]}")
        lines.append("")

    return "\n".join(lines)
