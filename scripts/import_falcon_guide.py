#!/usr/bin/env python3
"""
Import Falcon's "Hiking Utah's High Uintas" (3rd ed., Andrew Dash Gillman, 2024)
from the purchased, DRM-stripped EPUB into the guide_* tables of uinta_lakes.db.

The book is a clean, Sigil-authored EPUB organized as:
    3 regional Parts  ->  named TRAILHEAD sections  ->  90 numbered hikes.
Each hike chapter (OEBPS/Text/ChapterNN.xhtml) carries a labeled field block
    <div class="boxc"> <b>Start:</b> <span class="grey">...</span> ... </div>
(Start/Distance/Destination elevation/Approximate hiking time/Difficulty/Usage/
Nearest town/Drainage) followed by "THE HIKE" and "FINDING THE TRAILHEAD"
narrative sections. The narrative names lakes both by designation ("Lake BR-24",
en-dash in the source) and by name ("Amethyst Lake").

This importer parses that structure and links each hike to the lakes it reaches,
reusing the conservative matcher (database_utils.find_matching_lake): a lake is
credited only on an exact letter-number designation or an exact normalized name
(trailing "Lake"/"Reservoir" stripped). Matching is scoped to each hike's own
text, which avoids the sentence-start false positives a global scan produces.

The source EPUB is copyrighted and gitignored (data/falcon_guide/*.epub); only
the derived, structured data is committed (DB seeds + lakes_data.json), exactly
like the Cordell Andersen book pipeline (import_cma_book.py).

Usage:
    python3 scripts/import_falcon_guide.py --dump      # parse only, print summary
    python3 scripts/import_falcon_guide.py             # parse + write to the DB
"""

import argparse
import html
import os
import re
import sqlite3
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

from database_utils import (LAKE_SUFFIX_WORDS, _strip_trailing,  # noqa: E402
                            extract_letter_number, normalize_lake_name)
from writer_guard import exit_if_readonly       # noqa: E402

DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
EPUB_PATH = os.path.join(PROJECT_DIR, "data", "falcon_guide",
                         "hiking-utahs-high-uintas-3e.epub")

FIELD_LABELS = {
    "Start": "start_trailhead",
    "Distance": "distance",
    "Destination elevation": "destination_elevation",
    "Approximate hiking time": "hiking_time",
    "Difficulty": "difficulty",
    "Usage": "usage",
    "Nearest town": "nearest_town",
    "Drainage": "drainage",
}


# --------------------------------------------------------------------------- #
# EPUB reading
# --------------------------------------------------------------------------- #
def _read_epub(path):
    """Return {arcname: text} for OEBPS/Text/*.xhtml plus the toc.ncx text."""
    files = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith(".xhtml") and "/Text/" in name:
                files[os.path.basename(name)] = z.read(name).decode("utf-8")
            elif name.endswith("toc.ncx"):
                files["toc.ncx"] = z.read(name).decode("utf-8")
    return files


def _toc_order(ncx):
    """Ordered [(label, chapter_file)] from the NCX, fragments dropped."""
    out = []
    for label, src in re.findall(
        r"<navPoint[^>]*>.*?<text>(.*?)</text>.*?<content src=\"(.*?)\"",
        ncx, re.S,
    ):
        out.append((html.unescape(label).strip(),
                    os.path.basename(src.split("#")[0])))
    return out


# --------------------------------------------------------------------------- #
# HTML -> text helpers
# --------------------------------------------------------------------------- #
def _clean(fragment):
    """Strip tags from an HTML fragment -> collapsed plain text."""
    fragment = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(fragment)
    # en-dash/em-dash used in designations ("BR-24") -> hyphen; keep others.
    return re.sub(r"[ \t ]+", " ", text).strip()


def _section_text(body_html, heading):
    """Plain text between an <h5> whose text == heading and the next <h5>."""
    m = re.search(
        r"<h5[^>]*>\s*(?:<[^>]+>\s*)*" + re.escape(heading) +
        r"\s*(?:</[^>]+>\s*)*</h5>(.*?)(?=<h5|\Z)",
        body_html, re.S | re.I,
    )
    if not m:
        return None
    # keep paragraph breaks as blank lines for readable markdown-ish output
    chunk = re.sub(r"</p\s*>", "\n\n", m.group(1), flags=re.I)
    return _clean(chunk).strip() or None


