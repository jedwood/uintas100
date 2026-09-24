#!/usr/bin/env python3
"""Load chemical (rotenone) reclamation projects into lake_treatments.

Idempotent: re-running replaces the rows for each project listed here and
reports no net change. Only projects that actually included a *lettered lake*
belong here — stream-only treatments are out of scope.

Every row must be traceable to a primary source. The quotes that justify the
current contents are reproduced in the RECORDS table below so a future reader
can re-check them without re-doing the research.
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

WFSF = "West Fork Smiths Fork CRCT restoration"

# UDWR, "Native Cutthroat Trout Conservation Activities in the Northern
# Region, 2021", p. 45:
#   "A large crew of personnel from UDWR and USFS applied rotenone to the West
#    Fork Smiths Fork drainage over a three-day period, August 30-September 1,
#    2021. Treated water was neutralized a short distance upstream of the
#    Wyoming border at the migration barrier installed by UDWR in 2006. The
#    mainstem, as well as all tributaries and spring inputs upstream of the
#    barrier to the headwaters, totaling approximately 32.0 km of stream, plus
#    Lake G-64 (1.44 ha) and a small unnamed pond (0.26 ha) were targeted.
#    However, the headwater portions of two tributaries were excluded from the
#    treatment because genetic analyses showed their CRCT populations to be
#    genetically pure (see Evans and Shiozawa 2016)."
#
# UDWR, "Cutthroat Trout Report, Northern Region, 2023", p. 52:
#   "In addition, a small headwater lake, G-113, which was also part of the
#    rotenone treatment, was stocked with approximately 270 fingerling CRCT
#    (mean TL 44 mm) on September 19, 2023."
SRC_2021 = "UDWR, Native Cutthroat Trout Conservation Activities in the Northern Region, 2021, p. 45"
SRC_2023 = "UDWR, Cutthroat Trout Report, Northern Region, 2023, p. 52"
URL_2021 = ("https://web.archive.org/web/20250611224207/https://wildlife.utah.gov/pdf/fish/"
            "technical-reports/native_cutthroat_trout_conservation_activities_in_the_northern_region_2021.pdf")
URL_2023 = ("https://web.archive.org/web/20251010092535/https://wildlife.utah.gov/pdf/fish/"
            "technical-reports/cutthroat_trout_report,_northern_region_2023.pdf")

RECORDS = [
    dict(
        letter_number="G-64",
        printed_name="Lake G-64",
        project_name=WFSF,
        water_unit="IICK020B",
        treatment_type="rotenone",
        agency="UDWR + USFS (Uinta-Wasatch-Cache NF)",
        start_date="2021-08-30",
        end_date="2021-09-01",
        target_species="Nonnative trout (rainbow and hybridized cutthroat per the USFS decision memo)",
        restored_species="Tigers",
        note=("Named outright in the 2021 report as 'Lake G-64 (1.44 ha)' — 3.56 acres, "
              "against the 1986 pamphlet's 3.4. NOT a cutthroat water afterward: the biennial "
              "tiger trout program resumed 2022-06-28 and continues (2024, 2026). The USFS "
              "decision memo explains why — tigers are stocked at the downstream, "
              "non-wilderness end of the project area to hold a fishery while CRCT expand, "
              "and are to be dropped once CRCT are established."),
        pwa_marker=("\u26a0\ufe0f ROTENONE TREATED (Aug-Sep 2021, West Fork Smiths Fork "
                    "project). Tiger trout restocked from 2022 as an interim fishery, to be "
                    "dropped once cutthroat are established."),
        source=SRC_2021,
        source_url=URL_2021,
    ),
    dict(
        letter_number="G-113",
        printed_name="G-113",
        project_name=WFSF,
        water_unit="IICK020B",
        treatment_type="rotenone",
        agency="UDWR + USFS (Uinta-Wasatch-Cache NF)",
        start_date="2021-08-30",
        end_date="2021-09-01",
        target_species="Nonnative trout (rainbow and hybridized cutthroat per the USFS decision memo)",
        restored_species="Cutthroats",
        note=("The 2023 report states plainly that G-113 'was also part of the rotenone "
              "treatment'. Restocked 2023-09-19 with ~270 CRCT fingerling (mean TL 44 mm) "
              "from the North Slope brood at Mammoth Creek Hatchery — our stocking_records "
              "row of 276 Cutthroats on that date is the same event. INFERENCE, not stated: "
              "the 2021 report lists exactly two still waters, 'Lake G-64 (1.44 ha) and a "
              "small unnamed pond (0.26 ha)', so G-113 is almost certainly that 0.26 ha "
              "(0.64 acre) pond — recorded here rather than written into lakes.size_acres "
              "because no source says so directly."),
        pwa_marker=("\u26a0\ufe0f ROTENONE TREATED (Aug-Sep 2021, West Fork Smiths Fork "
                    "project). Restocked with Colorado River cutthroat trout Sep 2023."),
        source=SRC_2023,
        source_url=URL_2023,
    ),
]

COLUMNS = ["lake_id", "printed_name", "project_name", "water_unit",
           "treatment_type", "agency", "start_date", "end_date",
           "target_species", "restored_species", "note", "source", "source_url"]


def _apply_marker(cur, lake_id, project_name, marker):
    """Prepend the PWA's rotenone banner to lakes.dwr_notes, idempotently.

    index.html builds its "Lakes treated with rotenone" modal by regex over
    dwr_notes (see buildRotenoneGroups), so the banner — not lake_treatments —
    is what the app actually reads. lake_treatments stays the source of truth;
    this is the derived copy. Any existing banner for the SAME project is
    replaced, so re-running never stacks them.
    """
    notes = cur.execute("SELECT dwr_notes FROM lakes WHERE id = ?",
                        (lake_id,)).fetchone()[0] or ""
    key = project_name.replace(" CRCT restoration", "")
    pattern = re.compile(
        r"^\u26a0\ufe0f ROTENONE TREATED \([^)]*" + re.escape(key) + r"[^)]*\)[^\n]*\n*",
        re.MULTILINE)
    notes = pattern.sub("", notes).lstrip("\n")
    new = marker + ("\n\n" + notes if notes else "")
    if new != (cur.execute("SELECT dwr_notes FROM lakes WHERE id = ?",
                           (lake_id,)).fetchone()[0] or ""):
        cur.execute("UPDATE lakes SET dwr_notes = ? WHERE id = ?", (new, lake_id))


def main():
    if os.path.exists(os.path.join(PROJECT_DIR, ".db-readonly")):
        sys.exit("Refusing to write: this clone is a read-only mirror (.db-readonly present).")

    create_database(DB_PATH)  # converges the schema; no-op if already current
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    projects = sorted({r["project_name"] for r in RECORDS})
    before = cur.execute(
        "SELECT COUNT(*) FROM lake_treatments WHERE project_name IN (%s)"
        % ",".join("?" * len(projects)), projects).fetchone()[0]
    cur.execute("DELETE FROM lake_treatments WHERE project_name IN (%s)"
                % ",".join("?" * len(projects)), projects)

    missing = []
    for rec in RECORDS:
        row = cur.execute("SELECT id FROM lakes WHERE letter_number = ?",
                          (rec["letter_number"],)).fetchone()
        if row is None:
            missing.append(rec["letter_number"])
        rec = dict(rec)
        rec["lake_id"] = row[0] if row else None
        marker = rec.pop("pwa_marker", None)
        if row and marker:
            _apply_marker(cur, row[0], rec["project_name"], marker)
        rec.pop("letter_number")
        cur.execute(
            "INSERT INTO lake_treatments (%s) VALUES (%s)"
            % (",".join(COLUMNS), ",".join("?" * len(COLUMNS))),
            [rec[c] for c in COLUMNS])

    conn.commit()
    after = cur.execute(
        "SELECT COUNT(*) FROM lake_treatments WHERE project_name IN (%s)"
        % ",".join("?" * len(projects)), projects).fetchone()[0]
    conn.close()

    print(f"lake_treatments: {before} row(s) -> {after} row(s) "
          f"for {len(projects)} project(s)")
    for rec in RECORDS:
        print(f"  {rec['letter_number']:<7} {rec['project_name']} "
              f"({rec['start_date']} .. {rec['end_date']})")
    if missing:
        print(f"  WARNING: no lakes row for {', '.join(missing)} — lake_id left NULL")


if __name__ == "__main__":
    main()
