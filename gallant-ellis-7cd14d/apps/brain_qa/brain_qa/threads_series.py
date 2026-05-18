"""
threads_series.py — SIDIX 3-Post Series Engine for Threads

Sistem posting harian: Hook → Detail → CTA
- Post 1 (08:00 WIB): HOOK — tarik perhatian, buat penasaran
- Post 2 (12:00 WIB): DETAIL — jelaskan lebih dalam, tunjukkan nilai
- Post 3 (18:00 WIB): CTA — ajak aksi nyata, follow/visit/contribute

Series Angles (bergantian):
  0. ISLAMIC    — epistemologi Islam, halal AI, maqasid
  1. TECH_ID    — teknis, bahasa Indonesia
  2. TECH_EN    — teknis, bahasa Inggris
  3. US_ANGLE   — Amerika: startup, productivity, ROI
  4. EU_ANGLE   — Eropa: privacy, GDPR, sovereignty
  5. UK_ANGLE   — UK: academic, research, citations
  6. AU_ANGLE   — Australia: multilingual, inclusion
  7. DEV_INVITE — developer/researcher/akademisi recruitment
  8. FEATURE    — feature launch / "NEW!" announcement
  9. COMMUNITY  — interaksi, pertanyaan, poll

Rotasi: hari genap = Indonesia, hari ganjil = English.
Series berganti setiap hari (mod 10).
"""

from __future__ import annotations

import json
import time
import datetime
from pathlib import Path
from typing import Optional

# ── State file ─────────────────────────────────────────────────────────────────
_SERIES_STATE = Path(__file__).parent.parent.parent / ".data" / "threads_series_state.json"


def _load_state() -> dict:
    if _SERIES_STATE.exists():
        try:
            return json.loads(_SERIES_STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state: dict) -> None:
    _SERIES_STATE.parent.mkdir(parents=True, exist_ok=True)
    _SERIES_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _today_str() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


# ── Feature Showcase Registry ──────────────────────────────────────────────────
# Fitur SIDIX — mix antara yang sudah ada + roadmap yang coming soon

