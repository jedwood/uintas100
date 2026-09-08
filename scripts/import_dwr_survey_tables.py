#!/usr/bin/env python3
"""
Import the survey tables from the 2025 revised DWR pamphlets into
dwr_gillnet_samples (Whiterocks: per lake x species gillnet stats) and
dwr_lake_summary (Bear River, Blacks Fork: per-lake summary rows).
Plan + column meanings: docs/dwr-survey-tables-plan.md.

Reads the committed PDFs in data/dwr_new_pamphlets/ through `pdftotext
-layout` (poppler), so table rows stay on one line. Idempotent: every run
deletes and reloads all rows for SOURCE_EDITION. Obeys the writer guard.

Usage:
    python3 scripts/import_dwr_survey_tables.py --dry-run   # parse + report only
    python3 scripts/import_dwr_survey_tables.py             # write to the DB
"""
import argparse
import os
import re
import sqlite3
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
from writer_guard import exit_if_readonly            # noqa: E402
from species_utils import normalize_species_name    # noqa: E402

DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
PAMPHLET_DIR = os.path.join(PROJECT_DIR, "data", "dwr_new_pamphlets")
SOURCE_EDITION = 2025

# Hand-reviewed designation typos in the pamphlets: (printed name, printed
# designation) -> real designation. "Nellie (WR-25)" in the Whiterocks brook
# table: there is no WR-25; the cutthroat table prints Nellie as WR-75.
DESIGNATION_FIXES = {
    ("Nellie", "WR-25"): "WR-75",
    ("Denise", "WR-8"): "WR-9",     # brook table; Denise's description and DWR stocking say WR-9
}

# pdf file -> DB drainage(s) used to resolve name-only rows
PAMPHLETS = {
    "whiterocks-new.pdf": ["White Rocks Drainage"],
    "bear-river-updated.pdf": ["Bear River Drainage"],
    "blacks-fork-new.pdf": ["Blacks Fork Drainage"],
}

_DESIG = r"[A-Z]{1,3}-\d+[a-z]?"
_PAGE_HDR = re.compile(r"^\s*(?:[A-Z] )+[A-Z]?(?: (?:[A-Z] )+[A-Z]?)* ?\| ?\d+\s*$|D R A I N A G E")


def layout_text(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True,
                          capture_output=True, text=True).stdout


def _num(s):
    s = (s or "").replace(",", "").replace("–", "").strip()
    if s in ("", "-", "–", "unk"):
        return None
    if re.fullmatch(r"\d{1,2}\.\d{3}", s):      # "10.750" = OCR'd 10,750
        s = s.replace(".", "")
    return float(s) if "." in s else int(s)


# --------------------------------------------------------------------------- #
# Whiterocks: "<Species> gillnetting samples" tables, one row per line
# --------------------------------------------------------------------------- #
_GILL_HDR = re.compile(r"^\s*([A-Za-z ]+?) gillnetting samples\s*$")
_GILL_ROW = re.compile(
    r"^\s*(?P<name>[A-Za-z’'.\-]+(?: [A-Za-z’'.\-]+)*(?: \d)?)\s*"
    r"(?:\((?P<desig>" + _DESIG + r")\))?\s{2,}"
    r"(?P<cycle>NR|MIG|\d(?:/\d)?)\s+"
    r"(?P<other>None|[A-Z]{2,4}(?:,\s?[A-Z]{2,4})*)\s+"
    r"(?P<n>\d+)\s+"
    r"(?:(?P<ml>[\d.]+)\s+(?P<xl>[\d.]+)\s+(?P<mw>[\d.]+)\s+(?P<xw>[\d.]+)|None sampled)\s*$")
_FOOTNOTE = re.compile(r"^\s*([a-d])\s+(\S.*)$")


def parse_gillnet(text):
    rows, species, pending_mark = [], None, None
    footnotes = {}
    for line in text.splitlines():
        h = _GILL_HDR.match(line)
        if h:
            species = normalize_species_name(h.group(1).strip()) or h.group(1).strip()
            continue
        if re.fullmatch(r"\s*[a-d]\s*", line):          # footnote marker on its own line
            pending_mark = line.strip()
            continue
        f = _FOOTNOTE.match(line)
        if f and species and not _GILL_ROW.match(line):
            footnotes[f.group(1)] = f.group(2).strip()
            continue
        m = _GILL_ROW.match(line)
        if m and species:
            rows.append({
                "species": species, "printed_name": m["name"].strip(),
                "desig": m["desig"], "stocking_cycle": m["cycle"],
                "other_species": None if m["other"] == "None" else m["other"].replace(" ", ""),
                "n_sampled": int(m["n"]),
                "mean_length_in": _num(m["ml"]), "max_length_in": _num(m["xl"]),
                "mean_weight_lb": _num(m["mw"]), "max_weight_lb": _num(m["xw"]),
                "_mark": pending_mark,
            })
            pending_mark = None
    for r in rows:
        r["note"] = footnotes.get(r.pop("_mark")) if r.get("_mark") else r.pop("_mark", None) and None
    return rows


