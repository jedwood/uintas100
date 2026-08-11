#!/usr/bin/env python3
"""
Import lake + trailhead information from Cordell M. Andersen's self-published
book "The High Uinta Mountains" (data/the-high-uinta-mountains-by-cma.pdf,
gitignored — 148MB, local to the Mini only).

The PDF has a full embedded text layer, so no OCR is involved: the whole book
is extracted with pdftotext (poppler) in under a second, then mined with plain
text processing.

What it produces (all idempotent — safe to re-run):
  - lakes.cma_notes: for every lake whose DWR designation appears in the book
    body as "(X-nn)", a markdown digest of each paragraph mentioning it, with
    printed-page citations.
  - trailheads table: parsed from the book's index ("TRAILHEAD: ..." entries),
    with the "HOW TO GET HERE" intro excerpt from the section's first page.
  - trailhead_lakes table: a trailhead is linked to every lake whose
    designation appears on the trailhead's own pages.
  - Each trailhead's drainage = majority drainage of its linked lakes.
  - data/cma_index.json: git-diffable record of what was parsed.

Page math: the book's printed page numbers run a uniform +15 behind the PDF
page numbers (verified against the printed folio on all 681 numbered pages).
The index occupies PDF pages 700-713.

Requires the PDF and pdftotext; exits cleanly if either is missing. Writes the
DB, so it obeys the single-writer guard (Mini only).
"""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import writer_guard

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PDF_PATH = os.path.join(PROJECT_DIR, "data", "the-high-uinta-mountains-by-cma.pdf")
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
INDEX_JSON = os.path.join(PROJECT_DIR, "data", "cma_index.json")

PAGE_OFFSET = 15          # printed page N = PDF page N + 15
INDEX_FIRST_PDF_PAGE = 700  # the book's index starts here (PDF numbering)

MAX_EXCERPTS_PER_LAKE = 6
MAX_EXCERPT_CHARS = 900
MAX_TRAILHEAD_INFO_CHARS = 1500


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #

def extract_pages():
    """pdftotext the whole book -> list of page texts (index 0 = PDF page 1)."""
    if not os.path.exists(PDF_PATH):
        sys.exit(f"Book PDF not found at {PDF_PATH} (it is gitignored and "
                 "lives only on the Mini) — nothing to do.")
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext (poppler) not found on PATH — brew install poppler")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tmp = tf.name
    try:
        subprocess.run(["pdftotext", PDF_PATH, tmp], check=True)
        with open(tmp, encoding="utf-8") as f:
            return f.read().split("\f")
    finally:
        os.unlink(tmp)


def paragraphs(page_text):
    """Split a page into paragraphs (blank-line separated), joined to one line."""
    out = []
    for block in re.split(r"\n\s*\n", page_text):
        p = re.sub(r"\s+", " ", block).strip()
        if p:
            out.append(p)
    return out


# --------------------------------------------------------------------------- #
# Index parsing (PDF pages 700-713)
# --------------------------------------------------------------------------- #

def _parse_page_numbers(raw):
    """'65-66, 208=209, 216-' -> sorted unique printed page numbers."""
    nums = []
    for part in re.split(r"[ ,]+", raw.strip()):
        part = part.replace("=", "-").replace("–", "-").strip("-")
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            if a.isdigit() and b.isdigit() and 0 <= int(b) - int(a) < 30:
                nums.extend(range(int(a), int(b) + 1))
            elif a.isdigit():
                nums.append(int(a))
        elif part.isdigit():
            nums.append(int(part))
    return sorted(set(n for n in nums if 1 <= n <= 698))


def _merge_wrapped(lines, prefix_re):
    """Re-join index entries that wrapped onto the next line.

    A trailing comma alone doesn't prove a wrap (most complete entries end with
    one) — merge only when the NEXT line is a continuation: it starts with a
    digit (page numbers wrapped) or the current line has no page digits yet
    (the name itself wrapped).
    """
    lines = [l.strip() for l in lines if l.strip()]
    merged = []
    i = 0
    while i < len(lines):
        l = lines[i]
        while (i + 1 < len(lines) and re.match(prefix_re, l) and l.endswith(",")
               and (lines[i + 1][0].isdigit()
                    or not re.search(r"\d", l))):
            i += 1
            l = l + " " + lines[i]
        merged.append(l)
        i += 1
    return merged


