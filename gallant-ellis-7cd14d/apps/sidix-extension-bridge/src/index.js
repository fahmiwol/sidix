#!/usr/bin/env node
/**
 * SIDIX Extension Bridge — HTTP server for Chrome Extension ↔ MCP communication.
 * Port: 7788 (default)
 *
 * The Chrome Extension POSTs scan results here.
 * The MCP tool polls GET /last-scan to retrieve them.
 *
 * Endpoints:
 *   POST /push-scan  { url, platform, metadata, radar } → stores latest scan
 *   GET  /last-scan  → returns latest scan with age_ms
 *   POST /clear      → clears stored scan
 *   GET  /health     → status check
 */

import express from 'express';
import cors from 'cors';

const PORT = Number(process.env.SIDIX_BRIDGE_PORT || 7788);
const TTL_MS = 5 * 60 * 1000; // 5 minutes

let lastScan = null;

const app = express();

app.use(cors({ origin: '*' }));
app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'sidix-extension-bridge', has_scan: !!lastScan });
});

app.post('/push-scan', (req, res) => {
  const { url, platform, metadata, radar } = req.body || {};
  if (!url || !platform) {
    return res.status(400).json({ ok: false, error: 'url and platform required' });
  }
  lastScan = { url, platform, metadata: metadata || {}, radar: radar || {}, timestamp: Date.now() };
  console.log(`[SIDIX-BRIDGE] Received scan: ${platform} ${url}`);
  res.json({ ok: true });
});

app.get('/last-scan', (_req, res) => {
  if (!lastScan) {
    return res.json({ ok: false, reason: 'no_scan' });
  }
  const age_ms = Date.now() - lastScan.timestamp;
  if (age_ms > TTL_MS) {
    return res.json({ ok: false, reason: 'stale', age_ms });
  }
  res.json({ ok: true, age_ms, data: lastScan });
});

app.post('/clear', (_req, res) => {
  lastScan = null;
  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`[SIDIX-BRIDGE] Extension bridge running on http://localhost:${PORT}`);
});
