/**
 * HYPERX Browser Engine
 * Anonymous-first, ultra-light, scrape-friendly
 */

import { createWriteStream, mkdirSync, existsSync, readFileSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { pipeline } from 'stream/promises'
import { createRequire } from 'module'
import * as cheerio from 'cheerio'

const __dirname = dirname(fileURLToPath(import.meta.url))
const HISTORY_FILE = join(__dirname, '../config/history.json')
const CONFIG_FILE = join(__dirname, '../config/config.json')

// Ensure config dir exists
if (!existsSync(join(__dirname, '../config'))) mkdirSync(join(__dirname, '../config'), { recursive: true })
if (!existsSync(join(__dirname, '../downloads'))) mkdirSync(join(__dirname, '../downloads'), { recursive: true })

// --- USER AGENT POOL (rotate for anonymity) ---
const UA_POOL = [
  'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
  'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 Gecko/20100101 Firefox/119.0',
  'Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1',
  'curl/7.88.1',
  'python-requests/2.31.0',
  'Go-http-client/2.0',
]

function randomUA() {
  return UA_POOL[Math.floor(Math.random() * UA_POOL.length)]
}

// --- CONFIG ---
function loadConfig() {
  try {
    return JSON.parse(readFileSync(CONFIG_FILE, 'utf8'))
  } catch {
    return {
      anonymous: true,
      rotateUA: true,
      timeout: 15000,
      maxRetries: 3,
      downloadDir: join(__dirname, '../downloads'),
      proxy: null,        // 'http://host:port' or 'socks5://host:port'
      stripCookies: true,
      stripTrackers: true,
      compress: true,
      jsDisabled: true,   // we render server-side only
      searchEngine: 'google',
      engines: {
        google: 'https://www.google.com/search?q={q}&num=20',
        ddg: 'https://html.duckduckgo.com/html/?q={q}',
        brave: 'https://search.brave.com/search?q={q}',
        bing: 'https://www.bing.com/search?q={q}',
        startpage: 'https://www.startpage.com/do/search?q={q}',
        yandex: 'https://yandex.com/search/?text={q}',
        ecosia: 'https://www.ecosia.org/search?q={q}',
      }
    }
  }
}

function saveConfig(cfg) {
  writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2))
}

// --- HISTORY ---
function loadHistory() {
  try {
    return JSON.parse(readFileSync(HISTORY_FILE, 'utf8'))
  } catch {
    return []
  }
}

function appendHistory(entry) {
  const h = loadHistory()
  h.unshift({ ...entry, id: Math.random().toString(36).slice(2), time: Date.now() })
  if (h.length > 2000) h.splice(2000)
  writeFileSync(HISTORY_FILE, JSON.stringify(h, null, 2))
}

function clearHistory() {
  writeFileSync(HISTORY_FILE, '[]')
}

// --- TRACKER / ANALYTICS STRIP ---
const TRACKER_PATTERNS = [
  /[?&](utm_source|utm_medium|utm_campaign|utm_term|utm_content|fbclid|gclid|mc_eid|ref|affiliate)[^&]*/gi,
  /#.*$/,  // strip anchors by default unless needed
]

function stripTrackers(url) {
  let u = url
  TRACKER_PATTERNS.forEach(p => { u = u.replace(p, '') })
  u = u.replace(/[?&]+$/, '')
  return u
}

// --- HEADERS BUILDER (anonymous-first) ---
function buildHeaders(cfg, extra = {}) {
  const ua = cfg.rotateUA ? randomUA() : UA_POOL[0]
  const base = {
    'User-Agent': ua,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'no-cache',
    'DNT': '1',
    'Pragma': 'no-cache',
  }
  // Never send referer unless explicitly given (anonymous)
  if (extra.referer) base['Referer'] = extra.referer
  // Strip identifying headers
  if (cfg.anonymous) {
    delete base['X-Forwarded-For']
    delete base['X-Real-IP']
  }
  return { ...base, ...extra }
}

