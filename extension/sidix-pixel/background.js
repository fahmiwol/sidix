/**
 * SIDIX Pixel — Background Service Worker
 * Sprint 42 Phase 1 scaffold
 *
 * Receive trigger from content.js → POST ke SIDIX endpoint.
 * Per-domain opt-in/opt-out via chrome.storage.local.
 * Offline queue (IndexedDB Phase 2).
 */

const DEFAULT_ENDPOINT = "https://ctrl.sidixlab.com/sidix/pixel/capture";

const DEFAULT_DOMAIN_WHITELIST = [
  "twitter.com", "x.com",
  "www.instagram.com", "instagram.com",
  "www.facebook.com", "facebook.com",
  "www.linkedin.com", "linkedin.com",
  "www.youtube.com", "youtube.com",
  "github.com",
  "medium.com",
];

async function getSettings() {
  const stored = await chrome.storage.local.get([
    "endpoint", "token", "whitelist", "enabled",
  ]);
  return {
    endpoint: stored.endpoint || DEFAULT_ENDPOINT,
    token: stored.token || "",
    whitelist: stored.whitelist || DEFAULT_DOMAIN_WHITELIST,
    enabled: stored.enabled !== false, // default true
  };
}

function isWhitelisted(url, whitelist) {
  try {
    const host = new URL(url).hostname;
    return whitelist.some((w) => host === w || host.endsWith("." + w));
  } catch {
    return false;
  }
}

async function sendToSidix(payload) {
  const settings = await getSettings();
  if (!settings.enabled) return { ok: false, reason: "disabled" };
  if (!isWhitelisted(payload.url, settings.whitelist)) {
    return { ok: false, reason: "domain_not_whitelisted" };
  }

  try {
    const headers = { "Content-Type": "application/json" };
    if (settings.token) {
      headers["X-Sidix-Pixel-Token"] = settings.token;
    }
    const resp = await fetch(settings.endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...payload,
        captured_at: new Date().toISOString(),
        client_version: "0.1.0",
      }),
    });
    const ok = resp.ok;
    let data = null;
    try { data = await resp.json(); } catch {}
    return { ok, status: resp.status, data };
  } catch (e) {
    // Phase 2: queue to IndexedDB if offline
    return { ok: false, reason: "fetch_error", error: String(e) };
  }
}

async function recordCapture(payload, result) {
  const stored = await chrome.storage.local.get(["recent_captures"]);
  const recent = stored.recent_captures || [];
  recent.unshift({
    timestamp: new Date().toISOString(),
    url: payload.url,
    page_title: payload.page_title,
    surrounding_text: (payload.surrounding_text || "").slice(0, 200),
    source: payload.source,
    result_ok: result.ok,
    result_status: result.status,
  });
  await chrome.storage.local.set({
    recent_captures: recent.slice(0, 20), // keep latest 20
  });
}

async function notifyUser(payload, result) {
  const title = result.ok
    ? "SIDIX captured"
    : "SIDIX capture failed";
  const message = result.ok
    ? `Captured: ${payload.page_title?.slice(0, 60) || payload.url}`
    : `Reason: ${result.reason || result.status || "unknown"}`;
  try {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon48.png",
      title,
      message,
    });
  } catch {}
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "SIDIX_TRIGGER") {
    (async () => {
      const result = await sendToSidix(msg);
      await recordCapture(msg, result);
      await notifyUser(msg, result);
      sendResponse(result);
    })();
    return true; // async response
  }
});

// Initialize defaults on install
chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get(["whitelist", "enabled"]);
  const updates = {};
  if (!stored.whitelist) updates.whitelist = DEFAULT_DOMAIN_WHITELIST;
  if (stored.enabled === undefined) updates.enabled = true;
  if (Object.keys(updates).length) {
    await chrome.storage.local.set(updates);
  }
});
