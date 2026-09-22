#!/usr/bin/env python3
"""One-off: correct 18 mis-filed drainages and repair 4 damaged stocking records.

Run once, then re-export:  python3 scripts/export_web_data.py

────────────────────────────────────────────────────────────────────────────
PART 1 — drainage corrections
────────────────────────────────────────────────────────────────────────────
`lakes.drainage` means "which DWR pamphlet booklet prints this lake's write-up"
(watershed), NOT the letter prefix (which is a survey block — see CLAUDE.md).
These 18 rows disagree with the booklet that actually prints them. Each was
confirmed on four independent axes before being listed here:

  (a) PAMPHLET MEMBERSHIP — which booklet prints the designation.
  (b) NUMERIC BLOCK — the unbroken run of neighbours in the same drainage.
  (c) DWR COUNTY on the lake's own stocking records.
  (d) COORDINATES / the write-up's own named landmarks.

A. Eleven GR- lakes filed "Ashley Creek" that belong to Sheep/Carter.
   (a) The Ashley booklet prints exactly DF-2..18 and GR-34..77 — none of
       these eleven. All eleven are printed in the Sheep/Carter/Burnt Fork
       booklet.
   (b) GR-1..GR-33 is otherwise solidly Sheep/Carter; Ashley's GR block
       starts at GR-34. These eleven are interleaved among Sheep/Carter
       neighbours (GR-5 between GR-4 and GR-6, GR-19/20/21 between GR-18
       and GR-22 Bummer, and so on).
   (c) Their stocking records report DAGGETT county. Ashley Creek is
       overwhelmingly UINTAH (173 records); Sheep/Carter is DAGGETT (160).
       GR-5 reports SUMMIT, which Sheep/Carter also spans (49 records).
   (d) Coordinates cluster at 40.79-40.82 N with Spirit Lake (GR-3) and Red
       Lake (GR-33); Ashley's own block sits 4-8 miles south at 40.69-40.77.
       The write-ups name Spirit Lake, Anson Lakes (GR-9/10), Bummer Lake
       (GR-22), Weyman Lakes Basin, Lamb Lakes Basin, the Sheep Creek Canal,
       and the Carter Creek rotenone project — all Sheep/Carter features.
       GR-104 (no coordinates) reads "overlooking the Sheep Creek Canal
       approximately 3.1 miles from both the Beaver Creek Trail head and
       Spirit Lake".

B. Five GR- lakes filed "Sheep/Carter" that belong to Beaver Creek.
   (a) All five are printed in the Smiths Fork/Henrys Fork/Beaver Creek
       booklet, not the Sheep/Carter one.
   (b) They are the only non-Beaver rows inside the unbroken GR-144..GR-179
       Beaver Creek run.
   (d) GR-176 Utanna (40.9309, -110.2278) sits among GR-172/173/175
       (40.920-40.925, -110.22 to -110.23); the nearest genuine Sheep/Carter
       lake is ~20 km east. The other four have no coordinates.

C. Two G- lakes filed "Henrys Fork" that belong to Blacks Fork.
   (a) The Bear River/Blacks Fork booklet prints G-25,26,27,37,65..87,90,102;
       the Smiths/Henrys/Beaver booklet prints G-1..64 and G-92..103. G-87
       and G-90 appear only in the former.
   (b) G-65..G-86 are all Blacks Fork in the DB and G-92+ resumes
       Smiths/Henrys — these two are the only Henrys Fork rows in that run.
   Both are "does not sustain fish life / landmark only" rows with no
   coordinates, so the user-visible impact is only the drainage label.

────────────────────────────────────────────────────────────────────────────
PART 2 — four damaged stocking records
────────────────────────────────────────────────────────────────────────────
Four records entered through a different, lower-quality import path than the
other 7,341. All four share the same three defects — a Jan-1 placeholder date,
a zero length, and a mixed-case county string ('Summit' not 'SUMMIT') — and
they are the ONLY records in the table with any of them. The real values are
recoverable from data/dwr_archive (statewide, 2002-2026, complete at ~700
Uinta-county records/year), matched on designation + species + quantity:

    WR-2   1274 Cutthroats   2009-01-01 / 0.0 / 'Summit'
                          -> 2009-09-16 / 1.43 / 'DUCHESNE'
    D-45    448 Tigers       2010-01-01 / 0.0 / 'Duchesne'
                          -> 2010-07-13 / 2.34 / 'DUCHESNE'
    GR-129  493 Brookies     2012-01-01 / 0.0 / 'Summit'
                          -> 2012-08-06 / 2.68 / 'SUMMIT'
    D-45    450 Tigers       2013-01-01 / 0.0 / 'Duchesne'
                          -> 2013-07-08 / 3.08 / 'DUCHESNE'

Note on WR-2: the archive prints that 2009 row as "RC- 1", not "R C NO 1 LAKE
WR-2" like its 2013/2017/2024 rows. It is the same lake, not Rock Creek's
RC-1: the DB has no RC-1, the Rock Creek booklet never mentions one, the
county matches, and 1274 sits squarely in WR-2's own dose series (1227, 1197,
1274) on a clean four-year cutthroat cycle (2009, 2013, 2017, 2024). DWR
simply abbreviated the NAME "R.C. No. 1" that year. Spaced designations like
this are common in the archive (51 distinct ones: "G- 51", "U- 79", ...).
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import writer_guard  # noqa: E402

DB = Path(__file__).resolve().parent.parent / "uinta_lakes.db"

DRAINAGE_FIXES = [
    # (designation, expected current drainage, corrected drainage)
    *[(d, "Ashley Creek Drainage", "Sheep/Carter Creek Drainages") for d in
      ("GR-5", "GR-11", "GR-13", "GR-15", "GR-16", "GR-19",
       "GR-20", "GR-21", "GR-23", "GR-24", "GR-104")],
    *[(d, "Sheep/Carter Creek Drainages", "Beaver Creek Drainage") for d in
      ("GR-156", "GR-157", "GR-168", "GR-169", "GR-176")],
    *[(d, "Henrys Fork Drainage", "Blacks Fork Drainage") for d in
      ("G-87", "G-90")],
]

# (designation, species, quantity) -> (correct stock_date, length, county)
STOCKING_FIXES = {
    ("WR-2", "Cutthroats", 1274): ("2009-09-16", 1.43, "DUCHESNE"),
    ("D-45", "Tigers", 448):      ("2010-07-13", 2.34, "DUCHESNE"),
    ("GR-129", "Brookies", 493):  ("2012-08-06", 2.68, "SUMMIT"),
    ("D-45", "Tigers", 450):      ("2013-07-08", 3.08, "DUCHESNE"),
}


def fix_drainages(conn):
    cur = conn.cursor()
    changed = skipped = 0
    for desig, expect, correct in DRAINAGE_FIXES:
        row = cur.execute(
            "SELECT id, drainage FROM lakes WHERE letter_number = ?", (desig,)
        ).fetchone()
        if row is None:
            raise SystemExit(f"ABORT: {desig} not in lakes")
        lake_id, current = row
        if current == correct:
            print(f"    {desig:8s} already {correct}")
            skipped += 1
            continue
        if current != expect:
            # The DB moved since this script was written — stop rather than
            # overwrite a decision someone else made.
            raise SystemExit(
                f"ABORT: {desig} is {current!r}, expected {expect!r}; review by hand")
        cur.execute("UPDATE lakes SET drainage = ? WHERE id = ?", (correct, lake_id))
        print(f"    {desig:8s} {expect:30s} -> {correct}")
        changed += 1
    conn.commit()
    return changed, skipped


def fix_stocking(conn):
    cur = conn.cursor()
    changed = skipped = 0
    for (desig, species, qty), (date, length, county) in STOCKING_FIXES.items():
        rows = cur.execute("""
            SELECT s.id, s.stock_date, s.length, s.county
            FROM stocking_records s JOIN lakes l ON l.id = s.lake_id
            WHERE l.letter_number = ? AND s.species = ? AND s.quantity = ?
        """, (desig, species, qty)).fetchall()
        if len(rows) != 1:
            raise SystemExit(
                f"ABORT: {desig}/{species}/{qty} matched {len(rows)} records, expected 1")
        rec_id, old_date, old_len, old_county = rows[0]
        if (old_date, old_len, old_county) == (date, length, county):
            print(f"    {desig:8s} {species:11s} already repaired")
            skipped += 1
            continue
        # Only ever repair a record still showing the damaged signature.
        if not (old_date.endswith("-01-01") and not old_len):
            raise SystemExit(
                f"ABORT: {desig}/{species}/{qty} is {old_date}/{old_len}, "
                f"not the placeholder signature; review by hand")
        cur.execute(
            "UPDATE stocking_records SET stock_date = ?, length = ?, county = ? WHERE id = ?",
            (date, length, county, rec_id))
        print(f"    {desig:8s} {species:11s} {old_date}/{old_len}/{old_county:8s}"
              f" -> {date}/{length}/{county}")
        changed += 1
    conn.commit()
    return changed, skipped


def main():
    writer_guard.exit_if_readonly()
    conn = sqlite3.connect(DB)
    try:
        print("Drainage corrections:")
        dc, ds = fix_drainages(conn)
        print("\nStocking-record repairs:")
        sc, ss = fix_stocking(conn)
    finally:
        conn.close()
    print(f"\n{dc} drainages changed ({ds} already correct), "
          f"{sc} stocking records repaired ({ss} already correct).")
    print("Now run: python3 scripts/export_web_data.py")


if __name__ == "__main__":
    main()
