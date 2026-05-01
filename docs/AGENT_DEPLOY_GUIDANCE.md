# SIDIX Deploy Guidance untuk Agent (Kimi/Claude/GPT/Gemini)

> **Tanggal lock**: 2026-05-01
> **Trigger**: Founder caught Kimi deploy command salah path → LIVE tidak update 5 hari

---

## 🚨 PATH YANG BENAR

| Item | ❌ Salah | ✅ Benar |
|---|---|---|
| VPS root SIDIX | `/var/www/sidix` (TIDAK ADA) | `/opt/sidix` |
| Branch deploy aktif | `claude/gallant-ellis-7cd14d` (PR-only) | `work/gallant-ellis-7cd14d` (VPS track) |
| UI build dir | `/opt/sidix/SIDIX_USER_UI` | sama |
| UI dist asset | `/opt/sidix/SIDIX_USER_UI/dist/assets/` | sama |
| Service brain | PM2 `sidix-brain` (port 8765) | sama |
| Service UI | PM2 `sidix-ui` (port 4000) | sama |

## 📋 DEPLOY COMMAND CANONICAL

```bash
# 1. Pull latest code
cd /opt/sidix && git pull origin work/gallant-ellis-7cd14d

# 2. Kalau ada UI changes (SIDIX_USER_UI/), rebuild
cd /opt/sidix/SIDIX_USER_UI && npm install --no-audit --no-fund && npm run build

# 3. Restart services
pm2 restart sidix-brain --update-env
pm2 restart sidix-ui --update-env

# 4. Wait + verify
sleep 10
curl -sS http://localhost:8765/health | head -c 150
```

## 🔍 USER-SIDE VERIFY (WAJIB sebelum claim DONE)

Internal `curl localhost` ≠ user experience. WAJIB verify dari pintu user.

```bash
# Hash UI yang browser sees harus match VPS dist
curl -sS https://app.sidixlab.com/ | grep -oE 'index-[^"]*\.(js|css)' | head -3
# Compare dengan:
ls /opt/sidix/SIDIX_USER_UI/dist/assets/ | grep -E 'index-.*\.(js|css)$'
# Hash HARUS sama. Kalau beda = nginx cache, atau build belum apply, atau pm2 belum restart.
```

```bash
# Endpoint smoke test
curl -sS https://ctrl.sidixlab.com/health | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(f\"model_ready={d['model_ready']}, corpus={d['corpus_doc_count']}\")"

# Holistic chat test (aktual flow user)
curl -sS -X POST https://ctrl.sidixlab.com/agent/chat_holistic \
  -H 'Content-Type: application/json' \
  -d '{"question":"halo"}' --max-time 90 | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(f'ok={d.get(\"answer\",\"\")[:80]}... · {d.get(\"duration_ms\",0)/1000:.1f}s · n_sources={d.get(\"n_sources\")}'"
```

## 🔌 ENDPOINT SIDIX yang LIVE per 2026-05-01

| Endpoint | Method | Owner | Status |
|---|---|---|---|
| `/health` | GET | core | LIVE |
| `/agent/chat` | POST | legacy ReAct | LIVE |
| `/agent/chat_holistic` | POST | Sprint Α (multi_source_orchestrator) | LIVE |
| `/agent/chat_holistic_stream` | POST | Sprint Α + SSE | LIVE |
| `/agent/sanad/stats` | GET | Kimi Sprint A (sanad_orchestra) | LIVE |
| `/agent/validate` | POST | Kimi Sprint A | LIVE |
| `/agent/pencipta/status` | GET | Kimi Sprint E | LIVE |
| `/agent/pencipta/trigger` | POST | Kimi Sprint E | LIVE |
| `/agent/pencipta/outputs` | GET | Kimi Sprint E | LIVE |
| `/agent/pencipta/stats` | GET | Kimi Sprint E | LIVE |
| `/agent/sidix_state` | GET | monitoring | LIVE |
| `/dashboard` | GET | UI dashboard | LIVE |

## 🚫 ANTI-PATTERN AGENT (yang BIKIN founder bingung)

1. ❌ Pakai path `/var/www/sidix` (tidak ada — ini ngaco)
2. ❌ Push ke branch yang VPS tidak track (VPS = `work/gallant-ellis-7cd14d`)
3. ❌ Push ke local branch saja, tidak ke origin remote
4. ❌ Skip `npm run build` di SIDIX_USER_UI saat UI berubah
5. ❌ Lupa `pm2 restart sidix-ui --update-env` setelah build
6. ❌ Claim "deployed" tanpa verify user-side hash match
7. ❌ Internal `curl localhost` doang sebagai bukti LIVE
8. ❌ Asumsi cache HTTP — selalu test dengan hard refresh atau curl bypass cache

## 📞 FOUNDER FRUSTRATION PATTERN

Jika founder bilang "LIVE tidak ada perubahan", cek urut:
1. SSH ke VPS (`ssh sidix-vps` atau IP yang benar)
2. Cek path `/opt/sidix` exist?
3. `git log --oneline -1` — commit di VPS = commit di branch yang di-push?
4. Cek `pm2 list` — sidix-brain dan sidix-ui uptime kecil (baru restart)?
5. Cek dist hash di browser vs `/opt/sidix/SIDIX_USER_UI/dist/assets/`
6. Cek nginx cache (`/var/cache/nginx/` atau Cloudflare kalau ada)

Jangan asumsi "deployed". Always verify the chain: local → repo → origin → VPS git → PM2 process → dist file → nginx → browser.

---

**Author**: Fahmi Ghani · Mighan Lab / Tiranyx Digitalis Nusantara
**License**: MIT