def _parse_fields(body_html):
    """Extract the <div class='boxc'> label/value field block."""
    box = re.search(r"<div class=\"boxc\">(.*?)</div>", body_html, re.S)
    if not box:
        return {}, None
    fields, pages = {}, None
    for label, value in re.findall(
        r"<b>\s*(.*?)\s*:?\s*</b>\s*(?:<span[^>]*>)?(.*?)(?:</span>)?\s*</p>",
        box.group(1), re.S,
    ):
        lab = _clean(label).rstrip(":").strip()
        val = _clean(value).strip()
        if lab in FIELD_LABELS:
            fields[FIELD_LABELS[lab]] = val
        elif re.search(r"\bpages?\b", lab, re.I):
            # "See map and logistics on pages 38 and 42." or the split form
            # "See map on page 39 and logistics on page 22." — collect every
            # page number/range in the sentence, in order, de-duped.
            nums, seen = [], set()
            for tok in re.findall(r"\d+(?:[–-]\d+)?", lab):
                if tok not in seen:
                    seen.add(tok)
                    nums.append(tok)
            if nums:
                pages = ", ".join(nums)
    return fields, pages


# --------------------------------------------------------------------------- #
# Lake mentions -> candidate name strings
# --------------------------------------------------------------------------- #
_DESIG_RE = re.compile(r"\b([A-Z]{1,3})[-–](\d{1,3})\b")
_NAME_RE = re.compile(r"\b((?:[A-Z][a-z]+\s+){0,2}[A-Z][a-z]+)\s+Lakes?\b")


def _candidate_groups(*texts):
    """Yield candidate GROUPS — one list of water-name strings per mention,
    ordered longest-first. The matcher must take the first candidate in a
    group that names any lake at all and go no further: "Lower Red Castle
    Lake" has to stop at G-12, never fall through to a phantom "Castle Lake"
    (D-14, a different drainage entirely). The shorter fallbacks exist only
    for sentence-start noise ("Follow Big Elk Lake" -> "Big Elk Lake")."""
    seen = set()
    for text in texts:
        if not text:
            continue
        norm = text.replace("–", "-").replace("—", "-")
        for a, b in _DESIG_RE.findall(norm):
            c = f"{a}-{b}"
            if c not in seen:
                seen.add(c)
                yield [c]
        for phrase in _NAME_RE.findall(text):
            words = phrase.split()
            group = [phrase]
            if len(words) >= 3:
                group.append(" ".join(words[-2:]))
            if len(words) >= 2:
                group.append(words[-1])
            group = [g + " Lake" for g in group]
            key = tuple(g.lower() for g in group)
            if key not in seen:
                seen.add(key)
                yield group
        # comma/and lists sharing a trailing "Lakes": "Jean, Dean, and Daynes
        # Lakes", and the two-name form "between Betsy and Grandaddy Lakes"
        for lst in re.findall(
            r"((?:[A-Z][a-z]+,\s+)*[A-Z][a-z]+(?:,?\s+and\s+[A-Z][a-z]+)?)\s+Lakes\b", text):
            if "," not in lst and " and " not in lst:
                continue
            for part in re.split(r",\s*|\s+and\s+", lst):
                part = part.strip()
                if part and part.lower() not in seen:
                    seen.add(part.lower())
                    yield [part + " Lake"]


