# Plugin jembatan asisten (opsional)

**Bahasa Indonesia**

Folder ini menyediakan **pola integrasi opsional**: SIDIX tetap *standing alone*; Anda boleh menambahkan **endpoint sendiri** (self-hosted) yang memprotokolkan permintaan tambahan.

- **Tidak ada** kunci API bawaan di repositori.
- **Tidak ada** ketergantungan wajib pada layanan pihak ketiga.
- Konfigurasi hanya lewat variabel lingkungan di server Anda.

**English**

Optional **bridge pattern** only. Bring your own self-hosted HTTP endpoint. No bundled third-party credentials.

## Environment

| Variable | Meaning |
|----------|---------|
| `SIDIX_ASSISTANT_BRIDGE_URL` | Base URL (optional) for POST `/invoke` compatible endpoint |
| `SIDIX_ASSISTANT_BRIDGE_TOKEN` | Optional shared secret (set on server only, never commit) |

## Usage

Dari root repo, folder memakai tanda hubung — impor modul dengan path file:

```python
import importlib.util
from pathlib import Path

p = Path("kimi-plugin/bridge.py")
spec = importlib.util.spec_from_file_location("sidix_assistant_bridge", p)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

AssistantBridge = mod.AssistantBridge
bridge = AssistantBridge.from_env()
if bridge:
    out = bridge.forward({"task": "summarize", "text": "..."})
```

Lihat `bridge.py` untuk kontrak payload minimal.

## Artefak integrasi host (Kimi / skill)

| File | Fungsi |
|------|--------|
| `manifest.json` | Manifest plugin: 8 *skills*, *trigger* `/sidix`, `/sociometer`, `/nasihah`, konfigurasi multibahasa |
| `sidix_skill.yaml` | Definisi skill (persona **AYMAN, ABOO, OOMAR, ALEY, UTZ**, *tools*, templat respons) |

`mcp.enabled` pada YAML diset **`false`** secara default — tidak ada modul MCP bernama `brain.sociometer` di repo. Aktifkan setelah Anda menurunkan gateway sendiri.

**Dokumentasi lengkap:** `docs/KIMI_INTEGRATION_GUIDE.md` · **Brief master (Cursor / SocioMeter):** `docs/BRIEF_SIDIX_SocioMeter.md`.
