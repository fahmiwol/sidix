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

# Pivot 2026-04-25: current-events → web_search aggressive default.
# Bila user menanyakan hal terkini/berita/tokoh/harga/event → langsung web_search.
_CURRENT_EVENTS_RE = re.compile(
    r"\b("
    r"hari\s+ini|sekarang|saat\s+ini|terkini|terbaru|"
    r"berita|news|update\s+terbaru|"
    r"harga\s+(saham|bitcoin|btc|emas|dollar|rupiah|usd|idr)|"
    r"kurs\s+(dollar|usd|rupiah|idr|euro)|"
    r"cuaca|weather|"
    r"presiden\s+(amerika|indonesia|rusia|china)\s+(saat|sekarang|sekarang)|"
    r"siapa\s+(presiden|menteri|gubernur|ceo|juara)\s+.*(saat|sekarang|terkini)|"
    r"kapan\s+(event|pemilu|piala|olimpiade|konser)|"
    r"tanggal\s+berapa\s+(hari\s+ini|sekarang)"
    r")\b",
    re.IGNORECASE,
)


def _needs_web_search(question: str) -> bool:
    """True bila pertanyaan butuh data terkini/real-time → web_search dulu."""
    return bool(_CURRENT_EVENTS_RE.search(question or ""))


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
) -> tuple[str, str, dict]:
    """
    Returns (thought, action_name, action_args).
    action_name = "" berarti Final Answer sekarang.

    Rule-based planner — diganti LLM call saat Inference Engine siap.
    Untuk coding intents, delegasi ke coding_planner (LLM-based).
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

        # Pivot 2026-04-25: current-events routing — web_search aggressive default.
        # Bila pertanyaan butuh data terkini, langsung web_search sebelum corpus.
        if _needs_web_search(question) and allow_web_fallback and not corpus_only:
            return (
                f"Pertanyaan menyangkut data terkini/real-time. Langsung web_search: '{question}'.",
                "web_search",
                {"query": question, "max_results": 5},
            )

        # Default routing: corpus untuk topik SIDIX, model untuk topik umum.
        if _should_prioritize_corpus(question, corpus_only=corpus_only):
            return (
                f"Topik terkait SIDIX/sumber internal. Gunakan search_corpus dengan query: '{question}'.",
                "search_corpus",
                {"query": question, "k": 5, "persona": persona},
            )
        return (
            "Topik umum/non-SIDIX. Jawab langsung dari kemampuan model dulu, "
            "lalu gunakan corpus hanya bila diminta.",
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


def _compose_final_answer(
    question: str,
    persona: str,
    steps: list[ReActStep],
    *,
    simple_mode: bool = False,
    user_profile: "UserProfile | None" = None,
    session: "AgentSession | None" = None,
) -> tuple[str, list[dict], float, str]:
    """
    Compose jawaban final dari semua observation yang sudah dikumpulkan.
    Returns (answer_text, citations, confidence_score, answer_type).

    Pipeline:
    1. Coba Ollama (local LLM generative) + corpus context sebagai RAG
    2. Fallback: format corpus results langsung
    3. Fallback final: "tidak tahu" response
    """
    all_citations: list[dict] = []
    obs_blocks: list[str] = []

    for s in steps:
        if s.observation and not s.is_final:
            obs_blocks.append(s.observation)
        all_citations.extend(s.action_args.get("_citations", []))

    blend = _response_blend_profile(question, persona)
    max_obs_blocks = int(blend.get("max_obs_blocks", 2))
    system_hint = str(blend.get("system_hint", ""))

    # ── Coba Ollama generative (sebelum greeting check) ──────────────────────
    # Kalau Ollama tersedia: generate jawaban nyata pakai LLM + corpus context
    try:
        from .ollama_llm import ollama_available, ollama_generate
        if ollama_available():
            # Build corpus context dari semua observation
            corpus_ctx = "\n\n---\n\n".join(obs_blocks[:max_obs_blocks]) if obs_blocks else ""
            text, mode = ollama_generate(
                prompt=question,
                system=system_hint,
                corpus_context=corpus_ctx,
                max_tokens=600 if not simple_mode else 200,
                temperature=0.7,
            )
            if mode == "ollama":
                import logging as _log
                _log.getLogger("sidix.react").info(f"Ollama synthesis OK — persona={persona}")
                return (text, all_citations, 0.85, "fakta")
    except Exception as _ollama_err:
        import logging as _log
        _log.getLogger("sidix.react").warning(f"Ollama synthesis failed: {_ollama_err}")

    # Greeting special case (fallback kalau Ollama off)
    if _GREETING_RE.match(question.strip()):
        return (
            "📋 Fakta\n\n"
            "Halo! Saya SIDIX — AI multipurpose berbasis prinsip sidq (kejujuran), sanad (sitasi), "
            "dan tabayyun (verifikasi). Ada yang bisa saya bantu? "
            "Saya bisa mencari informasi dari corpus, menjawab pertanyaan, atau membantu analisis.",
            [],
            0.5,
            "fakta",
        )

    if not obs_blocks:
        # Fallback: coba Ollama juga
        try:
            from .ollama_llm import ollama_available, ollama_generate
            if ollama_available():
                text, mode = ollama_generate(prompt=question, max_tokens=400)
                if mode == "ollama":
                    return (text, [], 0.6, "opini")
        except Exception:
            pass

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

    # Tag question dengan referensi konteks
    ref = f"[FOLLOW-UP atas pertanyaan: '{last_user[:150]}']"
    return f"{question}\n\n{ref}"


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

    cached = answer_dedup.get_cached_answer(persona, working_question)
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
    import logging as _log_fp
    _log_fp.getLogger(__name__).warning(f"[ImageFastPath] check q={_q_lower[:80]!r} has_verb={_has_verb} has_noun={_has_noun}")
    if _has_verb and _has_noun:
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

    # ── Experience + Skill enrichment (pre-context injection) ─────────────────
    # experience_engine → pola dari pengalaman masa lalu yang relevan
    # skill_library → skill yang bisa dipakai untuk pertanyaan ini
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

    # Inject sebagai pre-step observation bila ada konten relevan
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

    # ── CoT Engine: inject reasoning scaffold untuk pertanyaan kompleks ───────
    try:
        from .cot_engine import get_cot_scaffold, get_complexity
        _cot_complexity = get_complexity(working_question)
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
        thought, action_name, action_args = _rule_based_plan(
            question=working_question,
            persona=persona,
            history=session.steps,
            step=step_num,
            corpus_only=corpus_only,
            allow_web_fallback=allow_web_fallback,
        )

        if verbose:
            print(f"\n[Step {step_num}] Thought: {thought}")

        # 2. Final Answer check
        if not action_name:
            final_answer, citations, conf_score, atype = _compose_final_answer(
                question=working_question,
                persona=persona,
                steps=session.steps,
                simple_mode=simple_mode,
                user_profile=session.user_profile,
                session=session,
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

            # ── Islamic Epistemology Engine ───────────────────────────────────
            final_answer = _apply_epistemology(
                session=session,
                question=working_question,
                final_answer=final_answer,
                citations=citations,
                persona=persona,
            )
            final_answer = _apply_maqashid_mode_gate(session, working_question, persona, final_answer)
            final_answer = _apply_constitution(final_answer)
            final_answer = _self_critique_lite(final_answer, working_question, persona)  # Pivot 2026-04-25
            # Brain upgrade: cognitive self-check (CoVe-inspired)
            final_answer, _csc_warnings = _cognitive_self_check(final_answer, citations, working_question, persona)
            if _csc_warnings:
                session.csc_warnings = ",".join(_csc_warnings)[:300]
            final_answer = _apply_hygiene(final_answer)  # Pivot 2026-04-25

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

    else:
        # Loop habis tanpa final answer
        final_answer, citations, conf_score, atype = _compose_final_answer(
            question=working_question,
            persona=persona,
            steps=session.steps,
            simple_mode=simple_mode,
            user_profile=session.user_profile,
            session=session,
        )
        session.citations = citations
        session.finished = True
        session.error = "Max steps reached"
        from .g1_policy import confidence_label
        session.confidence = confidence_label(conf_score)
        session.confidence_score = conf_score  # type: ignore[attr-defined]
        session.answer_type = atype            # type: ignore[attr-defined]
        # ── Islamic Epistemology Engine ───────────────────────────────────────
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
        final_answer = _apply_hygiene(final_answer)  # Pivot 2026-04-25
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
