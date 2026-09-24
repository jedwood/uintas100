# Runbook: data sources and imports

Where every column comes from and how to refresh it. Split out of
CLAUDE.md 2026-09-24; the text below is unchanged.

### Designation conventions (`lakes.letter_number`)
**The letter prefix is a survey block, NOT a drainage code** — do not "fix" a
lake whose prefix doesn't match its drainage. DWR assigned letters by *when a
lake was surveyed*, so a block routinely spans two drainages, and `lakes.drainage`
means "which pamphlet booklet prints this lake's write-up" (i.e. watershed).
Verified against the pamphlet OCR: the Duchesne booklet prints `D-*`, `X-11/12/14`
(the Marsell Canyon three — Duchesne water, but the pamphlet sends you to the Rock
Creek map for access) and `Z-1…21, 26, 27, 31…37, 42, 43` (Mirror Lake corridor +
Naturalist Basin); the Rock Creek booklet prints the rest of the `Z-` block
(Grandaddy + Four Lakes Basins) and its own `X-*`. Junesucker says so outright:
"Some of the abbreviations such as X will be used in multiple drainage's."
Split prefixes, all correct: `X` (Rock Creek/Lake Fork/Swift Creek/Yellowstone/
Duchesne), `Z` (Duchesne/Rock Creek), `GR` (Ashley/Sheep-Carter/Beaver Creek/Burnt
Fork — GR = Green River tributaries), `G` (Smiths Fork/Blacks Fork/Henrys Fork),
`U` (Uinta River + Dry Gulch, which share one booklet).
Gotcha for designation regexes: `U-150` in pamphlet text is **State Route 150**
(the Mirror Lake Scenic Byway), not a lake.

