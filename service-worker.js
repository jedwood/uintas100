const CACHE_NAME = 'uintas-v1756149517';
const MAX_CACHE_SIZE = 45 * 1024 * 1024; // Stay under iOS 50MB limit

// Resources to cache immediately
const urlsToCache = [
    './',
    './index.html',
    './uinta_lakes.db',
    './manifest.json',
    // External resources
    'https://cdn.tailwindcss.com',
    'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.js',
    'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.wasm'
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
        if (request.headers.get('accept').includes('text/html')) {
            return new Response(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Offline - Uintas 💯</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-slate-50 min-h-screen flex items-center justify-center">
                    <div class="text-center p-8">
                        <h1 class="text-3xl font-bold text-gray-800 mb-4">🏔️ Uintas 💯</h1>
                        <p class="text-gray-600 mb-4">You're offline, but the app should still work!</p>
                        <p class="text-sm text-gray-500">Try refreshing the page or check your connection.</p>
                        <button onclick="window.location.reload()" class="mt-4 bg-slate-700 text-white px-4 py-2 rounded-lg">
                            Retry
                        </button>
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