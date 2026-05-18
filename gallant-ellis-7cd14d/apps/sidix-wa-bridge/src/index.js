#!/usr/bin/env node
/**
 * SIDIX WA Bridge — HTTP server for MCP ↔ WhatsApp Web communication.
 * Port: 7789 (default)
 *
 * Endpoints:
 *   POST /send   — { jid, message } → sends WA message
 *   GET  /inbox  — returns recent received messages (ring buffer, max 50)
 *   GET  /status — WA connection status + QR if not yet paired
 *   POST /clear  — clears inbox buffer
 */

import express from 'express';
import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
} from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import qrcode from 'qrcode-terminal';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const AUTH_DIR = path.join(__dirname, '..', '.wa_auth');
const PORT = Number(process.env.SIDIX_WA_PORT || 7789);

// ── State ────────────────────────────────────────────────────────────────────
let sock = null;
let qrString = null;
let connectionState = 'disconnected'; // 'disconnected' | 'connecting' | 'open'
const inbox = []; // ring buffer max 50

function pushInbox(msg) {
  inbox.push(msg);
  if (inbox.length > 50) inbox.shift();
}

// ── Baileys connection ───────────────────────────────────────────────────────
async function connectWA() {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    logger: { level: 'silent', child: () => ({ level: 'silent', trace: () => {}, debug: () => {}, info: () => {}, warn: () => {}, error: () => {}, fatal: () => {}, child: () => {} }) },
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      qrString = qr;
      connectionState = 'connecting';
      qrcode.generate(qr, { small: true });
      console.log('[SIDIX-WA] Scan QR via GET /status');
    }
    if (connection === 'open') {
      qrString = null;
      connectionState = 'open';
      console.log('[SIDIX-WA] Connected to WhatsApp');
    }
    if (connection === 'close') {
      connectionState = 'disconnected';
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      if (reason !== DisconnectReason.loggedOut) {
        console.log('[SIDIX-WA] Reconnecting…');
        connectWA();
      } else {
        console.log('[SIDIX-WA] Logged out — delete .wa_auth and restart to re-pair');
      }
    }
  });

  sock.ev.on('messages.upsert', ({ messages, type }) => {
    if (type !== 'notify') return;
    for (const msg of messages) {
      if (msg.key.fromMe) continue;
      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        null;
      if (!text) continue;
      pushInbox({
        jid: msg.key.remoteJid,
        from: msg.pushName || msg.key.remoteJid,
        text,
        timestamp: msg.messageTimestamp,
        id: msg.key.id,
      });
      console.log(`[SIDIX-WA] ← ${msg.key.remoteJid}: ${text.slice(0, 80)}`);
    }
  });
}

connectWA().catch(console.error);

// ── HTTP API ─────────────────────────────────────────────────────────────────
const app = express();
app.use(express.json());

app.get('/status', (_req, res) => {
  res.json({
    status: connectionState,
    qr: qrString,
    inbox_count: inbox.length,
  });
});

app.post('/send', async (req, res) => {
  const { jid, message } = req.body || {};
  if (!jid || !message) {
    return res.status(400).json({ ok: false, error: 'jid and message required' });
  }
  if (connectionState !== 'open') {
    return res.status(503).json({ ok: false, error: `WA not connected (state: ${connectionState})` });
  }
  try {
    await sock.sendMessage(jid, { text: message });
    res.json({ ok: true, jid, message });
  } catch (err) {
    res.status(500).json({ ok: false, error: err.message });
  }
});

app.get('/inbox', (_req, res) => {
  res.json({ ok: true, messages: [...inbox].reverse() });
});

app.post('/clear', (_req, res) => {
  inbox.length = 0;
  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`[SIDIX-WA] Bridge running on http://localhost:${PORT}`);
});
