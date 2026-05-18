# SIDIX Built-in Apps Spec — Canvas, Studio & Artifact System
**Version:** 1.0  
**Status:** Spec Approved for Implementation  
**Date:** 2026-05-07  
**Adopted from:** ChatGPT Canvas + Claude Artifacts + Kimi Visual Agent

---

## 1. VISION

SIDIX tidak hanya chat — setiap output adalah **live app** yang bisa user interact, edit, dan export.  
ChatGPT punya Canvas (document editor). Claude punya Artifacts (live preview). Kimi punya visual agent.  
SIDIX akan punya **Studio System** — unified renderer untuk semua output type.

**Prinsip:**
- Every output is an artifact — bisa di-preview, di-edit, di-share
- App muncul di sidebar kanan (split-pane) — chat di kiri, app di kanan
- User bisa "pin" app → tetap terbuka saat chat berlanjut
- App bisa di-export (download, share link, embed)

---

## 2. APP REGISTRY

```python
APP_REGISTRY = {
    "text": {
        "renderer": "TextRenderer",
        "interactive": False,
        "export_formats": ["txt", "md"],
        "status": "LIVE"
    },
    "code": {
        "renderer": "CodeCanvas",
        "interactive": True,  # run, edit, debug
        "export_formats": ["py", "js", "html", "zip"],
        "status": "SPEC"
    },
    "image_prompt": {
        "renderer": "ImageStudio",
        "interactive": True,  # generate, edit, gallery
        "export_formats": ["png", "jpg", "webp"],
        "status": "SPEC"
    },
    "html": {
        "renderer": "WebPreview",
        "interactive": True,  # live preview, inspect
        "export_formats": ["html", "zip"],
        "status": "SPEC"
    },
    "structured": {
        "renderer": "DataNotebook",
        "interactive": True,  # sort, filter, chart
        "export_formats": ["csv", "json", "xlsx"],
        "status": "SPEC"
    },
    "document": {
        "renderer": "DocumentStudio",
        "interactive": True,  # rich text editor
        "export_formats": ["md", "pdf", "docx"],
        "status": "SPEC"
    },
    "audio_tts": {
        "renderer": "AudioPlayer",
        "interactive": True,  # play, pause, download
        "export_formats": ["wav", "mp3"],
        "status": "SPEC"
    },
    "video_storyboard": {
        "renderer": "StoryboardStudio",
        "interactive": True,  # scene editor, preview
        "export_formats": ["mp4", "zip"],
        "status": "SPEC"
    },
    "3d_prompt": {
        "renderer": "ThreeDViewer",
        "interactive": True,  # rotate, zoom, export
        "export_formats": ["obj", "gltf", "usd"],
        "status": "SPEC"
    }
}
```

---

## 3. APP DETAIL SPEC

### App 1: Code Canvas 💻

**Inspirasi:** ChatGPT Canvas (code editing) + Claude Artifacts (live preview)

**Layout:**
```
┌────────────────────────┬────────────────────────┐
│  Chat (kiri)           │  Code Canvas (kanan)   │
│                        │                        │
│  User: "Buatkan        │  ┌──────────────────┐  │
│  kalkulator BMI"       │  │ 1  def bmi(...):  │  │
│                        │  │ 2      ...        │  │
│  SIDIX: "Berikut..."   │  │ 3      ...        │  │
│                        │  └──────────────────┘  │
│                        │  [Run] [Debug] [Copy]  │
│                        │  ┌──────────────────┐  │
│                        │  │ Output: 24.5     │  │
│                        │  │ Normal           │  │
│                        │  └──────────────────┘  │
└────────────────────────┴────────────────────────┘
```

**Features:**
- Syntax highlighting (Monaco Editor atau CodeMirror)
- Run button → execute di `code_sandbox` backend
- Debug button → auto-detect error → suggest fix
- Copy / Download / Share
- Multi-file support (tabbed editor)
- Diff view (compare version)

**Backend:**
- `POST /app/code/run` → `code_sandbox` execution
- `POST /app/code/debug` → error analysis + fix suggestion
- `GET /app/code/history/{artifact_id}` → version history

---

### App 2: Document Studio 📝

**Inspirasi:** ChatGPT Canvas (document editing)

**Layout:**
- Rich text editor (TipTap / Slate.js)
- Markdown native — WYSIWYG optional
- Sidebar: outline/TOC
- Toolbar: bold, italic, heading, list, table, quote, code block

