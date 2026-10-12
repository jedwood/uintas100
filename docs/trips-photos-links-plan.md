# Plan: links, photos, trips, planned trips, home redesign

Started 2026-10-10. Built in phases, **one phase per fresh Claude session**, to
keep context windows tight. Each session: read this file (only this file and
the code it names; don't re-survey the repo), do the next unchecked phase,
verify it, tick it off here, and note anything the next phase needs under
"Handoff notes".

> **Kick-off prompt for a new session:** "Continue
> docs/trips-photos-links-plan.md — do the next unchecked phase."

## Status

- [x] **Phase 0** — search-field polish (2026-10-10, committed with this plan)
- [x] **Phase 1** — backend: journal store, edits-server endpoints, exporter, hook (2026-10-10, uncommitted)
- [x] **Phase 2** — client data layer: journal state + sync, media store, image pipeline (2026-10-10, uncommitted)
- [x] **Phase 3** — lake modal: Links card, Junesucker source link, Trips & photos card, photo lightbox (2026-10-10, uncommitted)
- [x] **Phase 4** — trip modal: view + editor, planned trips (2026-10-10, uncommitted)
- [x] **Phase 5** — top level: Photos / Trip reports / Future trips lists, drainage scoping, Sync-panel photo status (2026-10-10, uncommitted)
- [x] **Phase 6** — data migration: old `trip_reports` → Trips; URLs in `jed_notes` → Links (2026-10-10, docs live in ff6236a; script + month-only dates uncommitted; clearing `trip_reports` waits for Jed's review after Phase 7)
- [ ] **Phase 7** — ship: commit/push, restart edits server, phone test over Tailscale, runbooks (2026-10-12: shipped + docs done; **phone test pending**, see handoff notes)
- [ ] **Phase 8** — home page redesign (design mode)

Phases 1–5 can't be published piecemeal without care: Phase 1's server
endpoints are harmless to deploy alone, but don't push UI that writes journal
docs before the Mini's edits server understands them (Phase 7 restarts it).
Leaving work uncommitted between sessions is safe (automation commits through
a private index; see CLAUDE.md).

## What Jed asked for (2026-10-10)

1. **Links on lakes**, as first-class objects with an elegant UX (they used to
   be pasted into notes and got mangled by the Apple Notes era). Also: for
   lakes with Junesucker notes, show the **source page link** at the top of
   that section, before the cached text.
2. **Photos & screenshots**: pics at the lakes, screenshots of maps/trails.
3. **Trips**, replacing the per-lake "Trip Reports" text field. One report
   spans many lakes (no repeating across lakes). A trip has a description,
   photos and links; lakes are attached in a structured way. Each photo can
   optionally be tagged with one or more lakes. A lake's detail shows links to
   its trips **and** the photos tagged with that lake.
   - **3b. Future (planned) trips**: same structure, no date taken.
4. Top-level access to **all photos, all trip reports, all future trips**, and
   the same three **scoped to a drainage** (a trip can span drainages).
5. Then **redesign the home page** (design mode; Claude Design if available)
   now that it carries ~10 entry points: search, starred, map, recent
   stockings, jump to drainage, rotenone, photos, trip reports, future trips,
   filters.
6. Tiny fixes: drop the "Lake Name or Designation" label above search; add a
   clear (×) button that empties the field and keeps the cursor in it. **Done
   in Phase 0.**

## Decisions already made (don't re-ask)

- **Photos are private, on the Mini.** Repo is public and `.git` is ~617 MB.
  Image files live in a gitignored `data/media/` on the Mini and are served by
  the edits server at `/api/media/…` — reachable over the Tailscale :8443 proxy
  (or `olaf.local:8802` on LAN). Not on github.io. Each device keeps what it
  has viewed + the photos it took in IndexedDB for offline use.
- **Trip text, captions, links and photo metadata are public** (committed),
  same as `jed_notes` is today — **except photo location**, see next.
- **Save each photo's GPS location when it has one** (Jed, 2026-10-10: "could
  be really helpful for future ref"). It is extracted from EXIF on the device
  *before* re-encoding strips it, and stored **privately with the photo on the
  Mini** as a sidecar `data/media/<id>.json` — never in the public
  `journal.json` (precise coordinates of where Jed was, in public git history
  forever, would undercut the photos-are-private decision). If Jed later wants
  it public, moving it into the photo doc is a small change.
- **Old per-lake `trip_reports` get converted into Trips** (hand-grouped:
  one trip per outing, linked to all lakes it covered). The old field stays
  visible read-only as "Older notes" until Jed has reviewed and says it can go.
- Junesucker source URL: recovered **at export time** by matching each lake's
  `junesucker_notes` to `data/junesucker_pages/<slug>.md` (identical text — the
  scraper writes both) and `slug → url` via `data/uinta_lake_links.csv`.
  Verified 2026-10-10: **40/40** lakes match. No new DB column.

## Architecture

### Storage: `data/journal.json` (committed, outside the DB)

User-authored documents live in one JSON file, **not** in `uinta_lakes.db`,
the same reasoning as `data/collections.json` / `data/app_edits_log.jsonl`:
no seed/rebuild/verify changes, trivially diffable. Written only by the edits
server on the Mini (single-writer model holds).

```json
{
  "version": 1,
  "trips":  [ { "id": "t-lq2x9a-k3f1", "updated": "2026-10-10T18:22:01.123Z",
                "title": "Toomset + Amethyst w/ Ryan",
                "planned": false, "date": "2024-10-12", "end_date": "2024-10-14",
                "when": null,
                "body": "free text…",
                "lakes": ["BR-25", "BR-28"],
                "links": [ { "url": "https://…", "title": "…" } ] } ],
  "photos": [ { "id": "p-lq2xb1-9d0e", "updated": "…",
                "trip": "t-lq2x9a-k3f1",          // or null (photo on a lake only)
                "lakes": ["BR-28"],                // optional tags, may be []
                "caption": "", "taken": "2024-10-13T09:41:00", "w": 2048, "h": 1536 } ],
  "links":  [ { "id": "l-…", "updated": "…", "lake": "BR-29",
                "url": "https://…", "title": "…", "note": "" } ]
}
```

- `date` / `end_date` are `YYYY-MM-DD` or, when the day is unknown,
  month-only `YYYY-MM` (both the same precision; added in Phase 6 for the old
  reports). Shown as "Oct 2024" / "Jul–Aug 2024"; the editor has a "Month
  only" checkbox.
- `planned: true` ⇒ future trip: `date`/`end_date` null, optional free-text
  `when` ("summer 2027"). "Mark as done" flips `planned` and asks for a date.
- Trip links are **embedded** in the trip (edited together). Lake links are
  their own `links` docs.
- Deletes are **tombstones** (`"deleted": true`, other fields may be dropped)
  so last-write-wins sync can propagate them; the exporter filters them out.
- IDs are client-generated: `<kind letter>-<Date.now() base36>-<4 random>`.
- Lists are written sorted by `id` (≈ chronological), pretty-printed (indent 1)
  for readable diffs.

### Sync: per-document last-write-wins

Mirrors the existing per-(lake, field) model in `scripts/edits_server.py`:

- `POST /api/journal` `{device, docs:[{kind, doc}]}` → per doc
  `applied | superseded{current} | error{message}`. Apply iff
  `doc.updated >= stored.updated`. Validate: kind ∈ trip/photo/link; lake
  designations exist in `lakes`; `url` is http(s) ≤ 2000 chars; caps: title
  200, body 50k, caption 2k, ≤100 lakes, ≤50 links; `photo.trip` may refer to
  a trip not yet synced (allowed). Append each applied doc to
  `data/app_edits_log.jsonl` as `{"kind":…, "id":…, "ts":…, "device":…}` (no
  payload — the journal itself is the record).
- `GET /api/user-data` gains `"journal": {trips, photos, links}` (incl.
  tombstones), so other devices' docs fold in without waiting for github.io.
- `PUT /api/media/<id>.jpg` and `PUT /api/media/<id>_t.jpg` — raw
  `image/jpeg` body, ≤ 12 MB, id must match `^p-[a-z0-9]+-[a-z0-9]{4}$`,
  atomic write (tmp + rename) into `data/media/`. Idempotent.
- `GET /api/media/<id>.jpg|_t.jpg` — CORS `*`,
  `Cache-Control: private, max-age=31536000, immutable`; 404 if absent.
- `PUT /api/media/<id>.json` — the private location sidecar, ≤ 4 KB, validated
  shape `{lat, lng, alt|null, gps_time|null, taken|null, make|null,
  model|null}` (lat/lng finite and in range; nothing else accepted).
  `GET /api/user-data` gains `"media_meta": {<id>: sidecar, …}` — only ever
  served by the Mini, never exported to `lakes_data.json`.
- `GET /api/link-title?url=…` — the Mini fetches the page (6 s timeout, read
  ≤ 300 KB, browser-ish UA since Cloudflare 403s urllib's) and returns
  `{title}` from `og:title` or `<title>`. The client uses it to prefill the
  title while adding a link (it can't fetch cross-origin pages itself).
  Offline/failed → blank title; the UI then shows hostname + path.
- Committer: `commit_own_files([... "data/journal.json"], …)`. `data/media/`
  is never committed (gitignored).
- **Hardening while in there:** the handler falls back to
  `SimpleHTTPRequestHandler` static serving of the whole repo, so over
  Tailscale `/data/push/` (VAPID private key + subscriptions) is fetchable. Return
  404 for paths under `/data/push/` and `/data/media/` in `do_GET`.

### Export: `scripts/export_web_data.py`

- Load `data/journal.json` (missing file ⇒ empty), drop tombstones, drop and
  **warn** (don't raise — automation commits must not fail) on unknown lake
  designations. Emit top-level `"journal": {trips, photos, links}` in
  `lakes_data.json`.
- Per lake: `"junesucker_url"` via the content match described above.
- `.githooks/pre-commit`: also run `export_web_data.py` + `git add
  lakes_data.json` when `data/journal.json` is staged (today it only fires on
  `uinta_lakes.db`). Seeds only for the DB case.

### Client (`index.html`)

**Journal state.** `journalDocs: Map<"kind:id", doc>` built in `hydrate()`
from, in LWW order: `data.journal` (published) → last server snapshot
(`localStorage['uintas-server-journal']`, so offline reloads still show other
devices' recent docs) → local pending (`localStorage['uintas-local-journal']`,
`{ "kind:id": {kind, doc, synced} }`). Derived indices: `tripsByLake`,
`photosByLake` (explicit tags only — per Jed), `photosByTrip`, `linksByLake`.
`queueJournal(kind, doc)` stamps `updated`, stores pending, re-indexes,
re-renders. Prune a local entry once synced and the published/server copy's
`updated` ≥ it.

**Sync.** Extend `syncNow()`: after lake-field edits, (1) PUT pending media
blobs, (2) POST pending journal docs (superseded ⇒ drop local, ingest
`current`), (3) fold `user-data.journal` in, (4) background-prefetch missing
thumbnails (concurrency 3). Sync chip / panel counts include pending docs +
pending uploads.

**Media store.** Separate IndexedDB `uintas-media` (not the SW caches, so
`service-worker.js` and the offline contract are untouched):
`blobs` (key `"<id>:f"` / `"<id>:t"` → Blob) and `meta` (id →
`{uploadedF, uploadedT}`). Render images as
`<img data-pid=… data-size="t|f">` placeholders; `hydrateMedia(root)` resolves
each via IDB → else `fetch(syncUrl + '/api/media/…')` (store blob) → else an
"offline" placeholder. Cache object URLs in a Map. Call
`navigator.storage.persist()` once (best effort).

**Image pipeline (on add).** `<input type=file accept="image/*" multiple>`.
Per file: parse EXIF from the original bytes (tiny parser:
DateTimeOriginal → `taken`; GPSLatitude/Longitude(+Ref)/Altitude/DateStamp,
Make/Model → the **private location sidecar**, saved in the `meta` IDB store
and uploaded as `<id>.json` alongside the image). GPS also drives **suggested
nearest lakes within ~1.2 km** as one-tap tags. Decode with
`createImageBitmap` (fallback `<img>`), draw to canvas: full ≤ 2048 px long
side JPEG q 0.86, thumb ≤ 480 px q 0.8 — re-encoding strips all EXIF from the
image files themselves (the sidecar is the one place location lives).
Undecodable (e.g. HEIC on desktop Chrome) ⇒ friendly error. Screenshots (PNG)
go through the same path and simply have no sidecar. Caveat to verify on the
phone in Phase 7: iOS's photo picker can strip location from the file it hands
a web page unless the picker's "Options → Location" is on (iOS 17+); if GPS is
missing from real phone uploads, surface a one-line hint in the add-photo UI.

**Modal layering.** Existing: lake modal z 1200, stocking report 1150, one
history entry per modal stack (`pushModalState`), `hideModals()` on
popstate. New: journal-list modal z 1150 (rows open trips/lakes above it),
trip modal z 1250, photo lightbox z 1400 (no history entry; ×, backdrop,
Escape, swipe). Trip ↔ lake hops: hide the one being left and push
`{type, id}` onto a new `crossStack`; `modalBack()` pops `lakeNavStack`
first, then `crossStack`. Deep link `#trip-<id>`. Add the new modals to
`hideModals()`, the Escape handler, the popstate handler, and
`lockBodyScroll` names (`trip`, `journal`, `photo`).

**Tailwind.** `tailwind.css` is pre-generated: after adding classes, run
`npx tailwindcss@3.4.17 -o tailwind.css --content "./index.html" --minify`, or
put component styles in the `<style>` block (Phase 0 did the latter).

## Phases

### Phase 1 — backend
Files: new `scripts/journal_store.py` (load/save/validate/apply, used by
server + exporter), `scripts/edits_server.py`, `scripts/export_web_data.py`,
`.githooks/pre-commit`, `.gitignore` (`data/media/`),
`tests/auto_commit_isolation.sh` (if the committer's path list changes what it
asserts).
Verify: test harness `python3 scripts/edits_server.py --db /tmp/x.db --log
/tmp/x.jsonl --no-git --port 8899` (add a `--journal`/`--media` override so
tests never touch the real files); curl every endpoint incl. LWW
superseded, bad lake, bad url, oversized upload, tombstone, `/data/push/` 404;
`python3 scripts/export_web_data.py` emits `journal` + 40 `junesucker_url`s;
`python3 scripts/verify_rebuild.py` still exits 0; `tests/auto_commit_isolation.sh`
passes.

### Phase 2 — client data layer
Journal state + indices, `queueJournal`, sync extension, media IDB store,
`hydrateMedia`, image pipeline + EXIF + nearest-lake helper. No visible UI
beyond counts in the sync chip. Verify with Playwright against the Phase-1
harness: queue docs offline → sync → server file has them; a second browser
context sees them via `/api/user-data`; upload of a fixture JPEG lands in the
harness media dir with EXIF stripped (check with `exiftool` or a byte scan for
`Exif`), and a GPS-tagged fixture produces a correct `<id>.json` sidecar
(compare against `exiftool -n -GPSLatitude -GPSLongitude`).

### Phase 3 — lake modal
- Junesucker card: "View original on junesucker.com ↗" line under the heading,
  above the collapsible text.
- **Links card**: rows = title (or hostname + path), hostname chip, optional
  note; tap opens in a new tab. "＋ Add link": paste URL → prefill title via
  `/api/link-title` when reachable → optional note → Save. Edit/delete per row.
- **Trips & photos card** (below My Record): horizontal thumbnail strip of
  photos tagged with this lake (tap → lightbox over that set); trip rows
  ("🥾 Oct 12–14, 2024 · Toomset + Amethyst w/ Ryan", "🧭 Planned · …");
  action pills "＋ Photo" (lake-tagged, no trip) / "＋ Trip" (new trip
  prefilled with this lake) / "＋ Plan". Collapse to just the action pills
  when empty, so unvisited lakes stay uncluttered.
- My Record: drop the Trip Reports textarea; show old `trip_reports` text
  read-only as "Older notes" (until Phase 6 review is done).
- **Photo lightbox**: full image (thumb shown while full loads), caption,
  taken date, "📍 Open in Maps" when the sidecar has a location, lake chips (→ lake), "From trip: … →", prev/next + swipe, edit
  caption/tags inline, delete (tombstone + keep blob until synced).
Verify with Playwright at iPhone size + screenshots, and keep
`tests/journal/run.sh` green.

### Phase 4 — trip modal
View: title, date range or "Planned · when", lake chips, body (autolinked,
`whitespace-pre-line`), photo grid, links. Buttons: Edit; for planned,
"Mark as done". Editor: title; Taken/Planned segmented toggle; date + optional
end date | free-text when; lake picker (chips + type-ahead reusing the search
matcher; GPS suggestions from added photos); body; links (URL + auto title);
photos grid with "＋ Add photos" tile, per-photo caption + lake tags (trip's
lakes as toggle chips + "other lake…" search) + remove. Editor works on a
draft; **Save** queues the trip + all photo docs; **Cancel** on a new trip
deletes its unsaved blobs. Delete trip ⇒ tombstone trip; ask whether to delete
its photos or keep them (lake-tagged) unattached.

### Phase 5 — top level + drainage scoping
- Home: "📷 Photos", "🥾 Trip reports", "🧭 Future trips" entry points
  (simple buttons for now; Phase 8 redesigns the page).
- Journal-list modal with three tabs. Trips: cards newest first (first-photo
  thumb, title, date, lake names, snippet) + "＋ New trip". Planned: same,
  most-recently-updated first + "＋ Plan a trip". Photos: grid grouped by
  trip/month, lightbox over the visible set, "＋ Add photos" (opens photo editor
  for tags).
- Scope: optional drainage filter shown as a removable chip. A trip is in a
  drainage if any of its lakes is; a photo if any of its tags is (untagged
  trip photos inherit the trip's lakes for scoping only).
- Drainage view: a slim "🥾 N trips · 🧭 N planned · 📷 N photos" row between
  `#results-lead` and the list/map (visible in both views); `showDrainageMap`'s
  scroll target becomes that row when it's non-empty.
- Sync & offline panel: "N photos waiting to upload", "Save all full-size
  photos offline" button with progress.

### Phase 6 — migration
One-off script (commit it under `scripts/`, run once on the Mini) that writes
docs into `data/journal.json`:
- Trips from old `trip_reports` (16 lakes: A-14, A-18, A-22, BR-14, BR-15,
  BR-25, BR-28, BR-29, DF-11, G-15, G-18, G-49, LF-44, P-60, W-21, W-62).
  Hand-group by outing with Jed's names/dates. Obvious groupings from the
  text: BR-25 + BR-28 (Oct 2024, Ryan); BR-14 + BR-15 (Aug/Labor Day 2024,
  Dilworth) — check dates; G-15 + G-18 + G-49 entries span 2020 (Highline
  with Dilworth/Hui/John) and 2024 (Dilworth + Ryan); A-14 + A-18 (Sep 2026,
  Ryan, Norway Flats). Strip the Apple Notes `<ul class=Apple-dash-list>` HTML.
  Show Jed the proposed grouping **before** writing.
- Links from URLs in `jed_notes` (BR-31, BR-29, BR-20, G-38, LF-44, P-62),
  titled by hand. Leave `jed_notes` text untouched.
- Afterwards, once Jed OKs: clear `trip_reports` via the normal edit path and
  remove the "Older notes" block.

### Phase 7 — ship
`tests/offline/run.sh` (index.html data path touched), commit, push,
`launchctl kickstart -k gui/$(id -u)/com.limechile.uintas-edits-server`,
`curl http://olaf.local:8802/api/ping`, test on the phone with Tailscale on
(add a photo offline → reconnect → appears on the Mac PWA). Update
`docs/runbooks/edits-push.md` (journal + media endpoints, photo privacy,
`data/media/` backup = Time Machine on the Mini; originals stay in the phone's
camera roll), CLAUDE.md (architecture table, critical files, invariant: never
commit `data/media/`), and the `find-lakes` skill if `lake_search` should
expose trip/photo counts.

Also add photos-with-location as a possible later feature: a "photos" layer
on the map (pins from the sidecars).

### Phase 8 — home redesign
The `claude-design` MCP server failed to connect early on 2026-10-10 (HTTP
403); Jed then ran `/design-login` ("Design-system access authorized"), so it
should load in a fresh session — use it. If it's still unavailable: produce 2–3
concrete directions as a mockup artifact (real data counts, iPhone width
first), let Jed pick, then implement. Entry points to organize: search
(primary), starred, map, recent stockings, jump to drainage, rotenone,
photos, trip reports, future trips, filters. Keep the mission bar.

## Later ideas

- **Photos layer on the map**: pins from the private location sidecars
  (`mediaMeta`), tap → lightbox. Sidecars only reach devices that sync with
  the Mini, so the layer would be empty on a github.io-only client.

## Handoff notes

- 2026-10-10 (Phase 0): search label removed; `#lake-search-clear` added
  (`.search-wrap` CSS in the `<style>` block; pointerdown `preventDefault`
  keeps the iOS keyboard up). Verified in Playwright at iPhone 15 size.
- 2026-10-10 (Phase 1, **left uncommitted**; commit with Phase 7 or sooner):
  - `scripts/journal_store.py` is the schema authority: `clean_doc(kind, doc,
    known_lakes)` whitelists fields (unknown fields are **dropped**, so a new
    client field needs a server change too), dedupes lakes, nulls
    `date`/`end_date` when `planned` and `when` when not. `updated` must match
    `YYYY-MM-DDTHH:MM:SS(.fff)Z` — i.e. JS `new Date().toISOString()`; LWW
    compares it as a string. `taken` accepts `YYYY-MM-DD[THH:MM[:SS]]` (no zone).
    Tombstones are stored as just `{id, updated, deleted:true}` and a stale
    write can't resurrect one.
  - `POST /api/journal` results are `{kind, id, result: applied|superseded|error,
    current?|message?}`. journal.json is re-read on each batch (no in-memory
    cache), so a one-off script (Phase 6) can edit it while the server runs.
  - Media: `PUT` needs `Content-Type: image/jpeg` **and** JPEG magic bytes
    (415 otherwise), 413 over 12 MB (body not drained — the client should treat
    413 as permanent). The sidecar is `PUT …/<id>.json` with
    `Content-Type: application/json`; it is **not** `GET`-able — only via
    `/api/user-data` → `media_meta`. CORS now allows PUT.
  - `GET /api/link-title?url=` → `{title}` (blank on failure, 400 on non-http).
    Refuses hosts that resolve to private/loopback addresses. Verified live:
    junesucker.com and wildlife.utah.gov (both behind Cloudflare) return titles.
  - Static fence: `_is_private()` resolves through `translate_path` + lower-case
    compare; GET and HEAD to `data/push/` and `data/media/` → JSON 404. **The
    live server on the Mini still runs the old code and serves
    `data/push/vapid_private.pem` over Tailscale until it is restarted.**
  - Committer commits `data/journal.json` too (only if it exists) with message
    "App edits: updates from the PWA"; the hook regenerates `lakes_data.json`
    alone when only the journal is staged. `tests/auto_commit_isolation.sh`
    gained 4 journal checks (17/17 pass).
  - Exporter: top-level `journal: {trips, photos, links}` (tombstones dropped)
    + per-lake `junesucker_url` (40/40). Harness used for testing:
    `edits_server.py --db <copy> --log x.jsonl --journal j.json --media media
    --no-git --port 8899 --host 127.0.0.1` (49 curl checks, all pass).
- 2026-10-10: Phase 1 committed (874f202) and the live server restarted —
  `data/push/` now 404s on LAN + Tailscale (verified).
- 2026-10-10 (Phase 2, **left uncommitted**: `index.html`,
  `scripts/edits_server.py`, new `tests/journal/`). **Restart the live edits
  server when this is committed** (server now deletes a photo's media files
  when its tombstone arrives).
  - **Regression suite: `tests/journal/run.sh`** (server endpoints + client
    data layer in Chromium *and* WebKit + ImageIO leak check; ~3 min; never
    touches live data — harness on :8899, fixtures on :8898, live hosts
    aborted). Run it after any journal/sync/media change. Phases 3–5 should
    add their UI assertions to `client-test.js` (or a sibling file).
  - Client API (all in `index.html`, next to `syncNow`), for Phases 3–5 to call:
    `queueJournal(kind, doc)` (stamps `updated`, returns the stamped doc),
    `deleteJournal(kind, id)`, `newJournalId(kind)`, `getJournalDoc(kind, id)`
    (null if deleted), `journalList(kind)`, indices `tripsByLake`,
    `photosByLake`, `photosByTrip`, `linksByLake` (rebuilt by
    `rebuildJournal()`; trips sorted taken-newest-first then planned,
    photos by `taken`), `mediaMeta[id]` → private location sidecar.
    Re-render on the `journalchange` event (fired on queue, sync, and
    hydrate).
  - Photos: `addPhotoFile(file)` → `{id, taken, w, h, sidecar, nearLakes:
    [{letter_number, km}]}`; it stores blobs + meta but does **not** queue
    the photo doc — the caller does (`queueJournal('photo', {id, trip,
    lakes, caption, taken, w, h})`). Blobs of a photo with no doc are never
    uploaded and are purged after 3 days; for Cancel call
    `discardPhotoMedia(id)` right away. HEIC/undecodable → throws an Error
    with a friendly message. `lakesNear(lat, lng, km=1.2)` is reusable.
  - Rendering: `<img data-pid="p-…" data-size="t|f">` then
    `hydrateMedia(rootEl)`; states via `data-media-state` =
    loading|ok|offline (CSS in the `<style>` block). `getPhotoUrl(id, size)`
    for the lightbox (thumb first, then full).
  - Sync: `syncNow()` now returns the in-flight pass instead of a no-op when
    one is running (fixes awaiting callers racing the `online` event). Order:
    lake edits → media uploads → journal docs → fold `/api/user-data` →
    background thumbnail prefetch (3 at a time). Docs the server rejects keep
    `error` and are not retried until edited; the Sync panel line counts
    them. Chip now says "N changes pending" (edits + docs + photo uploads).
  - Media store = IndexedDB `uintas-media`, images stored as **ArrayBuffers**
    (`putImage`/`getImage`), not Blobs — Safari rejects Blobs in IDB in
    private/ephemeral mode.
  - WebKit findings: the picked File is read **once** (re-reading throws
    NotReadableError); Safari's canvas JPEG encoder writes its own tiny EXIF
    (ColorSpace + pixel dimensions only — verified no GPS/camera/date), so
    don't test for "no Exif bytes". Playwright-WebKit can't read files while
    `setOffline(true)` nor do offline SW navigations — harness artifacts; the
    real airplane-mode add-photo check is the Phase 7 phone test.
- 2026-10-10 (Phase 3, **left uncommitted**: `index.html`, `tests/journal/`,
  and a locally regenerated `lakes_data.json` — the committed copy predated
  Phase 1's exporter, so it lacked `journal` / `junesucker_url`; the
  pre-commit hook would regenerate it anyway).
  - Lake modal: `<div id="lake-journal">` sits right below My Record.
    `wireLakeJournal(lake)` (called from `showLakeDetail`) builds
    `#jr-cards` (re-rendered by `renderLakeJournal(ln)` on every
    `journalchange`), `#jr-status` (add-photo progress/errors) and
    `#jr-link-form` — the last two are outside the re-rendered part so a
    background sync can't wipe a half-typed link. Actions are delegated via
    `data-jr` attributes. Unvisited lake = one row of pills (＋ Photo ＋ Trip
    ＋ Plan ＋ Link); ＋ Link moves into the Links card once it exists.
  - **Phase 4 hooks (currently console.warn stubs)**: `showTripDetail(id)`
    (trip rows, lightbox "From trip: … →") and `openTripEditor(trip, {lakes,
    planned})` (＋ Trip / ＋ Plan pills, `trip` null = new). Replace them.
  - Reusable helpers: `tripDateLabel(trip)` ("Oct 12–14, 2024", "Sep 30 –
    Oct 2, 2024", "Planned · summer 2027"), `photoTakenLabel`, `fmtDay`,
    `normalizeUrl` (adds https:// to bare domains; null if not http(s)),
    `prettyUrl`, `urlHost`, `safeHref`, `lakeLabel(ln)`, `fetchLinkTitle(url)`
    (`null` = Mini unreachable, `''` = no title), `armDelete(btn, fn)`
    (two-tap delete, no `confirm()`), and `matchLakes(lowercasedQuery)` —
    the search box's matcher, factored out for the lake pickers.
  - Lightbox: `openLightbox(ids, startId)` / `closeLightbox()`; state in the
    `lightbox` object. Edit mode = caption + tag chips; one-tap candidates =
    the photo's trip's lakes, then `lakesNear` from the sidecar (with
    distance). Re-renders on `journalchange` but never clobbers an open edit.
    Closed by `hideModals()` (so browser-back closes it **and** the modal
    under it — no history entry, per the plan) and first in the Escape chain.
  - Saving a link with a blank title retries the title lookup in the
    background and fills it in if the doc is unchanged.
  - New CSS is in the `<style>` block (`.jr-*`, `.lb-*`, `#photo-lightbox`);
    `tailwind.css` was **not** regenerated — only classes already in it are
    used.
  - Tests: `tests/journal/ui-test.js` (37 checks, iPhone viewport) runs per
    browser from `run.sh`. Gotcha: Playwright-WebKit **can't route** requests
    from a service-worker-controlled page, so `/api/link-title` is mocked by
    wrapping `window.fetch` in the page, not with `context.route`.
  - Not verified here (Phase 7, on the phone): touch swipe in the lightbox,
    the iOS photo picker → ＋ Photo, keyboard + edit panel layout.
- 2026-10-10 (Phase 4, **left uncommitted**: `index.html`, `tests/journal/`).
  - Markup: `#trip-modal` (z 1250) → `#trip-modal-card` → sticky
    `#trip-modal-header` (← `#trip-back` / `#trip-close` in view mode;
    `#trip-cancel` / `#trip-save` in edit mode, swapped by
    `#trip-modal.editing`) + `#trip-content`. CSS `.tv-*` / `.te-*` in the
    `<style>` block; `tailwind.css` still **not** regenerated.
  - Entry points: `showTripDetail(id)` (returns false if the trip is gone)
    and `openTripEditor(tripOrNull, {lakes, planned})`. Both work from any
    state — lake modal open, trip modal open, or nothing open (Phase 5's
    list/“＋ New trip” can call them directly).
  - **Navigation**: `crossStack` entries are `{type:'lake', id, nav, scroll}`
    or `{type:'trip', id, scroll}`. `hopToTrip()` pushes whatever is being
    left; `openLakeFromTrip(ln)` pushes the trip; `popCross()` walks back
    (skipping deleted trips) and is what ← in both modals falls through to
    after `lakeNavStack`. The hidden lake modal keeps its DOM, so returning
    to the same lake restores scroll without a re-render. **Phase 5:** add a
    `{type:'journal', …}` entry for the list modal — push it in `hopToTrip`
    (and before `showLakeDetail` from a list row), restore it in `popCross`,
    and close it in `hideModals`.
  - History: still one entry per stack; the hash follows the top modal
    (`#trip-<id>` / `#BR-25`). Deep link `#trip-t-…` on load; forward
    navigation re-opens via the popstate `'trip'` branch. Escape closes the
    stack from the trip *view*; it is ignored in the editor (no lost drafts);
    the backdrop likewise.
  - Editor = draft in `tripEdit`; Save queues the trip + changed/new photo
    docs (`trip`, `caption`, `lakes`), tombstones removed photos, then
    `refreshPendingUploads → syncNow` and a background title lookup for
    untitled links (`fillTripLinkTitles`). Cancel / browser back / Escape-
    from-elsewhere all go through `discardTripDraft()`, which deletes the
    blobs of photos added during that edit. A URL left typed in the link box
    is added on Save. Validation: title required; end ≥ start; no end
    without start.
  - Photos in the editor: tag chips = trip lakes ∪ the photo's tags ∪ lakes
    within 1.2 km of its sidecar location (with distance); "＋ other lake…"
    opens a per-photo search. GPS near-lakes not yet in the trip show as
    dashed "＋ Lake · 166 m" suggestions in the Lakes section.
  - Delete: no photos → two-tap; with photos → "Delete trip and photos" /
    "Delete trip, keep photos" (kept ones get `trip: null`, keep tags).
  - "✓ Mark as done" on a planned trip = inline date form (today prefilled)
    → `planned:false`, dates set, `when` null.
  - New helpers: `rankedLakeMatches(q, exclude, n)` (the lightbox uses it
    now too), `autolinkHtml(text)`, `photoNearLakes(pid)`, `fmtKm`,
    `todayIso`, `isOpen(elementId)`.
  - Tests: `tests/journal/trip-test.js` (42 checks, iPhone viewport) runs per
    browser from `run.sh`; `JOURNAL_TEST_ONLY=trip-test.js
    tests/journal/run.sh chromium` runs one UI script alone. Full suite and
    `tests/offline/run.sh` pass.
  - Not verified here (Phase 7, on the phone): the iOS date wheel (the
    editor listens to `change` as well as `input` for it), keyboard over
    the sticky header, photo picker → editor.
- 2026-10-10 (Phase 5, **left uncommitted**: `index.html`, `tests/journal/`).
  - Home: `#home-journal` = three buttons (📷 Photos / 🥾 Trip reports /
    🧭 Future trips, counts under each) below "Recent stockings" — a plain
    grid for Phase 8 to restyle/move. `updateHomeJournal()` keeps counts
    current on `journalchange`.
  - Journal list = `#journal-modal` (z 1150, same tier as the stocking
    report) → tabs `[data-jl-tab]` trips|planned|photos, `#journal-status`
    (add-photo progress, outside the re-rendered body), `#journal-body`
    (re-rendered by `renderJournal()` on every `journalchange`, scroll kept).
    Entry: `openJournal(tab, drainage|null)`; state in `journalView {tab,
    drainage, photoIds}`; hash `#journal-<tab>` (deep link + popstate
    forward work; the drainage scope is in-memory only).
    `journalScoped(drainage)` → `{trips, planned, photos}` is the one scoping
    rule (trip: any lake in the drainage; photo: any tag, or its trip's
    lakes when untagged). Cards: `journalTripCard(t)`; photo grid:
    `journalPhotosHtml(photos)` (groups by trip, trip-less by month,
    newest group first, shooting order within).
  - **Navigation: the list stays open underneath** whatever it opens (lake,
    trip, lightbox) instead of the crossStack entry the Phase 4 note
    suggested — simpler, and it keeps the list's scroll for free.
    `hideModals()` computes `keepJournal` (list open *and* a lake/trip open
    above it): it then closes only the upper stack and `pushState`s
    `#journal-<tab>` again, so ×, ← with nothing left to pop, and browser
    back all land on the list; with nothing above it, the list closes too.
    Escape order: lightbox → trip → lake → list.
  - "＋ Add photos" in the list: trip-less, untagged photo docs, then the
    lightbox opens on the first in edit mode (GPS near-lake suggestions are
    the one-tap tags). ＋ New trip / ＋ Plan a trip call `openTripEditor`
    with no lakes.
  - Drainage view: `setResults` takes `drainage` (`view.drainage`, set only
    by `showDrainageLakes`); `#results-journal` row of pills under
    `#results-lead` opens the list scoped; hidden when the drainage has
    nothing. `showDrainageMap` scrolls to the row when it's visible, and
    aims again once the drainage map image above it has loaded (it has no
    fixed size, so it used to push the target ~300 px down mid-scroll —
    true of the old map-wrap target too).
  - Sync panel → "Photos" section: `refreshPhotoStatus()` ("N photos · N
    full-size on this device · N waiting to upload · N rejected"), called
    from `refreshSyncModalStatus`; `saveAllFullPhotos()` pulls missing
    full-size images 3 at a time with progress, asks for persistent storage
    (`askPersistentStorage()`, factored out of `addPhotoFile`).
  - Tests: `tests/journal/list-test.js` (34 checks, iPhone viewport), wired
    into `run.sh`; it sets `page.setDefaultTimeout(15000)` so a stuck step
    fails instead of hanging the suite. **WebKit gotcha:** Playwright's
    headless WebKit wedges the whole page (no rAF, no screenshots, evaluate
    never returns) on `pushManager.getSubscription()`, which
    `openSyncModal → refreshNotifStatus` calls — tests that open the Sync
    panel must stub `window.refreshNotifStatus` first. Real Safari is fine.
  - **Incident:** an ad-hoc Playwright probe on `:8804` (no sync-URL
    override) synced two junk "x" trips to the **live** edits server, which
    committed + pushed them (0d6229b, a3a3a12). Tombstoned through
    `POST olaf.local:8802/api/journal` per Jed (647f381); published journal
    is empty again. Probe only through the harness, or abort
    `olaf.local|ts.net` and set `uintas-sync-url` first.
  - Not verified here (Phase 7, on the phone): the list modal's scroll
    inside the fixed overlay on iOS, the photo picker from the list.
- 2026-10-10 (Phase 6). **Migrated docs are live** (applied through the live
  edits server, which committed + pushed them as ff6236a; `lakes_data.json`
  now carries 12 trips + 7 links). **Left uncommitted:** new
  `scripts/migrate_trip_reports.py`, `scripts/journal_store.py`,
  `index.html`, `tests/journal/`.
  - Jed approved the grouping as proposed: 12 trips from the 16 lakes (G-49/
    G-15/G-18 Sep 2020 Highline; G-18 Jul 2021; G-15+G-49 Aug 2024;
    BR-15+BR-14 Labor Day 2024; BR-25+BR-28 Oct 2024; A-22; P-60; BR-29
    + RoadTripRyan link; W-21; LF-44; A-18+A-14+W-62 Norway Flats; DF-11).
    Island A-57 deliberately untagged. 7 lake links (BR-20, BR-29, BR-31 ×2
    incl. the Utah Wildlife Forum thread found by search, G-38, LF-44, P-62).
    `jed_notes` untouched.
  - **Month-only dates** (Jed's choice over 1st-of-month): `DATE_RE` accepts
    `YYYY-MM`; `end_date` must match `date`'s precision (server-enforced).
    Client: `tripDateLabel` handles it; editor `#te-month-only` checkbox
    swaps the inputs to `type=month` (text fallback with pattern on desktop
    Safari/Firefox) via `setTripMonthOnly(on)` (day → month drops the day;
    month → day prefills the 1st). String sort already orders "2024-10"
    just after the days of Oct 2024 in newest-first lists. Tests: 1 server
    check, 7 trip-test checks (both browsers).
  - **The live edits server was restarted** to load the month-only
    validation, so it now runs the working tree's uncommitted
    `edits_server.py` (Phase 2: photo tombstone deletes its media files) +
    `journal_store.py`. Phase 7 should still restart after committing.
  - Script: fixed ids (base36 of the trip's start + hash) and a fixed
    `updated` of 2026-10-10T00:00Z; skips docs the server already has, so a
    re-run is a no-op and can't overwrite in-app edits.
  - **Still to do (after Phase 7, once Jed has reviewed the trips on his
    phone):** clear the 16 lakes' `trip_reports` via the normal edit path
    (`POST /api/edits`, field `trip_reports`, value `""`) and remove the
    "Older notes" block from My Record.
- 2026-10-12 (Phase 7). Committed + pushed Phases 2–7 together; live edits
  server restarted on the committed code.
  - Docs: `docs/runbooks/edits-push.md` gained a "Journal" section (storage,
    sync, private media + location, Time Machine backup, iOS picker
    location caveat, link-title, static fence, test suite); CLAUDE.md gained
    the `data/media/` invariant, journal in the architecture + critical
    files, `tests/journal/run.sh` among the suites.
  - `scripts/lakes.py` → `lake_search` gained `trip_count`, `last_trip`,
    `trip_titles` (" | "-joined), `planned_trip_count`,
    `planned_trip_titles`, `journal_photos`, `lake_links`; journal.json is a
    cache source. Documented in the `find-lakes` skill.
  - Tests no longer read the live published journal: `edits_server.py
    --web-root` + `run.sh` serves a symlinked copy of the repo whose
    `lakes_data.json` has an empty `journal` (the migrated trips had broken
    20 count/order assertions).
  - `tests/offline/run.sh` flaked once ("Execution context was destroyed")
    right after the journal suite; passed on rerun.
  - **Phone test (Jed, Tailscale on)** — still to do, then tick Phase 7:
    1. PWA picks up the new version (Sync panel shows today's data).
    2. Home → 🥾 Trip reports shows the 12 migrated trips; open a few, check
       the grouping/text; the "Older notes" block is still on those lakes.
    3. Airplane mode → a lake → ＋ Photo from the camera roll → turn
       Tailscale back on → it uploads (chip clears) → appears on the Mac PWA
       with its thumbnail. Check whether "📍 Open in Maps" appears (if not,
       the picker stripped GPS: picker "Options → Location").
    4. ＋ Trip with photos, a link and month-only date; iOS date + month
       wheels; keyboard vs the sticky header; lightbox swipe; list scroll.
  - After the phone test and Jed's OK on the trips: the remaining Phase 6
    step (clear `trip_reports`, drop "Older notes").
