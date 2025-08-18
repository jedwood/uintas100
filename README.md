# Uinta Mountains Fishing Database

A comprehensive SQLite database of fishing locations in the Uinta Mountains, combining official stocking data with detailed physical lake characteristics.

## Database Overview

**File**: `uinta_lakes.db` (SQLite)  
**Total Lakes**: 672  
**Total Drainages**: 18  
**Stocking Records**: 2,301  
**Data Sources**: Utah DWR stocking reports + Norrick physical data + Drainage system data

## Key Features

- **Letter-number lake designations** (e.g., BR-25, X-64, G-15) for precise identification
- **Physical characteristics**: Lake size (acres), maximum depth (feet)
- **Fish species data**: Detailed species with stocking/natural reproduction status
- **Fishing pressure ratings**: Low/Moderate/High/Very Low for trip planning
- **Stocking history**: Multi-year stocking records with species, quantities, dates
- **Drainage systems**: Comprehensive information on all 18 major drainage areas with access details and maps

## Database Schema

### `lakes` table
- `letter_number` (unique): Official designation (BR-25, X-64, etc.)
- `name`: Common lake name (may be null for designation-only lakes)  
- `drainage`: Watershed/drainage system
- `size_acres`: Surface area in acres
- `max_depth_ft`: Maximum depth in feet
- `fish_species`: Species present with reproduction notes
- `fishing_pressure`: Fishing pressure category
- `data_source`: Data provenance tracking

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

- **`database.py`**: Main processing script with all functions
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
SELECT letter_number, name, size_acres, fish_species
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
- **Most common species**: Brook trout (naturally reproducing in many lakes)
- **High-pressure lakes**: 89 premium destinations
- **Remote options**: 224 low-pressure lakes

## Recent Updates

- ✅ Integrated Norrick physical data (507 lakes enhanced)
- ✅ Fixed missing-dash designations (e.g., "WR35" → "WR-35")  
- ✅ Manual corrections: Amethyst=BR-28, Kermsuh=BR-20, Toomset=BR-25
- ✅ Comprehensive data quality validation
- ✅ **NEW**: Added complete drainage system data (18 drainages)
  - Created `drainages` table with detailed descriptions and map references
  - Generated individual markdown files for each drainage in `/drainages/`
  - Linked existing drainage map images to database records
  - Parsed and structured data from `all_drainages.md`

## Quick Start

**Run complete processing:**
```bash
python3 database.py
```

**Generate fresh lake dump:**
```python
from database import create_database, dump_lake_data
import sqlite3
conn = sqlite3.connect('uinta_lakes.db')
dump_lake_data(conn)
```

**Access drainage information:**
```sql
-- View all drainages
SELECT * FROM drainages ORDER BY name;

-- Get specific drainage details
SELECT info FROM drainages WHERE name = 'Bear River Drainage';
```

## Drainage System Files

All 18 major drainage systems are now documented with individual markdown files:

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
- **Sheep Creek/Carter Creek Drainage** (`sheep-creek-carter-creek-drainage.md`)
- **Smiths Fork Drainage** (`smiths-fork-drainage.md`)
- **Swift Creek Drainage** (`swift-creek-drainage.md`)
- **Uinta River Drainage** (`uinta-river-drainage.md`)
- **Weber River Drainage** (`weber-river-drainage.md`)
- **Whiterocks Drainage** (`whiterocks-drainage.md`)
- **Yellowstone River Drainage** (`yellowstone-river-drainage.md`)

Each file includes detailed access information, fishing characteristics, and formatted lake data tables.

This database provides the most comprehensive fishing resource available for the Uinta Mountains, combining official stocking data with detailed physical lake characteristics and drainage system information for informed trip planning.

# NEXT STEPS

## 1- create "jed_notes" text field, and a "status" field with ENUM of null, "CAUGHT", "NONE", and "OTHERS" in the lakes table

## 2- create a table linked to the lakes table called "fishing_reports" with fields of "date", "success" (with ENUM of "CAUGHT", "NONE", and "OTHERS"), and a "notes" field.

