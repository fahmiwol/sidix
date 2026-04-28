/**
 * SIDIX Pixel — Content Script
 * Sprint 42 Phase 1 scaffold
 *
 * Detect @sidix keyword di:
 *  - Live typing (form input, textarea, contenteditable)
 *  - Static page text (mutation observer)
 *
 * Privacy: never capture password/credential fields.
 *          opt-in per domain (checked in background.js).
 */

const KEYWORD_REGEX = /(?:^|\s)@sidix\b/i;
const SURROUNDING_CHARS_MAX = 500;
const DEBOUNCE_MS = 800;

const SENSITIVE_INPUT_TYPES = new Set([
  "password", "tel", "email", "credit-card", "cc-number",
]);

let debounceTimer = null;
let lastFiredText = "";

function isSensitiveField(el) {
  if (!el) return false;
  if (el.tagName === "INPUT" && SENSITIVE_INPUT_TYPES.has(el.type)) return true;
  if (el.autocomplete && el.autocomplete.includes("password")) return true;
  if (el.name && /password|passwd|pin|cvv/i.test(el.name)) return true;
  return false;
}

function extractSurroundingText(el) {
  let text = "";
  if (el && (el.value !== undefined)) {
    text = el.value;
  } else if (el && el.innerText) {
    text = el.innerText;
  }
  if (text.length > SURROUNDING_CHARS_MAX) {
    text = text.slice(0, SURROUNDING_CHARS_MAX) + "…";
  }
  return text;
}

function fireTrigger(payload) {
  if (payload.surrounding_text === lastFiredText) return;
  lastFiredText = payload.surrounding_text;
  chrome.runtime.sendMessage({
    type: "SIDIX_TRIGGER",
    ...payload,
  });
}

// Live typing detection
document.addEventListener("input", (e) => {
  const el = e.target;
  if (!el) return;
  if (isSensitiveField(el)) return;
  const text = extractSurroundingText(el);
  if (!KEYWORD_REGEX.test(text)) return;

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fireTrigger({
      url: location.href,
      page_title: document.title,
      trigger_keyword: "@sidix",
      surrounding_text: text,
      source: "live_typing",
      element_tag: el.tagName,
    });
  }, DEBOUNCE_MS);
}, true);

// Static page mention detection (debounced, run once per page load)
let pageScanned = false;
function scanPageOnce() {
  if (pageScanned) return;
  const bodyText = (document.body && document.body.innerText) || "";
  if (KEYWORD_REGEX.test(bodyText)) {
    pageScanned = true;
    // Find first occurrence with surrounding context
    const idx = bodyText.search(KEYWORD_REGEX);
    const start = Math.max(0, idx - 200);
    const end = Math.min(bodyText.length, idx + 300);
    const surrounding = bodyText.slice(start, end);
    fireTrigger({
      url: location.href,
      page_title: document.title,
      trigger_keyword: "@sidix",
      surrounding_text: surrounding,
      source: "page_mention",
    });
  }
}

// Run after content settles
setTimeout(scanPageOnce, 2000);

// Re-scan if SPA route change
const observer = new MutationObserver(() => {
  pageScanned = false;
  scanPageOnce();
});
observer.observe(document.body || document.documentElement,
                 { childList: true, subtree: true });
