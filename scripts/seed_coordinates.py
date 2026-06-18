#!/usr/bin/env python3
"""
Seed lake coordinates from OpenStreetMap (Overpass API).

OSM has many Uinta lakes tagged with either a name ("Butterfly Lake") or the
DWR designation ("BR-33"). This script fetches all named/ref'd water features
in the Uinta bounding box and matches them to our lakes:

  1. Designation match (BR-33 == "BR - 33")  -> highest confidence
  2. Unique name match within the whole range -> good confidence
  3. Ambiguous name -> pick the candidate nearest the drainage's centroid
     (computed from passes 1-2), within a sanity radius

Everything seeded is marked coord_status='seed_unverified' so the Lake Locator
makes you eyeball each one before it counts as done. Lakes that can't be matched
are left for fully manual placement.

Usage:
    python3 scripts/seed_coordinates.py            # use cache if present
    python3 scripts/seed_coordinates.py --refresh  # re-fetch from Overpass
"""

import argparse
import json
import math
import sqlite3
import statistics
from collections import defaultdict

import requests

from coord_utils import (
    DB_PATH,
    UINTA_BBOX,
    ensure_coord_columns,
    looks_like_designation,
    normalize_designation,
    normalize_name,
)
from coord_utils import REPO_ROOT

CACHE_PATH = REPO_ROOT / "data" / "osm_uinta_water.json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAX_NAME_MATCH_KM = 20.0  # reject drainage-disambiguated name matches farther than this
OUTLIER_KM = 30.0  # seeds farther than this from their drainage median are flagged suspect


def fetch_osm(refresh: bool) -> dict:
    if CACHE_PATH.exists() and not refresh:
        print(f"Using cached OSM data ({CACHE_PATH.name}); pass --refresh to re-fetch.")
        return json.loads(CACHE_PATH.read_text())

    s, w, n, e = UINTA_BBOX
    bbox = f"{s},{w},{n},{e}"
    query = f"""
    [out:json][timeout:90];
    (
      way["natural"="water"]["name"]({bbox});
      way["natural"="water"]["ref"]({bbox});
      relation["natural"="water"]["name"]({bbox});
      node["natural"="water"]["name"]({bbox});
      way["water"="lake"]["name"]({bbox});
    );
    out tags center;
    """
    print("Fetching water features from Overpass (this can take ~30-60s)...")
    headers = {"User-Agent": "uinta-lakes-seeder/1.0 (personal fishing map project)"}
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    CACHE_PATH.write_text(json.dumps(data))
    print(f"Cached {len(data.get('elements', []))} OSM elements -> {CACHE_PATH.name}")
    return data


def osm_candidates(data: dict):
    """Yield {lat, lng, names:set, designations:set} for each OSM water feature."""
    for el in data.get("elements", []):
        center = el.get("center") or ({"lat": el.get("lat"), "lon": el.get("lon")})
        lat, lng = center.get("lat"), center.get("lon")
        if lat is None or lng is None:
            continue
        tags = el.get("tags", {})
        names, designations = set(), set()
        for key in ("name", "alt_name", "old_name", "loc_name"):
            val = tags.get(key)
            if not val:
                continue
            # A "name" that is actually a designation (e.g. "BR-33") goes both ways
            if looks_like_designation(val.replace(" ", "")):
                designations.add(normalize_designation(val))
            else:
                names.add(normalize_name(val))
        if tags.get("ref"):
            designations.add(normalize_designation(tags["ref"]))
        yield {"lat": lat, "lng": lng, "names": names, "designations": designations}