Two house conventions on top of DWR's numbering:
- **`b` suffix** when DWR reuses a number for two distinct lakes: `X-22b` (Swift
  Creek's second X-22). `WR-14b` was retired 2026-09-08 — the 2025 pamphlet's
  "Becky Lake, WR-14" heading is a typo; Becky is **WR-77** (DWR stocking reports
  and both gillnet tables agree; `compare_new_pamphlets.HEADING_DESIGNATION_FIXES`
  keeps a re-apply from recreating it).
- **`JW-n`** (Jed's own numbering) for waters DWR describes in a pamphlet but
  never lettered: `JW-1` Deadfall (White Rocks, grayling, never in the public
  stocking report — see `WILD_SPECIES`), `JW-2` Fish Reservoir (Blacks Fork).
  Next unlettered water gets `JW-3`. Every designation regex in the code accepts
  the form, and name-only DWR stocking rows still match by exact name.

### DWR pamphlet editions (`lakes.dwr_edition`, `lakes.dwr_notes_prev`)
`dwr_notes` is the lake write-up from DWR's "Lakes of the High Uintas" pamphlet
series. `dwr_edition` records the **publication year** it came from: `2025` for
the revised editions DWR began reissuing in 2025 (Bear River, Blacks Fork,
Whiterocks so far — `data/dwr_new_pamphlets/`), otherwise the original pamphlet
for the drainage (1981–1999; the year map is `ORIGINAL_EDITION` in
`scripts/backfill_dwr_editions.py` and `DWR_ORIGINAL_EDITION` in `index.html`,
taken from the series list on the back of the 1999 Provo/Weber pamphlet).
When a new edition replaces a *materially different* write-up (difflib ratio
< 0.9), the superseded text is kept in `dwr_notes_prev`; the lake modal shows
the edition in the "DWR Notes" heading and the old text under a collapsed
"Previous edition" toggle. The 2025 pass was originally applied in place
(2026-03-03) with no provenance — `backfill_dwr_editions.py` reconstructed
both columns from the pre-March DB in git (`git show 36a0ffc^:uinta_lakes.db`).
```bash
python3 scripts/compare_new_pamphlets.py          # dry run: new pamphlet text vs DB
python3 scripts/compare_new_pamphlets.py apply    # sets dwr_edition + keeps dwr_notes_prev
```
When DWR reissues another drainage: drop its `pdftotext` output in
`data/dwr_new_pamphlets/`, add it to `PAMPHLET_FILES`, bump `PAMPHLET_EDITION`
if the year differs, dry-run, apply. The heading parser accepts digits and
curly apostrophes in names ("R.C. No. 1, WR-2", "Ted’s Lake, WR-44") — the
first pass didn't and silently skipped 16 lakes.

### DWR 2025 survey tables (`dwr_gillnet_samples`, `dwr_lake_summary`)
```bash
python3 scripts/import_dwr_survey_tables.py --dry-run   # parse the PDFs, report
python3 scripts/import_dwr_survey_tables.py             # reload rows for the 2025 edition
```
Parses the tables at the back of the 2025 pamphlet PDFs via `pdftotext -layout`
(poppler required): Whiterocks' per-species **gillnet sampling** stats (60 rows:
stocking cycle, other species, n sampled, mean/max length and weight) and Bear
River / Blacks Fork's **lake summary** rows (77: sub-drainage, access, trail
miles, campsites / spring water / horse feed, fish, stocking cycle, or "Unable to
support a fishery"). Exported nested per lake (`dwr_summary`, `dwr_gillnet`) and
shown in the modal as "DWR survey". Rows whose printed name matches no lake
(Deadfall, Fish in Blacks Fork, BR-54) keep `lake_id NULL`. Pamphlet designation
typos are corrected by name match ("Middle Rock (WR-67)" → WR-16) or by the
hand-reviewed `DESIGNATION_FIXES`; a `note` records what the pamphlet printed.
Plan/details: `docs/dwr-survey-tables-plan.md`.

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

### Falcon guide hike index (reference only, not used by the app)
```bash
python3 scripts/build_hike_index.py     # -> data/hike_index.json + data/hike_index.md
```
For "find me a hike that ..." questions, **read `data/hike_index.md` / query
`data/hike_index.json` instead of the `guide_*` tables** — the book's free-text
fields are parsed there into numbers (`distance_mi_min/max`, `time_hr_min/max`,
`destination_elevation_ft`, `difficulty` 1–4 + note, `usage_rank`, `route_types`),
each hike carries its lakes with the lake's own attributes AND Jed's status
(`jed_status`, `starred`, species, acres, elevation), plus aggregates
(`lake_count`, `lakes_uncaught_fishable`, `species_current`, ...), narrative
`tags`, the book's intro `summary`, and a reverse lake→hikes table. `lake_count`
excludes name-drops the hike doesn't visit (`mention_context: "reference"`, e.g.
"Mirror Lake Scenic Byway") — `lake_count_all_mentions` is the raw link count.
Re-run after `import_falcon_guide.py` or when lake statuses change (the CAUGHT
counts are baked in). On the Mini the EPUB adds the intro blurbs and the
book-TOC trailhead sections; on a mirror it degrades gracefully.

### Coordinates & Mapping (placing is DONE — Locator retired 2026-09-24)
**The coordinate pass is finished.** 738 lakes are `coord_status='confirmed'`;
the only 8 without coordinates are `cant_find`, and every one is a fishless,
unnamed "does not sustain fish life … shown on the map as a landmark" row with
no usable position in any source. The `seed_unverified` / `seed_suspect` review
queue is **empty**, so there is nothing left to place or verify.

Accordingly the **Lake Locator is retired**: `scripts/locator_server.py` now
exits immediately unless run with `UINTAS_LOCATOR=force`. It had been left
running on `--host 0.0.0.0` — a LAN-exposed writer into the canonical DB — for
a queue of zero. The source is kept, not deleted, because it is still the only
way to place a **new** water (a future `JW-n`, or a `cant_find` row that finally
gets a position):

