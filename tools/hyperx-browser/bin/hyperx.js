#!/usr/bin/env node
/**
 * HYPERX CLI Browser
 * Usage: hyperx [url|query]
 * Flags: --engine=ddg --download --raw --links --scrape --no-history
 */

import { HyperXEngine } from '../src/engine.js'
import dns from 'dns'
dns.setDefaultResultOrder('ipv4first')  // Day 48: container has no IPv6 route
import { writeFileSync } from 'fs'
import { join } from 'path'
import minimist from 'minimist'

const argv = minimist(process.argv.slice(2), {
  string: ['engine', 'output', 'proxy', 'post'],
  boolean: ['download', 'raw', 'links', 'images', 'scrape', 'crawl', 'help', 'version', 'history', 'no-history', 'json'],
  alias: { e: 'engine', o: 'output', h: 'help', v: 'version', d: 'download', r: 'raw', l: 'links', j: 'json' },
})

const engine = new HyperXEngine()

// Colors (minimal)
const C = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  cyan: '\x1b[36m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  gray: '\x1b[90m',
}

function c(color, text) {
  return process.stdout.isTTY ? `${C[color]}${text}${C.reset}` : text
}

function banner() {
  console.log(c('green', `
██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗ ██╗  ██╗
██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗╚██╗██╔╝
███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝ ╚███╔╝ 
██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗ ██╔██╗ 
██║  ██║   ██║   ██║     ███████╗██║  ██║██╔╝ ██╗
╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝`))
  console.log(c('gray', '  anonymous · ultra-light · cli browser · v1.0.0'))
  console.log(c('gray', '  type `help` for commands\n'))
}

function help() {
  console.log(`${c('bold', 'COMMANDS')}
  ${c('cyan', 'go <url>')}          fetch & render page
  ${c('cyan', 'search <query>')}    search the web
  ${c('cyan', 'get <url>')}         same as go
  ${c('cyan', 'post <url> <data>')} HTTP POST request
  ${c('cyan', 'dl <url>')}          download file
  ${c('cyan', 'links')}             show links from last page
  ${c('cyan', 'images')}            show images from last page
  ${c('cyan', 'raw')}               show raw HTML of last page
  ${c('cyan', 'crawl <url>')}       crawl site (max 10 pages)
  ${c('cyan', 'history [n]')}       show browse history
  ${c('cyan', 'clearhistory')}      clear all history
  ${c('cyan', 'engine <name>')}     switch engine (google/ddg/brave/bing/startpage)
  ${c('cyan', 'config')}            show current config
  ${c('cyan', 'set <key> <val>')}   update config
  ${c('cyan', 'proxy <url>')}       set proxy (http://... or socks5://...)
  ${c('cyan', 'save [file]')}       save last page to file
  ${c('cyan', 'open <n>')}          open link #n from last results
  ${c('cyan', 'back')}              go back in tab history
  ${c('cyan', 'quit / exit')}       exit browser

${c('bold', 'CLI FLAGS')}
  ${c('yellow', '--engine=ddg')}    set search engine
  ${c('yellow', '--download')}      download instead of render
  ${c('yellow', '--raw')}           print raw HTML
  ${c('yellow', '--links')}         print links only
  ${c('yellow', '--json')}          output JSON
  ${c('yellow', '--output=file')}   save output to file
  ${c('yellow', '--no-history')}    don't save to history
  ${c('yellow', '--post=data')}     POST with data

${c('bold', 'ENGINES')}
  google · ddg · brave · bing · startpage · yandex · ecosia
`)
}

let lastPage = null
let lastResults = []
let tabHistory = []
let tabIdx = -1

function pushHistory(entry) {
  tabHistory = tabHistory.slice(0, tabIdx + 1)
  tabHistory.push(entry)
  tabIdx = tabHistory.length - 1
}

function renderPage(page) {
  lastPage = page
  console.log()
  console.log(c('bold', '━'.repeat(60)))
  console.log(c('cyan', ` ${page.meta.title || page.url}`))
  console.log(c('gray', ` ${page.url}`))
  console.log(c('gray', ` HTTP ${page.status} · ${page.elapsed}ms · ${(page.size/1024).toFixed(1)}KB`))
  if (page.meta.description) console.log(c('dim', ` ${page.meta.description}`))
  console.log(c('bold', '━'.repeat(60)))
  console.log()
  // Print text content, paginated
  const lines = page.text.split('\n').filter(l => l.trim())
  const maxLines = 80
  if (lines.length > maxLines) {
    console.log(lines.slice(0, maxLines).join('\n'))
    console.log(c('gray', `\n... [${lines.length - maxLines} more lines — use 'raw' or 'save' to get full content]`))
  } else {
    console.log(lines.join('\n'))
  }
  console.log()
  console.log(c('gray', `[${page.links.length} links · ${page.images.length} images · 'links' to list · 'dl <n>' to download]`))
}

