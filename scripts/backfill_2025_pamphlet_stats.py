#!/usr/bin/env python3
"""
Backfill size_acres / elevation_ft / max_depth_ft for lakes whose dwr_notes
came from a 2025 revised pamphlet (dwr_edition = 2025) but never got their
physical stats populated in the original import.

The 2025 write-ups state these stats in prose (e.g. BR-43: "It is 1.7 surface
acres, 11,120 feet in elevation, with 10 feet maximum depth."), but
compare_new_pamphlets.py only ever set dwr_notes/dwr_edition, not the
physical-stat columns. Values below were hand-extracted from each lake's
dwr_notes text (see git blame for the source). Lakes whose pamphlet text says
"does not sustain fish life" or explicitly gives no stat ("depth information
is not available") are intentionally omitted -- there is nothing to extract.

Usage:
    python3 scripts/backfill_2025_pamphlet_stats.py          # dry run
    python3 scripts/backfill_2025_pamphlet_stats.py apply    # write changes
"""

import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")

# letter_number -> {field: value}, hand-extracted from dwr_notes prose.
UPDATES = {
    "BR-34": {"size_acres": 2.1, "elevation_ft": 10390, "max_depth_ft": 7},
    "BR-35": {"size_acres": 1.3, "elevation_ft": 10470, "max_depth_ft": 4},
    "BR-43": {"size_acres": 1.7, "elevation_ft": 11120, "max_depth_ft": 10},
    "BR-55": {"size_acres": 1.5, "elevation_ft": 10860, "max_depth_ft": 12},
    "G-105": {"size_acres": 2.2, "elevation_ft": 10820, "max_depth_ft": 3},
    "WR-1": {"size_acres": 3.9, "elevation_ft": 11060, "max_depth_ft": 5},
    "WR-29": {"size_acres": 9.7, "elevation_ft": 10075, "max_depth_ft": 15},
    "WR-30": {"size_acres": 6.2, "elevation_ft": 10780, "max_depth_ft": 8},
    "WR-33": {"size_acres": 5.7, "elevation_ft": 10652, "max_depth_ft": 10},
    "WR-41": {"size_acres": 4.5, "elevation_ft": 10500, "max_depth_ft": 4.5},
    "WR-73": {"max_depth_ft": 18},  # size_acres/elevation_ft already set
}


def main(apply=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    updated = 0
    for letter_number, fields in UPDATES.items():
        row = cur.execute(
            "SELECT id, size_acres, elevation_ft, max_depth_ft, dwr_edition "
            "FROM lakes WHERE letter_number = ?",
            (letter_number,),
        ).fetchone()
        if row is None:
            print(f"SKIP {letter_number}: not found in database")
            continue
        if row["dwr_edition"] != 2025:
            print(f"SKIP {letter_number}: dwr_edition is {row['dwr_edition']!r}, not 2025")
            continue

        # Only fill columns that are currently NULL -- never clobber existing data.
        to_set = {}
        for field, value in fields.items():
            if row[field] is None:
                to_set[field] = value
            elif row[field] != value:
                print(
                    f"WARN {letter_number}.{field}: existing value {row[field]!r} "
                    f"differs from extracted {value!r}, leaving as-is"
                )

        if not to_set:
            print(f"SKIP {letter_number}: nothing to fill")
            continue

        set_clause = ", ".join(f"{k} = ?" for k in to_set)
        print(f"{'APPLY' if apply else 'DRY RUN'} {letter_number}: {to_set}")
        if apply:
            cur.execute(
                f"UPDATE lakes SET {set_clause} WHERE id = ?",
                (*to_set.values(), row["id"]),
            )
        updated += 1

    if apply:
        conn.commit()
        print(f"\nUpdated {updated} lake(s).")
    else:
        print(f"\n{updated} lake(s) would be updated. Re-run with 'apply' to write changes.")

    conn.close()


if __name__ == "__main__":
    main(apply=len(sys.argv) > 1 and sys.argv[1] == "apply")
