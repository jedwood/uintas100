const CACHE_NAME = 'uintas-v1788473549';

// A version-INDEPENDENT cache used as a tiny key/value store shared between this
// service worker and the page (the unseen-badge count, the last stocking report,
// and the push config the SW needs to re-subscribe). It must survive cache
// version bumps, so the activate cleanup below deliberately spares it. Both
// contexts read/write it via caches.open(PUSH_STATE_CACHE) — never via fetch(),
// so it bypasses the fetch handler entirely.
const PUSH_STATE_CACHE = 'uintas-push-state';

// Map tiles live in their own version-INDEPENDENT cache (spared by the activate
// cleanup, like the push state). Two reasons: tiles saved for a trip must survive
// the cache-version bump every deploy triggers, and the tile store can grow far
// larger than the app shell so it must never be wiped along with it. Tiles get
// here two ways: passively (every tile viewed online is stored on the way through)
// and in bulk via the "Offline maps" download panel in index.html, which writes
// this same cache directly from the page.
const TILE_CACHE = 'uintas-tiles';

// A tile request is recognized by host. OpenTopoMap shards across subdomains
// a/b/c, so the SAME tile can be requested under three URLs — normalize to one
// cache key or two-thirds of cached tiles would be invisible on re-request.
function tileCacheKey(url) {
    if (url.hostname === 'basemap.nationalmap.gov') return url.href;
    if (/^[abc]\.tile\.opentopomap\.org$/.test(url.hostname)) {
        return url.href.replace(url.hostname, 'a.tile.opentopomap.org');
    }
    return null;
}

// Resources to cache immediately. Everything is served locally — no CDN
// dependence — so the app works offline even on its first install.
// Lake photos are cached lazily as they're viewed.
const urlsToCache = [
    './',
    './index.html',
    './tailwind.css',
    './lakes_data.json',
    './manifest.json',
    './favicon.ico',
    './icon-180.png',
    './icon-192.png',
    './icon-512.png',
    // Leaflet (vendored locally — map tiles still need a connection, but the
    // map library and app shell stay fully offline-capable)
    './vendor/leaflet/leaflet.js',
    './vendor/leaflet/leaflet-rotate.js',
    './vendor/leaflet/leaflet.css',
    './vendor/leaflet/images/marker-icon.png',
    './vendor/leaflet/images/marker-icon-2x.png',
    './vendor/leaflet/images/marker-shadow.png',
    './vendor/leaflet/images/layers.png',
    './vendor/leaflet/images/layers-2x.png',
    // Drainage maps — the ones you want at the trailhead
    './drainages/ashley-creek-drainage.jpg',
    './drainages/bear-river-drainage.jpg',
    './drainages/beaver-creek-drainage.jpg',
    './drainages/blacks-fork-drainage.jpg',
    './drainages/burnt-fork-drainage.jpg',
    './drainages/dry-gulch-drainage.jpg',
    './drainages/duchesne-river-drainage.jpg',
    './drainages/henrys-fork-drainage.jpg',
    './drainages/lake-fork-drainage.jpg',
    './drainages/provo-river-drainage.jpg',
    './drainages/rock-creek-drainage.jpg',
    './drainages/sheep-creek-carter-creek-drainage.jpg',
    './drainages/smiths-fork-drainage.jpg',
    './drainages/swift-creek-drainage.jpg',
    './drainages/uinta-river-drainage.jpg',
    './drainages/weber-river-drainage.jpg',
    './drainages/whiterocks-drainage.jpg',
    './drainages/yellowstone-river-drainage.jpg'
];

// Install event - cache core resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching core resources');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.warn('Service Worker: Install failed', error);
            })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        // Spare the current app cache AND the version-independent
                        // stores: push state (badge count / last report) and the
                        // offline map tiles — both must persist across version bumps.
                        if (cacheName !== CACHE_NAME && cacheName !== PUSH_STATE_CACHE && cacheName !== TILE_CACHE) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
    );
    self.clients.claim();
});

// Fetch event - handle requests with cache-first strategy for static assets
self.addEventListener('fetch', event => {
    event.respondWith(
        handleFetch(event.request)
    );
});

