# SIDIX Coding Knowledge Corpus

> Direktori ini berisi knowledge base teknis untuk SIDIX.
> Sumber: roadmap.sh (CC BY-SA 4.0) + sintesis dari dokumentasi resmi + epistemologi Islam.
> Total: 14 research notes + 12 roadmap topic files + 2 Python modules (epistemologi + user_intelligence)

## Research Notes (brain/public/research_notes/)

Comprehensive synthesis files (~2000-5000 kata + kode):

### Coding Research Notes (33–40)

| File | Topik | Tags |
|---|---|---|
| `../research_notes/33_coding_python_comprehensive.md` | Python lengkap | python, oop, async, pytest |
| `../research_notes/34_coding_backend_web_development.md` | Backend/FastAPI/REST | fastapi, rest, auth, sqlalchemy |
| `../research_notes/35_coding_data_structures_algorithms.md` | DSA + implementasi Python | dsa, sorting, graph, dp |
| `../research_notes/36_coding_system_design.md` | System Design | scalability, caching, microservices |
| `../research_notes/37_coding_javascript_typescript.md` | JS/TS/React/Node | javascript, typescript, react, hooks |
| `../research_notes/38_coding_git_docker_linux.md` | Git/Docker/Linux/Bash | git, docker, linux, devops |
| `../research_notes/39_coding_sql_databases.md` | SQL/PostgreSQL/ORM | sql, postgresql, indexes, transactions |
| `../research_notes/40_coding_machine_learning_ai.md` | ML/PyTorch/LoRA/RAG | ml, pytorch, lora, rag, llm |

### Islamic Epistemology Research Notes (41–43)

Fondasi filosofi epistemik SIDIX — konversi tradisi keilmuan Islam → arsitektur AI:

| File | Topik | Tags |
|---|---|---|
| `../research_notes/41_islamic_epistemology_sidix_architecture.md` | Fondasi Epistemologi SIDIX: sanad, maqashid, ijtihad, hikmah → SIDIX architecture | sanad, maqashid, ijtihad, hikmah, dikw-h, proof-of-hifdz |
| `../research_notes/42_quran_preservation_tafsir_diversity.md` | Preservasi Al-Qur'an 14 abad + keragaman tafsir (polisemi, ibn rushd) | quran, tafsir, sanad, qira'at, polisemi, epistemologi |
| `../research_notes/43_islamic_foundations_ai_methodology.md` | 23 topik keilmuan Islam → 12 aksioma AI bertumbuh + pipeline end-to-end | fitrah, marhalah, nafs, yaqin, amal-jariyah, sidix-constitution |

### Multilingual & Visual AI Research Notes (44–46)

Fondasi teknis SIDIX sebagai agen trilingual (ID/AR/EN) + pemahaman visual:

| File | Topik | Tags |
|---|---|---|
| `../research_notes/44_llm_indonesia_arab_code_blueprint.md` | Blueprint LLM trilingual: corpus ID/AR/EN, MoE, GRPO, tajwid, arud, training pipeline | llm, corpus, pretraining, indonesian, arabic, trilingual, moe, grpo, benchmark |
| `../research_notes/45_visual_ai_generatif_blueprint.md` | Visual AI Generatif: diffusion (DDPM→Flux), LoRA, VLM, caption pipeline, Nusantara peluang | diffusion, flux, lora, vlm, stable-diffusion, vae, mmdeit, qwen2.5-vl |
| `../research_notes/46_seni_visual_teknologi_fondasi.md` | Seni Visual & Teknologi: fotografi (exposure triangle), warna (CMYK/RGB), desain (Bauhaus, IA 8 prinsip), codec, deepfake, etika | fotografi, warna, tipografi, codec, deepfake, c2pa, bauhaus, wcag |

## Roadmap Topic Files (brain/public/coding/)

Quick reference files berisi topik index + code snippets:

