#!/usr/bin/env node
/**
 * HYPERX MCP Server
 * Exposes browser tools via Model Context Protocol (stdio transport)
 * 
 * Add to Claude / Cursor / VS Code:
 * {
 *   "mcpServers": {
 *     "hyperx": {
 *       "command": "node",
 *       "args": ["/path/to/hyperx-browser/bin/hyperx-mcp.js"]
 *     }
 *   }
 * }
 */

import { HyperXEngine } from '../src/engine.js'
import { writeFileSync, readFileSync } from 'fs'
import dns from 'dns'
dns.setDefaultResultOrder('ipv4first')  // Day 48: container has no IPv6 route

const engine = new HyperXEngine()

// --- MCP Protocol (stdio JSON-RPC) ---
function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n')
}

function ok(id, result) {
  send({ jsonrpc: '2.0', id, result })
}

function err(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } })
}

// Tool definitions
const TOOLS = [
  {
    name: 'hyperx_get',
    description: 'Fetch and render a webpage anonymously. Returns title, text content, links, images, metadata, and status code.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to fetch (must start with http/https)' },
        raw: { type: 'boolean', description: 'Return raw HTML instead of parsed text' },
      },
      required: ['url'],
    },
  },
  {
    name: 'hyperx_search',
    description: 'Search the web using any search engine. Returns structured results with title, URL, and snippet.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        engine: {
          type: 'string',
          enum: ['google', 'ddg', 'brave', 'bing', 'startpage', 'yandex', 'ecosia'],
          description: 'Search engine to use (default: configured engine)',
        },
        limit: { type: 'number', description: 'Max results to return (default: all)' },
      },
      required: ['query'],
    },
  },
  {
    name: 'hyperx_scrape',
    description: 'Scrape a webpage and extract structured data using regex patterns on the HTML.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to scrape' },
        selectors: {
          type: 'object',
          description: 'Key-value map of { fieldName: "regex pattern" } to extract from HTML',
          additionalProperties: { type: 'string' },
        },
      },
      required: ['url'],
    },
  },
  {
    name: 'hyperx_download',
    description: 'Download a file from a URL anonymously. Saves to downloads directory.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL of file to download' },
        filename: { type: 'string', description: 'Optional filename to save as (in downloads dir)' },
      },
      required: ['url'],
    },
  },
  {
    name: 'hyperx_post',
    description: 'Send an HTTP POST request to a URL with form data or JSON.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to POST to' },
        body: { type: 'object', description: 'Key-value pairs to send as form data' },
        json: { type: 'boolean', description: 'If true, send as JSON instead of form-encoded' },
      },
      required: ['url', 'body'],
    },
  },
  {
    name: 'hyperx_crawl',
    description: 'Crawl a website starting from a URL, following links. Returns page titles, URLs, and link counts.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'Start URL to crawl from' },
        maxPages: { type: 'number', description: 'Maximum pages to crawl (default: 10, max: 50)' },
        sameOrigin: { type: 'boolean', description: 'Only follow links on the same domain (default: true)' },
      },
      required: ['url'],
    },
  },
  {
    name: 'hyperx_history',
    description: 'Get browser history of previously visited pages and searches.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Number of history entries to return (default: 50)' },
        filter: { type: 'string', description: 'Filter by type: "page" or "search"' },
      },
    },
  },
  {
    name: 'hyperx_links',
    description: 'Get all links from a webpage.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL to extract links from' },
        filter: { type: 'string', description: 'Optional text filter for link text or URL' },
      },
      required: ['url'],
    },
  },
  {
    name: 'hyperx_config',
    description: 'Get or update HyperX browser configuration (engine, proxy, anonymity settings, timeout, etc).',
    inputSchema: {
      type: 'object',
      properties: {
        get: { type: 'boolean', description: 'If true, return current config' },
        set: {
          type: 'object',
          description: 'Key-value config updates to apply',
          additionalProperties: {},
        },
      },
    },
  },
  {
    name: 'hyperx_multi',
    description: 'Fetch multiple URLs in parallel (up to 10). Returns array of results.',
    inputSchema: {
      type: 'object',
      properties: {
        urls: {
          type: 'array',
          items: { type: 'string' },
          description: 'Array of URLs to fetch (max 10)',
        },
        raw: { type: 'boolean', description: 'Return raw HTML' },
      },
      required: ['urls'],
    },
  },
]