async function handleFetch(request) {
    try {
        // Sync API traffic (the edits server on :8802, or any /api/ path) must
        // never be answered from cache — pass it straight to the network. This
        // also covers POSTs, which the cache can't hold anyway.
        const reqUrl = new URL(request.url);
        if (request.method !== 'GET' || reqUrl.pathname.startsWith('/api/') || reqUrl.port === '8802') {
            return fetch(request);
        }

        // Map tiles: cache-first from the persistent tile store. Without this,
        // tiles only ever lived in Safari's HTTP cache — which iOS evicts within
        // ~a day (USGS sends max-age=86400), which is exactly how the map went
        // blank on day 2 of a trip despite pre-panning the whole area online.
        const tileKey = tileCacheKey(reqUrl);
        if (tileKey) {
            return handleTile(request, tileKey);
        }

        // For navigation requests, always try network first, fall back to cache
        if (request.mode === 'navigate') {
            try {
                const networkResponse = await fetch(request);
                return networkResponse;
            } catch (error) {
                console.log('Service Worker: Network failed for navigation, trying cache');
                const cachedResponse = await caches.match('./index.html') || await caches.match('/index.html');
                return cachedResponse || new Response('Offline - Please check your connection', {
                    status: 503,
                    statusText: 'Service Unavailable'
                });
            }
        }

        // lakes_data.json changes ~daily (stocking + notes sync). Serve it
        // stale-while-revalidate: hand back the cached copy instantly (fast +
        // offline), but always re-fetch in the background, update the cache,
        // and ping open clients when the bytes actually changed so a
        // long-running app can refresh itself without a restart or a
        // cache-version bump. Everything else stays cache-first.
        if (new URL(request.url).pathname.endsWith('lakes_data.json')) {
            return staleWhileRevalidate(request);
        }

        // For static assets, try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // If not in cache, try network
        const networkResponse = await fetch(request);

        // Cache successful responses (excluding range requests)
        if (networkResponse.status === 200 && !request.headers.get('range')) {
            await cacheResponse(request, networkResponse.clone());
        }

        return networkResponse;

    } catch (error) {
        console.warn('Service Worker: Fetch failed', error);

        // Return offline page for HTML requests
        if ((request.headers.get('accept') || '').includes('text/html')) {
            return new Response(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Offline - Uintas 💯</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc;
                               min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
                        .card { text-align: center; padding: 2rem; }
                        h1 { font-size: 1.875rem; color: #1f2937; margin-bottom: 1rem; }
                        p { color: #4b5563; margin-bottom: 1rem; }
                        .hint { font-size: 0.875rem; color: #6b7280; }
                        button { margin-top: 1rem; background: #334155; color: white; padding: 0.5rem 1rem;
                                 border: none; border-radius: 0.5rem; font-size: 1rem; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>🏔️ Uintas 💯</h1>
                        <p>You're offline, but the app should still work!</p>
                        <p class="hint">Try refreshing the page or check your connection.</p>
                        <button onclick="window.location.reload()">Retry</button>
                    </div>
                </body>
                </html>
            `, {
                headers: { 'Content-Type': 'text/html' }
            });
        }

        // For other requests, return a generic error
        return new Response('Offline', { status: 503 });
    }
}

// Cache-first for map tiles. Tiles are immutable in practice (USGS quads change
// on a years-long cadence), so a cached tile is always preferred — it's faster
// online and it's the whole point offline. On a miss we fetch and store the tile
// on the way through, so simply browsing the map while online builds up offline
// coverage that persists until explicitly cleared.
async function handleTile(request, tileKey) {
    const cache = await caches.open(TILE_CACHE);
    const cached = await cache.match(tileKey);
    if (cached) return cached;
    const networkResponse = await fetch(request);
    // The layers request tiles with crossOrigin=anonymous, so normally these are
    // clean 200s — but accept opaque responses too (e.g. a cached pre-upgrade
    // request shape) rather than silently not caching.
    if (networkResponse && (networkResponse.ok || networkResponse.type === 'opaque')) {
        try { await cache.put(tileKey, networkResponse.clone()); } catch (e) { /* quota — serve anyway */ }
    }
    return networkResponse;
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    // Kick off the revalidation regardless of a cache hit.
    const revalidate = fetch(request).then(async networkResponse => {
        if (!networkResponse || networkResponse.status !== 200 || request.headers.get('range')) {
            return networkResponse;
        }
        // Did the payload actually change? Compare clones so neither the
        // returned nor the cached body gets consumed.
        let changed = true;
        if (cached) {
            try {
                const [oldText, newText] = await Promise.all([
                    cached.clone().text(),
                    networkResponse.clone().text()
                ]);
                changed = oldText !== newText;
            } catch (e) { changed = true; }
        }
        await cache.put(request, networkResponse.clone());
        if (changed) {
            const clients = await self.clients.matchAll({ includeUncontrolled: true });
            clients.forEach(client => client.postMessage({ type: 'DATA_UPDATED' }));
        }
        return networkResponse;
    }).catch(() => null);

    // Offline (no cache yet) still needs the network attempt to resolve.
    return cached || (await revalidate) || new Response('Offline', { status: 503 });
}

async function cacheResponse(request, response) {
    try {
        const cache = await caches.open(CACHE_NAME);
        // No size gate here: the old "stay under iOS's 50MB" estimate() check
        // dates from iOS 13 — modern iOS grants installed PWAs gigabytes — and
        // since estimate() counts ALL storage, a single offline-map download
        // would have tripped it and silently stopped photo caching forever.
        // Quota pressure is handled by the catch below instead.
        await cache.put(request, response);
    } catch (error) {
        // iOS 17 cache bugs - fail silently
        console.warn('Service Worker: Cache error (iOS bug):', error);
    }
}

// Handle messages from the main thread
self.addEventListener('message', event => {
    if (!event.data) return;
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    // The page clears the app badge when it's opened/focused (the updates have
    // been seen), and resets our unseen counter so the next push starts fresh.
    if (event.data.type === 'CLEAR_BADGE') {
        event.waitUntil((async () => {
            await pushStateSet('badge', { n: 0 });
            if (self.navigator && self.navigator.clearAppBadge) {
                try { await self.navigator.clearAppBadge(); } catch (e) {}
            }
        })());
    }
    // The page hands us the info we need to re-subscribe on our own if the
    // push subscription is rotated by the OS while the app is closed.
    if (event.data.type === 'PUSH_CONFIG' && event.data.config) {
        event.waitUntil(pushStateSet('config', event.data.config));
    }
});

// ---- Web Push (iOS 16.4+ Home-Screen PWAs; standard VAPID) ----------------

// Tiny key/value helpers over PUSH_STATE_CACHE. Values are JSON. Reading via
// caches.open(...).match(...) bypasses the fetch handler, so these synthetic
// URLs never hit the network and never collide with real assets.
async function pushStateSet(key, value) {
    try {
        const cache = await caches.open(PUSH_STATE_CACHE);
        await cache.put('/__push__/' + key, new Response(JSON.stringify(value), {
            headers: { 'Content-Type': 'application/json' }
        }));
    } catch (e) { /* best-effort */ }
}
async function pushStateGet(key, fallback) {
    try {
        const cache = await caches.open(PUSH_STATE_CACHE);
        const res = await cache.match('/__push__/' + key);
        return res ? await res.json() : fallback;
    } catch (e) { return fallback; }
}

function b64ToU8(base64) {
    const padding = '='.repeat((4 - base64.length % 4) % 4);
    const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(b64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
}

self.addEventListener('push', event => {
    event.waitUntil(handlePush(event));
});

async function handlePush(event) {
    let payload = {};
    try {
        payload = event.data ? event.data.json() : {};
    } catch (e) {
        try { payload = { body: event.data.text() }; } catch (_) { payload = {}; }
    }
    const title = payload.title || '🏔️ Uintas';
    const body = payload.body || 'New stocking update';

    // Cumulative badge: this batch adds to whatever the user hasn't opened yet.
    // setAppBadge takes an absolute number, so we track the running total here.
    const batch = Number(payload.badge) || 0;
    if (batch > 0) {
        const prev = (await pushStateGet('badge', { n: 0 })).n || 0;
        const total = prev + batch;
        await pushStateSet('badge', { n: total });
        if (self.navigator && self.navigator.setAppBadge) {
            try { await self.navigator.setAppBadge(total); } catch (e) {}
        }
    }

    // Stash the full report so tapping the notification shows all of it even on
    // a cold start — the payload is the source of truth, so this never races the
    // github.io redeploy of lakes_data.json (which can lag the push by a minute).
    if (payload.report) await pushStateSet('report', payload.report);

    // If a window is already open, let it fold in the report/badge live.
    const clients = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
    clients.forEach(c => c.postMessage({ type: 'PUSH_RECEIVED', report: payload.report || null }));

    await self.registration.showNotification(title, {
        body,
        icon: './icon-192.png',
        badge: './icon-192.png',
        tag: 'uintas-stocking',   // collapse a burst into one notification
        renotify: true,
        data: { path: payload.path || './?view=stocking-report' }
    });
}

self.addEventListener('notificationclick', event => {
    event.notification.close();
    const path = (event.notification.data && event.notification.data.path)
        || './?view=stocking-report';
    event.waitUntil((async () => {
        const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
        for (const c of all) {
            if ('focus' in c) {
                await c.focus();
                c.postMessage({ type: 'SHOW_STOCKING_REPORT' });
                return;
            }
        }
        if (self.clients.openWindow) await self.clients.openWindow(path);
    })());
});

// If iOS rotates/expires the subscription while the app is closed, re-subscribe
// using the config the page stashed, and re-register it with the Mini. Falls
// back to a pending stash the page flushes on its next open.
self.addEventListener('pushsubscriptionchange', event => {
    event.waitUntil((async () => {
        const cfg = await pushStateGet('config', null);
        if (!cfg || !cfg.appServerKey) return;
        let sub;
        try {
            sub = await self.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: b64ToU8(cfg.appServerKey)
            });
        } catch (e) { return; }
        const subJson = sub.toJSON();
        let posted = false;
        if (cfg.serverUrl) {
            try {
                const r = await fetch(cfg.serverUrl + '/api/push/subscribe', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ subscription: subJson, device: cfg.deviceId || 'sw' })
                });
                posted = r.ok;
            } catch (e) { /* stash below */ }
        }
        if (!posted) await pushStateSet('pendingSubscription', subJson);
    })());
});
