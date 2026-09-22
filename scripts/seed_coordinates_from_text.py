#!/usr/bin/env python3
"""Seed unplaced lakes from the bearing+distance references in their DWR write-ups.

The DWR pamphlets almost always locate a lake against a NAMED NEIGHBOUR, with a
real bearing and distance -- "Whitewall Lake ... sits in a large meadow 0.4 miles
west of Island Lake". Where the neighbour is already on the map, that is enough
to compute an actual position rather than a guess, which is far more useful in
the Lake Locator than an empty list.

Everything written here is a SEED, never a placement:
    coord_source = 'dwr-text'
    coord_status = 'seed_unverified'   (or 'seed_suspect', see TIERS)
Only 'confirmed'/'manual' coordinates are exported to the PWA, so nothing from
this script reaches the phone. The Locator's "Needs work" / "Unplaced only"
filters surface these for eyeballing, and saving one there flips it to 'manual'.

    python3 scripts/seed_coordinates_from_text.py            # dry run, prints a table
    python3 scripts/seed_coordinates_from_text.py --apply
    python3 scripts/seed_coordinates_from_text.py --revert   # undo: clear dwr-text seeds

WHY THIS IS DELIBERATELY CONSERVATIVE
-------------------------------------
A first, looser cut of this placed 43 lakes -- and a review showed several were
badly wrong in exactly the way the Castle/Hidden/Crater/Lily coordinate
collisions were wrong:

  * Uinta River's U-25/26/34/46 ("... of the Kidney Lakes") anchored onto Lake
    Fork's X-35 Kidney, ~20 miles away. The Uintas reuse lake names constantly,
    so a cross-drainage name match is never safe.
  * Five Whiterocks lakes ("2 miles west of the West Fork Whiterocks Trailhead")
    anchored onto DF-14 West Kibah, because a fuzzy match on the word "West"
    hit a lake name. The reference was a TRAILHEAD, not a lake at all.
  * Lakes whose real reference was not yet placed silently fell through to a
    weaker phrase later in the same paragraph, so GR-7 Hidden -- whose text says
    "0.7 miles northwest of Lower Anson Lake" -- landed 0.2 miles north of the
    OTHER Hidden Lake.

A seed that is 20 miles out in the wrong drainage is worse than no seed: it
looks plausible on the map and has to be found before it can be fixed. So:

  1. ANCHORS ARE SAME-DRAINAGE ONLY. No global name matching, ever.
  2. THE REFERENCE MUST BE A LAKE. The text has to call it Lake/Lakes/Reservoir/
     Pond right there, or it has to match a lake name in that drainage exactly.
     Anything naming a trail, trailhead, campground, pass, peak, meadow, canal,
     creek, river, fork, basin, mountain, canyon, road or drainage is rejected.
  3. NO FALLING THROUGH. Each lake's candidate references are ranked, and if the
     best one's anchor is not placed yet the lake is DEFERRED to a later pass
     rather than settling for a worse phrase. Passes repeat until nothing new
     lands, so chains resolve (Island -> Bennion, Spirit -> Jesson -> ...).
  4. FUZZY MATCHING IS LAST AND LOCAL -- same drainage, >=0.88 similarity, which
     is what catches the DB's own spelling drift (Quent/Queant,
     Rassmussen/Rasmussen) without inventing matches.

TIERS
-----
  A  distance + bearing + named lake anchor   -> seed_unverified
  B  bearing only ("just north of X"), 0.3 mi -> seed_suspect
  C  proximity only ("near X Lake"), 0.25 mi  -> seed_suspect

  B and C both land a short hop from a confirmed neighbour IN THE SAME DRAINAGE,
  so the basin is right and only the side is a guess -- which is the whole point:
  a pin sitting next to its neighbour is trivial to drag into place in the
  Locator, whereas an empty list gives you nothing to work from. They are marked
  'seed_suspect' so the Locator sorts them to the front of the review queue.

Lakes still unplaced after this are ones with no usable text: the ~30 "does not
sustain fish life ... shown on the map as a landmark" boilerplate rows, and the
~16 with no dwr_notes at all. There is nothing in the record to place them from.
"""

import argparse
import collections
import difflib
import math
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import writer_guard  # noqa: E402

DB = Path(__file__).resolve().parent.parent / "uinta_lakes.db"
SOURCE = "dwr-text"
R_MI = 3958.8

BEARINGS = {
    'north': 0, 'north-northeast': 22.5, 'northeast': 45, 'east-northeast': 67.5,
    'east': 90, 'east-southeast': 112.5, 'southeast': 135, 'south-southeast': 157.5,
    'south': 180, 'south-southwest': 202.5, 'southwest': 225, 'west-southwest': 247.5,
    'west': 270, 'west-northwest': 292.5, 'northwest': 315, 'north-northwest': 337.5,
}
DIR = '|'.join(sorted(BEARINGS, key=len, reverse=True))
FRACTIONS = {'1/8': .125, '1/4': .25, '3/8': .375, '1/2': .5, '5/8': .625,
             '3/4': .75, '7/8': .875, '1/3': 1 / 3, '2/3': 2 / 3}