**Features:**
- Collaborative editing (future)
- Export: PDF, DOCX, Markdown
- Template library (report, proposal, letter)
- Sanad citation insertion (`[@source_id]`)
- Maqashid compliance checker

---

### App 3: Image Studio 🎨

**Inspirasi:** DALL-E interface + Midjourney gallery

**Layout:**
- Prompt input (with enhancement suggestions)
- Gallery grid (2×2 atau 3×3)
- Editor panel (crop, upscale, variant)
- History sidebar

**Features:**
- Generate: prompt → FLUX/SDXL → 4 variants
- Edit: inpaint, outpaint, style transfer
- Gallery: save, organize, export
- Prompt library (saved prompts)

**Backend:**
- `POST /app/image/generate` → queue → GPU server
- `POST /app/image/edit` → inpaint/outpaint
- `GET /app/image/gallery` → user's image history

---

### App 4: Web Preview 🌐

**Inspirasi:** Claude Artifacts (HTML live preview)

**Layout:**
- Split: code (HTML/CSS/JS) di atas, preview di bawah
- Fullscreen preview mode
- Console output panel
- Device simulator (mobile/tablet/desktop)

**Features:**
- Live reload saat code berubah
- Console log capture
- Export sebagai ZIP (single-file HTML)
- Share link (hosted static)

**Security:**
- Iframe sandbox (no network, no cookies)
- CSP strict
- No external resource fetch

---

### App 5: Data Notebook 📊

**Inspirasi:** ChatGPT Code Interpreter (CSV analysis)

**Layout:**
- Upload area (drag & drop CSV/Excel/JSON)
- Data table view (sortable, filterable)
- Chart gallery (bar, line, pie, scatter)
- Analysis panel (stats, correlation)

**Features:**
- Auto-detect data type
- Generate chart dari natural language
- Statistical analysis (mean, median, correlation)
- Export chart sebagai PNG/SVG
- SQL-like query (natural language → pandas)

---

### App 6: Audio Player 🔊

**Layout:**
- Waveform visualization
- Play/pause/stop controls
- Speed control (0.5x–2x)
- Download button
- Voice selector (5 persona voices)

**Features:**
- Streaming playback
- Voice cloning (future — XTTS)
- Playlist (multi-paragraph TTS)

---

## 4. ARTIFACT LIFECYCLE

```
1. DETECTION
   OutputTypeDetector → detect type dari query + response
   
2. GENERATION
   LLM generates content → structured artifact JSON
   
3. RENDER
   Frontend AppRenderer → load appropriate component
   
4. INTERACTION
   User edits / runs / exports → events ke backend
   
5. PERSISTENCE
   Artifact disimpan ke project/chat history
   
6. SHARING (optional)
   Generate share link / embed code
```

**Artifact JSON schema:**
```json
{
  "artifact_id": "art_xxx",
  "type": "code",
  "title": "Kalkulator BMI",
  "content": "def bmi(...): ...",
  "language": "python",
  "metadata": {
    "created_at": "2026-05-07T10:00:00Z",
    "model_used": "qwen2.5-7b",
    "mode": "thinking",
    "sanad_score": 8.5
  },
  "versions": [
    {"version": 1, "content": "...", "timestamp": "..."}
  ]
}
```

---

## 5. UI IMPLEMENTATION PLAN

### Phase 1: MVP (Sprint ini — 2026-05-07)
- Text renderer (sudah ada)
- Code Canvas: syntax highlight + run button
- Document Studio: markdown preview

### Phase 2: Enhancement (2026-05-15)
- Image Studio: generate + gallery
- Web Preview: HTML live preview
- Data Notebook: CSV upload + chart

### Phase 3: Polish (2026-06-01)
- Audio Player: TTS playback
- Video Storyboard: scene editor
- 3D Viewer: mesh preview

### Phase 4: Advanced (2026-07-01)
- Collaborative editing
- App marketplace (user-created apps)
- Embed/sharing system

---

## 6. TECH STACK

| Component | Library | Note |
|---|---|---|
| Code Editor | Monaco Editor (VS Code) | Heavy but full-featured |
| Rich Text | TipTap / Milkdown | Markdown-native |
| Charts | Apache ECharts | Free, powerful |
| Image Viewer | Lightbox2 | Simple, effective |
| Audio | Web Audio API | Native |
| Data Table | AG Grid Community | Free tier cukup |

---

*Document version: 1.0 | Adopted from ChatGPT Canvas + Claude Artifacts | Author: Claude Code*