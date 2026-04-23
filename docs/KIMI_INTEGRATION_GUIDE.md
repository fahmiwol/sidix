# Panduan jembatan sarang-tamu (nama file historis: `KIMI_INTEGRATION_GUIDE.md`)
## SIDIX-SocioMeter sebagai plugin di host percakapan eksternal

> **Leksikon metafora SIDIX:** *sarang-tamu* = host/orbit percakapan tempat SIDIX dipasang; *meja-arsip* = app desktop MCP; *bengkel-pena* = IDE MCP. Dokumen ini sengaja **tidak** mempromosikan merek pihak ketiga — ikuti path file (`kimi-plugin/`, `.kimi/`) sebagai kontrak teknis repo.

**Versi:** 1.0 | **Status:** INTEGRATION-READY

---

## STATUS HOST (cuplikan sesi)

Dari screenshot yang dikirim:
- ✅ Mode agen host: AKTIF
- ✅ Panel skill: Terlihat (image_tool, web_search, browser, python, dll)
- ✅ Model panas di UI tamu: Running
- ✅ File ZIP SIDIX: sudah di-generate

**Kesimpulan:** Host sarang-tamu siap untuk integrasi.

---

## CARA SIDIX MENJADI PLUGIN DI SARANG-TAMU

### Metode 1: Plugin kustom host (paling tepat)

Host sarang-tamu mendukung **skill/plugin kustom** yang bisa ditambahkan ke mode agen.

#### Langkah integrasi:

**Step 1: Buat manifest plugin**

File: `kimi-plugin/manifest.json`
```json
{
  "name": "SIDIX-SocioMeter",
  "version": "1.0.0",
  "description": "AI Agent berbasis IHOS untuk competitor analysis, creative content, dan self-training",
  "author": "SIDIX Team",
  "icon": "🔷",
  
  "skills": [
    {
      "name": "nasihah_creative",
      "description": "Generate creative content: copywriting, branding, marketing dengan Maqashid filter",
      "parameters": {
        "brief": {"type": "string", "required": true, "description": "Deskripsi tugas kreatif"},
        "persona": {"type": "string", "enum": ["AYMAN", "UTZ", "ABOO"], "default": "AYMAN"}
      }
    },
    {
      "name": "nasihah_analyze",
      "description": "Analyze data: competitor, market, trends dengan Sanad chain",
      "parameters": {
        "data": {"type": "string", "required": true},
        "analysis_type": {"type": "string", "enum": ["competitor", "market", "trends"], "default": "competitor"}
      }
    },
    {
      "name": "nasihah_design",
      "description": "Generate visual content: images, thumbnails, logos",
      "parameters": {
        "prompt": {"type": "string", "required": true},
        "format": {"type": "string", "enum": ["image", "thumbnail", "logo"], "default": "image"}
      }
    },
    {
      "name": "nasihah_code",
      "description": "Generate code dengan dokumentasi dan test cases",
      "parameters": {
        "task": {"type": "string", "required": true},
        "language": {"type": "string", "default": "python"}
      }
    },
    {
      "name": "maqashid_check",
      "description": "Evaluasi content dengan Maqashid filter (CREATIVE/ACADEMIC/IJTIHAD/GENERAL)",
      "parameters": {
        "content": {"type": "string", "required": true},
        "mode": {"type": "string", "enum": ["CREATIVE", "ACADEMIC", "IJTIHAD", "GENERAL"], "required": true}
      }
    },
    {
      "name": "typo_normalize",
      "description": "Normalize text dengan typo correction dan singkatan expansion",
      "parameters": {
        "text": {"type": "string", "required": true}
      }
    }
  ],
  
  "endpoints": {
    "primary": {
      "type": "mcp",
      "url": "http://localhost:8765/mcp",
      "transport": "streamable-http"
    },
    "fallback": {
      "type": "http",
      "url": "http://localhost:8765/api/v1",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }
}
```

---

### Metode 2: MCP Direct Connection (Recommended)

Host sarang-tamu mendukung MCP (Model Context Protocol) — pola yang sama dipakai meja-arsip, bengkel-pena, dan klien MCP lain.

#### Berkas konfigurasi (folder `.kimi/`):