// --- CORE FETCH (with retry + timeout) ---
async function fetchUrl(url, cfg, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), cfg.timeout || 15000)

  const fetchOpts = {
    method: options.method || 'GET',
    headers: buildHeaders(cfg, options.headers || {}),
    signal: controller.signal,
    redirect: 'follow',
  }

  if (options.body) fetchOpts.body = options.body

  try {
    const res = await fetch(url, fetchOpts)
    clearTimeout(timer)
    return res
  } catch (err) {
    clearTimeout(timer)
    throw err
  }
}

// --- HTML -> TEXT/MARKDOWN ---
function htmlToText(html) {
  // Remove scripts, styles, nav, footer, ads
  let text = html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<nav[\s\S]*?<\/nav>/gi, '')
    .replace(/<footer[\s\S]*?<\/footer>/gi, '')
    .replace(/<header[\s\S]*?<\/header>/gi, '')
    .replace(/<aside[\s\S]*?<\/aside>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    // Convert meaningful tags
    .replace(/<h([1-6])[^>]*>([\s\S]*?)<\/h\1>/gi, (_, l, t) => '\n' + '#'.repeat(+l) + ' ' + t.replace(/<[^>]+>/g,'').trim() + '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<p[^>]*>/gi, '\n')
    .replace(/<\/p>/gi, '\n')
    .replace(/<li[^>]*>/gi, '\n• ')
    .replace(/<\/li>/gi, '')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (_, href, txt) => `${txt.replace(/<[^>]+>/g,'')} [${href}]`)
    .replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, '**$1**')
    .replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, '_$1_')
    .replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, '`$1`')
    .replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, '\n```\n$1\n```\n')
    .replace(/<[^>]+>/g, '')
    // Decode entities
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')
    .replace(/&mdash;/g, '—').replace(/&ndash;/g, '–')
    // Collapse whitespace
    .replace(/\n{4,}/g, '\n\n\n')
    .replace(/[ \t]+/g, ' ')
    .trim()
  return text
}

function extractMeta(html) {
  const meta = {}
  const titleMatch = html.match(/<title[^>]*>([^<]*)<\/title>/i)
  if (titleMatch) meta.title = titleMatch[1].trim()
  const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']*)["']/i)
    || html.match(/<meta[^>]*content=["']([^"']*)["'][^>]*name=["']description["']/i)
  if (descMatch) meta.description = descMatch[1].trim()
  const canonMatch = html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']*)["']/i)
  if (canonMatch) meta.canonical = canonMatch[1].trim()
  return meta
}

function extractLinks(html, baseUrl) {
  const links = []
  const re = /<a[^>]*href=["']([^"'#][^"']*)["'][^>]*>([\s\S]*?)<\/a>/gi
  let m
  while ((m = re.exec(html)) !== null) {
    try {
      const url = new URL(m[1], baseUrl).href
      const text = m[2].replace(/<[^>]+>/g,'').trim()
      if (text && url.startsWith('http')) links.push({ url, text })
    } catch {}
  }
  return links.slice(0, 100)
}

function extractImages(html, baseUrl) {
  const imgs = []
  const re = /<img[^>]*src=["']([^"']*)["'][^>]*(?:alt=["']([^"']*)["'])?[^>]*>/gi
  let m
  while ((m = re.exec(html)) !== null) {
    try {
      const url = new URL(m[1], baseUrl).href
      imgs.push({ url, alt: m[2] || '' })
    } catch {}
  }
  return imgs.slice(0, 50)
}

