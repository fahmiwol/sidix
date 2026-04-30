"""
project_archetypes.py — Katalog archetype proyek nyata dari ekosistem Tiranyx/SIDIX.

Archetype dihasilkan dari scan D:\\Projects (2026-04-18):
  tiranyx, Galantara, bank-tiranyx, Omnyx, Shopee-API-Gateway,
  Mighan-Building-Dashboard, AGENT-HUB, raddict, dll.

Dipakai SIDIX untuk membantu user memulai proyek baru dengan pola yang sudah terbukti.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Katalog Archetype
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, dict] = {

    # 1 ─── Next.js Full-Stack (App Router + Prisma)
    "nextjs_fullstack": {
        "description": (
            "Web app full-stack dengan Next.js 14 App Router, TypeScript, Prisma ORM, "
            "dan SQLite/PostgreSQL. Cocok untuk CMS, dashboard admin, dan SaaS ringan."
        ),
        "stack": ["Next.js 14", "TypeScript", "Prisma", "SQLite/PostgreSQL", "TailwindCSS"],
        "real_project": "tiranyx-web (tiranyx.co.id)",
        "structure": {
            "app/": "Route segments (App Router)",
            "app/api/": "API Route handlers",
            "app/(site)/": "Public routes",
            "app/admin/(protected)/": "Protected admin routes",
            "components/": "Shared React components",
            "lib/": "Utility + Prisma client",
            "prisma/schema.prisma": "Skema database",
            "public/": "Aset statis",
        },
        "setup_steps": [
            "npx create-next-app@latest --typescript --tailwind --app",
            "npm install prisma @prisma/client",
            "npx prisma init",
            "Tulis schema.prisma → npx prisma migrate dev",
            "Buat lib/prisma.ts (singleton client)",
            "Set up middleware.ts untuk auth guard",
        ],
        "env_vars": ["DATABASE_URL", "NEXTAUTH_SECRET", "NEXTAUTH_URL"],
        "deploy": "Vercel / VPS via 'next build && next start'",
    },

    # 2 ─── Three.js Static Game + Socket.io Multiplayer
    "threejs_game_multiplayer": {
        "description": (
            "Game/simulasi 3D di browser dengan Three.js (ES modules), "
            "dikombinasikan dengan server multiplayer Socket.io + Express. "
            "Cocok untuk game sosial, metaverse mini, world simulation."
        ),
        "stack": ["Three.js", "JavaScript (ES Modules)", "Socket.io 4.x", "Express 4.x", "Node.js ≥18"],
        "real_project": "Galantara (galantara.io) — social-commerce semi-3D platform",
        "structure": {
            "index.html": "Entry point game",
            "main.js": "Bootstrap Three.js scene",
            "core/": "Scene, camera, renderer",
            "world/": "Map, terrain, environment",
            "entities/": "Player, NPC, item",
            "ui/": "HUD, menu, overlay",
            "multiplayer/": "Socket.io client",
            "galantara-server/": "Server multiplayer (Express + Socket.io)",
            "galantara-server/index.js": "Entry point server",
        },
        "setup_steps": [
            "Buat index.html dengan <script type='module' src='main.js'>",
            "npm init di folder server → npm install express socket.io",
            "Set up Socket.io room management di server",
            "Gunakan Three.js CDN atau npm + bundler (Vite)",
            "Deploy static ke CDN/VPS; server ke PM2 atau Railway",
        ],
        "env_vars": ["PORT", "CORS_ORIGIN"],
        "deploy": "Static: aaPanel / Nginx; Server: PM2 di VPS",
    },

    # 3 ─── Fastify + Prisma + PostgreSQL (API Backend)
    "fastify_prisma_api": {
        "description": (
            "REST API backend ringan dengan Fastify, Prisma ORM, PostgreSQL. "
            "Cocok untuk ledger/wallet system, transaksi koin, atau layanan keuangan."
        ),
        "stack": ["Fastify", "TypeScript", "Prisma", "PostgreSQL", "Node.js ≥18"],
        "real_project": "bank-tiranyx (Mighan Ledger Vault)",
        "structure": {
            "src/": "Source code utama",
            "src/modules/": "Modul fungsional (mint, wallet, transfer, ledger)",
            "src/lib/": "Utility (crypto, helpers)",
            "src/config/": "Konstanta + konfigurasi",
            "src/data/": "Data statis (JSON)",
            "prisma/schema.prisma": "Skema database",
            ".env.example": "Template env vars",
            "package.json": "Dependencies",
        },
        "setup_steps": [
            "npm init -y && npm install fastify @prisma/client",
            "npm install -D prisma typescript @types/node ts-node",
            "npx prisma init --datasource-provider postgresql",
            "Tulis schema.prisma → npx prisma migrate dev",
            "Buat src/app.ts (Fastify instance)",
            "Register plugin fastify-cors, fastify-helmet",
        ],
        "env_vars": ["DATABASE_URL", "PORT", "JWT_SECRET"],
        "deploy": "PM2 di VPS atau Railway",
    },

    # 4 ─── Hono Edge API + Prisma (OAuth Proxy / Gateway)
    "hono_edge_api": {
        "description": (
            "API gateway atau OAuth proxy berbasis Hono (edge-ready TypeScript framework). "
            "Sangat cepat untuk Cloudflare Workers atau Node. "
            "Cocok untuk proxy ke 3rd-party API (Shopee, marketplace)."
        ),
        "stack": ["Hono", "TypeScript", "Prisma", "PostgreSQL", "HMAC-SHA256"],
        "real_project": "Shopee-API-Gateway — OAuth proxy ke Shopee Open Platform",
        "structure": {
            "src/": "Source code",
            "src/routes/": "Endpoint definitions",
            "src/middleware/": "Auth, logging, rate-limit",
            "src/lib/": "Crypto helpers (HMAC), token manager",
            "prisma/schema.prisma": "Token storage",
            ".env.example": "Template env vars",
        },
        "setup_steps": [
            "npm create hono@latest myapp",
            "npm install @prisma/client && npm install -D prisma",
            "Implementasi OAuth flow: generate URL → handle callback → store token",
            "Buat HMAC-SHA256 signer untuk setiap request ke 3rd-party",
            "Tambah queue/retry untuk rate limit handling",
        ],
        "env_vars": [
            "DATABASE_URL", "PORT", "PARTNER_ID", "PARTNER_KEY",
            "REDIRECT_URI", "SHOPEE_BASE_URL",
        ],
        "deploy": "Cloudflare Workers atau PM2 VPS",
    },

    # 5 ─── Python Flask + HTML5 Canvas (Data Dashboard)
    "flask_canvas_dashboard": {
        "description": (
            "Dashboard visual berbasis Python Flask sebagai backend, "
            "HTML5 Canvas + JavaScript sebagai UI. Cocok untuk pipeline operasional, "
            "microstock tracker, atau monitoring berbasis metafora visual."
        ),
        "stack": ["Python Flask ≥3.0", "Pillow", "HTML5 Canvas", "JavaScript", "SQLite/PostgreSQL"],
        "real_project": "Mighan-Building-Dashboard — Adobe Stock pipeline dashboard",
        "structure": {
            "app.py": "Flask application entry point",
            "templates/": "Jinja2 HTML templates",
            "static/": "JS, CSS, images",
            "static/canvas/": "Canvas game/dashboard logic",
            "data/": "Data files (JSON, CSV, SQLite)",
            "requirements.txt": "Python dependencies",
            "config.json": "App configuration",
        },
        "setup_steps": [
            "python -m venv .venv && .venv/Scripts/activate",
            "pip install flask pillow",
            "Buat app.py dengan Flask(__name__)",
            "Buat templates/index.html dengan <canvas> element",
            "Hubungkan Flask API endpoint ke canvas JS via fetch()",
            "Tambahkan SQLite dengan sqlite3 atau SQLAlchemy",
        ],
        "env_vars": ["FLASK_ENV", "SECRET_KEY", "DATABASE_URL"],
        "deploy": "Gunicorn + Nginx atau python app.py (dev)",
    },

    # 6 ─── NestJS + Next.js (SaaS Platform)
    "nestjs_nextjs_saas": {
        "description": (
            "Platform SaaS dengan NestJS sebagai backend API (TypeScript, modular) "
            "dan Next.js sebagai dashboard frontend. Cocok untuk chatbot platform, "
            "multi-tenant SaaS, omnichannel communication tool."
        ),
        "stack": ["NestJS", "TypeScript", "Next.js", "PostgreSQL", "Prisma", "JWT", "Socket.io"],
        "real_project": "Omnyx — platform chatbot omnichannel (WhatsApp dll)",
        "structure": {
            "backend/": "NestJS app",
            "backend/src/modules/": "Modul NestJS (auth, workspace, inbox, bot)",
            "backend/src/common/": "Guards, interceptors, pipes",
            "backend/prisma/": "Skema database",
            "frontend/": "Next.js dashboard",
            "frontend/app/": "App Router pages",
            "frontend/components/": "UI components",
            ".env.example": "Shared env template",
        },
        "setup_steps": [
            "npm install -g @nestjs/cli && nest new backend",
            "npx create-next-app@latest frontend --typescript --tailwind --app",
            "nest generate module auth && nest generate module workspace",
            "Integrasi Prisma: npm install @prisma/client prisma",
            "Setup JWT guard dengan @nestjs/jwt + passport",
            "Hubungkan Next.js ke NestJS via env NEXT_PUBLIC_API_URL",
        ],
        "env_vars": [
            "DATABASE_URL", "JWT_SECRET", "WHATSAPP_API_KEY",
            "NEXT_PUBLIC_API_URL", "PORT",
        ],
        "deploy": "Backend: PM2 / Railway; Frontend: Vercel",
    },

    # 7 ─── Python FastAPI + BM25 RAG (AI Backend)
    "fastapi_rag_ai": {
        "description": (
            "Backend AI berbasis Python FastAPI dengan BM25 retrieval, "
            "lokal LLM inference (Ollama), dan corpus management. "
            "Own-stack, zero vendor API. Cocok untuk knowledge assistant, QA system."
        ),
        "stack": ["Python FastAPI", "BM25 (rank_bm25)", "Ollama", "SQLite", "Pydantic"],
        "real_project": "SIDIX / Mighan Model — brain_qa",
        "structure": {
            "brain_qa/": "Python package",
            "brain_qa/serve.py": "FastAPI app + endpoint",
            "brain_qa/query.py": "BM25 query logic",
            "brain_qa/indexer.py": "Corpus indexing",
            "brain_qa/storage.py": "Data persistence",
            "brain_qa/local_llm.py": "LLM inference wrapper",
            "brain/public/": "Corpus knowledge base",
            ".data/": "Runtime data (index, cache)",
        },
        "setup_steps": [
            "poetry new myapp || pip install fastapi uvicorn rank-bm25 pydantic",
            "Buat corpus di brain/public/ (markdown files)",
            "Implement indexer.py: load markdown → tokenize → BM25Index",
            "Implement query.py: query → BM25 top-k → LLM answer",
            "Buat serve.py: FastAPI + /qa endpoint",
            "Test: python -m brain_qa serve → port 8765",
        ],
        "env_vars": ["OLLAMA_BASE_URL", "MODEL_NAME", "CORPUS_PATH", "PORT"],
        "deploy": "python -m uvicorn serve:app --port 8765 atau PM2",
    },

    # 8 ─── Vite + React + TypeScript (Frontend SPA)
    "vite_react_ts": {
        "description": (
            "Frontend SPA modern dengan Vite + React + TypeScript + TailwindCSS. "
            "Cocok untuk dashboard, user interface AI, atau aplikasi web interaktif. "
            "Deploy sebagai static site atau serve dari VPS."
        ),
        "stack": ["Vite", "React", "TypeScript", "TailwindCSS", "Zustand/Context API"],
        "real_project": "SIDIX_USER_UI — antarmuka user SIDIX AI",
        "structure": {
            "src/": "Source code",
            "src/components/": "React components",
            "src/pages/": "Route pages",
            "src/hooks/": "Custom hooks",
            "src/store/": "State management",
            "src/lib/": "API client, helpers",
            "public/": "Aset statis",
            "index.html": "Entry HTML",
            "vite.config.ts": "Vite configuration",
        },
        "setup_steps": [
            "npm create vite@latest myapp -- --template react-ts",
            "cd myapp && npm install",
            "npm install -D tailwindcss postcss autoprefixer",
            "npx tailwindcss init -p",
            "npm install zustand react-router-dom",
            "npm run build → dist/ untuk deploy",
        ],
        "env_vars": ["VITE_API_URL", "VITE_APP_NAME"],
        "deploy": "serve dist -p 4000 (VPS) atau Vercel/Netlify",
    },
}

# ---------------------------------------------------------------------------
# Fungsi publik
# ---------------------------------------------------------------------------


def list_archetypes() -> list[str]:
    """Kembalikan daftar nama semua archetype yang tersedia."""
    return list(ARCHETYPES.keys())


def get_archetype(name: str) -> dict:
    """
    Kembalikan detail archetype berdasarkan nama.
    Raise KeyError jika tidak ditemukan.
    """
    if name not in ARCHETYPES:
        available = ", ".join(ARCHETYPES.keys())
        raise KeyError(
            f"Archetype '{name}' tidak ditemukan. "
            f"Pilihan yang tersedia: {available}"
        )
    return ARCHETYPES[name]


def suggest_archetype(description: str) -> str:
    """
    Sarankan archetype yang paling cocok berdasarkan deskripsi proyek (keyword matching).

    Args:
        description: Deskripsi proyek dalam bahasa natural (Indonesia/Inggris).

    Returns:
        Nama archetype yang paling relevan.
    """
    description_lower = description.lower()

    # Mapping keyword → archetype (urutan penting: lebih spesifik dulu)
    keyword_map: list[tuple[list[str], str]] = [
        # Game / 3D / multiplayer
        (["three.js", "threejs", "game", "3d", "multiplayer", "metaverse", "world", "socket.io"], "threejs_game_multiplayer"),
        # AI / RAG / knowledge base
        (["rag", "retrieval", "knowledge base", "qa system", "llm", "ollama", "ai backend", "chatbot ai", "brain"], "fastapi_rag_ai"),
        # Omnichannel / chatbot platform / saas
        (["saas", "omnichannel", "whatsapp", "chatbot platform", "multi-tenant", "nestjs"], "nestjs_nextjs_saas"),
        # OAuth / gateway / proxy / shopee
        (["gateway", "oauth", "proxy", "shopee", "marketplace", "affiliate", "hono", "edge"], "hono_edge_api"),
        # Wallet / ledger / koin / bank
        (["wallet", "ledger", "koin", "coin", "bank", "transfer", "mint", "fastify"], "fastify_prisma_api"),
        # Dashboard / pipeline / microstock / visual
        (["dashboard", "pipeline", "microstock", "adobe stock", "flask", "canvas", "monitoring"], "flask_canvas_dashboard"),
        # Next.js fullstack / CMS / admin
        (["cms", "admin", "next.js", "nextjs", "full-stack", "fullstack", "prisma", "sqlite"], "nextjs_fullstack"),
        # Frontend SPA / UI / vite / react
        (["vite", "react", "spa", "frontend", "ui", "interface", "single page"], "vite_react_ts"),
    ]

    description_lower = description.lower()
    scores: dict[str, int] = {name: 0 for name in ARCHETYPES}

    for keywords, archetype in keyword_map:
        for kw in keywords:
            if kw in description_lower:
                scores[archetype] = scores.get(archetype, 0) + 1

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        # Default fallback
        return "vite_react_ts"
    return best


def generate_project_plan(archetype: str, project_name: str) -> dict:
    """
    Hasilkan rencana proyek baru berdasarkan archetype dan nama proyek.

    Args:
        archetype: Nama archetype (gunakan list_archetypes() untuk pilihan).
        project_name: Nama proyek baru (contoh: "MyCoolApp").

    Returns:
        Dict berisi: name, archetype_used, description, stack, setup_steps,
                     structure, env_vars, deploy, dan sprint_plan.
    """
    arch = get_archetype(archetype)

    # Generate sprint plan generik berdasarkan modul dalam structure
    folders = [k for k in arch["structure"].keys() if k.endswith("/")]
    sprint_plan = []
    if len(folders) >= 4:
        sprint_plan = [
            {"sprint": 1, "scope": f"Setup project {project_name} — scaffold + env", "status": "TODO"},
            {"sprint": 2, "scope": f"Core modules: {', '.join(folders[:2])}", "status": "TODO"},
            {"sprint": 3, "scope": f"Business logic: {', '.join(folders[2:4])}", "status": "TODO"},
            {"sprint": 4, "scope": "Testing + deployment", "status": "TODO"},
        ]
    else:
        sprint_plan = [
            {"sprint": 1, "scope": f"Setup + scaffold {project_name}", "status": "TODO"},
            {"sprint": 2, "scope": "Core feature implementation", "status": "TODO"},
            {"sprint": 3, "scope": "Testing + deployment", "status": "TODO"},
        ]

    return {
        "name": project_name,
        "archetype_used": archetype,
        "description": arch["description"],
        "stack": arch["stack"],
        "structure": arch["structure"],
        "setup_steps": [step.replace("myapp", project_name.lower().replace(" ", "-"))
                        for step in arch["setup_steps"]],
        "env_vars": arch["env_vars"],
        "deploy": arch["deploy"],
        "sprint_plan": sprint_plan,
        "inspired_by": arch.get("real_project", ""),
    }
