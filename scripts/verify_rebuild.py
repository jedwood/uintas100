#!/usr/bin/env python3
"""
Regression guard: rebuild a DB from the committed seeds (data/seeds/) into a temp
file and prove it is content-equivalent to the canonical uinta_lakes.db.

Every table is compared on its NATURAL data (surrogate `id` and trigger-managed
`last_modified` are ignored; foreign keys are compared via the parent's natural
key). Exits 0 if identical, 1 if anything differs — so it can gate commits/CI and
keep the committed DB reproducible going forward.

    python3 verify_rebuild.py
"""

import collections
import os
import sqlite3
import sys
import tempfile

import rebuild_database

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
LIVE_DB = os.path.join(PROJECT_DIR, "uinta_lakes.db")

# table -> SELECT yielding natural-key rows (no surrogate id, no last_modified),
# FKs resolved to the parent's natural key. Order doesn't matter: rows are
# compared as a multiset.
TABLE_QUERIES = {
    "lakes": """
        SELECT letter_number, name, drainage, basin, junesucker_notes,
               coordinates, map_link, size_acres, max_depth_ft, elevation_ft,
               dwr_notes, fish_species, fishing_pressure, jed_notes, status,
               trip_reports, notes_needs_update, no_fish, lat, lng,
               coord_source, coord_status
        FROM lakes""",
    "drainages": "SELECT name, info, map FROM drainages",
    "photos": """
        SELECT l.letter_number, p.filename, p.source_url, p.downloaded_path
        FROM photos p LEFT JOIN lakes l ON p.lake_id = l.id""",
    "stocking_records": """
        SELECT l.letter_number, s.county, s.species, s.quantity, s.length,
               s.stock_date, s.source_year
        FROM stocking_records s LEFT JOIN lakes l ON s.lake_id = l.id""",
    "other_waters": """
        SELECT water_name, water_type, likely_drainage, inferred_from, county, notes
        FROM other_waters""",
    "other_stocking_records": """
        SELECT w.water_name, o.county, o.species, o.quantity, o.length,
               o.stock_date, o.source_year
        FROM other_stocking_records o LEFT JOIN other_waters w ON o.water_id = w.id""",
    "fishing_reports": """
        SELECT l.letter_number, f.date, f.success, f.notes
        FROM fishing_reports f LEFT JOIN lakes l ON f.lake_id = l.id""",
}


def multiset(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return collections.Counter(conn.execute(sql).fetchall())
    finally:
        conn.close()


def main():
    fd, tmp = tempfile.mkstemp(prefix="uinta_verify_", suffix=".db")
    os.close(fd)
    os.remove(tmp)
    print("=== VERIFY REBUILD (seeds -> DB vs canonical) ===")
    rebuild_database.rebuild(tmp)

    ok = True
    for table, sql in TABLE_QUERIES.items():
        live = multiset(LIVE_DB, sql)
        reb = multiset(tmp, sql)
        if live == reb:
            print(f"  ✓ {table:24} {sum(live.values()):6} rows match")
            continue
        ok = False
        only_live = live - reb
        only_reb = reb - live
        print(f"  ✗ {table:24} DIFF  "
              f"live={sum(live.values())} rebuild={sum(reb.values())}  "
              f"(+{sum(only_reb.values())} rebuild-only / "
              f"-{sum(only_live.values())} live-only)")
        for label, diff in (("live-only", only_live), ("rebuild-only", only_reb)):
            for row, n in list(diff.items())[:8]:
                print(f"       {label} x{n}: {row}")
            if len(diff) > 8:
                print(f"       ... and {len(diff) - 8} more {label} rows")

    os.remove(tmp)
    if ok:
        print("\nRESULT: PASS — rebuild from seeds is content-equivalent to "
              "uinta_lakes.db")
        sys.exit(0)
    print("\nRESULT: FAIL — seeds are out of sync with uinta_lakes.db. "
          "Re-run export_seeds.py (or investigate the diff above).")
    sys.exit(1)


if __name__ == "__main__":
    main()