# --------------------------------------------------------------------------- #
# Bear River / Blacks Fork: lake summary tables (multi-line cells)
# --------------------------------------------------------------------------- #
_SUM_DATA = re.compile(
    r"(?P<trail>[\d.]+|–|-)\s+(?P<elev>[\d,.]+)\s+(?P<size>[\d.]+)\s+(?P<depth>\d+|unk)\s+"
    r"(?P<camp>Y|N|–|-)\s+(?P<spring>Y|N|–|-)\s+(?P<horse>Y|N|limited|–|-)\s+"
    r"(?P<fish>[A-Za-z/​ ]+?)\s+(?P<cycle>NR|\d[a-d]?|–|-)\s*$")
_SUM_NOTE = re.compile(r"\s{3,}(?P<note>Unable to support a fishery|Private property[^\n]*?)\s*$")
_SUM_HDR = re.compile(r"^\s*Sub-")
_JUNK = re.compile(r"^\s*(Lake|drainage|\(mi\)|Trail|distance(?: \(mi\))?|Access)\s*$")
_JUNK_WORDS = re.compile(r"\b(Lake|drainage|\(mi\)|\(ft\)|\(acres\)|Trail|distance|Access|sites|water|feed|species|cycle)\b")


def _tidy(text):
    text = re.sub(r"\s+", " ", text.replace("\u200b", "")).strip()
    return text or None


def _fragments(line):
    """[(start_col, text)] split on runs of 2+ spaces."""
    return [(m.start(), m.group(0)) for m in re.finditer(r"\S+(?: \S+)*", line)]


