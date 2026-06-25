import sqlite3
import csv
import re
import os
from datetime import datetime

def create_database(db_path=None):
    """Create SQLite database with required schema"""
    if db_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(os.path.dirname(script_dir), "uinta_lakes.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lakes table.
    # Full canonical column set, in the order the live DB has them. The columns
    # after map_link were historically bolted on by ad-hoc ALTERs across several
    # scripts (Norrick physical data, notes/status, coordinate work); they are
    # declared up front here so a fresh build matches the committed DB's schema
    # exactly. CREATE TABLE IF NOT EXISTS is a no-op on an existing DB, so this
    # is non-destructive; the idempotent ALTER block below back-fills any column
    # missing from an older database.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter_number TEXT UNIQUE,
            name TEXT,
            drainage TEXT,
            basin TEXT,
            junesucker_notes TEXT,
            coordinates TEXT,
            map_link TEXT,
            size_acres REAL,
            max_depth_ft INTEGER,
            elevation_ft INTEGER,
            dwr_notes TEXT,
            fish_species TEXT,
            fishing_pressure TEXT,
            jed_notes TEXT,
            status TEXT CHECK(status IN ("CAUGHT", "NONE", "OTHERS")),
            trip_reports TEXT,
            notes_needs_update BOOLEAN DEFAULT FALSE,
            no_fish BOOLEAN DEFAULT 0,
            last_modified TIMESTAMP,
            lat REAL,
            lng REAL,
            coord_source TEXT,
            coord_status TEXT
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
            last_modified TIMESTAMP,
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

    # "Other waters" — creeks, ponds, forks, etc. that DWR stocks but which are
    # NOT one of our lettered lakes. Kept completely separate from `lakes` (and
    # the PWA). `likely_drainage` is a GUESS borrowed from a similarly-named lake
    # (see find_fringe_water); treat these as use-at-your-own-risk.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS other_waters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            water_name TEXT UNIQUE,
            water_type TEXT,
            likely_drainage TEXT,
            inferred_from TEXT,
            county TEXT,
            notes TEXT
        )
    ''')

    # Stocking records for the fringe waters above (mirrors stocking_records).
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS other_stocking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            water_id INTEGER,
            county TEXT,
            species TEXT,
            quantity INTEGER,
            length REAL,
            stock_date DATE,
            source_year INTEGER,
            FOREIGN KEY (water_id) REFERENCES other_waters (id)
        )
    ''')

    # Idempotent safety net: back-fill any lakes column an OLDER database might
    # be missing. No-ops on a fresh build (the full CREATE above already has
    # them) and on the current live DB. Keeps any create_database() entry point
    # converging to the canonical schema.
    lake_column_adds = [
        ('size_acres', 'REAL'),
        ('max_depth_ft', 'INTEGER'),
        ('elevation_ft', 'INTEGER'),
        ('dwr_notes', 'TEXT'),
        ('fish_species', 'TEXT'),
        ('fishing_pressure', 'TEXT'),
        ('jed_notes', 'TEXT'),
        ('status', 'TEXT CHECK(status IN ("CAUGHT", "NONE", "OTHERS"))'),
        ('trip_reports', 'TEXT'),
        ('notes_needs_update', 'BOOLEAN DEFAULT FALSE'),
        ('no_fish', 'BOOLEAN DEFAULT 0'),
        ('last_modified', 'TIMESTAMP'),
    ]
    for col, decl in lake_column_adds:
        try:
            cursor.execute(f'ALTER TABLE lakes ADD COLUMN {col} {decl}')
        except sqlite3.OperationalError:
            pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE stocking_records ADD COLUMN last_modified TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    # Coordinate columns (lat/lng/coord_source/coord_status) live in coord_utils
    # so the seeding/locator tools and the DB schema agree on one definition.
    from coord_utils import ensure_coord_columns
    ensure_coord_columns(conn)

    # Triggers: keep last_modified fresh and flag lakes whose user-facing fields
    # changed so the Apple Notes sync knows to re-export them. Defined here (not
    # only in setup_database) so every entry point gets a complete schema.
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS lakes_insert_trigger
        AFTER INSERT ON lakes
        BEGIN
            UPDATE lakes SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS lakes_update_trigger
        AFTER UPDATE ON lakes
        BEGIN
            UPDATE lakes SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS stocking_records_insert_trigger
        AFTER INSERT ON stocking_records
        BEGIN
            UPDATE stocking_records SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS stocking_records_update_trigger
        AFTER UPDATE ON stocking_records
        BEGIN
            UPDATE stocking_records SET last_modified = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS flag_lake_for_notes_update
        AFTER UPDATE ON lakes
        FOR EACH ROW
        WHEN (
            OLD.jed_notes IS NOT NEW.jed_notes OR
            OLD.status IS NOT NEW.status OR
            OLD.trip_reports IS NOT NEW.trip_reports OR
            OLD.fish_species IS NOT NEW.fish_species OR
            OLD.size_acres IS NOT NEW.size_acres OR
            OLD.max_depth_ft IS NOT NEW.max_depth_ft OR
            OLD.elevation_ft IS NOT NEW.elevation_ft OR
            OLD.fishing_pressure IS NOT NEW.fishing_pressure OR
            OLD.dwr_notes IS NOT NEW.dwr_notes OR
            OLD.junesucker_notes IS NOT NEW.junesucker_notes
        )
        BEGIN
            UPDATE lakes SET notes_needs_update = TRUE WHERE id = NEW.id;
        END
    ''')

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
        'DF': 'Duchesne River Drainage',
        'D': 'Duchesne River Drainage',
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

# Trailing words that just mean "the lake itself" — safe to ignore when deciding
# whether two names refer to the same LAKE (so "Hidden L" == "Hidden").
# Deliberately excludes RESERVOIR/POND/CREEK/etc.: a "Beaver Cr", "Cutthroat
# Pond", or "Echo Reservoir" is a DIFFERENT water from a same-named lake and must
# NOT match by name (it goes to fringe or is ignored). RESERVOIR in particular
# kept mis-crediting lowland reservoirs onto tiny same-named Uinta lakes
# ("Echo Reservoir" -> Z-16 "Echo"). A reservoir is credited to a lake only on an
# exact letter-number designation (handled first in find_matching_lake) — and a
# lake genuinely NAMED "... Reservoir" (e.g. Y-41 "Drift Reservoir") still matches
# a "Drift Reservoir" water, because RESERVOIR is now compared on both sides.
LAKE_SUFFIX_WORDS = {'LAKE'}
# When guessing a fringe water's drainage we strip a broader set to find the root
# (so "Uinta Pond" -> "UINTA" can borrow from the "Uintah" lake).
FRINGE_ROOT_SUFFIX_WORDS = {'LAKE', 'RESERVOIR', 'POND', 'PONDS'}

# Developed / front-country waters that are never Uinta backcountry creeks/ponds.
# Excluded from fringe entirely (e.g. "Rock Cliff St Park" must not borrow a
# high-lake drainage just because it contains the word "Cliff").
FRINGE_EXCLUDE_RE = re.compile(
    r'\b(ST\s*PARK|STATE\s*PARK|\bSP\b|WMA|GOLF|CITY|REGIONAL)\b', re.IGNORECASE
)


def _strip_trailing(normalized, words):
    parts = normalized.split()
    while parts and parts[-1] in words:
        parts.pop()
    return ' '.join(parts)


def classify_water_type(water_name):
    """Rough water-body type from a DWR water name."""
    u = water_name.upper()
    if re.search(r'\bCR\b|CREEK', u):
        return 'creek'
    if 'POND' in u:
        return 'pond'
    if re.search(r'\bRES\b|RESERVOIR', u):
        return 'reservoir'
    if 'SPRING' in u:
        return 'spring'
    if re.search(r'\bFK\b|\bFORK\b|\bR\b|RIVER', u):
        return 'stream'
    return 'other'


def find_matching_lake(cursor, water_name):
    """Find the LAKE a DWR water name refers to — conservatively.

    Matches only when we're confident it's the same water:
      1. an exact letter-number designation extracted from the name, or
      2. names that are equal once trailing LAKE/RESERVOIR words are stripped
         ("Hidden L" == "Hidden").

    The old loose substring matching was removed: it mis-filed creeks and ponds
    onto same-named lakes (e.g. "Beaver Cr" -> BR-10 Beaver). Those waters are
    handled by find_fringe_water() and stored in other_waters instead.
    """
    letter_number = extract_letter_number(water_name)
    if letter_number:
        cursor.execute('SELECT id, name FROM lakes WHERE letter_number = ?', (letter_number,))
        result = cursor.fetchone()
        if result:
            return result[0], "exact", f"Matched on letter-number: {letter_number}"

    target = _strip_trailing(normalize_lake_name(water_name), LAKE_SUFFIX_WORDS)
    if not target:
        return None, "none", "Empty normalized name"

    cursor.execute('SELECT id, name FROM lakes WHERE name IS NOT NULL AND name != ""')
    for lake_id, name in cursor.fetchall():
        if _strip_trailing(normalize_lake_name(name), LAKE_SUFFIX_WORDS) == target:
            return lake_id, "name", f"Matched on lake name: {target}"

    return None, "none", "No match found"


def find_fringe_water(cursor, water_name):
    """For a stocked water that is NOT one of our lakes, guess a likely drainage
    by borrowing it from a similarly-named lake.

    Returns a dict {water_type, likely_drainage, inferred_from} or None. This is
    intentionally loose (name-root substring) and is ONLY used to file creek/pond
    stockings into other_waters as use-at-your-own-risk hints — never to credit a
    stocking to a real lake.
    """
    if FRINGE_EXCLUDE_RE.search(water_name):
        return None

    root = _strip_trailing(normalize_lake_name(water_name), FRINGE_ROOT_SUFFIX_WORDS)
    if not root or len(root) < 4:
        return None
    water_tokens = root.split()

    cursor.execute('SELECT letter_number, name, drainage FROM lakes WHERE name IS NOT NULL AND name != ""')
    rows = cursor.fetchall()

    # Require the lake's FULL name to appear as whole consecutive words in the
    # water name ("Beaver Cr" contains the word "Beaver"), NOT a loose substring.
    # Substring matching wrongly grabbed lowland waters — e.g. "Jordanelle Res"
    # contains the letters of "Jordan" but is a different water entirely.
    best = None  # (name_len, designation, name, drainage)
    for designation, name, drainage in rows:
        lake_tokens = normalize_lake_name(name).split()
        lake_norm = ' '.join(lake_tokens)
        if len(lake_norm) <= 4:  # ignore very short, common names (Bear, Sand, ...)
            continue
        n = len(lake_tokens)
        is_match = any(water_tokens[i:i + n] == lake_tokens
                       for i in range(len(water_tokens) - n + 1))
        if is_match and (best is None or len(lake_norm) > best[0]):
            best = (len(lake_norm), designation, name, drainage)

    if not best:
        return None
    _, designation, name, drainage = best
    return {
        'water_type': classify_water_type(water_name),
        'likely_drainage': drainage,
        'inferred_from': f"{designation} {name}".strip(),
    }


def upsert_other_water(cursor, water_name, info, county=None):
    """Insert (or fetch) an other_waters row for a fringe water. Returns its id."""
    cursor.execute('SELECT id FROM other_waters WHERE water_name = ?', (water_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        '''INSERT INTO other_waters (water_name, water_type, likely_drainage, inferred_from, county)
           VALUES (?, ?, ?, ?, ?)''',
        (water_name, info.get('water_type'), info.get('likely_drainage'),
         info.get('inferred_from'), county),
    )
    return cursor.lastrowid


def other_stocking_exists(cursor, water_id, species, quantity, stock_date):
    cursor.execute(
        '''SELECT 1 FROM other_stocking_records
           WHERE water_id = ? AND species = ? AND quantity = ? AND stock_date = ?''',
        (water_id, species, quantity, stock_date),
    )
    return cursor.fetchone() is not None

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

def assert_lake_columns(conn, columns):
    """Fail loudly (not with a cryptic mid-query OperationalError) if the lakes
    table is missing a column a dump/reader needs — a sign of schema drift that
    create_database() should have prevented."""
    have = {row[1] for row in conn.execute("PRAGMA table_info(lakes)")}
    missing = [c for c in columns if c not in have]
    if missing:
        raise RuntimeError(
            f"lakes table is missing column(s) {missing}; the schema has drifted "
            f"from create_database(). Rebuild/verify with scripts/verify_rebuild.py."
        )

def dump_lake_data(conn, output_file="../logs/lake_dump.txt"):
    """Create a text dump of all lakes for review"""
    cursor = conn.cursor()
    assert_lake_columns(conn, [
        'letter_number', 'name', 'drainage', 'size_acres', 'max_depth_ft',
        'elevation_ft', 'fish_species', 'fishing_pressure', 'jed_notes',
        'status', 'dwr_notes',
    ])

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

def dump_stocking_data(conn, output_file="../logs/stocking_dump.txt"):
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

def dump_combined_data(conn, output_file="../logs/combined_dump.txt"):
    """Create a combined dump of lakes with their stocking records"""
    cursor = conn.cursor()
    assert_lake_columns(conn, [
        'letter_number', 'name', 'drainage', 'size_acres', 'max_depth_ft',
        'elevation_ft', 'fish_species', 'fishing_pressure', 'jed_notes',
        'status', 'dwr_notes',
    ])

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