def parse_index(pages):
    idx_text = "\n".join(pages[INDEX_FIRST_PDF_PAGE - 1:])

    # -- lakes: LAKE, / LAKE-W, / LAKE-E, entries ---------------------------- #
    text = re.sub(r"(?<=[^\n])(LAKES?(?:-[EW])?,)", r"\n\1", idx_text)
    lake_entries = []
    pat = re.compile(r"^LAKES?(-[EW])?, (.+?),? ([\d ,=–-]+)$")
    region = {None: "main", "-E": "east", "-W": "west"}
    for l in _merge_wrapped(text.splitlines(), r"^LAKES?(?:-[EW])?,"):
        m = pat.match(l)
        if m:
            lake_entries.append({
                "name": m.group(2).strip().rstrip(","),
                "region": region[m.group(1)],
                "pages": _parse_page_numbers(m.group(3)),
            })

    # -- trailheads: TRAILHEAD: / TRAILHEAD-Western: / TRAILHEAD--minor--... - #
    text = re.sub(r"(?<=[^\n])(TRAILHEAD)", r"\n\1", idx_text)
    th_pat = re.compile(
        r"^TRAILHEAD(?P<tag>(?:--?[A-Za-z]+)*)[:,]? (?P<name>.+?),? (?P<pages>[\d ,=–-]+)$")
    trailheads = {}
    for l in _merge_wrapped(text.splitlines(), r"^TRAILHEAD\S*"):
        m = th_pat.match(l)
        if not m:
            continue
        tag = m.group("tag").strip("-").lower() or "main"
        name = re.sub(r"\s+", " ", m.group("name")).strip().rstrip(",.")
        raw_pages = m.group("pages")
        # "… Trail No. 017, 481": the trail number is part of the NAME, not a
        # page reference — put the first number back onto the name.
        if re.search(r"\bNo$", name):
            num, _, raw_pages = raw_pages.strip().partition(",")
            name = f"{name}. {num.strip()}"
        pages_ = _parse_page_numbers(raw_pages)
        if not name or not pages_:
            continue
        key = name.lower()
        if key in trailheads:  # same name indexed twice -> merge pages
            trailheads[key]["pages"] = sorted(set(trailheads[key]["pages"] + pages_))
        else:
            trailheads[key] = {"name": name, "region": tag, "pages": pages_}
    return lake_entries, list(trailheads.values())


# --------------------------------------------------------------------------- #
# Body mining
# --------------------------------------------------------------------------- #

DESIG_RE = re.compile(r"\(([A-Z]{1,2}-\d{1,3})\)")

# Trailheads whose drainage neither their name nor their pages' lake mentions
# resolve — curated by geography (e.g. Hoop Lake TH serves the Burnt Fork
# lakes; the three minor "Trail No." trailheads are Sheep Creek country).
MANUAL_DRAINAGE = {
    "Hoop Lake": "Burnt Fork Drainage",
    "China Meadows": "Smiths Fork Drainage",
    "Chepeta-Highline Trail": "White Rocks Drainage",
    "Crystal Lake & Bald Mt": "Provo River Drainage",
    "Beaver Meadows": "Beaver Creek Drainage",
    "Beaver Meadows Reservoir": "Beaver Creek Drainage",
    "Crow Basin (Canyon)": "Dry Gulch Drainage",
    "Highline Trail - Leidy Peak, and area": "Ashley Creek Drainage",
    "Highline Trail, eastern end": "Ashley Creek Drainage",
    "Browne-/Spirit Lake Trail No. 017": "Sheep/Carter Creek Drainages",
    "Hickerson Park Trail No. 022a": "Sheep/Carter Creek Drainages",
    "N. Fk. Sheep Ck. Trail No. 023": "Sheep/Carter Creek Drainages",
}


def lake_excerpts(pages, db_designations):
    """designation -> [(printed_page, paragraph_text), ...] from the book body."""
    found = {}
    for pdf_page in range(1, INDEX_FIRST_PDF_PAGE):  # body only, not the index
        printed = pdf_page - PAGE_OFFSET
        if printed < 1:
            continue
        for para in paragraphs(pages[pdf_page - 1]):
            desigs = {d for d in DESIG_RE.findall(para) if d in db_designations}
            for d in desigs:
                excerpt = para
                if len(excerpt) > MAX_EXCERPT_CHARS:
                    cut = excerpt[:MAX_EXCERPT_CHARS]
                    excerpt = cut[:cut.rfind(" ")] + " …"
                found.setdefault(d, []).append((printed, excerpt))
    return found


def build_cma_notes(excerpts):
    """List of (printed_page, text) -> one markdown blob for lakes.cma_notes."""
    parts = []
    for printed, text in excerpts[:MAX_EXCERPTS_PER_LAKE]:
        parts.append(f"{text} *(p. {printed})*")
    skipped = len(excerpts) - MAX_EXCERPTS_PER_LAKE
    if skipped > 0:
        more_pages = sorted({p for p, _ in excerpts[MAX_EXCERPTS_PER_LAKE:]})
        parts.append("*Also mentioned on pages "
                     + ", ".join(str(p) for p in more_pages) + ".*")
    return "\n\n".join(parts)


