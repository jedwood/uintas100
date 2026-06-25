#!/usr/bin/env python3
"""
Rebuild a content-equivalent `uinta_lakes.db` from the committed CSV seeds in
data/seeds/ — fully offline, no network, deterministic.

This is the canonical recovery path. It does NOT replay the raw DWR stocking CSV
through the matcher (that reintroduces lowland-reservoir mis-matches and can't
recreate the manually-curated lakes/drainages/photos — see export_seeds.py); it
loads the curated seeds straight into a fresh canonical schema.

Usage:
    python3 rebuild_database.py                 # build into a temp file, print path
    python3 rebuild_database.py --output PATH    # build into PATH (refuses to
                                                 # overwrite the real DB unless
                                                 # --force is also given)

`verify_rebuild.py` uses this to prove the seeds round-trip to the canonical DB.
"""

import argparse
import csv
import os
import sqlite3
import sys
import tempfile

from database_utils import create_database

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SEED_DIR = os.path.join(PROJECT_DIR, "data", "seeds")
REAL_DB = os.path.join(PROJECT_DIR, "uinta_lakes.db")

NULL_SENTINEL = "\\N"


def _v(x):
    """CSV cell -> Python value, restoring SQL NULL from the sentinel."""
    return None if x == NULL_SENTINEL else x


def _read_seed(name):
    path = os.path.join(SEED_DIR, name)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [ {k: _v(v) for k, v in row.items()} for row in reader ]


def rebuild(output_path):
    conn = create_database(output_path)   # full canonical schema, empty tables
    cur = conn.cursor()

    # --- lakes (must come first; everything else FKs to it) ---
    lake_cols = [
        "letter_number", "name", "drainage", "basin", "junesucker_notes",
        "coordinates", "map_link", "size_acres", "max_depth_ft", "elevation_ft",
        "dwr_notes", "fish_species", "fishing_pressure", "jed_notes", "status",
        "trip_reports", "notes_needs_update", "no_fish", "lat", "lng",
        "coord_source", "coord_status",
    ]
    placeholders = ",".join("?" * len(lake_cols))
    for row in _read_seed("lakes.csv"):
        cur.execute(
            f"INSERT INTO lakes ({','.join(lake_cols)}) VALUES ({placeholders})",
            [row[c] for c in lake_cols],
        )
    lake_id = {ln: lid for lid, ln in cur.execute(
        "SELECT id, letter_number FROM lakes")}

    # --- drainages ---
    for row in _read_seed("drainages.csv"):
        cur.execute("INSERT INTO drainages (name, info, map) VALUES (?, ?, ?)",
                    (row["name"], row["info"], row["map"]))

    # --- other_waters (parent of other_stocking_records) ---
    for row in _read_seed("other_waters.csv"):
        cur.execute(
            """INSERT INTO other_waters
               (water_name, water_type, likely_drainage, inferred_from, county, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["water_name"], row["water_type"], row["likely_drainage"],
             row["inferred_from"], row["county"], row["notes"]),
        )
    water_id = {wn: wid for wid, wn in cur.execute(
        "SELECT id, water_name FROM other_waters")}

    # --- child tables, FKs resolved by natural key ---
    skipped = 0

    def lid(ln):
        nonlocal skipped
        if ln in lake_id:
            return lake_id[ln]
        skipped += 1
        return None

    for row in _read_seed("photos.csv"):
        cur.execute(
            """INSERT INTO photos (lake_id, filename, source_url, downloaded_path)
               VALUES (?, ?, ?, ?)""",
            (lid(row["letter_number"]), row["filename"], row["source_url"],
             row["downloaded_path"]),
        )

    for row in _read_seed("stocking_records.csv"):
        cur.execute(
            """INSERT INTO stocking_records
               (lake_id, county, species, quantity, length, stock_date, source_year)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (lid(row["letter_number"]), row["county"], row["species"],
             row["quantity"], row["length"], row["stock_date"], row["source_year"]),
        )

    for row in _read_seed("fishing_reports.csv"):
        cur.execute(
            "INSERT INTO fishing_reports (lake_id, date, success, notes) VALUES (?, ?, ?, ?)",
            (lid(row["letter_number"]), row["date"], row["success"], row["notes"]),
        )

    for row in _read_seed("other_stocking_records.csv"):
        wid = water_id.get(row["water_name"])
        if wid is None:
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO other_stocking_records
               (water_id, county, species, quantity, length, stock_date, source_year)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (wid, row["county"], row["species"], row["quantity"], row["length"],
             row["stock_date"], row["source_year"]),
        )

    conn.commit()
    conn.close()
    if skipped:
        print(f"  WARNING: skipped {skipped} child rows with an unresolved FK")
    return output_path


def main():
    ap = argparse.ArgumentParser(description="Rebuild uinta_lakes.db from CSV seeds")
    ap.add_argument("--output", help="output DB path (default: a temp file)")
    ap.add_argument("--force", action="store_true",
                    help="allow --output to be the real uinta_lakes.db")
    args = ap.parse_args()

    if args.output:
        out = os.path.abspath(args.output)
        if out == os.path.abspath(REAL_DB) and not args.force:
            sys.exit("Refusing to overwrite the canonical uinta_lakes.db "
                     "(pass --force if you really mean it). The rebuild is meant "
                     "to be verified against it, not to replace it.")
        if os.path.exists(out):
            os.remove(out)
    else:
        fd, out = tempfile.mkstemp(prefix="uinta_rebuild_", suffix=".db")
        os.close(fd)
        os.remove(out)

    print("=== REBUILDING DB FROM SEEDS ===")
    rebuild(out)
    print(f"Rebuilt database at: {out}")


if __name__ == "__main__":
    main()
