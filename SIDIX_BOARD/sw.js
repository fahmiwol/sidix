/**
 * SIDIX Command Board — Service Worker
 * Sprint 49 (PWA proper)
 *
 * Author:  Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
 * License: MIT (see repo LICENSE) - attribution required for derivative work.
 */

const CACHE_NAME = 'sidix-board-v1';
const SHELL_URLS = [
  '/chatbos/',
  '/chatbos/index.html',
  '/chatbos/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(SHELL_URLS).catch((e) => console.warn('[sw] pre-cache:', e))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.filter((n) => n.startsWith('sidix-board-') && n !== CACHE_NAME)
             .map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls — network-first
  if (
    url.pathname.startsWith('/agent/') ||
    url.pathname.startsWith('/sidix/') ||
    url.pathname.startsWith('/autonomous_dev/') ||
    url.pathname === '/health'
  ) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(
          JSON.stringify({ ok: false, error: 'offline' }),
          { headers: { 'Content-Type': 'application/json' }, status: 503 }
        )
      )
    );
    return;
  }

  // Static shell — cache-first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        fetch(event.request).then((fresh) => {
          if (fresh.ok) {
            caches.open(CACHE_NAME).then((c) => c.put(event.request, fresh.clone()));
          }
        }).catch(() => {});
        return cached;
      }
      return fetch(event.request).then((fresh) => {
        if (fresh.ok && url.pathname.startsWith('/chatbos/')) {
          caches.open(CACHE_NAME).then((c) => c.put(event.request, fresh.clone()));
        }
        return fresh;
      });
    })
  );
});

// Push notification handler
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : { title: 'SIDIX', body: 'Update' };
  event.waitUntil(
    self.registration.showNotification(data.title || 'SIDIX', {
      body: data.body || '',
      icon: '/chatbos/icons/icon-192.png',
      badge: '/chatbos/icons/icon-192.png',
      data: { url: data.url || '/chatbos/' },
      tag: data.tag || 'sidix-default',
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/chatbos/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((wins) => {
      for (const w of wins) {
        if (w.url.includes('/chatbos/') && 'focus' in w) return w.focus();
      }
      return clients.openWindow(url);
    })
  );
});
