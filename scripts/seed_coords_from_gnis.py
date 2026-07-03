#!/usr/bin/env python3
"""
Seed lake coordinates from USGS GNIS (Domestic Names) for named lakes that have
no coordinates at all.

GNIS points sit ON the named feature (validated vs 117 confirmed lakes: median
error 0.01 mi), so — unlike the PLSS section centroids — these are written as
ordinary seeds for the Locator's existing verify queue:

    coord_source = 'gnis'
    coord_status = 'seed_unverified'

The catch is name collisions: an unconstrained name match can land 40+ miles
away on a same-named lake in another drainage ("Mud", "Marsh", "Twin"...). So a
GNIS candidate is only accepted if it lies within MAX_DIST_MI of the NEAREST
already-placed lake in the same drainage (nearest-lake beats a drainage
centroid, which mis-rejects lakes on a big drainage's edge); among several
passing candidates the nearest wins. Drainages with no placed lakes are skipped.

Only fills lakes with NO coordinate (never touches confirmed/manual/seeded/
cant_find rows). Obeys the single-writer guard.

The GNIS state files are cached in data/gnis/ (downloaded on first run).

Usage:
    python3 scripts/seed_coords_from_gnis.py --dry-run
    python3 scripts/seed_coords_from_gnis.py
"""

import argparse
import csv
import io
import math
import re
import sqlite3
import sys
import urllib.request
import zipfile

from coord_utils import DB_PATH, REPO_ROOT, ensure_coord_columns
from writer_guard import is_readonly_mirror

GNIS_DIR = REPO_ROOT / "data" / "gnis"
GNIS_URL = ("https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/"
            "DomesticNames/DomesticNames_{st}_Text.zip")
STATES = ["UT", "WY"]  # north-slope drainages nose into Wyoming
# Uintas bounding box and the counties our lakes can fall in
BBOX = (40.35, 41.20, -111.25, -109.45)
COUNTIES = {"Summit", "Duchesne", "Uintah", "Daggett", "Wasatch",  # UT
            "Uinta", "Sweetwater"}                                  # WY
CLASSES = {"Lake", "Reservoir"}
MAX_DIST_MI = 4.0  # candidate must be this close to some placed lake in its drainage


def norm(name):
    n = name.strip().upper()
    n = re.sub(r"\s+(LAKES?|RESERVOIR)$", "", n)
    return re.sub(r"\s+", "", n)


def miles(la1, lo1, la2, lo2):
    R = 3958.8
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_gnis():
    """{normalized name: [(lat, lng, official name, county), ...]} in the Uintas bbox."""
    GNIS_DIR.mkdir(exist_ok=True)
    feats = {}
    for st in STATES:
        txt_path = GNIS_DIR / f"DomesticNames_{st}.txt"
        if not txt_path.exists():
            url = GNIS_URL.format(st=st)
            print(f"  downloading {url} ...")
            with urllib.request.urlopen(url, timeout=120) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
            member = next(m for m in z.namelist() if m.endswith(f"DomesticNames_{st}.txt"))
            txt_path.write_bytes(z.read(member))
        with open(txt_path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter="|"):
                if row["feature_class"] not in CLASSES or row["county_name"] not in COUNTIES:
                    continue
                lat, lng = float(row["prim_lat_dec"]), float(row["prim_long_dec"])
                if not (BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lng <= BBOX[3]):
                    continue
                feats.setdefault(norm(row["feature_name"]), []).append(
                    (lat, lng, row["feature_name"], row["county_name"]))
    return feats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-dist", type=float, default=MAX_DIST_MI)
    args = ap.parse_args()

    if is_readonly_mirror():
        print("[writer-guard] .db-readonly present — this clone is a read-only mirror. Aborting.")
        return 1

    gnis = load_gnis()
    print(f"GNIS Lake/Reservoir features in the Uintas bbox: "
          f"{sum(len(v) for v in gnis.values())} ({len(gnis)} unique names)")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_coord_columns(conn)

    # Per-drainage anchor points: every lake in the drainage that has any coordinate.
    anchors = {}
    for r in conn.execute("SELECT drainage, lat, lng FROM lakes WHERE lat IS NOT NULL"):
        anchors.setdefault(r["drainage"], []).append((r["lat"], r["lng"]))

    targets = conn.execute(
        """SELECT letter_number, name, drainage FROM lakes
           WHERE name IS NOT NULL AND name != '' AND lat IS NULL
             AND (coord_status IS NULL OR coord_status NOT IN ('cant_find'))
           ORDER BY drainage, letter_number""").fetchall()

    placed, skipped = 0, []
    for r in targets:
        cands = gnis.get(norm(r["name"]), [])
        anchor = anchors.get(r["drainage"])
        if not cands:
            continue  # silent: most informal names simply aren't in GNIS
        if not anchor:
            skipped.append((r["letter_number"], "drainage has no placed lakes to anchor on"))
            continue
        scored = sorted((min(miles(a, o, c[0], c[1]) for a, o in anchor), c) for c in cands)
        d, best = scored[0]
        if d > args.max_dist:
            skipped.append((r["letter_number"],
                            f"nearest '{best[2]}' is {d:.1f} mi from any placed lake in the drainage "
                            f"(> {args.max_dist})"))
            continue
        note = f" ({len(cands)} candidates, nearest won)" if len(cands) > 1 else ""
        print(f"  {r['letter_number']:8s} {r['name']:24s} {r['drainage']:28s} "
              f"-> ({best[0]:.5f},{best[1]:.5f}) '{best[2]}' {best[3]} {d:.1f}mi{note}")
        if not args.dry_run:
            conn.execute("UPDATE lakes SET lat=?, lng=?, coord_source='gnis', "
                         "coord_status='seed_unverified' WHERE letter_number=?",
                         (best[0], best[1], r["letter_number"]))
        placed += 1

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f"\n{'[dry-run] would place' if args.dry_run else 'Placed'} {placed} GNIS seeds; "
          f"{len(skipped)} rejected by the proximity guard.")
    for ln, why in skipped:
        print(f"  REJECTED {ln}: {why}")
    if not args.dry_run and placed:
        print("\nNext: they join the normal 'Seeds to verify' queue in the Locator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