File: `~/.config/kimi/mcp.json`
```json
{
  "mcpServers": {
    "sidix-sociometer": {
      "command": "python",
      "args": ["-m", "brain.sociometer.mcp_server"],
      "env": {
        "SIDIX_API_URL": "http://localhost:8765",
        "SIDIX_MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

#### Cara memuat di host:
1. Buka pengaturan host → Plugins/MCP
2. Klik "Add MCP Server"
3. Paste config di atas
4. Klik "Connect"
5. SIDIX akan muncul di panel skill host

---

### Metode 3: Webhook/API Integration

Kalau MCP belum fully supported, gunakan HTTP API langsung:

#### Action kustom (HTTP):

```python
# kimi-plugin/sidix_action.py
"""
SIDIX Action untuk mode agen host.
Dipanggil saat user mention @SIDIX atau trigger keyword.
"""

import requests
import json

SIDIX_API_URL = "http://localhost:8765/api/v1"

class SIDIXAction:
    """Action wrapper host → SIDIX."""
    
    def __init__(self):
        self.base_url = SIDIX_API_URL
        self.available_tools = [
            "nasihah_creative",
            "nasihah_analyze", 
            "nasihah_design",
            "nasihah_code",
            "nasihah_raudah",
            "nasihah_learn",
            "maqashid_check",
            "typo_normalize"
        ]
    
    async def handle(self, user_input: str, context: dict) -> dict:
        """
        Handle user input dari host sarang-tamu.
        
        Flow:
        1. Detect if user wants SIDIX
        2. Route to appropriate tool
        3. Return formatted response
        """
        
        # Check if SIDIX is requested
        if not self._is_sidix_request(user_input):
            return None  # Biarkan host tangani bila perlu
        
        # Normalize input (typo correction)
        normalized = await self._normalize(user_input)
        
        # Detect intent
        intent = self._detect_intent(normalized)
        
        # Route to tool
        if intent["tool"] in self.available_tools:
            result = await self._call_sidix(intent["tool"], intent["params"])
            return self._format_response(result, intent["tool"])
        
        return None
    
    def _is_sidix_request(self, text: str) -> bool:
        """Detect if user is requesting SIDIX."""
        triggers = [
            "@sidix", "@sociometer", "@SIDIX",
            "sidix tolong", "sociometer tolong",
            "pake sidix", "gunakan sidix",
            "sidix:", "sociometer:",
            "[SIDIX]", "[Sociometer]",
            "maqashid", "naskh", "raudah",
            "nasihah", "jariyah", "tafsir"
        ]
        return any(trigger in text.lower() for trigger in triggers)
    
    async def _normalize(self, text: str) -> str:
        """Normalize text via SIDIX typo normalizer."""
        try:
            response = requests.post(
                f"{self.base_url}/sociometer/typo/normalize",
                json={"text": text},
                timeout=5
            )
            return response.json().get("normalized", text)
        except:
            return text  # Fallback to original
    
    def _detect_intent(self, text: str) -> dict:
        """Detect intent from normalized text."""
        
        # Creative content
        if any(kw in text for kw in ["buatkan", "copywriting", "branding", "marketing", "iklan", "caption"]):
            return {"tool": "nasihah_creative", "params": {"brief": text, "persona": "AYMAN"}}
        
        # Analysis
        elif any(kw in text for kw in ["analisis", "analisa", "competitor", "tren", "market"]):
            return {"tool": "nasihah_analyze", "params": {"data": text, "analysis_type": "competitor"}}
        
        # Design
        elif any(kw in text for kw in ["gambar", "design", "logo", "thumbnail", "visual"]):
            return {"tool": "nasihah_design", "params": {"prompt": text, "format": "image"}}
        
        # Code
        elif any(kw in text for kw in ["code", "kode", "script", "program", "function"]):
            return {"tool": "nasihah_code", "params": {"task": text, "language": "python"}}
        
        # Multi-agent
        elif any(kw in text for kw in ["kompleks", "multi", "raudah", "collaborate"]):
            return {"tool": "nasihah_raudah", "params": {"task": text}}
        
        # Learning
        elif any(kw in text for kw in ["ajarin", "jelaskan", "teach", "belajar", "tutorial"]):
            return {"tool": "nasihah_learn", "params": {"topic": text, "level": "beginner"}}
        
        # Maqashid check
        elif any(kw in text for kw in ["maqashid", "check", "evaluasi", "filter"]):
            return {"tool": "maqashid_check", "params": {"content": text, "mode": "CREATIVE"}}
        
        # Default
        else:
            return {"tool": "nasihah_creative", "params": {"brief": text, "persona": "UTZ"}}
    
    async def _call_sidix(self, tool: str, params: dict) -> dict:
        """Call SIDIX tool via API."""
        try:
            response = requests.post(
                f"{self.base_url}/sociometer/tools/{tool}",
                json=params,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {
                "error": True,
                "message": f"SIDIX connection error: {str(e)}",
                "suggestion": "Pastikan SIDIX backend berjalan di localhost:8765"
            }
    
    def _format_response(self, result: dict, tool: str) -> dict:
        """Format respons SIDIX untuk UI host."""
        
        if result.get("error"):
            return {
                "type": "error",
                "content": result["message"],
                "suggestion": result.get("suggestion", "")
            }
        
        # Format based on tool
        formatters = {
            "nasihah_creative": self._format_creative,
            "nasihah_analyze": self._format_analyze,
            "nasihah_design": self._format_design,
            "nasihah_code": self._format_code,
            "nasihah_raudah": self._format_raudah,
            "nasihah_learn": self._format_learn,
            "maqashid_check": self._format_maqashid,
        }
        
        formatter = formatters.get(tool, self._format_default)
        return formatter(result)
    
    def _format_creative(self, result: dict) -> dict:
        return {
            "type": "creative",
            "title": "✨ Hasil Kreatif SIDIX",
            "content": result.get("output", ""),
            "persona": result.get("persona_used", "AYMAN"),
            "cqf_score": result.get("cqf_score", 0),
            "maqashid": result.get("maqashid_mode", "CREATIVE"),
            "sanad": result.get("sanad_chain", [])
        }
    
    def _format_analyze(self, result: dict) -> dict:
        return {
            "type": "analysis",
            "title": "📊 Analisis SIDIX",
            "content": result.get("output", ""),
            "analysis_type": result.get("analysis_type", "general"),
            "confidence": result.get("cqf_score", 0)
        }
    
    def _format_design(self, result: dict) -> dict:
        return {
            "type": "design",
            "title": "🎨 Desain Visual",
            "content": result.get("output", ""),
            "format": result.get("format", "image"),
            "url": result.get("url", "")
        }
    
    def _format_code(self, result: dict) -> dict:
        return {
            "type": "code",
            "title": "💻 Kode Generate",
            "content": result.get("code", ""),
            "language": result.get("language", "python"),
            "tests": result.get("tests", "")
        }
    
    def _format_raudah(self, result: dict) -> dict:
        return {
            "type": "multi_agent",
            "title": "🤝 Kolaborasi Multi-Agent",
            "content": result.get("result", ""),
            "agents": result.get("agents", []),
            "time_ms": result.get("total_time_ms", 0)
        }
    
    def _format_learn(self, result: dict) -> dict:
        return {
            "type": "education",
            "title": "📚 Materi Pembelajaran",
            "content": result.get("content", ""),
            "topic": result.get("topic", ""),
            "level": result.get("level", "beginner")
        }
    
    def _format_maqashid(self, result: dict) -> dict:
        return {
            "type": "evaluation",
            "title": "⚖️ Evaluasi Maqashid",
            "content": result.get("tagged_output", ""),
            "scores": result.get("scores", {}),
            "passed": result.get("passed", False)
        }
    
    def _format_default(self, result: dict) -> dict:
        return {
            "type": "general",
            "title": "🔷 SIDIX Response",
            "content": result.get("output", str(result)),
            "raw": result
        }


# Registrasi action host
HOST_ACTION = SIDIXAction()
```

---

## METODE 4: SIDIX sebagai skill host (paling sederhana)

Jika host punya sistem skill kustom seperti di screenshot (image_tool, web_search, browser, python):

### Register SIDIX sebagai Skill:

**File: `kimi-plugin/sidix_skill.py`**

```python
"""
SIDIX Skill untuk mode agen host.
Register sebagai skill di panel skill host.
"""

from kimi.skills import Skill, SkillContext

class SIDIXSkill(Skill):
    """SIDIX-SocioMeter Skill untuk host sarang-tamu."""
    
    name = "sidix"
    description = "AI Agent berbasis IHOS untuk creative, analysis, dan self-training"
    icon = "🔷"
    
    async def run(self, ctx: SkillContext, query: str) -> str:
        """
        Entry point untuk SIDIX skill.
        Dipanggil saat user ketik: /sidix <query>
        """
        
        # 1. Normalize input (typo correction)
        normalized = await self._normalize(ctx, query)
        
        # 2. Route ke tool yang sesuai
        tool_result = await self._route(ctx, normalized)
        
        # 3. Format output
        return self._format(tool_result)
    
    async def _normalize(self, ctx: SkillContext, text: str) -> str:
        """Normalize typo dan singkatan."""
        # Call SIDIX typo normalizer
        result = await ctx.http.post(
            "http://localhost:8765/api/v1/sociometer/typo/normalize",
            json={"text": text}
        )
        return result.get("normalized", text)
    
    async def _route(self, ctx: SkillContext, query: str) -> dict:
        """Route ke tool SIDIX."""
        
        # Detect intent
        if "buat" in query or "copy" in query:
            tool = "nasihah_creative"
            params = {"brief": query, "persona": "AYMAN"}
        elif "analisis" in query or "analisa" in query:
            tool = "nasihah_analyze"
            params = {"data": query}
        else:
            tool = "nasihah_creative"
            params = {"brief": query, "persona": "UTZ"}
        
        # Call SIDIX
        result = await ctx.http.post(
            f"http://localhost:8765/api/v1/sociometer/tools/{tool}",
            json=params
        )
        
        return result
    
    def _format(self, result: dict) -> str:
        """Format hasil untuk ditampilkan di UI host."""
        output = result.get("output", "Maaf, terjadi kesalahan.")
        
        # Add metadata
        metadata = []
        if "cqf_score" in result:
            metadata.append(f"📊 CQF: {result['cqf_score']:.1f}")
        if "persona_used" in result:
            metadata.append(f"🎭 Persona: {result['persona_used']}")
        if "maqashid_mode" in result:
            metadata.append(f"⚖️ Maqashid: {result['maqashid_mode']}")
        
        footer = "\n".join(metadata) if metadata else ""
        
        return f"{output}\n\n---\n{footer}"


# Register skill
SKILL = SIDIXSkill()
```

---

## CARA USER PAKAI SIDIX DI KIMI

Setelah integrasi selesai, user bisa:

### Method 1: Command
```
/sidix buatkan copywriting untuk kopi lokal
```

### Method 2: Mention
```
@SIDIX analisis competitor @nike di instagram
```

### Method 3: Trigger Keyword
```
SIDIX: jelaskan Maqashid mode
```

### Method 4: Context Menu (Right Click)
- Select text → Right Click → "Analyze with SIDIX"
- Select text → Right Click → "Generate with SIDIX"

---

## FORMAT RESPONS DI UI HOST

### Contoh respons

**Input:**
```
/sidix buatkan caption instagram untuk produk kopi lokal
```

**Output host:**
```markdown
✨ **Hasil Kreatif SIDIX** (Persona: AYMAN)

☕ Caption Instagram — Kopi Lokal

"Dari petani lokal ke cangkirmu. 
Setiap teguk adalah dukungan untuk 1.000+ petani kopi Indonesia. 

🌱 100% Arabika Indonesia
👨‍🌾 Fair trade untuk petani
☕ Roast fresh setiap hari

Tag temanmu yang butuh kopi berkualitas! 👇

#KopiLokal #KopiIndonesia #SupportLocal #KopiNusantara #FairTrade"

---
📊 CQF: 8.7/10 | ⚖️ Maqashid: CREATIVE | 📎 Sanad: [user_request]
```

---

## INTEGRATION CHECKLIST

| Step | Task | Status |
|------|------|--------|
| 1 | SIDIX backend running di localhost:8765 | ⬜ |
| 2 | MCP server configured | ⬜ |
| 3 | Manifest plugin (`kimi-plugin/`) dibuat | ⬜ |
| 4 | Berkas MCP host diperbarui | ⬜ |
| 5 | Test connection | ⬜ |
| 6 | Verify typo normalization works | ⬜ |
| 7 | Document untuk user | ⬜ |

---

## TROUBLESHOOTING

### Problem: Host tidak bisa connect ke SIDIX
**Check:**
```bash
# 1. SIDIX backend running?
curl http://localhost:8765/health

# 2. MCP server accessible?
curl http://localhost:8765/mcp/health

# 3. Firewall blocking?
sudo ufw allow 8765/tcp

# 4. Path konfigurasi MCP host benar? (sesuai dokumentasi host; contoh folder `.kimi/`)
cat path/ke/mcp.json
```

### Problem: Typo tidak ter-normalize
**Check:**
```bash
# Test normalizer directly
curl -X POST http://localhost:8765/api/v1/sociometer/typo/normalize \
  -H "Content-Type: application/json" \
  -d '{"text": "gmana cra stp gpu"}'
```

### Problem: Response lambat
**Solusi:**
- Gunakan GPU (cloud atau local)
- Reduce batch size
- Enable response caching
- Use streaming response

---

*SIDIX di sarang-tamu = agen yang mengerti typo, punya sanad chain, dan Maqashid filter — di antarmuka obrolan yang sudah Anda pakai.*
