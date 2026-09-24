# Runbook: the PWA offline contract

Service worker, offline map tiles, map behaviour, and the regression
suite. Split out of CLAUDE.md 2026-09-24; the text below is unchanged.

### Offline guarantee (service-worker contract, rewritten 2026-09-22)
Incident: 2026-09-21, a full day in a new drainage with the PWA showing "Lake
data not accessible" despite being opened the night before. Root causes, all
fixed — keep these invariants:
- **A failed precache must fail the install.** `CRITICAL_URLS` (shell, data,
  Leaflet, manifest, icons) are all-or-nothing; any failure rejects `waitUntil`
  so the browser discards the new worker and the previous one keeps serving its
  complete cache. The old code `.catch`-ed the error, activated with an EMPTY
  cache, and deleted the good one — which a flaky trailhead link triggers
  reliably (17 KB worker script downloads, 7 MB precache doesn't).
  `OPTIONAL_URLS` (drainage JPGs) are best-effort. `activate` also refuses to
  delete old caches unless the new cache verifiably holds every critical URL.
- **Lookups are cache-agnostic.** `lakes_data.json` is looked up in this
  version's cache, then any cache (`caches.match`), under one canonical
  query-less key (`dataCacheKey`) — the `?_=<ts>` refresh polls used to add a
  2 MB copy per poll. The shell is re-cached on every clean network navigation.
- **Captive portals can't poison the cache**: `isCleanAssetResponse` rejects
  redirects and cross-origin 200s, and HTML is never stored as data.
- **Second copy outside the worker**: `index.html` keeps the last-good
  `lakes_data.json` text in IndexedDB (`uintas-data`/`kv`); `loadLakeData()`
  tries worker → any Cache Storage copy → IndexedDB, and only then shows the
  (now honest, with a Details list + Try again) failure screen.
- **"Sync & offline" panel** (bottom link): `OFFLINE_STATUS`/`OFFLINE_REPAIR`
  messages ask the worker which precache URLs are really present; shows
  ✓ Ready / ✗ Not ready + Repair, and the worker's event ring buffer
  (`/__push__/swlog` in `uintas-push-state`: install/activate/repair/fallback
  events) so the next failure is diagnosable from the phone. A startup
  self-check (8 s after load) auto-repairs when online and shows a red header
  chip otherwise. **Check for "✓ Ready" the night before a trip.**
Regression suite: `tests/offline/run.sh` — a fault-injecting static server
(`tests/offline/testserver.py`: version bump, 503 on one asset, captive
portal, dropped connections) driven by playwright-cli through first load →
offline reload → failed update (must not take over) → offline again →
successful update → portal → lost data entry (IndexedDB fallback + Repair) →
nothing left (honest error + Try again). 20 assertions; run it after touching
`service-worker.js` or the data-loading path in `index.html`.

### Web Frontend (`index.html`)
- **Progressive Web App**: Full offline functionality with service worker, no CDN dependencies (Tailwind CSS vendored as `tailwind.css`, Leaflet vendored under `vendor/leaflet/`)
- **JSON Data**: Loads `lakes_data.json` (generated from the database by `scripts/export_web_data.py`) with stocking records and photos nested per lake
- **Search & Filtering**: By drainage, species, depth, elevation, size, stocking years. Filters collapse by default with an active-count badge.
- **List / Map views**: One filtered result set, toggle between a list and a Leaflet map (USGS Topo + Imagery layers, status-colored pins, auto-fit, GPS "locate me"). A "Browse all lakes on the map" button opens the whole range without first picking a filter/drainage. View choice persists. Only `confirmed`/`manual` coordinates appear.
- **Offline map tiles (added 2026-08-24)**: tiles live in the version-INDEPENDENT
  `uintas-tiles` cache (spared by the SW activate cleanup, like `uintas-push-state`),
  served cache-first. Two fill paths: every tile viewed online is stored passively on
  the way through, and the **⤓ map control** opens an "Offline maps" panel that bulk
  downloads the current view's full tile pyramid (z6→chosen max, USGS layers only —
  OpenTopoMap is volunteer-run so it's passive-only) with progress/resume, saved-area
  management (`uintas-offline-areas` in localStorage), and `navigator.storage.persist()`.
  Background: Safari's HTTP cache evicts tiles within ~a day (USGS sends
  `max-age=86400`), which is why pre-panning an area used to go blank mid-trip.
  Tile layers set `crossOrigin: 'anonymous'` so responses are clean CORS 200s (both
  tile hosts send `ACAO: *`) — required for the SW to see cacheable statuses. The SW
  normalizes OpenTopoMap's `{a,b,c}` subdomains to one cache key. The old global
  "45MB iOS limit" gate in `cacheResponse` was removed deliberately: modern iOS grants
  installed PWAs gigabytes, and since `estimate()` counts ALL storage a single map
  download would have tripped it and silently stopped photo caching.
  **Tiles self-heal (2026-09-15):** a stored tile is only trusted if it's a 200 with an
  `image/*` content-type — the SW validates on write and on read (evicting + refetching
  bad entries), never stores opaque responses, and retries a failed fetch once; the
  bulk downloader applies the same rule (so "Re-check" repairs a poisoned area), and
  every Leaflet layer's `tileerror` evicts a tile that fails to decode and reloads it
  once. Cause: desktop Safari showed tile-aligned gray blocks that survived restarts —
  bad responses had been cached forever by the old `ok || opaque` check.
- **Map orientation**: The red GPS marker shows a compass heading arrow (DeviceOrientation; iOS prompts for permission on the locate tap). The map supports rotation — two-finger twist on mobile, Shift+drag on desktop — via the vendored `leaflet-rotate` plugin (`vendor/leaflet/leaflet-rotate.js`); the heading arrow compensates for the current map bearing.
- **Lake Details**: Modal views with stocking history, photos, DWR notes, "Open in Maps" link when coordinates exist
- **Mission Progress**: Header shows CAUGHT-status count toward the 100-waters goal

### PWA Cache Strategy
- Service worker caches all static assets and database
- Cache version is automatically updated by commit hook when changes are committed
- Works offline indefinitely when installed to iPhone home screen