# --------------------------------------------------------------------------- #
# Parse the whole book
# --------------------------------------------------------------------------- #
def parse_book(epub_path):
    files = _read_epub(epub_path)
    order = _toc_order(files["toc.ncx"])

    regions = []        # {part_number, name, description}
    trailheads = {}     # name -> {name, part_number, description, maps}
    hikes = []          # dicts

    cur_part = None
    part_intro_file = {}

    # First pass: map each Part label to its file, and detect part membership.
    part_of_file = {}
    part_seq = 0
    for label, f in order:
        pm = re.match(r"Part\s+(\d+)\s*:\s*(.+)", label, re.I)
        if pm:
            part_seq = int(pm.group(1))
            part_intro_file[part_seq] = f
        if f.startswith("Part"):
            continue
        part_of_file.setdefault(f, part_seq)

    # Region descriptions from the Part intro files.
    for pnum, f in part_intro_file.items():
        body = files.get(f, "")
        name = ""
        pm = None
        for label, ff in order:
            if ff == f:
                m = re.match(r"Part\s+\d+\s*:\s*(.+)", label, re.I)
                if m:
                    name = m.group(1).strip()
                    break
        # description = all paragraphs in the part file
        desc = _clean(re.sub(r"</p\s*>", "\n\n", body, flags=re.I))
        # drop the repeated title lines at the top
        regions.append({"part_number": pnum, "name": name,
                        "description": desc})

    # Second pass: classify each unique chapter file.
    label_of_file = {}
    for label, f in order:
        label_of_file.setdefault(f, label)

    for f in sorted(set(part_of_file) | set(label_of_file),
                    key=lambda n: (int(re.sub(r"\D", "", n) or 0), n)):
        if not f.startswith("Chapter"):
            continue
        body = files.get(f)
        if body is None:
            continue
        pnum = part_of_file.get(f)
        label = label_of_file.get(f, "")
        fields, pages = _parse_fields(body)

        if "start_trailhead" in fields:
            # ---- a numbered HIKE ----
            hm = re.match(r"(\d+)\.\s*(.+)", label)
            num = int(hm.group(1)) if hm else None
            name = hm.group(2).strip() if hm else _clean(
                re.search(r"<h[1-4][^>]*>(.*?)</h[1-4]>", body, re.S).group(1)
                if re.search(r"<h[1-4]", body) else label)
            hikes.append({
                "hike_number": num,
                "name": name,
                "part_number": pnum,
                "narrative": _section_text(body, "THE HIKE"),
                "finding_trailhead": _section_text(body, "FINDING THE TRAILHEAD"),
                "source_pages": pages,
                "source_file": f,
                **fields,
            })
        else:
            # ---- a TRAILHEAD section (ALL-CAPS heading, no field block) ----
            if not label or not label.isupper():
                continue
            name = _title_case_trailhead(label)
            maps = None
            mm = re.search(r"Maps?:\s*(.+)", _clean(body))
            if mm:
                maps = mm.group(1).split("  ")[0].strip()[:400]
            trailheads[name] = {
                "name": name,
                "part_number": pnum,
                "description": _trailhead_description(body),
                "maps": maps,
            }

    return regions, list(trailheads.values()), hikes


def _title_case_trailhead(label):
    """CHRISTMAS MEADOWS TRAILHEAD -> Christmas Meadows Trailhead.

    Capitalizes each word (also after '/' and '(') except a few connectives,
    which stay lowercase unless they lead. 'Fork', 'West', etc. are proper here.
    """
    small = {"of", "the", "and", "to", "at", "or"}

    def cap_token(tok):
        # capitalize the first alphabetic char, keep the rest as-is (lowered)
        for i, ch in enumerate(tok):
            if ch.isalpha():
                return tok[:i] + ch.upper() + tok[i + 1:]
        return tok

    words = []
    for w in label.split():
        lw = w.lower()
        if lw in small and words:
            words.append(lw)
        else:
            # handle 'paradise park/blanchett' and '(west)'
            words.append(re.sub(r"[A-Za-z][a-z]*",
                                lambda m: cap_token(m.group(0)),
                                lw))
    return " ".join(words)


def _th_key(name):
    """Loose key for matching a hike's 'Start:' value to a trailhead section."""
    k = (name or "").lower()
    k = re.sub(r"\(.*?\)", " ", k)                      # drop parentheticals
    k = re.sub(r"\b(trailhead|lake|area|pass|the|end|of|road)\b", " ", k)
    return re.sub(r"[^a-z]+", "", k)


def _trailhead_description(body):
    paras = re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
    cleaned = [_clean(p) for p in paras if _clean(p)]
    # drop leading repeated ALL-CAPS title lines and the trailing "Maps:" /
    # "See trails N through M" cross-reference lines — those become the `maps`
    # column and are implicit from the hikes.
    out = []
    for p in cleaned:
        if p.isupper():
            continue
        if re.match(r"(See (map|trail)|Maps?:)", p):
            continue
        out.append(p)
    return "\n\n".join(out).strip() or None