We already have a method in the database.py called "process_stocking_data" that handles the info once it's in utah_dwr_stocking_data.csv so perhaps the workflow should tap into that. Just not sure how to go about preventing duplicate reports, since there isn't a built-in "only show me reports since..." feature.

## 3- create a simple web app for searching/filtering/querying the db and displaying detailed info

I want this to be mobile-first and offline-first, and available as a simple web-app or PWA if that still allows offline access to the SQLite db. I prefer Tailwind CSS, and if we're going to need a JS framework then I prefer Svelte. Above all I want simplicity of architecture and I don't care about optimizing for web performance and such, as it will mostly only be used by me. So if we can e.g. load the whole SQLite file at the beginning and then skip using a JS framework entirely, that's great. But I do care about a great UX, and want fast performance once it's loaded.

The home page should have the filters/controls listed below, and then a list of drainages that are links. When clicked, the drainage page should show pull in the info from the .md file that's in the drainages directory (let's get this info built into the app at build time rather than pulling dynamically from the .md file) and then a list of lakes for that drainage.

### filters 

For this first prototype we'll keep it simple and have three functions: 

1- I'd like a single text field where I can start to enter the name of a lake and there should be an autocomplete/filtered list that appears as I type. 

2- The "OR" option besides typing in the name of a lake, is a set of filters:
- species of trout (any, brook, tiger, cutthroat, rainbow)
- max depth of lake
- "last stocked" which will need to search the related stocking table. If I enter 2022 and there are records for the lake being stocked in 2022 and 2024, then that lake should not appear in the results. If there are no stocking reports for the lake, it should appear in all search results. When the result list appears, it should have in parentheses the years of stocking, abbreviated like: ('22, '20, '18) or (not stocked). *question for Claude: I don't have experience with SQLite-- will it make a noticeable different in performance if we put a "last stocked" field directly on the lakes table, or is the fact that we only have ~600 lake records mean it'll be very fast to do the related table lookup?*

1 & 2 - Upon selecting a lake from either of the above methods, I want to see the stocking reports, followed by related fishing_reports, if any, folowed by whatever other info we have available on the lake such as the drainage it's in, depth, size, jed's notes, junesucker notes

3- When viewing the details of a lake, I want place for me (Jed) to enter/edit some freeform text that goes into jed_notes for the lake, update the status of the lake, and to add a fishing report with a select field for the status. The lake part will be an edit of that record, where the fishing report will always add a new record.

## 4- collect and create mapping info for each lake
Evaluate Google Maps, check feasiability of including core vital info within map marker details panel. See also suggestions in Claude chat for "human in the loop" system to gather coordinates from lakes that I don't have that info for.

## 5- consider scanning and processing tables from my paperback book that include elevation

## 6- sync everything over to Apple Notes, both the one-time info and stocking updates

## 7- create a system for regularly fetching the latest stocking reports and syncing to db without duplicating/overlapping
The URL to hit is https://dwrapps.utah.gov/fishstocking/FishAjax?y=2025&sort=watername&sortorder=ASC&sortspecific={county}&whichSpecific=county with the two counties being "Summit" and "Duchesne." That returns HTML table rows with no table or HTML wrappers, like:

```
<tr class="table1">
  <td class="watername" onclick="newSort('watername','BAKER L BR-45')">BAKER L BR-45</td>
  <td class="county" onclick="newSort('county','Summit')">SUMMIT</td>
  <td class="species" onclick="newSort('species','TIGER TROUT')">TIGER TROUT</td>
  <td class="quantity">360</td>
  <td class="length">2.4</td>
  <td class="stockdate">07/31/2020</td>
</tr>


<tr class="table1">
  <td class="watername" onclick="newSort('watername','BEAR L G-7')">BEAR L G-7</td>
  <td class="county" onclick="newSort('county','Summit')">SUMMIT</td>
  <td class="species" onclick="newSort('species','BROOK TROUT')">BROOK TROUT</td>
  <td class="quantity">2010</td>
  <td class="length">3.49</td>
  <td class="stockdate">07/06/2020</td>
</tr>
```