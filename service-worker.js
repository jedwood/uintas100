const CACHE_NAME = 'uintas-v1790049934';

// A version-INDEPENDENT cache used as a tiny key/value store shared between this
// service worker and the page (the unseen-badge count, the last stocking report,
// the push config the SW needs to re-subscribe, and the worker event log). It must survive cache
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

// Resources to cache at install. Everything is served locally — no CDN
// dependence — so the app works offline even on its first install.
// Lake photos are cached lazily as they're viewed.
//
// CRITICAL assets are what the app needs to open and show lakes with zero
// connectivity. Install is all-or-nothing for these and FAILS if any one of
// them can't be fetched — a failed install leaves the previous worker (and its
// complete cache) in charge, and the browser simply retries the update at the
// next check. This is the fix for the 2026-09-21 trailhead incident: the old
// install swallowed precache errors, so on a flaky link the 17 KB worker
// script would download, the 7 MB precache would not, and the new worker
// activated anyway with an EMPTY cache and deleted the good one — "Lake data
// not accessible" for the whole day, with no network to recover.
const CRITICAL_URLS = [
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
    './vendor/leaflet/images/layers-2x.png'
];
// OPTIONAL assets (~5 MB of drainage maps): fetched at install too, but a
// failure here only logs — it must not block a data update. Anything missing
// is filled in later by the cache-first fetch path or the "Repair" button in
// the app's Offline panel.
const OPTIONAL_URLS = [
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

// A same-origin response worth caching as an app asset: a real 200 from OUR
// host, not a redirect. The redirect/origin test matters on the road — a
// motel or trailhead captive portal answers every URL with its own 200 HTML
// login page, and caching that as index.html or lakes_data.json would poison
// the offline copy exactly when it's about to be needed.
function isCleanAssetResponse(response, request) {
    if (!response || response.status !== 200 || response.redirected) return false;
    if (request && request.headers.get('range')) return false;
    if (response.url) {
        try { if (new URL(response.url).origin !== self.location.origin) return false; }
        catch (e) { return false; }
    }
    return true;
}
function looksLikeHtml(response) {
    return /text\/html/i.test(response.headers.get('content-type') || '');
}

// Fetch one asset for the precache. Every asset is fetched with cache: 'reload'
// so a version bump never re-caches a stale copy from the HTTP cache.
async function precacheOne(cache, url) {
    let request;
    try { request = new Request(url, { cache: 'reload' }); }
    catch (e) { request = new Request(url); }   // engine without RequestCache support
    const response = await fetch(request);
    if (!isCleanAssetResponse(response, request)) {
        throw new Error(`${url} → ${response.status}${response.redirected ? ' (redirected)' : ''}`);
    }
    await cache.put(url, response);
}

// Install: precache. Critical assets are all-or-nothing — the FIRST failure
// rejects waitUntil, the browser discards this worker as redundant, and the
// previous worker keeps serving its complete cache. Optional assets are
// best-effort.
self.addEventListener('install', event => {
    event.waitUntil((async () => {
        await swLog('install:start', { critical: CRITICAL_URLS.length, optional: OPTIONAL_URLS.length });
        // Only a cache this install created may be thrown away on failure. If
        // the name already exists (a worker change shipped without the hook's
        // version bump), it belongs to the ACTIVE worker — never delete that.
        const createdHere = !(await caches.has(CACHE_NAME));
        const cache = await caches.open(CACHE_NAME);
        try {
            await Promise.all(CRITICAL_URLS.map(url => precacheOne(cache, url)));
        } catch (error) {
            // Leave no half-filled cache behind for the next attempt to trust.
            if (createdHere) { try { await caches.delete(CACHE_NAME); } catch (e) { /* ignore */ } }
            await swLog('install:failed', { error: String(error && error.message || error) });
            console.warn('Service Worker: Install failed — keeping the previous version', error);
            throw error;
        }
        const optional = await Promise.allSettled(OPTIONAL_URLS.map(url => precacheOne(cache, url)));
        const missing = OPTIONAL_URLS.filter((u, i) => optional[i].status === 'rejected');
        await swLog('install:ok', { optionalMissing: missing });
        console.log('Service Worker: Precache complete', missing.length ? `(optional missing: ${missing.join(', ')})` : '');
    })());
    self.skipWaiting();
});

// Activate: clean up old caches — but only once this version's cache is proven
// complete. If a critical asset is somehow missing (it shouldn't be, given the
// install above), the old caches are KEPT so their copies remain reachable
// through the any-cache lookups in the fetch handler.
self.addEventListener('activate', event => {
    event.waitUntil((async () => {
        const cache = await caches.open(CACHE_NAME);
        const present = await Promise.all(CRITICAL_URLS.map(url => cache.match(url)));
        const missing = CRITICAL_URLS.filter((u, i) => !present[i]);
        if (missing.length) {
            await swLog('activate:incomplete', { missing });
            console.warn('Service Worker: Cache incomplete at activate, keeping old caches', missing);
            return;
        }
        const cacheNames = await caches.keys();
        const deleted = [];
        await Promise.all(cacheNames.map(cacheName => {
            // Spare the current app cache AND the version-independent
            // stores: push state (badge count / last report) and the
            // offline map tiles — both must persist across version bumps.
            if (cacheName !== CACHE_NAME && cacheName !== PUSH_STATE_CACHE && cacheName !== TILE_CACHE) {
                console.log('Service Worker: Deleting old cache', cacheName);
                deleted.push(cacheName);
                return caches.delete(cacheName);
            }
        }));
        await swLog('activate:ok', { deleted });
    })());
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

        // For navigation requests, always try network first, fall back to cache.
        // A clean network copy of the app shell is stored on the way through, so
        // the shell self-heals if the precached copy is ever lost — previously it
        // was cached ONLY at install, and a lost cache stayed lost until the next
        // complete precache.
        if (request.mode === 'navigate') {
            try {
                const networkResponse = await fetch(request);
                if (isCleanAssetResponse(networkResponse, request) && looksLikeHtml(networkResponse)
                        && /\/(index\.html)?$/.test(reqUrl.pathname)) {
                    await cacheResponse('./index.html', networkResponse.clone());
                }
                return networkResponse;
            } catch (error) {
                console.log('Service Worker: Network failed for navigation, trying cache');
                const cachedResponse = await caches.match('./index.html') || await caches.match('./');
                if (!cachedResponse) swLog('navigate:no-shell', {});
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
        if (reqUrl.pathname.endsWith('lakes_data.json')) {
            return staleWhileRevalidate(request);
        }

        // For static assets, try cache first — any cache, not just this
        // version's, so a copy left by a previous version still counts offline.
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // If not in cache, try network
        const networkResponse = await fetch(request);

        // Cache successful responses (excluding range requests). Same-origin
        // assets must also pass the redirect/origin check (captive portals).
        const sameOrigin = reqUrl.origin === self.location.origin;
        if (sameOrigin ? isCleanAssetResponse(networkResponse, request)
                       : (networkResponse.status === 200 && !request.headers.get('range'))) {
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
//
// A stored entry is only worth keeping if it is an actual image. Under load the
// USGS server can answer with something that isn't a tile, and a cache-first
// store that kept such a response served it on every visit thereafter — the
// symptom was tile-aligned gray blocks that survived quitting the app (Sept 2026,
// desktop Safari). So responses are validated on write, validated again on read
// (a bad entry is evicted and refetched), and opaque responses (status 0, which a
// CORS-mode <img> cannot render anyway) are never stored. index.html applies the
// same rule to its bulk downloader and evicts any tile whose image fails to decode.
function isGoodTile(resp) {
    return !!resp && resp.status === 200 && /^image\//i.test(resp.headers.get('content-type') || '');
}
// One retry after a short pause covers the common transient failures (a 429/5xx
// from a throttled tile server, or a dropped connection on a big desktop viewport
// that requests a hundred tiles at once). Leaflet itself never retries a tile.
async function fetchTileWithRetry(request) {
    let resp = null;
    for (let attempt = 0; attempt < 2; attempt++) {
        try { resp = await fetch(request); } catch (e) { resp = null; }
        if (isGoodTile(resp)) return resp;
        if (attempt === 0) await new Promise(r => setTimeout(r, 600));
    }
    return resp;
}
async function handleTile(request, tileKey) {
    const cache = await caches.open(TILE_CACHE);
    const cached = await cache.match(tileKey);
    if (cached) {
        if (isGoodTile(cached)) return cached;
        try { await cache.delete(tileKey); } catch (e) { /* ignore */ }
    }
    const networkResponse = await fetchTileWithRetry(request);
    if (isGoodTile(networkResponse)) {
        try { await cache.put(tileKey, networkResponse.clone()); } catch (e) { /* quota — serve anyway */ }
    }
    return networkResponse || Response.error();
}

// The lake data is stored under ONE canonical key (the query-less URL) no
// matter how it was requested. The page's refresh poll fetches
// `lakes_data.json?_=<timestamp>` to bust the HTTP cache, and the old code
// stored each of those under its unique URL — one more 2 MB copy on every
// launch, foreground, and 15-minute heartbeat.
function dataCacheKey(request) {
    const u = new URL(request.url);
    u.search = '';
    u.hash = '';
    return u.href;
}

async function staleWhileRevalidate(request) {
    const key = dataCacheKey(request);
    const cache = await caches.open(CACHE_NAME);
    // This version's copy first, then ANY cache's — the app shell was always
    // looked up across all caches, but the data wasn't, which is why a lost
    // current cache showed a perfectly styled shell with no lakes.
    let cached = await cache.match(key);
    if (!cached) {
        cached = await caches.match(key);
        if (cached) swLog('data:from-other-cache', {});
    }
    // A cache-busting poll wants the network's bytes when it can get them.
    const wantsFresh = request.cache === 'no-store' || new URL(request.url).search !== '';

    // Kick off the revalidation regardless of a cache hit.
    const revalidate = fetch(request).then(async networkResponse => {
        // Not a clean same-origin JSON 200 (e.g. a captive portal's HTML login
        // page) → don't touch the cache.
        if (!isCleanAssetResponse(networkResponse, request) || looksLikeHtml(networkResponse)) {
            return null;
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
        await cache.put(key, networkResponse.clone());
        if (changed) {
            const clients = await self.clients.matchAll({ includeUncontrolled: true });
            clients.forEach(client => client.postMessage({ type: 'DATA_UPDATED' }));
        }
        return networkResponse;
    }).catch(() => null);

    if (cached && !wantsFresh) return cached;
    // Offline (or a stale-poll while offline) falls back to whatever we have.
    const fresh = await revalidate;
    if (fresh) return fresh;
    if (cached) return cached;
    swLog('data:unavailable', {});
    return new Response('Offline', { status: 503 });
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
    // Offline-readiness check for the app's Offline panel: which precache
    // assets are actually present in THIS version's cache, plus the event log.
    // Replies on the MessageChannel port the page passed.
    if (event.data.type === 'OFFLINE_STATUS' && event.ports && event.ports[0]) {
        event.waitUntil(offlineStatus().then(status => event.ports[0].postMessage(status)));
    }
    // Repair: re-fetch whatever the status check found missing. Online only,
    // obviously — offline it just reports the same gaps.
    if (event.data.type === 'OFFLINE_REPAIR' && event.ports && event.ports[0]) {
        event.waitUntil(offlineRepair().then(status => event.ports[0].postMessage(status)));
    }
});

async function offlineStatus() {
    const cache = await caches.open(CACHE_NAME);
    const check = async urls => {
        const hits = await Promise.all(urls.map(u => cache.match(u)));
        return urls.filter((u, i) => !hits[i]);
    };
    const [criticalMissing, optionalMissing] = await Promise.all([check(CRITICAL_URLS), check(OPTIONAL_URLS)]);
    const data = await cache.match('./lakes_data.json');
    return {
        cacheName: CACHE_NAME,
        criticalTotal: CRITICAL_URLS.length,
        optionalTotal: OPTIONAL_URLS.length,
        criticalMissing,
        optionalMissing,
        dataDate: data ? (data.headers.get('last-modified') || data.headers.get('date') || null) : null,
        log: await pushStateGet('swlog', [])
    };
}

async function offlineRepair() {
    const before = await offlineStatus();
    const cache = await caches.open(CACHE_NAME);
    const results = await Promise.allSettled(
        before.criticalMissing.concat(before.optionalMissing).map(url => precacheOne(cache, url))
    );
    const failed = before.criticalMissing.concat(before.optionalMissing)
        .filter((u, i) => results[i].status === 'rejected');
    await swLog('repair', { attempted: results.length, failed });
    const after = await offlineStatus();
    after.repairFailed = failed;
    return after;
}

// Ring buffer of worker lifecycle events (installs, activations, cache
// deletions, data served from a fallback) in the version-independent KV
// cache, shown under "Details" in the app's Offline panel. Without this the
// 2026-09-21 failure was unreconstructable after the fact.
async function swLog(event, detail) {
    try {
        const log = await pushStateGet('swlog', []);
        log.push({ t: Date.now(), v: CACHE_NAME.replace(/^uintas-v1790049934/, ''), e: event, d: detail || {} });
        while (log.length > 60) log.shift();
        await pushStateSet('swlog', log);
    } catch (e) { /* best-effort */ }
}

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
