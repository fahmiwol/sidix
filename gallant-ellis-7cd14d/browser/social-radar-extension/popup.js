const API_CANDIDATES = [
  'http://localhost:8765',
  'https://ctrl.sidixlab.com',
  'https://brain.sidixlab.com',
];

let backendBase = null;

function detectPlatform(tabUrl) {
  try {
    const host = new URL(tabUrl).hostname.toLowerCase();
    if (host.includes('instagram.com')) return 'instagram';
    if (host.includes('threads.net')) return 'threads';
    if (host === 'x.com' || host.includes('twitter.com')) return 'twitter';
    if (host.includes('youtube.com')) return 'youtube';
    if (host.includes('facebook.com')) return 'facebook';
    return 'unknown';
  } catch (_err) {
    return 'unknown';
  }
}

async function findBackendBase() {
  for (const base of API_CANDIDATES) {
    try {
      const res = await fetch(`${base}/health`, { method: 'GET' });
      if (res.ok) {
        return base;
      }
    } catch (_err) {
      // try next endpoint
    }
  }
  return null;
}

async function checkStatus() {
  const statusEl = document.getElementById('conn-status');
  backendBase = await findBackendBase();
  if (backendBase) {
    statusEl.textContent = 'Backend Online';
    statusEl.style.color = '#0f0';
    return;
  }
  statusEl.textContent = 'Backend Offline';
  statusEl.style.color = '#f55';
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const urlEl = document.getElementById('page-url');
  if (!tab || !tab.url) {
    urlEl.textContent = 'Tidak ada tab aktif';
    return null;
  }

  const platform = detectPlatform(tab.url);
  const parsed = new URL(tab.url);
  urlEl.textContent = `${parsed.hostname}${parsed.pathname}`;
  return { ...tab, platform };
}

function formatResult(data) {
  const metrics = data?.metrics || {};
  const er = Number(metrics.engagement_rate ?? data.engagement_rate ?? 0);
  const sentiment = Number(metrics.sentiment ?? data.sentiment_score ?? 0);
  const tier = metrics.tier || data.tier || 'unknown';
  const advice = data?.advice || '-';

  return [
    `<div style="margin-bottom:8px"><b>Hasil Scan:</b></div>`,
    `<div style="color:var(--gold)">• Tier: ${tier}</div>`,
    `<div style="color:var(--gold)">• Engagement Rate: ${Number.isFinite(er) ? er.toFixed(2) : '-'}%</div>`,
    `<div style="color:var(--gold)">• Sentiment: ${Number.isFinite(sentiment) ? sentiment.toFixed(2) : '-'}</div>`,
    '<hr style="border:0; border-top:1px solid #333; margin:8px 0">',
    `<div style="font-size:10px; color:#888">${advice}</div>`,
  ].join('');
}

