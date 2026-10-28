/**
 * SIDIX Socio Bot MCP social tools.
 *
 * Canonical tools:
 * - scan_instagram_profile
 * - scan_threads_profile
 * - scan_youtube_channel
 * - scan_twitter_profile
 * - analyze_social
 * - compare_social_accounts
 * - social_post_threads
 * - wa_send
 * - wa_receive
 */

const SOCIAL_TOOL_DEFS = [
  {
    name: 'scan_instagram_profile',
    description:
      'Scan profil Instagram publik. Jika extension bridge aktif akan pakai data DOM real; jika tidak, fallback ke Social Radar backend.',
    inputSchema: {
      type: 'object',
      properties: {
        username: { type: 'string', description: 'Username Instagram tanpa @' },
        include_posts: { type: 'boolean', default: false },
        profile_data: {
          type: 'object',
          description: 'Metadata hasil extension DOM scrape (opsional).',
        },
      },
      required: ['username'],
    },
  },
  {
    name: 'scan_threads_profile',
    description: 'Scan profil Threads atau sinyal account berdasarkan username.',
    inputSchema: {
      type: 'object',
      properties: {
        username: { type: 'string', description: 'Username Threads tanpa @' },
      },
      required: ['username'],
    },
  },
  {
    name: 'scan_youtube_channel',
    description: 'Scan channel YouTube (channel ID atau @handle) untuk analisis social radar.',
    inputSchema: {
      type: 'object',
      properties: {
        channel_id: { type: 'string', description: 'Channel ID (UC...) atau @handle' },
      },
      required: ['channel_id'],
    },
  },
  {
    name: 'scan_twitter_profile',
    description: 'Scan profil X/Twitter publik berdasarkan username.',
    inputSchema: {
      type: 'object',
      properties: {
        username: { type: 'string', description: 'Username X tanpa @' },
      },
      required: ['username'],
    },
  },
  {
    name: 'analyze_social',
    description: 'Analisis social account (engagement, sentiment, tier, advice) dari URL + metadata opsional.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'URL akun social' },
        metadata: { type: 'object', description: 'Metadata tambahan opsional' },
      },
      required: ['url'],
    },
  },
  {
    name: 'compare_social_accounts',
    description: 'Bandingkan 2-5 akun social dan urutkan berdasarkan engagement rate.',
    inputSchema: {
      type: 'object',
      properties: {
        accounts: {
          type: 'array',
          items: { type: 'string' },
          minItems: 2,
          maxItems: 5,
        },
      },
      required: ['accounts'],
    },
  },
  {
    name: 'social_post_threads',
    description: 'Post konten ke Threads melalui backend SIDIX.',
    inputSchema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Teks post' },
        link: { type: 'string', description: 'Link opsional' },
        media_type: { type: 'string', enum: ['TEXT', 'LINK'], default: 'TEXT' },
      },
      required: ['text'],
    },
  },
  {
    name: 'wa_send',
    description: 'Kirim pesan WhatsApp via WA bridge MCP (jika dikonfigurasi).',
    inputSchema: {
      type: 'object',
      properties: {
        to: { type: 'string', description: 'Nomor tujuan (format internasional)' },
        text: { type: 'string', description: 'Isi pesan' },
      },
      required: ['to', 'text'],
    },
  },
  {
    name: 'wa_receive',
    description: 'Ambil inbox/queue pesan WhatsApp via WA bridge MCP.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', default: 10 },
      },
      required: [],
    },
  },
];

const TOOL_ALIASES = new Map([
  ['social_scan_instagram', 'scan_instagram_profile'],
  ['social_scan_threads', 'scan_threads_profile'],
  ['social_scan_youtube', 'scan_youtube_channel'],
  ['social_scan_twitter', 'scan_twitter_profile'],
  ['social_radar_analyze', 'analyze_social'],
  ['social_compare', 'compare_social_accounts'],
]);