SIDIX_FEATURES = [
    {
        "id": "chat_ai",
        "name": "AI Chat Assistant",
        "status": "live",
        "emoji": "🧠",
        "tagline_id": "Tanya apa saja — SIDIX menjawab dengan referensi nyata",
        "tagline_en": "Ask anything — SIDIX answers with real citations",
        "detail_id": (
            "Berbeda dari ChatGPT, SIDIX menyebutkan SUMBER setiap jawaban.\n"
            "Epistemologi terjaga. Tidak ada halusinasi tanpa konfirmasi.\n"
            "Tersedia di sidixlab.com — GRATIS, tanpa login."
        ),
        "detail_en": (
            "Unlike ChatGPT, SIDIX cites its SOURCES for every answer.\n"
            "Epistemological integrity built-in. No hallucination without flagging.\n"
            "Free at sidixlab.com — no account required."
        ),
    },
    {
        "id": "tools_builtin",
        "name": "Built-in Tools (18 tools)",
        "status": "live",
        "emoji": "🛠️",
        "tagline_id": "18 alat langsung dalam chat: kalkulator, waktu shalat, qiblat, zakat...",
        "tagline_en": "18 tools built right into chat: calculator, prayer times, qibla, zakat...",
        "detail_id": (
            "Tidak perlu pindah tab. Dalam satu chat SIDIX:\n"
            "• Kalkulator & statistik\n"
            "• Waktu shalat otomatis (lokasi kamu)\n"
            "• Arah kiblat + jarak ke Mekkah\n"
            "• Kalkulator zakat maal & fitrah\n"
            "• Asmaul Husna, UUID, hash, QR...\n"
            "Semua gratis. Semua lokal."
        ),
        "detail_en": (
            "No tab switching needed. Inside one SIDIX chat:\n"
            "• Calculator & statistics\n"
            "• Prayer times (auto-location)\n"
            "• Qibla direction + distance to Mecca\n"
            "• Zakat calculator (maal & fitrah)\n"
            "• 99 Names of Allah, UUID, hash, base64...\n"
            "All free. All local."
        ),
    },
    {
        "id": "rag_corpus",
        "name": "RAG Knowledge Base",
        "status": "live",
        "emoji": "📚",
        "tagline_id": "Lebih dari 500 dokumen riset tersimpan — SIDIX belajar setiap hari",
        "tagline_en": "500+ research docs indexed — SIDIX learns every day",
        "detail_id": (
            "RAG (Retrieval-Augmented Generation) = AI yang membaca dokumen dulu sebelum menjawab.\n"
            "SIDIX punya 500+ catatan riset: AI, Islam, coding, fisika, epistemologi.\n"
            "Diperbarui otomatis dari arXiv, GitHub, Wikipedia, dan kontribusi komunitas."
        ),
        "detail_en": (
            "RAG = AI that reads real documents before answering.\n"
            "SIDIX has 500+ research notes: AI, Islam, coding, physics, epistemology.\n"
            "Updated automatically from arXiv, GitHub, Wikipedia & community."
        ),
    },
    {
        "id": "audio_tts",
        "name": "Text-to-Speech (SIDIX Voice)",
        "status": "beta",
        "emoji": "🎙️",
        "tagline_id": "SIDIX bisa berbicara. Text-to-Speech dengan suara natural — beta.",
        "tagline_en": "SIDIX can speak. Natural TTS voice generation — now in beta.",
        "detail_id": (
            "SIDIX Voice menggunakan F5-TTS (state-of-art, open source).\n"
            "Bisa generate suara dari teks, termasuk:\n"
            "• Tilawah Quran dengan nada tartil\n"
            "• Narasi podcast bahasa Indonesia\n"
            "• Voice clone dari sampel 3 detik\n"
            "Beta — tersedia untuk early tester. DM kami!"
        ),
        "detail_en": (
            "SIDIX Voice uses F5-TTS (state-of-the-art, fully open source).\n"
            "Generate voice from text:\n"
            "• Natural Indonesian narration\n"
            "• Quran recitation in tartil style\n"
            "• 3-second voice clone for personalization\n"
            "Beta — available for early testers. DM us!"
        ),
    },
    {
        "id": "image_gen",
        "name": "AI Image Generation",
        "status": "coming_soon",
        "emoji": "🎨",
        "tagline_id": "Generasi gambar AI lokal — coming soon di SIDIX v2",
        "tagline_en": "Local AI image generation — coming to SIDIX v2",
        "detail_id": (
            "SIDIX Image akan menggunakan Stable Diffusion lokal — tidak ada cloud, tidak ada sensor.\n"
            "Rencana fitur:\n"
            "• Text-to-image bahasa Indonesia\n"
            "• Style Islam (kaligrafi, geometric, arabesque)\n"
            "• Photo editor langsung di chat\n"
            "• Inpainting & upscaling\n"
            "Target: Q3 2026. Daftarkan diri sebagai beta tester: sidixlab.com"
        ),
        "detail_en": (
            "SIDIX Image will use local Stable Diffusion — no cloud, no censorship.\n"
            "Planned features:\n"
            "• Indonesian-language text-to-image prompts\n"
            "• Islamic art styles (calligraphy, geometric, arabesque)\n"
            "• In-chat photo editor\n"
            "• Inpainting & AI upscaling\n"
            "Target: Q3 2026. Join beta: sidixlab.com"
        ),
    },
    {
        "id": "video_gen",
        "name": "AI Video Maker",
        "status": "roadmap",
        "emoji": "🎬",
        "tagline_id": "SIDIX Video — buat video edukasi AI dari teks. Roadmap Q4 2026.",
        "tagline_en": "SIDIX Video — generate educational AI videos from text. Q4 2026 roadmap.",
        "detail_id": (
            "Bayangkan: ketik 1 paragraf → dapat video penjelasan 60 detik.\n"
            "SIDIX Video (roadmap):\n"
            "• Script otomatis dari topik\n"
            "• Avatar AI berbicara (TTS + lip sync)\n"
            "• Subtitle bahasa Indonesia + Arab\n"
            "• Export ke format Reels/TikTok/YouTube Shorts\n"
            "Mau jadi kontributor? sidixlab.com"
        ),
        "detail_en": (
            "Imagine: type 1 paragraph → get a 60-second explainer video.\n"
            "SIDIX Video (roadmap):\n"
            "• Auto-script from any topic\n"
            "• AI avatar with TTS + lip sync\n"
            "• Indonesian + Arabic subtitles\n"
            "• Export to Reels/TikTok/YouTube Shorts format\n"
            "Want to contribute? sidixlab.com"
        ),
    },
    {
        "id": "agent_mode",
        "name": "ReAct AI Agent Mode",
        "status": "live",
        "emoji": "⚡",
        "tagline_id": "SIDIX tidak hanya menjawab — dia berpikir langkah demi langkah seperti manusia",
        "tagline_en": "SIDIX doesn't just answer — it thinks step by step like a human",
        "detail_id": (
            "ReAct = Reasoning + Acting. SIDIX Agent:\n"
            "1. Terima pertanyaan\n"
            "2. Pikir (Thought): apa yang perlu saya cari?\n"
            "3. Aksi (Action): cari di corpus, web, tools\n"
            "4. Observasi: apa yang ditemukan?\n"
            "5. Jawab dengan sumber\n\n"
            "Mirip cara manusia riset — bukan sekadar tebak kata berikutnya."
        ),
        "detail_en": (
            "ReAct = Reasoning + Acting. SIDIX Agent:\n"
            "1. Receive question\n"
            "2. Think: what do I need to find?\n"
            "3. Act: search corpus, web, tools\n"
            "4. Observe: what was found?\n"
            "5. Answer with citations\n\n"
            "Like how humans research — not just predicting next tokens."
        ),
    },
    {
        "id": "islamic_epi",
        "name": "Islamic Epistemology Engine",
        "status": "live",
        "emoji": "🕌",
        "tagline_id": "AI pertama yang mengintegrasikan Maqashid Syariah ke setiap jawaban",
        "tagline_en": "First AI to integrate Maqasid al-Shariah into every response",
        "detail_id": (
            "Setiap jawaban SIDIX melewati filter:\n"
            "• Sanad validator — apakah sumber terpercaya?\n"
            "• Maqashid check — apakah jawaban menjaga: Agama, Jiwa, Akal, Keturunan, Harta?\n"
            "• Constitutional check — 4 sifat: Siddiq, Amanah, Tabligh, Fathanah\n"
            "• Yaqin tiering — Ilm / Ain / Haqq al-Yaqin\n\n"
            "Bukan AI biasa. Ini AI dengan adab."
        ),
        "detail_en": (
            "Every SIDIX answer passes through:\n"
            "• Sanad validation — is the source credible?\n"
            "• Maqasid check — does it protect: Religion, Life, Intellect, Lineage, Wealth?\n"
            "• Constitutional check — 4 virtues: Truthfulness, Trust, Clarity, Wisdom\n"
            "• Yaqin tiering — Ilm / Ain / Haqq al-Yaqin certainty levels\n\n"
            "Not just AI. AI with integrity."
        ),
    },
]


# ── Regional Research Angles ───────────────────────────────────────────────────

