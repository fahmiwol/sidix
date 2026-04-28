/**
 * SIDIX Pixel — Popup script
 * Sprint 42 Phase 1 scaffold
 */

async function refresh() {
  const stored = await chrome.storage.local.get([
    "enabled", "endpoint", "recent_captures",
  ]);
  const enabled = stored.enabled !== false;
  document.getElementById("status-dot").className = "dot " + (enabled ? "on" : "off");
  document.getElementById("status-text").textContent = enabled
    ? `Active · ${stored.endpoint || "default endpoint"}`
    : "Disabled";

  const list = document.getElementById("recent-list");
  const recent = stored.recent_captures || [];
  if (recent.length === 0) {
    list.innerHTML = '<div class="meta">No captures yet.</div>';
  } else {
    list.innerHTML = recent.slice(0, 5).map((c) => `
      <div class="capture-item">
        <div>${escapeHtml(c.page_title || "(no title)")}</div>
        <div class="url">${escapeHtml(c.url)}</div>
        <div class="meta">
          ${escapeHtml(c.source)} · ${c.result_ok ? "✓" : "✗"} ·
          ${new Date(c.timestamp).toLocaleString("id-ID")}
        </div>
      </div>
    `).join("");
  }
}

function escapeHtml(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.getElementById("btn-toggle").addEventListener("click", async () => {
  const stored = await chrome.storage.local.get(["enabled"]);
  await chrome.storage.local.set({ enabled: !(stored.enabled !== false) });
  await refresh();
});

document.getElementById("btn-capture").addEventListener("click", async () => {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs[0]) return;
  const tab = tabs[0];
  const result = await chrome.runtime.sendMessage({
    type: "SIDIX_TRIGGER",
    url: tab.url,
    page_title: tab.title,
    trigger_keyword: "manual",
    surrounding_text: "(manual capture from popup)",
    source: "popup_manual",
  });
  await refresh();
});

document.getElementById("btn-options").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

refresh();