def parse_summary(text):
    lines = text.splitlines()
    rows, pending, cols = [], [], None
    i = 0
    while i < len(lines):
        line = lines[i]
        if _SUM_HDR.match(line):
            # header block: "Sub-… Elevation Size … Fish Stocking" / "Lake … Access …" /
            # "drainage … (ft) …" / "(mi)". Record column centers, skip the block.
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            cols = (line.find("Sub-") + 2,
                    (nxt.find("Access") + 3) if "Access" in nxt else line.find("Sub-") + 32,
                    line.find("Fish") + 2)
            pending = []
            i += 1
            while i < len(lines) and (_JUNK_WORDS.search(lines[i]) or not lines[i].strip()) \
                    and not _SUM_DATA.search(lines[i]) and not _SUM_NOTE.search(lines[i]):
                i += 1
            continue
        if not line.strip() or _PAGE_HDR.search(line) or _JUNK.match(line) or cols is None:
            if not line.strip():
                pass  # blank lines don't end a block; multi-line rows straddle them rarely
            i += 1
            continue
        if line.strip().startswith("NR = "):
            i += 1
            continue
        data = _SUM_DATA.search(line)
        note = None if data else _SUM_NOTE.search(line)
        if not data and not note:
            pending.append(line)
            i += 1
            continue
        block = pending + [line]
        pending = []
        text_end = (data or note).start()
        # trailing continuation lines: no lake name in the first columns
        j = i + 1
        n_above = len(block) - 1
        n_below = 0
        while j < len(lines) and lines[j].strip() and not _SUM_DATA.search(lines[j]) \
                and not _SUM_NOTE.search(lines[j]) and not _SUM_HDR.match(lines[j]) \
                and not _PAGE_HDR.search(lines[j]) and not lines[j].strip().startswith("NR = "):
            first = len(lines[j]) - len(lines[j].lstrip())
            has_desig = re.search(r"\(" + _DESIG + r"\)", lines[j]) or re.match(r"\s*" + _DESIG + r"\b", lines[j])
            # Cells are vertically centred, so a wrapped line BELOW the data
            # line implies one above it too (pending non-empty) — unless it is
            # the lake's own designation or an access-column wrap ("then 2 mi
            # west"). A bare sub-drainage line after a single-line row starts
            # the NEXT row ("BR-2 … / Stillwater Fork / BR-16 …").
            if has_desig or first >= (cols[0] + cols[1]) // 2:
                block.append(lines[j])
                j += 1
            elif n_below < n_above and first >= 9:
                block.append(lines[j])
                n_below += 1
                j += 1
            else:
                break
        # column assignment of text fragments
        name, sub, acc, fishfrag = [], [], [], []
        name_sub = (3 + cols[0]) // 2            # boundaries between column centres
        sub_acc = (cols[0] + cols[1]) // 2
        for bl in block:
            limit = text_end if bl is line else len(bl)
            for start, frag in _fragments(bl[:limit]):
                mid = start + len(frag) / 2
                if bl is not line and start >= cols[2] - 6:
                    fishfrag.append(frag.replace("\u200b", ""))
                elif mid < name_sub:
                    name.append(frag)
                elif mid < sub_acc:
                    sub.append(frag)
                else:
                    acc.append(frag)
        name_txt = " ".join(name)
        dm = re.search(r"\(?(" + _DESIG + r")\)?", name_txt)
        desig = dm.group(1) if dm else None
        printed = re.sub(r"\s*\(?" + _DESIG + r"\)?\s*", " ", name_txt).strip() or desig
        row = {"desig": desig, "printed_name": printed,
               "sub_drainage": _tidy(" ".join(sub)),
               "access": _tidy(" ".join(acc))}
        if data:
            fish = data["fish"].replace("\u200b", "").strip()
            if fishfrag:                                  # "Brook/" above + "Rainbow" below
                fish = "".join([f.strip() for f in fishfrag[:1]] + [fish] + [f.strip() for f in fishfrag[1:]])
                fish = re.sub(r"/+", "/", fish).strip("/")
            row.update({
                "trail_miles": _num(data["trail"]), "elevation_ft": _num(data["elev"]),
                "size_acres": _num(data["size"]), "depth_ft": _num(data["depth"]),
                "campsites": data["camp"].replace("–", "-"), "spring_water": data["spring"].replace("–", "-"),
                "horse_feed": data["horse"].replace("–", "-"), "fish_species": fish,
                "stocking_cycle": data["cycle"].replace("–", "-"), "note": None})
        else:
            row.update({"trail_miles": None, "elevation_ft": None, "size_acres": None,
                        "depth_ft": None, "campsites": None, "spring_water": None,
                        "horse_feed": None, "fish_species": None, "stocking_cycle": None,
                        "note": note["note"].strip()})
        rows.append(row)
        i = j
    return rows


# --------------------------------------------------------------------------- #
def _name_key(name):
    """'Rock Upper' == 'Upper Rock' == 'Upper Rock Lake'; 'Rassmussen #1' == 'Rassmussen 1'."""
    words = re.sub(r"[^a-z0-9 ]", "", (name or "").lower().replace("’", "").replace("'", "")).split()
    return "".join(sorted(w for w in words if w not in ("lake", "lakes", "reservoir")))


def _names_disagree(a, b):
    """True only for genuinely different names — spelling variants ("Quent"/
    "Queant", "Mocassin"/"Moccasin") and qualifiers ("Reader"/"Upper Reader",
    "Bourbon"/"Bourbon lake (Gold Hill)") are not worth a note."""
    import difflib
    if not a or not b or a in b or b in a:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() < 0.6


