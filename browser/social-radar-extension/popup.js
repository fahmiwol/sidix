// SIDIX Social Radar — Extension Logic v0.1.0

const API_URL = 'http://localhost:8765'; // Fallback ke lokal
const PROD_URL = 'https://brain.sidixlab.com'; // Backend prod

async function checkStatus() {
  const statusEl = document.getElementById('conn-status');
  try {
    const res = await fetch(`${API_URL}/health`);
    if (res.ok) {
      statusEl.textContent = 'Lokal Online';
      statusEl.style.color = '#0f0';
    } else {
      throw new Error();
    }
  } catch (e) {
    statusEl.textContent = 'Server Offline';
    statusEl.style.color = '#f55';
  }
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const urlEl = document.getElementById('page-url');
  if (tab && tab.url) {
    const url = new URL(tab.url);
    urlEl.textContent = url.hostname + url.pathname;
    return tab;
  }
  urlEl.textContent = 'Tidak ada tab aktif';
  return null;
}

async function scanCompetitor() {
  const resultsEl = document.getElementById('radar-results');
  const placeholderEl = document.getElementById('radar-placeholder');
  const btn = document.getElementById('btn-scan');

  btn.disabled = true;
  btn.textContent = 'Memindai...';
  placeholderEl.classList.add('hidden');
  resultsEl.classList.remove('hidden');
  resultsEl.innerHTML = '<i>Menghubungi SIDIX Brain...</i>';

  const tab = await getActiveTab();
  if (!tab) {
    resultsEl.innerHTML = '<span style="color:#f55">Gagal: Tab tidak terdeteksi.</span>';
    btn.disabled = false;
    btn.textContent = 'Scan Kompetitor';
    return;
  }

  // Simulasi OpHarvest — di sprint berikutnya ini akan memanggil content script
  // untuk scrape metadata minimal (likes, comments, bio) tanpa PII.
  setTimeout(() => {
    resultsEl.innerHTML = `
      <div style="margin-bottom:8px"><b>Sinyal Ditemukan:</b></div>
      <div style="color:var(--gold)">• Engagement Rate: 4.2%</div>
      <div style="color:var(--gold)">• Top Keywords: UMKM, Lokal, Handmade</div>
      <div style="color:var(--gold)">• Sentiment: Positif (88%)</div>
      <hr style="border:0; border-top:1px solid #333; margin:8px 0">
      <div style="font-size:10px; color:#888">
        OpHarvest: Data disanitasi. SIDIX menyarankan fokus pada konten "Behind the scenes"
        untuk menyaingi kompetitor ini.
      </div>
    `;
    btn.disabled = false;
    btn.textContent = 'Scan Ulang';
  }, 1500);
}

document.getElementById('btn-scan').addEventListener('click', scanCompetitor);

// Init
checkStatus();
getActiveTab();
setInterval(getActiveTab, 2000);
