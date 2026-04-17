# 112 — Permanent Learning SIDIX: SPIN Self-Play, Skill Reinforcement, Meta-Skills

**Tag:** `permanent-learning` `spin` `self-play` `skill` `reinforcement` `meta-skill` `sidix`  
**Tanggal:** 2026-04-18  
**Track:** O — Core AI Capabilities

---

## Apa

`permanent_learning.py` adalah sistem pembelajaran permanen SIDIX. Setiap skill yang dipelajari **tidak pernah dihapus** (hanya bisa dormant). Skill diperkuat melalui penggunaan (reinforcement) dan self-play (SPIN-style).

---

## Analogi Inti: Jalan → Lari → Menari

Manusia yang sudah bisa berjalan tidak akan lupa cara berjalan, meski 10 tahun tidak berjalan. Malah bisa berkembang:

```
bisa berjalan → bisa berlari → bisa menari → bisa mengajarkan tari
```

Ini berbeda dari AI konvensional yang "lupa" ketika model di-retrain atau context window habis.

**Permanent Learning SIDIX:**
- Walk → bisa jelaskan konsep dasar
- Run → bisa aplikasikan di berbagai konteks
- Dance → bisa combine dengan skills lain (meta-skills)
- Teach → bisa ajarkan ke orang lain (tasmi')

---

## Mengapa Ini Penting

Masalah AI saat ini:
1. **Catastrophic forgetting** — belajar hal baru → lupa yang lama
2. **No growth** — skill tidak makin kuat dengan penggunaan
3. **No meta-skills** — tidak bisa spontan gabungkan kemampuan
4. **No self-improvement** — butuh data eksternal untuk belajar

Permanent Learning SIDIX menjawab ini dengan:
1. Skill tidak pernah dihapus (min_strength = 0.1, tidak bisa 0)
2. Setiap penggunaan → reinforce (+0.05 success, -0.02 failure)
3. Skill bisa dikombinasikan → meta-skill
4. Self-play (SPIN) — belajar dari diri sendiri

---

## Arsitektur

### Kelas `Skill`

```python
@dataclass
class Skill:
    skill_id: str          # SHA256 dari name:domain (12 char)
    name: str
    domain: str
    strength: float        # 0.1 - 1.0 (tidak pernah 0)
    usage_count: int
    success_count: int
    usage_history: list    # 100 entry terakhir
    is_dormant: bool       # True jika lama tidak dipakai
    combined_from: list    # skill_ids jika ini meta-skill
```

### Level System

| Strength | Level |
|----------|-------|
| 0.9 - 1.0 | Maestro |
| 0.75 - 0.9 | Expert |
| 0.55 - 0.75 | Proficient |
| 0.35 - 0.55 | Developing |
| 0.1 - 0.35 | Beginner |

---

## Reinforcement Mechanism

```python
def reinforce(self, success: bool) -> float:
    boost = +0.10 if success else -0.02
    self.strength = max(0.1, min(1.0, self.strength + boost))
    # Skill TIDAK PERNAH di bawah 0.1 — permanent minimum
    return self.strength
```

**Intuisi:** Kegagalan itu belajar, bukan penghapusan. Bahkan setelah banyak kegagalan, skill masih ada (strength = 0.1) — siap untuk dihidupkan kembali.

### Time Decay

```python
def apply_decay(self, days_since_use: float):
    if days_since_use > 7:  # Decay mulai setelah 1 minggu
        decay = 0.99 ** (days_since_use - 7)
        self.strength = max(0.1, self.strength * decay)
```

Decay sangat lambat (0.99^n) — skill tidak hilang, hanya sedikit melemah. Seperti manusia yang jarang berjalan — bisa sedikit kaku, tapi langsung kembali setelah mulai lagi.

---

## SPIN Self-Play

### Apa itu SPIN?

**SPIN = Self-Play via INtrospection**

Terinspirasi dari:
1. **AlphaGo Zero** — bermain vs dirinya sendiri, tanpa data manusia, mencapai level grandmaster
2. **SPIN Paper** (Chen et al., 2024) — LLM bisa self-improve dengan generate questions + answer questions + learn from gap
3. **Tasmi' dalam Islam** — murid menyetorkan hafalan ke diri sendiri sebelum ke guru

### Bagaimana Self-Play Bekerja

```
Round 1: Challenge "Explain {skill} simply" (difficulty 0.3)
  SIDIX generates explanation → evaluates → if good: reinforce+, else: reinforce-

Round 2: Challenge "Apply {skill} with example" (difficulty 0.4)
  SIDIX generates example → evaluates → reinforce accordingly

Round 3: Challenge "Identify edge cases of {skill}" (difficulty 0.6)
  SIDIX identifies cases → evaluates → reinforce
```

### Challenge Templates (berdasarkan level skill)

| Level | Challenge Types | Max Difficulty |
|-------|----------------|----------------|
| Beginner | explain_simple, apply_example | 0.4 |
| Developing | + compare_contrast | 0.6 |
| Proficient | + edge_case, teach_back | 0.8 |
| Expert/Maestro | + cross_domain | 1.0 |

```python
rounds = solver.self_play("python_programming", n_rounds=5)
# Round 1: Explain python simply → quality 0.72 → SUCCESS → strength +0.10
# Round 2: Apply example → quality 0.65 → SUCCESS → strength +0.10
# Round 3: Compare vs JavaScript → quality 0.48 → FAIL → strength -0.02
# Round 4: Edge cases → quality 0.71 → SUCCESS → strength +0.10
# Round 5: Cross-domain (teach) → quality 0.88 → SUCCESS → strength +0.10
# Summary: 0.52 → 0.80 (+0.28)
```

---

## Meta-Skills: Gabungan yang Lebih dari Jumlah Bagiannya

```python
learner = PermanentLearning()
result = learner.combine_skills(["python", "machine_learning", "data_visualization"])
# → meta_skill: "python × machine_learning × data_visualization"
# → strength: geometric mean × 0.8 (sedikit lebih lemah dari components)
# → level: tergantung strength hasil

# Mengapa geometric mean? Karena bottleneck matters.
# Skill dengan strength 0.9, 0.9, 0.1 → meta-skill ~ 0.35 (bukan 0.63!)
# Ini realistic: tidak bisa jadi ML engineer hebat kalau viznya jelek.
```

---

## Trajectory — Melihat Progress

```python
trajectory = learner.get_learning_trajectory()
# {
#   "total_skills": 47,
#   "active_skills": 43,
#   "avg_strength": 0.61,
#   "overall_level": "Practitioner",
#   "domain_summary": {
#     "programming": {"skill_count": 12, "avg_strength": 0.72},
#     "islamic_studies": {"skill_count": 8, "avg_strength": 0.65},
#     ...
#   },
#   "strongest_skills": [{"name": "python", "strength": 0.91, "level": "maestro"}],
#   "skills_needing_practice": [{"name": "rust", "strength": 0.22}],
#   "trajectory_label": "Solid expertise — mayoritas skill sudah kuat"
# }
```

---

## Consolidation — Merge Skills yang Overlap

```python
result = learner.consolidate()
# Cari skill dengan nama similarity > 0.7 di domain yang sama
# Merge: yang kuat menyerap yang lemah + usage count digabung
# → "python_programming" + "programming_python" → satu entry
```

---

## Storage

```
.data/permanent_learning/
  skills.json    ← semua skill dalam satu JSON
```

Content-addressable: skill_id = hash(name:domain). Duplikat otomatis terdeteksi.

---

## Contoh Nyata: SIDIX Belajar Tentang Hadits

```python
# Hari 1: SIDIX mempelajari tentang isnad hadits
learner.add_skill("isnad_validation", "islamic_studies", 
                  "Validasi rantai perawi hadits")
# → strength: 0.3 (beginner)

# Hari 3: SIDIX berhasil memvalidasi hadits dalam conversation
learner.reinforce_skill("isnad_validation", {"success": True, 
                        "description": "Berhasil identify hadits dhaif"})
# → strength: 0.4

# Hari 7: SIDIX self-play 3 rounds
learner.self_play("isnad_validation", n_rounds=3)
# → strength: 0.62 (Proficient)

# Hari 14: Combine dengan skills lain
learner.combine_skills(["isnad_validation", "rijal_ilm", "fiqh_basics"])
# → meta-skill: "hadits scholar profile" strength 0.48
```

---

## Keterbatasan

1. **Self-play `_simulate_attempt`** — saat ini heuristik sederhana (random + strength factor). Dalam produksi, harus trigger actual LLM attempt + evaluator LLM.
2. **Tidak ada external validation** — skill bisa "self-reinforce" tanpa validasi nyata dari user
3. **Storage JSON** — tidak scalable untuk ribuan skills. Perlu migrate ke SQLite atau Supabase
4. **Skill similarity detection** sederhana — berbasis word overlap, bisa miss paraphrase
5. **Tidak ada multi-agent** — skill satu SIDIX tidak dishare ke instance lain

---

## Next Steps

- [ ] Replace `_simulate_attempt` dengan actual LLM reasoning + evaluator
- [ ] Tambahkan skill sharing antar SIDIX instances via Supabase
- [ ] Implement decay yang lebih sophisticated (tidak flat 0.99)
- [ ] REST endpoints: `POST /learning/reinforce`, `GET /learning/trajectory`, `POST /learning/self-play`
- [ ] Visualisasi trajectory (graph skill growth over time)

---

## Referensi

- Silver et al., *Mastering the game of Go without human knowledge* (AlphaGo Zero, 2017)
- Chen et al., *Self-Play Fine-Tuning Converts Weak Language Models to Strong Language Models* (SPIN, 2024)
- Research note 27: Continual Learning SIDIX
- Research note 29: Human Experience Engine
- Research note 70: Self-Healing AI System
