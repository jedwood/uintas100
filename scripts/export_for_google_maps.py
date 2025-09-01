#!/usr/bin/env python3
"""
Export Uinta Lakes Database to CSV for Google My Maps Import

Creates a CSV file suitable for Google My Maps import with:
- Lake names and designations
- Descriptions with species, size, depth, stocking history
- Coordinates from drainage centers
- Layer groupings based on DWR pamphlet organization

Usage: python3 scripts/export_for_google_maps.py
Output: uinta_lakes_for_mapping.csv
"""

import sqlite3
import json
import csv
from datetime import datetime
from pathlib import Path

# DWR Pamphlet Groupings for Layer Organization
DRAINAGE_GROUPS = {
    "Bear River + Blacks Fork": [
        "Bear River Drainage", 
        "Blacks Fork Drainage"
    ],
    "Dry Gulch + Uinta River": [
        "Dry Gulch Drainage", 
        "Uinta River Drainage"
    ],
    "Duchesne River": [
        "Duchesne River Drainage"
    ],
    "Provo + Weber Rivers": [
        "Provo River Drainage", 
        "Weber River Drainage"
    ],
    "Sheep + Carter + Burnt Fork": [
        "Sheep/Carter Creek Drainages", 
        "Burnt Fork Drainage"
    ],
    "Smiths + Henrys + Beaver": [
        "Smiths Fork Drainage", 
        "Henrys Fork Drainage", 
        "Beaver Creek Drainage"
    ],
    "Uintas + Rock Creek": [
        "Rock Creek Drainage",
        # Note: "Uintas" likely refers to a specific drainage, need to map this
    ],
    "Yellowstone + Lake Fork + Swift": [
        "Yellowstone Drainage", 
        "Lake Fork Drainage", 
        "Swift Creek Drainage"
    ],
    "Other Drainages": [
        "Ashley Creek Drainage",
        "White Rocks Drainage"
    ]
}

def load_drainage_centers():
    """Load drainage center coordinates from JSON file."""
    centers_file = Path("drainage_centers.json")
    
    if not centers_file.exists():
        print(f"Error: {centers_file} not found. Please create this file with drainage coordinates.")
        return {}
    
    with open(centers_file, 'r') as f:
        return json.load(f)

def get_drainage_group(drainage_name):
    """Map a drainage to its DWR pamphlet group for layer organization."""
    for group_name, drainages in DRAINAGE_GROUPS.items():
        if drainage_name in drainages:
            return group_name
    return "Other Drainages"

def format_lake_name(letter_number, name):
    """Format the lake name for the map marker."""
    if name and name.strip():
        return f"{letter_number} ({name})"
    return letter_number

def format_description(lake_data):
    """Create a concise description for the map popup following priority order."""
    parts = []
    
    # 1. Species (highest priority) - or NO FISH flag
    if lake_data['no_fish'] == 1:
        parts.append("🚫 NO FISH")
    elif lake_data['fish_species']:
        species_text = lake_data['fish_species'][:50]  # Truncate if very long
        parts.append(f"🐟 {species_text}")
    
    # 2. Size and Depth
    size_depth = []
    if lake_data['size_acres']:
        size_depth.append(f"{lake_data['size_acres']} acres")
    if lake_data['max_depth_ft']:
        size_depth.append(f"{lake_data['max_depth_ft']} ft deep")
    
    if size_depth:
        parts.append(" • ".join(size_depth))
    
    # 3. Recent Stocking History
    if lake_data['last_stocked'] and lake_data['last_species']:
        year = lake_data['last_stocked'][:4]  # Extract year from date
        parts.append(f"Last stocked: {year} {lake_data['last_species']}")
    
    # 4. Key DWR Notes (truncated)
    if lake_data['dwr_notes']:
        # Take first sentence or first 100 characters
        dwr_text = lake_data['dwr_notes'][:100]
        if len(lake_data['dwr_notes']) > 100:
            dwr_text += "..."
        parts.append(f"DWR: {dwr_text}")
    
    return " | ".join(parts)

def export_lakes_csv():
    """Main export function."""
    # Load drainage coordinates
    drainage_centers = load_drainage_centers()
    
    # Connect to database
    db_path = Path("uinta_lakes.db")
    if not db_path.exists():
        print(f"Error: Database {db_path} not found.")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Query for all lakes with optional stocking data
    query = """
    SELECT 
        l.letter_number,
        l.name,
        l.drainage,
        l.size_acres,
        l.max_depth_ft,
        l.fish_species,
        l.no_fish,
        l.dwr_notes,
        MAX(s.stock_date) as last_stocked,
        s.species as last_species
    FROM lakes l
    LEFT JOIN stocking_records s ON l.id = s.lake_id
    GROUP BY l.letter_number
    ORDER BY l.drainage, l.letter_number
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    lakes = cursor.fetchall()
    
    print(f"Found {len(lakes)} lakes to export")
    
    # Prepare CSV output
    output_file = "uinta_lakes_for_mapping.csv"
    missing_coords = []
    exported_count = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Description', 'Latitude', 'Longitude', 'Layer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for lake in lakes:
            lake_dict = dict(lake)  # Convert Row to dict for easier access
            
            # Check if drainage has coordinates available
            drainage_name = lake_dict['drainage']
            if drainage_name not in drainage_centers:
                missing_coords.append(f"{lake_dict['letter_number']} - {drainage_name} (drainage not in centers file)")
                continue
                
            coords = drainage_centers[drainage_name]
            if coords['lat'] is None or coords['lng'] is None:
                missing_coords.append(f"{lake_dict['letter_number']} - {drainage_name} (coordinates null)")
                continue
            
            # Format the CSV row
            row = {
                'Name': format_lake_name(lake_dict['letter_number'], lake_dict['name']),
                'Description': format_description(lake_dict),
                'Latitude': coords['lat'],
                'Longitude': coords['lng'],
                'Layer': get_drainage_group(drainage_name)
            }
            
            writer.writerow(row)
            exported_count += 1
    
    conn.close()
    
    # Report results
    print(f"\n✅ Export complete!")
    print(f"📁 Output file: {output_file}")
    print(f"📊 Exported {exported_count} lakes")
    print(f"⚠️  Skipped {len(missing_coords)} lakes with missing coordinates")
    
    # Show drainage summary for coordinate population
    if missing_coords:
        drainage_summary = {}
        for item in missing_coords:
            drainage = item.split(' - ')[1].split(' (')[0]
            drainage_summary[drainage] = drainage_summary.get(drainage, 0) + 1
        
        print(f"\n📍 Drainages needing coordinates (add to drainage_centers.json):")
        for drainage, count in sorted(drainage_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {drainage}: {count} lakes")
        
        print(f"\n💡 Populate coordinates for any drainage to start mapping those lakes")
    
    # Show layer distribution
    print(f"\nLayer Distribution:")
    layer_counts = {}
    with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            layer = row['Layer']
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
    
    for layer, count in sorted(layer_counts.items()):
        print(f"  {layer}: {count} lakes")
    print(f"\nTotal layers: {len(layer_counts)} (Google My Maps limit: 10)")

if __name__ == "__main__":
    export_lakes_csv()