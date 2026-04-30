/**
 * SIDIX Social Radar — Background Service Worker
 * Menyimpan hasil scan terbaru dan melayani bridge requests dari MCP server.
 */

const BRIDGE_STORAGE_KEY = 'sidix_last_scan';
const BRIDGE_TTL_MS = 5 * 60 * 1000; // 5 menit

// Simpan hasil scan ke storage session (dibersihkan saat browser tutup)
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'SIDIX_SCAN_RESULT') {
    const entry = {
      url: msg.url,
      platform: msg.platform,
      metadata: msg.metadata,
      radar: msg.radar,
      timestamp: Date.now(),
    };
    chrome.storage.session.set({ [BRIDGE_STORAGE_KEY]: entry });
    sendResponse({ ok: true });
    return true;
  }

  if (msg.type === 'SIDIX_GET_LAST_SCAN') {
    chrome.storage.session.get(BRIDGE_STORAGE_KEY, (result) => {
      const entry = result[BRIDGE_STORAGE_KEY];
      if (!entry) {
        sendResponse({ ok: false, reason: 'no_scan' });
        return;
      }
      const age = Date.now() - (entry.timestamp || 0);
      if (age > BRIDGE_TTL_MS) {
        sendResponse({ ok: false, reason: 'stale', age_ms: age });
        return;
      }
      sendResponse({ ok: true, data: entry });
    });
    return true; // async
  }

  if (msg.type === 'SIDIX_CLEAR_SCAN') {
    chrome.storage.session.remove(BRIDGE_STORAGE_KEY);
    sendResponse({ ok: true });
    return true;
  }
});

// Tandai extension aktif saat install/update
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[SIDIX] Social Radar installed/updated:', details.reason);
  chrome.storage.local.set({ sidix_version: chrome.runtime.getManifest().version });
});
