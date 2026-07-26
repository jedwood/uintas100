#!/usr/bin/env python3
"""
Water-name parsing and regional classification for the Boulder Mountain database.

## The DWR unit-code discovery

Utah DWR's stocking report appends a geographic management-unit code to most
water names in Wayne and Garfield counties -- e.g. "BLIND L NBS" vs
"BLIND L TLM". These are two genuinely different Blind Lakes, 30 km apart, and
without the code they would collapse into one water. The codes are not
documented publicly; they were reverse-engineered here from the data plus
outside confirmation:

    NBS  North Boulder Slope      confirmed: junesucker.com's page for
                                  "GREEN L NBS" is /green-lake-north-boulder-slope/
    GT   Griffin Top              confirmed: visitutah lists "Blue Lake (Griffin Top)",
                                  matching BLUE L GT (distinct from BLUE L NCL)
    NCL  North Creek Lakes        confirmed: Dixie NF describes Barker Reservoir as
                                  "within the North Creek Lakes drainage ... an
                                  extreme southwest extension of Boulder Mountain"
    BT   Boulder Top              Cook/Cub/Dead Horse, all on the plateau rim
    BTN  Boulder Top, north       cluster centre 38.15 N -- north half of the Top
    BTS  Boulder Top, south       cluster centre 38.09 N -- south half of the Top
    NB   North Boulder            small north-side cluster beside NBS
    EBS  East Boulder Slope       Deer Creek / Kings Pasture, east flank
    EB   East Boulder             Little Scout Lake, east flank
    SB   South Boulder            Grass Lake, south flank
    TLM  Thousand Lake Mountain   Deep Creek Lake at 38.43 N -- a SEPARATE mountain
                                  north of Boulder across the Fremont River gorge
    EMW  Escalante Mountains west Antimony/Otter/Pacer at -111.89, the far west
                                  edge of the Aquarius, ~35 km from Boulder Top

Every code is also stored verbatim on the row, so if one of these glosses is
ever corrected the underlying data is unaffected.

## Scope

Three nested scopes are recorded so a question can be asked at any of them:

    boulder_mountain  Boulder Mountain proper, including its North Creek Lakes
                      extension. This is "the Boulders".
    aquarius_plateau  Boulder Mountain + Griffin Top + the Escalante Mountains
                      -- the whole Aquarius Plateau highland.
    (neither)         Thousand Lake Mountain, and the Panguitch/Bryce/Escalante
                      lowland waters that share Garfield and Wayne counties but
                      are nowhere near the Boulders.
"""

import re

# ---------------------------------------------------------------------------
# Unit codes
# ---------------------------------------------------------------------------

UNIT_CODES = {
    'BT':  ('Boulder Top',              'Boulder Mountain'),
    'BTN': ('Boulder Top (north)',      'Boulder Mountain'),
    'BTS': ('Boulder Top (south)',      'Boulder Mountain'),
    'NBS': ('North Boulder Slope',      'Boulder Mountain'),
    'NB':  ('North Boulder',            'Boulder Mountain'),
    'EBS': ('East Boulder Slope',       'Boulder Mountain'),
    'EB':  ('East Boulder',             'Boulder Mountain'),
    'SB':  ('South Boulder',            'Boulder Mountain'),
    'NCL': ('North Creek Lakes',        'Boulder Mountain'),
    'GT':  ('Griffin Top',              'Griffin Top'),
    'EMW': ('Escalante Mountains west', 'Escalante Mountains'),
    'TLM': ('Thousand Lake Mountain',   'Thousand Lake Mountain'),
}

BOULDER_AREAS = {'Boulder Mountain'}
AQUARIUS_AREAS = {'Boulder Mountain', 'Griffin Top', 'Escalante Mountains'}

# Longest first so 'NBS' is tried before 'NB', and 'BTS'/'BTN' before 'BT'.
_CODES_BY_LEN = sorted(UNIT_CODES, key=len, reverse=True)


# ---------------------------------------------------------------------------
# Raw-name cleanup
# ---------------------------------------------------------------------------

