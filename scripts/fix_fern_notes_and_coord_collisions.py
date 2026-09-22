#!/usr/bin/env python3
"""One-off: attach Fern's stranded DWR write-up, refile GR-119, and unstick
six lakes that were all seeded onto a same-named neighbour's coordinates.

Run once, then re-export:  python3 scripts/export_web_data.py

────────────────────────────────────────────────────────────────────────────
PART 1 — X-5 Fern's missing DWR write-up
────────────────────────────────────────────────────────────────────────────
The Rock Creek pamphlet prints Fern's entry under the heading "FERN, X-58".
X-58 is already Swasey (Yellowstone) and has its own, different write-up, so
the notes import had nowhere to put this one and simply dropped it, leaving
X-5 with empty dwr_notes. Jed has since checked the pamphlet MAP and confirmed
the printed designation is the typo: the lake described is X-5.

The text corroborates that independently — it states 19.3 acres and 19 feet
maximum depth, which is exactly what X-5 already carries from the Norrick
data (X-58 Swasey is 24.6 acres / 36 feet). It also matches X-5's existing
fish_species ('Brookies', text: "stocked brook trout") and fishing_pressure
('Moderate', text: "Fishing pressure is moderate").

So this copies the write-up onto X-5, sets dwr_edition to 1997 (the Rock Creek
original, per ORIGINAL_EDITION in backfill_dwr_editions.py), and fills in the
elevation the text gives (9,890 ft) which X-5 was missing. Swasey is not
touched. The text is read straight out of the committed OCR rather than
retyped here, so it cannot drift from the source.

────────────────────────────────────────────────────────────────────────────
PART 2 — GR-119 refiled to Sheep/Carter
────────────────────────────────────────────────────────────────────────────
GR-119 is certainly not Ashley Creek: DWR reports it in SUMMIT county (Ashley
is overwhelmingly UINTAH), it sits outside Ashley's GR-34..77 block, and the
Ashley pamphlet never mentions it. Between the two live candidates the
evidence is genuinely split — number-block contiguity says Sheep/Carter
(GR-101..116), while its 2007 grayling plant arrived with the Burnt Fork trio
Snow/Round/Kabell. Jed's call: Sheep/Carter.

────────────────────────────────────────────────────────────────────────────
PART 3 — six lakes sharing a neighbour's coordinates
────────────────────────────────────────────────────────────────────────────
Four coordinate points each had 2-3 lakes stacked on them, because the OSM
seeder matched on NAME and the Uintas reuse names freely. In every group
exactly one lake genuinely belongs at the point; the others were dragged there.

Each winner was identified from the DWR write-up's own landmark and confirmed
against GNIS (data/gnis/DomesticNames_UT.txt):

  40.72219,-110.87580  Castle x3 -> D-14 (Duchesne) KEEPS it.
      D-14's text: "3/8 mile west of Butterfly Lake". Butterfly (Z-1) is
      0.44 mi away. GNIS "Castle Lake, Duchesne" = 40.7221125,-110.8757862,
      i.e. this exact point.
      W-67 (Weber) is "6 miles north of U-150 on the Upper Setting Road" at
      9,860 ft; G-11 (Henrys Fork) is "above timberline in the Henrys Fork
      Basin" at 11,363 ft and sits 25 mi from its nearest drainage-mate.

  40.84349,-110.01446  Hidden x3 -> GR-112 (Sheep/Carter) KEEPS it.
      GR-112's text: "0.8 miles northwest of the Spirit Lake campground";
      Spirit Lake (GR-3) is 0.81 mi away, and its write-up even warns it is
      "not to be confused with another water of the same name in Weyman Lake
      Basin". GNIS "Hidden Lake, Summit" = 40.8433468,-110.0144146.
      GR-7 belongs 0.7 mi NW of Lower Anson in Weyman Basin; GR-149 belongs
      1/2 mile north of Long Meadow in Beaver Creek's Middle Fork, 10.3 mi
      from the point.

  40.72427,-110.64029  Crater x2 -> X-94 (Lake Fork) KEEPS it.
      X-94's text: "northeast base of Explorer Peak"; GNIS Explorer Peak =
      40.7181748,-110.6440433, putting the point 0.44 mi NNE of it. GNIS lists
      exactly one "Crater Lake" in Duchesne, at 40.7240451,-110.6399448.
      LF-2 "sits next to the trail in Lambert Meadows" (GNIS Lambert Meadow,
      Duchesne = 40.7352226,-110.5857204), ~3 mi ENE, and is a different lake
      entirely: 40.7 acres/20 ft vs X-94's 28 acres/147 ft.

  40.80007,-110.21928  Lily x2 -> U-23 (Uinta River) KEEPS it.
      U-23's text: "about 1/2 mile northeast of the Kidney lakes"; GNIS
      "Kidney Lakes, Duchesne" = 40.7991146,-110.2287945, exactly 0.5 mi SW.
      S-15 (Swift Creek) is 8.75 mi from its nearest drainage-mate here.

The six losers keep their (already correct) drainage; only the borrowed
coordinates are cleared — lat, lng, coord_source and coord_status all set to
NULL, which is what a never-placed lake looks like, so they surface under the
Lake Locator's "Unplaced only" / "Needs work" filters for manual placement.
Deliberately NOT re-seeded to a guessed position, per Jed.

For reference when placing them, GNIS offers these candidates (unverified —
they are hints for the Locator, not applied here):
    W-67 Castle    -> "Castle Lake", Summit   40.6713265,-111.1253178
    G-11 Castle    -> "Castle Lake", Summit   40.8147123,-110.4134593
    GR-149 Hidden  -> "Hidden Lake", Summit   40.8791019,-110.2284800
    S-15 Lily      -> "Lily Lake",   Duchesne 40.6985323,-110.2221593
    GR-7 Hidden    -> no GNIS match; text puts it 0.7 mi NW of Lower Anson
    LF-2 Crater    -> no GNIS match; text puts it in Lambert Meadows
"""

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import writer_guard  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "uinta_lakes.db"
ROCK_CREEK_OCR = REPO / "data" / "ocr" / "uintas_rock_creek_ocr_text.txt"

