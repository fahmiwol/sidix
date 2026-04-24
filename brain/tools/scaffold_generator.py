"""
Scaffold Generator — SIDIX Sprint 8b
Generate struktur folder + file boilerplate untuk berbagai tipe project.

Templates yang tersedia:
  fastapi       — FastAPI app (Python)
  react_ts      — React + TypeScript + Tailwind
  fullstack     — FastAPI backend + React frontend
  landing       — Static landing page HTML/CSS/JS
  extension     — Chrome Extension (MV3)
  nextjs        — Next.js app
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ScaffoldFile:
    path: str          # relative path dari root project
    content: str       # isi file
    description: str = ""


@dataclass
class ScaffoldResult:
    template: str
    project_name: str
    files: list[ScaffoldFile] = field(default_factory=list)
    setup_commands: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "template": self.template,
            "project_name": self.project_name,
            "files": [{"path": f.path, "content": f.content, "description": f.description} for f in self.files],
            "setup_commands": self.setup_commands,
            "notes": self.notes,
        }


# ── Templates ─────────────────────────────────────────────────────────────────

def _fastapi_template(name: str) -> ScaffoldResult:
    result = ScaffoldResult(template="fastapi", project_name=name)
    snake = name.lower().replace("-", "_").replace(" ", "_")

    result.files = [
        ScaffoldFile(
            path="main.py",
            content=f'''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from {snake}.routers import health

app = FastAPI(title="{name}", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)

@app.get("/")
def root():
    return {{"name": "{name}", "status": "ok"}}
''',
            description="Entry point FastAPI",
        ),
        ScaffoldFile(
            path=f"{snake}/__init__.py",
            content="",
        ),
        ScaffoldFile(
            path=f"{snake}/routers/__init__.py",
            content="",
        ),
        ScaffoldFile(
            path=f"{snake}/routers/health.py",
            content=f'''from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check():
    return {{"ok": True, "service": "{name}"}}
''',
            description="Health check endpoint",
        ),
        ScaffoldFile(
            path="requirements.txt",
            content="fastapi>=0.111.0\nuvicorn[standard]>=0.29.0\npython-dotenv>=1.0.0\n",
        ),
        ScaffoldFile(
            path=".env.example",
            content=f"# {name} environment variables\nDEBUG=false\nPORT=8000\n",
        ),
        ScaffoldFile(
            path="Dockerfile",
            content=f'''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
        ),
    ]
    result.setup_commands = [
        "python -m venv venv && source venv/bin/activate",
        "pip install -r requirements.txt",
        "uvicorn main:app --reload",
    ]
    result.notes = ["Endpoint /health sudah tersedia", "Tambah router baru di routers/"]
    return result


def _react_ts_template(name: str) -> ScaffoldResult:
    result = ScaffoldResult(template="react_ts", project_name=name)
    result.files = [
        ScaffoldFile(
            path="package.json",
            content=json.dumps({
                "name": name.lower().replace(" ", "-"),
                "version": "0.1.0",
                "scripts": {"dev": "vite", "build": "tsc && vite build", "preview": "vite preview"},
                "dependencies": {"react": "^18.3.0", "react-dom": "^18.3.0"},
                "devDependencies": {
                    "@types/react": "^18.3.0",
                    "@vitejs/plugin-react": "^4.3.0",
                    "typescript": "^5.4.0",
                    "vite": "^5.4.0",
                    "tailwindcss": "^3.4.0",
                    "autoprefixer": "^10.4.0",
                    "postcss": "^8.4.0",
                },
            }, indent=2),
        ),
        ScaffoldFile(
            path="src/App.tsx",
            content=f'''export default function App() {{
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <h1 className="text-4xl font-bold text-gray-800">{name}</h1>
    </div>
  )
}}
''',
        ),
        ScaffoldFile(
            path="src/main.tsx",
            content='''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
''',
        ),
        ScaffoldFile(path="src/index.css", content="@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"),
        ScaffoldFile(
            path="index.html",
            content=f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name}</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
''',
        ),
        ScaffoldFile(path="tsconfig.json", content=json.dumps({
            "compilerOptions": {"target": "ES2020", "lib": ["ES2020", "DOM"], "module": "ESNext",
                                "moduleResolution": "bundler", "jsx": "react-jsx", "strict": True,
                                "skipLibCheck": True},
            "include": ["src"],
        }, indent=2)),
        ScaffoldFile(path="tailwind.config.js", content='/** @type {import("tailwindcss").Config} */\nexport default { content: ["./index.html", "./src/**/*.{tsx,ts}"], theme: { extend: {} }, plugins: [] }\n'),
        ScaffoldFile(path=".env.example", content=f"VITE_API_URL=http://localhost:8000\n"),
    ]
    result.setup_commands = ["npm install", "npm run dev"]
    result.notes = ["Tailwind CSS sudah dikonfigurasi", "TypeScript strict mode aktif"]
    return result


def _landing_template(name: str) -> ScaffoldResult:
    result = ScaffoldResult(template="landing", project_name=name)
    result.files = [
        ScaffoldFile(
            path="index.html",
            content=f'''<!doctype html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-gray-900">
  <header class="py-6 px-8 flex justify-between items-center border-b">
    <span class="text-2xl font-bold">{name}</span>
    <a href="#contact" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Hubungi Kami</a>
  </header>
  <main>
    <section class="py-24 text-center px-8">
      <h1 class="text-5xl font-bold mb-6">{name}</h1>
      <p class="text-xl text-gray-600 max-w-2xl mx-auto">Deskripsi singkat produk atau layanan kamu.</p>
      <a href="#features" class="mt-8 inline-block px-8 py-3 bg-blue-600 text-white rounded-full text-lg hover:bg-blue-700">Mulai Sekarang</a>
    </section>
    <section id="features" class="py-16 px-8 bg-gray-50">
      <h2 class="text-3xl font-bold text-center mb-12">Fitur Utama</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <div class="p-6 bg-white rounded-xl shadow-sm"><h3 class="font-bold text-xl mb-2">Fitur 1</h3><p class="text-gray-600">Deskripsi fitur pertama.</p></div>
        <div class="p-6 bg-white rounded-xl shadow-sm"><h3 class="font-bold text-xl mb-2">Fitur 2</h3><p class="text-gray-600">Deskripsi fitur kedua.</p></div>
        <div class="p-6 bg-white rounded-xl shadow-sm"><h3 class="font-bold text-xl mb-2">Fitur 3</h3><p class="text-gray-600">Deskripsi fitur ketiga.</p></div>
      </div>
    </section>
  </main>
  <footer id="contact" class="py-8 text-center text-gray-500 border-t">
    <p>&copy; 2026 {name}. All rights reserved.</p>
  </footer>
</body>
</html>
''',
        ),
    ]
    result.setup_commands = ["# Tidak perlu install — buka index.html di browser"]
    result.notes = ["Tailwind via CDN — ganti dengan local install untuk production", "Responsif mobile-first"]
    return result


# ── Registry ──────────────────────────────────────────────────────────────────

_TEMPLATES: dict[str, Any] = {
    "fastapi": _fastapi_template,
    "react_ts": _react_ts_template,
    "landing": _landing_template,
}


def list_templates() -> list[str]:
    return list(_TEMPLATES.keys())


def scaffold(project_name: str, template: str = "fastapi") -> ScaffoldResult:
    """
    Generate scaffold untuk project baru.

    Args:
      project_name — nama project (akan dipakai sebagai folder name, title, dll)
      template     — template yang dipakai (lihat list_templates())

    Returns ScaffoldResult dengan daftar file + setup commands.
    """
    name = (project_name or "my-project").strip()
    fn = _TEMPLATES.get(template.lower())
    if fn is None:
        raise ValueError(
            f"Template '{template}' tidak dikenal. Pilihan: {', '.join(list_templates())}"
        )
    return fn(name)
