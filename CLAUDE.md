# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

## Overview

A SQLite database of every lettered lake in Utah's Uinta Mountains (746
lakes, 24 years of DWR stocking records, DWR pamphlet write-ups, guidebook
hikes, photos, and Jed's own catch record), plus the Progressive Web App
that publishes it — <https://jedwood.github.io/uintas100>. The app is
feature-complete and every lake is placed on the map; most work here now is
**querying the data**, not changing the app.

## Answering "find me lakes that…"

Use the **`find-lakes` skill** (`.claude/skills/find-lakes/`) — it loads the
value vocabulary, the data gotchas, and query recipes. The short version:

```bash
python3 scripts/lakes.py "SELECT designation, name, drainage, last_stocked
                          FROM lake_search WHERE ... ORDER BY ... LIMIT 20"
python3 scripts/lakes.py --columns     # what you can filter on
```

`scripts/lakes.py` flattens six tables plus the hike index, the curated
collections and the OSM trail-distance cache into one row per lake in
`data/cache/lake_search.db` (gitignored, auto-rebuilt in ~1 s). It is
read-only. Don't hand-roll the joins; don't query `uinta_lakes.db` directly
for a multi-criteria search.

## Hard invariants

Violating one of these causes real damage, so they live here rather than in
a runbook:

- **One machine writes.** The Mac Mini is the sole writer of
  `uinta_lakes.db`; every other device is a client of the published app. A
  clone carrying a gitignored `.db-readonly` marker is a read-only mirror
  and the write scripts self-guard on it. Never add an unattended committer
  that isn't guarded. → `docs/runbooks/edits-push.md`
- **Automation commits in this same tree at any moment.** Leave in-progress
  work uncommitted as long as you like — the edits server and the stocking
  cron commit through a private index and take only their own files. Never
  `git add -A` / `git commit -a` from automation.
  → `docs/runbooks/publishing.md`
- **Generated files are never hand-edited**: `lakes_data.json`
  (`scripts/export_web_data.py`), `data/seeds/*.csv`
  (`scripts/export_seeds.py`), `data/hike_index.*`
  (`scripts/build_hike_index.py`), `cma_book.html`, `tailwind.css`. The
  pre-commit hook regenerates the first two when the DB is committed.
- **The DB must stay rebuildable from the seeds.** `scripts/verify_rebuild.py`
  must exit 0. Adding a table or column to `uinta_lakes.db` means adding a
  seed; derived data that doesn't belong in the canonical DB goes *outside*
  it (that's why `data/collections.json`, `data/app_edits_log.jsonl` and
  `data/cache/lake_search.db` are separate files).
- **The letter prefix is a survey block, not a drainage code.** `X-` lakes
  sit in five different drainages — don't "fix" a mismatch. Lakes are keyed
  on `letter_number`; `name` is optional and heavily reused across the range.
- **An asterisk in `fish_species` means historical**, not current
  (`"Brookies, Cutthroats*"`). All species names are normalized by
  `scripts/species_utils.py`.
- **A failed service-worker precache must fail the install.** The offline
  guarantee is a written contract with a regression suite; run
  `tests/offline/run.sh` after touching `service-worker.js` or the
  data-loading path in `index.html`. → `docs/runbooks/offline-pwa.md`
- **Never commit `data/push/` secrets** (VAPID private key, per-device
  subscriptions) — the repo is public.

## Common tasks

| Task | Command | Detail |
|---|---|---|
| Find lakes matching criteria | `python3 scripts/lakes.py "SELECT …"` | `find-lakes` skill |
| Pull the latest DWR stocking | `python3 scripts/fetch_latest_stocking.py` | publishing |
| Regenerate the app's data file | `python3 scripts/export_web_data.py` | publishing |
| Publish a change | `git commit` (the hook bumps the cache + re-exports) | publishing |
| Prove the seeds still round-trip | `python3 scripts/verify_rebuild.py` | publishing |
| Serve the app locally | `python3 -m http.server 8804` (**not** :8000) | publishing |
| Check the writer is up | `curl http://olaf.local:8802/api/ping` | edits-push |
| Send a test push | `python3 scripts/push_utils.py test "message"` | edits-push |
| Re-import a new DWR pamphlet | `python3 scripts/compare_new_pamphlets.py apply` | data-imports |
| Re-scrape junesucker.com | `python3 scripts/scrape_junesucker.py` | data-imports |
| Rebuild the hike index | `python3 scripts/build_hike_index.py` | data-imports |
| Verify a frontend change | Playwright (see `showboat` skill) | — |

One-time per clone: `git config core.hooksPath .githooks`.

## Runbooks

