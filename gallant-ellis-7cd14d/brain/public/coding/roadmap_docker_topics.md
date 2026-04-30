# Docker & Containers — Topic Index + Quick Reference

> Sumber: roadmap.sh/docker (CC BY-SA 4.0)
> Referensi: https://roadmap.sh/docker

## Container Fundamentals

### What is a Container?
- Isolated process with its own filesystem, network, PID namespace
- Shares host OS kernel (unlike VMs which virtualize hardware)
- Lightweight: starts in milliseconds, uses less memory than VM
- Portable: "works on my machine" → works everywhere Docker runs

### Docker Architecture
```
Docker Client (CLI) ──→ Docker Daemon (dockerd)
                              ↓
                    Container Runtime (containerd)
                              ↓
                    OCI Runtime (runc)
                              ↓
                    Linux namespaces + cgroups
```

- **Namespace**: isolates processes (pid, net, mnt, uts, ipc, user)
- **cgroups**: limits CPU, memory, I/O for process group
- **Union filesystem**: layers (OverlayFS) — each layer is read-only, top layer is writable

## Docker Images

### Dockerfile
```dockerfile
# Base image — use specific version tag in production
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency files first (layer cache optimization)
COPY requirements.txt .

# Install dependencies (cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (security best practice)
RUN addgroup --system app && adduser --system --group app
USER app

# Document the port (informational)
EXPOSE 8765

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Use exec form (not shell form) to receive signals properly
CMD ["python", "-m", "brain_qa", "serve", "--host", "0.0.0.0", "--port", "8765"]
```

### Multi-stage Build (reduces image size)
```dockerfile
# Stage 1: Build
FROM python:3.12 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim AS production
WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY . .

RUN addgroup --system app && adduser --system --group app
USER app

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "brain_qa", "serve"]
```

### .dockerignore
```
.git
.gitignore
__pycache__
*.pyc
*.pyo
.env
.venv
node_modules
*.log
dist/
.DS_Store
```

## Docker CLI — Common Commands

### Image Management
```bash
docker build -t sidix:latest .           # build image from Dockerfile
docker build -t sidix:1.0.0 -f Dockerfile.prod . # specify Dockerfile
docker images                            # list local images
docker image ls
docker image inspect sidix:latest        # detailed image info
docker image history sidix:latest        # show layers
docker pull python:3.12-slim             # pull from registry
docker push myrepo/sidix:1.0.0           # push to registry
docker rmi sidix:old                     # remove image
docker image prune                       # remove dangling images
docker image prune -a                    # remove all unused images
docker tag sidix:latest sidix:1.0.0      # add tag
```

### Container Lifecycle
```bash
docker run sidix:latest                  # run (create + start)
docker run -d sidix:latest               # detached (background)
docker run -it ubuntu bash               # interactive + TTY
docker run --name brain-server sidix:latest  # named container
docker run --rm sidix:latest             # auto-remove when done
docker run -p 8765:8765 sidix:latest     # port mapping host:container
docker run -p 127.0.0.1:8765:8765 sidix  # bind to localhost only
docker run -v /host/path:/app/data sidix # bind mount
docker run -v brain_data:/app/data sidix # named volume
docker run -e "DEBUG=1" sidix:latest     # environment variable
docker run --env-file .env sidix:latest  # env from file
docker run --memory 2g --cpus 1.5 sidix  # resource limits

docker ps                                # running containers
docker ps -a                             # all containers (incl. stopped)
docker start/stop/restart <container>
docker rm <container>                    # remove stopped container
docker rm -f <container>                 # force remove running container
docker container prune                   # remove all stopped containers

docker logs brain-server                 # view logs
docker logs -f brain-server              # follow (tail -f)
docker logs --tail 100 brain-server      # last 100 lines
docker exec -it brain-server bash        # exec into running container
docker exec brain-server python -c "import brain_qa; print('ok')"
docker cp file.txt brain-server:/app/    # copy to container
docker cp brain-server:/app/out.log .    # copy from container
docker inspect brain-server              # full container info
docker stats                             # live resource usage
docker top brain-server                  # running processes
```

### Volumes
```bash
docker volume create brain_data         # create named volume
docker volume ls
docker volume inspect brain_data
docker volume rm brain_data
docker volume prune                     # remove unused volumes

# Bind mount vs Named volume
# Bind mount: -v /absolute/host/path:/container/path
#   → host path must exist, good for dev
# Named volume: -v volume_name:/container/path
#   → managed by Docker, good for production data
```

