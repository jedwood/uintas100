#!/usr/bin/env python3
"""
Seed coarse lake coordinates from the Forest Service "Lakes of the
Uinta-Wasatch-Cache National Forest" data sheet (data/master-summary-forest-service.pdf).

That sheet lists each lake's Public Land Survey System location as a
Township/Range/Section (the "T,R,S" column, e.g. `1S,10E,12`) against a
principal meridian (`SL` = Salt Lake, `US` = Uintah Special). We convert each
T,R,S to the centroid of that 1-square-mile section via the BLM National PLSS
(CadNSDI) service, and write it as a NON-authoritative estimate:

    coord_source = 'plss-section'
    coord_status = 'plss_estimate'

Validation against 28 already-confirmed lakes: median error ~0.5 mi, 25/28
within their section (~0.9 mi); occasional ~1.9 mi outliers near section edges.
So this is a "get the pin close, then eyeball it" seed — it is NOT exported to
the PWA (export_web_data.py ships only confirmed/manual) and it shows up in the
Lake Locator under its own cyan category for you to nudge onto the real lake and
Confirm.

IMPORTANT scope: this sheet is the Uinta-Wasatch-Cache forest (north slope +
Wasatch) and contains NO Uintah-County / Ashley Creek lakes — those live in the
separate Ashley National Forest. This script only ever matches designations that
already exist in the DB, so it simply won't touch Ashley.

Writes the DB, so it obeys the single-writer guard (refuses on a mirror).

Usage:
    python3 scripts/seed_coords_from_forest_service.py --dry-run
    python3 scripts/seed_coords_from_forest_service.py --limit 5     # test a few
    python3 scripts/seed_coords_from_forest_service.py               # place all matches
    python3 scripts/seed_coords_from_forest_service.py --overwrite-seeds=false
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request

from coord_utils import DB_PATH, REPO_ROOT, ensure_coord_columns
from writer_guard import is_readonly_mirror

PDF = REPO_ROOT / "data" / "master-summary-forest-service.pdf"
BLM = ("https://gis.blm.gov/arcgis/rest/services/Cadastral/"
       "BLM_Natl_PLSS_CadNSDI/MapServer/2/query")
MERIDIAN_CODE = {"SL": "26", "US": "30"}  # Salt Lake / Uintah Special
# A data row: leading designation, then somewhere a `T{dir},R{dir},Sec` token and
# a meridian abbreviation.
DESIG_RE = re.compile(r"^([A-Z]{1,3}-\d+)\b")
TRS_RE = re.compile(r"\b(\d+)([NS]),\s?(\d+)([EW]),\s?(\d+)\b")
MER_RE = re.compile(r"\b(SL|US)\b")


def extract_rows(pdf_path):
    """Parse the sheet -> {designation: {tn,td,rn,rd,sec,mer}} for rows that
    carry a well-formed T,R,S. Malformed/partial TRS rows are skipped (reported)."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                         capture_output=True, text=True, check=True).stdout
    rows, skipped = {}, []
    for line in txt.splitlines():
        s = line.strip()
        m = DESIG_RE.match(s)
        if not m:
            continue
        desig = m.group(1).upper()
        trs = TRS_RE.search(line)
        mer = MER_RE.search(line)
        if not trs or not mer:
            skipped.append((desig, s[:60]))
            continue
        tn, td, rn, rd, sec = trs.groups()
        rows[desig] = dict(tn=int(tn), td=td, rn=int(rn), rd=rd, sec=int(sec),
                           mer=MERIDIAN_CODE[mer.group(1)])
    return rows, skipped


def section_centroid(p, timeout=60):
    """Section centroid (lat, lng) from the BLM PLSS service, or None."""
    plssid = f"UT{p['mer']}{p['tn']:03d}0{p['td']}{p['rn']:03d}0{p['rd']}0"
    where = f"PLSSID='{plssid}' AND FRSTDIVNO='{p['sec']:02d}'"
    q = urllib.parse.urlencode({"where": where, "outFields": "FRSTDIVNO",
                                "returnGeometry": "true", "outSR": "4326", "f": "json"})
    with urllib.request.urlopen(f"{BLM}?{q}", timeout=timeout) as r:
        d = json.load(r)
    feats = d.get("features") or []
    if not feats:
        return None
    ring = feats[0]["geometry"]["rings"][0]
    xs = [a[0] for a in ring]
    ys = [a[1] for a in ring]
    return round(sum(ys) / len(ys), 6), round(sum(xs) / len(xs), 6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="compute + report, write nothing")
    ap.add_argument("--limit", type=int, default=0, help="only process the first N matches (0 = all)")
    ap.add_argument("--overwrite-seeds", default="true",
                    help="true (default): replace existing seed_unverified/seed_suspect coords; "
                         "false: only fill lakes with NO coordinate")
    args = ap.parse_args()
    overwrite_seeds = args.overwrite_seeds.lower() != "false"

    if is_readonly_mirror():
        print("[writer-guard] .db-readonly present — this clone is a read-only mirror. Aborting.")
        return 1

    rows, skipped = extract_rows(PDF)
    print(f"Parsed {len(rows)} designation rows with a usable T,R,S "
          f"({len(skipped)} designation rows skipped for malformed/missing TRS).")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_coord_columns(conn)
    db = {r["letter_number"].upper(): r for r in conn.execute(
        "SELECT letter_number, name, drainage, lat, coord_status FROM lakes")}

    # Candidates: sheet designations that exist in the DB and are not already
    # authoritatively placed. Optionally skip lakes that already have any coord.
    candidates = []
    for desig, p in rows.items():
        r = db.get(desig)
        if not r:
            continue
        if r["coord_status"] in ("confirmed", "manual"):
            continue
        if not overwrite_seeds and r["lat"] is not None:
            continue
        candidates.append((desig, p, r))
    candidates.sort(key=lambda c: (c[2]["drainage"] or "", c[0]))
    if args.limit:
        candidates = candidates[:args.limit]

    print(f"{len(candidates)} candidate lakes to place as plss_estimate.\n")
    placed, failed = 0, []
    for desig, p, r in candidates:
        try:
            c = section_centroid(p)
        except Exception as e:  # network / service hiccup — keep going, report
            failed.append((desig, f"service error: {e}"))
            continue
        if not c:
            failed.append((desig, f"no PLSS section for T{p['tn']}{p['td']} R{p['rn']}{p['rd']} S{p['sec']}"))
            continue
        lat, lng = c
        was = r["coord_status"] or "empty"
        print(f"  {desig:7s} {(r['name'] or ''):22s} {r['drainage']:24s} "
              f"({lat:.5f},{lng:.5f})  [{was} -> plss_estimate]")
        if not args.dry_run:
            conn.execute(
                "UPDATE lakes SET lat=?, lng=?, coord_source='plss-section', "
                "coord_status='plss_estimate' WHERE letter_number=?",
                (lat, lng, r["letter_number"]))
        placed += 1

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f"\n{'[dry-run] would place' if args.dry_run else 'Placed'} {placed} estimates; "
          f"{len(failed)} failed.")
    for desig, why in failed:
        print(f"  FAILED {desig}: {why}")
    if not args.dry_run and placed:
        print("\nNext: review them in the Locator (filter '◆ PLSS estimates'), nudge each "
              "pin onto the real lake, and Confirm. Nothing was exported to the PWA.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
