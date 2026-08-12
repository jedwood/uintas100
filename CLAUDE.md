# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a comprehensive SQLite-based web application for exploring fishing locations in Utah's Uinta Mountains. It combines a Python backend for data management with a Progressive Web App (PWA) frontend, plus Apple Notes integration for personal fishing notes.

## Key Commands

### Database Management
```bash
# Initial setup (run once)
python3 scripts/setup_database.py

# Update with latest stocking data
python3 scripts/fetch_latest_stocking.py
python3 scripts/update_stocking.py

# Regenerate the frontend data file after any database change
# (the pre-commit hook also runs this automatically when uinta_lakes.db is committed)
python3 scripts/export_web_data.py

# Generate human-readable dumps
python3 -c "from scripts.database_utils import *; import sqlite3; conn = sqlite3.connect('uinta_lakes.db'); dump_lake_data(conn); dump_stocking_data(conn); dump_combined_data(conn)"
```

### Database Reproducibility (seeds → rebuild → verify)
`uinta_lakes.db` is canonical, but it is also fully reconstructable from committed,
git-diffable CSV **seeds** in `data/seeds/` (one per table). This is the recovery
path — and the regression guard that the DB never silently drifts.

```bash
# Enable the version-controlled git hooks ONCE per clone (this is the only manual
# step — afterward seeds stay in sync automatically):
git config core.hooksPath .githooks

# Rebuild a content-equivalent DB from the seeds, fully offline (writes a temp file)
python3 scripts/rebuild_database.py                      # or --output PATH

# Prove the seeds round-trip to the canonical DB (exit 0 = equivalent, 1 = drift)
python3 scripts/verify_rebuild.py

# Manual re-export (rarely needed — only if committing the DB with hooks disabled)
python3 scripts/export_seeds.py
```

**Seeds regenerate automatically** — you do not need to remember `export_seeds.py`:
- The `.githooks/pre-commit` hook regenerates + stages `data/seeds/` whenever
  `uinta_lakes.db` is staged (covers every manual commit and the cron auto-update,
  since both go through `git commit`). Enable it once with the `core.hooksPath`
  command above; it also bumps the PWA cache version.
- `fetch_latest_stocking.py` (the unattended cron path) also re-exports seeds in
  its commit step, so it can't push a DB with stale seeds even on a machine where
  the hook isn't enabled.

Why seeds and not a replay of `utah_dwr_stocking_data.csv`: a clean matcher replay
does **not** reproduce the curated DB. `find_matching_lake` strips `RESERVOIR`, so
it mis-credits lowland reservoirs onto same-named Uinta lakes (e.g. "Echo Reservoir"
→ Z-16 Echo, which the curated DB excludes), and it can't recreate the ~55
manually-added lakes or the drainage/photo rows (their original sources aren't
committed). The seeds capture the curated truth exactly; `verify_rebuild.py`
confirms an exact, zero-diff round-trip on every table. SQL `NULL` is stored in the
seeds as the sentinel `\N` (empty string stays empty) so the `NULL`-vs-`''`
distinction (e.g. `basin`) round-trips. Schema lives in one place —
`create_database()` builds the full canonical schema (all columns + triggers +
coordinate columns); `setup_database.py`/`update_stocking.py` no longer patch it
ad hoc. Full recovery write-up: `docs/db-recovery-plan.md`.

### Single-writer model (the Mac Mini writes; everything else mirrors)
Exactly ONE machine — the Mac Mini — writes `uinta_lakes.db` and pushes. Every
other clone (MacBook, etc.) is a **read-only mirror**: it only `git pull`s and
runs the app, and must never run a sync/fetch or commit the DB. This removes the
two-machine write-conflict class (e.g. the binary-DB autostash conflicts).

- **Enforcement:** a gitignored `.db-readonly` marker in the repo root makes a
  clone a mirror. `fetch_latest_stocking.py`, `update_stocking.py`,
  `sync_notes_to_db.sh`, and `sync_notes_and_push.sh` call
  `writer_guard.exit_if_readonly()` (or the bash equivalent) and exit early when
  the marker exists — so even if a scheduler fires the job, it does nothing.
  Exception: on a mirror, `fetch_latest_stocking.py` runs `git pull --ff-only`
  instead (`writer_guard.pull_and_exit_if_readonly()`) — so the MacBook's Tauri
  app scheduler, which fires the stocking job periodically, doubles as the
  mirror's auto-refresh: the clone (and the web app served from it on
  localhost:8804) picks up whatever the Mini pushed. Reload the app window to
  see fresh data (the PWA cache version bump makes the reload pick it up).
  - Mirror (MacBook): `touch .db-readonly`
  - Writer (Mini): the marker must NOT exist (`ls .db-readonly` → absent)
