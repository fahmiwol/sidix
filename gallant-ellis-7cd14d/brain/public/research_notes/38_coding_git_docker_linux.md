# Git, Docker, and Linux/Bash

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: Sintesis dari Git documentation, Docker best practices, Linux man pages, dan praktik DevOps industri.
> Relevan untuk: developers, DevOps engineers, system administrators, backend engineers
> Tags: git, docker, linux, bash, devops, containers, version-control, shell-scripting, ci-cd

## Git

### Core Concepts
```
Working Directory  — files on disk that you can edit
Staging Area       — index: snapshot of what will go into the next commit
Local Repository   — .git/ folder: all history, branches, objects
Remote Repository  — GitHub/GitLab: shared repo, one or more remotes

Git stores snapshots (not diffs). Each commit points to a tree of blobs.
Every object is addressed by SHA-1 hash of its content.
```

### Essential Commands
```bash
# Initialize and clone
git init                              # create new repo in current dir
git init --bare repo.git              # server-side repo (no working dir)
git clone https://github.com/org/repo.git
git clone --depth 1 url              # shallow clone (only latest commit)
git clone --branch main --single-branch url

# Stage and commit
git status                            # show working tree status
git diff                              # unstaged changes
git diff --staged                     # staged changes (what will be committed)
git add file.py                       # stage specific file
git add -p                            # interactively stage hunks
git add .                             # stage all changes in current dir
git commit -m "feat: add user auth"
git commit --amend                    # modify last commit (NEVER for pushed commits)

# History
git log --oneline --graph --all       # visual branch graph
git log -10 --stat                    # last 10 commits with file stats
git log --follow -- path/to/file      # history including renames
git show abc1234                      # show specific commit

# Remote
git remote -v                         # list remotes
git remote add origin https://...
git fetch origin                      # download remote changes, don't merge
git pull origin main                  # fetch + merge
git pull --rebase origin main         # fetch + rebase (cleaner history)
git push origin feature/auth          # push branch
git push -u origin feature/auth       # push and set upstream
git push --force-with-lease           # safer force push (fails if remote changed)
```

### Branching
```bash
# Branches are just pointers to commits
git branch                            # list local branches
git branch -a                         # list all (including remote)
git branch feature/login              # create branch at current HEAD
git checkout feature/login            # switch to branch (older syntax)
git switch feature/login              # switch (newer syntax)
git switch -c feature/login           # create and switch
git branch -d feature/login           # delete (safe — warns if not merged)
git branch -D feature/login           # force delete
git branch -m old-name new-name       # rename branch

# See what's been merged
git branch --merged main              # branches merged into main
git branch --no-merged main           # branches NOT merged into main
```

### Merging vs Rebasing
```bash
# Merge — preserves history, creates merge commit
git switch main
git merge feature/login
# Result: --o--o--o--M  (M = merge commit)
#              \---o--/

# Fast-forward merge (no divergence)
git merge --ff-only feature/login     # fail if not fast-forwardable

# Squash merge — combine feature branch into single commit on main
git merge --squash feature/login
git commit -m "feat: add login feature"

# Rebase — replays commits on top of target (linear history)
git switch feature/login
git rebase main
# Result: main--o--o--o--o'--o'  (o' = rebased commits, new SHA)
# Then fast-forward merge on main

# Interactive rebase — squash, reorder, edit commits
git rebase -i HEAD~3                  # edit last 3 commits
# pick abc1234 first commit
# squash def5678 second commit        ← squash into previous
# reword ghi9012 third commit         ← edit message

# Golden rule: NEVER rebase commits that have been pushed to shared branches
```

### Cherry-Pick, Bisect, Stash
```bash
# Cherry-pick — apply specific commits to current branch
git cherry-pick abc1234               # apply single commit
git cherry-pick abc1234..ghi9012      # apply range

# Bisect — binary search for commit that introduced a bug
git bisect start
git bisect bad                        # current commit is bad
git bisect good v1.2.0                # v1.2.0 was good
# Git checks out middle commit — test it, then:
git bisect bad                        # or: git bisect good
# Repeat until: "abc1234 is the first bad commit"
git bisect reset                      # restore HEAD

# Automated bisect
git bisect run python test_suite.py  # auto bisect using script exit code

# Stash — temporarily shelve changes
git stash                             # stash all tracked changes
git stash push -m "WIP: login form" --include-untracked
git stash list
git stash pop                         # apply and remove latest stash
git stash apply stash@{2}            # apply specific stash, keep it
git stash drop stash@{0}             # delete specific stash
git stash branch feature/from-stash  # create branch from stash
```

