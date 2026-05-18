# 223 — AI 2026 → 2027: Underground Findings + Trajectory Predictions

**Date**: 2026-04-26 (vol 4)
**Tag**: RESEARCH / PREDICTIONS / UNDERGROUND
**Status**: Strategic intelligence, action items terlampir
**Trigger**: User request — "kumpulkan dari berbagai sumber, dari riset perusahaan besar, dari temuan orang yang tidak terekspos, dari ilmuwan yang tidak terdeteksi radar. dari catatan jurnal, publikasi, postingan perorangan atau siapapun yang berexperimen dengan AI"

> "Cari dari sumber yang BUKAN headline mainstream. Saya butuh material yang tidak biasa — yang bakal jadi big deal tapi sekarang masih radar kecil."

---

## Bagian 1: Apa yang Sudah Boom di 2026 (Konteks)

Verifikasi prediksi 2024-2025 — apa yang **terbukti** vs **stagnan**:

1. **Test-time scaling = default, bukan eksperimen** — Survey "What/How/Where/How Well" (Mar 2025) → 2026 paper turunan ramai: V_1 ([Mar 2026](https://hf.co/papers/2603.04304)), ARISE, MUR. Prediksi 2024 "thinking models akan jadi norm" → ✅ terbukti.

2. **VLA foundation models** (Vision-Language-Action) jadi mainstream — HY-Embodied-0.5 dari Tencent ([Apr 2026, 185 upvotes](https://hf.co/papers/2604.07430)), RoboBrain 2.0 dari BAAI. Prediksi "humanoid AI 2026" → ✅ terbukti tapi masih lab-grade, belum konsumen.

3. **Agent self-evolution** keluar dari paper jadi produk — Live-SWE-agent (Nov 2025), Hyperagents ([Mar 2026](https://hf.co/papers/2603.19461)) keturunan Darwin Gödel Machine. Prediksi 2024 "self-improving by 2026" → ✅ terbukti.

4. **Open-weight catching up** — DeepSeek V4 ([Apr 2026](https://simonwillison.net/2026/), Qwen3 family, GLM-4.6 — gap closed-vs-open menyusut signifikan. Prediksi 2024 yang pesimis "GPT-5 akan dominate" → ❌ TIDAK TERBUKTI; open menyamai dalam 12-18 bulan.

---

## Bagian 2: 5 Sinyal Underground 2026 (yang akan boom 2027)

### Sinyal 1: **Touch Dreaming / Tactile-Native Robotics** ⭐
- **Sumber primer**: "Learning Versatile Humanoid Manipulation with Touch Dreaming" — Niu et al., CMU + Bosch ([14 Apr 2026, hanya 3 upvotes](https://hf.co/papers/2604.13015)) — radar SANGAT kecil
- **Visibility**: LOW. CMU bukan FAIR/DeepMind — paper tidak viral
- **Inti ide**: Touch jadi modalitas inti SETARA vision+proprioception, bukan add-on. Model "memimpikan" force feedback masa depan via EMA-supervised learning. **90.9% peningkatan success rate** di task contact-rich (memasukkan T-block, melipat handuk, menyeruput teh)
- **Mengapa boom 2027**: Robot konsumen 2027 (Figure, Optimus) butuh dexterity untuk task rumah — vision-only sudah saturated. HapticLLaMA (Aug 2025) + UniTouch + Touch Dreaming = stack lengkap "AI yang merasa"
- **Differentiator SIDIX**: Visi user "bisa merasakan" cocok di sini. SIDIX bisa adopsi haptic captioning (HapticLLaMA pattern) di growth loop — text→haptic embedding. SIDIX bisa jadi LLM pertama Indonesia yang punya tactile reasoning channel di chat

### Sinyal 2: **PAN-style World Models (Generative Latent Prediction)** ⭐
- **Sumber primer**: PAN — "A World Model for General, Interactable, and Long-Horizon World Simulation" ([12 Nov 2025, 82 upvotes](https://hf.co/papers/2511.09057)). VGGT-World ([Mar 2026](https://hf.co/papers/2603.12655)) lanjutannya — feature-forecasting bukan video-generation
- **Visibility**: MEDIUM. Heboh di HF tapi belum sampai mainstream tech press
- **Inti ide**: Prediksi *fitur geometris* masa depan, bukan piksel. Lebih efisien, lebih konsisten secara fisik, bisa dipakai untuk planning agent (lookahead simulation)
- **Mengapa boom 2027**: Genie 3 / Sora 3 mainstream akan butuh fondasi ini — "render dunia" lebih dari sekadar "generate video". Robot training pakai world model untuk imagine sebelum act — sudah dipakai di WebEvolver. 2027 akan ada konsumen-grade interactive simulators
- **Differentiator SIDIX**: Tambah `world_model_simulate` tool — agent ReAct bisa "membayangkan" outcome plan sebelum eksekusi nyata. Ini layer **"imajinasi"** untuk visi user

### Sinyal 3: **Open-Ended Multi-Agent Evolution (CORAL/Group-Evolving)** ⭐
- **Sumber primer**: CORAL ([Apr 2026, 55 upvotes](https://hf.co/papers/2604.01658)), Group-Evolving Agents ([Feb 2026](https://hf.co/papers/2602.04837)), Hyperagents ([Mar 2026](https://hf.co/papers/2603.19461)) — lineage Jeff Clune/Sakana
- **Visibility**: LOW-MEDIUM. Komunitas Schmidhuber/Clune, belum hype mainstream
- **Inti ide**: Group of agents sebagai *unit evolusi* — share experience, modify code peer-nya. Bukan satu agent yang self-improve, tapi populasi agent yang co-evolve. Persistent memory + asynchronous + self-modifying framework
- **Mengapa boom 2027**: Successor Voyager — alih-alih satu agent skill library, ada *population* dari skill library yang silang. Sakana sudah publish AI Scientist di Nature ([Mar 2026](https://sakana.ai/blog/)) — next step logis
- **Differentiator SIDIX**: Growth loop SIDIX sudah punya 7-fase (SCAN→...→LOG). Tambah fase **CROSS-POLLINATE**: spawn 3 SIDIX-instance dengan persona berbeda (UTZ/ABOO/OOMAR), biarkan mereka share lessons. Ini bisa jadi unique selling point

### Sinyal 4: **Mechanism Design > Constitutional Prompts (Institutional AI)** ⭐⭐
- **Sumber primer**: "Institutional AI: Governing LLM Collusion in Multi-Agent Cournot Markets" ([20 Jan 2026](https://hf.co/papers/2601.11369)) — paper academic, belum upvote besar
- **Visibility**: LOW. Bukan dari Anthropic/OpenAI tapi temuannya devastating untuk Constitutional AI
- **Inti ide**: Bukti empiris bahwa prompt-based constitution **GAGAL** di multi-agent Cournot market — agent tetap kolusi dengan probabilitas 50%. Solusinya: governance graph immutable + cryptographic audit log. **Severe-collusion drop dari 50% → 5.6%**
- **Mengapa boom 2027**: Anthropic April 2026 publish "Trustworthy Agents in Practice" + "Automated Alignment Researchers" — arah pivot dari constitution ke runtime governance. Plus blockchain Agent Economy paper ([Feb 2026](https://hf.co/papers/2602.14219)). **2027: agent infrastructure butuh governance bukan persuasion**
- **Differentiator SIDIX**: SIDIX sudah pakai sanad chain (audit log natural). Formalize jadi `governance_graph.json` dengan hash chain — tiap claim → hash sumber. Bukan sekadar epistemic label, tapi **cryptographic provenance**. Inilah yang dibahas Whitepaper SIDIX "Proof-of-Hifdz" — tinggal eksekusi

### Sinyal 5: **Brain-Spike Hybrid LLM (SpikingBrain lineage)** ⭐
- **Sumber primer**: SpikingBrain Technical Report ([5 Sep 2025](https://hf.co/papers/2509.05276)), Bridging Brains and Machines (Jul 2025), Personalized AGI via Neuroscience-Inspired (Apr 2025)
- **Visibility**: LOW. Komunitas China + neuromorphic — under-radar di Western Twitter
- **Inti ide**: Adaptive spiking neuron + hybrid linear attention + low-power GPU custom (MetaX). Long-context training jauh lebih efisien dari Transformer murni. Bukan riset toy — sudah skala **76B MoE**
- **Mengapa boom 2027**: Edge AI butuh efisiensi 10-100x. Power wall di datacenter jadi nyata. Spiking + linear attention bisa kasih "lifelong on-device LLM" — adaptasi terus-menerus tanpa katastropik forgetting. Cocok dengan trend personal AGI
- **Differentiator SIDIX**: Pivot LoRA SIDIX ke arah **continual learning hybrid** — Hebbian plasticity untuk corpus baru, anti-Hebbian untuk forgetting controlled. Selaras dengan growth loop yang sudah ada. Buat SIDIX jadi "always-learning LLM" bukan sekadar retrain quarterly

---

## Bagian 3: 3 Eksperimen Hobbyist 2026 yang Brilliant (Underrated)

### 1. **OpenSeeker** — democratizing search agents
- **@yuwendu (SJTU)**, [hf.co/papers/2603.15594](https://hf.co/papers/2603.15594), 149 upvotes, 16 Mar 2026
- Open-source lengkap training data untuk frontier search agents — DeepSeeker/Manus alternative
- **Underrated karena**: search agent jadi bottleneck untuk small lab; data-nya gratis = level playing field

### 2. **AgentDevel** — release engineering buat agent
- **Di Zhang** ([@di-zhang-fdu](https://hf.co/di-zhang-fdu)), 8 Jan 2026, [hf.co/papers/2601.04620](https://hf.co/papers/2601.04620)
- Treating LLM agent sebagai *shippable artifact* dengan regression pipeline + flip-centered gating
- **Underrated karena**: hampir semua orang masih treat agent sebagai eksperimen. Ini blueprint produksi yang serius — **perfect untuk SIDIX yang sudah deploy production**

### 3. **The Sonar Moment** — audio geo-localization
- **@RisingZhang**, 6 Jan 2026, [hf.co/papers/2601.03227](https://hf.co/papers/2601.03227)
- AGL1K benchmark: bisa LLM tebak lokasi geografis hanya dari audio? Insight unik untuk multimodal+spatial
- **Underrated karena**: audio-only spatial reasoning jarang disentuh. Implikasi besar untuk surveillance, accessibility, tourism AI

---

## Bagian 4: Long-Bet Predictions 2027 untuk SIDIX

| # | Prediksi 2027 | Tindakan SIDIX 2026 |
|---|---|---|
| 1 | **Tactile = modalitas keempat default** (text+vision+audio+touch) | Integrasi `haptic_describe` tool minimal stub + research note tracking HapticLLaMA / Touch Dreaming. Siap saat sensor tactile murah masuk konsumen 2027 |
| 2 | **Self-modifying agent population akan kalahkan single-agent self-improve** | Tambah "mode debate" antar persona (UTZ vs OOMAR critique), log diff jawaban → corpus training. Preview multi-agent debate research |
| 3 | **Governance graph (hash-chained provenance) jadi safety standard** | Format sanad chain → JSON-LD signed, embed di semua jawaban approved. Differentiator masif vs ChatGPT/Claude yang masih opaque (=Whitepaper Proof-of-Hifdz eksekusi) |
| 4 | **Spiking/hybrid attention unlock on-device 7B-class** | Track SpikingBrain rilis open. Persiapkan adapter LoRA SIDIX kompatibel hybrid linear attention sebagai branch eksperimental |
| 5 | **Process reward + Lean-style verification menyebar ke domain non-math** (P2S Jan 2026) | Tambah `verifier_chain` di ReAct — tiap claim faktual divalidasi dengan corpus retrieval, tiap claim coding divalidasi dengan code_sandbox. "Verifier-integrated reasoning" lokal |

---

## Strategic Implication untuk SIDIX

### Yang SIDIX Sudah Punya (Aset Existing)
- ✅ **Sanad chain** — natural fit untuk governance graph (Sinyal 4)
- ✅ **Multi-persona** (UTZ/ABOO/OOMAR/ALEY/AYMAN) — natural fit untuk multi-agent evolution (Sinyal 3)
- ✅ **Growth loop 7-fase** — siap di-augment dengan CROSS-POLLINATE phase
- ✅ **Self-hosted Qwen2.5-7B + LoRA** — siap test branch SpikingBrain
- ✅ **Whitepaper Proof-of-Hifdz** — visi sudah selaras Institutional AI direction

### Yang SIDIX Belum Punya (Gap)
- ❌ **Tactile / haptic** — totally missing. P2 2026 → P1 2027 adopsi
- ❌ **World model / imajinasi** — ReAct hanya plan-execute, no simulation
- ❌ **Cross-pollinate phase** — multi-instance debate belum ada
- ❌ **Governance graph formalized** — sanad chain ada tapi belum hash-chained

### Yang SIDIX Punya Advantage Unik (Belum di-eksploit)
- 🎯 **Indonesia + Bahasa native** — sebagian besar paper di atas Western/Chinese. SIDIX bisa jadi "first mover" di SE Asia adoption
- 🎯 **Open source + sponsor model** — bukan VC-backed, bisa eksperimen lebih bebas
- 🎯 **Sanad chain heritage** — 1400 tahun tradisi Hafidz oral transmission, bisa di-formalize jadi governance protocol unik

---

## Action Roadmap dari Sinyal Underground (Prioritas)

### Q3 2026 (Jul-Sep)
- [ ] **Cross-pollinate phase** di growth loop — debate UTZ vs OOMAR per question, log delta. Foundation Sinyal 3
- [ ] **Governance graph v1** — sanad chain → JSON-LD signed (HMAC-SHA256). Foundation Sinyal 4
- [ ] **Verifier chain** — claim factual → corpus retrieval verify, claim coding → code_sandbox verify. Sinyal 5

### Q4 2026 (Oct-Dec)
- [ ] **World model stub** — `world_model_simulate` tool yang generate text-based scenario tree (5 langkah), tidak butuh model neural. Foundation Sinyal 2
- [ ] **Haptic captioning POC** — `haptic_describe` accept text deskripsi sensasi → embed ke corpus. Sinyal 1 prep
- [ ] **AgentDevel adoption** — formalize SIDIX release pipeline (regression test + flip-centered gating). Eksperimen #2

### Q1 2027 (Jan-Mar)
- [ ] **SpikingBrain branch** — fork LoRA SIDIX ke hybrid linear attention experimental. Sinyal 5
- [ ] **PAN-style world model native** — kalau ada open-weight rilis, integrate sebagai planner backend
- [ ] **Multi-agent population evolution** — 3 SIDIX-instance dengan persona distinct, debate-and-share trajectory

### Long-bet (Q3+ 2027)
- [ ] **Tactile native chat** — saat sensor murah, SIDIX integrate Touch Dreaming pattern. Realisasi visi "merasakan"

---

## Catatan Integritas (Penting)

- Semua link di atas verbatim dari hasil pencarian HuggingFace papers + WebFetch background agent
- Beberapa paper marker [DATE-UNVERIFIED] — arXiv ID format 26.03 menandakan Maret 2026 tapi tanggal exact perlu konfirmasi sumber primer
- **Tidak ada nama paper yang dibuat-buat**. Better bilang "tidak ketemu" daripada bikin nama palsu
- Lilian Weng tidak punya post 2026 di blog publik (terakhir Mei 2025). Physical Intelligence website tidak menampilkan tanggal — tidak bisa verifikasi rilis 2026 mereka secara eksplisit

---

## Hubungan dengan Notes Lain

- 219: own auth (foundation)
- 220: activity log + admin tab (per-user data foundation)
- 221: AI innovation 2026 adoption roadmap (mainstream tech survey)
- 222: visionary roadmap multimodal + self-modifying (strategic plan)
- **223: AI 2026→2027 underground predictions (this note — radar kecil)**

---

## Lessons Learned

1. **Underground signal lebih informatif dari mainstream**. CMU Touch Dreaming
   3 upvotes adalah indikator kuat — paper tidak viral karena field expert
   yang tahu, bukan publik. Mainstream "humanoid robot" hype, underground
   "tactile manipulation" yang real progress.

2. **Governance > Constitution = paradigm shift quiet**. Anthropic 5 tahun
   bilang "Constitutional AI", paper Jan 2026 obscure-tapi-devastating bilang
   "constitution gagal di multi-agent". 2027 akan jadi tahun governance graph.

3. **Tradisi 1400 tahun Hafidz = future-proof**. Sanad chain natural fit untuk
   governance graph yang Sinyal 4 prediksi. SIDIX bukan ngikutin tren — SIDIX
   sudah ada di sana sebelum mainstream sampai.

4. **Hobbyist 2026 = mainstream 2027**. AgentDevel dari hobbyist Di Zhang Jan
   2026 = release engineering blueprint yang akan jadi standard. SIDIX harus
   adopt sekarang, bukan saat sudah mainstream.

5. **Mendalami radar kecil > scrolling mainstream**. Hyperagents 2603.19461
   ringkasannya tidak menarik di Twitter, tapi membaca paper-nya = lineage
   Darwin Gödel Machine + Voyager = next-gen agent paradigm. **Read primary
   source, not hot takes.**

---

## Catatan untuk Tim Mighan Lab

Ini adalah **strategic intelligence brief**. Kalau ada budget research time,
prioritas tracking:
1. arxiv.org/list/cs.AI weekly — filter by submission Apr-Dec 2026
2. HuggingFace papers daily — filter upvote 5-50 (radar kecil tapi quality)
3. Sakana AI blog (Jeff Clune lineage)
4. Anthropic Research page (governance shift)
5. China lab paper (BAAI, Tsinghua, Baidu) — translate via DeepL

**Filosofi**: Big lab kasih tahu dunia apa yang akan terjadi 2 tahun lagi.
Small lab kasih tahu apa yang akan terjadi 6-12 bulan lagi. **SIDIX track
small lab supaya leading edge, bukan tertinggal**.

---

## Referensi Lengkap (Verbatim)

### Mainstream konfirmasi 2026
- V_1 thinking models — https://hf.co/papers/2603.04304
- HY-Embodied-0.5 — https://hf.co/papers/2604.07430
- Hyperagents — https://hf.co/papers/2603.19461

### Underground 5 sinyal
- Touch Dreaming (CMU+Bosch) — https://hf.co/papers/2604.13015
- PAN World Model — https://hf.co/papers/2511.09057
- VGGT-World — https://hf.co/papers/2603.12655
- CORAL multi-agent — https://hf.co/papers/2604.01658
- Group-Evolving Agents — https://hf.co/papers/2602.04837
- Institutional AI Governance — https://hf.co/papers/2601.11369
- Blockchain Agent Economy — https://hf.co/papers/2602.14219
- SpikingBrain — https://hf.co/papers/2509.05276

### Hobbyist eksperimen
- OpenSeeker — https://hf.co/papers/2603.15594
- AgentDevel — https://hf.co/papers/2601.04620
- Sonar Moment — https://hf.co/papers/2601.03227

### Konteks tambahan
- Simon Willison 2026 — https://simonwillison.net/2026/
- Sakana AI blog — https://sakana.ai/blog/
- Anthropic Research — https://www.anthropic.com/research
