#!/usr/bin/env node
/**
 * HYPERX Daemon - Background Process
 * Watches a job queue file and processes fetch/search/download jobs
 * 
 * Start: node bin/hyperx-daemon.js &
 * Submit job: echo '{"type":"search","query":"python tutorial","id":"job1"}' >> config/queue.json
 * Check results: cat config/results/job1.json
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, unlinkSync, watchFile } from 'fs'
import dns from 'dns'
dns.setDefaultResultOrder('ipv4first')  // Day 48: container has no IPv6 route
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const QUEUE_FILE = join(__dirname, '../config/queue.jsonl')
const RESULTS_DIR = join(__dirname, '../config/results')
const PID_FILE = join(__dirname, '../config/daemon.pid')
const LOG_FILE = join(__dirname, '../config/daemon.log')

if (!existsSync(RESULTS_DIR)) mkdirSync(RESULTS_DIR, { recursive: true })

const engine = new HyperXEngine()

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`
  process.stdout.write(line)
  try { appendFileSync(LOG_FILE, line) } catch {}
}

function writeResult(id, data) {
  writeFileSync(join(RESULTS_DIR, `${id}.json`), JSON.stringify(data, null, 2))
}

async function processJob(job) {
  const { id, type } = job
  if (!id) return
  log(`Processing job ${id} type=${type}`)
  const t0 = Date.now()

  try {
    let result
    switch (type) {
      case 'get': case 'fetch': {
        const page = await engine.get(job.url)
        result = { id, status: 'done', type, url: page.url, title: page.meta.title, text: page.text, links: page.links, elapsed: Date.now()-t0 }
        break
      }
      case 'search': {
        const res = await engine.search(job.query, job.engine)
        result = { id, status: 'done', type, ...res, elapsed: Date.now()-t0 }
        break
      }
      case 'download': {
        const dl = await engine.download(job.url, job.dest)
        result = { id, status: 'done', type, ...dl, elapsed: Date.now()-t0 }
        break
      }
      case 'scrape': {
        const res = await engine.scrape(job.url, job.selectors || {})
        result = { id, status: 'done', type, ...res, elapsed: Date.now()-t0 }
        break
      }
      case 'multi': {
        const urls = (job.urls || []).slice(0, 20)
        const pages = await Promise.allSettled(urls.map(u => engine.get(u)))
        result = { id, status: 'done', type, results: pages.map((r,i) => r.status === 'fulfilled' ? { url: urls[i], title: r.value.meta.title, text: r.value.text.slice(0,2000) } : { url: urls[i], error: r.reason.message }), elapsed: Date.now()-t0 }
        break
      }
      case 'crawl': {
        const res = await engine.crawl(job.url, { maxPages: job.maxPages||10, sameOrigin: job.sameOrigin!==false })
        result = { id, status: 'done', type, ...res, elapsed: Date.now()-t0 }
        break
      }
      default:
        result = { id, status: 'error', error: `Unknown job type: ${type}` }
    }
    writeResult(id, result)
    log(`Job ${id} done in ${Date.now()-t0}ms`)
  } catch(e) {
    writeResult(id, { id, status: 'error', error: e.message, elapsed: Date.now()-t0 })
    log(`Job ${id} failed: ${e.message}`)
  }
}

const processed = new Set()

async function pollQueue() {
  if (!existsSync(QUEUE_FILE)) return
  const lines = readFileSync(QUEUE_FILE, 'utf8').split('\n').filter(l => l.trim())
  for (const line of lines) {
    try {
      const job = JSON.parse(line)
      if (job.id && !processed.has(job.id)) {
        processed.add(job.id)
        writeResult(job.id, { id: job.id, status: 'processing' })
        await processJob(job)
      }
    } catch {}
  }
}

// Write PID
writeFileSync(PID_FILE, process.pid.toString())
log(`HyperX Daemon started (PID ${process.pid})`)
log(`Queue: ${QUEUE_FILE}`)
log(`Results: ${RESULTS_DIR}`)
log(`Submit: echo '{"id":"job1","type":"search","query":"hello"}' >> ${QUEUE_FILE}`)

// Poll every second
setInterval(pollQueue, 1000)
pollQueue()

// Handle shutdown
process.on('SIGTERM', () => { log('Shutdown'); try { unlinkSync(PID_FILE) } catch {} process.exit(0) })
process.on('SIGINT', () => { log('Shutdown'); try { unlinkSync(PID_FILE) } catch {} process.exit(0) })
