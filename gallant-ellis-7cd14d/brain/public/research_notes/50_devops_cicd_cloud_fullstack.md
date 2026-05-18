# Research Note 50 — DevOps, CI/CD & Cloud Fullstack

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-17
**Sumber**: Pengetahuan teknis + roadmap.sh best practices
**Relevance SIDIX**: SIDIX adalah self-hosted LLM platform — deployment, monitoring, dan operasional infrastruktur adalah hal yang kritis. Note ini mencakup GitHub Actions untuk CI/CD otomatis, Docker production-grade untuk containerisasi, Nginx/Caddy sebagai reverse proxy dengan SSL, opsi hosting hemat (Hetzner/Railway/Fly.io), monitoring dengan Prometheus+Grafana, dan docker-compose.yml lengkap untuk deploy SIDIX (brain_qa + UI + Caddy) secara satu perintah.
**Tags**: `github-actions`, `docker`, `kubernetes`, `nginx`, `caddy`, `monitoring`, `devops`, `self-hosting`, `sidix-deployment`, `railway`, `hetzner`

---

## 1. GitHub Actions — Workflow YAML

GitHub Actions adalah CI/CD platform terintegrasi dengan GitHub. Workflow didefinisikan sebagai YAML di `.github/workflows/`.

### Anatomi Workflow
```yaml
# .github/workflows/ci.yml
name: SIDIX CI/CD Pipeline

# Trigger events
on:
  push:
    branches: [main, develop]
    paths:
      - 'apps/brain_qa/**'
      - 'apps/ui/**'
  pull_request:
    branches: [main]
  workflow_dispatch:   # Manual trigger dari UI
    inputs:
      environment:
        description: 'Deploy target'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]

# Environment variables global
env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ─────────────────────────────────────────
  # JOB 1: Test backend
  # ─────────────────────────────────────────
  test-backend:
    name: Test Python Backend
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'  # Cache pip dependencies

      - name: Install dependencies
        run: |
          cd apps/brain_qa
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd apps/brain_qa
          pytest tests/ --cov=brain_qa --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./apps/brain_qa/coverage.xml

  # ─────────────────────────────────────────
  # JOB 2: Test frontend
  # ─────────────────────────────────────────
  test-frontend:
    name: Test Vite UI
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - name: Install pnpm
        uses: pnpm/action-setup@v3
        with:
          version: 9

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Type check
        run: pnpm --filter ui type-check

      - name: Lint
        run: pnpm --filter ui lint

      - name: Unit tests
        run: pnpm --filter ui test --coverage

      - name: Build
        run: pnpm --filter ui build

  # ─────────────────────────────────────────
  # JOB 3: Build & Push Docker image
  # ─────────────────────────────────────────
  build-docker:
    name: Build Docker Image
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Setup QEMU (untuk multi-arch build)
        uses: docker/setup-qemu-action@v3

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./apps/brain_qa
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ─────────────────────────────────────────
  # JOB 4: Deploy ke server
  # ─────────────────────────────────────────
  deploy:
    name: Deploy to Production
    needs: build-docker
    runs-on: ubuntu-latest
    environment: production  # Butuh approval manual jika dikonfigurasi

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/sidix
            docker compose pull
            docker compose up -d --remove-orphans
            docker image prune -f
```

### Matrix Builds — Test di Banyak Environment
```yaml
jobs:
  test-matrix:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]
      fail-fast: false  # Lanjut jika satu matrix gagal

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt && pytest
```

### Caching Strategy
```yaml
# Cache pip packages (Python)
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

# Cache node_modules (Node.js)
- uses: actions/cache@v4
  with:
    path: ~/.pnpm-store
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}

# Cache Docker layers
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Branch Protection Rules
```yaml
# Branch protection (dikonfigurasi di GitHub Settings, bukan YAML)
# main branch:
# - Require status checks: test-backend, test-frontend
# - Require pull request reviews: 1 reviewer
# - Dismiss stale pull request approvals
# - Require branches to be up to date
# - Restrict who can push to matching branches
```

---

## 2. Docker Production — Multi-stage, Distroless, Health Checks

### Multi-stage Build — Optimal untuk Python
```dockerfile
# Dockerfile untuk SIDIX brain_qa
# Stage 1: Builder — install dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy requirements dulu (Docker layer cache)
COPY requirements.txt .

