#!/usr/bin/env python3
"""
One-time database setup script for Uinta Mountains fishing database.
Run this ONCE to create tables and load initial lake data.

After running this, use update_stocking.py for ongoing stocking updates.
"""

import sqlite3
import csv
import re
from database_utils import create_database, extract_letter_number, parse_norrick_depth, parse_norrick_size
from species_utils import normalize_species_list, format_species_display

def load_lake_data(conn):
    """Load lake data from lake_data.csv into database"""
    cursor = conn.cursor()
    
    with open('../data/lake_data.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            drainage = row['drainage']
            lake_name = row['lake_name'].strip() if row['lake_name'] else None
            lake_designation = row['lake_designation'].strip() if row['lake_designation'] else None
            
            # Skip rows without designation (not in Uintas boundary per requirements)
            if not lake_designation:
                continue
                
            try:
                cursor.execute('''
                    INSERT INTO lakes (letter_number, name, drainage, basin)
                    VALUES (?, ?, ?, ?)
                ''', (lake_designation, lake_name, drainage, ''))
            except sqlite3.IntegrityError:
                # Handle duplicate letter_number (shouldn't happen but just in case)
                print(f"Duplicate designation found: {lake_designation}")
    
    conn.commit()
    print(f"Loaded lake data from ../data/lake_data.csv")

def load_norrick_data(conn):
    """Load Norrick lake data from norrick_lakes.txt into database"""
    cursor = conn.cursor()
    updated_count = 0
    new_count = 0
    unmatched_count = 0
    
    with open('../data/norrick_lakes.txt', 'r') as f:
        lines = f.readlines()
        
        # Skip header line
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
                
            lake_name_full = parts[0].strip()
            size_acres = parse_norrick_size(parts[1])
            max_depth_ft = parse_norrick_depth(parts[2])
            raw_fish_species = parts[3].strip()
            fishing_pressure = parts[4].strip()
            
            # Normalize fish species to standardized names
            normalized_species = normalize_species_list(raw_fish_species)
            fish_species = format_species_display(normalized_species) if normalized_species else None
            
            # Extract letter-number designation from lake name
            letter_number = extract_letter_number(lake_name_full)
            
            if letter_number:
                # Check for multiple designations (skip problematic entries)
                all_designations = re.findall(r'\b[A-Z]{1,3}\s*-\s*\d+\b', lake_name_full)
                if len(all_designations) > 1:
                    print(f"Skipping entry with multiple designations: {lake_name_full}")
                    unmatched_count += 1
                    continue
                
                # Try to find existing lake
                cursor.execute('SELECT id, name FROM lakes WHERE letter_number = ?', (letter_number,))
                result = cursor.fetchone()
                
                if result:
                    # Update existing lake
                    lake_id = result[0]
                    cursor.execute('''
                        UPDATE lakes 
                        SET size_acres = ?, max_depth_ft = ?, fish_species = ?, 
                            fishing_pressure = ?
                        WHERE id = ?
                    ''', (size_acres, max_depth_ft, fish_species, fishing_pressure, lake_id))
                    updated_count += 1
                else:
                    # Create new lake entry with better name cleaning
                    base_name = lake_name_full
                    # Remove the letter-number designation from anywhere in the string
                    base_name = re.sub(rf'\b{re.escape(letter_number)}\b,?\s*', '', base_name).strip()
                    # Clean up extra spaces and commas
                    base_name = re.sub(r'\s*,\s*, '', base_name).strip()
                    base_name = re.sub(r'^\s*,\s*', '', base_name).strip()
                    
                    if not base_name or base_name == letter_number:
                        base_name = None  # No meaningful name
                    
                    cursor.execute('''
                        INSERT INTO lakes (letter_number, name, drainage, basin, 
                                         size_acres, max_depth_ft, fish_species, 
                                         fishing_pressure)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (letter_number, base_name, 'Unknown', '', size_acres, 
                          max_depth_ft, fish_species, fishing_pressure))
                    new_count += 1
            else:
                unmatched_count += 1
                print(f"No letter-number found for: {lake_name_full}")
    
    conn.commit()
    print(f"Norrick data loaded: {updated_count} updated, {new_count} new, {unmatched_count} unmatched")

def load_drainage_data(conn):
    """Load drainage data from markdown files"""
    cursor = conn.cursor()
    import os
    
    drainage_dir = 'drainages'
    drainage_files = [f for f in os.listdir(drainage_dir) if f.endswith('.md')]
    
    for file in drainage_files:
        file_path = os.path.join(drainage_dir, file)
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract title from first line (remove # and strip)
        lines = content.split('\n')
        title = lines[0].replace('#', '').strip() if lines else file.replace('.md', '').title()
        
        # Find image filename in content and prepend ../drainages/ path
        image_match = re.search(r'!\\[.*?\\]\(([^)]+\.jpg)\)', content)
        image_file = f"../drainages/{image_match.group(1)}" if image_match else None
        
        # Extract content (everything after title, but stop at image or lakes section)
        info_lines = []
        for line in lines[2:]:
            # Stop at image markdown or lakes section
            if line.startswith('![') or line.startswith('## Lakes') or line.startswith('| Lake name'):
                break
            info_lines.append(line)
        
        info_content = '\n'.join(info_lines).strip()
        
        try:
            cursor.execute('''
                INSERT INTO drainages (name, info, map)
                VALUES (?, ?, ?)
            ''', (title, info_content, image_file))
        except sqlite3.IntegrityError:
            # Update existing drainage with real content
            cursor.execute('''
                UPDATE drainages 
                SET info = ?, map = ?
                WHERE name = ?
            ''', (info_content, image_file, title))
    
    conn.commit()
    print(f"Loaded drainage data from {len(drainage_files)} markdown files")

def main():
    """One-time database setup"""
    print("=== UINTA LAKES DATABASE SETUP ===")
    print("This script creates tables and loads initial lake data.")
    print("Run this ONCE, then use update_stocking.py for ongoing updates.\n")
    
    print("Creating database and tables...")
    conn = create_database()
    cursor = conn.cursor()

    # Add last_modified columns and triggers
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN last_modified TIMESTAMP')
    except sqlite3.OperationalError:
        pass # Column already exists
    
    try:
        cursor.execute('ALTER TABLE stocking_records ADD COLUMN last_modified TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS lakes_insert_trigger
        AFTER INSERT ON lakes
        BEGIN
            UPDATE lakes SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS lakes_update_trigger
        AFTER UPDATE ON lakes
        BEGIN
            UPDATE lakes SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS stocking_records_insert_trigger
        AFTER INSERT ON stocking_records
        BEGIN
            UPDATE stocking_records SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS stocking_records_update_trigger
        AFTER UPDATE ON stocking_records
        BEGIN
            UPDATE stocking_records SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    ''')
    
    print("Loading lake data from CSV...")
    load_lake_data(conn)
    
    print("Loading Norrick data...")
    load_norrick_data(conn)
    
    print("Loading drainage data...")
    load_drainage_data(conn)
    
    # Generate summary stats
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM lakes')
    lake_count = cursor.fetchone()[0]
    
    print(f"\nSetup complete!")
    print(f"Lakes: {lake_count}")
    print(f"Next: Use update_stocking.py to add stocking data")
    
    conn.close()

if __name__ == "__main__":
    main()
