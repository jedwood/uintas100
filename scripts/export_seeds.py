#!/usr/bin/env python3
"""
Export the canonical `uinta_lakes.db` to committed, human-diffable CSV seeds
under data/seeds/. These seeds — not the binary .db — are the reconstruction
source: `rebuild_database.py` loads them back into a content-equivalent DB and
`verify_rebuild.py` proves the round-trip.

Why seeds instead of replaying data/utah_dwr_stocking_data.csv through the
matcher: a clean replay does NOT reproduce the curated DB. It re-credits lowland
reservoirs onto same-named Uinta lakes (e.g. "Echo Reservoir" -> Z-16 Echo), and
it can't recreate the ~55 manually-added lakes or the drainage/photo data, whose
original sources aren't committed. The seeds capture the curated truth exactly.

Run this after any change to uinta_lakes.db (same spirit as export_web_data.py),
then commit the updated seeds alongside the DB so the two never drift.

Surrogate `id` and trigger-managed `last_modified` columns are intentionally
omitted; foreign keys are written as the referenced row's natural key.
"""

import csv
import os
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
SEED_DIR = os.path.join(PROJECT_DIR, "data", "seeds")

# CSV can't tell SQL NULL apart from an empty string, but the DB does (e.g.
# `basin` is '' for most lakes yet NULL for 11; `status` must be NULL because its
# CHECK constraint forbids ''). We write NULL as this sentinel and leave true
# empty strings empty, so the round-trip preserves the distinction exactly.
NULL_SENTINEL = "\\N"

# Each seed: output file, column headers, and the SELECT that produces rows in a
# deterministic order (FKs resolved to natural keys). Headers must match the
# loader in rebuild_database.py.
SEEDS = {
    "lakes.csv": {
        "columns": [
            "letter_number", "name", "drainage", "basin", "junesucker_notes",
            "coordinates", "map_link", "size_acres", "max_depth_ft",
            "elevation_ft", "dwr_notes", "fish_species", "fishing_pressure",
            "jed_notes", "status", "trip_reports", "notes_needs_update",
            "no_fish", "lat", "lng", "coord_source", "coord_status",
        ],
        "sql": """
            SELECT letter_number, name, drainage, basin, junesucker_notes,
                   coordinates, map_link, size_acres, max_depth_ft, elevation_ft,
                   dwr_notes, fish_species, fishing_pressure, jed_notes, status,
                   trip_reports, notes_needs_update, no_fish, lat, lng,
                   coord_source, coord_status
            FROM lakes
            ORDER BY letter_number
        """,
    },
    "drainages.csv": {
        "columns": ["name", "info", "map"],
        "sql": "SELECT name, info, map FROM drainages ORDER BY name",
    },
    "photos.csv": {
        "columns": ["letter_number", "filename", "source_url", "downloaded_path"],
        "sql": """
            SELECT l.letter_number, p.filename, p.source_url, p.downloaded_path
            FROM photos p
            LEFT JOIN lakes l ON p.lake_id = l.id
            ORDER BY l.letter_number, p.filename
        """,
    },
    "stocking_records.csv": {
        "columns": ["letter_number", "county", "species", "quantity", "length",
                    "stock_date", "source_year"],
        "sql": """
            SELECT l.letter_number, s.county, s.species, s.quantity, s.length,
                   s.stock_date, s.source_year
            FROM stocking_records s
            LEFT JOIN lakes l ON s.lake_id = l.id
            ORDER BY l.letter_number, s.stock_date, s.species, s.quantity,
                     s.length, s.county, s.source_year
        """,
    },
    "other_waters.csv": {
        "columns": ["water_name", "water_type", "likely_drainage",
                    "inferred_from", "county", "notes"],
        "sql": """
            SELECT water_name, water_type, likely_drainage, inferred_from,
                   county, notes
            FROM other_waters
            ORDER BY water_name
        """,
    },
    "other_stocking_records.csv": {
        "columns": ["water_name", "county", "species", "quantity", "length",
                    "stock_date", "source_year"],
        "sql": """
            SELECT w.water_name, o.county, o.species, o.quantity, o.length,
                   o.stock_date, o.source_year
            FROM other_stocking_records o
            LEFT JOIN other_waters w ON o.water_id = w.id
            ORDER BY w.water_name, o.stock_date, o.species, o.quantity, o.length
        """,
    },
    "fishing_reports.csv": {
        "columns": ["letter_number", "date", "success", "notes"],
        "sql": """
            SELECT l.letter_number, f.date, f.success, f.notes
            FROM fishing_reports f
            LEFT JOIN lakes l ON f.lake_id = l.id
            ORDER BY l.letter_number, f.date
        """,
    },
}


def export(db_path=DB_PATH, seed_dir=SEED_DIR):
    os.makedirs(seed_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    total = 0
    for filename, spec in SEEDS.items():
        rows = cursor.execute(spec["sql"]).fetchall()
        # Guard: a NULL natural key means an orphaned FK that won't round-trip.
        if spec["columns"][0] in ("letter_number", "water_name"):
            orphans = sum(1 for r in rows if r[0] is None)
            if orphans:
                print(f"  WARNING: {filename}: {orphans} rows with a NULL "
                      f"{spec['columns'][0]} (orphaned FK) — will not round-trip")
        path = os.path.join(seed_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(spec["columns"])
            for row in rows:
                writer.writerow([NULL_SENTINEL if v is None else v for v in row])
        print(f"  {filename:30} {len(rows):6} rows")
        total += len(rows)
    conn.close()
    print(f"Exported {total} rows across {len(SEEDS)} seed files to {seed_dir}")


if __name__ == "__main__":
    print("=== EXPORTING DB SEEDS ===")
    export()
