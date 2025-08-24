#!/usr/bin/env python3
"""
Script to extract lake information from DWR PDF pamphlets and integrate into database.
Adds elevation data and DWR notes to existing lakes.
"""

import sqlite3
import re
import pymupdf
import json
from database_utils import create_database

def add_dwr_columns(conn):
    """Add elevation_ft and dwr_notes columns if they don't exist"""
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN elevation_ft INTEGER')
        print("Added elevation_ft column")
    except sqlite3.OperationalError:
        print("elevation_ft column already exists")
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN dwr_notes TEXT')
        print("Added dwr_notes column") 
    except sqlite3.OperationalError:
        print("dwr_notes column already exists")
    
    conn.commit()

def extract_lake_data(text):
    """Extract structured data from a lake description paragraph"""
    
    # Clean up text - remove extra whitespace
    text = ' '.join(text.split())
    
    # Extract size in acres
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*acres?', text, re.IGNORECASE)
    size_acres = float(size_match.group(1)) if size_match else None
    
    # Extract elevation 
    elevation_match = re.search(r'(\d+(?:,\d+)?)\s*feet?\s*in\s*elevation', text, re.IGNORECASE)
    elevation_ft = None
    if elevation_match:
        elevation_str = elevation_match.group(1).replace(',', '')
        elevation_ft = int(elevation_str)
    
    # Extract maximum depth
    depth_match = re.search(r'(\d+)\s*feet?\s*maximum\s*depth', text, re.IGNORECASE)
    max_depth_ft = int(depth_match.group(1)) if depth_match else None
    
    return {
        'size_acres': size_acres,
        'elevation_ft': elevation_ft, 
        'max_depth_ft': max_depth_ft
    }

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    print(f"Extracting text from {pdf_path}")
    
    doc = pymupdf.open(pdf_path)
    full_text = ""
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        full_text += f"\n--- PAGE {page_num + 1} ---\n"
        full_text += text
    
    doc.close()
    return full_text

def parse_lake_entries(text):
    """Parse extracted PDF text to identify individual lake entries"""
    
    entries = []
    
    # Look for lake designation patterns like "DG-10.", "BOLLIE, U-96.", etc.
    # Pattern 1: "DESIGNATION." at start of paragraph
    pattern1 = r'^([A-Z-]+\d*)\.\s*(.+?)(?=^[A-Z-]+\d*\.|$)'
    
    # Pattern 2: "NAME, DESIGNATION." at start of paragraph  
    pattern2 = r'^([A-Z\s]+),\s*([A-Z-]+\d*)\.\s*(.+?)(?=^[A-Z-]+\d*\.|^[A-Z\s]+,\s*[A-Z-]+\d*\.|$)'
    
    # Split text into potential entries (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Try pattern 1 (designation only)
        match1 = re.match(pattern1, paragraph, re.MULTILINE | re.DOTALL)
        if match1:
            designation = match1.group(1)
            description = match1.group(2).strip()
            entries.append({
                'designation': designation,
                'name': None,
                'text': description
            })
            continue
            
        # Try pattern 2 (name, designation) 
        match2 = re.match(pattern2, paragraph, re.MULTILINE | re.DOTALL)
        if match2:
            name = match2.group(1).strip()
            designation = match2.group(2)
            description = match2.group(3).strip()
            entries.append({
                'designation': designation,
                'name': name,
                'text': description
            })
            continue
            
        # If no pattern matched but contains lake-like indicators
        if any(keyword in paragraph.lower() for keyword in ['lake', 'acres', 'elevation', 'depth', 'trout']):
            print(f"Unmatched potential lake entry: {paragraph[:100]}...")
    
    return entries

def save_review_file(entries, filename="../output/dwr_extraction_review.json"):
    """Save extracted entries for manual review"""
    import os
    os.makedirs('output', exist_ok=True)
    
    review_data = {
        'extraction_count': len(entries),
        'entries': entries
    }
    
    with open(filename, 'w') as f:
        json.dump(review_data, f, indent=2)
    
    print(f"Saved {len(entries)} extracted entries to {filename} for review")
    
    # Also create a readable text version
    text_filename = filename.replace('.json', '.txt')
    with open(text_filename, 'w') as f:
        f.write("DWR LAKE DATA EXTRACTION REVIEW\n")
        f.write("=" * 50 + "\n\n")
        
        for i, entry in enumerate(entries, 1):
            f.write(f"{i}. {entry['designation']}")
            if entry['name']:
                f.write(f" ({entry['name']})")
            f.write("\n")
            f.write("-" * 40 + "\n")
            f.write(entry['text'])
            f.write("\n\n")
    
    print(f"Also saved readable version to {text_filename}")

