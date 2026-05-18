# SIDIX_NEXT_UI

Next.js (App Router) frontend untuk SIDIX — replacement gradual dari `SIDIX_USER_UI` (vanilla TS+Vite).

**Status: 2026-04-30 — Initial scaffold + 3 components ported.**

## Lock Decisions (per FOUNDER_JOURNAL 2026-04-30)

- Framework: **Next.js 15 App Router** + TypeScript + Tailwind v3 + lucide-react + framer-motion
- Source scaffolding: `C:\Users\ASUS\Downloads\Kimi_Agent_Sidix AI Agent Selesai\UI Baru SIDIX\app\`
- Brand: Space Grotesk + neon palette (#7C5CFF #00D2FF #FF6EC7 #0B0F2A #FFFFFF)
- Backend: `ctrl.sidixlab.com:8765` (FastAPI brain_qa) — **TIDAK BERUBAH**
- **NO MOCK DATA**: hapus "Halo Ayudia / Pro Plan / 1,250 Credits / Healthy Drink Campaign / Aktivitas dummy" — wire ke fitur SIDIX real

## Struktur

```
SIDIX_NEXT_UI/
├── app/
│   ├── globals.css       # Space Grotesk import + brand CSS vars
│   ├── layout.tsx        # Root layout (font-grotesk + bg)
│   └── page.tsx          # Home: 3-column LeftSidebar/ChatDashboard/RightPanel
├── components/
│   ├── LeftSidebar.tsx   # Navigation (Chat/Agent/Tools/Projects/Knowledge/Integrations/History)
│   ├── ChatDashboard.tsx # Real chat dengan persona selector + quick actions + loading state
│   └── RightPanel.tsx    # Built-in Tools panel + status (placeholder, real wire post-reset)
├── lib/
│   ├── sidix-client.ts   # API wrapper: chat() + health() + streamGenerate()
│   └── cn.ts             # clsx + tailwind-merge
├── package.json
├── next.config.mjs       # Rewrite /api/brain/* -> ctrl.sidixlab.com
├── tailwind.config.ts    # SIDIX brand tokens
├── postcss.config.mjs
└── tsconfig.json
```

## Yang Sudah Ada (Hari ini)

✅ Next.js scaffolding minimal (manual, tanpa `create-next-app` untuk hemat token)  
✅ Tailwind brand tokens (`sidix-purple/cyan/pink/dark/surface`)  
✅ Layout 3-column responsive (sidebar 250px / chat flex / right 320px hidden lg)  
✅ ChatDashboard wired ke `POST /agent/chat` REAL (bukan mock)  
✅ Persona selector (5 SIDIX persona LOCKED)  
✅ Loading state dengan timer transparan ("SIDIX sedang berpikir... 12s")  
✅ Error state graceful (message + saran cek /health)  
✅ Quick actions sebagai prompt starter

## Yang Belum (Post Limit Reset)

⏳ ParticleBackground component (Three.js / canvas) — defer, optional polish  
⏳ Real wire RightPanel ke tools registry endpoint  
⏳ Streaming SSE wrapper untuk `/agent/chat` (sekarang stream cuma di `/agent/generate/stream` raw)  
⏳ Auth (Supabase) — replace static greeting dengan user real  
⏳ Quota display real dari `/quota/status`  
⏳ Mobile responsive polish (sidebar collapse, bottom nav)  
⏳ Mascot Option B (image bos + SDXL state variants)  
⏳ Deploy: PM2 reconfig `sidix-ui` ganti `serve dist` → `next start -p 4000`  
⏳ Test e2e: install deps + npm run build + npm run start

## Run Locally (saat dev)

```bash
cd SIDIX_NEXT_UI
npm install
# (set NEXT_PUBLIC_BRAIN_QA_URL kalau mau backend lain)
npm run dev
# Browse: http://localhost:4000
```

## Deploy ke VPS (Future)

```bash
# Di VPS:
cd /opt/sidix
git pull
cd SIDIX_NEXT_UI
npm install --omit=dev
npm run build

# Update PM2:
pm2 stop sidix-ui     # stop yang lama (serve dist dari SIDIX_USER_UI)
pm2 delete sidix-ui
pm2 start npm --name "sidix-next-ui" -- run start
pm2 save

# Nginx tetap proxy_pass ke localhost:4000
```

Atau parallel deploy dulu di subdomain `next.sidixlab.com` sebelum cutover dari `app.sidixlab.com` lama.