async function callTool(name, args) {
  switch (name) {
    case 'hyperx_get': {
      const page = await engine.get(args.url)
      if (args.raw) return { url: page.url, status: page.status, html: page.html, elapsed: page.elapsed }
      return {
        url: page.url,
        finalUrl: page.finalUrl,
        status: page.status,
        title: page.meta.title,
        description: page.meta.description,
        text: page.text.slice(0, 8000),
        textTruncated: page.text.length > 8000,
        links: page.links.slice(0, 50),
        images: page.images.slice(0, 20),
        elapsed: page.elapsed,
        size: page.size,
      }
    }

    case 'hyperx_search': {
      const res = await engine.search(args.query, args.engine)
      let results = res.results
      if (args.limit) results = results.slice(0, args.limit)
      return { query: res.query, engine: res.engine, results, total: res.total, elapsed: res.elapsed }
    }

    case 'hyperx_scrape': {
      const res = await engine.scrape(args.url, args.selectors || {})
      return {
        url: res.url,
        meta: res.meta,
        extracted: res.extracted,
        links: res.links.slice(0, 30),
        images: res.images.slice(0, 20),
        text: res.text.slice(0, 4000),
      }
    }

    case 'hyperx_download': {
      const cfg = engine.getConfig()
      let dest = null
      if (args.filename) dest = `${cfg.downloadDir}/${args.filename}`
      const result = await engine.download(args.url, dest)
      return { filename: result.filename, size: result.size, contentType: result.contentType }
    }

    case 'hyperx_post': {
      const ct = args.json ? 'application/json' : 'application/x-www-form-urlencoded'
      const page = await engine.post(args.url, args.body, ct)
      return { url: page.url, status: page.status, title: page.meta.title, text: page.text.slice(0, 4000) }
    }

    case 'hyperx_crawl': {
      const maxPages = Math.min(args.maxPages || 10, 50)
      const res = await engine.crawl(args.url, { maxPages, sameOrigin: args.sameOrigin !== false })
      return res
    }

    case 'hyperx_history': {
      let hist = engine.history(args.limit || 50)
      if (args.filter) hist = hist.filter(h => h.type === args.filter)
      return { count: hist.length, items: hist }
    }

    case 'hyperx_links': {
      const page = await engine.get(args.url)
      let links = page.links
      if (args.filter) {
        const f = args.filter.toLowerCase()
        links = links.filter(l => l.url.toLowerCase().includes(f) || l.text.toLowerCase().includes(f))
      }
      return { url: args.url, count: links.length, links }
    }

    case 'hyperx_config': {
      if (args.get || !args.set) return engine.getConfig()
      if (args.set) engine.setConfig(args.set)
      return { updated: args.set, config: engine.getConfig() }
    }

    case 'hyperx_multi': {
      const urls = (args.urls || []).slice(0, 10)
      const results = await Promise.allSettled(urls.map(url => engine.get(url)))
      return results.map((r, i) => {
        if (r.status === 'rejected') return { url: urls[i], error: r.reason.message }
        const p = r.value
        return args.raw
          ? { url: p.url, status: p.status, html: p.html }
          : { url: p.url, status: p.status, title: p.meta.title, text: p.text.slice(0, 2000), links: p.links.slice(0,10), elapsed: p.elapsed }
      })
    }

    default:
      throw new Error(`Unknown tool: ${name}`)
  }
}

// MCP main loop
let buffer = ''
process.stdin.setEncoding('utf8')
process.stdin.on('data', async (chunk) => {
  buffer += chunk
  const lines = buffer.split('\n')
  buffer = lines.pop()
  for (const line of lines) {
    if (!line.trim()) continue
    let msg
    try { msg = JSON.parse(line) } catch { continue }

    const { id, method, params } = msg

    if (method === 'initialize') {
      ok(id, {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'hyperx-browser', version: '1.0.0' },
      })
    } else if (method === 'tools/list') {
      ok(id, { tools: TOOLS })
    } else if (method === 'tools/call') {
      const { name, arguments: args } = params
      try {
        const result = await callTool(name, args || {})
        ok(id, {
          content: [{ type: 'text', text: typeof result === 'string' ? result : JSON.stringify(result, null, 2) }],
        })
      } catch (e) {
        ok(id, {
          content: [{ type: 'text', text: `Error: ${e.message}` }],
          isError: true,
        })
      }
    } else if (method === 'ping') {
      ok(id, {})
    } else if (method === 'notifications/initialized') {
      // no response needed
    } else {
      err(id, -32601, `Method not found: ${method}`)
    }
  }
})

process.stdin.on('end', () => process.exit(0))
process.stderr.write('[hyperx-mcp] MCP server ready (stdio)\n')
