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

# Generate human-readable dumps
python3 -c "from scripts.database_utils import *; import sqlite3; conn = sqlite3.connect('uinta_lakes.db'); dump_lake_data(conn); dump_stocking_data(conn); dump_combined_data(conn)"
```

### Apple Notes Sync
```bash
# Sync changes from Apple Notes to database
osascript scripts/sync_notes_to_db_jxa.js

# Sync flagged database changes to Apple Notes
osascript scripts/sync_db_to_notes_jxa.js

# Shell wrapper for notes sync
./scripts/sync_notes_to_db.sh
```

### PWA Cache Management
```bash
# PWA cache version is automatically updated by commit hook
# No manual intervention needed - just commit and the hook handles it
git commit -m "your changes"  # Automatically updates cache version
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

### Python Backend (`scripts/`)
- **Data Pipeline**: CSV sources → SQLite via setup/update scripts
- **Species Standardization**: `species_utils.py` normalizes all species names to consistent format (Brookies, Tigers, Cutthroats, etc.)
- **Apple Notes Integration**: Bidirectional sync using JXA scripts for personal fishing notes
- **Lake Identification**: Letter-number system (BR-25, X-64) as primary keys

### Web Frontend (`index.html`)
- **Progressive Web App**: Full offline functionality with service worker
- **SQL.js Integration**: Client-side SQLite queries for real-time filtering
- **Search & Filtering**: By drainage, species, depth, elevation, size, stocking years
- **Lake Details**: Modal views with stocking history, photos, DWR notes

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
- `index.html` - Web app frontend
- `service-worker.js` - PWA offline functionality
- `scripts/setup_database.py` - Initial database creation
- `scripts/species_utils.py` - Species name standardization

### Data Sources (`data/`)
- `lake_data.csv` - Original 609 lake designations
- `utah_dwr_stocking_data.csv` - DWR stocking records
- `norrick_lakes.txt` - Physical lake characteristics
- `dwr_original_pamphlets/` - Historical DWR PDFs

### Generated Files (`logs/`)
- `lake_dump.txt` - Human-readable lake export
- `notes_sync.log` - Apple Notes sync history