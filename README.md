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

**Asterisk System**: Species with asterisks (*) appear in historical Norrick data but haven't been stocked since 2018, indicating potential treatment or natural changes. Example: "Brookies, Cutthroats*" means brook trout are currently stocked but cutthroat presence is historical only.

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
- **`lake_dump.txt`**: Human-readable database export
- **`unmatched_stocking.csv`**: Non-Uintas stocking records (correctly filtered)
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

# NEXT STEPS

## 1- Lake Coordinate Mapping Project

Evaluate Google Maps integration and check feasibility of including core vital info within map marker details panel. Consider implementing a "human in the loop" system to gather GPS coordinates for lakes that don't have location data.

**Potential approaches:**
- Google Maps API integration with custom markers
- Crowdsourced coordinate collection system
- Integration with existing USGS or DWR geographic data sources

## 2- Apple Notes Integration ✅ **IN PROGRESS**

**🎯 Status**: Database → Apple Notes sync **COMPLETE**. Notes → Database sync pending.

### **Current Functionality**
- **Automated note creation** with beautiful HTML formatting 
- **Surgical updates** - only processes lakes flagged in database (`notes_needs_update = TRUE`)
- **Smart duplicate prevention** - finds existing notes across all emoji variations
- **Comprehensive content** - includes all lake data, stocking records, DWR notes, Junesucker notes
- **Bidirectional structure** - editable sections above delimiter, auto-generated below
- **Auto-flagging system** - SQLite triggers automatically flag lakes when data changes

### **Apple Notes Structure**
```
Lake Name (A-42) 🎣        ← Status emoji (🎣=CAUGHT, 🚫=OTHERS/NONE)

Status: CAUGHT
Jed's Notes                 ← Always visible for editing
Add your notes here...

Trip Reports               ← Always visible for editing  
Add trip reports here...

═══════════════════════    ← Visual delimiter

• Size, elevation, species  ← Auto-generated from database
• Stocking records         ← Updates automatically  
• Junesucker/DWR notes     ← Reference information
```

### **Scripts**
- `sync_flagged_notes_jxa.js` - Processes flagged lakes and creates/updates Apple Notes
- `fetch_latest_stocking.py` - Auto-flags lakes when new stocking data added
- SQLite triggers auto-flag lakes on any data changes

### **Next Steps**
1. **Notes → Database parsing** - Parse Apple Notes content back to database
2. **Automated scheduling** - Set up cron job to run `sync_flagged_notes_jxa.js`
3. **Hashtag processing** - Parse `#update` tags from edited Apple Notes
4. **Two-way sync workflow** - Complete bidirectional sync system
5. **Create "About" page** - add a little "About" link at the bottom of the web app that displays a page with the following:
- paragraph that says "I'm on a mission to catch a fish out of at least 100 different Uintas waters. I grew up in Provo fishing and camping all over, but somehow never in the Uintas. At the ripe age of 42 I spent a week on the Highline trail and realized what I've been missing."
- A section with the title "Sources of Information & Inspiration" that then has subsections with links:
  - Websites
    - [Junesucker.com](https://junesucker.com/uintas)
    - [DWR Stocking Reports](https://dwrapps.utah.gov/fishstocking/Fish)
  - YouTube Channels
    - [TroutHowler](https://www.youtube.com/@TroutHowler)
    - [Utah Water Log](https://www.youtube.com/@UtahWaterLog)
  - Books
    - [Hiking Utah's High Uintas](https://www.amazon.com/Hiking-Utahs-Uintas-Andrew-Gillman/dp/1493075691)
    - [High Uintas Adventures](https://www.amazon.com/High-Uintas-Adventures-Backcountry-Planner/dp/B08FPGJ214)
  - Old DWR Pamphlets
    {provide links to each of the files in `data/dwr_original_pamphlets` and name them by extrapolation from their file names. Note that they contain multiple drainages per file}

