#!/usr/bin/env python3
"""
Build boulders.db from the cached DWR stocking pages.

Pipeline:
  1. parse every cached page into raw rows
  2. canonicalize water names, split off the DWR unit code, derive display names
  3. classify each water into an area (unit code first, curated table second)
  4. normalize species names
  5. attach GNIS coordinates, constrained so a name collision cannot place a
     water in the wrong mountain range
  6. load, then recompute the denormalized per-water rollups
  7. print a QA report

Safe to re-run: the database is rebuilt from scratch each time, so the cached
pages plus data/water_classification.csv are the only inputs that matter.
"""

import argparse
import collections
import csv
import math
import re
import sys
from pathlib import Path

from db_utils import DB_PATH, create_database
from species_utils import standardize_species, NON_GAME
from water_utils import (UNIT_CODES, canonical_dwr_name, classify, display_name,
                         split_unit_code, water_type)

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / 'data' / 'raw_stocking'
CLASSIFICATION_CSV = REPO_ROOT / 'data' / 'water_classification.csv'
STOCKING_CSV = REPO_ROOT / 'data' / 'dwr_stocking_data.csv'
# GNIS is shared with the parent Uintas project rather than duplicated -- it is
# a 3.5 MB statewide file and both databases geolocate against the same copy.
GNIS_FILE = REPO_ROOT.parent / 'data' / 'gnis' / 'DomesticNames_UT.txt'

