#!/usr/bin/env python3
"""Load chemical (rotenone) reclamation projects into lake_treatments.

Idempotent: re-running replaces every row this script owns and reports no net
change. Only projects that actually included a *lettered lake* belong here —
stream-only treatments (e.g. North Fork Sheep Creek, 2026) are out of scope.

One row per lake x treatment APPLICATION, not per project: DWR's standard
protocol is two or three treatments a year apart before restocking, and the
per-year detail is the interesting part. A lake treated three times has three
rows.

Every row must be traceable to a primary source. The quotes that justify the
contents are reproduced beside each project so a future reader can re-check
them without re-doing the research. Where two DWR sources disagree on dates
(a forecast news release vs. a post-hoc WRI completion report) both are cited
and the discrepancy is recorded in the note rather than silently resolved.

Provenance note: the 10 pre-2026 lakes here carried a hand-curated
"ROTENONE TREATED" banner in dwr_notes long before this table existed, with no
citation. Those banners were the starting point; every project was then
re-sourced from DWR news releases and Utah WRI project reports, which corrected
the Fall Creek entries — see that block.
"""

import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from database_utils import create_database  # noqa: E402

DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")

USFS = "UDWR + USFS"
NONNATIVE = "Brook trout, nonnative cutthroat, rainbow trout"
CRCT = "Cutthroats"

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

# West Fork Smiths Fork — UDWR Northern Region technical reports.
#   2021, p. 45: "A large crew of personnel from UDWR and USFS applied rotenone
#   to the West Fork Smiths Fork drainage over a three-day period, August
#   30-September 1, 2021... totaling approximately 32.0 km of stream, plus Lake
#   G-64 (1.44 ha) and a small unnamed pond (0.26 ha) were targeted."
#   2023, p. 52: "a small headwater lake, G-113, which was also part of the
#   rotenone treatment, was stocked with approximately 270 fingerling CRCT."
SRC_WFSF_21 = "UDWR, Native Cutthroat Trout Conservation Activities in the Northern Region, 2021, p. 45"
SRC_WFSF_23 = "UDWR, Cutthroat Trout Report, Northern Region, 2023, p. 52"
URL_WFSF_21 = ("https://web.archive.org/web/20250611224207/https://wildlife.utah.gov/pdf/fish/"
               "technical-reports/native_cutthroat_trout_conservation_activities_in_the_northern_region_2021.pdf")
URL_WFSF_23 = ("https://web.archive.org/web/20251010092535/https://wildlife.utah.gov/pdf/fish/"
               "technical-reports/cutthroat_trout_report,_northern_region_2023.pdf")

# Carter Creek 2021 — UDWR news release, 9 Aug 2021:
#   "From Aug. 17-25, the DWR will chemically treat the following locations with
#   rotenone: East Fork Carter Creek above the Sheep Creek canal / Ram, Mutton
#   and Bummer lakes / West Fork Carter Creek above the Sheep Creek canal"
#   "The treatments will remove any remaining brook trout in the streams."
SRC_CC21 = "UDWR news release, 9 Aug 2021, 'Stream treatments to benefit cutthroat trout in High Uintas'"
URL_CC21 = ("https://web.archive.org/web/20210809183917/https://wildlife.utah.gov/news/"
            "utah-wildlife-news/1246-stream-treatments-in-high-uintas-benefit-cutthroat-trout.html")

# Carter Creek 2023 — UDWR news release, 16 May 2023:
#   "Daggett, Penguin, Upper Anson and Lower Anson lakes (north slope) from
#   Aug. 28-29."
# and Utah WRI project 6834 (helicopter support), which gives the day-by-day:
#   "On Monday, we had three lakes and a few stream segments that needed to be
#   treated... On Tuesday, we treated Daggett Lake and all inflowing and
#   outflowing segments from Daggett."
SRC_CC23 = "UDWR news release, 16 May 2023 + Utah WRI project 6834 completion report"
URL_CC23 = ("https://web.archive.org/web/20230524000625/https://wildlife.utah.gov/news/"
            "utah-wildlife-news/1654-upcoming-waterbody-treatments-in-high-uintas-to-help-"
            "restore-native-cutthroat-trout.html")
URL_WRI6834 = "https://wri.utah.gov/wri/reports/ProjectSummaryReport.html?id=6834"