# The book's "Drainage:" field -> lakes.drainage value(s). Lake NAMES repeat
# across the range (two Crystals, four Islands, ...), so an exact-name match
# alone picks an arbitrary duplicate — the original import credited the
# Provo-side Crystal Lake hikes to GR-128 Crystal in Burnt Fork. A hike's own
# Drainage field is the book's ground truth for which duplicate it means.
_BOOK_TO_DB_DRAINAGE = {
    "Ashley Creek": "Ashley Creek Drainage",
    "Bear River": "Bear River Drainage",
    "Beaver Creek": "Beaver Creek Drainage",
    "Burnt Fork": "Burnt Fork Drainage",
    "Carter Creek": "Sheep/Carter Creek Drainages",
    "Duchesne River": "Duchesne River Drainage",
    "East Fork Blacks Fork": "Blacks Fork Drainage",
    "Henrys Fork": "Henrys Fork Drainage",
    "Lake Fork": "Lake Fork Drainage",
    "Provo River": "Provo River Drainage",
    "Rock Creek": "Rock Creek Drainage",
    "Sheep Creek": "Sheep/Carter Creek Drainages",
    "Smiths Fork": "Smiths Fork Drainage",
    "Swift Creek": "Swift Creek Drainage",
    "Uinta River": "Uinta River Drainage",
    "Weber River": "Weber River Drainage",
    "Whiterocks River": "White Rocks Drainage",
    "Yellowstone River": "Yellowstone Drainage",
}


def _hike_db_drainages(book_drainage):
    """DB drainage(s) for a hike's Drainage field ("A or B" yields both)."""
    out = set()
    for part in re.split(r"\s+or\s+", book_drainage or ""):
        db = _BOOK_TO_DB_DRAINAGE.get(part.strip())
        if db:
            out.add(db)
    return out


# Lakes the DB names as members of a family — directional ("Kidney East"/
# "Kidney West"), numbered ("Divide, #1"/"Divide #2", "Chain 1 (Lower)"),
# or with a parenthetical alternate ("Shallow (Haystack #2)") — are what
# the book calls collectively or plainly ("Kidney Lakes", "Divide Lakes",
# "Haystack Lake"). Index them under those base names too, as non-exact
# ALIASES. An alias never outranks an exact name, but its presence marks a
# bare name as geographically ambiguous: "Kidney Lakes" in a Uinta River
# hike must not fall through to Lake Fork's X-35 just because bare
# "Kidney" is unique among exact names.
_DIRECTIONAL = {"EAST", "WEST", "NORTH", "SOUTH", "UPPER", "LOWER", "MIDDLE"}


def _alias_bases(key):
    """Alternate lookup keys for a normalized DB lake name (see above)."""
    bases = set()
    stripped = re.sub(r"\s*\([^)]*\)$", "", key).strip()
    inner = re.search(r"\(([^)]*)\)$", key)
    variants = {stripped, inner.group(1).strip() if inner else ""}
    # The book says "Five Point Lake" for what the DB names "Five Point
    # Reservoir" (X-106) — index reservoir names minus the suffix as
    # aliases too. This is the REVERSE of the DWR stocking rule ("Echo
    # Reservoir" must never name-match the Z-16 "Echo" lake): here the
    # RESERVOIR is on the curated-lake side, and the alias only ever
    # matches in-drainage, so a lowland water can't sneak in.
    for v in list(variants):
        if v.endswith(" RESERVOIR"):
            variants.add(v[: -len(" RESERVOIR")].strip())
    for variant in variants:
        if not variant:
            continue
        bases.add(variant)
        bases.add(re.sub(r"[,\s]*#?\d+$", "", variant).strip())
        words = variant.split()
        if len(words) >= 2:
            if words[-1] in _DIRECTIONAL:
                bases.add(" ".join(words[:-1]))
            elif words[0] in _DIRECTIONAL:
                bases.add(" ".join(words[1:]))
    return {b for b in bases if b and b != key and b not in _DIRECTIONAL}