# Spelling inconsistencies in DWR's own water names. The Bullberry lakes are
# spelled two different ways in the same report ("BULBERRY L, SOUTH" alongside
# "BULLBERRY L#4(NORTH)"); GNIS and USGS both use "Bullberry".
SPELLING_FIXES = {
    'BULBERRY': 'BULLBERRY',
    'GOVERNMNT': 'GOVERNMENT',
}


def canonical_dwr_name(raw):
    """Collapse whitespace and repair DWR spelling slips, preserving the code.

    DWR emits stray double spaces ('CLEAR L  NBS', 'ROW L  3 GT') that would
    otherwise make one water look like two.
    """
    name = re.sub(r'\s+', ' ', (raw or '')).strip().upper()
    for wrong, right in SPELLING_FIXES.items():
        name = name.replace(wrong, right)
    return name


def split_unit_code(canonical_name):
    """Split a canonical DWR name into (base_name, unit_code_or_None).

    The code is a trailing token, but DWR is inconsistent about the separator:
    'BLIND L NBS' (space), 'PLEASANT CR L-BTS' (hyphen),
    'LOST LAKE(GOVERNMENT)NBS' (no separator at all).
    """
    name = canonical_name
    for code in _CODES_BY_LEN:
        # Space- or hyphen-separated trailing code.
        m = re.search(rf'[\s\-]{re.escape(code)}$', name)
        if m:
            return name[:m.start()].rstrip(' -,'), code
        # Code glued directly onto a closing paren or digit.
        m = re.search(rf'(?<=[)\d]){re.escape(code)}$', name)
        if m:
            return name[:m.start()].rstrip(' -,'), code
    return name, None


# DWR's abbreviations, expanded for display. Applied on word boundaries only.
_ABBREV = [
    (r'\bL\b',    'Lake'),
    (r'\bRES\b',  'Reservoir'),
    (r'\bCR\b',   'Creek'),
    (r'\bFK\b',   'Fork'),
    (r'\bR\b',    'River'),
    (r'\bIMP\b',  'Impoundment'),
    (r'\bLWR\b',  'Lower'),
    (r'\bUPR\b',  'Upper'),
    # The lone-letter compass expansions must not fire on the possessive S of
    # "DWAIN'S POND", which would render as "DWAIN'South Pond".
    (r"(?<!')\bE\b", 'East'),
    (r"(?<!')\bW\b", 'West'),
    (r"(?<!')\bN\b", 'North'),
    (r"(?<!')\bS\b", 'South'),
]

_SMALL_WORDS = {'of', 'the', 'and'}


def display_name(base_name):
    """Turn a DWR base name into a readable one.

    'BOWNS RES, LOWER'      -> 'Lower Bowns Reservoir'
    'LOST LAKE(GOVERNMENT)' -> 'Lost Lake (Government)'
    'ROW LAKE 7-BANANA'     -> 'Row Lake 7 (Banana)'
    'PINE CREEK POND,LWR'   -> 'Lower Pine Creek Pond'
    """
    name = base_name

    # Pull a parenthetical aside out before other processing.
    paren = None
    m = re.search(r'\(([^)]*)\)', name)
    if m:
        paren = m.group(1).strip()
        name = (name[:m.start()] + ' ' + name[m.end():]).strip()

    # 'ROW LAKE 7-BANANA' -- a hyphenated alias, not a code.
    m = re.match(r'^(.*?)[\s]*-\s*([A-Z][A-Z ]+)$', name)
    if m and not paren:
        name, paren = m.group(1).strip(), m.group(2).strip()

    # A trailing ', LOWER' / ', SOUTH' qualifier reads better in front.
    qualifier = None
    m = re.search(r',\s*(LOWER|UPPER|LWR|UPR|NORTH|SOUTH|EAST|WEST)\s*$', name)
    if m:
        qualifier = m.group(1)
        name = name[:m.start()].strip()
    name = name.replace(',', ' ')

    for pattern, repl in _ABBREV:
        name = re.sub(pattern, repl, name)
    if qualifier:
        qualifier = {'LWR': 'Lower', 'UPR': 'Upper'}.get(qualifier, qualifier.title())
        name = f'{qualifier} {name}'

    # '#4' reads better as ' #4'
    name = re.sub(r'(?<=[A-Za-z])#', ' #', name)
    name = re.sub(r'\s+', ' ', name).strip()

    words = []
    for i, w in enumerate(name.split(' ')):
        lw = w.lower()
        # Words containing a digit keep their exact form ('#4', '7'); the
        # possessive is title-cased here and repaired just below.
        words.append(lw if (i and lw in _SMALL_WORDS) else
                     (w if re.search(r'\d', w) else w.title()))
    name = ' '.join(words)
    name = re.sub(r"(\w)'S\b", lambda m: m.group(1) + "'s", name)

    if paren:
        name = f'{name} ({paren.title()})'
    return name


