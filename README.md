# Uinta Mountains Fishing Database

A comprehensive SQLite database of fishing locations in the Uinta Mountains, combining official stocking data with detailed physical lake characteristics.

## Database Overview

**File**: `uinta_lakes.db` (SQLite)  
**Total Lakes**: 669  
**Total Drainages**: 17  
**Stocking Records**: 2,290  
**Data Sources**: Utah DWR stocking reports + Norrick physical data + Drainage system data

## Key Features

- **Letter-number lake designations** (e.g., BR-25, X-64, G-15) for precise identification
- **Physical characteristics**: Lake size (acres), maximum depth (feet)
- **Fish species data**: Detailed species with stocking/natural reproduction status
- **Fishing pressure ratings**: Low/Moderate/High/Very Low for trip planning
- **Stocking history**: Multi-year stocking records with species, quantities, dates
- **Drainage systems**: Comprehensive information on all 17 major drainage areas with access details and maps

## Database Schema

### `lakes` table
- `letter_number` (unique): Official designation (BR-25, X-64, etc.)
- `name`: Common lake name (may be null for designation-only lakes)  
- `drainage`: Watershed/drainage system
- `size_acres`: Surface area in acres
- `max_depth_ft`: Maximum depth in feet
- `elevation_ft`: Elevation of the lake
- `dwr_notes`: desriptions pulled from old DWR pamphlets
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

- **`setup_database.py`**: One-time database setup (lakes, Norrick data, drainages)
- **`update_stocking.py`**: Stocking data import and updates
- **`database_utils.py`**: Core database utility functions
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
- ✅ **NEW**: Added complete drainage system data (17 drainages)
  - Created `drainages` table with detailed descriptions and map references
  - Generated individual markdown files for each drainage in `/drainages/`
  - Linked existing drainage map images to database records
  - Parsed and structured data from `all_drainages.md`

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

## 1- Continue DWR PDF Lake Data Extraction Project

  I was working on extracting historical lake data from scanned DWR pamphlets to enhance my Uinta Mountains
  fishing database. Here's the current status:

  What's Complete:

  - ✅ Added elevation_ft and dwr_notes columns to lakes table
  - ✅ Built extraction framework in process_dwr_pdf.py
  - ✅ Successfully extracted & integrated many lakes from data/dwr-dry-gulch-and-uinta-trimmed.pdf and data/dwr-bear-blacks-fork-trimmed.pdf
  - ✅ Data parsing works perfectly (extracts acres, elevation, depth from text)
  - ✅ Review system creates output/dwr_extraction_review.txt for quality control
  - ✅ Smart integration only updates missing database fields

  Current Data File:

  dwr_lake_data.py contains 15 manually extracted entries from Page 1. Example format:
  {
      'designation': 'DG-3',
      'name': 'CROW',
      'text': "Crow is an irregular shaped lake located in steep rocky terrain. It is 18 acres, 10,350 feet in 
  elevation, with 26 feet maximum depth..."
  }

  ## Continue with other DWR pamphlets
  1. dwr-duchesne-trimmed.pdf
  2. dwr-provo-weber-trimmed.pdf
  3. dwr-sheep-carter-burnt-fork-trimmed.pdf
  4. dwr-smith-henry-beaver-trimmed.pdf
  5. dwr-uintas-rock-creek-trimmed.pdf
  6. dwr-yellowstone-lake-fork-swift-trimmed.pdf

  Process:

  - Automated PDF text extraction failed (scanned images, not searchable text)
  - Manual extraction works perfectly - I read the PDF and type entries into dwr_lake_data.py
  - Run python3 process_dwr_pdf.py to test extraction
  - Run with integrate=True to add to database

  ## PDF Extraction Workflow (COMPLETED FOR: Duchesne, Provo-Weber)

  ### Step 1: OCR Text Extraction
  Since DWR PDFs contain scanned images (not searchable text), use Tesseract OCR:

  ```bash
  # Convert PDF pages to high-resolution images
  python3 -c "
  import pymupdf
  import os
  pdf_path = 'data/dwr-[DRAINAGE-NAME]-trimmed.pdf'
  doc = pymupdf.open(pdf_path)
  os.makedirs('output/[drainage]_pages', exist_ok=True)
  for page_num in range(len(doc)):
      page = doc.load_page(page_num)
      pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x zoom for better OCR
      pix.save(f'output/[drainage]_pages/page_{page_num + 1}.png')
  doc.close()
  "

  # Run OCR on all pages
  for i in {1..N}; do  # N = number of pages
      echo "=== PAGE $i ===" >> output/[drainage]_ocr_text.txt
      tesseract "output/[drainage]_pages/page_$i.png" stdout >> output/[drainage]_ocr_text.txt 2>/dev/null
  done
  ```

  ### Step 2: Manual Lake Entry Extraction
  Read through the OCR text and extract each lake entry following this pattern:
  - **LAKE NAME, DESIGNATION.** [Description with acres, elevation, depth, access, etc.]

  Add entries to `dwr_lake_data.py` in this format:
  ```python
  {
      'designation': 'A-61',
      'name': 'TRIAL',
      'text': "Trial Reservoir is a popular fishing water located ¾ mile west of the Mirror Lake Highway..."
  },
  ```

  ### Step 3: Integration
  ```bash
  # Test extraction (dry run)
  python3 process_dwr_pdf.py

  # Integrate into database  
  python3 process_dwr_pdf.py integrate=True
  ```

  ### Step 4: Verification
  Query database to verify successful integration:
  ```python
  # Sample check - replace with specific lake names/designations
  cursor.execute("SELECT letter_number, name, size_acres, elevation_ft FROM lakes WHERE name LIKE '%TRIAL%'")
  ```

  ## DWR PDF Processing Status: ✅ COMPLETE!
  - [x] dwr-duchesne-trimmed.pdf (COMPLETED - 47 lakes)
  - [x] dwr-provo-weber-trimmed.pdf (COMPLETED - 66 lakes)
  - [x] dwr-dry-gulch-and-uinta-trimmed.pdf (COMPLETED - 61 lakes)
  - [x] dwr-bear-blacks-fork-trimmed.pdf (COMPLETED - 60 lakes)
  - [x] dwr-sheep-carter-burnt-fork-trimmed.pdf (COMPLETED - 69 lakes)
  - [x] dwr-smith-henry-beaver-trimmed.pdf (COMPLETED - 70 lakes)
  - [x] dwr-uintas-rock-creek-trimmed.pdf (COMPLETED - 64 lakes)
  - [x] dwr-yellowstone-lake-fork-swift-trimmed.pdf (COMPLETED - 90 lakes)

  **Final Status**: 487 total lake entries extracted from all 8 DWR drainage PDFs!
  All entries successfully integrated into database with elevation, depth, and descriptive notes.
  
  This represents complete coverage of all major Uinta Mountains drainage systems from the historical DWR lake survey pamphlets.

## 2- collect and create mapping info for each lake
Evaluate Google Maps, check feasiability of including core vital info within map marker details panel. See also suggestions in Claude chat for "human in the loop" system to gather coordinates from lakes that I don't have that info for.

## 3- sync everything over to Apple Notes, both the one-time info and stocking updates