# Install ke virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime — image final yang ringan
FROM python:3.11-slim AS runtime

# Security: jalankan sebagai non-root user
RUN groupadd -r sidix && useradd -r -g sidix sidix

WORKDIR /app

# Copy virtual environment dari builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=sidix:sidix . .

# Aktifkan virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER sidix

EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/health')"

CMD ["uvicorn", "brain_qa.main:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "2"]
```

### Multi-stage untuk Node.js/Vite
```dockerfile
# Dockerfile untuk SIDIX UI
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable pnpm

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

# Stage 2: Serve dengan nginx minimal
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -q --spider http://localhost/health || exit 1
```

### Docker Compose Profiles
```yaml
# docker-compose.yml
services:
  brain_qa:
    # ... (lihat Section 10 untuk full config)

  ui:
    profiles: [ui, full]
    # ...

  prometheus:
    profiles: [monitoring]
    # ...

  grafana:
    profiles: [monitoring]
    # ...
```

```bash
# Run hanya service tertentu
docker compose --profile ui up -d
docker compose --profile monitoring up -d
docker compose --profile full up -d
```

### Docker Networks
```yaml
# Isolasi network untuk keamanan
networks:
  frontend:          # Public-facing (Caddy <-> UI, Caddy <-> brain_qa)
    driver: bridge
  backend:           # Internal only (brain_qa <-> database)
    driver: bridge
    internal: true   # Tidak bisa akses internet langsung

services:
  caddy:
    networks: [frontend]
  brain_qa:
    networks: [frontend, backend]
  db:
    networks: [backend]
```

---

## 3. Kubernetes Basics

### Core Objects

```yaml
# Pod — unit terkecil deployment
apiVersion: v1
kind: Pod
metadata:
  name: sidix-brain-qa
  labels:
    app: sidix
    component: brain-qa
spec:
  containers:
    - name: brain-qa
      image: ghcr.io/fahmi/sidix-brain-qa:latest
      ports:
        - containerPort: 8765
      env:
        - name: DATA_DIR
          value: /data
      resources:
        requests:
          memory: "256Mi"
          cpu: "250m"
        limits:
          memory: "512Mi"
          cpu: "500m"
      livenessProbe:
        httpGet:
          path: /health
          port: 8765
        initialDelaySeconds: 30
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 8765
        initialDelaySeconds: 10

---
# Deployment — manage Pod replicas
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sidix-brain-qa
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sidix
      component: brain-qa
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: sidix
        component: brain-qa
    spec:
      containers:
        - name: brain-qa
          image: ghcr.io/fahmi/sidix-brain-qa:latest
          # ... (same as Pod spec)

---
# Service — expose Deployment
apiVersion: v1
kind: Service
metadata:
  name: sidix-brain-qa-svc
spec:
  selector:
    app: sidix
    component: brain-qa
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8765
  type: ClusterIP  # Internal only

---
# Ingress — routing dari luar
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sidix-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
    - hosts:
        - sidix.example.com
      secretName: sidix-tls
  rules:
    - host: sidix.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: sidix-brain-qa-svc
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: sidix-ui-svc
                port:
                  number: 80

---
# HPA — auto scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sidix-brain-qa-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sidix-brain-qa
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

---
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: sidix-config
data:
  DATA_DIR: "/data"
  LOG_LEVEL: "info"
  MAX_RESULTS: "10"

---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: sidix-secrets
type: Opaque
stringData:
  API_KEY: "your-secret-key"
  DB_PASSWORD: "db-secret"
```

---

## 4. Cloud Providers — Perbandingan

### Free Tier / Budget Friendly

| Platform | Tipe | Harga | RAM | CPU | Cocok untuk |
|----------|------|-------|-----|-----|-------------|
| **Railway** | PaaS | $5/mo (500h free) | 512MB | Shared | Quick deploy, hobbyist |
| **Render** | PaaS | $7/mo (free spin down) | 512MB | Shared | Backend API |
| **Fly.io** | Container PaaS | $0 (3 shared VMs free) | 256MB | Shared | Global edge deploy |
| **Hetzner Cloud** | VPS | €4.51/mo (CX22) | 4GB | 2 vCPU | Best value VPS |
| **DigitalOcean** | VPS | $6/mo (Droplet) | 1GB | 1 vCPU | Populer, mudah |
| **Vultr** | VPS | $5/mo | 1GB | 1 vCPU | Alternatif DO |
| **Oracle Cloud** | VPS | $0 (always free) | 1GB | 1 vCPU | Gratis selamanya |
| **AWS EC2 t3.micro** | IaaS | $7-10/mo | 1GB | 2 vCPU | Enterprise |
| **GCP e2-micro** | IaaS | $0 (free tier) | 1GB | 0.25 vCPU | Dev/testing |

### Rekomendasi untuk SIDIX
```
Phase 1 (prototyping): Fly.io atau Railway
Phase 2 (production, budget): Hetzner CX22 (€4.51/mo, 4GB RAM = cukup untuk SIDIX)
Phase 3 (scale): Hetzner CCX13 + Load Balancer atau k3s cluster
```

### Deploy ke Railway
```yaml
# railway.toml
[build]
builder = "dockerfile"
dockerfilePath = "apps/brain_qa/Dockerfile"

[deploy]
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[[services]]
name = "brain-qa"
source = "apps/brain_qa"

[services.variables]
PORT = "8765"
DATA_DIR = "/data"
```

### Deploy ke Fly.io
```toml
# fly.toml
app = "sidix-brain-qa"
primary_region = "sin"  # Singapore

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8765
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512

[mounts]
  source = "sidix_data"
  destination = "/data"
```

---

## 5. Nginx & Caddy — Reverse Proxy

### Nginx Config untuk SIDIX
```nginx
# /etc/nginx/sites-available/sidix.conf

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;

# Upstream servers
upstream brain_qa {
    server 127.0.0.1:8765;
    keepalive 32;
}

upstream sidix_ui {
    server 127.0.0.1:3000;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name sidix.example.com;
    return 301 https://$host$request_uri;
}

# Main server
server {
    listen 443 ssl http2;
    server_name sidix.example.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/sidix.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sidix.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    gzip_min_length 1000;
    gzip_comp_level 6;

    # API proxy
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;

        proxy_pass http://brain_qa/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Timeout untuk LLM yang lambat
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;

        # Streaming support
        proxy_buffering off;
        proxy_cache off;
    }

    # Static UI files
    location / {
        proxy_pass http://sidix_ui;
        proxy_set_header Host $host;

        # Cache static assets
        location ~* \.(js|css|png|jpg|svg|woff2)$ {
            proxy_pass http://sidix_ui;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check (bypass auth)
    location /health {
        proxy_pass http://brain_qa/health;
        access_log off;
    }
}
```

### Caddy — Otomatis SSL (Lebih Simple dari Nginx)
```caddyfile
# Caddyfile — SSL otomatis dari Let's Encrypt

sidix.example.com {
    # Gzip compression
    encode gzip

    # Rate limiting
    rate_limit {
        zone api {
            key {remote_host}
            events 30
            window 1m
        }
    }

    # API backend
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy brain_qa:8765 {
            transport http {
                response_header_timeout 120s
            }
            flush_interval -1  # Enable streaming
        }
    }

    # Static UI
    handle {
        reverse_proxy sidix-ui:80
    }

    # Logging
    log {
        output file /var/log/caddy/sidix.log
        format json
    }
}

# Monitoring (internal only)
:2019 {
    metrics /metrics
}
```

---

## 6. Database Hosting

### Perbandingan Database Cloud

| Service | Engine | Free Tier | Notes |
|---------|--------|-----------|-------|
| **Neon** | PostgreSQL | 0.5GB, 1 branch | Serverless, auto-suspend |
| **Supabase** | PostgreSQL | 500MB, 2 project | Full BaaS |
| **PlanetScale** | MySQL (Vitess) | 1GB | Branching workflow |
| **MongoDB Atlas** | MongoDB | 512MB | M0 cluster |
| **Turso** | SQLite (LibSQL) | 8GB, 500 DBs | Edge SQLite |
| **Redis Cloud** | Redis | 30MB | Cache layer |

### SQLite untuk SIDIX (Self-hosted Sederhana)
```python
# SIDIX menggunakan file-based storage, SQLite cocok
import sqlite3
from pathlib import Path

class SidixDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    title TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT REFERENCES sessions(id),
                    role TEXT CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sources TEXT  -- JSON array of source references
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, created_at);
            """)
```

---

## 7. Monitoring — Prometheus, Grafana, Sentry

### Prometheus Metrics di FastAPI (SIDIX)
```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time

# Metrics definitions
query_counter = Counter(
    'sidix_queries_total',
    'Total queries processed',
    ['status', 'endpoint']
)

query_duration = Histogram(
    'sidix_query_duration_seconds',
    'Query processing duration',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

active_sessions = Gauge(
    'sidix_active_sessions',
    'Number of active chat sessions'
)

bm25_index_size = Gauge(
    'sidix_bm25_documents_total',
    'Total documents in BM25 index'
)

# FastAPI integration
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        query_counter.labels(
            status=response.status_code,
            endpoint=request.url.path
        ).inc()

        query_duration.labels(
            endpoint=request.url.path
        ).observe(duration)

        return response

app = FastAPI()
app.add_middleware(MetricsMiddleware)

# Expose metrics endpoint
metrics_app = make_asgi_app()
app.mount('/metrics', metrics_app)
```

### Grafana Dashboard (JSON snippet)
```json
{
  "panels": [
    {
      "title": "Query Rate",
      "type": "timeseries",
      "targets": [
        {
          "expr": "rate(sidix_queries_total[5m])",
          "legendFormat": "{{status}} {{endpoint}}"
        }
      ]
    },
    {
      "title": "P95 Query Duration",
      "type": "stat",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(sidix_query_duration_seconds_bucket[10m]))",
          "legendFormat": "P95 Latency"
        }
      ]
    },
    {
      "title": "BM25 Index Size",
      "type": "stat",
      "targets": [
        {
          "expr": "sidix_bm25_documents_total"
        }
      ]
    }
  ]
}
```

### Sentry — Error Tracking
```python
# SIDIX FastAPI dengan Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        StarletteIntegration(),
        FastApiIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% performance monitoring
    environment=os.getenv("ENVIRONMENT", "development"),
    release=f"sidix@{VERSION}",

    # Filter out health check noise
    before_send=lambda event, hint: None if "/health" in str(event) else event
)
```

### UptimeRobot — Free Uptime Monitoring
```
Setup di uptimerobot.com:
1. Monitor type: HTTP(s)
2. URL: https://sidix.example.com/health
3. Interval: 5 minutes
4. Alert contacts: email/Telegram/Slack
5. Free plan: 50 monitors
```

---

## 8. CDN — Cloudflare & BunnyCDN

### Cloudflare Setup untuk SIDIX
```
1. Tambah domain ke Cloudflare
2. Update nameservers ke Cloudflare
3. Proxy status: Proxied (orange cloud)

Konfigurasi penting:
- SSL: Full (strict) — end-to-end encryption
- Auto Minify: JS, CSS, HTML
- Brotli: ON
- HTTP/3: ON
- Cache Rules:
  - /api/* → bypass cache (dynamic content)
  - /assets/* → cache 1 year (static assets)
  - /*.html → cache 1 hour

Rate Limiting (Cloudflare free tier):
- Rule: /api/ask → 30 req/menit per IP
```

### Cloudflare Workers untuk Edge Caching
```javascript
// worker.js — cache frequent SIDIX queries
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Hanya cache GET requests ke /api/ask dengan query sederhana
    if (request.method === 'GET' && url.pathname === '/api/search') {
      const cacheKey = new Request(url.toString(), request);
      const cache = caches.default;

      // Check cache
      let response = await cache.match(cacheKey);
      if (response) {
        return new Response(response.body, {
          headers: { ...response.headers, 'X-Cache': 'HIT' }
        });
      }

      // Forward ke origin
      response = await fetch(request);

      // Cache 5 menit untuk query umum
      const responseToCache = new Response(response.body, response);
      responseToCache.headers.set('Cache-Control', 'public, max-age=300');
      await cache.put(cacheKey, responseToCache.clone());

      return responseToCache;
    }

    return fetch(request);
  }
};
```

---

## 9. Cost Optimization

### Strategi Hemat Biaya

| Teknik | Penghematan | Trade-off |
|--------|-------------|-----------|
| **Spot/preemptible instances** | 60-90% lebih murah | Bisa di-terminate sewaktu-waktu |
| **Auto-stop saat idle** | 100% saat tidak digunakan | Cold start delay |
| **Serverless functions** | Pay per invocation | Tidak cocok untuk LLM warm |
| **SQLite alih-alih PostgreSQL** | Tidak perlu managed DB | Scaling terbatas |
| **BunnyCDN vs Cloudflare** | $0.01/GB (lebih murah) | Setup lebih manual |
| **Hetzner vs AWS** | 3-5x lebih murah | Kurang enterprise features |

### Serverless vs Always-on untuk SIDIX

```
LLM/RAG workload: SELALU pilih always-on server
Alasan:
- Model harus di-load ke memory (5-10 detik cold start)
- BM25 index harus ter-load di memory
- Streaming response butuh persistent connection

Serverless COCOK untuk:
- Auth/webhook handlers
- Image resize
- Email processing
- Scheduled jobs (reindex BM25 tiap malam)
```

---

## 10. Self-Hosting SIDIX — docker-compose.yml Lengkap

```yaml
# docker-compose.yml — Full SIDIX stack
# Usage:
#   docker compose up -d                    # semua service
#   docker compose --profile dev up -d      # + dev tools
#   docker compose --profile monitoring up  # + monitoring

version: '3.8'

services:
  # ─────────────────────────────────────────
  # Core: SIDIX Brain QA (FastAPI + BM25 RAG)
  # ─────────────────────────────────────────
  brain_qa:
    build:
      context: ./apps/brain_qa
      dockerfile: Dockerfile
      target: runtime
    container_name: sidix-brain-qa
    restart: unless-stopped
    environment:
      - DATA_DIR=/data
      - INDEX_DIR=/data/index
      - LOG_LEVEL=info
      - MAX_RESULTS=10
      - CORS_ORIGINS=http://localhost:3000,https://sidix.example.com
    volumes:
      - brain_data:/data
      - ./brain:/data/brain:ro  # Mount brain notes (read-only)
    ports:
      - "8765:8765"  # Expose untuk development
    networks:
      - internal
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8765/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ─────────────────────────────────────────
  # Core: SIDIX UI (Vite + React)
  # ─────────────────────────────────────────
  sidix_ui:
    build:
      context: ./apps/ui
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=/api
    container_name: sidix-ui
    restart: unless-stopped
    networks:
      - internal
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80"]
      interval: 30s
      timeout: 5s
      retries: 3

  # ─────────────────────────────────────────
  # Edge: Caddy (Reverse Proxy + SSL)
  # ─────────────────────────────────────────
  caddy:
    image: caddy:2-alpine
    container_name: sidix-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"  # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - internal
    depends_on:
      brain_qa:
        condition: service_healthy
      sidix_ui:
        condition: service_healthy

  # ─────────────────────────────────────────
  # Monitoring: Prometheus
  # ─────────────────────────────────────────
  prometheus:
    image: prom/prometheus:latest
    container_name: sidix-prometheus
    profiles: [monitoring]
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - internal
    ports:
      - "9090:9090"  # Dev only

  # ─────────────────────────────────────────
  # Monitoring: Grafana
  # ─────────────────────────────────────────
  grafana:
    image: grafana/grafana:latest
    container_name: sidix-grafana
    profiles: [monitoring]
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    networks:
      - internal
    ports:
      - "3001:3000"  # Dev only

  # ─────────────────────────────────────────
  # Dev: Adminer (Database UI)
  # ─────────────────────────────────────────
  adminer:
    image: adminer:latest
    profiles: [dev]
    ports:
      - "8080:8080"
    networks:
      - internal

networks:
  internal:
    driver: bridge

volumes:
  brain_data:
    driver: local
  caddy_data:
    driver: local
  caddy_config:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### Caddyfile untuk SIDIX
```caddyfile
# Caddyfile

{
    # Email untuk Let's Encrypt
    email admin@example.com

    # Aktifkan admin API (untuk reload config)
    admin 0.0.0.0:2019
}

# Production domain
sidix.example.com {
    encode gzip

    # Security headers
    header {
        X-Frame-Options DENY
        X-Content-Type-Options nosniff
        Strict-Transport-Security "max-age=31536000"
    }

    # Brain QA API
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy brain_qa:8765 {
            flush_interval -1  # Streaming support
            transport http {
                response_header_timeout 120s
            }
        }
    }

    # Metrics (internal access only)
    handle /metrics {
        reverse_proxy brain_qa:8765/metrics
        @external not remote_ip private_ranges
        abort @external
    }

    # UI
    handle {
        reverse_proxy sidix_ui:80
    }

    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# Local development (HTTP only)
:8080 {
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy brain_qa:8765 {
            flush_interval -1
        }
    }

    handle {
        reverse_proxy sidix_ui:80
    }
}
```

### Prometheus Config
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sidix-brain-qa'
    static_configs:
      - targets: ['brain_qa:8765']
    metrics_path: '/metrics'

  - job_name: 'caddy'
    static_configs:
      - targets: ['caddy:2019']
    metrics_path: '/metrics'
```

### .env Template untuk SIDIX
```bash
# .env.example — copy ke .env dan isi nilai

# Server
DOMAIN=sidix.example.com
ENVIRONMENT=production

# Brain QA
DATA_DIR=/data
MAX_RESULTS=10
LOG_LEVEL=info

# Security
GRAFANA_PASSWORD=changeme-secure-password
API_SECRET_KEY=generate-with-openssl-rand-hex-32

# Optional: Sentry
SENTRY_DSN=

# Optional: Cloudflare
CLOUDFLARE_API_TOKEN=
```

### Deploy Commands
```bash
# Clone dan setup
git clone https://github.com/fahmi/sidix.git
cd sidix
cp .env.example .env
nano .env  # edit values

# Pertama kali: build dan start
docker compose build
docker compose up -d

# Reindex BM25 setelah tambah notes
docker compose exec brain_qa python -m brain_qa index

# Update ke versi terbaru
git pull
docker compose build brain_qa
docker compose up -d brain_qa
docker compose exec brain_qa python -m brain_qa index

# Logs
docker compose logs -f brain_qa
docker compose logs -f caddy

# Dengan monitoring
docker compose --profile monitoring up -d
```

---

## 11. Implikasi untuk SIDIX

1. **GitHub Actions Pipeline**: Setiap push ke `main` → test Python + test frontend → build Docker → deploy otomatis ke VPS dengan SSH. Zero-downtime rolling update.

2. **Docker Production**: Multi-stage build mengurangi image size dari ~800MB → ~150MB. Non-root user untuk security. Health check memastikan service ready sebelum menerima traffic.

3. **Caddy > Nginx untuk SIDIX**: SSL otomatis tanpa certbot, config jauh lebih simple, support HTTP/3, built-in streaming proxy. Cocok untuk solo founder yang tidak mau repot.

4. **Hetzner CX22 (€4.51/mo, 4GB RAM)**: Cukup untuk SIDIX production — 4GB RAM buat brain_qa (BM25 index ~100MB), UI, Caddy, dan Prometheus semua berjalan.

5. **Monitoring Minimal**: Prometheus + Grafana untuk track query rate dan latency. Sentry untuk catch errors. UptimeRobot gratis untuk alerting down.

6. **Cost Reality SIDIX**: Hetzner CX22 €4.51 + domain €10/tahun + Cloudflare free = ~€55/tahun untuk full production deployment. Sangat affordable untuk solo founder.

7. **docker-compose.yml**: Satu file untuk deploy semua — jalankan `docker compose up -d` dari fresh VPS dan dalam 5 menit SIDIX sudah live dengan HTTPS.

---

## Ringkasan untuk Corpus SIDIX

Note ini mencakup seluruh pipeline DevOps modern: GitHub Actions (workflow YAML, matrix builds, caching, secrets, environments, Docker build & push), Docker production-grade (multi-stage builds, non-root user, health checks, compose profiles, network isolation), Kubernetes fundamentals (Pod, Deployment, Service, Ingress, ConfigMap, Secret, HPA), perbandingan cloud providers (Hetzner €4.51 vs Railway vs Fly.io vs AWS), Nginx dan Caddy sebagai reverse proxy dengan SSL otomatis, database hosting (Neon/Supabase/Turso), monitoring stack (Prometheus metrics di FastAPI, Grafana dashboard, Sentry error tracking, UptimeRobot), CDN Cloudflare dengan Workers, optimasi biaya, dan docker-compose.yml lengkap untuk deploy SIDIX (brain_qa + UI + Caddy + Prometheus + Grafana) secara production-ready.
