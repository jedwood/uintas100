#!/usr/bin/env python3
"""
Split creek/pond/"fringe" stockings out of the lakes data.

Historically the stocking matcher used loose substring matching, which mis-filed
creek and pond stockings onto same-named lakes (e.g. "BEAVER CR" -> BR-10 Beaver,
the Oweep Cr tributaries -> LF-30 Oweep). The matcher is now conservative
(scripts/database_utils.find_matching_lake), so this one-time migration cleans up
the records that were already inserted under the old behaviour:

  1. create the other_waters / other_stocking_records tables (via create_database),
  2. rebuild those tables from data/utah_dwr_stocking_data.csv using the new
     classifier (find_matching_lake = real lake; find_fringe_water = creek/pond
     with a likely drainage borrowed from a namesake lake),
  3. delete the mis-filed creek/pond rows from stocking_records,
  4. refresh fish_species for the affected lakes.

Idempotent: the other_* tables are rebuilt from scratch and the stocking_records
cleanup is a no-op on re-run. Dry run by default; pass 'apply' to write.

    python3 scripts/migrate_fringe_waters.py          # dry run
    python3 scripts/migrate_fringe_waters.py apply     # apply
"""
import csv
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from database_utils import (
    create_database,
    find_matching_lake,
    find_fringe_water,
    upsert_other_water,
    other_stocking_exists,
)
from species_utils import standardize_stocking_species, update_lake_fish_species

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(PROJECT_DIR, "data", "utah_dwr_stocking_data.csv")


def to_iso(date_str):
    return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    conn = create_database()
    cur = conn.cursor()

    designation_to_id = {
        d: i for i, d in cur.execute(
            "SELECT id, letter_number FROM lakes WHERE letter_number IS NOT NULL"
        )
    }

    # Classify each DISTINCT water name once.
    waters = defaultdict(list)
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            waters[r["water_name"].strip()].append(r)

    classification = {}  # water_name -> ('lake', lake_id) | ('fringe', info) | ('none', None)
    for water in waters:
        lake_id, _, _ = find_matching_lake(cur, water)
        if lake_id:
            classification[water] = ("lake", lake_id)
            continue
        info = find_fringe_water(cur, water)
        classification[water] = ("fringe", info) if info else ("none", None)

    # Build per-lake tuple sets so we never delete a stocking that is *also* a
    # legitimate lake stocking (collision safety).
    legit_tuples = defaultdict(set)   # lake_id -> {(species, qty, iso_date)}
    fringe_tuples = defaultdict(set)  # namesake lake_id -> {(species, qty, iso_date)}
    fringe_rows = defaultdict(list)   # water_name -> [csv rows]

    for water, rows in waters.items():
        kind, payload = classification[water]
        for r in rows:
            sp = standardize_stocking_species(r["species"].strip())
            try:
                key = (sp, int(r["quantity"]), to_iso(r["stock_date"].strip()))
            except (ValueError, KeyError):
                continue
            if kind == "lake":
                legit_tuples[payload].add(key)
            elif kind == "fringe":
                inferred = payload["inferred_from"].split(" ", 1)[0]
                nid = designation_to_id.get(inferred)
                if nid is not None:
                    fringe_tuples[nid].add(key)
                fringe_rows[water].append(r)

    # ---- report ----
    n_fringe_waters = len(fringe_rows)
    n_fringe_rows = sum(len(v) for v in fringe_rows.values())
    to_delete = 0
    for lid, fset in fringe_tuples.items():
        to_delete += len(fset - legit_tuples.get(lid, set()))

    print(f"Fringe waters:               {n_fringe_waters}")
    print(f"Fringe stocking rows (CSV):  {n_fringe_rows}")
    print(f"Mis-filed rows to remove from stocking_records: {to_delete}")
    affected = sorted(fringe_tuples.keys())
    print(f"Affected lakes (fish_species refresh): {len(affected)}")

    if not apply:
        print("\n*** DRY RUN — pass 'apply' to write changes ***")
        conn.close()
        return

    # ---- rebuild other_waters / other_stocking_records ----
    cur.execute("DELETE FROM other_stocking_records")
    cur.execute("DELETE FROM other_waters")

    for water, rows in fringe_rows.items():
        info = classification[water][1]
        county = Counter(r["county"].strip().title() for r in rows).most_common(1)[0][0]
        wid = upsert_other_water(cur, water, info, county=county)
        for r in rows:
            sp = standardize_stocking_species(r["species"].strip())
            try:
                qty = int(r["quantity"])
                iso = to_iso(r["stock_date"].strip())
                length = float(r["length"]) if r.get("length") else None
                year = int(r.get("source_year") or iso[:4])
            except (ValueError, KeyError):
                continue
            if other_stocking_exists(cur, wid, sp, qty, iso):
                continue
            cur.execute(
                """INSERT INTO other_stocking_records
                   (water_id, county, species, quantity, length, stock_date, source_year)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (wid, r["county"].strip(), sp, qty, length, iso, year),
            )

    # ---- remove mis-filed rows from stocking_records ----
    removed = 0
    for lid, fset in fringe_tuples.items():
        for sp, qty, iso in (fset - legit_tuples.get(lid, set())):
            cur.execute(
                """DELETE FROM stocking_records
                   WHERE lake_id = ? AND species = ? AND quantity = ? AND stock_date = ?""",
                (lid, sp, qty, iso),
            )
            removed += cur.rowcount

    # ---- refresh fish_species on affected lakes ----
    for lid in affected:
        update_lake_fish_species(cur, lid)

    conn.commit()
    print(f"\nApplied: removed {removed} mis-filed stocking rows; "
          f"rebuilt {n_fringe_waters} other_waters with their stockings.")
    conn.close()


if __name__ == "__main__":
    main()