# Oweep Creek — three treatments. News releases 21 Jul 2022, 16 May 2023,
# 2 Jul 2024, plus Utah WRI 6665 (Phase II) and 6893 (Phase III). WRI 6893:
#   "DWR started the first project (Oweep Creek) in 2022 with our first rotenone
#   treatment and followed the initial treatment up with a second treatment in
#   2023. This project supported a final, third... follow-up treatment."
SRC_OW22 = "UDWR news release, 21 Jul 2022"
URL_OW22 = ("https://web.archive.org/web/20220721200524/https://wildlife.utah.gov/news/"
            "utah-wildlife-news/1471-dwr-ashley-national-forest-reminds-public-to-stay-out-"
            "during-stream-treatments-in-high-unitas.html")
SRC_OW23 = "UDWR news release, 16 May 2023 + Utah WRI project 6665 (Phase II)"
URL_OW23 = "https://wri.utah.gov/wri/reports/ProjectSummaryReport.html?id=6665"
SRC_OW24 = "UDWR news release, 2 Jul 2024 + Utah WRI project 6893 (Phase III)"
URL_OW24 = "https://wri.utah.gov/wri/reports/ProjectSummaryReport.html?id=6893"

# Fall Creek — Utah WRI 7370 objectives: "Eradicating current fish populations
# in Anderson and Phinney Lakes" and "Eradicating all fish populations upstream
# of the natural waterfall barrier". Second treatment confirmed in the same
# report's completion narrative and in the 2026 news release.
SRC_FC25 = "UDWR news release, 22 Jul 2025 + Utah WRI project 7370"
URL_FC25 = "https://wri.utah.gov/wri/reports/ProjectSummaryReport.html?id=7370"
SRC_FC26 = "UDWR news release, 28 Jul 2026"
URL_FC26 = ("https://wildlife.utah.gov/news/2026/07/28/dwr-conducting-waterbody-treatments-"
            "in-high-uintas-to-help-restore-native-cutthroat-trout")

CC_CAVEAT = ("DWR's own sources call GR-6/9/10/16 'north slope' lakes and never assign them to "
             "Carter Creek by name; 'Carter Creek project' is this repo's grouping, kept for "
             "continuity with the PWA's rotenone modal.")
LAMB_CAVEAT = ("Naming trap: DWR's 2022 release calls the 2021 trio 'Lamb, Mutton and Ram lakes' "
               "where the 2021 release said 'Bummer'. Lamb Lakes is the basin. Do not read "
               "'Lamb Lake' as a fourth treated lake.")


def T(ln, project, start, end, source, url, note, target=NONNATIVE,
      restored=CRCT, unit=None, agency=USFS):
    return dict(letter_number=ln, printed_name=ln, project_name=project,
                water_unit=unit, treatment_type="rotenone", agency=agency,
                start_date=start, end_date=end, target_species=target,
                restored_species=restored, note=note, source=source, source_url=url)


