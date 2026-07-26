#!/usr/bin/env python3
"""
Species-name normalization for the Boulder Mountain database.

Mirrors the Uintas project's species_utils, but the Boulders draw from a wider
DWR species pool: the Wayne/Garfield reports include warmwater species (wiper,
crappie, largemouth, bluegill, channel catfish), kokanee, lake trout, brown
trout and non-game fish (sucker, dace) that never appear in the Uinta data.

Display convention (kept identical to the Uintas app so the two databases can be
compared directly): the common trouts are pluralized nicknames -- Brookies,
Rainbows, Cutthroats, Tigers, Browns, Goldens -- while everything else keeps a
readable proper name.
"""

import re

# Exact DWR report codes -> display name. DWR writes these ALL-CAPS and in a
# "noun-first" order for some species (MUSKIE TIGER, GRAYLING ARCTIC,
# BASS LARGEMOUTH, CRAPPIE BLACK, SUNFISH BLUEGILL).
DWR_SPECIES = {
    'BROOK TROUT':     'Brookies',
    'RAINBOW':         'Rainbows',
    'RAINBOW TROUT':   'Rainbows',
    'CUTTHROAT':       'Cutthroats',
    'CUTTHROAT TROUT': 'Cutthroats',
    'TIGER TROUT':     'Tigers',
    'BROWN TROUT':     'Browns',
    'GOLDEN TROUT':    'Goldens',
    'GRAYLING ARCTIC': 'Grayling',
    'ARCTIC GRAYLING': 'Grayling',
    'SPLAKE':          'Splake',
    'LAKE TROUT':      'Lake trout',
    'KOKANEE':         'Kokanee',
    'MUSKIE TIGER':    'Tiger muskie',
    'TIGER MUSKIE':    'Tiger muskie',
    'WIPER':           'Wiper',
    'CHANNEL CATFISH': 'Channel catfish',
    'BASS LARGEMOUTH': 'Largemouth bass',
    'BASS SMALLMOUTH': 'Smallmouth bass',
    'CRAPPIE BLACK':   'Black crappie',
    'CRAPPIE WHITE':   'White crappie',
    'SUNFISH BLUEGILL': 'Bluegill',
    'SUCKER':          'Sucker',
    'DACE':            'Dace',
}

# Values that are not real species. DWR has exactly one of these in the
# Wayne/Garfield archive: a 2006 "ALL TROUT" row at Posey Lake. It is kept in
# the database (the fish were really stocked) but marked so it never pollutes a
# "which species live here" query.
UNKNOWN_SPECIES = {'ALL TROUT', 'TROUT', 'UNKNOWN', ''}

# Species that are stocked sport fish, as opposed to forage/non-game species
# that DWR moves for management reasons. A "this lake only holds X" question
# should not be broken by a single sucker transplant.
NON_GAME = {'Sucker', 'Dace'}

# Coldwater sport fish, for "trout-only" style filtering.
TROUT = {'Brookies', 'Rainbows', 'Cutthroats', 'Tigers', 'Browns', 'Goldens',
         'Splake', 'Lake trout', 'Grayling'}


def standardize_species(raw):
    """Map a raw DWR species string to its display name.

    Returns (display_name, is_known). Unrecognized values fall back to title
    case so nothing is silently dropped, and is_known=False flags them for
    review rather than letting them look like real species.
    """
    if raw is None:
        return None, False
    text = re.sub(r'\s+', ' ', raw).strip()
    key = text.upper()

    if key in UNKNOWN_SPECIES:
        return text.title() if text else None, False
    if key in DWR_SPECIES:
        return DWR_SPECIES[key], True

    # Fall back to the loose pattern matching used for free-text species lists.
    loose = normalize_species_name(text)
    return loose, loose is not None and key not in UNKNOWN_SPECIES


def normalize_species_name(species_text):
    """Normalize a free-text species name (e.g. from a guidebook) to display form."""
    if not species_text:
        return None
    text = species_text.strip().lower()

    # Order matters: "tiger muskie" must be tested before the bare "tiger"
    # trout rule, and "brook" before any generic trout handling.
    if re.search(r'tiger.*musk|musk.*tiger', text):
        return 'Tiger muskie'
    if re.search(r'brook', text):
        return 'Brookies'
    if re.search(r'(arctic\s+)?grayling', text):
        return 'Grayling'
    if re.search(r'rainbow', text):
        return 'Rainbows'
    if re.search(r'tiger', text):
        return 'Tigers'
    if re.search(r'golden', text):
        return 'Goldens'
    if re.search(r'cut.?throat|cuthroat', text):
        return 'Cutthroats'
    if re.search(r'\bbrown\b', text):
        return 'Browns'
    if re.search(r'splake', text):
        return 'Splake'
    if re.search(r'lake\s+trout|mackinaw', text):
        return 'Lake trout'
    if re.search(r'kokanee', text):
        return 'Kokanee'
    if re.search(r'wiper', text):
        return 'Wiper'
    if re.search(r'channel.*catfish|catfish.*channel', text):
        return 'Channel catfish'
    if re.search(r'largemouth', text):
        return 'Largemouth bass'
    if re.search(r'smallmouth', text):
        return 'Smallmouth bass'
    if re.search(r'black.*crappie|crappie.*black', text):
        return 'Black crappie'
    if re.search(r'white.*crappie|crappie.*white', text):
        return 'White crappie'
    if re.search(r'bluegill', text):
        return 'Bluegill'
    if re.search(r'sucker', text):
        return 'Sucker'
    if re.search(r'\bdace\b', text):
        return 'Dace'

    return species_text.title()


if __name__ == '__main__':
    for raw in ['BROOK TROUT', 'GRAYLING ARCTIC', 'MUSKIE TIGER', 'ALL TROUT',
                'BASS LARGEMOUTH', 'SUNFISH BLUEGILL', 'WIPER', 'GOLDEN TROUT']:
        print(f'{raw!r:20s} -> {standardize_species(raw)}')
