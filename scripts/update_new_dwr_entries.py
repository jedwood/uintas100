#!/usr/bin/env python3
"""
Script to update database with new DWR lake data from Ashley Creek and Whiterocks drainages.
Only updates lakes that don't already have dwr_notes.
"""

import sqlite3
import re
from dwr_lake_data import DWR_LAKE_ENTRIES

def extract_lake_data_from_text(text):
    """Extract size, depth, elevation, and no_fish status from DWR description text"""
    
    # Clean up text - remove extra whitespace
    text = ' '.join(text.split())
    
    # Extract size in acres
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*acres?', text, re.IGNORECASE)
    size_acres = float(size_match.group(1)) if size_match else None
    
    # Extract elevation - multiple patterns
    elevation_ft = None
    # Pattern 1: "Elevation X feet" or "elevation X,XXX feet"
    elevation_match = re.search(r'elevation\s+(\d+(?:,\d+)?)\s*feet?', text, re.IGNORECASE)
    if elevation_match:
        elevation_str = elevation_match.group(1).replace(',', '')
        elevation_ft = int(elevation_str)
    # Pattern 2: "X feet in elevation" or "X,XXX feet in elevation"  
    elif re.search(r'(\d+(?:,\d+)?)\s*feet?\s*(?:in\s*)?elevation', text, re.IGNORECASE):
        match = re.search(r'(\d+(?:,\d+)?)\s*feet?\s*(?:in\s*)?elevation', text, re.IGNORECASE)
        elevation_str = match.group(1).replace(',', '')
        elevation_ft = int(elevation_str)
    
    # Extract maximum depth
    depth_match = re.search(r'(\d+)\s*feet?\s*maximum\s*depth', text, re.IGNORECASE)
    max_depth_ft = int(depth_match.group(1)) if depth_match else None
    
    # Check if text indicates no fish
    no_fish = 'does not sustain fish life' in text.lower()
    
    return {
        'size_acres': size_acres,
        'elevation_ft': elevation_ft, 
        'max_depth_ft': max_depth_ft,
        'no_fish': no_fish
    }

def get_new_ashley_whiterocks_entries():
    """Get only the new Ashley Creek and Whiterocks entries (the last 74 entries)"""
    # The new entries are all the ones after the original 732
    return DWR_LAKE_ENTRIES[732:]

def update_database_with_new_entries(conn, dry_run=True):
    """Update database with new DWR entries, only for lakes without existing dwr_notes"""
    cursor = conn.cursor()
    
    # Get the new entries
    new_entries = get_new_ashley_whiterocks_entries()
    print(f"Processing {len(new_entries)} new DWR entries...")
    
    updated_count = 0
    not_found_count = 0
    already_has_notes_count = 0
    
    for entry in new_entries:
        designation = entry['designation']
        text = entry['text']
        
        # Check if lake exists in database and doesn't already have dwr_notes
        cursor.execute('''
            SELECT id, size_acres, max_depth_ft, elevation_ft, dwr_notes 
            FROM lakes 
            WHERE letter_number = ?
        ''', (designation,))
        result = cursor.fetchone()
        
        if not result:
            not_found_count += 1
            print(f"Lake {designation} not found in database")
            continue
            
        lake_id, current_size, current_depth, current_elevation, current_dwr_notes = result
        
        # Skip if already has DWR notes
        if current_dwr_notes:
            already_has_notes_count += 1
            print(f"Lake {designation} already has dwr_notes, skipping")
            continue
        
        # Extract data from DWR text
        extracted_data = extract_lake_data_from_text(text)
        
        # Prepare update values
        updates = []
        values = []
        
        # Always add DWR notes and no_fish status
        updates.append('dwr_notes = ?')
        values.append(text)
        updates.append('no_fish = ?')
        values.append(extracted_data['no_fish'])
        
        # Only update fields if we don't have the data currently
        if not current_elevation and extracted_data['elevation_ft']:
            updates.append('elevation_ft = ?')
            values.append(extracted_data['elevation_ft'])
        
        if not current_size and extracted_data['size_acres']:
            updates.append('size_acres = ?')
            values.append(extracted_data['size_acres'])
            
        if not current_depth and extracted_data['max_depth_ft']:
            updates.append('max_depth_ft = ?')
            values.append(extracted_data['max_depth_ft'])
        
        if updates:
            sql = f"UPDATE lakes SET {', '.join(updates)} WHERE id = ?"
            values.append(lake_id)
            
            if dry_run:
                print(f"DRY RUN - Would update {designation}: {extracted_data}")
                print(f"  SQL: {sql}")
                print(f"  Values: {values}")
            else:
                cursor.execute(sql, values)
                print(f"Updated {designation}: {extracted_data}")
            
            updated_count += 1
    
    if not dry_run:
        conn.commit()
    
    print(f"\n=== SUMMARY ===")
    print(f"New entries processed: {len(new_entries)}")
    print(f"Lakes updated: {updated_count}")
    print(f"Lakes not found in DB: {not_found_count}")
    print(f"Lakes already have notes: {already_has_notes_count}")
    
    if dry_run:
        print("\n*** THIS WAS A DRY RUN - No changes made to database ***")
        print("Run with dry_run=False to actually update the database")
    else:
        print("\n*** Database updated successfully ***")

def main(auto_proceed=False):
    """Main function to update database with new DWR entries"""
    print("=== UPDATING DATABASE WITH NEW DWR ENTRIES ===")
    print("Ashley Creek and Whiterocks drainage lakes")
    
    # Connect to database  
    conn = sqlite3.connect('../uinta_lakes.db')
    
    # First do a dry run to show what would be updated
    print("\n--- DRY RUN ---")
    update_database_with_new_entries(conn, dry_run=True)
    
    if auto_proceed:
        print("\n--- PROCEEDING WITH ACTUAL UPDATE ---")
        update_database_with_new_entries(conn, dry_run=False)
    else:
        # Ask for confirmation
        print("\nDo you want to proceed with the actual updates? (y/N): ", end="")
        response = input().strip().lower()
        
        if response == 'y':
            print("\n--- ACTUAL UPDATE ---")
            update_database_with_new_entries(conn, dry_run=False)
        else:
            print("Update cancelled.")
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    import sys
    auto_proceed = len(sys.argv) > 1 and 'auto' in sys.argv[1]
    main(auto_proceed=auto_proceed)