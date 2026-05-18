"""
dummy_agents.py — SIDIX Synthetic User Agents
Simulasi percakapan dari berbagai tipe user untuk mengisi Jariyah pairs.

5 agent persona:
  1. DevBot       — coding, debugging, minta bikin aplikasi
  2. DesignBot    — konsep desain, branding, UI/UX, konten video & kreatif
  3. PolyglotBot  — pertanyaan dalam Arabic, English, Javanese, Sundanese, Malay
  4. CuriousBot   — pengetahuan umum, sains, sejarah, berita & isu terkini
  5. BizBot       — bisnis, marketing, strategi, entrepreneur

Flow per agent:
  1. Ambil pertanyaan dari bank soal (shuffle + random)
  2. POST /agent/chat → dapat session_id + answer
  3. Auto-rate: heuristic quality check → "up" / "down"
  4. POST /agent/feedback → Jariyah pair tersimpan
  5. Delay acak 2-8 detik (simulasi user nyata)

Jalankan:
  python scripts/dummy_agents.py                 # semua agent, 1 round
  python scripts/dummy_agents.py --rounds 5      # 5 round
  python scripts/dummy_agents.py --agent dev     # hanya DevBot
  python scripts/dummy_agents.py --dry-run       # tanpa kirim ke server
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import urllib.request
import urllib.error

# ── Config ─────────────────────────────────────────────────────────────────────
_CFG = {"base_url": "https://ctrl.sidixlab.com"}  # mutable — diupdate dari args
# _CFG = {"base_url": "http://localhost:8765"}    # lokal dev


# ── Quality heuristic untuk auto-rating ─────────────────────────────────────
def _auto_rate(question: str, answer: str) -> str:
    """
    Heuristic sederhana: up jika jawaban ≥ 80 karakter dan tidak berisi error marker.
    Down jika terlalu pendek atau mengandung tanda gagal.
    """
    if not answer or len(answer) < 60:
        return "down"
    fail_signals = [
        "maaf, saya tidak", "tidak bisa menjawab", "error", "gagal",
        "cannot", "i don't know", "i'm not sure", "i cannot",
        "[error]", "404", "500",
    ]
    low = answer.lower()
    if any(sig in low for sig in fail_signals):
        return "down"
    # Bonus: ada struktur (code block, numbered list, heading) → up
    quality_signals = ["```", "1.", "##", "**", "langkah", "contoh", "step"]
    if any(sig in low for sig in quality_signals):
        return "up"
    if len(answer) >= 200:
        return "up"
    return "up" if random.random() > 0.25 else "down"


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _post(path: str, payload: dict, timeout: int = 90) -> Optional[dict]:
    url = f"{_CFG['base_url']}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        print(f"  [HTTP {e.code}] {path} — {body}")
    except Exception as e:
        print(f"  [ERR] {path} — {type(e).__name__}: {e}")
    return None


# ── Agent dataclass ───────────────────────────────────────────────────────────
@dataclass
class DummyAgent:
    name: str
    slug: str
    persona: str
    color: str   # ANSI color code
    questions: list[str]
    mode: str = "default"   # default | simple


# ── Question Banks ────────────────────────────────────────────────────────────

_DEV_QUESTIONS = [
    # Coding & debugging
    "Apa perbedaan antara async/await dan Promise di JavaScript?",
    "Bagaimana cara handle race condition di Python threading?",
    "Jelaskan perbedaan SQL JOIN: INNER, LEFT, RIGHT, FULL OUTER",
    "Buatkan fungsi Python untuk validasi email dengan regex",
    "Kenapa kode ini infinite loop? while True: if x > 5: break",
    "Apa itu Big O notation? Jelaskan O(n), O(log n), O(n²)",
    "Bagaimana cara implementasi binary search di Python?",
    "Apa perbedaan stack dan heap memory?",
    "Debug: TypeError: 'NoneType' object is not subscriptable",
    "Cara optimasi query SQL yang lambat di tabel 10 juta baris",

    # Bikin aplikasi
    "Buatkan todo app sederhana dengan HTML, CSS, JavaScript murni",
    "Buatkan REST API sederhana dengan FastAPI + endpoint CRUD",
    "Buat script Python untuk scraping harga produk dari website",
    "Buatkan chatbot sederhana dengan Python tanpa library AI",
    "Buat sistem login dengan JWT token di Node.js Express",
    "Buatkan kalkulator BMI dengan Python + GUI tkinter",
    "Buat script otomatis backup file setiap jam ke folder tertentu",
    "Buatkan API rate limiter sederhana di Python",
    "Buat sistem notifikasi email dengan Python smtplib",
    "Buatkan web scraper untuk ambil berita dari website publik",

    # Konsep teknis
    "Jelaskan cara kerja HTTPS dan SSL/TLS certificate",
    "Apa itu Docker dan kenapa developer harus pakai Docker?",
    "Perbedaan monolith vs microservices, kapan pakai yang mana?",
    "Jelaskan konsep event-driven architecture",
    "Apa itu GraphQL dan bedanya dengan REST API?",
    "Cara kerja DNS dari ketik URL sampai halaman tampil",
    "Apa itu CI/CD pipeline dan bagaimana implementasinya?",
    "Jelaskan perbedaan Redis dan database SQL biasa",
    "Apa itu WebSocket dan kapan lebih baik dari HTTP polling?",
    "Cara kerja garbage collector di Python",
]

_DESIGN_QUESTIONS = [
    # UI/UX
    "Apa prinsip dasar desain UI yang harus diketahui pemula?",
    "Bagaimana cara membuat color palette yang profesional?",
    "Jelaskan konsep whitespace dalam desain dan kenapa penting",
    "Apa perbedaan UX dan UI? Mana yang lebih penting?",
    "Tips membuat typography hierarchy yang efektif",
    "Bagaimana cara desain form yang user-friendly?",
    "Jelaskan konsep visual hierarchy dalam desain",
    "Apa itu design system dan kenapa perusahaan besar membutuhkannya?",
    "Bagaimana cara membuat mockup aplikasi mobile yang meyakinkan?",
    "Prinsip Gestalt apa saja yang sering dipakai di desain digital?",

    # Branding
    "Apa elemen penting dalam membangun brand identity?",
    "Cara membuat logo yang simple tapi memorable",
    "Jelaskan perbedaan brand, branding, dan brand identity",
    "Bagaimana cara riset target audience untuk campaign branding?",
    "Apa itu brand archetype? Berikan contoh brand yang pakai hero archetype",
    "Tips membuat brand voice yang konsisten di semua channel",
    "Bagaimana cara audit brand yang sudah lama berjalan?",

    # Konten video & kreatif
    "Struktur video YouTube yang paling efektif untuk retensi penonton",
    "Cara bikin hook video TikTok yang bikin orang tidak skip dalam 3 detik",
    "Tips menulis script video edukasi yang engaging",
    "Bagaimana cara storytelling yang baik dalam konten Instagram?",
    "Apa perbedaan konten evergreen vs trending? Kapan pakai masing-masing?",
    "Cara membuat thumbnail YouTube yang tinggi CTR",
    "Tips repurposing satu konten jadi 5 format berbeda",
    "Bagaimana cara riset konten yang viral di niche tertentu?",
    "Jelaskan konsep content pillar dalam strategi konten media sosial",
    "Cara membuat storyboard untuk iklan 30 detik",
]

_POLYGLOT_QUESTIONS = [
    # English
    "What is the difference between machine learning and deep learning?",
    "Explain the concept of compound interest with an example",
    "What are the main causes of climate change?",
    "How does the human immune system fight viruses?",
    "What is stoicism and how can it be applied in modern life?",
    "Explain blockchain technology in simple terms",
    "What makes a great leader according to modern research?",
    "How do habits form in the brain? Explain the habit loop",

    # Arabic
    "ما هو الفرق بين الذكاء الاصطناعي والتعلم الآلي؟",
    "اشرح مفهوم التضخم الاقتصادي وأسبابه",
    "ما هي أهمية الذكاء العاطفي في بيئة العمل؟",
    "اشرح مبدأ أوكام المعروف بـ شفرة أوكام",
    "ما هي الفرق بين الادخار والاستثمار؟",

    # Javanese
    "Apa bedane antara basa krama lan basa ngoko ing basa Jawa?",
    "Coba jelasno opo kui revolusi industri 4.0 nganggo basa sing gampang",

    # Sundanese
    "Naon bédana antara élmu jeung pangaweruh?",
    "Kumaha carana diajar éféktif nurutkeun psikologi modern?",

    # Malay (Malaysia/Brunei style)
    "Apakah perbezaan antara kecerdasan buatan dan kecerdasan manusia?",
    "Bolehkah anda jelaskan konsep ekonomi gig dengan contoh?",
    "Bagaimana cara untuk meningkatkan produktiviti kerja dari rumah?",

    # Informal/Gaul Indonesia
    "Bro, jelasin dong gimana cara crypto itu kerja, tapi yang simple",
    "Eh SIDIX, lo tau ga perbedaan saham sama obligasi? jelasin dong",
    "Gue penasaran, kenapa orang susah bangun pagi? ada penjelasan ilmiahnya ga?",
]

_CURIOUS_QUESTIONS = [
    # Sains
    "Jelaskan teori relativitas Einstein dengan bahasa yang mudah dipahami",
    "Bagaimana cara kerja vaksin di dalam tubuh manusia?",
    "Apa itu kuantum computing dan bedanya dengan komputer biasa?",
    "Kenapa langit berwarna biru? Jelaskan secara ilmiah",
    "Bagaimana otak manusia menyimpan memori jangka panjang?",
    "Apa itu CRISPR dan bagaimana teknologi ini bisa mengubah dunia?",
    "Jelaskan fenomena efek kupu-kupu dalam teori chaos",
    "Kenapa kita butuh tidur? Apa yang terjadi di otak saat tidur?",

    # Sejarah & sosial
    "Apa penyebab utama jatuhnya Kekaisaran Romawi?",
    "Jelaskan dampak revolusi industri terhadap masyarakat modern",
    "Apa itu efek Dunning-Kruger dan contoh nyatanya dalam kehidupan?",
    "Bagaimana cara kerja propaganda dan mengapa efektif?",
    "Jelaskan konsep cognitive bias yang paling umum ditemui sehari-hari",
    "Apa perbedaan sosialisme, kapitalisme, dan komunisme?",

    # Pengetahuan umum & berita
    "Apa itu inflasi dan bagaimana pengaruhnya terhadap masyarakat biasa?",
    "Jelaskan apa itu geopolitik dan contoh konflik geopolitik terkini",
    "Apa itu resesi ekonomi dan tanda-tandanya?",
    "Bagaimana cara kerja sistem demokrasi di Indonesia?",
    "Apa dampak jangka panjang kecerdasan buatan terhadap lapangan kerja?",
    "Jelaskan apa itu green energy dan mengapa penting untuk masa depan",
    "Apa itu Web3 dan bagaimana berbeda dari internet yang ada sekarang?",
    "Jelaskan perkembangan AI terbaru yang paling signifikan di 2024-2025",

    # Filsafat & kehidupan
    "Apa itu stoikisme dan bagaimana praktis diterapkan sehari-hari?",
    "Jelaskan konsep ikigai dari filosofi Jepang",
    "Apa perbedaan antara moral dan etika?",
    "Mengapa manusia cenderung takut pada ketidakpastian?",
]

_BIZ_QUESTIONS = [
    # Bisnis & startup
    "Jelaskan framework lean startup dan kapan cocok digunakan",
    "Apa perbedaan B2B dan B2C? Mana yang lebih menguntungkan?",
    "Bagaimana cara validasi ide bisnis sebelum invest banyak waktu?",
    "Jelaskan konsep product-market fit dan cara mengukurnya",
    "Tips negosiasi harga dengan supplier agar dapat harga terbaik",
    "Apa itu unit economics dan kenapa penting untuk startup?",
    "Jelaskan perbedaan growth hacking vs traditional marketing",
    "Bagaimana cara membangun tim kecil yang produktif?",

    # Marketing & konten
    "Jelaskan framework AIDA untuk copywriting yang efektif",
    "Apa itu content marketing dan bagaimana strategi yang efektif?",
    "Cara membuat email marketing yang open rate-nya tinggi",
    "Jelaskan perbedaan SEO on-page dan off-page beserta tips praktis",
    "Apa itu funnel marketing dan bagaimana cara kerjanya?",
    "Bagaimana cara membuat lead magnet yang efektif?",
    "Tips membuat pitch deck yang menarik investor",
    "Cara menghitung ROI dari campaign iklan media sosial",

    # Keuangan bisnis
    "Jelaskan perbedaan cash flow, profit, dan revenue",
    "Apa itu burn rate dan runway di konteks startup?",
    "Bagaimana cara buat proyeksi keuangan sederhana untuk bisnis baru?",
    "Jelaskan konsep bootstrapping vs funding, mana yang lebih baik?",
]


# ── Agent instances ───────────────────────────────────────────────────────────
AGENTS: dict[str, DummyAgent] = {
    "dev": DummyAgent(
        name="DevBot",
        slug="dev",
        persona="AYMAN",
        color="\033[36m",   # cyan
        questions=_DEV_QUESTIONS,
    ),
    "design": DummyAgent(
        name="DesignBot",
        slug="design",
        persona="ABOO",
        color="\033[35m",   # magenta
        questions=_DESIGN_QUESTIONS,
    ),
    "polyglot": DummyAgent(
        name="PolyglotBot",
        slug="polyglot",
        persona="UTZ",
        color="\033[33m",   # yellow
        questions=_POLYGLOT_QUESTIONS,
    ),
    "curious": DummyAgent(
        name="CuriousBot",
        slug="curious",
        persona="UTZ",
        color="\033[32m",   # green
        questions=_CURIOUS_QUESTIONS,
    ),
    "biz": DummyAgent(
        name="BizBot",
        slug="biz",
        persona="AYMAN",
        color="\033[34m",   # blue
        questions=_BIZ_QUESTIONS,
    ),
}

RESET = "\033[0m"
BOLD = "\033[1m"


# ── Core loop ─────────────────────────────────────────────────────────────────
def run_agent(agent: DummyAgent, dry_run: bool = False, verbose: bool = False) -> dict:
    """Ambil 1 pertanyaan random, kirim ke SIDIX, auto-rate, submit feedback."""
    question = random.choice(agent.questions)
    ts = datetime.now().strftime("%H:%M:%S")

    print(f"{agent.color}{BOLD}[{agent.name}]{RESET} {ts} → {question[:80]}{'…' if len(question) > 80 else ''}")

    if dry_run:
        print(f"  [dry-run] skip HTTP call")
        return {"ok": True, "dry_run": True}

    # Step 1: Tanya SIDIX
    # Deteksi pertanyaan panjang/kompleks → simple_mode untuk respons lebih cepat
    is_complex = len(question) > 60 or any(
        k in question.lower() for k in ["buatkan", "buat ", "implement", "bikin", "create", "build"]
    )
    resp = _post("/agent/chat", {
        "question": question,
        "persona": agent.persona,
        "simple_mode": is_complex,
        "allow_web_fallback": True,
    })

    if not resp:
        print(f"  {agent.color}✗ No response{RESET}")
        return {"ok": False, "reason": "no_response"}

    session_id = resp.get("session_id", "")
    answer = resp.get("answer", "")
    steps = resp.get("steps", 0)
    duration = resp.get("duration_ms", 0)

    if verbose:
        print(f"  steps={steps} duration={duration}ms")
        print(f"  answer: {answer[:150]}{'…' if len(answer) > 150 else ''}")

    # Step 2: Auto-rate
    vote = _auto_rate(question, answer)
    vote_icon = "[up]" if vote == "up" else "[dn]"

    # Step 3: Submit feedback
    fb = _post("/agent/feedback", {
        "session_id": session_id,
        "vote": vote,
    })

    fb_ok = fb is not None and fb.get("ok", False)
    status = "✓" if fb_ok else "~"
    print(f"  {agent.color}{status}{RESET} {vote_icon} session={session_id[:8]} ans={len(answer)}chars")

    return {
        "ok": True,
        "session_id": session_id,
        "vote": vote,
        "answer_len": len(answer),
        "steps": steps,
    }


def run_round(agents: list[DummyAgent], dry_run: bool = False, delay: tuple = (2, 8), verbose: bool = False) -> dict:
    """Satu round: semua agent dapat 1 pertanyaan masing-masing (urutan random)."""
    random.shuffle(agents)
    stats = {"up": 0, "down": 0, "fail": 0}

    for agent in agents:
        result = run_agent(agent, dry_run=dry_run, verbose=verbose)
        if result.get("ok"):
            if result.get("vote") == "up":
                stats["up"] += 1
            elif result.get("vote") == "down":
                stats["down"] += 1
        else:
            stats["fail"] += 1

        # Jeda acak antar request — simulasi user nyata + jaga rate limit
        if not dry_run:
            wait = random.uniform(*delay)
            time.sleep(wait)

    return stats


# ── Progress display ──────────────────────────────────────────────────────────
def print_stats(total_up: int, total_down: int, total_fail: int, rounds_done: int) -> None:
    total = total_up + total_down
    rate = f"{total_up/total*100:.0f}%" if total > 0 else "0%"
    print(f"\n{BOLD}--- Round {rounds_done} selesai ---{RESET}")
    print(f"  👍 up={total_up}  👎 down={total_down}  ✗ fail={total_fail}")
    print(f"  Quality rate: {rate} | Total pairs: {total}")


def print_jariyah_stats(dry_run: bool) -> None:
    if dry_run:
        return
    try:
        with urllib.request.urlopen(f"{_CFG['base_url']}/jariyah/stats", timeout=10) as r:
            d = json.loads(r.read().decode())
        print(f"\n{BOLD}[Jariyah DB]{RESET}")
        print(f"  total={d.get('total',0)} | up={d.get('thumbs_up',0)} | down={d.get('thumbs_down',0)}")
        print(f"  exportable={d.get('exportable',0)} | ready_for_lora={d.get('ready_for_lora',False)}")
        print(f"  threshold={d.get('threshold',500)}")
    except Exception:
        pass


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SIDIX Dummy Agents — generate Jariyah training pairs")
    parser.add_argument("--rounds", type=int, default=1, help="Jumlah round (default: 1)")
    parser.add_argument("--agent", choices=list(AGENTS.keys()) + ["all"], default="all",
                        help="Agent mana yang jalan (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Jangan kirim ke server, simulasi saja")
    parser.add_argument("--delay-min", type=float, default=2.0, help="Delay min antar request (detik)")
    parser.add_argument("--delay-max", type=float, default=8.0, help="Delay max antar request (detik)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Tampilkan preview jawaban")
    parser.add_argument("--url", default=_CFG["base_url"], help=f"Base URL backend (default: {_CFG['base_url']})")
    args = parser.parse_args()

    _CFG["base_url"] = args.url

    # Pilih agents
    if args.agent == "all":
        active_agents = list(AGENTS.values())
    else:
        active_agents = [AGENTS[args.agent]]

    total_up = total_down = total_fail = 0

    print(f"\n{BOLD}=== SIDIX Dummy Agents ==={RESET}")
    print(f"URL    : {_CFG['base_url']}")
    print(f"Agents : {', '.join(a.name for a in active_agents)}")
    print(f"Rounds : {args.rounds}")
    print(f"Delay  : {args.delay_min}–{args.delay_max}s")
    print(f"Dry run: {args.dry_run}")
    print()

    for round_num in range(1, args.rounds + 1):
        print(f"{BOLD}Round {round_num}/{args.rounds}{RESET}")
        print("-" * 50)

        stats = run_round(
            active_agents,
            dry_run=args.dry_run,
            delay=(args.delay_min, args.delay_max),
            verbose=args.verbose,
        )
        total_up += stats["up"]
        total_down += stats["down"]
        total_fail += stats["fail"]

        print_stats(total_up, total_down, total_fail, round_num)

        # Jeda antar round (lebih panjang)
        if round_num < args.rounds and not args.dry_run:
            between = random.uniform(5, 15)
            print(f"  (jeda {between:.0f}s sebelum round berikutnya…)")
            time.sleep(between)

    print_jariyah_stats(args.dry_run)
    print(f"\n{BOLD}=== SELESAI ==={RESET}")


if __name__ == "__main__":
    main()