### Tags
```bash
git tag v1.2.0                        # lightweight tag (just a pointer)
git tag -a v1.2.0 -m "Release v1.2.0" # annotated tag (has metadata)
git tag -a v1.2.0 abc1234            # tag specific commit
git push origin v1.2.0              # push specific tag
git push origin --tags              # push all tags
git tag -d v1.2.0                   # delete local tag
git push origin :refs/tags/v1.2.0   # delete remote tag
```

### Conventional Commits
```
Format: <type>[optional scope]: <description>

Types:
  feat:     new feature (triggers MINOR version bump in semver)
  fix:      bug fix (triggers PATCH version bump)
  docs:     documentation only
  style:    formatting, whitespace (no logic change)
  refactor: code restructure (no feature or fix)
  perf:     performance improvement
  test:     adding or fixing tests
  build:    build system, dependencies
  ci:       CI configuration files
  chore:    other maintenance

Examples:
  feat(auth): add OAuth2 login with Google
  fix(api): correct pagination offset calculation
  feat!: change default response format to JSON  (! = breaking change)

BREAKING CHANGE: include "BREAKING CHANGE:" footer or ! after type
```

### Git Hooks
```bash
# .git/hooks/ — scripts that run at lifecycle points
# Client-side hooks:
pre-commit      — runs before commit (lint, test, format)
commit-msg      — validate commit message format
pre-push        — runs before push (integration tests)

# Make executable
chmod +x .git/hooks/pre-commit

# Example pre-commit hook
#!/bin/bash
set -e
echo "Running linter..."
ruff check .
echo "Running type check..."
mypy src/
echo "Running tests..."
pytest -x -q
echo "All checks passed!"

# husky — manage hooks via npm for JS projects
npm install --save-dev husky
npx husky init
echo "npm test" > .husky/pre-commit
```

## Docker

### Core Concepts
```
Image     — read-only template with app + dependencies (built from Dockerfile)
Container — running instance of an image (writable layer on top)
Registry  — storage for images (Docker Hub, GHCR, AWS ECR)
Volume    — persistent storage outside container filesystem
Network   — isolated communication between containers
Layer     — each Dockerfile instruction creates a cached layer
```

### Dockerfile Best Practices
```dockerfile
# Use specific version tags, not :latest
FROM python:3.12-slim

# Set working directory early
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system deps first (changes rarely → cache stays valid longer)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*  # clean up in same layer to avoid bloat

# Copy dependency files first — Docker caches this layer
# Only invalidated when requirements change
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install uv && uv sync --frozen --no-dev

# Copy source code last (changes most frequently)
COPY src/ ./src/
COPY main.py ./

# Switch to non-root user
USER appuser

# Expose port (documentation only — doesn't actually open port)
EXPOSE 8000

# ENTRYPOINT: command that always runs
# CMD: default arguments (can be overridden)
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-Stage Builds
Dramatically reduce final image size by separating build and runtime stages.

```dockerfile
# Stage 1: Build stage — has all dev tools
FROM python:3.12 AS builder

WORKDIR /build

RUN pip install uv

COPY pyproject.toml uv.lock ./
# Install all deps including dev (for building wheels, compiling)
RUN uv sync --frozen

COPY src/ ./src/
RUN python -m build --wheel

# Stage 2: Runtime stage — minimal
FROM python:3.12-slim AS runtime

WORKDIR /app