REGIONAL_RESEARCH = {
    "US": {
        "what_they_care": [
            "startup productivity", "ROI on AI tools", "open source vs SaaS cost",
            "building your own AI stack", "privacy for enterprise", "no vendor lock-in",
        ],
        "hooks_en": [
            "Tired of paying $20/month for AI that doesn't even cite sources? 👀",
            "What if your startup had its own AI — with zero API costs? 🚀",
            "Open source AI is eating the world. SIDIX is the proof. 💡",
            "Your data doesn't belong to OpenAI. It belongs to you. 🔒",
        ],
        "tone": "bold, ROI-focused, startup energy",
    },
    "EU": {
        "what_they_care": [
            "GDPR compliance", "data sovereignty", "AI Act readiness",
            "on-premise AI", "privacy by design", "no US data transfer",
        ],
        "hooks_en": [
            "GDPR-friendly AI that runs on YOUR server. 🇪🇺",
            "EU AI Act compliant by design — SIDIX keeps your data local. 🔒",
            "No data sent to the US. No GDPR liability. Just local AI. ✅",
            "The EU deserves AI that respects privacy. Meet SIDIX. 🛡️",
        ],
        "tone": "privacy-first, regulatory-aware, serious",
    },
    "UK": {
        "what_they_care": [
            "academic research tools", "citation integrity", "open access AI",
            "PhD research assistant", "epistemological rigor", "reproducible AI",
        ],
        "hooks_en": [
            "Finally — an AI that actually cites its sources. 📖",
            "SIDIX: the AI research assistant that doesn't hallucinate citations. 🎓",
            "For researchers who can't afford to trust black-box AI. 🔬",
            "Open source. Self-hosted. Citable. Everything academia needs. ✅",
        ],
        "tone": "academic, rigorous, citation-focused",
    },
    "AU": {
        "what_they_care": [
            "multilingual AI for diverse communities", "AI for indigenous languages",
            "regional language support", "local AI sovereignty", "community-driven tech",
        ],
        "hooks_en": [
            "AI for every language, every community — not just English. 🌏",
            "SIDIX is building AI that works for non-English speakers too. 🗣️",
            "Local AI that respects local communities. Australia included. 🦘",
            "Open source AI for the Global South — and beyond. 🌍",
        ],
        "tone": "inclusive, community-focused, multilingual angle",
    },
}


# ── Series Definitions ─────────────────────────────────────────────────────────

def _get_feature(day: int) -> dict:
    return SIDIX_FEATURES[day % len(SIDIX_FEATURES)]


def _get_region(day: int) -> tuple[str, dict]:
    regions = list(REGIONAL_RESEARCH.keys())
    region_key = regions[day % len(regions)]
    return region_key, REGIONAL_RESEARCH[region_key]


def _get_hook(day: int) -> str:
    regional_hooks_flat = []
    for r in REGIONAL_RESEARCH.values():
        regional_hooks_flat.extend(r["hooks_en"])
    return regional_hooks_flat[day % len(regional_hooks_flat)]