const TOOL_NAMES = new Set([
  ...SOCIAL_TOOL_DEFS.map((tool) => tool.name),
  ...TOOL_ALIASES.keys(),
]);

export function getSocialToolDefinitions() {
  return SOCIAL_TOOL_DEFS;
}

export function isSocialToolName(name) {
  return TOOL_NAMES.has(name);
}

function canonicalToolName(name) {
  return TOOL_ALIASES.get(name) || name;
}

async function fetchJson(url, init = {}, errorLabel = 'Request gagal') {
  const res = await fetch(url, init);
  let payload;
  try {
    payload = await res.json();
  } catch (_err) {
    payload = {};
  }
  if (!res.ok) {
    throw new Error(`${errorLabel}: HTTP ${res.status}`);
  }
  return payload;
}

async function analyzeViaRadar(brainUrl, url, metadata = {}) {
  return await fetchJson(
    `${brainUrl}/social/radar/scan`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, metadata }),
    },
    'Social Radar gagal',
  );
}

function normalizeRadarPayload(data) {
  if (!data || typeof data !== 'object') {
    return {
      engagement_rate: null,
      sentiment_score: null,
      tier: 'unknown',
      advice: '',
      strengths: [],
      status: 'unknown',
      raw: {},
    };
  }

  // Kompatibel dengan dua format:
  // 1) legacy: engagement_rate/sentiment_score/tier
  // 2) terbaru social_radar: metrics.engagement_rate/metrics.sentiment/metrics.tier
  const metrics = data.metrics || {};
  const engagement_rate =
    data.engagement_rate ??
    metrics.engagement_rate ??
    null;
  const sentiment_score =
    data.sentiment_score ??
    metrics.sentiment ??
    null;
  const tier =
    data.tier ??
    metrics.tier ??
    'unknown';

  return {
    engagement_rate,
    sentiment_score,
    tier,
    advice: data.advice || '',
    strengths: Array.isArray(data.strengths) ? data.strengths : [],
    status: data.status || 'ok',
    raw: data,
  };
}

function asNumber(value) {
  if (value == null) {
    return null;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function formatSocialResult(platform, handle, url, normalized, sourceLabel = 'backend') {
  const er = asNumber(normalized.engagement_rate);
  const sentiment = asNumber(normalized.sentiment_score);
  const lines = [
    `${platform} Scan: @${handle}`,
    `URL: ${url}`,
    `Source: ${sourceLabel}`,
    '',
    `Tier: ${normalized.tier || 'unknown'}`,
    `Engagement Rate: ${er == null ? '-' : `${er.toFixed(2)}%`}`,
    `Sentiment Score: ${sentiment == null ? '-' : sentiment.toFixed(2)}`,
  ];

  if (normalized.advice) {
    lines.push('', `Advice: ${normalized.advice}`);
  }
  if (normalized.strengths.length > 0) {
    lines.push('', `Strengths: ${normalized.strengths.join(', ')}`);
  }

  return { content: [{ type: 'text', text: lines.join('\n') }] };
}

async function scanInstagramWithBridge(username) {
  const bridge = (process.env.SIDIX_IG_EXTENSION_BRIDGE_URL || '').trim();
  if (!bridge) {
    return null;
  }
  const payload = await fetchJson(
    `${bridge.replace(/\/$/, '')}/scan`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform: 'instagram', username }),
    },
    'IG extension bridge gagal',
  );

  if (payload && payload.metadata) {
    return payload.metadata;
  }
  return null;
}

async function handleInstagram(args, brainUrl) {
  const username = String(args.username || '').replace(/^@/, '').trim();
  if (!username) {
    throw new Error('username wajib diisi');
  }

  const url = `https://www.instagram.com/${username}/`;
  let sourceLabel = 'social-radar';
  let metadata = args.profile_data && typeof args.profile_data === 'object' ? args.profile_data : null;

  if (!metadata) {
    try {
      metadata = await scanInstagramWithBridge(username);
      if (metadata) {
        sourceLabel = 'chrome-extension';
      }
    } catch (_err) {
      // fallback ke backend langsung
      metadata = null;
    }
  }

  const result = await analyzeViaRadar(brainUrl, url, metadata || { platform: 'instagram', username });
  const normalized = normalizeRadarPayload(result);
  return formatSocialResult('Instagram', username, url, normalized, sourceLabel);
}