# Only copy what's needed from builder
COPY --from=builder /build/dist/*.whl ./
COPY --from=builder /build/.venv ./venv

RUN pip install *.whl && rm *.whl

ENV PATH="/app/venv/bin:$PATH"

RUN groupadd -r app && useradd -r -g app app
USER app

EXPOSE 8000
CMD ["uvicorn", "myapp:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Go multi-stage (binary is standalone — very small final image)
FROM golang:1.23 AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o server ./cmd/server

FROM scratch AS runtime  # literally empty image
COPY --from=builder /build/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### docker-compose
```yaml
# docker-compose.yml
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:secret@db:5432/sidix
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env.local
    volumes:
      - ./uploads:/app/uploads  # bind mount for development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    networks:
      - backend

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: sidix
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    networks:
      - backend

volumes:
  postgres_data:
  redis_data:

networks:
  backend:
    driver: bridge
```

```bash
# Common docker-compose commands
docker compose up -d               # start all services in background
docker compose up -d --build       # rebuild images before starting
docker compose down                # stop and remove containers
docker compose down -v             # also remove volumes
docker compose logs -f app         # follow logs for specific service
docker compose exec app bash       # interactive shell in container
docker compose ps                  # list running services
docker compose scale app=3         # scale service to 3 instances
```

### Useful Docker Commands
```bash
# Images
docker build -t myapp:1.0 .
docker build -t myapp:1.0 --target runtime .   # specific stage
docker images                                   # list images
docker rmi myapp:1.0                           # remove image
docker pull python:3.12-slim                   # pull from registry
docker push ghcr.io/org/myapp:1.0             # push to registry

# Containers
docker run -d -p 8000:8000 --name sidix myapp:1.0
docker run --rm -it python:3.12-slim bash      # ephemeral interactive
docker ps                                      # running containers
docker ps -a                                   # all containers
docker stop sidix
docker rm sidix
docker exec -it sidix bash                    # shell inside running container
docker logs sidix -f --tail 100              # follow logs

# Cleanup
docker system prune -f                         # remove unused: containers, networks, images
docker volume prune -f                         # remove unused volumes
docker image prune -a -f                      # remove all unused images
```

## Linux / Bash

### File System Navigation
```bash
pwd                        # print working directory
ls -la                     # list all files with permissions
ls -lhS                    # sort by size, human readable
cd -                       # go to previous directory
tree -L 2                  # directory tree, 2 levels deep

# File permissions: rwxrwxrwx (owner, group, others)
chmod 755 script.sh        # rwx r-x r-x
chmod +x script.sh         # add execute permission
chmod -R 644 /var/www/html # recursive, files
chown -R www-data:www-data /var/www/html  # change owner:group

# Find files
find /var/log -name "*.log" -mtime +7 -delete  # delete logs older than 7 days
find . -type f -size +100M                      # files larger than 100MB
find . -name "*.py" -not -path "*/venv/*"      # exclude directory
```

### Text Processing: grep, sed, awk
```bash
# grep — search
grep "ERROR" app.log                 # find lines with ERROR
grep -r "TODO" ./src --include="*.py"  # recursive, specific extension
grep -n "def main" *.py              # show line numbers
grep -v "DEBUG" app.log              # invert: exclude DEBUG
grep -c "ERROR" app.log              # count matching lines
grep -E "ERROR|WARN" app.log         # extended regex (OR)
grep -A 3 "Exception" app.log        # 3 lines after match
grep -B 2 -A 5 "Traceback" app.log  # context around match

# sed — stream editor
sed 's/foo/bar/' file.txt            # replace first occurrence per line
sed 's/foo/bar/g' file.txt           # replace all occurrences
sed -i 's/localhost/0.0.0.0/g' config.py  # in-place edit
sed -n '10,20p' file.txt             # print lines 10-20
sed '/^#/d' config.txt               # delete comment lines
sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/' dates.txt  # reorder date

# awk — pattern scanning and processing
awk '{print $1, $3}' file.txt                # print columns 1 and 3
awk -F: '{print $1}' /etc/passwd             # use : as delimiter
awk 'NR==5' file.txt                         # print line 5
awk '/ERROR/ {print $0}' app.log             # print lines matching pattern
awk '{sum += $5} END {print "Total:", sum}' data.csv  # sum column 5
awk 'NR>1 {print $0}' file.csv              # skip header line

# Combining with pipes
cat app.log | grep "ERROR" | awk '{print $1, $2}' | sort | uniq -c | sort -rn | head -20
```

### Process Management
```bash
# View processes
ps aux                     # all processes (BSD style)
ps aux | grep python       # filter
top                        # interactive process viewer
htop                       # improved top (may need install)

# Background jobs
command &                  # run in background
jobs                       # list background jobs
fg %1                      # bring job 1 to foreground
bg %1                      # resume job 1 in background
nohup command &            # run immune to hangup (continues after logout)

# Kill processes
kill 1234                  # send SIGTERM (graceful shutdown)
kill -9 1234               # send SIGKILL (force kill)
pkill -f "python app.py"   # kill by command pattern
killall nginx              # kill all processes named nginx

# Process signals
SIGTERM (15) — graceful shutdown (application can clean up)
SIGKILL (9)  — immediate kill (cannot be caught)
SIGHUP  (1)  — hangup / reload config
SIGINT  (2)  — Ctrl+C

# systemd service management
systemctl status nginx
systemctl start nginx
systemctl stop nginx
systemctl restart nginx
systemctl reload nginx          # reload config without restart
systemctl enable nginx          # start on boot
systemctl disable nginx
journalctl -u nginx -f          # follow systemd logs for service
journalctl --since "1 hour ago"
```

### SSH
```bash
# Basic connection
ssh user@hostname
ssh -p 2222 user@hostname        # non-default port
ssh -i ~/.ssh/mykey.pem user@host  # specific key

# Key generation
ssh-keygen -t ed25519 -C "my comment"     # modern algorithm (preferred)
ssh-keygen -t rsa -b 4096 -C "my comment" # RSA legacy

# Copy public key to server
ssh-copy-id user@hostname
# or manually: cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# SSH config (~/.ssh/config)
Host dev-server
    HostName 10.0.0.100
    User ubuntu
    IdentityFile ~/.ssh/dev_key
    Port 22
    ServerAliveInterval 60

# Now just: ssh dev-server

# Tunneling
ssh -L 5432:localhost:5432 user@remote   # local port forward (access remote DB locally)
ssh -R 8080:localhost:8080 user@remote   # remote port forward
ssh -N -f -L 5432:db-host:5432 user@bastion  # background tunnel, no shell

# SCP / RSYNC
scp -r local/path user@host:/remote/path
rsync -avz --progress local/ user@host:/remote/  # incremental sync
rsync -avz --exclude="*.pyc" --exclude=".git" src/ user@host:/app/
```

### Cron Jobs
```bash
# Edit crontab
crontab -e        # edit current user's crontab
crontab -l        # list crontab
crontab -r        # remove crontab

# Cron syntax: minute hour day month weekday command
# * = any value, */5 = every 5, 1-5 = range, 1,3,5 = list

