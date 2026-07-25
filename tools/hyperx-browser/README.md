# HYPERX Browser

Ultra-light anonymous CLI browser. No Electron. No Chrome. No tracking. Pure Node.js.

## Install

```bash
npm install
chmod +x bin/hyperx.js bin/hyperx-mcp.js bin/hyperx-daemon.js

# Optional: global install
npm link
```

## Usage

### Interactive REPL
```bash
node bin/hyperx.js
# or: hyperx
```

### One-shot CLI
```bash
# Fetch a page
hyperx https://example.com

# Search
hyperx "cara buat nasi goreng"

# Search with specific engine
hyperx --engine=ddg "python tutorial"

# Get raw HTML
hyperx --raw https://example.com

# Extract links only
hyperx --links https://example.com

# Output JSON
hyperx --json https://example.com

# Download a file
hyperx --download https://example.com/file.pdf

# Save output to file
hyperx --output=result.txt https://example.com

# POST request
hyperx --post="user=admin&pass=test" https://example.com/login
```

### REPL Commands
```
go <url>           fetch & render page
search <query>     search the web
post <url> <data>  HTTP POST
dl <url>           download file
links              show links from last page
images             show images from last page
raw                show raw HTML
crawl <url>        crawl site (max 10 pages)
history [n]        show browse history
clearhistory       clear all history
engine <name>      switch engine
proxy <url>        set proxy
config             show config
set <key> <val>    update config
save [file]        save page to file
open <n>           open link #n from results
back / fwd         navigate history
json               show last result as JSON
quit               exit
```

### Search Engines
- `google` - Google (default)
- `ddg` - DuckDuckGo (more private)
- `brave` - Brave Search
- `bing` - Bing
- `startpage` - Startpage (anonymous Google)
- `yandex` - Yandex
- `ecosia` - Ecosia

## Background Daemon

```bash
# Start daemon in background
node bin/hyperx-daemon.js &

# Submit jobs via JSONL queue
echo '{"id":"job1","type":"search","query":"berita hari ini"}' >> config/queue.jsonl
echo '{"id":"job2","type":"fetch","url":"https://example.com"}' >> config/queue.jsonl
echo '{"id":"job3","type":"download","url":"https://example.com/file.pdf"}' >> config/queue.jsonl
echo '{"id":"job4","type":"crawl","url":"https://example.com","maxPages":5}' >> config/queue.jsonl
echo '{"id":"job5","type":"multi","urls":["https://a.com","https://b.com"]}' >> config/queue.jsonl

# Check results
cat config/results/job1.json

# Stop daemon
kill $(cat config/daemon.pid)
```

## MCP Server (Claude / Cursor / VS Code)

Add to your MCP config:

```json
{
  "mcpServers": {
    "hyperx": {
      "command": "node",
      "args": ["/absolute/path/to/hyperx-browser/bin/hyperx-mcp.js"]
    }
  }
}
```

### Available MCP Tools
| Tool | Description |
|------|-------------|
| `hyperx_get` | Fetch & parse a webpage |
| `hyperx_search` | Search any engine |
| `hyperx_scrape` | Scrape with regex patterns |
| `hyperx_download` | Download files |
| `hyperx_post` | HTTP POST requests |
| `hyperx_crawl` | Crawl a website |
| `hyperx_links` | Extract all links from page |
| `hyperx_multi` | Fetch multiple URLs in parallel |
| `hyperx_history` | Get browse history |
| `hyperx_config` | Get/update config |

### MCP Example (from AI agent)
```
hyperx_search(query="best python frameworks 2024", engine="ddg", limit=10)
hyperx_get(url="https://fastapi.tiangolo.com")
hyperx_scrape(url="https://example.com", selectors={"emails": "[a-z0-9.]+@[a-z0-9.]+\\.[a-z]+"})
hyperx_multi(urls=["https://a.com", "https://b.com", "https://c.com"])
hyperx_crawl(url="https://docs.example.com", maxPages=20)
```

## Config

Edit `config/config.json`:

```json
{
  "anonymous": true,
  "rotateUA": true,
  "timeout": 15000,
  "maxRetries": 3,
  "downloadDir": "./downloads",
  "proxy": null,
  "stripCookies": true,
  "stripTrackers": true,
  "compress": true,
  "jsDisabled": true,
  "searchEngine": "google"
}
```

### Proxy Support
```bash
# In REPL
hyperx> proxy http://127.0.0.1:8080
hyperx> proxy socks5://127.0.0.1:1080

# Via config
set proxy http://127.0.0.1:8080
```

## Anonymity Features

- Random User-Agent rotation from pool (Firefox, Chrome, Safari, curl, Python, etc.)
- No cookies sent by default (`stripCookies: true`)
- Tracking params stripped (utm_*, fbclid, gclid, etc.)
- DNT header always set
- No Referer header sent (anonymous navigation)
- No persistent session / fingerprinting
- Proxy-ready (HTTP, SOCKS5)

## Architecture

```
hyperx-browser/
├── bin/
│   ├── hyperx.js        ← CLI REPL + one-shot mode
│   ├── hyperx-mcp.js    ← MCP stdio server
│   └── hyperx-daemon.js ← Background queue processor
├── src/
│   └── engine.js        ← Core: fetch, parse, search, download
├── config/
│   ├── config.json      ← Settings
│   ├── history.json     ← Browse history
│   ├── queue.jsonl      ← Daemon job queue
│   └── results/         ← Daemon job results
└── downloads/           ← Downloaded files
```