def resolve(conn, rows, drainages):
    """Attach lake_id by designation, else by unique name within the drainage."""
    by_desig = {ln: lid for lid, ln in conn.execute("SELECT id, letter_number FROM lakes")}
    by_name = {}
    q = "SELECT id, name FROM lakes WHERE drainage IN (%s)" % ",".join("?" * len(drainages))
    for lid, name in conn.execute(q, drainages):
        key = _name_key(name)
        if key:
            by_name.setdefault(key, []).append(lid)
    name_of = {lid: _name_key(name) for lid, name in conn.execute("SELECT id, name FROM lakes")}
    unresolved = []
    for r in rows:
        fix = DESIGNATION_FIXES.get((r["printed_name"], r["desig"]))
        if fix:
            r["note"] = ((r.get("note") + "; ") if r.get("note") else "") + f"pamphlet prints {r['desig']}"
            r["desig"] = fix
        lid_d = by_desig.get(r["desig"]) if r["desig"] else None
        lid_n = None
        if r["printed_name"]:
            cands = by_name.get(_name_key(r["printed_name"]), [])
            if len(cands) == 1:
                lid_n = cands[0]
        lid = lid_d
        if lid_d is None:
            lid = lid_n
        elif r["printed_name"] and lid_n is None and name_of.get(lid_d) and \
                _names_disagree(name_of[lid_d], _name_key(r["printed_name"])) and r["printed_name"] != r["desig"]:
            db_name = conn.execute("SELECT name FROM lakes WHERE id = ?", (lid_d,)).fetchone()[0]
            r["note"] = ((r.get("note") + "; ") if r.get("note") else "") + \
                f"pamphlet prints '{r['printed_name']}'; DB names {r['desig']} '{db_name}'"
        elif lid_n and lid_n != lid_d and name_of.get(lid_d) != _name_key(r["printed_name"]):
            # the pamphlet printed the wrong designation next to a real name
            # ("Nellie (WR-25)" — Nellie is WR-75; "Taylor (WR-8)" is Denise's)
            lid = lid_n
            r["note"] = ((r.get("note") + "; ") if r.get("note") else "") + \
                f"pamphlet prints {r['desig']}"
        r["lake_id"] = lid
        if lid is None:
            unresolved.append((r["desig"], r["printed_name"]))
    return unresolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.dry_run:
        exit_if_readonly()
    conn = sqlite3.connect(args.db)

    gill, summ = [], []
    for pdf, drainages in PAMPHLETS.items():
        path = os.path.join(PAMPHLET_DIR, pdf)
        if not os.path.exists(path):
            print(f"missing {pdf}, skipped")
            continue
        text = layout_text(path)
        g = parse_gillnet(text)
        s = parse_summary(text)
        ug = resolve(conn, g, drainages)
        us = resolve(conn, s, drainages)
        print(f"{pdf}: {len(g)} gillnet rows ({len(ug)} unresolved), "
              f"{len(s)} summary rows ({len(us)} unresolved)")
        for u in ug + us:
            print("   unresolved:", u)
        gill += g
        summ += s

    if args.dry_run:
        for r in gill:
            print("G", r["species"], r["desig"], r["printed_name"], r["stocking_cycle"], r["other_species"],
                  r["n_sampled"], r["mean_length_in"], r["max_length_in"], r["mean_weight_lb"], r["max_weight_lb"], r["note"] or "")
        for r in summ:
            print("S", r["desig"], r["printed_name"], "|", r["sub_drainage"], "|", r["access"], "|",
                  r["trail_miles"], r["elevation_ft"], r["size_acres"], r["depth_ft"], r["campsites"],
                  r["spring_water"], r["horse_feed"], r["fish_species"], r["stocking_cycle"], r["note"] or "")
        return

    cur = conn.cursor()
    cur.execute("DELETE FROM dwr_gillnet_samples WHERE source_edition = ?", (SOURCE_EDITION,))
    cur.execute("DELETE FROM dwr_lake_summary WHERE source_edition = ?", (SOURCE_EDITION,))
    for r in gill:
        cur.execute("""INSERT INTO dwr_gillnet_samples (lake_id, printed_name, species, stocking_cycle,
                       other_species, n_sampled, mean_length_in, max_length_in, mean_weight_lb,
                       max_weight_lb, note, source_edition) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r["lake_id"], r["printed_name"], r["species"], r["stocking_cycle"], r["other_species"],
                     r["n_sampled"], r["mean_length_in"], r["max_length_in"], r["mean_weight_lb"],
                     r["max_weight_lb"], r["note"], SOURCE_EDITION))
    for r in summ:
        cur.execute("""INSERT INTO dwr_lake_summary (lake_id, printed_name, sub_drainage, access, trail_miles,
                       elevation_ft, size_acres, depth_ft, campsites, spring_water, horse_feed, fish_species,
                       stocking_cycle, note, source_edition) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r["lake_id"], r["printed_name"], r["sub_drainage"], r["access"], r["trail_miles"],
                     r["elevation_ft"], r["size_acres"], r["depth_ft"], r["campsites"], r["spring_water"],
                     r["horse_feed"], r["fish_species"], r["stocking_cycle"], r["note"], SOURCE_EDITION))
    conn.commit()
    print(f"Wrote {len(gill)} gillnet rows and {len(summ)} summary rows.")


if __name__ == "__main__":
    main()