FERN_HEADING = "FERN, X-58"      # the pamphlet's typo; the lake is X-5
FERN_TARGET = "X-5"
FERN_EDITION = 1997              # Rock Creek original, per ORIGINAL_EDITION
FERN_ELEVATION = 9890

GR119 = ("GR-119", "Ashley Creek Drainage", "Sheep/Carter Creek Drainages")

# point -> (designation that keeps it, designations to clear)
COORD_COLLISIONS = [
    ("Castle", "D-14",   ["W-67", "G-11"]),
    ("Hidden", "GR-112", ["GR-7", "GR-149"]),
    ("Crater", "X-94",   ["LF-2"]),
    ("Lily",   "U-23",   ["S-15"]),
]


def fern_text():
    """Pull Fern's write-up out of the committed pamphlet OCR."""
    lines = ROCK_CREEK_OCR.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines):
        if line.strip() == FERN_HEADING:
            body = lines[i + 1].strip()
            if not body or len(body) < 200:
                raise SystemExit(f"ABORT: text under {FERN_HEADING!r} looks wrong: {body[:80]!r}")
            return body
    raise SystemExit(f"ABORT: heading {FERN_HEADING!r} not found in {ROCK_CREEK_OCR.name}")


def fix_fern(conn):
    text = fern_text()
    # Sanity-check the text really is Fern's and really describes X-5's lake.
    if "19.3 acres" not in text or "19 feet maximum depth" not in text:
        raise SystemExit("ABORT: Fern text lacks the 19.3-acre / 19-foot figures that identify X-5")
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, name, size_acres, max_depth_ft, dwr_notes FROM lakes WHERE letter_number = ?",
        (FERN_TARGET,)).fetchone()
    if row is None:
        raise SystemExit(f"ABORT: {FERN_TARGET} not in lakes")
    lake_id, name, acres, depth, existing = row
    if name != "Fern":
        raise SystemExit(f"ABORT: {FERN_TARGET} is named {name!r}, not 'Fern'")
    if (acres, depth) != (19.3, 19):
        raise SystemExit(f"ABORT: {FERN_TARGET} is {acres} acres/{depth} ft, not 19.3/19 — recheck")
    if existing and existing.strip():
        if existing.strip() == text:
            print(f"    {FERN_TARGET} Fern: already applied")
            return 0
        raise SystemExit(f"ABORT: {FERN_TARGET} already has different dwr_notes; review by hand")
    cur.execute(
        "UPDATE lakes SET dwr_notes = ?, dwr_edition = ?, elevation_ft = COALESCE(elevation_ft, ?) "
        "WHERE id = ?", (text, FERN_EDITION, FERN_ELEVATION, lake_id))
    conn.commit()
    print(f"    {FERN_TARGET} Fern: applied {len(text)} chars, edition {FERN_EDITION}, elev {FERN_ELEVATION}")
    return 1