```bash
UINTAS_LOCATOR=force python3 scripts/locator_server.py              # localhost only
UINTAS_LOCATOR=force python3 scripts/locator_server.py --host 0.0.0.0   # LAN; prints the URL
python3 scripts/export_web_data.py                                  # then push coords into the PWA
```
Stop it when you're done. It still obeys the single-writer model (refuses to
start on a clone carrying `.db-readonly`).

The seeding scripts below are likewise only needed if new lakes are ever added:
```bash
python3 scripts/seed_coordinates.py            # OSM seed; uses cached data if present
python3 scripts/seed_coordinates.py --refresh  # re-fetch from Overpass
```
Seeding from the pamphlet text (fills the Locator's queue, never the PWA):
```bash
python3 scripts/seed_coordinates_from_text.py            # dry run + table
python3 scripts/seed_coordinates_from_text.py --apply    # writes coord_source='dwr-text'
python3 scripts/seed_coordinates_from_text.py --revert   # undo, back to unplaced
```
DWR write-ups usually locate a lake off a named neighbour with a real bearing and
distance ("0.4 miles west of Island Lake"), which is enough to compute a position.
Guards, learned the hard way — the loose first cut put Uinta River lakes ~20 miles
away on Lake Fork's same-named Kidney, and anchored five Whiterocks lakes onto a
*trailhead* that fuzzy-matched a lake name: **anchors must be in the same drainage**
(the Uintas reuse names constantly), the reference must be called Lake/Reservoir/Pond
right there and not name a trail/pass/meadow/creek/basin, and a lake whose anchor
isn't placed yet is deferred to a later pass rather than falling through to a weaker
phrase in the same paragraph. What's left unplaced after this has no usable text —
mostly the "does not sustain fish life … shown on the map as a landmark" rows.
Coordinate columns on `lakes`: `lat`, `lng`, `coord_source` (`osm-designation`/`osm-name`/`manual`),
`coord_status` (`seed_unverified` | `seed_suspect` | `confirmed` | `manual` | `cant_find`).
Only `confirmed`/`manual` coordinates are exported to the PWA (which shows an "Open in Maps"
link); seeds stay internal to the Locator until you eyeball them. The Locator writes straight
back into `uinta_lakes.db` — which is why it obeys the `.db-readonly` writer guard.

### Python Backend (`scripts/`)
- **Data Pipeline**: CSV sources → SQLite via setup/update scripts
- **Species Standardization**: `species_utils.py` normalizes all species names to consistent format (Brookies, Tigers, Cutthroats, etc.)
- **Stocking matcher** (`database_utils.find_matching_lake`): a DWR water is credited to a lake ONLY on an exact letter-number designation or an exact name (after stripping a trailing "Lake"). Loose substring matching was removed because it mis-filed creeks/ponds onto same-named lakes (e.g. "Beaver Cr" → BR-10). "Reservoir" is NOT a throwaway suffix (only "Lake" is): a lowland "Echo Reservoir" must not name-match the tiny Uinta "Echo" lake (Z-16) — reservoirs are credited to a lake only by explicit designation, while a lake genuinely *named* "… Reservoir" (e.g. Y-41 "Drift Reservoir") still matches because "Reservoir" is compared on both sides. Such waters are instead routed to `other_waters` via `find_fringe_water` (whole-word name match → likely drainage). Fetch covers 5 counties: Summit, Duchesne, Uintah, Daggett, Wasatch. Fringe routing now lives in **both** stocking paths — `fetch_latest_stocking.py` (live DWR scrape) and `update_stocking.py` (CSV replay) — so either path keeps creeks/ponds out of `lakes`; `migrate_fringe_waters.py` was the one-time backfill for records already inserted under the old loose matcher.
- **Apple Notes Integration**: Bidirectional sync using JXA scripts for personal fishing notes
- **Lake Identification**: Letter-number system (BR-25, X-64) as primary keys

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

