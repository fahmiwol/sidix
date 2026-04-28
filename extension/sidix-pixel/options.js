/**
 * SIDIX Pixel — Options page script
 * Sprint 42 Phase 1 scaffold
 */

async function load() {
  const stored = await chrome.storage.local.get([
    "endpoint", "token", "whitelist",
  ]);
  document.getElementById("endpoint").value = stored.endpoint || "";
  document.getElementById("token").value = stored.token || "";
  document.getElementById("whitelist").value =
    (stored.whitelist || []).join("\n");
}

async function save() {
  const endpoint = document.getElementById("endpoint").value.trim();
  const token = document.getElementById("token").value.trim();
  const whitelist = document.getElementById("whitelist").value
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
  await chrome.storage.local.set({ endpoint, token, whitelist });
  const s = document.getElementById("status");
  s.textContent = "Saved ✓";
  setTimeout(() => { s.textContent = ""; }, 2000);
}

document.getElementById("save").addEventListener("click", save);
load();