RECORDS = [
    # --- West Fork Smiths Fork (Northern Region) ---------------------------
    T("G-64", "West Fork Smiths Fork project", "2021-08-30", "2021-09-01",
      SRC_WFSF_21, URL_WFSF_21, unit="IICK020B",
      agency="UDWR + USFS (Uinta-Wasatch-Cache NF)", restored="Tigers",
      target="Nonnative trout (rainbow and hybridized cutthroat per the USFS decision memo)",
      note=("Named outright in the 2021 report as 'Lake G-64 (1.44 ha)' — 3.56 acres, against "
            "the 1986 pamphlet's 3.4. NOT a cutthroat water afterward: the biennial tiger trout "
            "program resumed 2022-06-28 and continues (2024, 2026). The USFS decision memo "
            "explains why — tigers are stocked at the downstream, non-wilderness end of the "
            "project area to hold a fishery while CRCT expand, to be dropped once CRCT establish. "
            "Neutralized at a barrier UDWR installed in 2006 near the Wyoming border.")),
    T("G-113", "West Fork Smiths Fork project", "2021-08-30", "2021-09-01",
      SRC_WFSF_23, URL_WFSF_23, unit="IICK020B",
      agency="UDWR + USFS (Uinta-Wasatch-Cache NF)",
      target="Nonnative trout (rainbow and hybridized cutthroat per the USFS decision memo)",
      note=("The 2023 report states plainly that G-113 'was also part of the rotenone treatment'. "
            "Restocked 2023-09-19 with ~270 CRCT fingerling (mean TL 44 mm) from the North Slope "
            "brood at Mammoth Creek Hatchery — our stocking_records row of 276 Cutthroats on that "
            "date is the same event. The 2021 report lists exactly two still waters, 'Lake G-64 "
            "(1.44 ha) and a small unnamed pond (0.26 ha)', so G-113 is that 0.26 ha pond; its "
            "0.64 acres in lakes.size_acres is sourced by that deduction, not printed by DWR "
            "against the G-113 designation.")),

    # --- Carter Creek, Aug 2021 (Lamb Lakes Basin) -------------------------
    T("GR-22", "Carter Creek project", "2021-08-17", "2021-08-25", SRC_CC21, URL_CC21,
      target="Brook trout",
      note=("Named in the release as one of 'Ram, Mutton and Bummer lakes', treated alongside "
            "East and West Fork Carter Creek above the Sheep Creek canal. Third and final year "
            "for East Fork Carter Creek. The release put Bummer's restocking at '2023 at the "
            "earliest' — the records show 2023-09-19 (221 fish), so that held. " + LAMB_CAVEAT)),
    T("GR-23", "Carter Creek project", "2021-08-17", "2021-08-25", SRC_CC21, URL_CC21,
      target="Brook trout",
      note=("Named in the release as one of 'Ram, Mutton and Bummer lakes'. The release planned "
            "Mutton's restocking for 2022; the records show it actually began 2023-09-19 (387 "
            "fish), so the plan slipped a year. " + LAMB_CAVEAT)),
    T("GR-24", "Carter Creek project", "2021-08-17", "2021-08-25", SRC_CC21, URL_CC21,
      target="Brook trout",
      note=("Named in the release as one of 'Ram, Mutton and Bummer lakes'. Planned for 2022 "
            "restocking; actually restocked from 2023-09-19 (497), then 2024 and 2025 — the "
            "most heavily re-seeded of the three. " + LAMB_CAVEAT)),

    # --- Carter Creek, Aug 2023 (Weyman Basin / Daggett) -------------------
    T("GR-16", "Carter Creek project", "2023-08-28", "2023-08-28", SRC_CC23, URL_CC23,
      note=("One of 'Daggett, Penguin, Upper Anson and Lower Anson lakes (north slope)'. WRI 6834 "
            "puts three lakes on the Monday (Aug 28) and Daggett on the Tuesday, so Penguin falls "
            "on the 28th. Still awaiting restocking — nothing since Tigers in 2016. " + CC_CAVEAT)),
    T("GR-10", "Carter Creek project", "2023-08-28", "2023-08-28", SRC_CC23, URL_CC23,
      note=("Monday of the Aug 28-29 pair (WRI 6834). Still awaiting restocking — nothing since "
            "Tigers in 2016, despite DWR planning to restock all four in 2024. " + CC_CAVEAT)),
    T("GR-9", "Carter Creek project", "2023-08-28", "2023-08-28", SRC_CC23, URL_CC23,
      note=("Monday of the Aug 28-29 pair (WRI 6834). Restocked from 2025-06-30 (649), again "
            "2026-07-15 (659) — a year later than DWR's 2024 plan. " + CC_CAVEAT)),
    T("GR-6", "Carter Creek project", "2023-08-29", "2023-08-29", SRC_CC23, URL_WRI6834,
      note=("WRI 6834: 'On Tuesday, we treated Daggett Lake and all inflowing and outflowing "
            "segments from Daggett.' The only one of the four treated on its own day. Restocked "
            "fastest too — 2024-10-01 (1,304 + 1,892 the same day), then 2025 and 2026. "
            + CC_CAVEAT)),

    # --- Oweep Creek, three treatments 2022-2024 ---------------------------
    T("LF-22", "Oweep Creek project", "2022-08-01", "2022-08-05", SRC_OW22, URL_OW22,
      target="Brook trout, rainbow trout",
      note=("First of three. 'Porcupine Lake (south slope)' named as its own line in the release. "
            "No restocking this year by design: 'Because this is the first year of the Oweep "
            "treatment, fish will not be restocked this year.' DWR raised the daily limit to 16 "
            "fish in May 2022 to let anglers harvest ahead of the treatment.")),
    T("LF-22", "Oweep Creek project", "2023-07-22", "2023-07-30", SRC_OW23, URL_OW23,
      target="Brook trout, rainbow trout",
      note=("Second of three. DATE CONFLICT, unresolved: the May 2023 news release forecast "
            "'July 31 to Aug. 4'; WRI 6665, filed after the fact, gives 22-30 July. The WRI "
            "dates are recorded here as the post-hoc figure, but both are DWR.")),
    T("LF-22", "Oweep Creek project", "2024-07-28", "2024-07-31", SRC_OW24, URL_OW24,
      target="Brook trout, rainbow trout",
      note=("Third and final. CAVEAT: the 2024 release names only 'Oweep Creek drainage (south "
            "slope)' and does not list Porcupine separately, unlike 2022 and 2023 — Porcupine's "
            "inclusion is inferred from WRI 6893, whose treatment area is Porcupine Lake plus "
            "15.8 miles of Oweep Creek upstream of natural waterfall barriers. Restocked "
            "2024-09-23 with 299 cutthroat from the South Slope Uinta CRCT brood. WRI 6893 also "
            "claims a second stocking in July 2025 with no matching Porcupine record — that may "
            "have gone to stream reaches. The barrier here is natural waterfalls, not a built "
            "structure.")),

    # --- Fall Creek, 2025 + 2026 -------------------------------------------
    T("X-117", "Fall Creek project", "2025-08-03", "2025-08-07", SRC_FC25, URL_FC25,
      note=("WRI 7370 objective (a): 'Eradicating current fish populations in Anderson and "
            "Phinney Lakes', plus 7 miles of inhabited stream upstream of the natural waterfall "
            "barrier, with a detox station run 3-4 days so Rock Creek below was unaffected. "
            "DRAINAGE NAMING: DWR files this under the FALL CREEK drainage, a headwater tributary "
            "to Rock Creek — searching DWR for 'Rock Creek treatment' misses it. Access is "
            "13 miles from the Stillwater Reservoir Trailhead. DATE CONFLICT: the news release "
            "says Aug 4-7, WRI 7370 says Aug 3-6; the span here covers both.")),
    T("X-119", "Fall Creek project", "2025-08-03", "2025-08-07", SRC_FC25, URL_FC25,
      note=("Named with Anderson in WRI 7370 objective (a). Last stocked 2021-06-29 (1,357 "
            "brookies) and fishless since the treatment. Same drainage-naming and date caveats "
            "as X-117.")),
    T("X-117", "Fall Creek project", "2026-08-03", "2026-08-06", SRC_FC26, URL_FC26,
      note=("Second treatment — the first did not finish the job. The 2026 release calls it 'the "
            "second year of treatment' and WRI 7370's completion narrative confirms 'A second "
            "treatment of Fall Creek was also completed in August of 2026 to continue the "
            "standard methods of treating lakes and streams twice before repatriating'. "
            "STOCKING IS NOW 2027, not 2026: 'If deemed successful, Colorado River cutthroat "
            "trout will be stocked into both Phinney Lake and Anderson Lake in 2027.' The 2026 "
            "release names the drainage rather than the two lakes individually.")),
    T("X-119", "Fall Creek project", "2026-08-03", "2026-08-06", SRC_FC26, URL_FC26,
      note=("Second treatment, with X-117. Stocking pushed to 2027. See X-117's note.")),
]

