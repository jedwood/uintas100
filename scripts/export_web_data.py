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
                  status, trip_reports, junesucker_notes, dwr_notes, cma_notes,
                  no_fish, lat, lng, coord_status, starred
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
                "trip_reports": row["trip_reports"],
                "junesucker_notes": row["junesucker_notes"],
                "dwr_notes": row["dwr_notes"],
                "cma_notes": row["cma_notes"],
                "starred": row["starred"],
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

    # Trailheads (mined from the CMA book): each carries the letter_numbers of
    # the lakes its book pages mention, so the frontend can join both ways.
    trailheads = []
    for row in conn.execute(
        "SELECT id, name, region, drainage, pages, info FROM trailheads ORDER BY name"
    ):
        lake_lns = [r[0] for r in conn.execute(
            """SELECT l.letter_number FROM trailhead_lakes tl
               JOIN lakes l ON tl.lake_id = l.id
               WHERE tl.trailhead_id = ? ORDER BY l.letter_number""", (row["id"],))]
        trailheads.append(
            {
                "name": row["name"],
                "region": row["region"],
                "drainage": row["drainage"],
                "pages": row["pages"],
                "info": row["info"],
                "lakes": lake_lns,
            }
        )

    # Falcon guidebook hikes: emitted once as a top-level array (like
    # `trailheads`), each carrying the letter_numbers of the lakes it reaches so
    # the lake modal can filter without duplicating the (long) narratives.
    hikes = []
    for row in conn.execute(
        """SELECT h.id, h.hike_number, h.name, r.name AS region,
                  h.start_trailhead, t.name AS trailhead, t.maps,
                  h.distance, h.destination_elevation, h.hiking_time,
                  h.difficulty, h.usage, h.nearest_town, h.drainage,
                  h.narrative, h.finding_trailhead, h.source_pages
           FROM guide_hikes h
           LEFT JOIN guide_regions r ON h.region_id = r.id
           LEFT JOIN guide_trailheads t ON h.trailhead_id = t.id
           ORDER BY h.hike_number"""
    ):
        lake_links = [
            {"letter_number": r["letter_number"], "primary": r["is_primary"]}
            for r in conn.execute(
                """SELECT l.letter_number, hl.is_primary
                   FROM guide_hike_lakes hl
                   JOIN lakes l ON hl.lake_id = l.id
                   WHERE hl.hike_id = ?
                   ORDER BY hl.is_primary DESC, l.letter_number""", (row["id"],))
        ]
        hikes.append(
            {
                "number": row["hike_number"],
                "name": row["name"],
                "region": row["region"],
                "trailhead": row["trailhead"] or row["start_trailhead"],
                "start": row["start_trailhead"],
                "maps": row["maps"],
                "distance": row["distance"],
                "destination_elevation": row["destination_elevation"],
                "hiking_time": row["hiking_time"],
                "difficulty": row["difficulty"],
                "usage": row["usage"],
                "nearest_town": row["nearest_town"],
                "drainage": row["drainage"],
                "narrative": row["narrative"],
                "finding_trailhead": row["finding_trailhead"],
                "source_pages": row["source_pages"],
                "lakes": lake_links,
            }
        )

    conn.close()

    data = {"lakes": lakes, "drainages": drainages, "trailheads": trailheads,
            "hikes": hikes}
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )

    n_stocking = sum(len(l["stocking"]) for l in lakes)
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(
        f"Exported {len(lakes)} lakes, {n_stocking} stocking records, "
        f"{len(drainages)} drainages, {len(trailheads)} trailheads, "
        f"{len(hikes)} hikes "
        f"-> {OUTPUT_PATH.name} ({size_kb:.0f} KB)"
    )


if __name__ == "__main__":
    export()
