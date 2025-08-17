import sqlite3
import csv
import re
from datetime import datetime

def create_database(db_path="uinta_lakes.db"):
    """Create SQLite database with required schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lakes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter_number TEXT UNIQUE,
            name TEXT,
            drainage TEXT,
            basin TEXT,
            junesucker_notes TEXT,
            coordinates TEXT,
            map_link TEXT
        )
    ''')
    
    # Stocking records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lake_id INTEGER,
            county TEXT,
            species TEXT,
            quantity INTEGER,
            length REAL,
            stock_date DATE,
            source_year INTEGER,
            FOREIGN KEY (lake_id) REFERENCES lakes (id)
        )
    ''')
    
    # Photos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lake_id INTEGER,
            filename TEXT,
            source_url TEXT,
            downloaded_path TEXT,
            FOREIGN KEY (lake_id) REFERENCES lakes (id)
        )
    ''')
    
    # Fishing reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fishing_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lake_id INTEGER,
            date DATE,
            success TEXT CHECK(success IN ("CAUGHT", "NONE", "OTHERS")),
            notes TEXT,
            FOREIGN KEY (lake_id) REFERENCES lakes (id)
        )
    ''')
    
    # Add new columns for Norrick data if they don't exist
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN size_acres REAL')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN max_depth_ft INTEGER')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN fish_species TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN fishing_pressure TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN data_source TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN jed_notes TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE lakes ADD COLUMN status TEXT CHECK(status IN ("CAUGHT", "NONE", "OTHERS"))')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    return conn

def extract_letter_number(water_name):
    """Extract letter-number designation from water name"""
    # Handle spaces around hyphen like "U- 22" or "U -22"
    pattern = r'\b([A-Z]{1,3})\s*-\s*(\d+)\b'
    match = re.search(pattern, water_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Handle missing dash format like "WR35" or "G14" 
    pattern_no_dash = r'\b([A-Z]{1,3})(\d+)\b'
    match = re.search(pattern_no_dash, water_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    return None

def normalize_lake_name(name):
    """Normalize lake names for matching"""
    if not name:
        return ""
    
    normalized = name.upper()
    # Remove letter-number designations for name matching
    normalized = re.sub(r'\b[A-Z]{1,3}\s*-\s*\d+\b', '', normalized)
    # Normalize common abbreviations
    normalized = re.sub(r'\bL\b', 'LAKE', normalized)
    normalized = re.sub(r'\bRES\b', 'RESERVOIR', normalized)
    normalized = re.sub(r'\bR\b', 'RIVER', normalized)
    normalized = re.sub(r'\bCR\b', 'CREEK', normalized)
    normalized = re.sub(r'\bFK\b', 'FORK', normalized)
    normalized = re.sub(r'\bN\b', 'NORTH', normalized)
    normalized = re.sub(r'\bS\b', 'SOUTH', normalized)
    normalized = re.sub(r'\bE\b', 'EAST', normalized)
    normalized = re.sub(r'\bW\b', 'WEST', normalized)
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def find_matching_lake(cursor, water_name):
    """Find matching lake in database"""
    letter_number = extract_letter_number(water_name)
    
    # Primary match: letter-number designation
    if letter_number:
        cursor.execute('SELECT id, name FROM lakes WHERE letter_number = ?', (letter_number,))
        result = cursor.fetchone()
        if result:
            return result[0], "exact", f"Matched on letter-number: {letter_number}"
    
    # Secondary match: word name
    normalized_water = normalize_lake_name(water_name)
    if not normalized_water:
        return None, "none", "Empty normalized name"
    
    cursor.execute('SELECT id, name, letter_number FROM lakes')
    all_lakes = cursor.fetchall()
    
    for lake_id, name, lake_letter_number in all_lakes:
        
        # Try matching against word name only
        normalized_word = normalize_lake_name(name)
        if normalized_water == normalized_word:
            return lake_id, "high", f"Matched on normalized word name: {normalized_water}"
        
        # Try partial matching for common cases
        if normalized_water in normalized_word or normalized_word in normalized_water:
            if len(normalized_water) > 4 and len(normalized_word) > 4:
                return lake_id, "medium", f"Partial match: {normalized_water} <-> {normalized_word}"
    
    return None, "none", "No match found"


def load_lake_data(conn):
    """Load lake data from lake_data.csv into database"""
    cursor = conn.cursor()
    
    with open('data/lake_data.csv', 'r') as f:
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
    print(f"Loaded lake data from lake_data.csv")

def parse_norrick_depth(depth_str):
    """Parse depth field handling 'Unknown' and 'n/a' values"""
    if not depth_str or depth_str.lower() in ['unknown', 'n/a']:
        return None
    try:
        return int(float(depth_str))
    except (ValueError, TypeError):
        return None

def parse_norrick_size(size_str):
    """Parse size field handling 'Unknown' and 'n/a' values"""
    if not size_str or size_str.lower() in ['unknown', 'n/a']:
        return None
    try:
        return float(size_str)
    except (ValueError, TypeError):
        return None

def load_norrick_data(conn):
    """Load Norrick lake data from norrick_lakes.txt into database"""
    cursor = conn.cursor()
    updated_count = 0
    new_count = 0
    unmatched_count = 0
    
    with open('data/norrick_lakes.txt', 'r') as f:
        lines = f.readlines()
        
        # Skip header line
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
                
            lake_name_full = parts[0].strip()
            size_acres = parse_norrick_size(parts[1])
            max_depth_ft = parse_norrick_depth(parts[2])
            fish_species = parts[3].strip()
            fishing_pressure = parts[4].strip()
            
            # Extract letter-number designation from lake name
            letter_number = extract_letter_number(lake_name_full)
            
            if letter_number:
                # Try to find existing lake
                cursor.execute('SELECT id, name FROM lakes WHERE letter_number = ?', (letter_number,))
                result = cursor.fetchone()
                
                if result:
                    # Update existing lake
                    lake_id = result[0]
                    cursor.execute('''
                        UPDATE lakes 
                        SET size_acres = ?, max_depth_ft = ?, fish_species = ?, 
                            fishing_pressure = ?, data_source = ?
                        WHERE id = ?
                    ''', (size_acres, max_depth_ft, fish_species, fishing_pressure, 'Norrick', lake_id))
                    updated_count += 1
                else:
                    # Create new lake entry
                    base_name = lake_name_full.replace(f' {letter_number}', '').replace(f', {letter_number}', '').strip()
                    cursor.execute('''
                        INSERT INTO lakes (letter_number, name, drainage, basin, 
                                         size_acres, max_depth_ft, fish_species, 
                                         fishing_pressure, data_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (letter_number, base_name, 'Unknown', '', size_acres, 
                          max_depth_ft, fish_species, fishing_pressure, 'Norrick'))
                    new_count += 1
            else:
                unmatched_count += 1
                print(f"No letter-number found for: {lake_name_full}")
    
    conn.commit()
    print(f"Norrick data loaded: {updated_count} updated, {new_count} new, {unmatched_count} unmatched")

def dump_lake_data(conn, output_file="output/lake_dump.txt"):
    """Create a text dump of all lakes for review"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT letter_number, name, drainage, size_acres, max_depth_ft, 
               fish_species, fishing_pressure, data_source, jed_notes, status
        FROM lakes 
        ORDER BY drainage, letter_number
    ''')
    
    lakes = cursor.fetchall()
    
    with open(output_file, 'w') as f:
        f.write("UINTA MOUNTAINS LAKE DATABASE DUMP\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Lakes: {len(lakes)}\n\n")
        
        current_drainage = None
        for lake_data in lakes:
            letter_number, name, drainage, size_acres, max_depth_ft, fish_species, fishing_pressure, data_source, jed_notes, status = lake_data
            
            if drainage != current_drainage:
                current_drainage = drainage
                f.write(f"\n--- {drainage} ---\n")
            
            name_display = name if name else "(No name)"
            size_display = f"{size_acres:.1f}ac" if size_acres else "?ac"
            depth_display = f"{max_depth_ft}ft" if max_depth_ft else "?ft"
            pressure_display = fishing_pressure if fishing_pressure else "?"
            source_display = f"[{data_source}]" if data_source else ""
            status_display = f"[{status}]" if status else ""
            jed_notes_display = f" - {jed_notes}" if jed_notes else ""
            
            f.write(f"{letter_number:8} | {name_display:25} | {size_display:8} | {depth_display:6} | {pressure_display:8} | {source_display}{status_display}{jed_notes_display}\n")
    
    print(f"Lake dump written to {output_file}")

def dump_stocking_data(conn, output_file="output/stocking_dump.txt"):
    """Create a text dump of all stocking records for review"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT l.letter_number, l.name, s.species, s.quantity, s.length, 
               s.stock_date, s.source_year, s.county
        FROM stocking_records s
        JOIN lakes l ON s.lake_id = l.id
        ORDER BY l.name, l.letter_number, s.stock_date DESC
    ''')
    
    records = cursor.fetchall()
    
    with open(output_file, 'w') as f:
        f.write("UINTA MOUNTAINS STOCKING RECORDS DUMP\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Stocking Records: {len(records)}\n\n")
        
        current_lake = None
        for record_data in records:
            letter_number, name, species, quantity, length, stock_date, source_year, county = record_data
            
            lake_display = f"{name} {letter_number}" if name else letter_number
            
            if lake_display != current_lake:
                current_lake = lake_display
                f.write(f"\n--- {lake_display} ---\n")
            
            length_display = f"{length}\"" if length else "?"
            
            f.write(f"  {stock_date} | {species:15} | {quantity:6} fish | {length_display:6} | {county}\n")
    
    print(f"Stocking dump written to {output_file}")