# Hand-reviewed resolutions (2026-08-28, checked against the DWR pamphlet
# notes in this DB) for the mentions the conservative matcher reports as
# unresolvable — keyed by (hike_number, normalized mention key). A
# letter_number links that lake with method 'manual'; None records
# "reviewed: correctly no link" (a trailhead name-drop, or an alternate
# name for a lake the hike already links) so re-imports only report NEW,
# unreviewed drops.
# Book spellings that differ from the DB/DWR name, keyed by the normalized
# DB name -> alternate normalized spellings. Indexed as EXACT names (not
# family aliases), so they resolve like the real name and stay subject to
# the same drainage scoping. Add here when the book consistently misspells
# a lake rather than hand-linking every hike that mentions it.
_SPELLING_ALIASES = {
    "BETSEY": ("BETSY",),       # X-7 "Betsey" (DWR) — Falcon writes "Betsy Lake" (hikes 33, 34)
}

_MANUAL_LINKS = {
    (8,  "NORTH TWIN"): None,   # the Provo Twins (A-32/A-33) already linked; GR-50 is Dry Fork's
    (23, "CRYSTAL"): None,      # "...Lakes Country Trail of Crystal Lake trailhead fame" — name-drop
    (46, "CRATER"): "X-94",     # DWR: "northeast base of Explorer Peak"; LF-2 is Lambert Meadows' Crater
    (56, "ISLAND"): None,       # "Pippen Lake (sometimes called Island Lake)" — U-9 already linked
    (60, "CLEVELAND"): "WR-7",  # before Fox-Queant Pass: the Whiterocks-side Cleveland
    (62, "CLEVELAND"): "WR-7",
    (85, "BEAVER"): "GR-147",   # right off Burnt Ridge into Middle Fork Beaver Creek (hike 83's lake)
    (86, "HIDDEN"): "GR-112",   # DWR: "0.8 miles northwest of the Spirit Lake campground" (by Tamarack)
    (87, "FISH"): "GR-125",     # DWR: "atop the divide between the Burnt Fork and Sheep Creek drainage"
    (89, "HIDDEN"): "GR-7",     # DWR: "0.7 miles northwest of Lower Anson Lake in Weyman Lakes Basin"
}