function renderResults(res) {
  lastResults = res.results
  console.log()
  console.log(c('bold', `━━ Search: "${res.query}" via ${res.engine.toUpperCase()} [${res.elapsed}ms] ━━`))
  console.log()
  res.results.forEach((r, i) => {
    console.log(`${c('yellow', ` [${i+1}]`)} ${c('bold', r.title)}`)
    console.log(`     ${c('cyan', r.url)}`)
    if (r.snippet) console.log(`     ${c('gray', r.snippet.slice(0, 120))}`)
    console.log()
  })
  if (!res.results.length) {
    console.log(c('red', '  No results parsed. Try a different engine: `engine ddg`'))
  }
  console.log(c('gray', `'open <n>' to visit · 'engine <name>' to switch`))
}

function renderLinks() {
  if (!lastPage) { console.log(c('red', 'No page loaded')); return }
  lastPage.links.forEach((l, i) => {
    console.log(`${c('yellow', `[${i+1}]`)} ${c('gray', l.text.slice(0, 40).padEnd(40))}  ${c('cyan', l.url)}`)
  })
}

function renderImages() {
  if (!lastPage) { console.log(c('red', 'No page loaded')); return }
  lastPage.images.forEach((img, i) => {
    console.log(`${c('yellow', `[${i+1}]`)} ${c('gray', (img.alt||'').slice(0,30).padEnd(30))}  ${c('cyan', img.url)}`)
  })
}

async function handleCommand(input) {
  const parts = input.trim().split(/\s+/)
  const cmd = parts[0].toLowerCase()
  const args = parts.slice(1)

  try {
    switch (cmd) {
      case '':
        break

      case 'help': case '?':
        help()
        break

      case 'go': case 'get': case 'open': {
        let target = args.join(' ')
        // If numeric, open from last results/links
        if (/^\d+$/.test(target)) {
          const idx = parseInt(target) - 1
          if (lastResults[idx]) target = lastResults[idx].url
          else if (lastPage?.links[idx]) target = lastPage.links[idx].url
          else { console.log(c('red', `No item #${target}`)); break }
        }
        if (!target.startsWith('http')) target = 'https://' + target
        process.stdout.write(c('gray', `  fetching ${target}...\r`))
        const page = await engine.get(target)
        pushHistory({ type: 'page', data: page })
        renderPage(page)
        break
      }

      case 'search': case 's': case '/': {
        const q = args.join(' ')
        if (!q) { console.log(c('red', 'Usage: search <query>')); break }
        process.stdout.write(c('gray', `  searching "${q}"...\r`))
        const res = await engine.search(q)
        pushHistory({ type: 'results', data: res })
        renderResults(res)
        break
      }

      case 'post': {
        const url = args[0]
        const body = args.slice(1).join(' ')
        if (!url || !body) { console.log(c('red', 'Usage: post <url> <key=val&key2=val2>')); break }
        process.stdout.write(c('gray', `  posting to ${url}...\r`))
        const page = await engine.post(url, Object.fromEntries(body.split('&').map(p => p.split('='))))
        renderPage(page)
        break
      }

      case 'dl': case 'download': {
        let target = args.join(' ')
        if (/^\d+$/.test(target)) {
          const idx = parseInt(target) - 1
          if (lastPage?.links[idx]) target = lastPage.links[idx].url
          else if (lastPage?.images[idx]) target = lastPage.images[idx].url
          else { console.log(c('red', `No item #${target}`)); break }
        }
        if (!target.startsWith('http')) target = 'https://' + target
        process.stdout.write(c('gray', `  downloading ${target}...\r`))
        const result = await engine.download(target)
        console.log(c('green', `  ✓ Downloaded: ${result.filename} (${(result.size/1024).toFixed(1)}KB)`))
        break
      }

      case 'links': case 'l':
        renderLinks()
        break

      case 'images': case 'img':
        renderImages()
        break

      case 'raw':
        if (!lastPage) { console.log(c('red', 'No page loaded')); break }
        console.log(lastPage.html)
        break

      case 'crawl': {
        const url = args[0]
        if (!url) { console.log(c('red', 'Usage: crawl <url>')); break }
        const maxPages = parseInt(args[1]) || 10
        console.log(c('gray', `  crawling ${url} (max ${maxPages} pages)...`))
        const res = await engine.crawl(url.startsWith('http') ? url : 'https://'+url, { maxPages, sameOrigin: true })
        console.log(c('bold', `\n  Crawled ${res.pages.length} pages:\n`))
        res.pages.forEach(p => {
          if (p.error) console.log(`  ${c('red', '✗')} ${p.url} — ${p.error}`)
          else console.log(`  ${c('green', '✓')} ${(p.title||'').slice(0,40).padEnd(40)}  ${c('gray', p.url)}`)
        })
        break
      }

      case 'save': {
        if (!lastPage) { console.log(c('red', 'No page loaded')); break }
        const file = args[0] || `hyperx-${Date.now()}.txt`
        writeFileSync(file, lastPage.text)
        console.log(c('green', `  Saved to ${file}`))
        break
      }

      case 'history': case 'hist': {
        const limit = parseInt(args[0]) || 20
        const hist = engine.history(limit)
        if (!hist.length) { console.log(c('gray', '  No history')); break }
        hist.forEach((h, i) => {
          const date = new Date(h.time).toLocaleString()
          console.log(`${c('gray', `[${i+1}]`)} ${c('cyan', (h.title||h.url).slice(0,50).padEnd(50))}  ${c('gray', date)}`)
        })
        break
      }

      case 'clearhistory': case 'clh':
        engine.clearHistory()
        console.log(c('green', '  History cleared'))
        break

      case 'engine': {
        const eng = args[0]
        if (!eng) { console.log(c('gray', `  Current: ${engine.cfg.searchEngine}`)); break }
        engine.setConfig({ searchEngine: eng })
        console.log(c('green', `  Engine set to: ${eng}`))
        break
      }

      case 'proxy': {
        const proxy = args[0] || null
        engine.setConfig({ proxy })
        console.log(c('green', proxy ? `  Proxy set: ${proxy}` : '  Proxy cleared'))
        break
      }

      case 'config':
        console.log(JSON.stringify(engine.getConfig(), null, 2))
        break

      case 'set': {
        const key = args[0]
        let val = args.slice(1).join(' ')
        if (val === 'true') val = true
        else if (val === 'false') val = false
        else if (!isNaN(val)) val = Number(val)
        if (!key) { console.log(c('red', 'Usage: set <key> <value>')); break }
        engine.setConfig({ [key]: val })
        console.log(c('green', `  Set ${key} = ${val}`))
        break
      }

      case 'back': {
        if (tabIdx <= 0) { console.log(c('gray', '  Nothing to go back to')); break }
        tabIdx--
        const prev = tabHistory[tabIdx]
        if (prev.type === 'page') renderPage(prev.data)
        else renderResults(prev.data)
        break
      }

      case 'fwd': case 'forward': {
        if (tabIdx >= tabHistory.length - 1) { console.log(c('gray', '  Nothing to go forward to')); break }
        tabIdx++
        const next = tabHistory[tabIdx]
        if (next.type === 'page') renderPage(next.data)
        else renderResults(next.data)
        break
      }

      case 'json':
        if (lastPage) console.log(JSON.stringify(lastPage, null, 2))
        else if (lastResults.length) console.log(JSON.stringify(lastResults, null, 2))
        else console.log(c('red', 'Nothing loaded'))
        break

      case 'version': case 'v':
        console.log('hyperx-browser v1.0.0')
        break

      case 'quit': case 'exit': case 'q':
        console.log(c('gray', '\n  bye\n'))
        process.exit(0)
        break

      default:
        // If it looks like a URL, go to it
        if (cmd.includes('.') || cmd.startsWith('http')) {
          await handleCommand('go ' + input)
        } else {
          // Treat as search
          await handleCommand('search ' + input)
        }
    }
  } catch (err) {
    console.log(c('red', `  Error: ${err.message}`))
  }
}

