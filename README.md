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

### 🔄 **IMPORTANT: Updating PWA After Code Changes**

**When you update the database or HTML files, you MUST update the PWA cache version to push updates to installed apps:**

1. **Before committing any changes**, update the cache version in `service-worker.js`:
   ```javascript
   const CACHE_NAME = 'uintas-v1'; // Change to 'uintas-v2', 'uintas-v3', etc.
   ```

2. **Automated approach** - Run this before committing:
   ```bash
   # Update cache version automatically
   sed -i '' "s/uintas-v[0-9]*/uintas-v$(date +%s)/g" service-worker.js
   ```

3. **After pushing changes**, the PWA will automatically:
   - Detect the cache version change
   - Download new files in background
   - Show "New version available! Refresh to update?" popup
   - Update with new content after user confirms

**Manual refresh for iPhone PWA**: If auto-update doesn't work, go to Settings → Safari → Clear History and Website Data, then reopen the PWA.

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

**Asterisk System**: Species with asterisks (*) appear in historical data but haven't been stocked since 2018, indicating potential treatment or natural changes. Example: "Brookies, Cutthroats*" means brook trout are currently stocked but cutthroat presence is historical only.

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
- ✅ **Enhanced Fish Species Data**: Merged Norrick historical data with stocking records since 2018
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

## Apple Notes Integration ✅ **COMPLETE**

The system provides full bidirectional synchronization between the SQLite database and Apple Notes, allowing you to manage lake data, notes, and trip reports seamlessly across both platforms.

### **Features**
- **Automated bidirectional sync** - Changes flow both ways between database and Apple Notes
- **Visual status indicators** - Emoji system for quick lake status identification
- **Surgical updates** - Only processes lakes flagged for updates (efficient performance)
- **Smart duplicate prevention** - Advanced search prevents duplicate note creation
- **Comprehensive content** - Includes all lake data, stocking records, DWR notes, Junesucker notes
- **Organized structure** - Notes organized by drainage in dedicated "Uintas 💯" folder

### **Apple Notes Structure**
```
Lake Name (A-42) 🎣        ← Status emoji in title
                             🎣=CAUGHT, ✖️=OTHERS/NONE, 🚫=NO_FISH

Status: CAUGHT             ← Editable status field
Jed's Notes               ← Always visible for editing
Add your notes here...

Trip Reports              ← Always visible for editing  
Add trip reports here...

═══════════════════════   ← Visual delimiter

• Size, elevation, species ← Auto-generated from database
• Stocking records        ← Updates automatically  
• Junesucker/DWR notes    ← Reference information
```

### **Status Emoji System**
- **🎣** = Fish caught at this lake
- **✖️** = Status marked as OTHERS or NONE
- **🚫** = Lake does not sustain fish (DWR confirmed)
- **No emoji** = No status assigned

### **Sync Scripts**
- **`sync_notes_to_db_jxa.js`** - Scans Apple Notes for `*update` tags and syncs changes back to database
- **`sync_db_to_notes_jxa.js`** - Processes flagged lakes (`notes_needs_update = TRUE`) and creates/updates Apple Notes
- **`fetch_latest_stocking.py`** - Auto-flags lakes when new stocking data is added

### **Automated Scheduling**
Cron jobs run every 6 hours to maintain synchronization:
```bash
# Check for user updates in Apple Notes (every 6 hours)
0 */6 * * * osascript sync_notes_to_db_jxa.js

# Push flagged database changes to Apple Notes (15 minutes after)
15 */6 * * * osascript sync_db_to_notes_jxa.js
```

### **Manual Sync Usage**
To manually trigger updates, add `*update` to any Apple Note and run:
```bash
osascript scripts/sync_notes_to_db_jxa.js
```

To flag specific lakes for Apple Notes updates:
```sql
UPDATE lakes SET notes_needs_update = TRUE WHERE letter_number = 'G-15';
```
Then run: `osascript scripts/sync_db_to_notes_jxa.js`

# NEXT

## 1- Lake Coordinate Mapping Project

### Prepare Google My Maps CSV Export with Drainage Groupings and Center Coordinates

I need to create a CSV export for Google My Maps import. Since Google My Maps has a 10-layer limit but we have 18 drainages, we need to group drainages based on how they were organized in the old DWR pamphlets.

Step 0: briefly research the current state of Google "My Maps" and/or Maps API. As a final product I want a map that will handle all ~700 of these lakes, that I can share with others, embed in the web app, and ideally use offline in my iPhone Google Maps app.

Step 1: Parse DWR Pamphlet Groupings
Look at the DWR pamphlet filenames in the project and determine which drainages were grouped together in each pamphlet. Create a mapping of drainage groups that will keep us under the 10-layer limit for Google My Maps.

Step 2: Create Drainage Coordinates Stub File
Create a JSON or CSV file called drainage_centers.json (or similar) with this structure:
json{
  "Ashley Creek": {"lat": null, "lng": null},
  "Bear River": {"lat": null, "lng": null},
  [... for all 18 drainages]
}
This will be a stub file that I'll manually populate with center coordinates for each drainage.

Step 3: Create CSV Export Script
Write a script that:

- Reads the drainage center coordinates from the stub file
- Queries the database for all lakes
- Assigns each lake the coordinates of its drainage center
- Groups drainages into layers based on the DWR pamphlet groupings
- Exports a CSV suitable for Google My Maps import with these columns:

- Name (lake name + designation)
- Description (follow a similar pattern that we use for the Apple Notes creation: I want as much info in this description as we have, subject to Google Map limitations, which you'll need to research)
- Latitude (from drainage center)
- Longitude (from drainage center)
- Layer (the drainage group name for organizing into separate layers)

Requirements:

- Handle cases where drainage center coordinates might be missing (skip or use default)
- Make the Description field informative but concise for the map popup
- Ensure the Layer field groups drainages logically for the 10-layer limit
- Generate filename like uinta_lakes_for_mapping.csv

The goal is to create a CSV I can import to Google My Maps, where each drainage group becomes a separate layer, and all lakes start positioned at their drainage center so I can drag them to precise locations while noting elevations.

## 2- Add info from my books
- scan in simple additional drainage maps
- scan in and OCR data tables to fill in missing elevation, size, depth values
- hiking/camping/fishing info for each lake that we have info on.
