/**
 * SIDIX Pixel Chrome Extension
 *
 * Author:  Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
 * License: MIT (see repo LICENSE) - attribution required for derivative work.
 * Prior-art declaration: see repo CLAIM_OF_INVENTION.md
 * Project: SIDIX (Self-Improving Distributed Intelligence eXchange)
 * URL:     https://sidixlab.com  -  https://github.com/fahmiwol/sidix
 *
 * AI assistance: drafted with Claude (Sonnet 4.6) under direction of the
 * named author. AI tools are scribes, not authors of invention.
 */
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