async function handleThreads(args, brainUrl) {
  const username = String(args.username || '').replace(/^@/, '').trim();
  if (!username) {
    throw new Error('username wajib diisi');
  }

  try {
    const search = await fetchJson(
      `${brainUrl}/threads/search?q=${encodeURIComponent(username)}&limit=10`,
      {},
      'Threads search gagal',
    );
    return {
      content: [
        {
          type: 'text',
          text: `Threads Search: @${username}\n\n${JSON.stringify(search, null, 2).slice(0, 1800)}`,
        },
      ],
    };
  } catch (_err) {
    const url = `https://www.threads.net/@${username}`;
    const result = await analyzeViaRadar(brainUrl, url, { platform: 'threads', username });
    return formatSocialResult('Threads', username, url, normalizeRadarPayload(result), 'social-radar');
  }
}

async function handleYoutube(args, brainUrl) {
  const channelId = String(args.channel_id || '').trim();
  if (!channelId) {
    throw new Error('channel_id wajib diisi');
  }

  const normalizedHandle = channelId.replace(/^@/, '');
  const url = channelId.startsWith('UC')
    ? `https://www.youtube.com/channel/${channelId}`
    : `https://www.youtube.com/@${normalizedHandle}`;

  const result = await analyzeViaRadar(brainUrl, url, {
    platform: 'youtube',
    channel_id: channelId,
  });
  return formatSocialResult('YouTube', normalizedHandle, url, normalizeRadarPayload(result), 'social-radar');
}

async function handleTwitter(args, brainUrl) {
  const username = String(args.username || '').replace(/^@/, '').trim();
  if (!username) {
    throw new Error('username wajib diisi');
  }

  const url = `https://x.com/${username}`;
  const result = await analyzeViaRadar(brainUrl, url, { platform: 'twitter', username });
  return formatSocialResult('X/Twitter', username, url, normalizeRadarPayload(result), 'social-radar');
}

async function handleAnalyzeSocial(args, brainUrl) {
  const url = String(args.url || '').trim();
  if (!url) {
    throw new Error('url wajib diisi');
  }

  const result = await analyzeViaRadar(brainUrl, url, args.metadata || {});
  const normalized = normalizeRadarPayload(result);
  return {
    content: [
      {
        type: 'text',
        text: [
          `Social Analysis: ${url}`,
          '',
          `Tier: ${normalized.tier}`,
          `Engagement Rate: ${normalized.engagement_rate == null ? '-' : Number(normalized.engagement_rate).toFixed(2) + '%'}`,
          `Sentiment: ${normalized.sentiment_score == null ? '-' : Number(normalized.sentiment_score).toFixed(2)}`,
          '',
          `Advice: ${normalized.advice || '-'}`,
        ].join('\n'),
      },
    ],
  };
}