// --- SEARCH RESULT PARSING ---
function parseGoogleResults(html) {
  const results = []
  // Google result blocks
  const blocks = html.match(/<div class="[^"]*tF2Cxc[^"]*"[\s\S]*?(?=<div class="[^"]*tF2Cxc|$)/g) || []
  blocks.forEach(block => {
    const urlM = block.match(/href="(https?:\/\/[^"]+)"/)
    const titleM = block.match(/<h3[^>]*>([^<]+)<\/h3>/)
    const snippetM = block.match(/<div[^>]*class="[^"]*VwiC3b[^"]*"[^>]*>([\s\S]*?)<\/div>/)
    if (urlM && titleM) {
      results.push({
        url: urlM[1],
        title: titleM[1].replace(/<[^>]+>/g,'').trim(),
        snippet: snippetM ? snippetM[1].replace(/<[^>]+>/g,'').trim() : '',
      })
    }
  })
  // Fallback: grab all h3 + nearby hrefs
  if (results.length === 0) {
    const fallback = html.match(/<a href="(https?:\/\/[^"&]+)"[^>]*>\s*<h3[^>]*>([^<]+)<\/h3>/g) || []
    fallback.forEach(f => {
      const u = f.match(/href="([^"]+)"/)
      const t = f.match(/<h3[^>]*>([^<]+)<\/h3>/)
      if (u && t) results.push({ url: u[1], title: t[1].trim(), snippet: '' })
    })
  }
  return results
}

function parseDDGResults(html) {
  const results = []
  const re = /<a class="result__a" href="([^"]+)"[^>]*>([\s\S]*?)<\/a>[\s\S]*?<a class="result__snippet"[^>]*>([\s\S]*?)<\/a>/g
  let m
  while ((m = re.exec(html)) !== null) {
    results.push({
      url: m[1],
      title: m[2].replace(/<[^>]+>/g,'').trim(),
      snippet: m[3].replace(/<[^>]+>/g,'').trim(),
    })
  }
  return results
}

function parseGenericResults(html, baseUrl) {
  const links = extractLinks(html, baseUrl)
  return links.filter(l => !l.url.includes(new URL(baseUrl).hostname)).slice(0, 20).map(l => ({
    url: l.url, title: l.text, snippet: ''
  }))
}

// --- MULTI-SOURCE SEARCH AGGREGATOR ---
// Uses only open/accessible APIs — no JS-required sites, no blocked endpoints

async function searchHackerNews(query, limit = 10) {
  const url = `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&hitsPerPage=${limit}`
  const res = await fetch(url, { headers: { 'User-Agent': 'HyperX/1.0' }, signal: AbortSignal.timeout(8000) })
  const data = await res.json()
  return (data.hits || []).map(h => ({
    url: h.url || `https://news.ycombinator.com/item?id=${h.objectID}`,
    title: h.title || h.story_title || '',
    snippet: h.comment_text?.replace(/<[^>]+>/g,'').slice(0, 200) || `HN Score: ${h.points} | ${h.num_comments} comments`,
    source: 'hackernews',
    date: h.created_at,
  })).filter(r => r.title && r.url)
}

async function searchGitHub(query, limit = 8) {
  const url = `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&per_page=${limit}&sort=stars`
  const res = await fetch(url, { headers: { 'User-Agent': 'HyperX/1.0', Accept: 'application/vnd.github.v3+json' }, signal: AbortSignal.timeout(8000) })
  const data = await res.json()
  return (data.items || []).map(r => ({
    url: r.html_url,
    title: `${r.full_name} ★${r.stargazers_count}`,
    snippet: r.description || '',
    source: 'github',
    date: r.updated_at,
  }))
}

async function searchOpenLibrary(query, limit = 5) {
  const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=${limit}&fields=title,author_name,key,first_publish_year`
  const res = await fetch(url, { headers: { 'User-Agent': 'HyperX/1.0' }, signal: AbortSignal.timeout(8000) })
  const data = await res.json()
  return (data.docs || []).map(d => ({
    url: `https://openlibrary.org${d.key}`,
    title: d.title + (d.first_publish_year ? ` (${d.first_publish_year})` : ''),
    snippet: d.author_name ? `By: ${d.author_name.slice(0,3).join(', ')}` : '',
    source: 'openlibrary',
  }))
}

