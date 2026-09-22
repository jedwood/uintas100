# Uinta Mountains Fishing Database

A comprehensive SQLite database of fishing locations in the Uinta Mountains, combining official stocking data with detailed physical lake characteristics.

## Live Web App

**🌐 Live Site**: https://jedwood.github.io/uintas100  
**📁 Repository**: https://github.com/jedwood/uintas100

The web app (`index.html`) provides a complete interface for searching and filtering lakes with real-time database queries using SQL.js. Features include lake search, drainage browsing, detailed lake modals with stocking history, standardized fish species filtering, and responsive design.

### PWA (Progressive Web App) Features
**✨ Offline Access**: The app works completely offline when added to iPhone home screen
- Service Worker caches all data for indefinite offline access
- SQLite database (672 lakes) cached locally  
- All drainage images and app resources cached
- No 7-day Safari eviction when installed to home screen

**📱 iPhone Installation**: 
1. Visit the site in Safari on your iPhone
2. Tap the Share button (⎋)  
3. Select "Add to Home Screen"
4. The app will work offline indefinitely

### ✅ Before a trip: check "Sync & offline" says Ready
Open the app on the phone (any connection), tap **Sync & offline** at the
bottom, and look for **✓ Ready for offline — lake data from …, 18 drainage
maps, backup copy saved**. If it says **✗ Not ready**, tap **Repair** while
you still have signal. The app also self-checks a few seconds after every
launch and shows a red **⚠ Offline copy incomplete** chip in the header if
something is missing, so a broken offline copy is visible at home, not at the
trailhead. Map tiles are separate — download them from the ⤓ button on the map.

Why this exists: on 2026-09-21 the app opened all day to "Lake data not
accessible" in a new drainage. A version update on a flaky connection had
replaced a complete cache with an empty one. The service worker now refuses to
activate unless every critical file downloaded, looks for data in every cache
it has, keeps a second copy of the lake data in IndexedDB, and logs its
lifecycle events (visible under **Details** in the same panel).

### 🔄 Updating the PWA after code changes

Nothing manual: the version-controlled pre-commit hook (`git config
core.hooksPath .githooks`, once per clone) bumps the cache version in
`service-worker.js` on **every** commit — including the unattended ones (the
08:00 stocking update and every "App edits" commit from the phone sync). After
the push and the github.io deploy, an installed app finds the new version on
its next launch/foreground, precaches everything (all-or-nothing), then shows
"New version available! Refresh to update?".

### 🧑‍💻 Working in this repo while the automation runs (read this)

The Mini's automation — the edits server (commits whenever the phone syncs)
and the 08:00 stocking cron — commits **in this same working tree, at any
moment, without asking**. Two rules keep your half-finished work out of those
pushes, and both are enforced by code, not memory:

- **Automation commits only what it owns.** `scripts/auto_commit.py` builds
  each unattended commit in a private index (HEAD + just the DB/edit-log/CSV
  and what the hook derives from them), so anything you have `git add`ed or
  edited elsewhere is never included — it used to be: a plain `git commit`
  took the whole index.
- **The hook stages only the version bump**, not the whole
  `service-worker.js`. It used to `git add` the file, which shipped every
  in-progress edit to the worker on the next auto-commit — several
  half-rewritten workers went live that way in Sept 2026.

What that means for you: edit freely; nothing goes out until *you* commit it.
Two things it can't protect: (1) the DB itself — if you run a migration, do it
as one script (SQLite keeps each run consistent), because the DB is committed
as-is whenever the automation fires; (2) the exporters
(`scripts/export_seeds.py`, `scripts/export_web_data.py`) — the hook runs the
working-tree copies, so finish and commit an exporter change in one go.
`tests/auto_commit_isolation.sh` proves the isolation in a throwaway clone;
`tests/offline/run.sh` proves the offline guarantee in a browser.

