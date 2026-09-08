#!/usr/bin/env python3
"""
One-time backfill (2026-09-07) of lakes.dwr_edition and lakes.dwr_notes_prev.

Background: the 2025 revised DWR pamphlets (Bear River, Blacks Fork,
Whiterocks) were applied to dwr_notes IN PLACE on 2026-03-03 (commit 36a0ffc)
and finished by hand in the 2026-08-05 audit, so the DB never recorded which
edition a description came from and the superseded text survived only in git.

This script:
  1. Sets dwr_edition for every lake with notes — 2025 where the text matches
     the 2025 pamphlet entry, otherwise the publication year of the original
     "Lakes of the High Uintas" pamphlet for the lake's drainage (the series
     list on the back of the 1999 Provo/Weber pamphlet supplies the years).
  2. For 2025-edition lakes, recovers the pre-March-2026 write-up from an
     older copy of the DB (default: `git show 36a0ffc^:uinta_lakes.db`) and
     stores it in dwr_notes_prev when it is materially different
     (difflib ratio < 0.9 after whitespace/banner normalization).

Idempotent: re-running recomputes the same values. Obeys the writer guard.

Usage:
    python3 scripts/backfill_dwr_editions.py [--old-db PATH] [--dry-run]
"""
import argparse
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
from writer_guard import exit_if_readonly                     # noqa: E402
from compare_new_pamphlets import (parse_lake_entries, PAMPHLET_FILES,   # noqa: E402
                                   NEW_PAMPHLETS_DIR, PAMPHLET_EDITION,
                                   materially_different)

DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
OLD_DB_GIT_REV = "36a0ffc^"     # last commit before the 2025 pamphlets were applied

# Publication year of the original DWR "Lakes of the High Uintas" pamphlet
# covering each drainage (series list, back page of the 1999 Provo/Weber
# pamphlet; Ashley Creek is Publication 81-6, reprinted 1988).
ORIGINAL_EDITION = {
    "Ashley Creek Drainage": 1981,
    "Bear River Drainage": 1985,
    "Blacks Fork Drainage": 1985,
    "Dry Gulch Drainage": 1997,
    "Uinta River Drainage": 1997,
    "Duchesne River Drainage": 1996,
    "Provo River Drainage": 1999,
    "Weber River Drainage": 1999,
    "Rock Creek Drainage": 1997,
    "Sheep/Carter Creek Drainages": 1996,
    "Burnt Fork Drainage": 1996,
    "Smiths Fork Drainage": 1986,
    "Henrys Fork Drainage": 1986,
    "Beaver Creek Drainage": 1986,
    "White Rocks Drainage": 1987,
    "Yellowstone Drainage": 1996,
    "Lake Fork Drainage": 1996,
    "Swift Creek Drainage": 1996,
}

_BANNER = re.compile(r"^⚠️ ROTENONE.*?\n\n", re.S)


def _body(text):
    return " ".join(_BANNER.sub("", text or "").split()).lower()


def _new_pamphlet_entries():
    """{designation: text} for every entry in the 2025 pamphlet text files."""
    out = {}
    for fname in PAMPHLET_FILES:
        path = os.path.join(NEW_PAMPHLETS_DIR, fname)
        if not os.path.exists(path):
            continue
        for e in parse_lake_entries(open(path, encoding="utf-8").read()):
            out.setdefault(e["designation"], e["text"])
    return out


def _old_db(path):
    if path:
        return path
    tmp = os.path.join(tempfile.gettempdir(), "uintas_pre2025_pamphlets.db")
    with open(tmp, "wb") as f:
        subprocess.run(["git", "show", f"{OLD_DB_GIT_REV}:uinta_lakes.db"],
                       cwd=PROJECT_DIR, check=True, stdout=f)
    return tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--old-db", help="pre-2025-pamphlet DB (default: from git)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.dry_run:
        exit_if_readonly()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    for col, decl in (("dwr_edition", "INTEGER"), ("dwr_notes_prev", "TEXT")):
        try:
            cur.execute(f"ALTER TABLE lakes ADD COLUMN {col} {decl}")
        except sqlite3.OperationalError:
            pass

    new_entries = _new_pamphlet_entries()
    old = sqlite3.connect(_old_db(args.old_db))
    old_notes = {ln: n for ln, n in old.execute(
        "SELECT letter_number, dwr_notes FROM lakes")}

    counts = {"2025": 0, "original": 0, "no_notes": 0, "prev_kept": 0,
              "prev_same": 0, "unknown_drainage": []}
    for lid, ln, drainage, notes, cur_edition, cur_prev in list(cur.execute(
            "SELECT id, letter_number, drainage, dwr_notes, dwr_edition, dwr_notes_prev FROM lakes")):
        if not notes or not notes.strip():
            edition, prev = None, None
            counts["no_notes"] += 1
        else:
            body = _body(notes)
            new = new_entries.get(ln)
            is_new = bool(new) and (body.startswith(_body(new)[:150]) or
                                    _body(new).startswith(body[:150]))
            if is_new:
                edition = PAMPHLET_EDITION
                counts["2025"] += 1
                prev = None
                old_text = old_notes.get(ln)
                if old_text and old_text.strip():
                    old_body = _BANNER.sub("", old_text).strip()
                    if materially_different(old_body, _BANNER.sub("", notes)):
                        prev = old_body
                        counts["prev_kept"] += 1
                    else:
                        counts["prev_same"] += 1
            else:
                edition = ORIGINAL_EDITION.get(drainage)
                if edition is None:
                    counts["unknown_drainage"].append((ln, drainage))
                counts["original"] += 1
                prev = None
        if not args.dry_run:
            cur.execute("UPDATE lakes SET dwr_edition = ?, dwr_notes_prev = ? WHERE id = ?",
                        (edition, prev, lid))
    if not args.dry_run:
        conn.commit()
    print(f"{'DRY RUN — ' if args.dry_run else ''}edition 2025: {counts['2025']}, "
          f"original pamphlet: {counts['original']}, no notes: {counts['no_notes']}; "
          f"previous text kept: {counts['prev_kept']} (dropped as near-identical: {counts['prev_same']})")
    if counts["unknown_drainage"]:
        print("No edition year for drainage:", counts["unknown_drainage"])


if __name__ == "__main__":
    main()