- The Mini is the only machine that should run the schedulers/cron for fetch and
  Notes sync. You edit Apple Notes on any device; iCloud syncs them to the Mini,
  which is the only place Notes↔DB is translated.
- Notes sync runs on the Mini as the `com.limechile.uintas-notes-sync` LaunchAgent
  (every 6h; `scripts/notes_sync_agent.py` → Notes→DB, then DB→Notes for lakes
  flagged by stocking updates, then commit+push). Because
  the home is on an external `/Volumes` disk, its deployment is non-standard
  (internal-disk plist, FDA on the venv python, reboot revival via the
  agent-bootstrapper). Full runbook: `deploy/README.md`.

### App edits (status / Jed's Notes / trip reports) — the PWA write path
Since 2026-08-10 the user-owned lake fields (`status`, `jed_notes`,
`trip_reports`) are edited **in the PWA itself** ("My Record" section of the
lake modal), not in Apple Notes. This keeps the single-writer model intact
while allowing edits to *originate* on any device:

- **Client side (`index.html`)**: saves land in `localStorage` instantly
  (fully offline — designed for multi-day trips), overlay the loaded data, and
  are flushed to the edits server whenever it's reachable. A header chip shows
  the pending count; the "Sync" link (next to "About") opens a panel with a
  manual sync button and a server-URL override. Server auto-resolution tries
  the page's own host on :8802, then `http://olaf.local:8802` (LAN), then
  `https://olaf.tailbf6340.ts.net` (Tailscale). The Tailscale HTTPS proxy
  (`tailscale serve --bg localhost:8802` on the Mini; config persists across
  reboots) exists because the iPhone's PWA is installed from the **https**
  github.io page, and a secure page cannot fetch `http://` LAN URLs (Safari
  silently blocks mixed content) — so the iPhone syncs only via the Tailscale
  URL, and only while its Tailscale VPN is on (from anywhere, not just home).
- **Server side (`scripts/edits_server.py`)**: runs ONLY on the Mini (writer
  guard) as the `com.limechile.uintas-edits-server` LaunchAgent, port 8802.
  Applies edits last-write-wins per (lake, field) using the committed audit log
  `data/app_edits_log.jsonl` (kept OUTSIDE the DB on purpose, so the
  seeds/rebuild/verify machinery is untouched), then commits + pushes in the
  background — the pre-commit hook regenerates seeds + `lakes_data.json`, and
  mirrors pick the edits up on their next pull. A device that was offline for a
  week gets "superseded" (not applied) for any edit older than what another
  device already wrote to the same field.
- **Test harness**: `python3 scripts/edits_server.py --db /tmp/x.db --log
  /tmp/x.jsonl --no-git --port 8899` — also serves the repo statically, so one
  process backs a full browser test.

```bash
curl http://olaf.local:8802/api/ping        # is the writer up?
tail -f /Users/jed/Library/Logs/uintas-edits-server.log
```