**Manual refresh for iPhone PWA**: if an update doesn't show up, quit and
reopen the app (it checks for a new worker on every foreground). Clearing
Safari website data also deletes the offline data and map tiles — last resort.

## Database Overview

**File**: `uinta_lakes.db` (SQLite)  
**Total Lakes**: 672  
**Total Drainages**: 17  
**Stocking Records**: 2,290  
**Data Sources**: Utah DWR stocking reports + Norrick physical data + Historical DWR lake pamphlets + Drainage system data

## Key Features

- **Letter-number lake designations** (e.g., BR-25, X-64, G-15) for precise identification
- **Physical characteristics**: Lake size (acres), maximum depth (feet), elevation
- **Fish species data**: Standardized species names (Brookies, Cutthroats, Tigers, etc.) with comprehensive merging of historical and stocking data
- **Fishing pressure ratings**: Low/Moderate/High/Very Low for trip planning
- **Stocking history**: Multi-year stocking records with species, quantities, dates
- **Drainage systems**: Comprehensive information on all 17 major drainage areas with access details and maps
- **Historical DWR notes**: Detailed lake descriptions from original DWR survey pamphlets

## Fish Species Standardization

The database uses standardized species names for consistency across all data sources:

- **Brookies** (Brook trout)
- **Cutthroats** (Cutthroat trout)  
- **Tigers** (Tiger trout)
- **Rainbows** (Rainbow trout)
- **Goldens** (Golden trout)
- **Grayling** (Arctic grayling)
- **Splake** (Splake)
- **Tiger muskie** (Tiger muskie)
- **Channel catfish** (Channel catfish)

**Asterisk System**: Species with asterisks (*) appear in historical data but haven't been stocked since 2015, indicating potential treatment or natural changes. Example: "Brookies, Cutthroats*" means brook trout are currently stocked but cutthroat presence is historical only.

## Database Schema

### `lakes` table
- `letter_number` (unique): Official designation (BR-25, X-64, etc.)
- `name`: Common lake name (may be null for designation-only lakes)  
- `drainage`: Watershed/drainage system
- `size_acres`: Surface area in acres
- `max_depth_ft`: Maximum depth in feet
- `elevation_ft`: Elevation of the lake in feet
- `dwr_notes`: Historical descriptions from DWR lake pamphlets
- `fish_species`: Standardized species names (Brookies, Cutthroats, etc.) with asterisk indicators for historical-only species
- `junesucker_notes`: June sucker habitat and conservation notes
- `jed_notes`: Personal fishing notes and observations
- `status`: Lake accessibility status
- `fishing_pressure`: Fishing pressure category
= `no_fish`: for lakes that have explicit info from the DWR as not sustaining fish

### `stocking_records` table
- Links to lakes via `lake_id`
- Species, quantities, lengths, stocking dates
- Multi-year historical data

### `drainages` table
- `id`: Primary key
- `name`: Drainage system name (e.g., "Ashley Creek Drainage")
- `info`: Detailed description, access information, and fishing characteristics
- `map`: Relative path to drainage map image

## Key Files

- **`setup_database.py`**: One-time database setup (lakes, Norrick data, drainages)
- **`update_stocking.py`**: Stocking data import and updates
- **`database_utils.py`**: Core database utility functions
- **`species_utils.py`**: Shared species name normalization and formatting functions
- **`lake_data.csv`**: Original lake designations and drainages (609 lakes)
- **`utah_dwr_stocking_data.csv`**: DWR stocking data (3,361 records)
- **`norrick_lakes.txt`**: Physical lake data (565+ records)
- **`logs/lake_dump.txt`**: Human-readable database export
- **`logs/unmatched_stocking.csv`**: Non-Uintas stocking records (correctly filtered)
- **`all_drainages.md`**: Source data for drainage system information (processed)
- **`drainages/`**: Individual drainage markdown files and map images
- **`lake_pages/`**: Individual lake information pages

## Processing Logic