# ---------------------------------------------------------------------------
# Water type
# ---------------------------------------------------------------------------

def water_type(base_name, unit_code=None):
    """Classify a water as lake / reservoir / pond / stream / river / other."""
    n = base_name.upper()
    if re.search(r'\bRIVER\b|\bR\b$', n):
        return 'river'
    # Impoundment/reservoir wins over a creek word in the same name: DWR's
    # "GARKANE IMP, MAIN FK" is a dam on a fork, not the fork itself.
    if re.search(r'\bRES(ERVOIR)?\b|\bIMP(OUNDMENT)?\b', n):
        return 'reservoir'
    if re.search(r'\bCREEK\b|\bCR\b|\bFORK\b|\bFK\b', n) and not re.search(r'\bLAKE\b|\bL\b|\bPOND\b', n):
        return 'stream'
    if re.search(r'\bPOND\b', n):
        return 'pond'
    if re.search(r'\bLAKE\b|\bL\b', n):
        return 'lake'
    # Named basins/meadows that are fished as stillwater: Bobs Hole, Beaver
    # Dams, Dougherty Basin, Kings Pasture, Long Willow Bottoms, Dead Horse.
    if re.search(r'\bHOLE\b|\bDAMS\b|\bBASIN\b|\bPASTURE\b|\bBOTTOMS?\b|\bHOLLOW\b', n):
        return 'lake'
    return 'other'


# ---------------------------------------------------------------------------
# Region classification
# ---------------------------------------------------------------------------

def classify(canonical_name, unit_code, curated=None):
    """Return (area, boulder_mountain, aquarius_plateau, basis).

    A DWR unit code decides the area outright -- it is the fisheries manager's
    own grouping and beats any guess of ours. Waters with no code fall back to
    the curated table in data/water_classification.csv, which records a reason
    for every call.
    """
    if unit_code and unit_code in UNIT_CODES:
        _, area = UNIT_CODES[unit_code]
        return area, area in BOULDER_AREAS, area in AQUARIUS_AREAS, f'dwr-unit-code:{unit_code}'

    if curated:
        area = curated['area']
        return (area,
                area in BOULDER_AREAS,
                area in AQUARIUS_AREAS,
                f"curated:{curated.get('basis', 'manual')}")

    return None, False, False, 'unclassified'


if __name__ == '__main__':
    samples = ['BLIND L NBS', 'CLEAR L  NBS', 'LOST L(GOVERNMNT)NBS', 'ROW L  7-BANANA-GT',
               'PLEASANT CR L-BTS', 'BOWNS RES, LOWER', 'BULBERRY L, SOUTH',
               'BULLBERRY L#4(NORTH)', 'PINE CR POND,LWR BTN', 'GARKANE IMP, MAIN FK',
               'SEVIER R, E FK', "DWAIN'S POND NBS", 'BARKER RES,LOWER NCL', 'FREMONT R']
    for s in samples:
        c = canonical_dwr_name(s)
        base, code = split_unit_code(c)
        print(f'{s!r:26s} -> {display_name(base)!r:34s} code={code or "-":4s} type={water_type(base, code)}')