def link_lakes(cursor, hikes):
    """Attach matched lake letter_numbers to each hike dict.

    Matching mirrors database_utils.find_matching_lake (exact designation,
    else exact normalized name) but resolves DUPLICATE names by drainage:
    "Crystal Lake" in a Provo River hike is A-51, not Burnt Fork's GR-128.
    Two passes per hike — first against the hike's own Drainage field, then
    (for hikes that cross a divide, e.g. the Weber-drainage hikes starting at
    Crystal Lake trailhead) against the drainages of the lakes the hike has
    already matched unambiguously. A duplicate name with no single candidate
    in either scope is dropped rather than guessed.
    """
    by_designation, by_name, id_to_ln = {}, {}, {}
    lake_drainage, lake_coords = {}, {}
    for lid, ln, name, drainage, lat, lng in cursor.execute(
            "SELECT id, letter_number, name, drainage, lat, lng FROM lakes"):
        by_designation[ln] = lid
        id_to_ln[lid] = ln
        lake_drainage[lid] = drainage
        if lat is not None and lng is not None:
            lake_coords[lid] = (lat, lng)
        key = _strip_trailing(normalize_lake_name(name or ""),
                              LAKE_SUFFIX_WORDS)
        if not key:
            continue
        by_name.setdefault(key, []).append((lid, drainage, True))
        for alt in _SPELLING_ALIASES.get(key, ()):
            by_name.setdefault(alt, []).append((lid, drainage, True))
        for base in _alias_bases(key):
            by_name.setdefault(base, []).append((lid, drainage, False))

    dropped = set()

    def lone_exact_in_basin(cands, ctx_pts):
        """A key with ONE exact-named lake plus directional aliases, none in
        scope ("Red Castle Lake" in an East Fork Blacks Fork hike): keep the
        exact only if coordinates prove it sits in the same basin as the
        candidate nearest the hike's other lakes — every candidate must have
        coords, or we can't rule the aliases out (Kidney: U-25/U-26 have no
        coords, so a Whiterocks hike's "Kidney Lakes" is dropped instead of
        mis-crediting Lake Fork's X-35)."""
        exact = [c for c in cands if c[2]]
        if len(exact) != 1 or not ctx_pts:
            return None
        if any(c[0] not in lake_coords for c in cands):
            return None
        cy = sum(p[0] for p in ctx_pts) / len(ctx_pts)
        cx = sum(p[1] for p in ctx_pts) / len(ctx_pts)

        def km(lid):
            lat, lng = lake_coords[lid]
            return (((lat - cy) * 111.0) ** 2 +
                    ((lng - cx) * 85.0) ** 2) ** 0.5
        dists = {c[0]: km(c[0]) for c in cands}
        if dists[exact[0][0]] <= min(dists.values()) + 3.0:
            return exact[0][0]
        return None

    def resolve(cand, drainages, ctx_pts=None):
        """(list_of_lake_ids, method) or ([], ambiguous_bool)."""
        ln = extract_letter_number(cand)
        if ln and ln in by_designation:
            return [by_designation[ln]], "exact"
        key = _strip_trailing(normalize_lake_name(cand), LAKE_SUFFIX_WORDS)
        cands = by_name.get(key, [])
        if len(cands) == 1 and cands[0][2]:
            return [cands[0][0]], "name"
        scoped = [c for c in cands if c[1] in drainages]
        exact_scoped = [c for c in scoped if c[2]]
        if len(exact_scoped) == 1:
            return [exact_scoped[0][0]], "name-drainage"
        if scoped and not exact_scoped:
            # A directional family the book names collectively ("Kidney
            # Lakes" -> Kidney East + Kidney West): link the whole group.
            return ([c[0] for c in scoped],
                    "name-drainage" if len(scoped) == 1 else "name-group")
        if scoped:
            return [], True
        if ctx_pts is not None:
            lid = lone_exact_in_basin(cands, ctx_pts)
            if lid is not None:
                return [lid], "name"
        return [], bool(cands)

    def group_candidate(group):
        """First candidate in the group that names any lake; None if none."""
        for cand in group:
            ln = extract_letter_number(cand)
            if ln and ln in by_designation:
                return cand
            key = _strip_trailing(normalize_lake_name(cand),
                                  LAKE_SUFFIX_WORDS)
            if key in by_name:
                return cand
        return None

    for h in hikes:
        drainages = _hike_db_drainages(h.get("drainage"))
        body_cands = [c for c in map(group_candidate, _candidate_groups(
            h.get("narrative"), h.get("finding_trailhead"), h["name"])) if c]
        matches, pending = {}, []
        for cand in body_cands:
            lids, method = resolve(cand, drainages)
            for lid in lids:
                matches.setdefault(lid, method)
            if not lids and method:
                pending.append(cand)
        # Second pass: a hike that crosses a divide names lakes outside its
        # own drainage — widen the scope to every drainage it already
        # matched a lake in, and keep only still-unique candidates. The
        # matched lakes' coordinates also anchor the lone-exact basin check.
        widened = drainages | {lake_drainage[lid] for lid in matches}
        ctx_pts = [lake_coords[lid] for lid in matches if lid in lake_coords]
        for cand in pending:
            lids, method = resolve(cand, widened, ctx_pts)
            if lids:
                for lid in lids:
                    matches.setdefault(
                        lid, "name-group" if len(lids) > 1 else "name-context")
            else:
                key = _strip_trailing(normalize_lake_name(cand),
                                      LAKE_SUFFIX_WORDS)
                if (h["hike_number"], key) in _MANUAL_LINKS:
                    ln = _MANUAL_LINKS[(h["hike_number"], key)]
                    if ln:
                        matches.setdefault(by_designation[ln], "manual")
                else:
                    alts = tuple(sorted(id_to_ln[l]
                                        for l, _, _ in by_name.get(key, [])))
                    dropped.add((h["hike_number"], cand, alts))

        primary_ids = set()
        for group in _candidate_groups(h["name"] or ""):
            cand = group_candidate(group)
            if cand:
                lids, method = resolve(cand, widened, ctx_pts)
                primary_ids.update(lids)

        h["lakes"] = [
            {"letter_number": id_to_ln[lid], "method": method,
             "is_primary": 1 if lid in primary_ids else 0}
            for lid, method in matches.items()
        ]

    if dropped:
        print(f"Ambiguous names dropped (no single candidate in scope): "
              f"{len(dropped)}")
        for hn, cand, lns in sorted(dropped, key=lambda x: (x[0] or 0, x[1])):
            print(f"  hike #{hn}: {cand} -> {', '.join(lns)}")