1. **Lake boundary filter**: Only includes lakes with letter-number designations
2. **Pattern matching**: Handles both "X-64" and "X64" formats  
3. **Data integration**: Matches stocking records to lakes via designations
4. **Quality control**: Tracks data sources and confidence levels

## Usage Examples

**View all lakes in Bear River drainage:**
```sql
SELECT letter_number, name, size_acres, max_depth_ft 
FROM lakes 
WHERE drainage = 'Bear River Drainage' 
ORDER BY size_acres DESC;
```

**Find high-pressure fishing destinations:**
```sql
SELECT letter_number, name, size_acres, fish_species, elevation_ft
FROM lakes 
WHERE fishing_pressure = 'High' 
ORDER BY size_acres DESC;
```

**Get stocking history for specific lake:**
```sql
SELECT s.species, s.quantity, s.stock_date, s.source_year
FROM stocking_records s 
JOIN lakes l ON s.lake_id = l.id 
WHERE l.letter_number = 'Z-1';
-- Returns normalized species like "Brookies", "Tigers", "Cutthroats"
```

**Find lakes by fish species (using normalized names):**
```sql
SELECT letter_number, name, fish_species 
FROM lakes 
WHERE fish_species LIKE '%Brookies%' 
ORDER BY name;
```

**View all drainage systems:**
```sql
SELECT name, map FROM drainages ORDER BY name;
```

**Find drainage information:**
```sql
SELECT name, info FROM drainages WHERE name LIKE '%Bear River%';
```

## Notable Statistics

- **Largest lake**: Atwood (U-16) at 200 acres
- **Deepest lake**: Crater (X-94) at 147 feet  
- **Most common species**: Brookies (naturally reproducing in many lakes)
- **High-pressure lakes**: 89 premium destinations
- **Remote options**: 224 low-pressure lakes

## Recent Updates

- ✅ **Species Name Standardization**: Comprehensive normalization to "Brookies", "Cutthroats", "Tigers", etc.
  - Updated 2,290 stocking records with normalized species names
  - Updated 576 lakes with merged historical and stocking species data
  - Added asterisk indicators (*) for species in historical data but not recently stocked
  - Implemented shared species_utils.py for consistent normalization across all scripts
- ✅ **Enhanced Fish Species Data**: Merged Norrick historical data with stocking records since 2015
  - Intelligent filtering matches either historical or stocking data
  - Display shows comprehensive species with provenance indicators
  - Removed old manual species translation logic from web app
- ✅ **DWR Historical Notes Integration**: Added "This lake does not sustain fish life" notes
  - Updated 37 lakes with DWR sustainability information
  - Enhanced lake detail views with historical context
- ✅ **Data Quality Improvements**: 
  - Removed unused `data_source` field from lakes table
  - Cleaned up 6 erroneous lake names with spacing issues
  - Fixed drainage references and separated combined drainages
- ✅ **Complete Drainage System Data**: All 17 drainages with detailed descriptions and maps
- ✅ **Complete DWR PDF Extraction**: 487 lake entries from 8 historical DWR pamphlets
- ✅ **PWA Enhancements**: Offline functionality with automatic cache updates

## Quick Start

**Initial database setup (run once):**
```bash
python3 setup_database.py
```

**Add/update stocking data:**
```bash  
python3 update_stocking.py
```

**Generate fresh dump files:**
```python
from database_utils import dump_lake_data, dump_stocking_data, dump_combined_data
import sqlite3
conn = sqlite3.connect('uinta_lakes.db')
dump_lake_data(conn)
dump_stocking_data(conn) 
dump_combined_data(conn)
```

**Access drainage information:**
```sql
-- View all drainages
SELECT * FROM drainages ORDER BY name;

-- Get specific drainage details
SELECT info FROM drainages WHERE name = 'Bear River Drainage';
```

## Drainage System Files

All 17 major drainage systems are now documented with individual markdown files:

