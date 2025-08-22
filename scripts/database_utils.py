import sqlite3
import csv
import re
from datetime import datetime

def create_database(db_path="../uinta_lakes.db"):
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
    
    # Drainages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drainages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            info TEXT,
            map TEXT
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
    # Special cases for known problematic patterns
    if 'LG103' in water_name:
        return 'G-103'
    if re.search(r'NO1.*WR35', water_name):
        return 'WR-35'
    if re.search(r'NO2.*WR36', water_name):
        return 'WR-36'
    
    # Handle spaces around hyphen like "U- 22", "U -22", "G- 52"
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

def assign_drainage_by_designation(letter_number):
    """Assign drainage based on letter designation prefix"""
    if not letter_number:
        return 'Unknown'
    
    prefix = letter_number.split('-')[0]
    
    drainage_map = {
        'BR': 'Bear River Drainage',
        'G': 'Blacks Fork Drainage',  # but not DG-
        'A': 'Provo River Drainage',
        'P': 'Provo River Drainage', 
        'Z': 'Rock Creek Drainage',
        'W': 'Weber River Drainage',
        'WR': 'Weber River Drainage',
        'U': 'Uinta River Drainage',
        'DF': 'Duchesne Drainage',
        'D': 'Duchesne Drainage',
        'X': 'Yellowstone Drainage',
        'RC': 'Rock Creek Drainage',
        'GR': 'Ashley Creek Drainage'
    }
    
    # Special cases
    if letter_number.startswith('DG-'):
        return 'Dry Gulch Drainage'
    
    # GR- lakes 147 and higher belong to Beaver Creek Drainage
    if letter_number.startswith('GR-'):
        try:
            number = int(letter_number.split('-')[1])
            if number >= 147:
                return 'Beaver Creek Drainage'
        except (ValueError, IndexError):
            pass
    
    return drainage_map.get(prefix, 'Unknown')

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


def stocking_record_exists(cursor, lake_id, species, quantity, stock_date):
    """Check if a specific stocking record already exists."""
    # Convert stock_date string to date object if it's a string
    if isinstance(stock_date, str):
        try:
            stock_date = datetime.strptime(stock_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            try:
                stock_date = datetime.strptime(stock_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return False # Or handle error appropriately

    query = """
        SELECT 1 FROM stocking_records 
        WHERE lake_id = ? 
        AND species = ? 
        AND quantity = ? 
        AND stock_date = ?
    """
    cursor.execute(query, (lake_id, species, quantity, stock_date))
    return cursor.fetchone() is not None

def dump_lake_data(conn, output_file="../output/lake_dump.txt"):
    """Create a text dump of all lakes for review"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT letter_number, name, drainage, size_acres, max_depth_ft, elevation_ft,
               fish_species, fishing_pressure, jed_notes, status, dwr_notes
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
            letter_number, name, drainage, size_acres, max_depth_ft, elevation_ft, fish_species, fishing_pressure, jed_notes, status, dwr_notes = lake_data
            
            if drainage != current_drainage:
                current_drainage = drainage
                f.write(f"\n--- {drainage} ---\n")
            
            name_display = name if name else "(No name)"
            size_display = f"{size_acres:.1f}ac" if size_acres else "?ac"
            depth_display = f"{max_depth_ft}ft" if max_depth_ft else "?ft"
            elevation_display = f"{elevation_ft}ft elev" if elevation_ft else "?ft elev"
            pressure_display = fishing_pressure if fishing_pressure else "?"
            status_display = f"[{status}]" if status else ""
            jed_notes_display = f" - {jed_notes}" if jed_notes else ""
            
            f.write(f"{letter_number:8} | {name_display:25} | {size_display:8} | {depth_display:6} | {elevation_display:10} | {pressure_display:8} | {status_display}{jed_notes_display}\n")
            
            # Add DWR notes on a separate line if they exist
            if dwr_notes:
                f.write(f"         DWR: {dwr_notes}\n")
    
    print(f"Lake dump written to {output_file}")

def dump_stocking_data(conn, output_file="../output/stocking_dump.txt"):
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

def dump_combined_data(conn, output_file="../output/combined_dump.txt"):
    """Create a combined dump of lakes with their stocking records"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT l.letter_number, l.name, l.drainage, l.size_acres, l.max_depth_ft, l.elevation_ft,
               l.fish_species, l.fishing_pressure, l.jed_notes, l.status, l.dwr_notes
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
            letter_number, name, drainage, size_acres, max_depth_ft, elevation_ft, fish_species, fishing_pressure, jed_notes, status, dwr_notes = lake_data
            
            if drainage != current_drainage:
                current_drainage = drainage
                f.write(f"\n--- {drainage} ---\n")
            
            name_display = name if name else "(No name)"
            size_display = f"{size_acres:.1f}ac" if size_acres else "?ac"
            depth_display = f"{max_depth_ft}ft" if max_depth_ft else "?ft"
            elevation_display = f"{elevation_ft}ft elev" if elevation_ft else "?ft elev"
            pressure_display = fishing_pressure if fishing_pressure else "?"
            status_display = f"[{status}]" if status else ""
            jed_notes_display = f" - {jed_notes}" if jed_notes else ""
            
            f.write(f"{letter_number:8} | {name_display:25} | {size_display:8} | {depth_display:6} | {elevation_display:10} | {pressure_display:8} | {status_display}{jed_notes_display}\n")
            
            # Add DWR notes on a separate line if they exist
            if dwr_notes:
                f.write(f"         DWR: {dwr_notes}\n")
            
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