def _page_runs(printed_pages):
    """[5,6,27,160,161] -> [[5,6],[27],[160,161]] (consecutive runs)."""
    runs = []
    for p in printed_pages:
        if runs and p == runs[-1][-1] + 1:
            runs[-1].append(p)
        else:
            runs.append([p])
    return runs


def trailhead_info(pages, printed_pages):
    """Intro excerpt: prefer the 'HOW TO GET HERE' page, else the start of the
    trailhead's own section (the longest/last run of pages — early single pages
    are usually passing mentions in overview chapters)."""
    candidates = [p for p in printed_pages
                  if "HOW TO GET HERE" in pages[p + PAGE_OFFSET - 1]]
    if candidates:
        page = candidates[0]
    else:
        runs = _page_runs(printed_pages)
        page = max(reversed(runs), key=len)[0]
    paras = paragraphs(pages[page + PAGE_OFFSET - 1])
    # Drop a trailing bare folio number
    if paras and re.fullmatch(r"\d{1,3}", paras[-1]):
        paras.pop()
    out = ""
    for p in paras:
        if len(out) + len(p) > MAX_TRAILHEAD_INFO_CHARS and out:
            break
        out += ("\n\n" if out else "") + p
    return out[:MAX_TRAILHEAD_INFO_CHARS], page


def trailhead_lake_links(pages, printed_pages, db_designations):
    desigs = set()
    for printed in printed_pages:
        page_text = pages[printed + PAGE_OFFSET - 1]
        desigs |= {d for d in DESIG_RE.findall(page_text) if d in db_designations}
    return sorted(desigs)


# --------------------------------------------------------------------------- #
# DB write
# --------------------------------------------------------------------------- #

def ensure_schema(conn):
    from database_utils import create_database  # canonical schema incl. cma tables
    create_database(DB_PATH).close()
    return conn


def main():
    writer_guard.exit_if_readonly("import_cma_book")

    pages = extract_pages()
    print(f"Extracted {len(pages)} PDF pages of text")

    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    lake_rows = conn.execute(
        "SELECT letter_number, drainage FROM lakes").fetchall()
    db_designations = {r[0] for r in lake_rows}
    drainage_of = dict(lake_rows)
    drainage_names = [r[0] for r in conn.execute("SELECT name FROM drainages")]

    lake_entries, trailheads = parse_index(pages)
    print(f"Index parsed: {len(lake_entries)} lake entries, "
          f"{len(trailheads)} trailheads")

    # --- lakes.cma_notes --------------------------------------------------- #
    excerpts = lake_excerpts(pages, db_designations)
    conn.execute("UPDATE lakes SET cma_notes = NULL")
    for desig, exc in excerpts.items():
        conn.execute("UPDATE lakes SET cma_notes = ? WHERE letter_number = ?",
                     (build_cma_notes(exc), desig))
    print(f"cma_notes written for {len(excerpts)} lakes")

    # --- trailheads + links ------------------------------------------------ #
    conn.execute("DELETE FROM trailhead_lakes")
    conn.execute("DELETE FROM trailheads")
    n_links = 0
    for th in trailheads:
        info, info_page = trailhead_info(pages, th["pages"])
        links = trailhead_lake_links(pages, th["pages"], db_designations)
        # Drainage: a DB drainage named IN the trailhead name wins (high
        # precision); otherwise majority drainage of the linked lakes.
        # spaces removed too: the DB says "White Rocks", the book "Whiterocks"
        norm = lambda s: re.sub(r"[^a-z]", "", s.lower())
        drainage = next(
            (dn for dn in drainage_names
             if norm(dn.replace(" Drainage", "").replace(" Drainages", ""))
             in norm(th["name"])),
            None)
        if drainage is None:
            counts = Counter(drainage_of[d] for d in links if drainage_of.get(d))
            if counts:
                drainage = counts.most_common(1)[0][0]
        if drainage is None:
            drainage = MANUAL_DRAINAGE.get(th["name"])
        cur = conn.execute(
            """INSERT INTO trailheads (name, region, drainage, pages, info)
               VALUES (?, ?, ?, ?, ?)""",
            (th["name"], th["region"], drainage,
             ",".join(str(p) for p in th["pages"]), info))
        th_id = cur.lastrowid
        for d in links:
            conn.execute(
                """INSERT INTO trailhead_lakes (trailhead_id, lake_id)
                   SELECT ?, id FROM lakes WHERE letter_number = ?""",
                (th_id, d))
        n_links += len(links)
        th["drainage"] = drainage
        th["lakes"] = links
        th["info_page"] = info_page
    print(f"trailheads: {len(trailheads)} rows, {n_links} lake links")

    conn.commit()
    conn.close()

    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump({"lakes": lake_entries, "trailheads": trailheads}, f,
                  indent=1, ensure_ascii=False)
    print(f"Wrote {INDEX_JSON}")


if __name__ == "__main__":
    main()