async function searchWiby(query) {
  const url = `https://wiby.me/json/?q=${encodeURIComponent(query)}`
  const res = await fetch(url, { headers: { 'User-Agent': 'HyperX/1.0' }, signal: AbortSignal.timeout(8000) })
  const data = await res.json()
  return (Array.isArray(data) ? data : []).map(r => ({
    url: r.URL,
    title: r.Title?.replace(/&#34;/g,'"') || r.URL,
    snippet: r.Snippet?.replace(/&#34;/g,'"') || '',
    source: 'wiby',
  })).filter(r => r.url && r.title)
}


// --- Day 46 fix: real web-engine HTML search (DDG/Brave/Bing/Google/Startpage/Ecosia/Yandex)
// HYPERX previously had engines config but search() never used it (always fell
// through to HN+GitHub+Wiby). This adds proper HTML-scrape search per engine,
// using cheerio (already a dep). Falls back to multi-source if a layout breaks.
async function searchEngineHTML(query, engineKey, cfg) {
  const engineUrl = (cfg.engines || {})[engineKey]
  if (!engineUrl) throw new Error(`Unknown engine: ${engineKey}`)
  const url = engineUrl.replace('{q}', encodeURIComponent(query))
  const res = await fetchUrl(url, cfg)
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${engineKey}`)
  const html = await res.text()
  const $ = cheerio.load(html)
  const out = []
  const seen = new Set()

  function pushResult(title, link, snippet) {
    title = (title || '').trim().replace(/\s+/g, ' ')
    link = (link || '').trim()
    snippet = (snippet || '').trim().replace(/\s+/g, ' ').slice(0, 280)
    if (!title || !link || seen.has(link)) return
    if (!/^https?:\/\//.test(link)) return
    seen.add(link)
    out.push({ url: link, title, snippet, source: engineKey })
  }

  if (engineKey === 'ddg') {
    $('.result').each((_, el) => {
      const a = $(el).find('a.result__a, .result__title a').first()
      let href = a.attr('href') || ''
      const m = href.match(/[?&]uddg=([^&]+)/)
      if (m) href = decodeURIComponent(m[1])
      pushResult(a.text(), href, $(el).find('.result__snippet').text())
    })
  } else if (engineKey === 'bing') {
    $('#b_results > li.b_algo').each((_, el) => {
      const a = $(el).find('h2 a').first()
      pushResult(a.text(), a.attr('href'), $(el).find('.b_caption p').first().text())
    })
  } else if (engineKey === 'brave') {
    $('div.snippet, [data-type="web"] .snippet').each((_, el) => {
      const a = $(el).find('a').first()
      pushResult(
        $(el).find('.snippet-title, .title').first().text() || a.text(),
        a.attr('href'),
        $(el).find('.snippet-description, .description').first().text()
      )
    })
  } else if (engineKey === 'startpage') {
    $('.w-gl__result, section.w-gl__result').each((_, el) => {
      const a = $(el).find('a').first()
      pushResult(
        $(el).find('.w-gl__result-title h3').text() || a.text(),
        a.attr('href'),
        $(el).find('.w-gl__description').text()
      )
    })
  } else if (engineKey === 'ecosia') {
    $('div.result, article.result').each((_, el) => {
      const a = $(el).find('a.result-title, h2 a').first()
      pushResult(a.text(), a.attr('href'), $(el).find('.result__description, .result-description').text())
    })
  } else if (engineKey === 'yandex') {
    $('li.serp-item, .organic').each((_, el) => {
      const a = $(el).find('a.organic__url, h2 a').first()
      pushResult(a.text(), a.attr('href'), $(el).find('.organic__text, .extended-text').text())
    })
  } else if (engineKey === 'google') {
    $('div.g, div[data-sokoban-container]').each((_, el) => {
      const a = $(el).find('a').first()
      const h3 = $(el).find('h3').first()
      pushResult(h3.text(), a.attr('href'), $(el).find('.VwiC3b, .yXK7lf').text())
    })
  }

  return out.slice(0, 20)
}


async function searchWikipedia(query, lang = 'id', limit = 8) {
  // Wikipedia opensearch returns [query, [titles], [snippets], [urls]]
  // Try requested lang first, fallback to English if no results
  async function fetchLang(l) {
    const url = `https://${l}.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=${limit}&namespace=0&format=json`
    const res = await fetch(url, {
      headers: { 'User-Agent': 'HyperX/1.0 (https://migancore.com)' },
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) return []
    const data = await res.json()
    if (!Array.isArray(data) || data.length < 4) return []
    const [, titles, snippets, urls] = data
    return titles.map((t, i) => ({
      url: urls[i],
      title: t,
      snippet: snippets[i] || '',
      source: `wikipedia-${l}`,
    })).filter(r => r.url && r.title)
  }
  let out = await fetchLang(lang)
  if (out.length === 0 && lang !== 'en') out = await fetchLang('en')
  return out
}

async function searchMultiSource(query, sources = ['wikipedia', 'hn', 'github', 'wiby']) {
  const tasks = []
  if (sources.includes('hn')) tasks.push(searchHackerNews(query).catch(() => []))
  if (sources.includes('github')) tasks.push(searchGitHub(query).catch(() => []))
  if (sources.includes('books')) tasks.push(searchOpenLibrary(query).catch(() => []))
  if (sources.includes('wiby')) tasks.push(searchWiby(query).catch(() => []))
  if (sources.includes('wikipedia')) tasks.push(searchWikipedia(query, 'id').catch(() => []))
  const results = await Promise.all(tasks)
  // Interleave results from different sources
  const merged = []
  const maxLen = Math.max(...results.map(r => r.length))
  for (let i = 0; i < maxLen; i++) {
    results.forEach(arr => { if (arr[i]) merged.push(arr[i]) })
  }
  return merged
}

// --- DOWNLOAD ---
async function downloadFile(url, cfg, destPath) {
  const res = await fetchUrl(url, cfg)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const contentType = res.headers.get('content-type') || ''
  const contentDisp = res.headers.get('content-disposition') || ''
  // Figure out filename
  let filename = destPath
  if (!filename) {
    const cdMatch = contentDisp.match(/filename=["']?([^"';\n]+)["']?/i)
    if (cdMatch) filename = cdMatch[1].trim()
    else {
      const urlPath = new URL(url).pathname
      filename = urlPath.split('/').pop() || 'download'
    }
    filename = join(cfg.downloadDir, filename)
  }
  const dir = dirname(filename)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  const fileStream = createWriteStream(filename)
  await pipeline(res.body, fileStream)
  const size = (await import('fs')).statSync(filename).size
  return { filename, size, contentType }
}

// --- MAIN ENGINE API ---
export class HyperXEngine {
  constructor() {
    this.cfg = loadConfig()
  }

  // Fetch + parse a page
  async get(url, opts = {}) {
    const cleaned = this.cfg.stripTrackers ? stripTrackers(url) : url
    const t0 = Date.now()
    const res = await fetchUrl(cleaned, this.cfg, opts)
    const html = await res.text()
    const elapsed = Date.now() - t0
    const meta = extractMeta(html)
    const text = htmlToText(html)
    const links = extractLinks(html, cleaned)
    const images = extractImages(html, cleaned)

    appendHistory({
      url: cleaned,
      title: meta.title || cleaned,
      type: 'page',
      statusCode: res.status,
      elapsed,
    })

    return {
      url: cleaned,
      finalUrl: res.url,
      status: res.status,
      headers: Object.fromEntries(res.headers.entries()),
      meta,
      html,
      text,
      links,
      images,
      elapsed,
      size: html.length,
    }
  }

  // Search - multi-source aggregator + direct fetch fallback
  async search(query, engine) {
    engine = engine || this.cfg.searchEngine
    const t0 = Date.now()
    let results = []
    let url = `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}`

    if (engine === 'hn' || engine === 'hackernews') {
      results = await searchHackerNews(query, 20)
      url = `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}`
    } else if (engine === 'github') {
      results = await searchGitHub(query, 20)
      url = `https://github.com/search?q=${encodeURIComponent(query)}`
    } else if (engine === 'books') {
      results = await searchOpenLibrary(query, 20)
      url = `https://openlibrary.org/search?q=${encodeURIComponent(query)}`
    } else if (engine === 'wiby') {
      results = await searchWiby(query)
      url = `https://wiby.me/?q=${encodeURIComponent(query)}`
    } else if (engine === 'wikipedia' || engine === 'wiki' || engine === 'wp') {
      // Day 46: real Wikipedia search via opensearch API (id->en fallback)
      results = await searchWikipedia(query, 'id')
      url = `https://id.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(query)}`
    } else if (engine === 'multi' || engine === 'all') {
      results = await searchMultiSource(query, ['hn', 'github', 'wiby'])
      url = `multi:${query}`
    } else if (['ddg', 'brave', 'bing', 'google', 'startpage', 'ecosia', 'yandex'].includes(engine)) {
      // Day 46 fix — real web-engine HTML scrape (was previously falling through
      // to HN aggregator). Falls back to multi-source if engine returns 0 results.
      try {
        results = await searchEngineHTML(query, engine, this.cfg)
        url = (this.cfg.engines || {})[engine] || engine
        if (results.length === 0) {
          results = await searchMultiSource(query, ['hn', 'github', 'wiby'])
          url = `${engine}-fallback:${query}`
        }
      } catch (err) {
        results = await searchMultiSource(query, ['hn', 'github', 'wiby'])
        url = `${engine}-error-fallback:${query}`
      }
    } else {
      // Default: aggregate HN + GitHub + Wiby for best coverage
      results = await searchMultiSource(query, ['wikipedia', 'hn', 'github', 'wiby'])
      url = `hyperx-search:${query}`
    }

    const elapsed = Date.now() - t0
    appendHistory({ url: `hyperx-search:${query}`, title: `Search: ${query}`, type: 'search', engine, elapsed })
    return { query, engine, url, results, elapsed, total: results.length }
  }

  // Download file
  async download(url, destPath) {
    return downloadFile(url, this.cfg, destPath)
  }

  // POST request
  async post(url, body, contentType = 'application/x-www-form-urlencoded') {
    const payload = typeof body === 'object' && contentType.includes('json')
      ? JSON.stringify(body)
      : typeof body === 'object'
        ? new URLSearchParams(body).toString()
        : body
    return this.get(url, { method: 'POST', body: payload, headers: { 'Content-Type': contentType } })
  }

  // Scrape: extract structured data from a page
  async scrape(url, selectors = {}) {
    const page = await this.get(url)
    const result = { url, meta: page.meta, extracted: {} }
    // selectors is { key: 'regex or text pattern' }
    for (const [key, pattern] of Object.entries(selectors)) {
      const re = new RegExp(pattern, 'gi')
      const matches = [...page.html.matchAll(re)].map(m => m[1] || m[0])
      result.extracted[key] = matches
    }
    result.links = page.links
    result.images = page.images
    result.text = page.text
    return result
  }

  // Bulk crawl
  async crawl(startUrl, opts = { maxPages: 10, sameOrigin: true }) {
    const visited = new Set()
    const queue = [startUrl]
    const pages = []
    const origin = new URL(startUrl).origin

    while (queue.length && pages.length < opts.maxPages) {
      const url = queue.shift()
      if (visited.has(url)) continue
      visited.add(url)
      try {
        const page = await this.get(url)
        pages.push({ url, title: page.meta.title, links: page.links.length, size: page.size })
        page.links.forEach(l => {
          if (!visited.has(l.url)) {
            if (!opts.sameOrigin || l.url.startsWith(origin)) queue.push(l.url)
          }
        })
      } catch (e) {
        pages.push({ url, error: e.message })
      }
      await new Promise(r => setTimeout(r, 300)) // polite delay
    }
    return { start: startUrl, pages, visited: [...visited] }
  }

  // History
  history(limit = 50) {
    return loadHistory().slice(0, limit)
  }

  clearHistory() {
    clearHistory()
  }

  // Config
  getConfig() { return this.cfg }
  setConfig(updates) {
    this.cfg = { ...this.cfg, ...updates }
    saveConfig(this.cfg)
  }
}

export { loadConfig, saveConfig, loadHistory, clearHistory, appendHistory, htmlToText, extractLinks, extractMeta, searchHackerNews, searchGitHub, searchOpenLibrary, searchWiby, searchMultiSource }