# The PWA builds its rotenone modal by regex over dwr_notes (index.html,
# buildRotenoneGroups), so these banners — not lake_treatments — are what the
# app reads. One per lake; the parenthesised part must contain the word
# "project" or the lake lands in the modal's "Other treatments" bucket.
WARN = "⚠️"
MARKERS = {
    "G-64": (f"{WARN} ROTENONE TREATED (Aug-Sep 2021, West Fork Smiths Fork project). Tiger trout "
             "restocked from 2022 as an interim fishery, to be dropped once cutthroat are established."),
    "G-113": (f"{WARN} ROTENONE TREATED (Aug-Sep 2021, West Fork Smiths Fork project). Restocked "
              "with Colorado River cutthroat trout Sep 2023."),
    "GR-22": (f"{WARN} ROTENONE TREATED (Aug 2021, Carter Creek project). Restocked with cutthroat "
              "trout beginning 2023."),
    "GR-23": (f"{WARN} ROTENONE TREATED (Aug 2021, Carter Creek project). Restocked with cutthroat "
              "trout beginning 2023."),
    "GR-24": (f"{WARN} ROTENONE TREATED (Aug 2021, Carter Creek project). Restocked with cutthroat "
              "trout beginning 2023."),
    "GR-6": (f"{WARN} ROTENONE TREATED (Aug 2023, Carter Creek project). Restocked with cutthroat "
             "trout beginning Oct 2024."),
    "GR-9": (f"{WARN} ROTENONE TREATED (Aug 2023, Carter Creek project). Restocked with cutthroat "
             "trout beginning 2025."),
    "GR-10": f"{WARN} ROTENONE TREATED (Aug 2023, Carter Creek project). Awaiting restocking.",
    "GR-16": f"{WARN} ROTENONE TREATED (Aug 2023, Carter Creek project). Awaiting restocking.",
    "LF-22": (f"{WARN} ROTENONE TREATED (2022, 2023 and 2024, Oweep Creek project). Restocked with "
              "cutthroat trout Sep 2024."),
    "X-117": (f"{WARN} ROTENONE TREATED (Aug 2025 and Aug 2026, Fall Creek project). Currently "
              "fishless. Colorado River cutthroat stocking planned for 2027."),
    "X-119": (f"{WARN} ROTENONE TREATED (Aug 2025 and Aug 2026, Fall Creek project). Currently "
              "fishless. Colorado River cutthroat stocking planned for 2027."),
}