async function main() {
  // One-shot CLI mode
  const oneShot = argv._[0]
  if (oneShot) {
    try {
      if (argv.download) {
        const r = await engine.download(oneShot, argv.output)
        console.log(JSON.stringify(r))
      } else if (argv.raw) {
        const p = await engine.get(oneShot)
        console.log(p.html)
      } else if (argv.links) {
        const p = await engine.get(oneShot)
        p.links.forEach(l => console.log(`${l.url}\t${l.text}`))
      } else if (argv.json) {
        const p = await engine.get(oneShot)
        console.log(JSON.stringify(p, null, 2))
        if (argv.output) writeFileSync(argv.output, JSON.stringify(p, null, 2))
      } else {
        // Is it a URL or search?
        if (oneShot.startsWith('http') || oneShot.includes('.')) {
          const p = await engine.get(oneShot)
          if (argv.output) { writeFileSync(argv.output, p.text); process.exit(0) }
          renderPage(p)
        } else {
          const query = process.argv.slice(2).join(' ').replace(/^--[^\s]+\s*/g,'')
          const res = await engine.search(query, argv.engine)
          if (argv.json) { console.log(JSON.stringify(res, null, 2)); process.exit(0) }
          renderResults(res)
        }
      }
      process.exit(0)
    } catch(e) {
      console.error('Error:', e.message)
      process.exit(1)
    }
  }

  // Interactive REPL mode
  banner()

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: c('green', 'hyperx') + c('gray', '> '),
    historySize: 100,
    completer: (line) => {
      const cmds = ['go ','search ','get ','post ','dl ','links','images','raw','crawl ','save ','history','clearhistory','engine ','proxy ','config','set ','back','fwd','json','quit','help']
      const hits = cmds.filter(c => c.startsWith(line))
      return [hits.length ? hits : cmds, line]
    }
  })

  rl.prompt()
  rl.on('line', async (line) => {
    await handleCommand(line)
    rl.prompt()
  })
  rl.on('close', () => {
    console.log(c('gray', '\n  bye\n'))
    process.exit(0)
  })
}

main()