Each is the full, unabridged text that used to live in this file.

| File | Covers |
|---|---|
| `docs/runbooks/publishing.md` | Seeds → rebuild → verify, the pre-commit hook, PWA cache bump, Collections, frontend asset regeneration, dev server, working in this tree while the automation commits |
| `docs/runbooks/edits-push.md` | Single-writer model and the `.db-readonly` guard, the PWA edits server on :8802, Tailscale :8443, iOS Web Push + badge |
| `docs/runbooks/offline-pwa.md` | Service-worker offline contract and its regression suite, offline map tiles, map views and rotation, lake modal |
| `docs/runbooks/data-imports.md` | Designation conventions, DWR pamphlet editions, 2025 survey tables, junesucker scrape, Falcon hike index, coordinates, stocking matcher and fringe waters, `data/` inventory |
| `docs/runbooks/retired.md` | Apple Notes sync, the Tauri control panel, the Lake Locator — why each was retired and how to run it manually if ever needed |
| `docs/db-recovery-plan.md` | Full disaster-recovery write-up |
| `deploy/README.md` | LaunchAgent deployment on the Mini (non-standard: home on an external volume) |

## Architecture at a glance

**Database** — `uinta_lakes.db`, canonical, reconstructable from
`data/seeds/*.csv`.

| Table | Rows | What |
|---|--:|---|
| `lakes` | 746 | designation (`A-1`, `BR-25`, `X-64`), physical data, species, coordinates, DWR/junesucker/Andersen notes, Jed's status |
| `stocking_records` | 7,357 | DWR stocking history, 2002–present, normalized species |
| `drainages` | 18 | drainage systems with access info and maps |
| `guide_hikes` / `guide_hike_lakes` / `guide_trailheads` | 90 / 405 / 22 | Falcon *Hiking Utah's High Uintas* (3rd ed.) |
| `dwr_lake_summary` / `dwr_gillnet_samples` | 77 / 60 | tables from the 2025 DWR pamphlets |
| `lake_treatments` | 2 | rotenone reclamation projects that included a lettered lake (`scripts/import_lake_treatments.py`); stream-only treatments are out of scope |
| `trailheads` / `trailhead_lakes` | 50 / — | Andersen book trailheads |
| `other_waters` / `other_stocking_records` | 15 / — | "fringe" waters DWR stocks that are **not** lettered lakes (creeks, ponds). Deliberately outside `lakes` and the PWA |
| `photos`, `fishing_reports` | 34 / — | junesucker photos; per-trip records |

**Frontend** — `index.html` is the whole app: a single-file PWA with no CDN
dependencies (Tailwind vendored as `tailwind.css`, Leaflet under
`vendor/leaflet/`). It loads `lakes_data.json`, offers search + filters
(drainage, species, depth, elevation, size, stocking years, Collections),
list and map views, lake modals, offline map tiles and Web Push. No build
step. `#A-11` deep-links straight to a lake.

**Backend** — `scripts/`, plain Python 3 + sqlite3, no framework. Data
pipeline is CSV/PDF/web sources → SQLite → `lakes_data.json`.

## Critical files

- `uinta_lakes.db` — the database. `data/seeds/` — its committed, diffable source.
- `scripts/lakes.py` — read-only query tool (see above).
- `scripts/export_web_data.py` → `lakes_data.json` (generated; don't edit).
- `scripts/export_seeds.py` / `rebuild_database.py` / `verify_rebuild.py` — the reproducibility loop.
- `scripts/species_utils.py` — species normalization and `WILD_SPECIES`.
- `scripts/database_utils.py` — `find_matching_lake`, the stocking matcher.
- `scripts/auto_commit.py` — private-index commits for unattended writers.
- `index.html`, `service-worker.js`, `manifest.json`, `tailwind.css`, `vendor/leaflet/` — the app.
- `.githooks/pre-commit` — cache bump + seed/JSON re-export.
- `data/collections.json` — hand-curated lake sets behind the PWA's Collections filter.
- `data/hike_index.md` / `.json` — the Falcon guide parsed into numbers; read this, not the `guide_*` tables, for "find me a hike that…".
- `docs/less-visited-lakes.md`, `docs/4x4-access-lakes.md` — worked arguments behind the collections.
- `tests/offline/run.sh`, `tests/auto_commit_isolation.sh` — the two regression suites.

## Boulder Mountain sub-project (`boulders/`)

A second, independent database for Boulder Mountain ("the Boulders") in Wayne +
Garfield counties — data only, no front end. Fully self-contained under
`boulders/`; it does not touch `uinta_lakes.db` and is not part of the
single-writer/PWA machinery. Full write-up: `boulders/README.md`.

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