def dump_combined_data(conn, output_file="output/combined_dump.txt"):
    """Create a combined dump of lakes with their stocking records"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT l.letter_number, l.name, l.drainage, l.size_acres, l.max_depth_ft, 
               l.fish_species, l.fishing_pressure, l.data_source, l.jed_notes, l.status
        FROM lakes l
        ORDER BY l.drainage, l.name, l.letter_number
    ''')
    
    lakes = cursor.fetchall()
    
    with open(output_file, 'w') as f:
        f.write("UINTA MOUNTAINS COMBINED LAKE & STOCKING DATA\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Lakes: {len(lakes)}\n\n")
        
        current_drainage = None
        for lake_data in lakes:
            letter_number, name, drainage, size_acres, max_depth_ft, fish_species, fishing_pressure, data_source, jed_notes, status = lake_data
            
            if drainage != current_drainage:
                current_drainage = drainage
                f.write(f"\n--- {drainage} ---\n")
            
            name_display = name if name else "(No name)"
            size_display = f"{size_acres:.1f}ac" if size_acres else "?ac"
            depth_display = f"{max_depth_ft}ft" if max_depth_ft else "?ft"
            pressure_display = fishing_pressure if fishing_pressure else "?"
            source_display = f"[{data_source}]" if data_source else ""
            status_display = f"[{status}]" if status else ""
            jed_notes_display = f" - {jed_notes}" if jed_notes else ""
            
            f.write(f"{letter_number:8} | {name_display:25} | {size_display:8} | {depth_display:6} | {pressure_display:8} | {source_display}{status_display}{jed_notes_display}\n")
            
            # Get stocking records for this lake
            cursor.execute('''
                SELECT species, quantity, length, stock_date, county
                FROM stocking_records 
                WHERE lake_id = (SELECT id FROM lakes WHERE letter_number = ?)
                ORDER BY stock_date DESC
            ''', (letter_number,))
            
            stocking_records = cursor.fetchall()
            
            if stocking_records:
                for species, quantity, length, stock_date, county in stocking_records:
                    length_display = f"{length}\"" if length else "?"
                    f.write(f"         └─ {stock_date} | {species:15} | {quantity:6} fish | {length_display:6} | {county}\n")
            else:
                f.write(f"         └─ No stocking records\n")
            
            f.write("\n")
    
    print(f"Combined dump written to {output_file}")

def process_stocking_data(conn):
    """Process stocking data and match with lakes"""
    cursor = conn.cursor()
    unmatched_records = []
    
    with open('data/utah_dwr_stocking_data.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            water_name = row['water_name']
            lake_id, confidence, notes = find_matching_lake(cursor, water_name)
            
            if lake_id:
                # Convert date from MM/DD/YYYY to YYYY-MM-DD for comparison and storage
                try:
                    date_obj = datetime.strptime(row['stock_date'], '%m/%d/%Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                except:
                    formatted_date = row['stock_date']
                
                # Check if record already exists
                cursor.execute('''
                    SELECT COUNT(*) FROM stocking_records 
                    WHERE lake_id = ? AND species = ? AND quantity = ? AND stock_date = ? AND source_year = ?
                ''', (
                    lake_id,
                    row['species'],
                    int(row['quantity']) if row['quantity'].isdigit() else 0,
                    formatted_date,
                    int(row['source_year'])
                ))
                
                if cursor.fetchone()[0] == 0:
                    # Insert stocking record only if it doesn't exist
                    cursor.execute('''
                        INSERT INTO stocking_records (lake_id, county, species, quantity, length, stock_date, source_year)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        lake_id,
                        row['county'],
                        row['species'],
                        int(row['quantity']) if row['quantity'].isdigit() else 0,
                        float(row['length']) if row['length'].replace('.', '').isdigit() else 0.0,
                        formatted_date,
                        int(row['source_year'])
                    ))
                                
                
            else:
                # Check if it has letter-number format
                letter_number = extract_letter_number(water_name)
                if letter_number:
                    # Create new lake record
                    base_name = water_name.replace(f' {letter_number}', '').strip()
                    cursor.execute('''
                        INSERT INTO lakes (letter_number, name, drainage, basin)
                        VALUES (?, ?, ?, ?)
                    ''', (letter_number, base_name, 'Unknown', ''))
                    
                    new_lake_id = cursor.lastrowid
                    
                    # Convert date from MM/DD/YYYY to YYYY-MM-DD
                    try:
                        date_obj = datetime.strptime(row['stock_date'], '%m/%d/%Y')
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    except:
                        formatted_date = row['stock_date']
                    
                    # Insert stocking record
                    cursor.execute('''
                        INSERT INTO stocking_records (lake_id, county, species, quantity, length, stock_date, source_year)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_lake_id,
                        row['county'],
                        row['species'],
                        int(row['quantity']) if row['quantity'].isdigit() else 0,
                        float(row['length']) if row['length'].replace('.', '').isdigit() else 0.0,
                        formatted_date,
                        int(row['source_year'])
                    ))
                                        
                    
                else:
                    # Add to unmatched list
                    unmatched_records.append(row)                    
    
    conn.commit()
    
    # Save unmatched records
    if unmatched_records:
        with open('output/unmatched_stocking.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['water_name', 'county', 'species', 'quantity', 'length', 'stock_date', 'source_year'])
            writer.writeheader()
            writer.writerows(unmatched_records)
    
    print(f"Processed stocking data. {len(unmatched_records)} unmatched records saved to output/unmatched_stocking.csv")

def main():
    """Main execution function"""
    print("Creating database...")
    conn = create_database()    
    
    print("Loading lake data...")
    load_lake_data(conn)
    
    print("Loading Norrick data...")
    load_norrick_data(conn)
    
    print("Processing stocking data...")
    process_stocking_data(conn)
    
    print("Creating enhanced lake dump...")
    dump_lake_data(conn)
    
    print("Creating stocking data dump...")
    dump_stocking_data(conn)
    
    print("Creating combined lake and stocking dump...")
    dump_combined_data(conn)
    
    # Generate summary stats
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM lakes')
    lake_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stocking_records')
    stocking_count = cursor.fetchone()[0]
    
    print(f"\nDatabase processing complete!")
    print(f"Lakes: {lake_count}")
    print(f"Stocking records: {stocking_count}")
    print(f"Lake dump created: lake_dump.txt")
    
    conn.close()

if __name__ == "__main__":
    main()