async function handleCompare(args, brainUrl) {
  const accounts = Array.isArray(args.accounts) ? args.accounts.slice(0, 5) : [];
  if (accounts.length < 2) {
    throw new Error('accounts minimal 2 item');
  }

  const results = [];
  for (const account of accounts) {
    const raw = String(account || '').trim();
    const url = raw.startsWith('http') ? raw : `https://www.instagram.com/${raw.replace(/^@/, '')}/`;

    try {
      const analyzed = normalizeRadarPayload(await analyzeViaRadar(brainUrl, url, {}));
      results.push({
        account: raw,
        url,
        er: asNumber(analyzed.engagement_rate),
        tier: analyzed.tier,
        sentiment: asNumber(analyzed.sentiment_score),
      });
    } catch (_err) {
      results.push({ account: raw, url, er: null, tier: 'unknown', sentiment: null });
    }
  }

  results.sort((a, b) => (b.er || 0) - (a.er || 0));

  const lines = ['Social Comparison', ''];
  results.forEach((row, idx) => {
    lines.push(
      `${idx + 1}. ${row.account} | ER=${row.er == null ? '-' : row.er.toFixed(2) + '%'} | tier=${row.tier} | sentiment=${row.sentiment == null ? '-' : row.sentiment.toFixed(2)}`,
    );
  });

  if (results[0]) {
    lines.push('', `Best candidate: ${results[0].account}`);
  }

  return { content: [{ type: 'text', text: lines.join('\n') }] };
}

async function handlePostThreads(args, brainUrl) {
  const text = String(args.text || '').slice(0, 500).trim();
  if (!text) {
    throw new Error('text wajib diisi');
  }

  const payload = await fetchJson(
    `${brainUrl}/threads/post`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        link_attachment: args.link || null,
        media_type: args.media_type || 'TEXT',
      }),
    },
    'Threads post gagal',
  );

  return {
    content: [
      {
        type: 'text',
        text: `Threads post terkirim\nID: ${payload.id || '-'}\nText: ${text}`,
      },
    ],
  };
}

function getWaBridgeBase() {
  return (process.env.SIDIX_WA_BRIDGE_URL || '').trim().replace(/\/$/, '');
}

async function handleWaSend(args) {
  const bridge = getWaBridgeBase();
  if (!bridge) {
    throw new Error('SIDIX_WA_BRIDGE_URL belum diset. Contoh: http://localhost:3977');
  }

  const to = String(args.to || '').trim();
  const text = String(args.text || '').trim();
  if (!to || !text) {
    throw new Error('to dan text wajib diisi');
  }

  const payload = await fetchJson(
    `${bridge}/wa/send`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, text }),
    },
    'WA send gagal',
  );

  return {
    content: [
      {
        type: 'text',
        text: `WA message queued\nTo: ${to}\nMessage ID: ${payload.id || payload.message_id || '-'}`,
      },
    ],
  };
}

async function handleWaReceive(args) {
  const bridge = getWaBridgeBase();
  if (!bridge) {
    throw new Error('SIDIX_WA_BRIDGE_URL belum diset. Contoh: http://localhost:3977');
  }

  const limit = Number.isFinite(Number(args.limit)) ? Math.max(1, Math.min(50, Number(args.limit))) : 10;
  const payload = await fetchJson(`${bridge}/wa/inbox?limit=${limit}`, {}, 'WA receive gagal');
  const messages = Array.isArray(payload.messages) ? payload.messages : [];

  return {
    content: [
      {
        type: 'text',
        text: `WA inbox (${messages.length} messages)\n\n${JSON.stringify(messages, null, 2).slice(0, 1800)}`,
      },
    ],
  };
}

export async function handleSocialTool(toolName, args, brainUrl) {
  const name = canonicalToolName(toolName);

  switch (name) {
    case 'scan_instagram_profile':
      return await handleInstagram(args, brainUrl);
    case 'scan_threads_profile':
      return await handleThreads(args, brainUrl);
    case 'scan_youtube_channel':
      return await handleYoutube(args, brainUrl);
    case 'scan_twitter_profile':
      return await handleTwitter(args, brainUrl);
    case 'analyze_social':
      return await handleAnalyzeSocial(args, brainUrl);
    case 'compare_social_accounts':
      return await handleCompare(args, brainUrl);
    case 'social_post_threads':
      return await handlePostThreads(args, brainUrl);
    case 'wa_send':
      return await handleWaSend(args);
    case 'wa_receive':
      return await handleWaReceive(args);
    default:
      throw new Error(`Social tool tidak dikenal: ${toolName}`);
  }
}