NUM = r'(\d+ \d/\d|\d/\d|\d+(?:\.\d+)?)'
UNIT = r'(miles?|yards?|yds?|feet|foot|ft)'
# The reference must be named as a water right here -- that single requirement
# is what keeps trailheads, passes and meadows out.
WATER = r"([A-Z][A-Za-z'\.#]*(?:[ ](?:[A-Z][A-Za-z'\.#]*|No\.|#\s?\d+|\d+))*)[ ](Lakes?|Reservoirs?|Ponds?)"
OF = r'(?:of|from|above|below)'
# Tier C nominal offset: far enough to be a distinct pin, near enough to read as
# "beside that one". Bearing is arbitrary (north) and the status says so.
PROXIMITY_HOP = 0.25
PROXIMITY_BEARING = 0.0
APPROX = r'(?:approximately |about |roughly |some |only )?'

P_FULL = re.compile(APPROX + NUM + r' ?' + UNIT + r' (?:due )?(' + DIR + r') ' + OF + r' (?:the )?' + WATER)
P_DIRO = re.compile(r'(?:just|immediately|directly|slightly) (' + DIR + r') ' + OF + r' (?:the )?' + WATER)
# Tier C: a proximity statement with no bearing -- "a few hundred yards upstream
# from Lower Bennion Lake", "near Pole Creek Lake". Placed a short nominal hop
# away; safe only because the anchor is still required to be a lake in the SAME
# drainage, so the seed lands in the right basin even though the side is a guess.
P_PROX = re.compile(
    r'(?:near|adjacent to|next to|beside|between|upstream from|downstream from|'
    r'outlet of|inlet of|distance from|short distance from|above|below) '
    r'(?:the )?' + WATER)

# Words that mean the captured phrase is not a lake even if "Lake" follows.
NOT_A_LAKE = re.compile(
    r'\b(trail|trailhead|head|campground|camp|pass|peak|meadow|meadows|canal|creek|'
    r'river|fork|basin|mountain|canyon|road|highway|drainage|ridge|hollow|park|'
    r'guard|station|ranger|forest|wilderness)\b', re.IGNORECASE)

NAME_NOISE = re.compile(r'\b(lakes?|reservoirs?|ponds?)\b')
MODIFIERS = ('upper', 'lower', 'east', 'west', 'north', 'south', 'big', 'little',
             'middle', 'center')


def destination(lat, lng, bearing, dist_mi):
    b = math.radians(bearing)
    d = dist_mi / R_MI
    p1, l1 = math.radians(lat), math.radians(lng)
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1),
                         math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def parse_distance(num, unit):
    num = num.strip()
    if num in FRACTIONS:
        v = FRACTIONS[num]
    elif ' ' in num and num.split()[-1] in FRACTIONS:
        whole, frac = num.rsplit(' ', 1)
        v = float(whole) + FRACTIONS[frac]
    else:
        try:
            v = float(num)
        except ValueError:
            return None
    u = unit.lower()
    if u.startswith('mi'):
        return v
    if u.startswith(('yard', 'yd')):
        return v / 1760
    if u.startswith(('feet', 'foot', 'ft')):
        return v / 5280
    return None


def normalize(name):
    n = (name or '').lower().replace('.', '').replace(',', '').replace('#', '')
    n = NAME_NOISE.sub('', n)
    return re.sub(r'\s+', ' ', n).strip()


def name_keys(name):
    """Normalized forms, including the DB's inverted word order (Anson Lower)."""
    n = normalize(name)
    keys = {n}
    words = n.split()
    if len(words) > 1 and words[0] in MODIFIERS:
        keys.add(' '.join(words[1:] + [words[0]]))
    if len(words) > 1 and words[-1] in MODIFIERS:
        keys.add(' '.join([words[-1]] + words[:-1]))
    return {k for k in keys if len(k) > 2}


def load(conn):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(
        "SELECT id, letter_number, name, drainage, lat, lng, coord_source, coord_status, "
        "dwr_notes, junesucker_notes FROM lakes")]


def candidates_for(lake):
    """Every usable reference in this lake's text, best tier first."""
    text = ' '.join(filter(None, [lake['dwr_notes'], lake['junesucker_notes']]))
    text = re.sub(r'\s+', ' ', text)
    if not text.strip():
        return []
    found = []
    for m in P_FULL.finditer(text):
        dist = parse_distance(m.group(1), m.group(2))
        if dist is None or dist > 6:
            continue
        phrase, ref = m.group(0), m.group(4)
        if NOT_A_LAKE.search(phrase):
            continue
        found.append(('A', dist, BEARINGS[m.group(3)], ref, phrase))
    for m in P_DIRO.finditer(text):
        phrase, ref = m.group(0), m.group(2)
        if NOT_A_LAKE.search(phrase):
            continue
        found.append(('B', 0.3, BEARINGS[m.group(1)], ref, phrase))
    for m in P_PROX.finditer(text):
        phrase, ref = m.group(0), m.group(1)
        if NOT_A_LAKE.search(phrase):
            continue
        found.append(('C', PROXIMITY_HOP, PROXIMITY_BEARING, ref, phrase))
    found.sort(key=lambda f: (f[0], f[1]))
    return found