function extractSocialMetadataFromPage(platform) {
  function parseShortCount(input) {
    if (!input) return null;
    const raw = String(input).trim().toLowerCase().replace(/,/g, '').replace(/\s+/g, '');
    const m = raw.match(/^(\d+(?:\.\d+)?)(k|m|b)?$/);
    if (!m) return Number.parseInt(raw.replace(/[^\d]/g, ''), 10) || null;
    const base = Number(m[1]);
    const unit = m[2];
    if (unit === 'k') return Math.round(base * 1_000);
    if (unit === 'm') return Math.round(base * 1_000_000);
    if (unit === 'b') return Math.round(base * 1_000_000_000);
    return Math.round(base);
  }

  function parseInstagramDescription(desc) {
    // Example: "1,234 followers, 56 following, 78 posts - Name (@handle)"
    const lowered = (desc || '').toLowerCase();
    const parts = lowered.split('-')[0] || lowered;

    let followers = null;
    let following = null;
    let posts = null;

    const followersMatch = parts.match(/([\d.,kmb]+)\s+followers?/i) || parts.match(/([\d.,kmb]+)\s+pengikut/i);
    const followingMatch = parts.match(/([\d.,kmb]+)\s+following/i) || parts.match(/([\d.,kmb]+)\s+mengikuti/i);
    const postsMatch = parts.match(/([\d.,kmb]+)\s+posts?/i) || parts.match(/([\d.,kmb]+)\s+postingan/i);

    if (followersMatch) followers = parseShortCount(followersMatch[1]);
    if (followingMatch) following = parseShortCount(followingMatch[1]);
    if (postsMatch) posts = parseShortCount(postsMatch[1]);

    return { followers, following, post_count: posts };
  }

  const metadata = {
    platform,
    followers: 0,
    following: 0,
    post_count: 0,
    likes: 0,
    comments: 0,
    recent_comments: [],
    bio: '',
    page_title: document.title || '',
  };

  const description = document.querySelector('meta[name="description"]')?.content || '';
  if (platform === 'instagram') {
    const parsed = parseInstagramDescription(description);
    metadata.followers = parsed.followers || 0;
    metadata.following = parsed.following || 0;
    metadata.post_count = parsed.post_count || 0;

    // Try JSON-LD for profile data when available.
    const jsonLds = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    for (const node of jsonLds) {
      try {
        const data = JSON.parse(node.textContent || '{}');
        const list = Array.isArray(data) ? data : [data];
        for (const obj of list) {
          if (!obj || typeof obj !== 'object') continue;
          if (obj?.description && !metadata.bio) {
            metadata.bio = String(obj.description).slice(0, 800);
          }
          const stats = Array.isArray(obj.interactionStatistic)
            ? obj.interactionStatistic
            : obj.interactionStatistic
              ? [obj.interactionStatistic]
              : [];
          for (const stat of stats) {
            const type = String(stat?.interactionType || '').toLowerCase();
            const count = parseShortCount(stat?.userInteractionCount);
            if (count == null) continue;
            if (type.includes('follow')) {
              metadata.followers = Math.max(metadata.followers, count);
            }
          }
        }
      } catch (_err) {
        // ignore malformed json-ld
      }
    }

    if (!metadata.bio && description) {
      const chunks = description.split('-').map((part) => part.trim());
      metadata.bio = chunks.slice(1).join(' - ').slice(0, 800);
    }
  }

  return metadata;
}

async function collectMetadata(tab) {
  const execution = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: extractSocialMetadataFromPage,
    args: [tab.platform],
  });

  if (!execution || execution.length === 0) {
    throw new Error('Tidak dapat mengeksekusi scraper pada tab aktif.');
  }

  return execution[0]?.result || {};
}

async function scanCompetitor() {
  const resultsEl = document.getElementById('radar-results');
  const placeholderEl = document.getElementById('radar-placeholder');
  const btn = document.getElementById('btn-scan');

  btn.disabled = true;
  btn.textContent = 'Memindai...';
  placeholderEl.classList.add('hidden');
  resultsEl.classList.remove('hidden');
  resultsEl.innerHTML = '<i>Mengumpulkan metadata halaman...</i>';

  try {
    if (!backendBase) {
      backendBase = await findBackendBase();
    }
    if (!backendBase) {
      throw new Error('Backend SIDIX tidak tersedia. Jalankan /health terlebih dahulu.');
    }

    const tab = await getActiveTab();
    if (!tab || !tab.url) {
      throw new Error('Tab aktif tidak terdeteksi.');
    }

    if (tab.platform === 'unknown') {
      throw new Error('Platform belum didukung. Buka Instagram/Threads/X/YouTube/Facebook.');
    }

    const metadata = await collectMetadata(tab);
    const payload = {
      url: tab.url,
      metadata,
    };

    resultsEl.innerHTML = '<i>Menganalisis ke backend SIDIX...</i>';

    const res = await fetch(`${backendBase}/social/radar/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Backend error HTTP ${res.status}`);
    }

    const data = await res.json();
    resultsEl.innerHTML = formatResult(data);

    // Push to extension bridge (MCP reads from here) + background storage
    const scanEntry = { url: tab.url, platform: tab.platform, metadata, radar: data };
    chrome.runtime.sendMessage({ type: 'SIDIX_SCAN_RESULT', ...scanEntry });
    fetch('http://localhost:7788/push-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scanEntry),
    }).catch(() => {}); // bridge may not be running — silent fail
  } catch (err) {
    resultsEl.innerHTML = `<span style="color:#f55">Gagal: ${err.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Scan Ulang';
  }
}

document.getElementById('btn-scan').addEventListener('click', scanCompetitor);
checkStatus();
getActiveTab();
setInterval(getActiveTab, 2000);