| File | Sumber | Topik Utama |
|---|---|---|
| `roadmap_system_design_topics.md` | roadmap.sh/system-design | CAP, Load Balancing, Caching, Patterns |
| `roadmap_dsa_topics.md` | roadmap.sh/datastructures-and-algorithms | Sorting, Search, Trees, Graphs, DP |
| `roadmap_computer_science_topics.md` | roadmap.sh/computer-science | Data structures, Algorithms, OS, Security |
| `roadmap_sql_topics.md` | roadmap.sh/sql | JOIN, CTE, Window Functions, ACID |
| `roadmap_git_topics.md` | roadmap.sh/git-github | Branching, Rebase, GitHub Flow, CI/CD |
| `roadmap_docker_topics.md` | roadmap.sh/docker | Dockerfile, Compose, Networking, Registry |
| `roadmap_linux_topics.md` | roadmap.sh/linux | Shell, Process, systemd, SSH, Scripting |
| `roadmap_javascript_topics.md` | roadmap.sh/javascript | Closures, Async, Modules, DOM, Patterns |
| `roadmap_ml_topics.md` | roadmap.sh/machine-learning | sklearn, PyTorch, NLP, Transformers |
| `roadmap_python_topics.md` | roadmap.sh/python | Types, OOP, Decorators, Async, Testing |
| `roadmap_backend_topics.md` | roadmap.sh/backend | REST, FastAPI, Auth, Redis, WebSocket |
| `roadmap_ai_engineer_topics.md` | roadmap.sh/ai-engineer | Prompting, RAG, LoRA, Evaluation, LLMOps |

## Python Module Epistemologi

| File | Deskripsi |
|---|---|
| `apps/brain_qa/brain_qa/epistemology.py` | Full epistemology engine — Maqashid, Sanad, Ijtihad Loop, ConstitutionalCheck, Hikmah register |
| `apps/brain_qa/brain_qa/user_intelligence.py` | User Intelligence module — language detection (ID/AR/EN/JV/SU/mixed), literacy inference (awam→akademik), intent classification (8 archetypes), cultural frame detection, SessionIntelligence accumulator |

### Komponen `epistemology.py`

- `YaqinLevel` — 3 tingkat kepastian ('ilm / 'ain / haqq)
- `EpistemicTier` — mutawatir / ahad_hasan / ahad_dhaif / mawdhu'
- `AudienceRegister` — burhan / jadal / khitabah (Ibn Rushd)
- `CognitiveMode` — ta'aqqul / tafakkur / tadabbur / tadzakkur
- `NafsStage` — 7 martabat alignment trajectory
- `SanadLink`, `Sanad`, `SanadValidator` — citation chain + trust scoring 2D
- `MaqashidScore`, `MaqashidEvaluator` — 5-axis alignment (Al-Shatibi)
- `ConstitutionalCheck`, `validate_constitutional()` — 4 sifat Nabi check
- `HikmahContext`, `infer_audience_register()`, `format_for_register()` — audience-adaptive
- `IjtihadResult`, `IjtihadLoop` — 4-step grounded reasoning
- `SIDIXEpistemologyEngine` — pipeline utama
- `process()` — shorthand untuk integrasi ke agent_react.py

### Integrasi ke agent pipeline

```python
from brain_qa.epistemology import process

# Di dalam agent_react.py / agent_serve.py:
result = process(
    question=user_question,
    raw_answer=llm_output,
    context=rag_context,
    sources=retrieved_sources,
    user_context=user_profile,
)

if result["passes"]:
    return result["answer"]  # formatted + epistemic labels
else:
    failed = result["constitutional"]["failed"]
    return f"[Output difilter: {failed}]"
```

## Reindex setelah update corpus

```powershell
cd apps\brain_qa
python -m brain_qa index
```

## Dataset SFT

| File | Deskripsi | Jumlah |
|---|---|---|
| `brain/datasets/finetune_sft.jsonl` | Dataset v1 (Mighan general) | 713 samples |
| `apps/brain_qa/data/finetune_coding_sft.jsonl` | Dataset coding (untuk v2) | ~150 samples |

Merge untuk fine-tune v2:
```bash
cat brain/datasets/finetune_sft.jsonl \
    apps/brain_qa/data/finetune_coding_sft.jsonl \
    > combined_sft_v2.jsonl
wc -l combined_sft_v2.jsonl  # should be ~863+
```
