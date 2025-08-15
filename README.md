# Uinta Mountains Fishing Database

A comprehensive SQLite database of fishing locations in the Uinta Mountains, combining official stocking data with detailed physical lake characteristics.

## Database Overview

**File**: `uinta_lakes.db` (SQLite)  
**Total Lakes**: 672  
**Stocking Records**: 2,301  
**Data Sources**: Utah DWR stocking reports + Norrick physical data

## Key Features

- **Letter-number lake designations** (e.g., BR-25, X-64, G-15) for precise identification
- **Physical characteristics**: Lake size (acres), maximum depth (feet)
- **Fish species data**: Detailed species with stocking/natural reproduction status
- **Fishing pressure ratings**: Low/Moderate/High/Very Low for trip planning
- **Stocking history**: Multi-year stocking records with species, quantities, dates

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

## Key Files

- **`database.py`**: Main processing script with all functions
- **`lake_data.csv`**: Original lake designations and drainages (609 lakes)
- **`utah_dwr_stocking_data.csv`**: DWR stocking data (3,361 records)
- **`norrick_lakes.txt`**: Physical lake data (565+ records)
- **`lake_dump.txt`**: Human-readable database export
- **`unmatched_stocking.csv`**: Non-Uintas stocking records (correctly filtered)

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

This database provides the most comprehensive fishing resource available for the Uinta Mountains, combining official stocking data with detailed physical lake characteristics for informed trip planning.