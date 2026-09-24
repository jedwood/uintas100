#!/usr/bin/env python3
"""Fetch the OSM trail + road network for the Uinta bbox into data/cache/.

Feeds scripts/lake_trail_distance.py. The cache is gitignored (~16 MB) and
regenerable; re-run when you want fresher OSM coverage.
Written for docs/less-visited-lakes.md (2026-09-23)."""
import json, sys, time, urllib.request, urllib.parse, os

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "data", "cache")
os.makedirs(CACHE, exist_ok=True)

OUT = os.path.join(CACHE, "osm_routes.json")
BBOX = "40.50,-111.35,41.05,-109.70"
MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.jp/api/interpreter",
]
QUERY = f"""[out:json][timeout:600];
(
  way["highway"~"^(path|footway|bridleway|track|service|unclassified|residential|tertiary|secondary|primary|trunk|motorway)$"]({BBOX});
);
out geom;
"""

def fetch():
    for url in MIRRORS:
        try:
            print(f"trying {url}", file=sys.stderr, flush=True)
            data = urllib.parse.urlencode({"data": QUERY}).encode()
            req = urllib.request.Request(url, data=data,
                headers={"User-Agent": "uintas-remoteness-research/1.0 (personal project)"})
            with urllib.request.urlopen(req, timeout=900) as r:
                raw = r.read()
            j = json.loads(raw)
            if "elements" in j and len(j["elements"]) > 100:
                print(f"OK {len(j['elements'])} ways from {url}", file=sys.stderr)
                return j
            print(f"  thin response: {len(j.get('elements',[]))}", file=sys.stderr)
        except Exception as e:
            print(f"  fail: {e}", file=sys.stderr)
        time.sleep(5)
    return None

j = fetch()
if j is None:
    sys.exit("all mirrors failed")
with open(OUT, "w") as f:
    json.dump(j, f)
print(f"wrote {OUT}")