### Apple Notes Sync (RETIRED as a write path, 2026-08-10; LaunchAgent undeployed 2026-08-12)
The Notes round trip is retired: `notes_sync_agent.py` exits immediately unless
run with `UINTAS_NOTES_SYNC=force`. Reason: the user fields are now edited in
the app (above), and a Notes→DB run would overwrite them with stale note
content (most notes still carry pre-migration placeholders — see the
2026-08-10 data-loss investigation). The `com.limechile.uintas-notes-sync`
LaunchAgent is no longer loaded or scheduled at all (`launchctl bootout`-ed,
plist removed from `/Users/jed/Library/LaunchAgents/` — source of truth stays
in `deploy/`, see `deploy/README.md`); leaving it loaded as a no-op used to
also trip a stale-log watchdog in `fetch_latest_stocking.py` on every stocking
run, which has since been removed. The JXA scripts below remain for manual /
archival use only.
```bash
# Sync changes from Apple Notes to database
osascript scripts/sync_notes_to_db_jxa.js

# Sync flagged database changes to Apple Notes
osascript scripts/sync_db_to_notes_jxa.js

# Shell wrapper for notes sync (Notes -> DB only; self-guards on mirrors)
./scripts/sync_notes_to_db.sh

# Mini-only: Notes -> DB AND commit+push the result (durably persists note edits)
./scripts/sync_notes_and_push.sh
```
**DB→Notes (`sync_db_to_notes_jxa.js`) is now wipe-safe.** Apple Notes has no
surgical edit (writing a note replaces its whole body), so for an EXISTING note
the script reads the live note and **preserves everything above the ═══ delimiter
verbatim** (your Status / Jed's Notes / Trip Reports), rebuilding the body as
preserved-above + fresh delimiter + DB-regenerated auto-data; only the `<h1>`
title emoji is refreshed. It does NOT source your editable content from the DB, so
it can't clobber un-captured edits regardless of the `*update`-tag/ordering.
Safety nets: it **backs up** each old note body to `logs/notes_backups/` before
overwriting, **skips** (won't touch) any note lacking a ═══ delimiter or that looks
conflict-merged (2+ delimiters / doubled title), and **waits 30s after launching
Notes** for iCloud to pull before reading (`UINTAS_SYNC_SETTLE=<secs>` to tune, `0`
to skip) — rewriting from a stale replica makes iCloud concatenate both versions
into one note (the 2026-07-01 incident). Never set `note.name` after setting
`body` (the first body line already becomes the name; setting both doubles the
title text).
Preview without writing: `UINTAS_DRYRUN=1 osascript scripts/sync_db_to_notes_jxa.js`.
`notes_sync_agent.py` still implements the full **round trip** (Notes→DB, then
DB→Notes for any lakes flagged `notes_needs_update`, then commit+push) but only
runs it when manually invoked with `UINTAS_NOTES_SYNC=force` — there is no
longer a LaunchAgent firing it automatically. `sync_notes_and_push.sh` (the
manual wrapper) remains Notes→DB only. Known hiccup: if a lake note is OPEN on
another device while DB→Notes rewrites it, that device may iCloud-conflict-merge
and show a duplicated section — fix is simply deleting the duplicated lower
section(s) by hand on that device.

### June Sucker notes (`lakes.junesucker_notes`)
```bash
python3 scripts/scrape_junesucker.py --dry-run   # report what would change
python3 scripts/scrape_junesucker.py             # scrape junesucker.com + update the DB
```
Re-scrapes every lake page linked from `https://junesucker.com/lakes/uintas/`. It is
**idempotent** (re-running with no site changes reports `lakes updated: 0`) and stores
markdown with `## ` section headings, which `index.html` styles in the lake modal.

- **Two section types are deliberately dropped:** anything whose heading mentions DWR
  ("Historical DWR Info", "DWR Historical Data", "DWR Info", "Historical Information")
  because it repeats `dwr_notes`, and "Nearby Areas to Fish" because it's a directory of
  *other* lakes. Older pages express these as a bold lead-in paragraph
  (`Historical DWR Info: ...`) rather than an `<h4>`; both markups are handled.
- **Matching is designation-first** (title → index link text → body, and only if the body
  names exactly one lake), with an exact unique whole-name match as the last resort. The
  original loose matcher mis-filed the *Julius Park Reservoir* page onto DF-17 Little Elk.
- Cloudflare 403s a bare urllib/curl UA — the browser-like `HEADERS` are required.
- Cleaned markdown is also written to `data/junesucker_pages/<slug>.md` (git-diffable
  record of what the site said), and `data/uinta_lake_links.csv` is refreshed each run.
- Supersedes the one-off `data/process_all_lake_pages.py`.

### Coordinates & Mapping
```bash
# 1. Seed ~70% of lake coordinates from OpenStreetMap (matched by designation + name)
python3 scripts/seed_coordinates.py            # uses cached OSM data if present
python3 scripts/seed_coordinates.py --refresh  # re-fetch from Overpass

# 2. Manually place/verify the rest in the Lake Locator (local web tool).
#    The Locator WRITES the DB, so under the single-writer model it must run on
#    the Mini (it refuses to start on a mirror). Serve it over the LAN and click
#    from any machine's browser:
python3 scripts/locator_server.py --host 0.0.0.0   # on the Mini; prints the LAN URL
#    (--host defaults to 127.0.0.1 — localhost-only — if you're at the Mini itself)

# 3. Push verified coords into the PWA data
python3 scripts/export_web_data.py
```
Coordinate columns on `lakes`: `lat`, `lng`, `coord_source` (`osm-designation`/`osm-name`/`manual`),
`coord_status` (`seed_unverified` | `seed_suspect` | `confirmed` | `manual` | `cant_find`).
Only `confirmed`/`manual` coordinates are exported to the PWA (which shows an "Open in Maps"
link); seeds stay internal to the Locator until you eyeball them. The Locator writes straight
back into `uinta_lakes.db` — which is why it obeys the `.db-readonly` writer guard.

### PWA Cache Management
```bash
# PWA cache version is automatically updated by the .githooks/pre-commit hook
# (enable once per clone: git config core.hooksPath .githooks)
# No manual intervention needed - just commit and the hook handles it
git commit -m "your changes"  # Bumps cache version + re-exports data/seeds when the DB changed
```

### Development Server
Since this is a static web app, serve locally with:
```bash
python3 -m http.server 8804   # NOT 8000 — the Qwen3 embeddings LaunchAgent owns :8000 on the Mini
# or
npx serve .
```

### Tauri control-panel app (`tauri-app/`)
The desktop wrapper (`/Applications/Uintas.app`) that runs the schedulers, serves
the web app on :8804 (moved off :8000 2026-08-12 — the shared Qwen3 embeddings
LaunchAgent claims :8000), and exposes a gear-icon control panel. Build + install:
```bash
cd tauri-app && cargo tauri build --bundles app
rm -rf /Applications/Uintas.app && cp -R src-tauri/target/release/bundle/macos/Uintas.app /Applications/
```
- **Schedule lives in a store, not in the repo.** Live intervals are in
  `~/Library/Application Support/com.jedwood.uintas/schedule.json`; the values in
  `scheduler.rs` are only defaults for a machine with no store yet. Don't read the
  source and conclude what a given machine is doing — read that file (or the panel).
- **On a mirror, the "Stocking Updates" interval IS the mirror-refresh cadence.**
  `writer_guard.pull_and_exit_if_readonly()` turns that job into a
  `git pull --ff-only`, so the interval sets how far behind the clone can drift.
  The MacBook runs it hourly. End-to-end freshness is still capped by how often the
  *Mini* actually fetches from DWR — a mirror can't be fresher than what was pushed.
- The frontend is embedded at compile time by `tauri::generate_context!()`.
  `build.rs` emits `rerun-if-changed` for `frontend/` to force a recompile on
  frontend-only edits — `tauri_build::build()` does NOT do this itself, and without
  it cargo skips the rebuild and silently ships a stale UI.
- Editing an interval by hand in `schedule.json` requires quitting the app first;
  a running app holds the config in memory and overwrites the file on its next save.

## High-Level Architecture

### Database (SQLite)
- **`uinta_lakes.db`** - Main SQLite database containing all data
- **Core Tables**:
  - `lakes` - 672 lakes with designations (A-1, BR-25, etc.), physical data, species info
  - `stocking_records` - DWR stocking history with normalized species names
  - `drainages` - 17 major drainage systems with access info and maps
  - `photos` - Lake photos from junesucker.com
  - `other_waters` / `other_stocking_records` - "fringe" waters DWR stocks that are NOT lettered lakes (creeks, ponds, forks). Kept entirely separate from `lakes` and the PWA. `likely_drainage` is a GUESS borrowed from a namesake lake (e.g. "Beaver Cr" → BR-10 Beaver's drainage) — treat as use-at-your-own-risk. Rebuilt by `scripts/migrate_fringe_waters.py`.

### Python Backend (`scripts/`)
- **Data Pipeline**: CSV sources → SQLite via setup/update scripts
- **Species Standardization**: `species_utils.py` normalizes all species names to consistent format (Brookies, Tigers, Cutthroats, etc.)
- **Stocking matcher** (`database_utils.find_matching_lake`): a DWR water is credited to a lake ONLY on an exact letter-number designation or an exact name (after stripping a trailing "Lake"). Loose substring matching was removed because it mis-filed creeks/ponds onto same-named lakes (e.g. "Beaver Cr" → BR-10). "Reservoir" is NOT a throwaway suffix (only "Lake" is): a lowland "Echo Reservoir" must not name-match the tiny Uinta "Echo" lake (Z-16) — reservoirs are credited to a lake only by explicit designation, while a lake genuinely *named* "… Reservoir" (e.g. Y-41 "Drift Reservoir") still matches because "Reservoir" is compared on both sides. Such waters are instead routed to `other_waters` via `find_fringe_water` (whole-word name match → likely drainage). Fetch covers 5 counties: Summit, Duchesne, Uintah, Daggett, Wasatch. Fringe routing now lives in **both** stocking paths — `fetch_latest_stocking.py` (live DWR scrape) and `update_stocking.py` (CSV replay) — so either path keeps creeks/ponds out of `lakes`; `migrate_fringe_waters.py` was the one-time backfill for records already inserted under the old loose matcher.
- **Apple Notes Integration**: Bidirectional sync using JXA scripts for personal fishing notes
- **Lake Identification**: Letter-number system (BR-25, X-64) as primary keys

### Web Frontend (`index.html`)
- **Progressive Web App**: Full offline functionality with service worker, no CDN dependencies (Tailwind CSS vendored as `tailwind.css`, Leaflet vendored under `vendor/leaflet/`)
- **JSON Data**: Loads `lakes_data.json` (generated from the database by `scripts/export_web_data.py`) with stocking records and photos nested per lake
- **Search & Filtering**: By drainage, species, depth, elevation, size, stocking years. Filters collapse by default with an active-count badge.
- **List / Map views**: One filtered result set, toggle between a list and a Leaflet map (USGS Topo + Imagery layers, status-colored pins, auto-fit, GPS "locate me"). A "Browse all lakes on the map" button opens the whole range without first picking a filter/drainage. View choice persists. Map tiles need a connection; pins/data work offline. Only `confirmed`/`manual` coordinates appear.
- **Map orientation**: The red GPS marker shows a compass heading arrow (DeviceOrientation; iOS prompts for permission on the locate tap). The map supports rotation — two-finger twist on mobile, Shift+drag on desktop — via the vendored `leaflet-rotate` plugin (`vendor/leaflet/leaflet-rotate.js`); the heading arrow compensates for the current map bearing.
- **Lake Details**: Modal views with stocking history, photos, DWR notes, "Open in Maps" link when coordinates exist
- **Mission Progress**: Header shows CAUGHT-status count toward the 100-waters goal

### Frontend Asset Regeneration
- `lakes_data.json` - regenerate with `python3 scripts/export_web_data.py` after db changes (pre-commit hook does this automatically when the db is committed)
- `cma_book.html` - full text of Cordell Andersen's book, one `<section id="cma-pNNN">` per printed page; regenerate with `python3 scripts/export_cma_book.py` (Mini-only — needs the gitignored PDF). The lake modal's "(p. NNN)" citation links and trailhead "book p. N" links fetch this file and jump to the cited page in an in-modal viewer (back arrow returns to the lake). It is deliberately NOT in the service-worker precache list (a missing file must not break install); `initApp` warm-fetches it so the SW caches it lazily for offline use.
- `tailwind.css` - regenerate only if new Tailwind classes are added to index.html: `npx tailwindcss@3.4.17 -o tailwind.css --content "./index.html" --minify`

### Data Sources Integration
- **Utah DWR**: Official stocking reports (automated fetch from dwrapps.utah.gov)
- **Norrick Data**: Physical lake characteristics (size, depth, elevation)
- **Historical DWR Pamphlets**: OCR-extracted lake descriptions from 8 vintage PDFs
- **Junesucker.com**: Species data and lake photos
- **Personal Notes**: Apple Notes sync for trip reports and fishing status

## Important Data Patterns

### Lake Identification System
- Primary key: `letter_number` (A-1, BR-25, X-64, etc.)
- Name is optional - many lakes only have designations
- Always use letter_number for lake lookups, not name

### Species Normalization
All fish species are standardized using `species_utils.py`:
- "Brook trout" → "Brookies"
- "Tiger trout" → "Tigers" 
- "Cutthroat trout" → "Cutthroats"
- Historical species marked with asterisks (*) if not recently stocked

### Apple Notes Structure
**Organization**: Notes are organized in the "Uintas 💯" folder with subfolders for each drainage. Lake notes are stored within their respective drainage subfolders.

```
Lake Name (A-42) 🎣        ← Status emoji in title
Status: CAUGHT             ← Sync field
Jed's Notes                ← User content
Trip Reports               ← User content
═══════════════════════   ← Delimiter
Auto-generated lake data   ← System content
```

### PWA Cache Strategy
- Service worker caches all static assets and database
- Cache version is automatically updated by commit hook when changes are committed
- Works offline indefinitely when installed to iPhone home screen

## Development Notes

- No build process required - static files served directly
- Database changes require re-running appropriate Python scripts
- PWA updates are handled automatically by commit hook (no manual cache version updates needed)
- Apple Notes sync requires macOS with JXA (JavaScript for Automation)
- Species data uses intelligent merging of historical and current stocking records

## File Organization

### Critical Files
- `uinta_lakes.db` - Main database
- `lakes_data.json` - Generated frontend data (do not edit by hand; regenerate via `scripts/export_web_data.py`)
- `index.html` - Web app frontend
- `tailwind.css` - Vendored static Tailwind build
- `vendor/leaflet/` - Vendored Leaflet library + marker/layer-control images, plus the `leaflet-rotate` plugin (map view)
- `service-worker.js` - PWA offline functionality
- `scripts/setup_database.py` - Initial database creation
- `scripts/export_web_data.py` - Database → lakes_data.json export
- `scripts/export_seeds.py` - Database → `data/seeds/*.csv` (reconstruction source)
- `scripts/rebuild_database.py` - Seeds → content-equivalent DB (offline recovery)
- `scripts/verify_rebuild.py` - Proves seeds round-trip to the canonical DB (drift guard)
- `data/seeds/` - Committed CSV seeds, one per table (the reproducible source of the DB)
- `.githooks/pre-commit` - Version-controlled hook: PWA cache bump + auto re-export of `data/seeds/` when the DB is committed (enable: `git config core.hooksPath .githooks`)
- `scripts/species_utils.py` - Species name standardization
- `scripts/seed_coordinates.py` - OSM coordinate seeder
- `scripts/locator_server.py` + `locator.html` - Lake Locator tool for placing/verifying coordinates
- `scripts/coord_utils.py` - Shared coordinate helpers (schema migration, name/designation normalization)

### Data Sources (`data/`)
- `lake_data.csv` - Original 609 lake designations
- `utah_dwr_stocking_data.csv` - DWR stocking records
- `norrick_lakes.txt` - Physical lake characteristics
- `dwr_original_pamphlets/` - Historical DWR PDFs
- `dwr_archive/` - **Statewide** DWR stocking snapshot (all counties, 2002-2026,
  59,357 records) plus the raw year pages, so no future project has to re-scrape.
  See its README for the three working URL facets (`label` / `county` / `species`)
  and the archive-wide data quirks.

### Generated Files (`logs/`)
- `lake_dump.txt` - Human-readable lake export
- `notes_sync.log` - Apple Notes sync history

## Boulder Mountain sub-project (`boulders/`)

A second, independent database for Boulder Mountain ("the Boulders") in Wayne +
Garfield counties — data only, no front end. Fully self-contained under
`boulders/`; it does not touch `uinta_lakes.db` and is not part of the
single-writer/Notes/PWA machinery. Full write-up: `boulders/README.md`.

```bash
cd boulders
python3 scripts/fetch_stocking.py     # DWR -> data/raw_stocking/ (cached)
python3 scripts/build_database.py     # rebuild boulders.db + QA report
python3 scripts/query.py species --has Grayling --only
```

Two things worth knowing before touching it:

- **DWR appends undocumented geographic unit codes** to water names in these
  counties (`BLIND L NBS` vs `BLIND L TLM` are different lakes 30 mi apart).
  Never match Wayne/Garfield waters on the bare name. Decoded in
  `boulders/scripts/water_utils.py`.
- **Golden trout do not exist on Boulder Mountain.** A full-archive sweep found
  only 9 golden records statewide, all 2012-2015, all Uinta lakes (U-16, Z-16,
  W-58, U-19, U-13, GR-39) — matching the 6 waters in `uinta_lakes.db`.

It shares `data/gnis/` with this project rather than duplicating the 3.5 MB
GNIS file, so don't move or rename that directory.