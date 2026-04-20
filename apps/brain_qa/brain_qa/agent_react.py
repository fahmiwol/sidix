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
from .orchestration import agent_build_intent
from .user_intelligence import analyze_user, get_response_instructions, UserProfile


# ── Config ────────────────────────────────────────────────────────────────────
MAX_STEPS = 6           # max ReAct loop iterations (default)
MAX_STEPS_BUILD = 12    # lebih panjang bila intent implementasi / app / game
MAX_TOKENS_PER_OBS = 600  # potong observation supaya tidak bloat context


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


def _effective_max_steps(question: str, max_steps: int | None) -> int:
    if max_steps is not None:
        return max(2, min(24, int(max_steps)))
    if agent_build_intent(question):
        return MAX_STEPS_BUILD
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
    """
    q_lower = question.lower()

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

        # Default: search corpus
        return (
            f"Pertanyaan ini butuh referensi dari corpus. Gunakan search_corpus dengan query: '{question}'.",
            "search_corpus",
            {"query": question, "k": 5, "persona": persona},
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

        # Jika ada error di observation, coba search corpus sebagai fallback
        if "[error]" in obs_lower[:200] or "error" in obs_lower[:50]:
            if step < 3:
                return (
                    f"Langkah sebelumnya error. Coba search_corpus sebagai fallback.",
                    "search_corpus",
                    {"query": question, "k": 3, "persona": persona},
                )

    # Default: final answer setelah MAX_STEPS/2
    if step >= MAX_STEPS // 2:
        return ("Cukup informasi untuk menjawab. Buat final answer.", "", {})

    return (
        "Belum cukup info. Coba search lebih dalam.",
        "search_corpus",
        {"query": question, "k": 5, "persona": persona},
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

    # ── Coba Ollama generative (sebelum greeting check) ──────────────────────
    # Kalau Ollama tersedia: generate jawaban nyata pakai LLM + corpus context
    try:
        from .ollama_llm import ollama_available, ollama_generate
        if ollama_available():
            # Build corpus context dari semua observation
            corpus_ctx = "\n\n---\n\n".join(obs_blocks[:3]) if obs_blocks else ""
            text, mode = ollama_generate(
                prompt=question,
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

    # ── Coba Anthropic Haiku (fallback cloud, hemat) ──────────────────────────
    try:
        from .anthropic_llm import anthropic_available, anthropic_generate
        if anthropic_available():
            corpus_ctx_snippets = obs_blocks[:3] if obs_blocks else None
            max_tok = 500 if not simple_mode else 200
            text, mode = anthropic_generate(
                prompt=question,
                max_tokens=max_tok,
                temperature=0.7,
                context_snippets=corpus_ctx_snippets,
            )
            if mode == "anthropic_haiku" and text:
                import logging as _log
                _log.getLogger("sidix.react").info("Anthropic Haiku synthesis OK")
                return (text, all_citations, 0.82, "fakta")
    except Exception as _anth_err:
        import logging as _log
        _log.getLogger("sidix.react").warning(f"Anthropic synthesis failed: {_anth_err}")
    # ── End cloud fallback ────────────────────────────────────────────────────

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
        # Kalau Ollama off dan tidak ada corpus → coba Anthropic Haiku
        try:
            from .anthropic_llm import anthropic_available, anthropic_generate
            if anthropic_available():
                text, mode = anthropic_generate(
                    prompt=question,
                    max_tokens=500,
                    temperature=0.7,
                )
                if mode == "anthropic_haiku" and text:
                    return (text, [], 0.75, "fakta")
        except Exception:
            pass

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


def run_react(
    *,
    question: str,
    persona: str = "INAN",
    allow_restricted: bool = False,
    max_steps: int | None = None,
    verbose: bool = False,
    corpus_only: bool = False,
    allow_web_fallback: bool = True,
    simple_mode: bool = False,
) -> AgentSession:
    """
    Jalankan ReAct loop untuk satu pertanyaan.
    Returns AgentSession dengan steps + final_answer + citations.
    """
    from . import g1_policy
    from . import answer_dedup

    session_id = str(uuid.uuid4())[:8]
    session = AgentSession(
        session_id=session_id,
        question=question,
        persona=persona,
    )

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
        session.final_answer = g1_policy.safe_injection_response()
        session.finished = True
        session.confidence = "diblokir (keamanan)"
        _praxis.record_praxis_event(session_id, "blocked", {"reason": "prompt_injection"})
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass
        return session

    if g1_policy.detect_toxic_user_message(question):
        session.final_answer = g1_policy.safe_toxic_response()
        session.finished = True
        session.confidence = "diblokir (ujaran)"
        _praxis.record_praxis_event(session_id, "blocked", {"reason": "toxic"})
        try:
            _praxis.finalize_session_teaching(session)
        except Exception:
            pass
        return session

    cached = answer_dedup.get_cached_answer(persona, question)
    if cached is not None:
        session.final_answer = cached
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
    _q_lower = question.lower()
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
                enh = enhance_prompt_creative(question)
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
                enhanced = question
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
                session.final_answer = _result.output
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
        _experience_context = _exp.synthesize(question, top_k=2)
    except Exception as _exp_err:
        import logging as _log
        _log.getLogger(__name__).debug(f"[ExperienceEngine] skip — {_exp_err}")

    try:
        from .skill_library import get_skill_library
        _skills = get_skill_library()
        _skill_context = _skills.search_skills(question, top_k=2)
    except Exception as _skill_err:
        import logging as _log
        _log.getLogger(__name__).debug(f"[SkillLibrary] skip — {_skill_err}")

    # Inject sebagai pre-step observation bila ada konten relevan
    if _experience_context and "Tidak ditemukan" not in _experience_context:
        _pre_step_exp = ReActStep(
            step=-2,
            thought="[Pre-context] Ambil pola pengalaman relevan dari ExperienceEngine.",
            action_name="experience_synthesize",
            action_args={"query": question[:80]},
            observation=_experience_context[:MAX_TOKENS_PER_OBS],
        )
        session.steps.insert(0, _pre_step_exp)

    if _skill_context and "Tidak ditemukan" not in _skill_context:
        _pre_step_skill = ReActStep(
            step=-1,
            thought="[Pre-context] Cari skill relevan dari SkillLibrary.",
            action_name="skill_search",
            action_args={"query": question[:80]},
            observation=_skill_context[:MAX_TOKENS_PER_OBS],
        )
        session.steps.insert(len(session.steps), _pre_step_skill)
    # ─────────────────────────────────────────────────────────────────────────

    if verbose:
        print(f"\n{'='*50}")
        print(f"[SIDIX Agent] Session: {session_id}")
        print(f"Q: {question}")
        print(f"Persona: {persona}")
        if u_profile:
            print(f"UserProfile: lang={u_profile.language.value} | "
                  f"literacy={u_profile.literacy.value} | "
                  f"intent={u_profile.intent.value} | "
                  f"culture={u_profile.cultural_frame.value} | "
                  f"style={u_profile.suggested_formality}/{u_profile.suggested_depth}/{u_profile.suggested_style}")
        print(f"{'='*50}")

    eff_max = _effective_max_steps(question, max_steps)
    for step_num in range(eff_max):
        # 1. THINK
        thought, action_name, action_args = _rule_based_plan(
            question=question,
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
                question=question,
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
                question=question,
                final_answer=final_answer,
                citations=citations,
                persona=persona,
            )
            session.final_answer = final_answer
            # ─────────────────────────────────────────────────────────────────

            answer_dedup.set_cached_answer(persona, question, final_answer)
            session.finished = True
            _attach_orchestration_digest(session, question, persona)

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

        result: ToolResult = call_tool(
            tool_name=action_name,
            args=action_args,
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
            question=question,
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
            question=question,
            final_answer=final_answer,
            citations=citations,
            persona=persona,
        )
        session.final_answer = final_answer
        # ─────────────────────────────────────────────────────────────────────
        answer_dedup.set_cached_answer(persona, question, final_answer)
        _attach_orchestration_digest(session, question, persona)
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
