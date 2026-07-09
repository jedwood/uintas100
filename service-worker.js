const CACHE_NAME = 'uintas-v1783615814';
const MAX_CACHE_SIZE = 45 * 1024 * 1024; // Stay under iOS 50MB limit

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
                        if (cacheName !== CACHE_NAME) {
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

async function cacheResponse(request, response) {
    try {
        const cache = await caches.open(CACHE_NAME);

        // Check cache size before adding
        const usage = await navigator.storage?.estimate?.();
        if (usage && usage.usage > MAX_CACHE_SIZE * 0.8) {
            console.log('Service Worker: Cache approaching limit, skipping cache');
            return;
        }

        await cache.put(request, response);
    } catch (error) {
        // iOS 17 cache bugs - fail silently
        console.warn('Service Worker: Cache error (iOS bug):', error);
    }
}

// Handle messages from the main thread
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