- **Ashley Creek Drainage** (`ashley-creek-drainage.md`)
- **Bear River Drainage** (`bear-river-drainage.md`) 
- **Beaver Creek Drainage** (`beaver-creek-drainage.md`)
- **Blacks Fork Drainage** (`blacks-fork-drainage.md`)
- **Burnt Fork Drainage** (`burnt-fork-drainage.md`)
- **Dry Gulch Drainage** (`dry-gulch-drainage.md`)
- **Duchesne River Drainage** (`duchesne-river-drainage.md`)
- **Henrys Fork Drainage** (`henrys-fork-drainage.md`)
- **Lake Fork Drainage** (`lake-fork-drainage.md`)
- **Provo River Drainage** (`provo-river-drainage.md`)
- **Rock Creek Drainage** (`rock-creek-drainage.md`)
- **Sheep/Carter Creek Drainages** (`sheep-creek-carter-creek-drainage.md`)
- **Smiths Fork Drainage** (`smiths-fork-drainage.md`)
- **Swift Creek Drainage** (`swift-creek-drainage.md`)
- **Uinta River Drainage** (`uinta-river-drainage.md`)
- **Weber River Drainage** (`weber-river-drainage.md`)
- **Whiterocks Drainage** (`whiterocks-drainage.md`)
- **Yellowstone River Drainage** (`yellowstone-river-drainage.md`)

Each file includes detailed access information, fishing characteristics, and formatted lake data tables.

This database provides the most comprehensive fishing resource available for the Uinta Mountains, combining official stocking data with detailed physical lake characteristics and drainage system information for informed trip planning.

## Personal Notes & Status Sync

Lake `status`, Jed's Notes, and Trip Reports are edited directly in the PWA
itself — the "My Record" section of the lake modal — from any device, online
or offline. **Apple Notes is no longer used for this sync** (retired as a
write path 2026-08-10); see below.

### **How it works**
- **Client (`index.html`)**: edits save instantly to `localStorage` (fully
  offline, built for multi-day trips), overlay the loaded data, and flush to
  the edits server whenever it's reachable. A header chip shows the pending
  count; the "Sync" panel has a manual sync button and a server-URL override.
- **Server (`scripts/edits_server.py`)**: runs only on the Mac Mini (the
  sole database writer) as a LaunchAgent on port 8802. Applies edits
  last-write-wins per (lake, field) against an audit log
  (`data/app_edits_log.jsonl`), then commits and pushes in the background —
  every installed PWA picks up the change on its next service-worker update.
- The iPhone's PWA (installed from the https github.io page) reaches the
  edits server over a Tailscale HTTPS proxy, since a secure page can't fetch
  `http://` LAN URLs directly.

```bash
curl http://olaf.local:8802/api/ping   # is the edits server up?
```

### **Apple Notes (retired as a write path, 2026-08-10)**
Personal notes and status used to sync bidirectionally with Apple Notes via
JXA scripts and an automatic LaunchAgent (`com.limechile.uintas-notes-sync`).
That round trip is retired: user fields are now edited in the PWA (above),
and re-enabling Notes→DB sync would overwrite them with stale note content.
The scheduling LaunchAgent has been unloaded and is no longer deployed on any
machine.

- **`sync_notes_to_db_jxa.js`** / **`sync_db_to_notes_jxa.js`** — the JXA
  sync scripts remain in `scripts/` for manual/archival use only, and
  `notes_sync_agent.py` (the combined round trip) now runs only when
  explicitly invoked with `UINTAS_NOTES_SYNC=force`.

# NEXT

## 1- Lake Coordinate Mapping Project

### Prepare Google My Maps CSV Export with Drainage Groupings and Center Coordinates

I need to create a CSV export for Google My Maps import. Since Google My Maps has a 10-layer limit but we have 18 drainages, we need to group drainages based on how they were organized in the old DWR pamphlets.

**Step 0: Research Findings (2025) ✅**

