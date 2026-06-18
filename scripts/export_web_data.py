#!/usr/bin/env python3
"""
Export the SQLite database to lakes_data.json for the web frontend.

The PWA loads this JSON file directly instead of shipping the SQLite
database and the sql.js wasm runtime to the browser. Stocking records
and photos are nested under each lake so the frontend needs no joins.

Run after any database update:
    python3 scripts/export_web_data.py

The pre-commit hook runs this automatically whenever uinta_lakes.db
is part of a commit.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "uinta_lakes.db"
OUTPUT_PATH = REPO_ROOT / "lakes_data.json"


def export():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Tolerate a database built before coordinates existed (fresh setup_database.py)
    try:
        from coord_utils import ensure_coord_columns
        ensure_coord_columns(conn)
    except ImportError:
        pass

    stocking_by_lake = {}
    for row in conn.execute(
        """SELECT lake_id, species, quantity, length, stock_date
           FROM stocking_records ORDER BY stock_date DESC"""
    ):
        stocking_by_lake.setdefault(row["lake_id"], []).append(
            {
                "species": row["species"],
                "quantity": row["quantity"],
                "length": row["length"],
                "stock_date": row["stock_date"],
            }
        )

    photos_by_lake = {}
    for row in conn.execute(
        "SELECT lake_id, downloaded_path FROM photos ORDER BY filename"
    ):
        photos_by_lake.setdefault(row["lake_id"], []).append(row["downloaded_path"])

    # Only surface human-verified coordinates in the PWA, so a half-finished
    # seeding pass doesn't ship wrong pins. Seeds stay internal to the Locator.
    verified = {"confirmed", "manual"}

    lakes = []
    for row in conn.execute(
        """SELECT id, letter_number, name, drainage, size_acres, max_depth_ft,
                  elevation_ft, fish_species, fishing_pressure, jed_notes,
                  status, junesucker_notes, dwr_notes, no_fish,
                  lat, lng, coord_status
           FROM lakes"""
    ):
        coords_ok = row["coord_status"] in verified and row["lat"] is not None
        lakes.append(
            {
                "letter_number": row["letter_number"],
                "name": row["name"],
                "drainage": row["drainage"],
                "size_acres": row["size_acres"],
                "max_depth_ft": row["max_depth_ft"],
                "elevation_ft": row["elevation_ft"],
                "fish_species": row["fish_species"],
                "fishing_pressure": row["fishing_pressure"],
                "jed_notes": row["jed_notes"],
                "status": row["status"],
                "junesucker_notes": row["junesucker_notes"],
                "dwr_notes": row["dwr_notes"],
                "no_fish": row["no_fish"] or 0,
                "lat": row["lat"] if coords_ok else None,
                "lng": row["lng"] if coords_ok else None,
                "stocking": stocking_by_lake.get(row["id"], []),
                "photos": photos_by_lake.get(row["id"], []),
            }
        )

    # Pre-sort alphabetically (letter_number as name fallback) so the
    # frontend can use the list as-is.
    lakes.sort(key=lambda l: (l["name"] or l["letter_number"] or "").lower())

    drainages = [
        {"name": row["name"], "info": row["info"], "map": row["map"]}
        for row in conn.execute("SELECT name, info, map FROM drainages ORDER BY name")
    ]

    conn.close()

    data = {"lakes": lakes, "drainages": drainages}
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )

    n_stocking = sum(len(l["stocking"]) for l in lakes)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(
        f"Exported {len(lakes)} lakes, {n_stocking} stocking records, "
        f"{len(drainages)} drainages -> {OUTPUT_PATH.name} ({size_kb:.0f} KB)"
    )


if __name__ == "__main__":
    export()
