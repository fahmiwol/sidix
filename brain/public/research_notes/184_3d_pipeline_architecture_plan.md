# 3D Generation Pipeline — Arsitektur & Implementation Plan
**[OPINION]** — 2026-04-21 (pre-implementation skeleton)

## Target Sprint 6
`text_to_3d.py` + `image_to_3d.py` minimal viable → live sebagai tool SIDIX #36/#37.
DoD: `tools_available ≥ 38` (base 35 + 3D text + 3D image + procedural).

---

## Stack Keputusan

### Primary: Hunyuan3D (self-host, Tencent open-source)
- Model: `tencent/Hunyuan3D-2` (HuggingFace)
- Kelebihan: open-source, bisa self-host di VPS/Colab, output GLB/OBJ
- Masalah: butuh GPU ≥ 8GB VRAM. VPS saat ini CPU-only → **fallback wajib**

### Fallback: Sloyd Bridge API
- REST API: `https://api.sloyd.ai/v1/generate` (game asset 3D)
- Auth: `SLOYD_API_KEY` di `.env`
- Output: GLB download URL
- Gratis tier: 100 model/bulan

### Fallback 2: Meshy API  
- `https://api.meshy.ai/v1/text-to-3d` (text → 3D mesh)
- Auth: `MESHY_API_KEY` di `.env`
- Output: OBJ/FBX/GLB + preview thumbnail PNG

### For `procedural_3d.py`: Blender headless
- `blender --background --python script.py`
- Harus Blender terinstall di server
- Alternatif: `trimesh` library (pure Python, tidak perlu Blender binary)

---

## File Structure Sprint 6

```
apps/brain_qa/brain_qa/
├── text_to_3d.py          ← NEW: teks → 3D mesh (Hunyuan3D / Sloyd / Meshy)
├── image_to_3d.py         ← NEW: gambar → 3D mesh (Hunyuan3D / tripo3d)
├── procedural_3d.py       ← NEW: Blender headless / trimesh parametric
├── npc_generator.py       ← NEW: personality + dialogue tree + character sheet
└── character_builder.py   ← NEW: brand maskot + IP-Adapter consistency
```

---

## text_to_3d.py — Skeleton

```python
"""text_to_3d.py — SIDIX 3D Text-to-Mesh pipeline."""

_PROVIDER_ORDER = ["hunyuan3d", "sloyd", "meshy", "mock"]

def generate_3d_from_text(
    prompt: str,
    style: str = "realistic",       # realistic | cartoon | low_poly | isometric
    output_format: str = "glb",     # glb | obj | fbx
    provider: str | None = None,    # None = auto fallback chain
) -> dict:
    """
    Returns:
      {ok, model_url, preview_url, format, provider_used, elapsed_s}
    """
    ...

def _try_hunyuan3d(prompt, style, fmt) -> dict: ...
def _try_sloyd(prompt, style, fmt) -> dict: ...
def _try_meshy(prompt, style, fmt) -> dict: ...
def _mock_response(prompt) -> dict: ...  # dev/test tanpa API
```

**Agent tool registration** (di `agent_tools.py`):
```python
{
  "name": "text_to_3d",
  "description": "Generate 3D model dari deskripsi teks. Output: GLB/OBJ download URL.",
  "parameters": {
    "prompt": "str — deskripsi objek 3D",
    "style": "str — realistic|cartoon|low_poly|isometric (default: realistic)",
    "output_format": "str — glb|obj|fbx (default: glb)",
  }
}
```

---

## image_to_3d.py — Skeleton

```python
"""image_to_3d.py — SIDIX Image-to-3D pipeline."""

def generate_3d_from_image(
    image_url: str,         # URL gambar referensi
    output_format: str = "glb",
    provider: str | None = None,
) -> dict:
    """
    Returns:
      {ok, model_url, preview_url, format, provider_used, elapsed_s}
    """
    ...
```

**Provider kandidat untuk image_to_3d:**
- Hunyuan3D-2 (multi-view reconstruction)
- TripoSR (open-source, cepat, 1 gambar → mesh)
  - `pip install tsr` — model ~1GB
  - CPU feasible (lambat tapi jalan)
- Meshy image-to-3d endpoint

---

## npc_generator.py — Skeleton

```python
"""npc_generator.py — Gaming NPC personality + dialogue generator."""

@dataclass
class NPCProfile:
    name: str
    archetype: str          # hero | villain | mentor | trickster | sage | guardian
    personality_traits: list[str]
    backstory: str
    dialogue_samples: list[str]    # 5 sample dialogues
    stats: dict                    # strength/intelligence/charisma/agility
    faction: str

def generate_npc(
    game_context: str,
    role: str = "npc",
    archetype: str | None = None,
) -> dict:
    """Hasilkan NPC lengkap dengan personality, backstory, dialogue tree."""
    ...
```

---

## Urutan Implementasi (sesi berikutnya)

1. **Setup env vars** — tambah ke `.env.sample`: `SLOYD_API_KEY`, `MESHY_API_KEY`
2. **`text_to_3d.py`** — fallback chain: Sloyd (paling reliable) → Meshy → mock
3. **`image_to_3d.py`** — TripoSR (CPU-feasible) + Meshy fallback
4. **Register di `agent_tools.py`** — tool #36 + #37
5. **Endpoint di `agent_serve.py`** — `POST /3d/text` + `POST /3d/image`
6. **Test** — `test_3d_pipeline.py` dengan mock provider
7. **`npc_generator.py`** — setelah 3D mesh tools live

---

## Risiko & Mitigasi

| Risiko | Kemungkinan | Mitigasi |
|--------|-------------|----------|
| Hunyuan3D butuh GPU | Tinggi (VPS CPU-only) | Skip Hunyuan3D di prod, Sloyd/Meshy dulu |
| Sloyd API rate limit | Sedang | Mock fallback untuk dev + cache hasil |
| TripoSR model besar (1GB) | Tinggi | Lazy-load, download only on first use |
| Output GLB besar (>10MB) | Tinggi | Simpan ke `/tmp/`, return URL bukan embed |

---

## Referensi
- `docs/MASTER_ROADMAP_2026-2027.md` Sprint 6 §3D
- `brain/public/research_notes/165_sidix_creative_capability_expansion.md`
- `brain/public/research_notes/171_image_model_comparison_sdxl_flux_alternatif.md`
- HuggingFace: `tencent/Hunyuan3D-2`
- Sloyd API docs: sloyd.ai/developers
- TripoSR: `VAST-AI-Research/TripoSR`