ROW_RE = re.compile(r'<tr class="table1">(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
TAG_RE = re.compile(r'<[^>]+>')

# GNIS official spellings that differ from DWR usage, and DWR names whose GNIS
# feature is named differently. Keyed by our display name, uppercased.
GNIS_ALIASES = {
    'POSEY LAKE': 'POSY LAKE',                    # GNIS drops the second 'e'
    'SOUTH BULLBERRY LAKE': 'BULLBERRY LAKES',
    'BULLBERRY LAKE #4 (NORTH)': 'BULLBERRY LAKES',
    'MOSS LAKE': 'BULLBERRY LAKES',               # guide: Bulberry #2 (Moss)
    'CLEAR LAKE': 'BULLBERRY LAKES',              # guide: Bulberry #3 (Clear)
    'DONKEY POND': 'DONKEY RESERVOIR',
    'LAKE EMILY': 'EMILY LAKE',
    'TULE LAKE': 'TULE LAKES',
    'LONG WILLOW BOTTOMS': 'LONG WILLOW BOTTOM RESERVOIR',
    'ROUND WILLOW BOTTOM': 'ROUND WILLOW BOTTOM RESERVOIR',
    'JOE LAY LAKE': 'JOE LAY RESERVOIR',
    'BEAVER DAMS': 'BEAVER DAM RESERVOIR',
    'MOOSMAN LAKE': 'MOOSMAN RESERVOIR',
    'DEAD HORSE': 'DEAD HORSE LAKE',
    'UPPER BIG HOLLOW': 'BIG HOLLOW',
    'LOWER TWIN LAKE': 'TWIN LAKES',
    'UPPER TWIN LAKE': 'TWIN LAKES',
    'ROW LAKE 3': 'ROW LAKES',
    'ROW LAKE 8': 'ROW LAKES',
    'ROW LAKE 7 (BANANA)': 'ROW LAKES',
}

GNIS_CLASSES = {'Lake', 'Reservoir', 'Stream', 'Swamp', 'Basin', 'Flat', 'Valley'}
MAX_MATCH_MI = 15.0     # a candidate further than this from its unit is rejected


def miles(lat1, lng1, lat2, lng2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def parse_cache():
    """Yield (water_name, county, species, quantity, length, date) from cached pages."""
    rows = []
    pages = sorted(CACHE_DIR.glob('*.html'))
    if not pages:
        sys.exit(f'No cached pages in {CACHE_DIR} -- run scripts/fetch_stocking.py first.')
    for page in pages:
        html = page.read_text(encoding='utf-8', errors='replace')
        for tr in ROW_RE.findall(html):
            cells = CELL_RE.findall(tr)
            if len(cells) != 6:
                continue
            rows.append([TAG_RE.sub('', c).strip() for c in cells])
    return rows, len(pages)


def load_classification():
    curated = {}
    with open(CLASSIFICATION_CSV, encoding='utf-8') as f:
        for row in csv.DictReader(l for l in f if not l.lstrip().startswith('#')):
            if not row.get('dwr_name'):
                continue
            curated[canonical_dwr_name(row['dwr_name'])] = {
                'area': row['area'].strip(),
                'confidence': (row.get('confidence') or '').strip(),
                'basis': (row.get('basis') or '').strip(),
            }
    return curated


def load_gnis():
    index = collections.defaultdict(list)
    if not GNIS_FILE.exists():
        print(f'  (no GNIS file at {GNIS_FILE} -- skipping coordinates)')
        return index
    with open(GNIS_FILE, encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f, delimiter='|'):
            if r.get('feature_class') not in GNIS_CLASSES:
                continue
            try:
                lat, lng = float(r['prim_lat_dec']), float(r['prim_long_dec'])
            except (TypeError, ValueError):
                continue
            if not lat:
                continue
            index[r['feature_name'].upper()].append({
                'name': r['feature_name'], 'county': (r['county_name'] or ''),
                'lat': lat, 'lng': lng, 'cls': r['feature_class'],
            })
    return index


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------

def attach_coordinates(waters, gnis):
    """Two-pass GNIS match.

    Pass 1 accepts only unambiguous hits (one candidate, right county) and uses
    them to compute a centroid per unit code. Pass 2 resolves the rest against
    that centroid, which is what stops 'Heart Lake' from being placed on
    Thousand Lake Mountain and 'Donkey Lake' 30 miles south in Garfield.
    """
    def candidates(w):
        key = GNIS_ALIASES.get(w['name'].upper(), w['name'].upper())
        return gnis.get(key, [])

    for w in waters.values():
        same_county = [c for c in candidates(w) if c['county'].upper() == (w['county'] or '').upper()]
        if len(same_county) == 1:
            c = same_county[0]
            w.update(lat=c['lat'], lng=c['lng'], coord_source='gnis',
                     gnis_name=c['name'] if c['name'].upper() != w['name'].upper() else None)

    centroids = {}
    for code in UNIT_CODES:
        pts = [(w['lat'], w['lng']) for w in waters.values()
               if w['unit_code'] == code and w.get('lat')]
        if pts:
            centroids[code] = (sum(p[0] for p in pts) / len(pts),
                               sum(p[1] for p in pts) / len(pts))

    resolved = rejected = 0
    for w in waters.values():
        if w.get('lat'):
            continue
        cands = candidates(w)
        if not cands:
            continue
        anchor = centroids.get(w['unit_code'])
        if anchor is None:
            # No unit code: fall back to the county, and to the Boulder Top
            # centroid for waters curated onto the mountain.
            anchor = centroids.get('BT') if w['boulder_mountain'] else None
        if anchor is None:
            pool = [c for c in cands if c['county'].upper() == (w['county'] or '').upper()]
            if len(pool) == 1:
                c = pool[0]
                w.update(lat=c['lat'], lng=c['lng'], coord_source='gnis',
                         gnis_name=c['name'] if c['name'].upper() != w['name'].upper() else None)
                resolved += 1
            continue
        best, best_d = None, None
        for c in cands:
            d = miles(anchor[0], anchor[1], c['lat'], c['lng'])
            if best_d is None or d < best_d:
                best, best_d = c, d
        if best_d is not None and best_d <= MAX_MATCH_MI:
            w.update(lat=best['lat'], lng=best['lng'], coord_source='gnis',
                     gnis_name=best['name'] if best['name'].upper() != w['name'].upper() else None)
            resolved += 1
        else:
            rejected += 1
    return resolved, rejected


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    rows, n_pages = parse_cache()
    curated = load_classification()
    print(f'Parsed {len(rows)} stocking rows from {n_pages} cached pages')

    waters, records = {}, []
    unknown_species = collections.Counter()

    for water_name, county, raw_species, qty, length, date in rows:
        canon = canonical_dwr_name(water_name)
        base, code = split_unit_code(canon)
        county = (county or '').title()

        if canon not in waters:
            cur = curated.get(canon)
            area, boulder, aquarius, basis = classify(canon, code, cur)
            unit_name = UNIT_CODES[code][0] if code in UNIT_CODES else None
            waters[canon] = {
                'dwr_name': canon, 'name': display_name(base),
                'unit_code': code, 'unit_name': unit_name,
                'area': area, 'boulder_mountain': int(boulder),
                'aquarius_plateau': int(aquarius),
                'classification_basis': basis,
                'classification_confidence': (
                    'high' if code else (cur or {}).get('confidence') or 'none'),
                'water_type': water_type(base, code), 'county': county,
                'county_suspect': 0, 'lat': None, 'lng': None,
                'coord_source': None, 'gnis_name': None,
                'notes': (cur or {}).get('basis'),
            }
        elif waters[canon]['county'] != county:
            # Pine Creek legitimately spans the Wayne/Garfield line.
            waters[canon]['county'] = f"{waters[canon]['county']}/{county}" \
                if county not in waters[canon]['county'] else waters[canon]['county']

        species, known = standardize_species(raw_species)
        if not known:
            unknown_species[raw_species] += 1

        try:
            quantity = int(qty)
        except (TypeError, ValueError):
            quantity = None
        try:
            length_in = float(length)
        except (TypeError, ValueError):
            length_in = None

        m = re.match(r'(\d{2})/(\d{2})/(\d{4})$', date)
        if not m:
            print(f'  skipping unparseable date {date!r} for {canon}')
            continue
        iso = f'{m.group(3)}-{m.group(1)}-{m.group(2)}'

        flags = []
        if quantity == 0:
            flags.append('zero-quantity')
        if not known:
            flags.append('unknown-species')

        records.append({
            'dwr_name': canon, 'species': species, 'species_raw': raw_species,
            'species_known': int(known), 'quantity': quantity,
            'length_in': length_in, 'stock_date': iso,
            'source_year': int(m.group(3)), 'county': county,
            'qa_flag': ','.join(flags) or None,
        })

    # Gunlock is in Washington county, ~250 miles from Wayne. DWR's row says
    # Wayne; mark the water rather than quietly trusting either value.
    for canon, w in waters.items():
        if 'GUNLOCK' in canon:
            w['county_suspect'] = 1

    # Mark byte-identical rows as a duplicate set instead of dropping them.
    groups = collections.defaultdict(list)
    for i, r in enumerate(records):
        groups[(r['dwr_name'], r['species_raw'], r['quantity'],
                r['length_in'], r['stock_date'])].append(i)
    dup_rows = 0
    for idxs in groups.values():
        for n, i in enumerate(idxs, 1):
            records[i]['dup_index'] = n
            records[i]['dup_total'] = len(idxs)
        if len(idxs) > 1:
            dup_rows += len(idxs) - 1

    resolved, rejected = attach_coordinates(waters, load_gnis())
    placed = sum(1 for w in waters.values() if w.get('lat'))

    # ---- load -------------------------------------------------------------
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = create_database()
    cur = conn.cursor()

    ids = {}
    for canon, w in sorted(waters.items()):
        cur.execute("""
            INSERT INTO waters (dwr_name, name, unit_code, unit_name, area,
                boulder_mountain, aquarius_plateau, classification_basis,
                classification_confidence, water_type, county, county_suspect,
                lat, lng, coord_source, gnis_name, notes)
            VALUES (:dwr_name,:name,:unit_code,:unit_name,:area,:boulder_mountain,
                :aquarius_plateau,:classification_basis,:classification_confidence,
                :water_type,:county,:county_suspect,:lat,:lng,:coord_source,
                :gnis_name,:notes)
        """, w)
        ids[canon] = cur.lastrowid

    for r in records:
        cur.execute("""
            INSERT INTO stocking_records (water_id, species, species_raw,
                species_known, quantity, length_in, stock_date, source_year,
                county, dup_index, dup_total, qa_flag)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (ids[r['dwr_name']], r['species'], r['species_raw'], r['species_known'],
              r['quantity'], r['length_in'], r['stock_date'], r['source_year'],
              r['county'], r['dup_index'], r['dup_total'], r['qa_flag']))

    # ---- rollups ----------------------------------------------------------
    cur.execute("""
        UPDATE waters SET
          first_year = (SELECT MIN(source_year) FROM stocking_records s WHERE s.water_id = waters.id),
          last_year  = (SELECT MAX(source_year) FROM stocking_records s WHERE s.water_id = waters.id),
          stocking_events = (SELECT COUNT(*) FROM stocking_records s
                             WHERE s.water_id = waters.id AND s.dup_index = 1),
          total_stocked   = (SELECT COALESCE(SUM(quantity),0) FROM stocking_records s
                             WHERE s.water_id = waters.id AND s.dup_index = 1)
    """)
    # species_list holds game species only, so a one-off sucker or dace
    # transplant cannot break an "only holds X" question.
    for wid, in cur.execute('SELECT id FROM waters').fetchall():
        sp = [r[0] for r in cur.execute(
            """SELECT DISTINCT species FROM stocking_records
               WHERE water_id = ? AND species_known = 1 ORDER BY species""", (wid,))
            if r[0] not in NON_GAME]
        cur.execute('UPDATE waters SET species_list = ? WHERE id = ?',
                    (', '.join(sp) or None, wid))
    conn.commit()

    # ---- full-fidelity CSV log -------------------------------------------
    with open(STOCKING_CSV, 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['dwr_name', 'water', 'area', 'unit', 'county', 'species',
                     'species_raw', 'quantity', 'length_in', 'stock_date',
                     'source_year', 'dup_index', 'dup_total', 'qa_flag'])
        for row in cur.execute("""
                SELECT w.dwr_name, w.name, w.area, w.unit_name, s.county, s.species,
                       s.species_raw, s.quantity, s.length_in, s.stock_date,
                       s.source_year, s.dup_index, s.dup_total, s.qa_flag
                FROM stocking_records s JOIN waters w ON w.id = s.water_id
                ORDER BY w.name, s.stock_date, s.species"""):
            wr.writerow(row)

    # ---- QA report --------------------------------------------------------
    print(f'\nLoaded {len(waters)} waters and {len(records)} stocking rows -> {DB_PATH}')
    print(f'Coordinates: {placed} waters placed from GNIS '
          f'({resolved} needed the unit-centroid constraint, {rejected} candidates rejected as too far)')

    print('\n--- waters by area ---')
    for area, n, ev in cur.execute("""
            SELECT COALESCE(area,'(none)'), COUNT(*), SUM(stocking_events)
            FROM waters GROUP BY area ORDER BY 3 DESC"""):
        print(f'  {area:24s} {n:3d} waters  {ev:5d} stocking events')

    print('\n--- data quality ---')
    print(f'  duplicate published rows collapsed to dup_index>1 : {dup_rows}')
    for flag, n in cur.execute("""SELECT qa_flag, COUNT(*) FROM stocking_records
                                  WHERE qa_flag IS NOT NULL GROUP BY qa_flag"""):
        print(f'  rows flagged {flag:22s}: {n}')
    if unknown_species:
        print(f'  unrecognized species values: {dict(unknown_species)}')
    for r in cur.execute("""SELECT name, county FROM waters WHERE county_suspect = 1"""):
        print(f'  county looks wrong: {r[0]} (DWR says {r[1]})')
    n_unclass = cur.execute(
        "SELECT COUNT(*) FROM waters WHERE area IS NULL OR area = 'Unclassified'").fetchone()[0]
    if n_unclass:
        print(f'  waters with no established area: {n_unclass}')
        for r in cur.execute("""SELECT name, county, stocking_events FROM waters
                                WHERE area IS NULL OR area = 'Unclassified'
                                ORDER BY stocking_events DESC"""):
            print(f'      {r[0]:26s} {r[1]:9s} {r[2]:3d} events')
    conn.close()


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()
