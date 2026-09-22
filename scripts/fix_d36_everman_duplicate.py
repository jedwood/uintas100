#!/usr/bin/env python3
"""One-off: remove the phantom "D-36 Everman" duplicate of Z-36.

Everman Lake sits in Naturalist Basin and DWR designates it **Z-36**. Every
primary source agrees:

    data/ocr/duchesne_ocr_text.txt:58      "EVERMAN, Z-36"
    data/ocr/dwr_extraction_review.txt:560 "140. Z-36 (EVERMAN)"
    data/norrick_lakes.txt:168             "Everman, Z-36"
    lakes.cma_notes (Cordell Andersen)     "EVERMAN (Z-36): 10,520 ft. ..."

The single exception is `data/lake_data.csv` line 135 — the hand-transcribed
"original 609 designations" list — which reads `Everman,D-36`. That typo is
where the extra row came from: `setup_database.py` created a D-36 lake, and
nothing ever populated it, because every downstream source keys off Z-36.

State before this script (lake ids 135 = D-36, 623 = Z-36):

    D-36: name + drainage + manually-placed coordinates. Nothing else.
          0 stocking records, 0 photos, 0 trailhead links, 0 survey rows,
          0 guide-hike links, no DWR notes, no elevation/size/depth,
          no user fields (status / jed_notes / trip_reports / starred),
          and no mention in data/app_edits_log.jsonl.
    Z-36: the real lake — DWR write-up, 7.8 acres / 7 ft / 10,520 ft,
          Brookies, 8 stocking records, a trailhead link, CMA notes.

So D-36 carries nothing that needs merging; it is deleted outright. The one
thing it *did* have was confirmed coordinates, and Z-36 has its own confirmed
manual coordinates ~60 m away (placed 2026-09-22), so the map keeps its pin.

This also fixes the typo at the source in data/lake_data.csv, so a replay of
setup_database.py can't resurrect the phantom.

Run once, then re-export:  python3 scripts/export_web_data.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import writer_guard  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "uinta_lakes.db"
SOURCE_CSV = REPO / "data" / "lake_data.csv"

BAD = "D-36"
GOOD = "Z-36"
NAME = "Everman"

# Tables that reference lakes.id — checked (not just assumed) to be empty for
# the phantom before it is deleted.
REFERENCING = [
    ("stocking_records", "lake_id"),
    ("photos", "lake_id"),
    ("dwr_gillnet_samples", "lake_id"),
    ("dwr_lake_summary", "lake_id"),
    ("guide_hike_lakes", "lake_id"),
    ("trailhead_lakes", "lake_id"),
    ("fishing_reports", "lake_id"),
]

# Columns that would mean losing curated or user-entered content on delete.
MUST_BE_EMPTY = [
    "basin", "junesucker_notes", "coordinates", "map_link", "size_acres",
    "max_depth_ft", "elevation_ft", "dwr_notes", "dwr_notes_prev", "dwr_edition",
    "fish_species", "fishing_pressure", "jed_notes", "status", "trip_reports",
    "cma_notes", "starred",
]


def fix_database(conn):
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, name FROM lakes WHERE letter_number = ?", (BAD,)
    ).fetchone()
    if row is None:
        print(f"  {BAD}: already gone — nothing to delete")
        return False
    bad_id, bad_name = row

    if bad_name != NAME:
        raise SystemExit(f"ABORT: {BAD} is named {bad_name!r}, not {NAME!r}")

    keeper = cur.execute(
        "SELECT id FROM lakes WHERE letter_number = ?", (GOOD,)
    ).fetchone()
    if keeper is None:
        raise SystemExit(f"ABORT: {GOOD} does not exist — refusing to delete {BAD}")

    # Refuse to delete a row that turns out to carry data after all.
    populated = [
        col for col in MUST_BE_EMPTY
        if cur.execute(
            f"SELECT {col} FROM lakes WHERE id = ?", (bad_id,)
        ).fetchone()[0] not in (None, "", 0)
    ]
    if populated:
        raise SystemExit(f"ABORT: {BAD} has data in {populated} — merge by hand")

    for table, col in REFERENCING:
        n = cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", (bad_id,)
        ).fetchone()[0]
        if n:
            raise SystemExit(f"ABORT: {BAD} has {n} row(s) in {table} — merge by hand")

    cur.execute("DELETE FROM lakes WHERE id = ?", (bad_id,))
    conn.commit()
    print(f"  deleted lakes id={bad_id} ({BAD} {NAME}); kept {GOOD} id={keeper[0]}")
    return True


def fix_source_csv():
    """Correct the transcription typo that created the phantom.

    Edited line-by-line rather than via a csv round-trip: csv.writer would
    rewrite all 600 lines with CRLF endings and bury a one-cell fix in a
    whole-file diff.
    """
    text = SOURCE_CSV.read_text(encoding="utf-8")
    target = f",{NAME},{BAD}"
    if target not in text:
        print(f"  {SOURCE_CSV.name}: already correct")
        return False
    fixed = text.replace(target, f",{NAME},{GOOD}")
    SOURCE_CSV.write_text(fixed, encoding="utf-8", newline="")
    print(f"  {SOURCE_CSV.name}: {NAME} {BAD} -> {GOOD}")
    return True


def main():
    writer_guard.exit_if_readonly()
    print("Removing the phantom D-36 Everman duplicate:")
    conn = sqlite3.connect(DB)
    try:
        fix_database(conn)
    finally:
        conn.close()
    fix_source_csv()
    print("\nDone. Now run: python3 scripts/export_web_data.py")


if __name__ == "__main__":
    main()