def haversine_km(a, b):
    lat1, lng1 = a
    lat2, lng2 = b
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    h = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(h))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="re-fetch from Overpass")
    parser.add_argument("--reseed", action="store_true",
                        help="overwrite existing seeds (skips confirmed/manual lakes)")
    args = parser.parse_args()

    data = fetch_osm(args.refresh)
    cands = list(osm_candidates(data))

    # Build lookup indexes
    by_designation = {}
    by_name = defaultdict(list)
    for c in cands:
        for d in c["designations"]:
            by_designation.setdefault(d, c)  # first wins; designations are ~unique
        for nm in c["names"]:
            by_name[nm].append(c)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_coord_columns(conn)

    lakes = list(conn.execute(
        "SELECT id, letter_number, name, drainage, lat, lng, coord_status FROM lakes"
    ))

    # Which lakes are eligible to (re)seed: never clobber human decisions
    def eligible(lake):
        status = lake["coord_status"]
        if status in ("confirmed", "manual", "cant_find"):
            return False
        if lake["lat"] is not None and not args.reseed:
            return False
        return True

    updates = {}  # lake_id -> (lat, lng, source)

    # Pass 1: designation matches
    for lake in lakes:
        if not eligible(lake):
            continue
        key = normalize_designation(lake["letter_number"])
        # Strip our disambiguating 'b' suffix (X-22b) is preserved by normalize;
        # try exact then without trailing letter
        match = by_designation.get(key)
        if not match and key and key[-1].isalpha():
            match = by_designation.get(key[:-1])
        if match:
            updates[lake["id"]] = (match["lat"], match["lng"], "osm-designation")

    # Pass 2: unique-name matches
    for lake in lakes:
        if lake["id"] in updates or not eligible(lake) or not lake["name"]:
            continue
        key = normalize_name(lake["name"])
        matches = by_name.get(key, [])
        if len(matches) == 1:
            updates[lake["id"]] = (matches[0]["lat"], matches[0]["lng"], "osm-name")

    # Compute drainage centroids from what we've matched so far
    drainage_pts = defaultdict(list)
    seeded_now = {lid: (lat, lng) for lid, (lat, lng, _) in updates.items()}
    lake_by_id = {l["id"]: l for l in lakes}
    for lid, (lat, lng) in seeded_now.items():
        drainage_pts[lake_by_id[lid]["drainage"]].append((lat, lng))
    # also fold in any pre-existing coordinates
    for lake in lakes:
        if lake["lat"] is not None and lake["id"] not in seeded_now:
            drainage_pts[lake["drainage"]].append((lake["lat"], lake["lng"]))
    drainage_centroid = {
        d: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for d, pts in drainage_pts.items() if pts
    }

    # Pass 3: ambiguous names disambiguated by drainage centroid
    for lake in lakes:
        if lake["id"] in updates or not eligible(lake) or not lake["name"]:
            continue
        key = normalize_name(lake["name"])
        matches = by_name.get(key, [])
        if len(matches) < 2:
            continue
        centroid = drainage_centroid.get(lake["drainage"])
        if not centroid:
            continue
        best = min(matches, key=lambda c: haversine_km(centroid, (c["lat"], c["lng"])))
        if haversine_km(centroid, (best["lat"], best["lng"])) <= MAX_NAME_MATCH_KM:
            updates[lake["id"]] = (best["lat"], best["lng"], "osm-name-drainage")

    # Write
    for lid, (lat, lng, source) in updates.items():
        conn.execute(
            "UPDATE lakes SET lat=?, lng=?, coord_source=?, coord_status='seed_unverified' WHERE id=?",
            (lat, lng, source, lid),
        )
    conn.commit()

    # Outlier pass: a single Uinta drainage doesn't span tens of km, so any
    # unverified seed far from its drainage's median location is a likely bad
    # match (name collision, duplicate designation). Flag it 'seed_suspect' so
    # the Locator queues it for review first, but keep the pin as a starting hint.
    seeds_by_drainage = defaultdict(list)
    for row in conn.execute(
        "SELECT id, drainage, lat, lng FROM lakes WHERE lat IS NOT NULL"
    ):
        seeds_by_drainage[row["drainage"]].append(row)
    suspect_count = 0
    for drainage, rows in seeds_by_drainage.items():
        if len(rows) < 4:  # too few points for a meaningful median
            continue
        med = (statistics.median([r["lat"] for r in rows]),
               statistics.median([r["lng"] for r in rows]))
        for row in rows:
            if haversine_km(med, (row["lat"], row["lng"])) > OUTLIER_KM:
                cur = conn.execute(
                    "UPDATE lakes SET coord_status='seed_suspect' "
                    "WHERE id=? AND coord_status='seed_unverified'",
                    (row["id"],),
                )
                suspect_count += cur.rowcount
    conn.commit()

    # Report
    by_source = defaultdict(int)
    for _, _, source in updates.values():
        by_source[source] += 1
    total = len(lakes)
    placed = conn.execute(
        "SELECT COUNT(*) FROM lakes WHERE lat IS NOT NULL"
    ).fetchone()[0]
    conn.close()

    print(f"\nSeeded {len(updates)} lakes this run:")
    for source, count in sorted(by_source.items()):
        print(f"  {source:22} {count}")
    if suspect_count:
        print(f"  (of which {suspect_count} flagged suspect, >30km from drainage median -- review first)")
    print(f"\nCoordinates now present for {placed}/{total} lakes "
          f"({100*placed//total}%). Remaining {total-placed} need manual placement.")
    print("Run the Lake Locator to verify seeds and place the rest:")
    print("  python3 scripts/locator_server.py")


if __name__ == "__main__":
    main()