def parse_dwr_text(pdf_path):
    """Extract and parse lake entries from DWR PDF"""
    
    # Extract raw text from PDF
    raw_text = extract_text_from_pdf(pdf_path)
    
    # Save raw text for debugging
    with open('../output/raw_pdf_text.txt', 'w') as f:
        f.write(raw_text)
    
    # Parse into individual lake entries
    entries = parse_lake_entries(raw_text)
    
    # Save for manual review
    save_review_file(entries)
    
    return entries

def map_designation_to_drainage(designation):
    """Map lake designation to drainage based on prefix patterns"""
    prefix = designation.split('-')[0] if '-' in designation else designation[:2]
    
    drainage_map = {
        'BR': 'Bear River Drainage',
        'D': 'Duchesne River Drainage', 
        'G': 'Henrys Fork Drainage',
        'GR': 'Sheep/Carter Creek Drainages',
        'LF': 'Lake Fork Drainage',
        'X': 'Rock Creek Drainage',
        'W': 'Weber River Drainage'
    }
    
    return drainage_map.get(prefix, 'Unknown Drainage')

def integrate_dwr_data(conn, lake_entries):
    """Integrate DWR data into the existing lakes database"""
    cursor = conn.cursor()
    
    updated_count = 0
    created_count = 0
    no_fish_count = 0
    
    for entry in lake_entries:
        designation = entry['designation']
        text = entry['text']
        name = entry.get('name')
        
        # Check if text indicates no fish
        no_fish = 'does not sustain' in text.lower()
        if no_fish:
            no_fish_count += 1
        
        # Check if lake exists in database
        cursor.execute('SELECT id, size_acres, max_depth_ft, elevation_ft FROM lakes WHERE letter_number = ?', 
                      (designation,))
        result = cursor.fetchone()
        
        if not result:
            # Create new lake entry
            drainage = map_designation_to_drainage(designation)
            extracted_data = extract_lake_data(text)
            
            cursor.execute('''
                INSERT INTO lakes (letter_number, name, drainage, basin, size_acres, max_depth_ft, 
                                 elevation_ft, dwr_notes, no_fish)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (designation, name, drainage, '', extracted_data['size_acres'], 
                  extracted_data['max_depth_ft'], extracted_data['elevation_ft'], text, no_fish))
            created_count += 1
            print(f"Created new lake {designation}: {extracted_data}")
            continue
            
        lake_id, current_size, current_depth, current_elevation = result
        
        # Extract data from DWR text
        extracted_data = extract_lake_data(text)
        
        # Prepare update values - only update if we don't have the data
        updates = []
        values = []
        
        # Always add DWR notes and no_fish status
        updates.append('dwr_notes = ?')
        values.append(text)
        updates.append('no_fish = ?')
        values.append(no_fish)
        
        # Only update elevation (we don't have any currently)
        if not current_elevation and extracted_data['elevation_ft']:
            updates.append('elevation_ft = ?')
            values.append(extracted_data['elevation_ft'])
        
        # Only update size if we don't have it
        if not current_size and extracted_data['size_acres']:
            updates.append('size_acres = ?')
            values.append(extracted_data['size_acres'])
            
        # Only update depth if we don't have it  
        if not current_depth and extracted_data['max_depth_ft']:
            updates.append('max_depth_ft = ?')
            values.append(extracted_data['max_depth_ft'])
        
        if updates:
            sql = f"UPDATE lakes SET {', '.join(updates)} WHERE id = ?"
            values.append(lake_id)
            cursor.execute(sql, values)
            updated_count += 1
            print(f"Updated {designation}: {extracted_data}")
    
    conn.commit()
    print(f"\nIntegration complete: {updated_count} updated, {created_count} created, {no_fish_count} marked as no fish")

def main(use_manual_data=True, integrate=False):
    """Process DWR PDF data and integrate into database"""
    print("=== DWR PDF DATA EXTRACTION ===")
    
    # Connect to database  
    conn = sqlite3.connect('../uinta_lakes.db')
    
    # Add new columns
    add_dwr_columns(conn)
    
    if use_manual_data:
        print("Using manually extracted DWR lake data...")
        from dwr_lake_data import get_all_entries
        lake_entries = get_all_entries()
    else:
        print("Using automated PDF extraction...")
        pdf_path = "../data/dwr-dry-gulch-and-uinta-trimmed.pdf"
        lake_entries = parse_dwr_text(pdf_path)
    
    # Save for review
    save_review_file(lake_entries)
    
    print(f"\nExtracted {len(lake_entries)} lake entries")
    print("Review files created in ../output/ directory")
    print("Check ../output/dwr_extraction_review.txt to verify extraction quality")
    
    if integrate:
        print("\nIntegrating into database...")
        integrate_dwr_data(conn, lake_entries)
    else:
        print("\nSkipping database integration (use integrate=True to enable)")
        print("Review the extracted data first, then re-run with integration enabled")
    
    conn.close()
    print("Done!")

if __name__ == "__main__":
    import sys
    
    # Check for integrate parameter
    integrate = len(sys.argv) > 1 and 'integrate=True' in sys.argv[1:]
    
    main(integrate=integrate)