def fix_gr119(conn):
    desig, expect, correct = GR119
    cur = conn.cursor()
    row = cur.execute("SELECT id, drainage FROM lakes WHERE letter_number = ?", (desig,)).fetchone()
    if row is None:
        raise SystemExit(f"ABORT: {desig} not in lakes")
    lake_id, current = row
    if current == correct:
        print(f"    {desig}: already {correct}")
        return 0
    if current != expect:
        raise SystemExit(f"ABORT: {desig} is {current!r}, expected {expect!r}")
    cur.execute("UPDATE lakes SET drainage = ? WHERE id = ?", (correct, lake_id))
    conn.commit()
    print(f"    {desig}: {expect} -> {correct}")
    return 1


def fix_collisions(conn):
    cur = conn.cursor()
    cleared = 0
    for label, keeper, losers in COORD_COLLISIONS:
        pt = cur.execute("SELECT lat, lng FROM lakes WHERE letter_number = ?", (keeper,)).fetchone()
        if pt is None or pt[0] is None:
            raise SystemExit(f"ABORT: keeper {keeper} has no coordinates")
        print(f"    {label}: {keeper} keeps {pt[0]:.5f},{pt[1]:.5f}")
        for loser in losers:
            row = cur.execute(
                "SELECT id, lat, lng FROM lakes WHERE letter_number = ?", (loser,)).fetchone()
            if row is None:
                raise SystemExit(f"ABORT: {loser} not in lakes")
            lake_id, lat, lng = row
            if lat is None:
                print(f"        {loser}: already unplaced")
                continue
            # Only clear a lake still sitting on the keeper's exact point.
            if (round(lat, 6), round(lng, 6)) != (round(pt[0], 6), round(pt[1], 6)):
                raise SystemExit(
                    f"ABORT: {loser} is at {lat},{lng}, no longer on {keeper}'s point — "
                    "someone has already moved it; review by hand")
            cur.execute(
                "UPDATE lakes SET lat=NULL, lng=NULL, coord_source=NULL, coord_status=NULL "
                "WHERE id = ?", (lake_id,))
            print(f"        {loser}: cleared -> unplaced (drainage unchanged)")
            cleared += 1
    conn.commit()
    return cleared


def main():
    writer_guard.exit_if_readonly()
    conn = sqlite3.connect(DB)
    try:
        print("X-5 Fern write-up:")
        f = fix_fern(conn)
        print("\nGR-119 drainage:")
        g = fix_gr119(conn)
        print("\nCoordinate collisions:")
        n = fix_collisions(conn)
    finally:
        conn.close()
    print(f"\nFern: {f} applied; GR-119: {g} changed; {n} lakes cleared for manual placement.")
    print("Now run: python3 scripts/export_web_data.py")


if __name__ == "__main__":
    main()
