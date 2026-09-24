#!/usr/bin/env python3
"""One-off corrections for data problems found by the less-visited-lakes pass
(2026-09-23). See docs/less-visited-lakes.md -> "Data issues this turned up".

Four corrections, each sourced against committed source files:

1. GR-28 Upper Potter physical fields + pressure.
   The DB held 4.3 acres / 28 ft / High. Both independent sources agree it is
   21.3 acres / 75 ft / Low:
     - data/norrick_lakes.txt:353 "Potter, Upper, GR-28  21.3  75  ...  Low"
     - its own dwr_notes (1996): "Upper Potter Lake is 21.3 acres, 10,130 feet
       in elevation with a maximum depth of 75 feet ... Fishing pressure is
       light."
   The stored values matched NEITHER source, i.e. a transcription error.

2. WR-40 Wooley fishing_pressure Moderate -> Low.
   Every other physical field on this record is taken verbatim from the 2025
   pamphlet ("sits at 10,680 feet ... 20.5 surface acres with a maximum depth
   of 42 feet"), which also says "fishing pressure is light". Only the pressure
   field was left at the older Norrick value (18 ac / 42 ft / Moderate), so the
   record was internally inconsistent about its own source edition.

3. X-77 -> X-49: move a misattributed Andersen paragraph.
   CMA p.326 prints "TWIN (X-77): Access is 3/4 mile northwest of White Miller
   ... 10,816 ft. elevation, 14 acres, 15' deep ... Cutthroat trout". Those
   numbers are an exact match for X-49 Twin (Swift Creek, 14.0 ac / 15 ft /
   10,816 ft, Cutthroats), and White Miller (X-54) and Farmers (X-23) are both
   Swift Creek. Lake Fork's X-77 Twin is a different lake (12.9 ac / 15 ft /
   10,594 ft, Grayling). The book misprinted the designation; the importer
   filed the paragraph on X-77, which had been showing a stranger's stats in
   the PWA modal. X-49 had no cma_notes at all.

4. G-73 -> U-73: same class of error.
   CMA p.292 prints "MILK (G-73): ... At 11,236 ft. elevation, 13.1 acres,
   35' deep ... Abundant Cutthroat trout, rarely fished." Exact match for U-73
   Milk (Uinta River, 13.1 ac / 35 ft / 11,236 ft). A G/U designation typo.
   The surrounding U-80/U-81/U-83 sentences in the same block are Uinta lakes
   too, so the whole p.292 block moves. U-73 had no cma_notes.

Deliberately NOT changed:
  - X-121 Continent pressure. Norrick says Moderate, the 1997 pamphlet says
    light, and the physical fields match both. Two contemporaneous independent
    sources disagree and there is no basis to prefer one; overwriting would
    manufacture false confidence. Documented in the report instead.
  - Missing elevation/acreage/depth on the 15 undescribed lakes (RC-36, U-100,
    U-91, U-79, U-22 ...). No source exists: they are absent from
    norrick_lakes.txt and from dwr_lake_summary. Left NULL rather than invented.
  - Name collisions (U-99 Wall vs A-29 Wall; the four "Hidden" lakes). These
    are what the sources genuinely call them, not an error.

Idempotent: re-running reports 0 changes.
"""
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
DB = REPO / "uinta_lakes.db"

# The paragraph CMA printed under "TWIN (X-77)" but which describes X-49.
X77_MISFILED_SENTENCE = (
    "TWIN (X-77): Access is 3/4 mile northwest of White Miller over a rocky, "
    "timbered ridge, 10,816 ft. elevation, 14 acres, 15' deep, horse friendly, "
    "a productive lake with Cutthroat trout."
)
X49_NOTE = (
    "TWIN (X-49): Access is 3/4 mile northwest of White Miller over a rocky, "
    "timbered ridge, 10,816 ft. elevation, 14 acres, 15' deep, horse friendly, "
    "a productive lake with Cutthroat trout. *(p. 326)*\n\n"
    "[Editor's note: the book prints this entry as \"TWIN (X-77)\", but the "
    "stats and the White Miller reference identify it as X-49 in Swift Creek; "
    "X-77 Twin is a different lake in Lake Fork.]"
)