def run(conn, apply_changes):
    lakes = load(conn)
    placements = []

    for pass_no in range(1, 12):
        # Index of anchors: same drainage only, and only lakes that have a position.
        index = collections.defaultdict(list)
        for r in lakes:
            if r['lat'] is None or not r['name']:
                continue
            for k in name_keys(r['name']):
                index[(r['drainage'], k)].append(r)

        def anchor_for(ref, drainage, self_ln):
            for k in name_keys(ref):
                for cand in index.get((drainage, k), []):
                    if cand['letter_number'] != self_ln:
                        return cand, 'name'
            pool = [k[1] for k in index if k[0] == drainage]
            for k in name_keys(ref):
                near = difflib.get_close_matches(k, pool, n=1, cutoff=0.88)
                if near:
                    for cand in index[(drainage, near[0])]:
                        if cand['letter_number'] != self_ln:
                            return cand, f'fuzzy~{near[0]}'
            return None, None

        made = 0
        for lake in lakes:
            if lake['lat'] is not None:
                continue
            cands = candidates_for(lake)
            if not cands:
                continue
            # Best candidate only. If its anchor is not placed yet, wait for a
            # later pass rather than accepting a worse reference.
            tier, dist, bearing, ref, phrase = cands[0]
            anchor, how = anchor_for(ref, lake['drainage'], lake['letter_number'])
            if anchor is None:
                continue
            lat, lng = destination(anchor['lat'], anchor['lng'], bearing, dist)
            lake['lat'], lake['lng'] = lat, lng
            lake['coord_source'] = SOURCE
            lake['coord_status'] = 'seed_unverified' if tier == 'A' else 'seed_suspect'
            placements.append({
                'ln': lake['letter_number'], 'name': lake['name'], 'drainage': lake['drainage'],
                'lat': lat, 'lng': lng, 'status': lake['coord_status'], 'tier': tier,
                'pass': pass_no, 'dist': dist, 'bearing': bearing, 'phrase': phrase,
                'anchor': anchor['letter_number'], 'anchor_name': anchor['name'],
                'anchor_status': anchor['coord_status'], 'how': how,
            })
            made += 1
        if not made:
            break

    tiers = collections.Counter(p['tier'] for p in placements)
    print(f"{len(placements)} placeable   tiers={dict(tiers)}   "
          f"still unplaced: {sum(1 for r in lakes if r['lat'] is None)}\n")
    header = (f"{'':4s} {'desig':8s} {'name':15s} {'drainage':14s} {'position':22s} "
              f"{'offset':12s} {'anchor':24s} phrase")
    print(header)
    print('-' * 150)
    for p in sorted(placements, key=lambda x: (x['drainage'], x['ln'])):
        print(f"[{p['tier']}{p['pass']}] {p['ln']:8s} {str(p['name'] or '—')[:15]:15s} "
              f"{p['drainage'].replace(' Drainage', '')[:14]:14s} "
              f"{p['lat']:.5f},{p['lng']:.5f}  {p['dist']:.2f}mi @{p['bearing']:5.1f}°  "
              f"{p['anchor'] + ' ' + str(p['anchor_name'] or ''):24s} {p['phrase'][:44]}")

    if not apply_changes:
        print("\n(dry run — nothing written; pass --apply to write these seeds)")
        return

    cur = conn.cursor()
    for p in placements:
        cur.execute(
            "UPDATE lakes SET lat=?, lng=?, coord_source=?, coord_status=? "
            "WHERE letter_number=? AND lat IS NULL",
            (p['lat'], p['lng'], SOURCE, p['status'], p['ln']))
    conn.commit()
    print(f"\nWrote {len(placements)} seeds (coord_source='{SOURCE}'). "
          "Review them in the Lake Locator; none are exported to the PWA.")


def revert(conn):
    cur = conn.cursor()
    n = cur.execute("SELECT COUNT(*) FROM lakes WHERE coord_source=?", (SOURCE,)).fetchone()[0]
    cur.execute("UPDATE lakes SET lat=NULL, lng=NULL, coord_source=NULL, coord_status=NULL "
                "WHERE coord_source=?", (SOURCE,))
    conn.commit()
    print(f"Cleared {n} '{SOURCE}' seeds back to unplaced.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='write the seeds')
    ap.add_argument('--revert', action='store_true', help='clear all dwr-text seeds')
    args = ap.parse_args()
    if args.apply or args.revert:
        writer_guard.exit_if_readonly()
    conn = sqlite3.connect(DB)
    try:
        revert(conn) if args.revert else run(conn, args.apply)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
