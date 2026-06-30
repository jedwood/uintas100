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
  - Mirror (MacBook): `touch .db-readonly`
  - Writer (Mini): the marker must NOT exist (`ls .db-readonly` → absent)
- The Mini is the only machine that should run the schedulers/cron for fetch and
  Notes sync. You edit Apple Notes on any device; iCloud syncs them to the Mini,
  which is the only place Notes↔DB is translated.
- Notes→DB runs on the Mini as the `com.limechile.uintas-notes-sync` LaunchAgent
  (every 6h; `scripts/notes_sync_agent.py` → Notes→DB then commit+push). Because
  the home is on an external `/Volumes` disk, its deployment is non-standard
  (internal-disk plist, FDA on the venv python, reboot revival via the
  agent-bootstrapper). Full runbook: `deploy/README.md`.

### Apple Notes Sync
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
**⚠️ DB→Notes is a known data-loss hazard right now.** `sync_db_to_notes_jxa.js`
rebuilds the whole note body and **wipes anything above the ═══ delimiter**
(un-captured trip reports / status). Do NOT schedule it. Run it by hand only,
until a wipe-safe version (preserve everything above ═══, regenerate only the
auto-data section below) exists. `sync_notes_and_push.sh` deliberately runs only
the Notes→DB direction for this reason.

### Coordinates & Mapping
```bash
# 1. Seed ~70% of lake coordinates from OpenStreetMap (matched by designation + name)
python3 scripts/seed_coordinates.py            # uses cached OSM data if present
python3 scripts/seed_coordinates.py --refresh  # re-fetch from Overpass

# 2. Manually place/verify the rest in the Lake Locator (local web tool)
python3 scripts/locator_server.py              # open http://localhost:8777/locator.html

# 3. Push verified coords into the PWA data
python3 scripts/export_web_data.py
```
Coordinate columns on `lakes`: `lat`, `lng`, `coord_source` (`osm-designation`/`osm-name`/`manual`),
`coord_status` (`seed_unverified` | `seed_suspect` | `confirmed` | `manual` | `cant_find`).
Only `confirmed`/`manual` coordinates are exported to the PWA (which shows an "Open in Maps"
link); seeds stay internal to the Locator until you eyeball them. The Locator writes straight
back into `uinta_lakes.db`.

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
python3 -m http.server 8000
# or
npx serve .
```

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

### Generated Files (`logs/`)
- `lake_dump.txt` - Human-readable lake export
- `notes_sync.log` - Apple Notes sync history