# --------------------------------------------------------------------------- #
# Write to the DB (idempotent: replaces all guide_* rows each run)
# --------------------------------------------------------------------------- #
def write_db(conn, regions, trailheads, hikes):
    cur = conn.cursor()
    # Fresh load every run — guide_* are wholly derived from the EPUB, so we
    # clear and repopulate rather than diff (children first for FK safety).
    for t in ("guide_hike_lakes", "guide_hikes", "guide_trailheads",
              "guide_regions"):
        cur.execute(f"DELETE FROM {t}")

    region_id = {}
    for r in regions:
        cur.execute(
            "INSERT INTO guide_regions (part_number, name, description) "
            "VALUES (?, ?, ?)", (r["part_number"], r["name"], r["description"]))
        region_id[r["part_number"]] = cur.lastrowid

    th_id, th_key_to_id = {}, {}
    for t in trailheads:
        cur.execute(
            "INSERT INTO guide_trailheads (name, region_id, description, maps) "
            "VALUES (?, ?, ?, ?)",
            (t["name"], region_id.get(t["part_number"]), t["description"],
             t["maps"]))
        th_id[t["name"]] = cur.lastrowid
        th_key_to_id[_th_key(t["name"])] = cur.lastrowid

    lake_id = {ln: lid for lid, ln in cur.execute(
        "SELECT id, letter_number FROM lakes")}

    for h in hikes:
        thid = th_key_to_id.get(_th_key(h.get("start_trailhead")))
        cur.execute(
            """INSERT INTO guide_hikes
               (hike_number, name, region_id, trailhead_id, start_trailhead,
                distance, destination_elevation, hiking_time, difficulty,
                usage, nearest_town, drainage, narrative, finding_trailhead,
                source_pages, source_file)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (h["hike_number"], h["name"], region_id.get(h["part_number"]),
             thid, h.get("start_trailhead"), h.get("distance"),
             h.get("destination_elevation"), h.get("hiking_time"),
             h.get("difficulty"), h.get("usage"), h.get("nearest_town"),
             h.get("drainage"), h.get("narrative"), h.get("finding_trailhead"),
             h.get("source_pages"), h.get("source_file")))
        hid = cur.lastrowid
        for l in h["lakes"]:
            cur.execute(
                """INSERT OR IGNORE INTO guide_hike_lakes
                   (hike_id, lake_id, match_method, is_primary)
                   VALUES (?, ?, ?, ?)""",
                (hid, lake_id[l["letter_number"]], l["method"], l["is_primary"]))

    conn.commit()
    linked = sum(len(h["lakes"]) for h in hikes)
    print(f"Wrote {len(regions)} regions, {len(trailheads)} trailheads, "
          f"{len(hikes)} hikes, {linked} hike-lake links to the DB.")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true",
                    help="parse only; print a summary and don't touch the DB")
    ap.add_argument("--epub", default=EPUB_PATH)
    ap.add_argument("--db", default=DB_PATH)
    args = ap.parse_args()

    if not os.path.exists(args.epub):
        sys.exit(f"EPUB not found: {args.epub}\n"
                 "It is gitignored — decrypt the purchased Kobo copy first.")

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    regions, trailheads, hikes = parse_book(args.epub)
    link_lakes(cur, hikes)

    linked = sum(len(h["lakes"]) for h in hikes)
    distinct = len({l["letter_number"] for h in hikes for l in h["lakes"]})
    print(f"Parsed: {len(regions)} regions, {len(trailheads)} trailheads, "
          f"{len(hikes)} hikes")
    print(f"Lake links: {linked} total, {distinct} distinct lakes")
    nolake = [h["hike_number"] for h in hikes if not h["lakes"]]
    print(f"Hikes with no lake match: {sorted(x for x in nolake if x)}")

    if args.dump:
        for h in sorted(hikes, key=lambda x: x["hike_number"] or 0)[:5]:
            print("\n" + "=" * 60)
            for k in ("hike_number", "name", "part_number", "start_trailhead",
                      "distance", "difficulty", "drainage", "source_pages"):
                print(f"  {k:20}: {h.get(k)}")
            print(f"  lakes               : {h['lakes']}")
            print(f"  narrative[:160]     : {(h.get('narrative') or '')[:160]}")
        conn.close()
        return

    exit_if_readonly()
    write_db(conn, regions, trailheads, hikes)
    conn.close()


if __name__ == "__main__":
    main()