**Google My Maps Capabilities:**
- **Layer Limit**: 10 layers maximum (confirmed for 2025)
- **Data Import**: Up to 2,000 rows per import, 40MB file size limit
- **CSV Requirements**: Column names limited to 64 characters, first row must be headers
- **Sharing**: Public web links, private sharing, website embedding supported
- **Mobile**: Android app available, basic offline capabilities through standard Google Maps
- **Export**: Can export to KML for use in other platforms

**Alternative Platform Research:**
- **CalTopo**: Supports GPX/KML/GeoJSON import but **crashes with "anything over a few hundred points"** - not suitable for 700+ lakes
- **Apple Maps**: Personal favorite mentioned, can import from KML exports
- **Export Strategy**: Start with Google My Maps, then export KML/CSV for import to CalTopo, Apple Maps, etc.

**Recommendation**: Proceed with Google My Maps as primary platform (web-based sharing priority), then use KML export for other platforms. The 10-layer limit requires strategic drainage groupings per DWR pamphlet organization.

**Step 1: DWR Pamphlet Groupings Analysis ✅**

Based on DWR pamphlet filenames in `data/dwr_original_pamphlets/`, the historical groupings are:

1. **Bear River + Blacks Fork** (`dwr-bear-blacks-fork.pdf`)
2. **Dry Gulch + Uinta River** (`dwr-dry-gulch-and-uinta.pdf`)
3. **Duchesne River** (`dwr-duchesne.pdf`)
4. **Provo River + Weber River** (`dwr-provo-weber.pdf`)
5. **Sheep Creek + Carter Creek + Burnt Fork** (`dwr-sheep-carter-burnt-fork.pdf`)
6. **Smiths Fork + Henrys Fork + Beaver Creek** (`dwr-smith-henry-beaver.pdf`)
7. **Uintas + Rock Creek** (`dwr-uintas-rock-creek.pdf`)
8. **Yellowstone + Lake Fork + Swift Creek** (`dwr-yellowstone-lake-fork-swift.pdf`)

**Total: 8 Layer Groups** (well under the 10-layer Google My Maps limit)

**Step 2: Create Drainage Coordinates Stub File**

Create `drainage_centers.json` with this structure:
```json
{
  "Ashley Creek Drainage": {"lat": null, "lng": null},
  "Bear River Drainage": {"lat": null, "lng": null},
  "Beaver Creek Drainage": {"lat": null, "lng": null},
  [... for all 18 drainages]
}
```
**Format: JSON** (preferred for easy programmatic access)

**Step 3: CSV Export Script Requirements**

**Description Field Priority** (researched Google My Maps limits):
1. **Species** (or "NO FISH" if flagged as no_fish)
2. **Depth, Size** (brief format: "45 acres, 12 ft deep")
3. **Stocking History** (most recent: "Last stocked: 2023 Brookies")  
4. **DWR Notes** (truncated if needed)
5. **Character Limit**: No specific limit found for description content, but keep concise for mobile readability

**CSV Columns:**
- **Name**: Lake designation + name (e.g., "G-49" or "G-49 (Sample Lake)")
- **Description**: Species, depth, size, recent stocking, key DWR info
- **Latitude**: From drainage center coordinates
- **Longitude**: From drainage center coordinates  
- **Layer**: DWR pamphlet group name (8 total groups)

Requirements:

- Handle cases where drainage center coordinates might be missing (skip or use default)
- Make the Description field informative but concise for the map popup
- Ensure the Layer field groups drainages logically for the 10-layer limit
- Generate filename like uinta_lakes_for_mapping.csv

The goal is to create a CSV I can import to Google My Maps, where each drainage group becomes a separate layer, and all lakes start positioned at their drainage center so I can drag them to precise locations while noting elevations.


# FUTURE
## 2- Add info from my books
- scan in simple additional drainage maps
- scan in and OCR data tables to fill in missing elevation, size, depth values
- hiking/camping/fishing info for each lake that we have info on.
