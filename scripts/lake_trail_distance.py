#!/usr/bin/env python3
"""Distance from every lake to the nearest OSM route, and to the nearest road.

Needs data/cache/osm_routes.json (run scripts/fetch_osm_routes.py first).
Writes data/cache/lake_trail_distance.json and prints the most off-route
fishable lakes. Read the caveats in docs/less-visited-lakes.md before
trusting a number: OSM coverage in the Uintas is uneven in BOTH directions
(real trails unmapped; cross-country routes tagged as paths)."""
import json, math, os, sqlite3, collections

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "data", "cache")
os.makedirs(CACHE, exist_ok=True)

HERE = CACHE
DB = os.path.join(REPO, "uinta_lakes.db")
LAT0 = 40.75
M_PER_DEG_LAT = 111132.0
M_PER_DEG_LNG = 111320.0 * math.cos(math.radians(LAT0))

TRAIL = {"path", "footway", "bridleway"}
ROUGH_ROAD = {"track", "service"}
DRIVE = {"unclassified", "residential", "tertiary", "secondary", "primary", "motorway"}

def to_xy(lat, lng):
    return (lng * M_PER_DEG_LNG, lat * M_PER_DEG_LAT)

def densify(geom, step=100.0):
    pts = []
    prev = None
    for g in geom:
        p = to_xy(g["lat"], g["lon"])
        if prev is not None:
            dx, dy = p[0]-prev[0], p[1]-prev[1]
            d = math.hypot(dx, dy)
            n = int(d // step)
            for i in range(1, n+1):
                t = i*step/d
                pts.append((prev[0]+dx*t, prev[1]+dy*t))
        pts.append(p)
        prev = p
    return pts

class Grid:
    CELL = 500.0
    def __init__(self):
        self.g = collections.defaultdict(list)
        self.n = 0
    def add(self, pts, meta):
        for x, y in pts:
            self.g[(int(x//self.CELL), int(y//self.CELL))].append((x, y, meta))
            self.n += 1
    def nearest(self, x, y, max_rings=120):
        cx, cy = int(x//self.CELL), int(y//self.CELL)
        best, bestmeta = float("inf"), None
        for r in range(max_rings):
            if best < (r-1)*self.CELL:      # nothing in further rings can beat it
                break
            for i in range(cx-r, cx+r+1):
                for j in range(cy-r, cy+r+1):
                    if r and max(abs(i-cx), abs(j-cy)) != r:
                        continue
                    for px, py, meta in self.g.get((i, j), ()):
                        d = math.hypot(px-x, py-y)
                        if d < best:
                            best, bestmeta = d, meta
        return best, bestmeta

print("loading OSM…")
osm = json.load(open(f"{CACHE}/osm_routes.json"))
grids = {"trail": Grid(), "rough": Grid(), "drive": Grid(), "any": Grid()}
for e in osm["elements"]:
    hw = e.get("tags", {}).get("highway")
    geom = e.get("geometry")
    if not geom or len(geom) < 2:
        continue
    nm = e.get("tags", {}).get("name") or e.get("tags", {}).get("ref") or f"(unnamed {hw})"
    pts = densify(geom)
    meta = (hw, nm)
    grids["any"].add(pts, meta)
    if hw in TRAIL:   grids["trail"].add(pts, meta)
    if hw in ROUGH_ROAD: grids["rough"].add(pts, meta)
    if hw in DRIVE:   grids["drive"].add(pts, meta)
for k, g in grids.items():
    print(f"  {k}: {g.n} densified points")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
lakes = conn.execute("""SELECT id, letter_number, name, drainage, lat, lng, elevation_ft, size_acres,
                               max_depth_ft, fish_species, fishing_pressure, status, no_fish, coord_status
                        FROM lakes WHERE lat IS NOT NULL AND coord_status IN ('confirmed','manual')""").fetchall()
print(f"{len(lakes)} lakes with trusted coords")

rows = []
for L in lakes:
    x, y = to_xy(L["lat"], L["lng"])
    rec = dict(L)
    for k, g in grids.items():
        d, meta = g.nearest(x, y)
        rec[f"d_{k}_m"] = None if d == float("inf") else round(d)
        rec[f"near_{k}"] = meta
    rows.append(rec)

out = f"{CACHE}/lake_trail_distance.json"
json.dump(rows, open(out, "w"), indent=1)
print("wrote", out)

fish = [r for r in rows if not r["no_fish"]]
fish.sort(key=lambda r: -(r["d_trail_m"] or 0))
print("\nTop 40 fishable lakes by distance to nearest OSM foot trail:")
print(f"{'desig':<8}{'name':<22}{'drainage':<22}{'trail_m':>8}{'road_m':>8}{'any_m':>7}  species")
for r in fish[:40]:
    print(f"{r['letter_number']:<8}{(r['name'] or '—')[:21]:<22}{(r['drainage'] or '')[:21]:<22}"
          f"{r['d_trail_m'] or -1:>8}{r['d_drive_m'] or -1:>8}{r['d_any_m'] or -1:>7}  {(r['fish_species'] or '')[:30]}")