## Docker Compose

### docker-compose.yml
```yaml
version: "3.9"

services:
  brain-qa:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    image: sidix/brain-qa:1.0.0
    container_name: brain-qa
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - BRAIN_QA_MODEL_MODE=local_lora
      - SIDIX_DISABLE_4BIT=0
    env_file:
      - .env
    volumes:
      - ./apps/brain_qa/models:/app/models:ro
      - bm25_index:/app/.data
      - ./brain:/app/brain:ro
    networks:
      - sidix-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: "4"

  sidix-ui:
    image: nginx:alpine
    container_name: sidix-ui
    restart: unless-stopped
    ports:
      - "3000:80"
    volumes:
      - ./SIDIX_USER_UI/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - sidix-net
    depends_on:
      brain-qa:
        condition: service_healthy

volumes:
  bm25_index:

networks:
  sidix-net:
    driver: bridge
```

### Compose Commands
```bash
docker compose up                       # start all services
docker compose up -d                    # detached
docker compose up --build               # rebuild images
docker compose up brain-qa              # start specific service
docker compose down                     # stop + remove containers
docker compose down -v                  # also remove volumes
docker compose ps                       # list services
docker compose logs                     # all service logs
docker compose logs -f brain-qa         # follow specific service
docker compose exec brain-qa bash       # exec into service
docker compose run brain-qa python -m brain_qa index  # one-off command
docker compose pull                     # pull latest images
docker compose build                    # build images
docker compose restart brain-qa         # restart service
docker compose scale brain-qa=3         # scale replicas
```

## Networking

```bash
# Network types
# bridge (default): containers on same host can communicate via container name
# host: container shares host network stack (no isolation, better performance)
# none: no network
# overlay: multi-host networking (Docker Swarm/Kubernetes)

docker network create sidix-net
docker network ls
docker network inspect sidix-net
docker network connect sidix-net brain-qa     # connect container to network
docker network disconnect sidix-net brain-qa  # disconnect

# Container DNS: in same network, use container name as hostname
# brain-qa can reach sidix-ui at http://sidix-ui:80
```

## Registry

```bash
# Docker Hub
docker login
docker push username/image:tag
docker pull username/image:tag

# GitHub Container Registry
docker login ghcr.io -u USERNAME --password-stdin
docker tag image ghcr.io/USERNAME/IMAGE:TAG
docker push ghcr.io/USERNAME/IMAGE:TAG

# Self-hosted registry
docker run -d -p 5000:5000 --name registry registry:2
docker tag sidix:latest localhost:5000/sidix:latest
docker push localhost:5000/sidix:latest
```

## Best Practices

### Security
```dockerfile
# 1. Use specific version tags (not :latest in production)
FROM python:3.12.3-slim-bookworm

# 2. Run as non-root user
RUN addgroup --gid 1001 --system app \
 && adduser --no-create-home --shell /bin/false --disabled-password \
    --uid 1001 --system --group app
USER 1001

# 3. Read-only filesystem (except specific dirs)
# docker run --read-only --tmpfs /tmp sidix:latest

# 4. Drop capabilities
# docker run --cap-drop ALL --cap-add NET_BIND_SERVICE sidix:latest

# 5. Scan for vulnerabilities
# docker scout cves sidix:latest
```

### Image Optimization
```dockerfile
# Order layers from least to most frequently changed
# Less change → more cache hits

# ✗ Bad: everything in one layer, no cache benefit
COPY . .
RUN pip install -r requirements.txt && python setup.py build

# ✓ Good: dependencies cached separately
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Use slim/alpine base images
FROM python:3.12-slim    # ~130MB vs python:3.12 ~1GB
FROM python:3.12-alpine  # ~60MB but musl libc (compat issues)

# Combine RUN commands to reduce layers
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
```

## Docker Swarm (basic)

```bash
docker swarm init                       # initialize swarm manager
docker swarm join --token TOKEN HOST    # join as worker
docker service create --name web nginx  # create service
docker service ls
docker service scale web=5              # scale to 5 replicas
docker service update --image nginx:1.25 web  # rolling update
docker stack deploy -c docker-compose.yml sidix  # deploy stack
docker stack ls
docker stack rm sidix
```

## Referensi Lanjut
- https://roadmap.sh/docker
- https://docs.docker.com/
- https://github.com/veggiemonk/awesome-docker
- https://docs.docker.com/compose/
- Docker security: https://docs.docker.com/engine/security/
