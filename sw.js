// Kobra – Service Worker: Offline-Cache und synchroner Kanal fuer input()/GUI.
const VERSION = 'kobra-v1.0.0';
const APP_CACHE = `${VERSION}-app`;
const RUNTIME_CACHE = 'kobra-runtime-v1';
const APP_FILES = [
  './', './index.html', './styles.css', './manifest.webmanifest', './py-bundle.json', './worker.js',
  './vendor/vendor.js',
  './js/app.js', './js/ui.js', './js/storage.js', './js/editor.js', './js/runner.js', './js/gui.js',
  './js/git.js', './js/packages.js', './js/snippets.js', './js/icons.js',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png', './icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(APP_CACHE);
    await cache.addAll(APP_FILES.map(u => new Request(u, { cache: 'reload' })));
    if (!(await self.clients.matchAll()).length) await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith('kobra-v') && key !== APP_CACHE) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});

// ------------------------------------------------------- synchroner Kanal
const waiting = new Map();   // token/id -> resolve
const values = new Map();    // token/id -> wert (falls Antwort vor Anfrage kam)
const queues = new Map();    // token -> [events]
const eventWaiters = new Map(); // token -> {resolve, timer}

function respondJson(text, status = 200) {
  return new Response(text, { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
}

function waitForValue(key) {
  if (values.has(key)) {
    const v = values.get(key);
    values.delete(key);
    return Promise.resolve(respondJson(v));
  }
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      if (waiting.get(key)?.resolve === resolve) waiting.delete(key);
      resolve(new Response(null, { status: 204 }));
    }, 25000);
    waiting.set(key, { resolve, timer });
  });
}

function waitForEvents(token, waitMs) {
  const q = queues.get(token);
  if (q && q.length) {
    queues.set(token, []);
    return Promise.resolve(respondJson(JSON.stringify(q)));
  }
  const prev = eventWaiters.get(token);
  if (prev) { clearTimeout(prev.timer); prev.resolve(respondJson('[]')); eventWaiters.delete(token); }
  if (!waitMs) return Promise.resolve(respondJson('[]'));
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      if (eventWaiters.get(token)?.resolve === resolve) eventWaiters.delete(token);
      resolve(respondJson('[]'));
    }, Math.min(waitMs, 25000));
    eventWaiters.set(token, { resolve, timer });
  });
}

function pushEvents(token, events) {
  const q = queues.get(token) || [];
  q.push(...events);
  queues.set(token, q);
  const w = eventWaiters.get(token);
  if (w) {
    eventWaiters.delete(token);
    clearTimeout(w.timer);
    // kurz sammeln, damit zusammengehoerige Ereignisse gemeinsam ankommen
    setTimeout(() => {
      const items = queues.get(token) || [];
      queues.set(token, []);
      w.resolve(respondJson(JSON.stringify(items)));
    }, 0);
  }
}

self.addEventListener('message', (event) => {
  const msg = event.data || {};
  if (msg.type === 'sync-reply') {
    const key = `${msg.token}/${msg.id}`;
    const w = waiting.get(key);
    if (w) { waiting.delete(key); clearTimeout(w.timer); w.resolve(respondJson(msg.value)); }
    else values.set(key, msg.value);
  } else if (msg.type === 'gui-events') {
    pushEvents(msg.token, msg.events || []);
  } else if (msg.type === 'clear-events') {
    queues.set(msg.token, []);
  } else if (msg.type === 'skip-waiting') {
    self.skipWaiting();
  }
});

// ------------------------------------------------------------- Abrufe
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  const syncPrefix = new URL('__kobra__/', self.registration.scope).pathname;

  if (url.origin === self.location.origin && url.pathname.startsWith(syncPrefix)) {
    const parts = url.pathname.slice(syncPrefix.length).split('/');
    if (parts[0] === 'ping') { event.respondWith(new Response('pong', { headers: { 'Cache-Control': 'no-store' } })); return; }
    if (parts[0] === 'sync') { event.respondWith(waitForValue(`${parts[1]}/${parts[2]}`)); return; }
    if (parts[0] === 'events') {
      event.respondWith(waitForEvents(parts[1], parseInt(url.searchParams.get('wait') || '0', 10)));
      return;
    }
    event.respondWith(new Response('not found', { status: 404 }));
    return;
  }

  if (req.method !== 'GET') return;

  // Pyodide und Wheels aendern sich nie: zuerst Cache
  if (url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'files.pythonhosted.org') {
    event.respondWith(cacheFirst(req, RUNTIME_CACHE));
    return;
  }
  // PyPI-Metadaten: zuerst Netz, offline aus dem Cache
  if (url.hostname === 'pypi.org') {
    event.respondWith(networkFirst(req, RUNTIME_CACHE));
    return;
  }
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req, APP_CACHE, true));
  }
});

async function cacheFirst(req, cacheName, ignoreSearch) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreSearch: !!ignoreSearch });
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok && (res.type === 'basic' || res.type === 'cors')) {
    cache.put(req, res.clone()).catch(() => {});
  }
  return res;
}

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone()).catch(() => {});
    return res;
  } catch (e) {
    const hit = await cache.match(req);
    if (hit) return hit;
    throw e;
  }
}