def generate_series(day: int | None = None) -> dict[str, str]:
    """
    Generate 3-post series untuk hari tertentu.
    Returns: {"hook": str, "detail": str, "cta": str, "angle": str, "language": str}
    """
    if day is None:
        day = int(time.time() // 86400)

    angle_idx = day % 10
    is_english = (day % 2 == 1)
    lang = "EN" if is_english else "ID"

    # Pilih angle
    if angle_idx == 0:
        return _series_islamic(day, lang)
    elif angle_idx == 1:
        return _series_tech(day, "ID")
    elif angle_idx == 2:
        return _series_tech(day, "EN")
    elif angle_idx == 3:
        return _series_regional(day, "US")
    elif angle_idx == 4:
        return _series_regional(day, "EU")
    elif angle_idx == 5:
        return _series_regional(day, "UK")
    elif angle_idx == 6:
        return _series_regional(day, "AU")
    elif angle_idx == 7:
        return _series_dev_invite(day, lang)
    elif angle_idx == 8:
        return _series_feature_launch(day, lang)
    else:
        return _series_community(day, lang)


# ── Series: Islamic Angle ──────────────────────────────────────────────────────

ISLAMIC_TOPICS = [
    {
        "topic": "Maqashid Syariah & AI Ethics",
        "hook_id": (
            "🕌 Bagaimana Islam bisa memandu etika AI?\n\n"
            "Bukan pertanyaan retoris. SIDIX sudah menjawabnya dalam kode.\n\n"
            "Setiap jawaban SIDIX melewati 5 filter Maqashid Syariah.\n"
            "Thread 🧵 ⬇️"
        ),
        "hook_en": (
            "🕌 Can Islamic ethics guide AI development?\n\n"
            "Not a rhetorical question. SIDIX has answered it — in code.\n\n"
            "Every SIDIX response passes through 5 Maqasid al-Shariah filters.\n"
            "Thread 🧵 ⬇️"
        ),
        "detail_id": (
            "📖 Maqashid Syariah = 5 tujuan utama hukum Islam:\n\n"
            "1️⃣ Hifdz al-Din — jaga agama\n"
            "2️⃣ Hifdz al-Nafs — jaga jiwa\n"
            "3️⃣ Hifdz al-Aql — jaga akal\n"
            "4️⃣ Hifdz al-Nasl — jaga keturunan\n"
            "5️⃣ Hifdz al-Mal — jaga harta\n\n"
            "SIDIX mengevaluasi SETIAP jawaban terhadap kelima sumbu ini.\n"
            "Jika konten mengancam salah satunya → diblokir atau diberi peringatan.\n\n"
            "Ini bukan filter spam biasa. Ini filsafat yang dikodekan.\n"
            "🔗 sidixlab.com"
        ),
        "detail_en": (
            "📖 Maqasid al-Shariah = 5 ultimate objectives of Islamic law:\n\n"
            "1️⃣ Hifdz al-Din — protect religion\n"
            "2️⃣ Hifdz al-Nafs — protect life\n"
            "3️⃣ Hifdz al-Aql — protect intellect\n"
            "4️⃣ Hifdz al-Nasl — protect family\n"
            "5️⃣ Hifdz al-Mal — protect wealth\n\n"
            "SIDIX evaluates EVERY response against these 5 axes.\n"
            "If content threatens any of them → blocked or flagged.\n\n"
            "Not a spam filter. This is philosophy encoded into software.\n"
            "🔗 sidixlab.com"
        ),
        "cta_id": (
            "✅ AI yang punya adab itu beda.\n\n"
            "SIDIX bukan sekadar tools — ini ekspresi nilai Islam dalam teknologi.\n\n"
            "Untuk para peneliti Islam, developer Muslim, dan akademisi:\n"
            "Kontribusi ke SIDIX adalah jariyah ilmu yang terus mengalir. 🙏\n\n"
            "👉 sidixlab.com\n"
            "Follow @sidixlab untuk series ini setiap minggu!\n\n"
            "#HalalAI #IslamicTech #AIOpenSource #FreeAIAgent"
        ),
        "cta_en": (
            "✅ AI with ethics is different.\n\n"
            "SIDIX isn't just a tool — it's Islamic values expressed in code.\n\n"
            "For Islamic scholars, Muslim developers, and ethical AI researchers:\n"
            "Contributing to SIDIX is an act of ongoing knowledge charity (jariyah). 🙏\n\n"
            "👉 sidixlab.com\n"
            "Follow @sidixlab for this series every week!\n\n"
            "#HalalAI #IslamicTech #AIOpenSource #EthicalAI"
        ),
    },
    {
        "topic": "Sanad System & AI Credibility",
        "hook_id": (
            "📜 Ulama Islam sudah solve masalah fake news 1000 tahun yang lalu.\n\n"
            "Namanya: SANAD — rantai periwayatan yang bisa diverifikasi.\n\n"
            "SIDIX mengadopsinya untuk AI. Ini caranya 🧵"
        ),
        "hook_en": (
            "📜 Islamic scholars solved fake news 1,000 years ago.\n\n"
            "It's called: SANAD — a verifiable chain of transmission.\n\n"
            "SIDIX adopts this for AI. Here's how 🧵"
        ),
        "detail_id": (
            "🔗 Sanad dalam hadis = siapa yang meriwayatkan dari siapa.\n"
            "Setiap rawi dinilai: 'adalah (integritas) × dhabt (akurasi).\n\n"
            "SIDIX Sanad Validator:\n"
            "• Setiap sumber diberi trust score (0-1)\n"
            "• Sahih = 3+ sumber valid + BFT 2/3 threshold\n"
            "• Dhaif = sumber lemah, diberi disclaimer otomatis\n"
            "• Mawdhu = palsu/berbahaya, diblokir\n\n"
            "Sistem ini diwarisi dari ulama hadis — bukan diciptakan dari nol.\n"
            "🔗 sidixlab.com"
        ),
        "detail_en": (
            "🔗 Isnad in hadith = who narrated from whom.\n"
            "Each narrator rated: 'adalah (integrity) × dhabt (accuracy).\n\n"
            "SIDIX Sanad Validator:\n"
            "• Each source gets a trust score (0-1)\n"
            "• Sahih = 3+ valid sources + BFT 2/3 threshold\n"
            "• Da'if = weak source, auto-disclaimer applied\n"
            "• Mawdu' = fabricated/harmful, blocked\n\n"
            "Inherited from hadith scholars — not invented from scratch.\n"
            "🔗 sidixlab.com"
        ),
        "cta_id": (
            "🕌 Bayangkan AI yang bisa membedakan:\n"
            "hadits shahih vs dhaif vs mawdhu.\n\n"
            "Itu adalah SIDIX yang sedang kita bangun bersama.\n\n"
            "Kamu bisa bantu:\n"
            "• Kontribusi corpus hadis terverifikasi\n"
            "• Jadi penguji fitur Islamic AI\n"
            "• Share research Islam ke SIDIX\n\n"
            "👉 sidixlab.com | Follow @sidixlab\n\n"
            "#HalalAI #IslamicAI #AIOpenSource #Sanad"
        ),
        "cta_en": (
            "🕌 Imagine an AI that can distinguish:\n"
            "sahih hadith vs da'if vs mawdu'.\n\n"
            "That's what we're building together with SIDIX.\n\n"
            "You can help:\n"
            "• Contribute verified hadith corpus\n"
            "• Become an Islamic AI feature tester\n"
            "• Share Islamic research with SIDIX\n\n"
            "👉 sidixlab.com | Follow @sidixlab\n\n"
            "#HalalAI #IslamicAI #AIOpenSource #Sanad"
        ),
    },
]


def _series_islamic(day: int, lang: str) -> dict:
    topic = ISLAMIC_TOPICS[day % len(ISLAMIC_TOPICS)]
    sfx = "_id" if lang == "ID" else "_en"
    return {
        "angle": "ISLAMIC",
        "language": lang,
        "topic": topic["topic"],
        "hook": topic[f"hook{sfx}"],
        "detail": topic[f"detail{sfx}"],
        "cta": topic[f"cta{sfx}"],
    }


# ── Series: Tech Angle ─────────────────────────────────────────────────────────

TECH_TOPICS_ID = [
    {
        "angle_name": "RAG vs Fine-tune",
        "hook": (
            "🤔 Kapan kamu pakai RAG vs Fine-tuning?\n\n"
            "Ini pertanyaan yang bikin banyak developer salah pilih.\n"
            "SIDIX pakai keduanya — tapi di tempat yang tepat. 🧵"
        ),
        "detail": (
            "📊 RAG vs Fine-tuning — kapan pakai apa?\n\n"
            "RAG (Retrieval-Augmented Generation):\n"
            "✅ Cocok untuk: dokumen yang sering update\n"
            "✅ Tidak perlu GPU besar\n"
            "✅ Mudah tambah knowledge baru\n"
            "❌ Agak lambat (harus search dulu)\n\n"
            "Fine-tuning (LoRA/QLoRA):\n"
            "✅ Cocok untuk: gaya bicara, persona, domain tetap\n"
            "✅ Lebih cepat saat inference\n"
            "❌ Butuh GPU + waktu training\n"
            "❌ Knowledge 'beku' saat training\n\n"
            "SIDIX pakai: RAG untuk knowledge + LoRA untuk gaya bahasa Indonesia.\n"
            "🔗 sidixlab.com"
        ),
        "cta": (
            "💡 Mau implement RAG sendiri?\n\n"
            "SIDIX adalah contoh nyata RAG + ReAct Agent + LoRA di atas satu server VPS biasa.\n"
            "Open source. Bisa kamu pelajari, fork, dan kembangkan.\n\n"
            "👉 sidixlab.com\n"
            "Follow @sidixlab untuk tutorial teknis setiap minggu!\n\n"
            "#AIOpenSource #LearningAI #RAG #FineTuning #FreeAIAgent"
        ),
    },
    {
        "angle_name": "Local LLM vs Cloud API",
        "hook": (
            "💸 Kamu tahu gak, biaya API OpenAI itu bisa ngurangin profit startup kamu?\n\n"
            "Ada alternatifnya. Dan itu yang SIDIX pilih dari hari pertama. 🧵"
        ),
        "detail": (
            "📊 Local LLM vs Cloud API — perbandingan jujur:\n\n"
            "☁️ Cloud API (OpenAI, Gemini, Claude):\n"
            "💰 $0.002–0.06 per 1K token\n"
            "🔒 Data dikirim ke server mereka\n"
            "⚡ Fast, no maintenance\n"
            "🔗 Vendor lock-in\n\n"
            "🏠 Local LLM (Qwen, LLaMA, Mistral):\n"
            "💰 $0 per query (biaya server sudah fixed)\n"
            "🔒 Data TIDAK keluar dari server kamu\n"
            "⚡ Sedikit lebih lambat, tapi scalable\n"
            "🔓 Bebas dari vendor\n\n"
            "SIDIX: Qwen2.5-7B + LoRA, jalan di VPS $10/bulan.\n"
            "Tidak ada biaya per query. Tidak ada privacy leak.\n"
            "🔗 sidixlab.com"
        ),
        "cta": (
            "🚀 Mau bangun AI agent sendiri tanpa bayar API?\n\n"
            "SIDIX sudah buktikan ini bisa dilakukan:\n"
            "• VPS biasa ($10/bulan)\n"
            "• Model open source (Qwen2.5)\n"
            "• Python + FastAPI\n"
            "• 500+ dokumen knowledge base\n\n"
            "Semua kodenya open source. Semua tutorialnya di sini.\n"
            "👉 sidixlab.com | Follow @sidixlab\n\n"
            "#FreeAIAgent #AIOpenSource #LocalLLM #LearningAI"
        ),
    },
]

TECH_TOPICS_EN = [
    {
        "angle_name": "How SIDIX Works",
        "hook": (
            "🔬 I built an AI agent that runs on a $10/month VPS.\n\n"
            "No OpenAI. No Google. No Azure.\n"
            "Here's the full stack 🧵"
        ),
        "detail": (
            "⚙️ The SIDIX Stack (full breakdown):\n\n"
            "🧠 Model: Qwen2.5-7B-Instruct + LoRA adapter\n"
            "📚 Knowledge: BM25 RAG, 500+ research docs\n"
            "🔄 Agent: ReAct loop (Thought→Action→Observation)\n"
            "🕌 Ethics: Islamic Epistemology Engine (Maqasid filter)\n"
            "🌐 Backend: Python FastAPI, port 8765\n"
            "💻 Frontend: Vite + TypeScript\n"
            "🖥️ Server: Ubuntu 22.04 VPS, 4GB RAM\n"
            "💰 Cost: ~$10/month total\n\n"
            "Zero cloud AI APIs. Zero vendor lock-in.\n"
            "🔗 sidixlab.com — try it free"
        ),
        "cta": (
            "✅ Everything is open source.\n\n"
            "You can:\n"
            "⭐ Star the repo\n"
            "🍴 Fork and build your own\n"
            "📝 Contribute research notes to the corpus\n"
            "🐛 Report bugs and request features\n"
            "💡 Suggest new tools and integrations\n\n"
            "Join us: sidixlab.com\n"
            "Follow @sidixlab for daily AI insights!\n\n"
            "#AIOpenSource #FreeAIAgent #OpenSourceAI #LearningAI"
        ),
    },
]


def _series_tech(day: int, lang: str) -> dict:
    if lang == "ID":
        topic = TECH_TOPICS_ID[day % len(TECH_TOPICS_ID)]
    else:
        topic = TECH_TOPICS_EN[day % len(TECH_TOPICS_EN)]
    return {
        "angle": f"TECH_{lang}",
        "language": lang,
        "topic": topic["angle_name"],
        "hook": topic["hook"],
        "detail": topic["detail"],
        "cta": topic["cta"],
    }


# ── Series: Regional Angles ────────────────────────────────────────────────────

REGIONAL_SERIES = {
    "US": [
        {
            "topic": "US Startup AI Cost",
            "hook": (
                "💸 Startup founders: how much are you spending on AI APIs?\n\n"
                "The average SaaS startup spends $2,000–$8,000/month on OpenAI alone.\n\n"
                "There's a better way. Meet SIDIX 🧵"
            ),
            "detail": (
                "📊 The math that kills startups:\n\n"
                "100 users × 50 queries/day × 500 tokens = 2.5M tokens/day\n"
                "At GPT-4o rate ($0.005/1K tokens) = $12.50/day = $375/month\n"
                "Scale to 1,000 users = $3,750/month on API alone\n\n"
                "SIDIX alternative:\n"
                "✅ $10/month VPS\n"
                "✅ Qwen2.5-7B local model\n"
                "✅ Zero cost per query\n"
                "✅ Your data stays private\n\n"
                "We've proven it works. Open source. You can fork it.\n"
                "🔗 sidixlab.com"
            ),
            "cta": (
                "🚀 Ready to cut your AI costs to near zero?\n\n"
                "SIDIX is the proof-of-concept that local AI works.\n"
                "Fork it, adapt it, deploy it for your startup.\n\n"
                "Free to use: sidixlab.com\n"
                "Follow @sidixlab for more AI cost-cutting strategies!\n\n"
                "#AIStartup #FreeAIAgent #AIOpenSource #StartupLife #LearningAI"
            ),
        },
    ],
    "EU": [
        {
            "topic": "EU Privacy & SIDIX",
            "hook": (
                "🇪🇺 EU AI Act is here. GDPR is still watching.\n\n"
                "Is your AI stack compliant?\n\n"
                "SIDIX is built privacy-first from day one. Here's why that matters 🧵"
            ),
            "detail": (
                "🔒 SIDIX Privacy Architecture:\n\n"
                "✅ Data never leaves your server\n"
                "✅ No US data transfer (no GDPR Article 46 risk)\n"
                "✅ No third-party AI APIs (no data processor agreements needed)\n"
                "✅ Full audit trail (every query logged locally)\n"
                "✅ Self-hosted = you control the data lifecycle\n"
                "✅ Open source = full transparency, no black boxes\n\n"
                "EU AI Act categories:\n"
                "SIDIX = Low risk (open source, transparent, no biometric data)\n\n"
                "🔗 sidixlab.com"
            ),
            "cta": (
                "🛡️ For European businesses who need GDPR-compliant AI:\n\n"
                "SIDIX is your answer.\n"
                "Self-hosted. Open source. Transparent. Local.\n\n"
                "Deploy it in your EU datacenter:\n"
                "👉 sidixlab.com\n\n"
                "Follow @sidixlab for AI compliance updates!\n\n"
                "#GDPR #EUAIAct #DataPrivacy #AIOpenSource #FreeAIAgent"
            ),
        },
    ],
    "UK": [
        {
            "topic": "Academic AI & Citations",
            "hook": (
                "🎓 Every academic's nightmare: AI that hallucrinates citations.\n\n"
                "I've been building an AI that actually cites its sources.\n\n"
                "Here's how SIDIX handles academic integrity 🧵"
            ),
            "detail": (
                "📚 How SIDIX handles citations:\n\n"
                "1. Every answer includes source references (RAG citations)\n"
                "2. Sanad validator rates source credibility (0-1 score)\n"
                "3. Low-confidence answers are explicitly flagged\n"
                "4. Mawdu' (fabricated) content is blocked entirely\n"
                "5. All corpus documents are versioned and traceable\n\n"
                "For researchers:\n"
                "• Feed SIDIX your papers → it answers FROM your corpus\n"
                "• Create a private research assistant with YOUR literature\n"
                "• Export citations in standard format\n\n"
                "Open source. Self-hosted. Reproducible.\n"
                "🔗 sidixlab.com"
            ),
            "cta": (
                "🔬 For PhD students, researchers, and academics:\n\n"
                "SIDIX is building the AI research assistant you actually need.\n"
                "We'd love your input on what features matter most.\n\n"
                "What would make SIDIX useful for your research?\n"
                "Reply below 👇 or visit: sidixlab.com\n\n"
                "Follow @sidixlab for academic AI updates!\n\n"
                "#AcademicAI #ResearchAI #AIOpenSource #PhDLife #LearningAI"
            ),
        },
    ],
    "AU": [
        {
            "topic": "Multilingual & Inclusion",
            "hook": (
                "🌏 90% of AI is built for English speakers.\n\n"
                "What about the other 7+ billion people?\n\n"
                "SIDIX is building AI for underserved languages. Starting with Indonesian. 🧵"
            ),
            "detail": (
                "🗣️ Why Indonesian matters:\n\n"
                "• 270 million speakers (4th most populous country)\n"
                "• Extremely underrepresented in AI training data\n"
                "• Complex local context (Islamic culture, regional dialects, local laws)\n"
                "• Standard AI models often give wrong answers for Indonesian context\n\n"
                "What SIDIX does differently:\n"
                "✅ Primary language: Bahasa Indonesia\n"
                "✅ Corpus: Indonesian research, Islamic scholarship, local context\n"
                "✅ Fine-tuned for Indonesian cultural nuance\n"
                "✅ Open source → any language community can fork it\n\n"
                "🔗 sidixlab.com"
            ),
            "cta": (
                "🌍 Multilingual AI is not a feature — it's a right.\n\n"
                "SIDIX proves that any language community can build their own AI.\n"
                "Our architecture is forkable for any language.\n\n"
                "Researchers, linguists, community builders:\n"
                "Let's build multilingual AI together.\n\n"
                "👉 sidixlab.com | Follow @sidixlab\n\n"
                "#MultilingualAI #InclusiveAI #AIOpenSource #FreeAIAgent #LearningAI"
            ),
        },
    ],
}


def _series_regional(day: int, region: str) -> dict:
    topics = REGIONAL_SERIES.get(region, REGIONAL_SERIES["US"])
    topic = topics[day % len(topics)]
    return {
        "angle": f"REGIONAL_{region}",
        "language": "EN",
        "topic": f"{region}: {topic['topic']}",
        "hook": topic["hook"],
        "detail": topic["detail"],
        "cta": topic["cta"],
    }


# ── Series: Developer/Researcher Invite ────────────────────────────────────────

DEV_INVITE_ID = {
    "hook": (
        "👨‍💻 Developer, researcher, akademisi — SIDIX butuh kamu.\n\n"
        "Ini bukan basa-basi. Ini kerja nyata yang bisa kamu contribute sekarang.\n\n"
        "Ada 5 jalur kontribusi yang terbuka 🧵"
    ),
    "detail": (
        "🛠️ 5 jalur kontribusi SIDIX:\n\n"
        "1️⃣ Research Notes — tulis 1 topik AI/Islam/sains → masuk corpus SIDIX\n"
        "2️⃣ Q&A Pairs — buat 10 pertanyaan+jawaban → jadi training data\n"
        "3️⃣ Bug Report — temukan bug → lapor → fix together\n"
        "4️⃣ Feature Request — ada ide fitur? Buka issue di GitHub\n"
        "5️⃣ Domain Expert — Islamic scholar? Fisikawan? Programmer?\n"
        "   Kontribusi knowledge domain kamu.\n\n"
        "Semua kontribusi dicatat. Setiap knowledge yang tersebar = amal jariyah.\n"
        "🔗 sidixlab.com"
    ),
    "cta": (
        "🤝 Komunitas SIDIX terbuka untuk semua:\n\n"
        "• Developer Python/FastAPI/TypeScript\n"
        "• Researcher AI/ML\n"
        "• Akademisi Islam & epistemologi\n"
        "• Penulis teknis\n"
        "• Early adopter & beta tester\n\n"
        "Mulai dari mana saja. Kontribusi sekecil apapun berarti.\n"
        "👉 sidixlab.com | Follow @sidixlab\n\n"
        "#AIOpenSource #OpenSourceContrib #LearningAI #FreeAIAgent #BuildInPublic"
    ),
}

DEV_INVITE_EN = {
    "hook": (
        "👨‍💻 Developers, researchers, academics — SIDIX needs you.\n\n"
        "Not a PR pitch. Real work you can contribute right now.\n\n"
        "5 open contribution paths 🧵"
    ),
    "detail": (
        "🛠️ 5 ways to contribute to SIDIX:\n\n"
        "1️⃣ Research Notes — write about any AI/science topic → enters SIDIX corpus\n"
        "2️⃣ Q&A Pairs — create 10 question+answer pairs → training data\n"
        "3️⃣ Bug Reports — find a bug → report → fix together\n"
        "4️⃣ Feature Requests — have an idea? Open a GitHub issue\n"
        "5️⃣ Domain Expert — Islamic scholar? Physicist? ML researcher?\n"
        "   Contribute your domain knowledge.\n\n"
        "All contributions credited. Every shared knowledge = lasting impact.\n"
        "🔗 sidixlab.com"
    ),
    "cta": (
        "🤝 The SIDIX community is open to everyone:\n\n"
        "• Python/FastAPI/TypeScript developers\n"
        "• AI/ML researchers\n"
        "• Islamic scholars & epistemologists\n"
        "• Technical writers\n"
        "• Early adopters & beta testers\n\n"
        "Start anywhere. Every contribution matters.\n"
        "👉 sidixlab.com | Follow @sidixlab\n\n"
        "#AIOpenSource #OpenSourceContrib #LearningAI #FreeAIAgent #BuildInPublic"
    ),
}


def _series_dev_invite(day: int, lang: str) -> dict:
    src = DEV_INVITE_ID if lang == "ID" else DEV_INVITE_EN
    return {
        "angle": "DEV_INVITE",
        "language": lang,
        "topic": "Developer/Researcher Recruitment",
        "hook": src["hook"],
        "detail": src["detail"],
        "cta": src["cta"],
    }


# ── Series: Feature Launch ─────────────────────────────────────────────────────

def _series_feature_launch(day: int, lang: str) -> dict:
    feat = _get_feature(day)
    status_label = {
        "live": "🟢 LIVE",
        "beta": "🟡 BETA",
        "coming_soon": "🔵 COMING SOON",
        "roadmap": "⚪ ROADMAP",
    }.get(feat["status"], "🔵")

    if lang == "ID":
        hook = (
            f"{feat['emoji']} NEW SIDIX FEATURE {status_label}\n\n"
            f"{feat['tagline_id']}\n\n"
            f"Kita bahas lebih dalam 🧵"
        )
        detail = (
            f"{feat['emoji']} {feat['name']} — {status_label}\n\n"
            f"{feat['detail_id']}\n\n"
            f"🔗 sidixlab.com"
        )
        cta = (
            f"✅ {feat['name']} adalah satu dari banyak fitur SIDIX.\n\n"
            f"Masih banyak yang sedang dibangun. Kamu bisa ikut membangunnya!\n\n"
            f"Coba gratis: sidixlab.com\n"
            f"Follow @sidixlab untuk update fitur terbaru!\n\n"
            f"#SIDIXFeature #FreeAIAgent #AIOpenSource #LearningAI"
        )
    else:
        hook = (
            f"{feat['emoji']} NEW SIDIX FEATURE {status_label}\n\n"
            f"{feat['tagline_en']}\n\n"
            f"Thread 🧵"
        )
        detail = (
            f"{feat['emoji']} {feat['name']} — {status_label}\n\n"
            f"{feat['detail_en']}\n\n"
            f"🔗 sidixlab.com"
        )
        cta = (
            f"✅ {feat['name']} is one of many SIDIX features.\n\n"
            f"More are being built. You can help build them!\n\n"
            f"Try free: sidixlab.com\n"
            f"Follow @sidixlab for the latest feature releases!\n\n"
            f"#SIDIXFeature #FreeAIAgent #AIOpenSource #LearningAI"
        )

    return {
        "angle": "FEATURE_LAUNCH",
        "language": lang,
        "topic": f"Feature: {feat['name']}",
        "hook": hook,
        "detail": detail,
        "cta": cta,
    }


# ── Series: Community Engagement ──────────────────────────────────────────────

COMMUNITY_POSTS = [
    {
        "lang": "ID",
        "hook": (
            "🗣️ Pertanyaan untuk komunitas AI Indonesia:\n\n"
            "Kalau ada satu fitur AI yang bisa kamu request sekarang, apa yang kamu pilih?\n\n"
            "Bisa jadi kita bangun untuk SIDIX! 👇"
        ),
        "detail": (
            "📋 Fitur yang sedang diminta komunitas SIDIX:\n\n"
            "🔹 Voice input (rekam suara → teks → jawab)\n"
            "🔹 PDF reader (upload dokumen → tanya isinya)\n"
            "🔹 Multi-bahasa daerah (Jawa, Sunda, dll)\n"
            "🔹 Integrasi kalender Islam\n"
            "🔹 Generator konten dakwah\n\n"
            "Yang mana yang paling kamu butuhkan?\n"
            "Comment di bawah ⬇️ | sidixlab.com"
        ),
        "cta": (
            "💬 Setiap feedback adalah kontribusi nyata.\n\n"
            "SIDIX dibangun DARI komunitas, UNTUK komunitas.\n"
            "Suara kamu menentukan roadmap kami.\n\n"
            "👉 sidixlab.com\n"
            "Follow @sidixlab dan ikut shaping AI Indonesia!\n\n"
            "#AIIndonesia #FreeAIAgent #AIOpenSource #LearningAI #BuildInPublic"
        ),
    },
    {
        "lang": "EN",
        "hook": (
            "💬 Question for the AI community:\n\n"
            "What's the one AI feature you wish existed but doesn't yet?\n\n"
            "We might build it into SIDIX. Reply below 👇"
        ),
        "detail": (
            "📋 Most-requested SIDIX features so far:\n\n"
            "🔹 Voice input (speak → transcribe → AI answers)\n"
            "🔹 PDF reader (upload any doc → ask questions about it)\n"
            "🔹 Real-time web search integration\n"
            "🔹 Multi-agent collaboration\n"
            "🔹 API for developers to build on top\n\n"
            "Which one matters most to you?\n"
            "Comment below ⬇️ | sidixlab.com"
        ),
        "cta": (
            "💡 Every reply is a contribution to SIDIX.\n\n"
            "We build based on real community needs.\n"
            "Your voice shapes our roadmap.\n\n"
            "👉 sidixlab.com\n"
            "Follow @sidixlab and help shape the future of open AI!\n\n"
            "#AIOpenSource #FreeAIAgent #OpenSourceAI #LearningAI #BuildInPublic"
        ),
    },
]


def _series_community(day: int, lang: str) -> dict:
    # Filter by lang
    options = [p for p in COMMUNITY_POSTS if p["lang"] == lang]
    if not options:
        options = COMMUNITY_POSTS
    post = options[day % len(options)]
    return {
        "angle": "COMMUNITY",
        "language": lang,
        "topic": "Community Engagement",
        "hook": post["hook"],
        "detail": post["detail"],
        "cta": post["cta"],
    }


# ── State Tracking ─────────────────────────────────────────────────────────────

def get_today_series() -> dict:
    """Get series untuk hari ini, cek apakah sudah dipost."""
    day = int(time.time() // 86400)
    series = generate_series(day)
    state = _load_state()
    today = _today_str()
    posted = state.get("posted", {}).get(today, {})
    return {
        "day": day,
        "series": series,
        "posted": {
            "hook": posted.get("hook", False),
            "detail": posted.get("detail", False),
            "cta": posted.get("cta", False),
        },
        "ready": {
            "hook": not posted.get("hook", False),
            "detail": posted.get("hook", False) and not posted.get("detail", False),
            "cta": posted.get("detail", False) and not posted.get("cta", False),
        },
    }


def mark_post_sent(post_type: str, post_id: str) -> None:
    """Catat bahwa sebuah tipe post sudah dikirim hari ini."""
    state = _load_state()
    today = _today_str()
    if "posted" not in state:
        state["posted"] = {}
    if today not in state["posted"]:
        state["posted"][today] = {}
    state["posted"][today][post_type] = post_id
    # Track total
    state["total_series_posts"] = state.get("total_series_posts", 0) + 1
    _save_state(state)


def get_series_stats() -> dict:
    state = _load_state()
    today = _today_str()
    posted_today = state.get("posted", {}).get(today, {})
    return {
        "total_series_posts": state.get("total_series_posts", 0),
        "today": today,
        "posted_today": posted_today,
        "hook_done": bool(posted_today.get("hook")),
        "detail_done": bool(posted_today.get("detail")),
        "cta_done": bool(posted_today.get("cta")),
        "today_angle": generate_series()["angle"],
        "today_language": generate_series()["language"],
        "today_topic": generate_series()["topic"],
    }