# Physical fields this research established that the lakes row was missing.
LAKE_FIELDS = {
    "G-113": dict(size_acres=0.64),   # the 2021 report's 0.26 ha pond; Jed's call, 2026-09-24
}

COLUMNS = ["lake_id", "printed_name", "project_name", "water_unit",
           "treatment_type", "agency", "start_date", "end_date",
           "target_species", "restored_species", "note", "source", "source_url"]

BANNER_RE = re.compile(
    r"^⚠️ ROTENONE TREATED \([^)]*\)[^\n]*\n*", re.MULTILINE)


def _apply_marker(cur, lake_id, marker):
    """Prepend the PWA's rotenone banner to lakes.dwr_notes, idempotently.

    Strips ANY existing banner first — including one written under a different
    project name — so re-running never stacks them and a project rename lands
    cleanly. Returns True if the row changed.
    """
    old = cur.execute("SELECT dwr_notes FROM lakes WHERE id = ?",
                      (lake_id,)).fetchone()[0] or ""
    body = BANNER_RE.sub("", old).lstrip("\n")
    new = marker + ("\n\n" + body if body else "")
    if new == old:
        return False
    cur.execute("UPDATE lakes SET dwr_notes = ? WHERE id = ?", (new, lake_id))
    return True


def main():
    if os.path.exists(os.path.join(PROJECT_DIR, ".db-readonly")):
        sys.exit("Refusing to write: this clone is a read-only mirror (.db-readonly present).")

    create_database(DB_PATH)  # converges the schema; no-op if already current
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # This script is the sole writer of lake_treatments, so it clears the whole
    # table rather than just the projects it is about to insert. Deleting only
    # the named projects strands rows whenever a project is RENAMED, which is
    # exactly what happened on 2026-09-24 ("... CRCT restoration" -> "... project").
    projects = sorted({r["project_name"] for r in RECORDS})
    before = cur.execute("SELECT COUNT(*) FROM lake_treatments").fetchone()[0]
    cur.execute("DELETE FROM lake_treatments")

    def lake_id(ln):
        row = cur.execute("SELECT id FROM lakes WHERE letter_number = ?", (ln,)).fetchone()
        return row[0] if row else None

    missing = set()
    for rec in RECORDS:
        rec = dict(rec)
        ln = rec.pop("letter_number")
        rec["lake_id"] = lake_id(ln)
        if rec["lake_id"] is None:
            missing.add(ln)
        cur.execute(
            "INSERT INTO lake_treatments (%s) VALUES (%s)"
            % (",".join(COLUMNS), ",".join("?" * len(COLUMNS))),
            [rec[c] for c in COLUMNS])

    banners = 0
    for ln, marker in MARKERS.items():
        lid = lake_id(ln)
        if lid is None:
            missing.add(ln)
            continue
        banners += _apply_marker(cur, lid, marker)

    fields = 0
    for ln, cols in LAKE_FIELDS.items():
        lid = lake_id(ln)
        if lid is None:
            missing.add(ln)
            continue
        for col, val in sorted(cols.items()):
            cur.execute(f"UPDATE lakes SET {col} = ? WHERE id = ? "
                        f"AND ({col} IS NULL OR {col} != ?)", (val, lid, val))
            fields += cur.rowcount

    conn.commit()
    after = cur.execute("SELECT COUNT(*) FROM lake_treatments").fetchone()[0]
    summary = cur.execute(
        "SELECT project_name, COUNT(DISTINCT lake_id), COUNT(*) "
        "FROM lake_treatments GROUP BY project_name ORDER BY project_name").fetchall()
    conn.close()

    print(f"lake_treatments: {before} row(s) -> {after} row(s) "
          f"across {len(projects)} project(s)")
    for name, lakes_n, rows_n in summary:
        print(f"  {name:<34} {lakes_n} lake(s), {rows_n} treatment(s)")
    print(f"  dwr_notes banners rewritten: {banners}; lakes fields set: {fields}")
    if missing:
        print(f"  WARNING: no lakes row for {', '.join(sorted(missing))}")


if __name__ == "__main__":
    main()
