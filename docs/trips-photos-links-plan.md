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
- [ ] **Phase 2** — client data layer: journal state + sync, media store, image pipeline
- [ ] **Phase 3** — lake modal: Links card, Junesucker source link, Trips & photos card, photo lightbox
- [ ] **Phase 4** — trip modal: view + editor, planned trips
- [ ] **Phase 5** — top level: Photos / Trip reports / Future trips lists, drainage scoping, Sync-panel photo status
- [ ] **Phase 6** — data migration: old `trip_reports` → Trips; URLs in `jed_notes` → Links
- [ ] **Phase 7** — ship: commit/push, restart edits server, phone test over Tailscale, runbooks
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
Verify with Playwright at iPhone size + screenshots.

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