def main():
    try:
        from writer_guard import exit_if_readonly
        exit_if_readonly()
    except ImportError:
        if (REPO / ".db-readonly").exists():
            sys.exit("refusing to write: .db-readonly marker present")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    changes = []

    def get(desig, col):
        row = conn.execute(
            f"SELECT {col} AS v FROM lakes WHERE letter_number = ?", (desig,)
        ).fetchone()
        if row is None:
            sys.exit(f"lake {desig} not found")
        return row["v"]

    def set_field(desig, col, new, why):
        old = get(desig, col)
        if old == new:
            return
        conn.execute(
            f"UPDATE lakes SET {col} = ? WHERE letter_number = ?", (new, desig)
        )
        changes.append(f"{desig}.{col}: {old!r} -> {new!r}   ({why})")

    # 1. GR-28 Upper Potter — matched neither Norrick nor its own DWR text.
    set_field("GR-28", "size_acres", 21.3, "norrick_lakes.txt:353 + dwr_notes 1996")
    set_field("GR-28", "max_depth_ft", 75, "norrick_lakes.txt:353 + dwr_notes 1996")
    set_field("GR-28", "fishing_pressure", "Low", "norrick 'Low' + dwr_notes 'pressure is light'")

    # 2. WR-40 Wooley — record is 2025-sourced everywhere except pressure.
    set_field("WR-40", "fishing_pressure", "Low", "dwr_notes 2025 'fishing pressure is light'")

    # 3. X-77 -> X-49 misattributed Andersen paragraph.
    x77 = get("X-77", "cma_notes") or ""
    if X77_MISFILED_SENTENCE in x77:
        cleaned = x77.replace(X77_MISFILED_SENTENCE, "").replace("  ", " ").strip()
        conn.execute(
            "UPDATE lakes SET cma_notes = ? WHERE letter_number = 'X-77'", (cleaned,)
        )
        changes.append(
            "X-77.cma_notes: removed the 'TWIN (X-77)' paragraph "
            "(describes X-49; surrounding-paragraph bleed left intact, as on 92 other records)"
        )
    if not (get("X-49", "cma_notes") or "").strip():
        conn.execute(
            "UPDATE lakes SET cma_notes = ? WHERE letter_number = 'X-49'", (X49_NOTE,)
        )
        changes.append("X-49.cma_notes: added the Andersen entry that actually describes it")

    # 4. G-73 -> U-73 misattributed Andersen block (the p. 292 block).
    g73 = get("G-73", "cma_notes") or ""
    marker = "\n\nLAKE U-81:"
    if marker in g73 and "MILK (G-73)" in g73:
        keep, moved = g73.split(marker, 1)
        moved = ("LAKE U-81:" + moved).strip()
        moved_fixed = moved.replace("MILK (G-73):", "MILK (U-73):")
        moved_fixed += (
            "\n\n[Editor's note: the book prints this entry as \"MILK (G-73)\"; "
            "the stats and location identify it as U-73 in the Uinta River "
            "drainage. G-73 is Bob's Lake in Blacks Fork.]"
        )
        conn.execute(
            "UPDATE lakes SET cma_notes = ? WHERE letter_number = 'G-73'", (keep.strip(),)
        )
        changes.append("G-73.cma_notes: removed the p.292 block (U-80/81/83 + 'MILK (G-73)')")
        if not (get("U-73", "cma_notes") or "").strip():
            conn.execute(
                "UPDATE lakes SET cma_notes = ? WHERE letter_number = 'U-73'", (moved_fixed,)
            )
            changes.append("U-73.cma_notes: added the Andersen Milk Lake entry")

    conn.commit()

    if changes:
        print(f"{len(changes)} change(s) applied:")
        for c in changes:
            print(f"  - {c}")
    else:
        print("no changes needed (already applied)")
    conn.close()


if __name__ == "__main__":
    main()