0  * * * *  /usr/bin/python3 /app/hourly.py         # every hour at :00
30 2 * * *  /usr/bin/pg_dump sidix > /backup.sql    # 2:30 AM daily
0  0 * * 1  /app/weekly-report.sh                   # midnight Monday
*/5 * * * * curl -fs http://localhost:8000/health || systemctl restart myapp

# Redirect output (cron doesn't have PATH by default — use full paths)
*/10 * * * * /full/path/to/script.sh >> /var/log/script.log 2>&1

# Useful shortcuts
@reboot    — run once at startup
@daily     — equivalent to 0 0 * * *
@weekly    — equivalent to 0 0 * * 0
@monthly   — equivalent to 0 0 1 * *
@hourly    — equivalent to 0 * * * *
```

### Environment Variables
```bash
# Set and export
export DATABASE_URL="postgresql://user:pass@localhost/db"
export -p              # show all exported variables
printenv               # show all environment variables
printenv PATH

# Source a file to load vars into current shell
source .env            # or: . .env
export $(cat .env | grep -v '^#' | xargs)  # export from .env file

# .env file format
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=super-secret-key
DEBUG=false

# Temporary variables (only for one command)
DATABASE_URL=test_db python manage.py test

# Check if variable is set
if [ -z "${DATABASE_URL}" ]; then
    echo "DATABASE_URL is not set"
    exit 1
fi

# Default value if unset
PORT="${PORT:-8000}"
```

### Bash Scripting Patterns
```bash
#!/usr/bin/env bash
set -euo pipefail   # exit on error, unbound var, pipe failures
IFS=$'\n\t'         # safer word splitting

# Functions
log() {
    echo "[$(date +%Y-%m-%dT%H:%M:%S)] $*" >&2
}

die() {
    log "ERROR: $*"
    exit 1
}

# Argument parsing
VERBOSE=false
OUTPUT_DIR="/tmp/output"

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -v|--verbose) VERBOSE=true ;;
        -o|--output) OUTPUT_DIR="$2"; shift ;;
        -h|--help) echo "Usage: $0 [-v] [-o dir]"; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
    shift
done

# Array operations
files=("a.txt" "b.txt" "c.txt")
for f in "${files[@]}"; do
    log "Processing $f"
done

# String operations
filename="/path/to/file.tar.gz"
basename "$filename"          # file.tar.gz
dirname "$filename"           # /path/to
extension="${filename##*.}"   # gz
without_ext="${filename%.*}"  # /path/to/file.tar

# Conditionals
if [[ -f "$file" ]]; then echo "file exists"; fi
if [[ -d "$dir" ]]; then echo "is directory"; fi
if [[ "$var" == "value" ]]; then echo "match"; fi
if [[ "$count" -gt 10 ]]; then echo "greater than 10"; fi

# Process substitution
diff <(sort file1.txt) <(sort file2.txt)
```

## Referensi & Sumber Lanjut
- https://git-scm.com/book/en/v2 — Pro Git (free, comprehensive)
- https://docs.docker.com/
- https://docs.docker.com/compose/
- https://www.conventionalcommits.org/
- https://www.shellcheck.net/ — Bash script linter
- https://explainshell.com/ — explains any shell command
- https://linuxcommand.org/
- roadmap.sh/git-github
- roadmap.sh/docker
- roadmap.sh/linux
