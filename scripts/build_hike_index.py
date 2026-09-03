#!/usr/bin/env python3
"""
Build a query-friendly index of the Falcon "Hiking Utah's High Uintas" hikes.

The guide_* tables (from import_falcon_guide.py) store the book's fields as
free text ("5.6 to 6.9 miles out and back", "Moderate—one steep section",
"8.5 to 12 hours"). That is faithful but useless for questions like
"a hike between 8 and 14 miles that visits at least 3 lakes". This script
parses those fields into numbers/enums, joins each hike to the lakes it
reaches (with the lake's own attributes AND Jed's status), derives a few
aggregates, tags the narrative, and writes two reference files:

    data/hike_index.json   machine-readable (jq / python)
    data/hike_index.md     human/Claude-readable digest + per-hike blocks

Neither file is used by the app; they exist so "dig through the book for
me" questions can be answered quickly. Re-run after import_falcon_guide.py
or after lake statuses change (Jed's CAUGHT counts are baked in).

If the gitignored EPUB is present (Mini only) the one-paragraph intro blurb
that precedes each hike's field block is also captured as `summary`; on a
mirror the summary falls back to the first sentences of THE HIKE.

Usage:
    python3 scripts/build_hike_index.py            # writes both files
    python3 scripts/build_hike_index.py --stdout   # print the markdown
"""

import argparse
import html
import json
import os
import re
import sqlite3
import sys
import zipfile
from collections import OrderedDict, defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
EPUB_PATH = os.path.join(PROJECT_DIR, "data", "falcon_guide",
                         "hiking-utahs-high-uintas-3e.epub")
JSON_OUT = os.path.join(PROJECT_DIR, "data", "hike_index.json")
MD_OUT = os.path.join(PROJECT_DIR, "data", "hike_index.md")
BOOK_URL = "https://olaf.tailbf6340.ts.net/data/tailscale_book/falcon_guide/index.html"

_NUM = r"\d+(?:\.\d+)?"


# --------------------------------------------------------------------------- #
# Field parsers
# --------------------------------------------------------------------------- #
def parse_distance(text):
    """'5.6 to 6.9 miles out and back' -> numbers + route types."""
    out = {"distance_text": text, "distance_mi_min": None,
           "distance_mi_max": None, "route_types": [], "has_length_options": False}
    if not text:
        return out
    lead = re.split(r"\s*-?\s*miles?\b", text, maxsplit=1)[0]
    nums = [float(n) for n in re.findall(_NUM, lead)]
    if nums:
        out["distance_mi_min"] = min(nums)
        out["distance_mi_max"] = max(nums)
        out["has_length_options"] = len(nums) > 1
    low = text.lower()
    if "out and back" in low:
        out["route_types"].append("out and back")
    if "loop" in low:
        out["route_types"].append("loop")
    if "one way" in low or "one-way" in low:
        out["route_types"].append("one way")
    if "shuttle" in low:
        out["route_types"].append("shuttle")
    return out


def parse_time(text):
    """'8.5 to 12 hours' / '45 mins' / 'Variable' -> hours."""
    out = {"time_text": text, "time_hr_min": None, "time_hr_max": None,
           "time_variable": False}
    if not text:
        return out
    if re.search(r"variable", text, re.I):
        out["time_variable"] = True
        return out
    nums = [float(n) for n in re.findall(_NUM, text)]
    if not nums:
        return out
    if re.search(r"\bmin", text, re.I) and not re.search(r"\bh(ou)?rs?\b", text, re.I):
        nums = [n / 60.0 for n in nums]
    out["time_hr_min"] = round(min(nums), 2)
    out["time_hr_max"] = round(max(nums), 2)
    return out


def parse_elevation(text):
    m = re.search(r"(\d{1,2}),?(\d{3})", text or "")
    return int(m.group(1) + m.group(2)) if m else None


_LEVELS = OrderedDict([
    ("extremely difficult", 4), ("very difficult", 4),
    ("difficult", 3), ("strenuous", 3), ("high", 3),
    ("moderate", 2), ("easy", 1),
])
_LEVEL_NAME = {1: "Easy", 2: "Moderate", 3: "Difficult", 4: "Extremely difficult"}


def parse_difficulty(text):
    """'Moderate to difficult—several river crossings' -> ranks + note."""
    out = {"difficulty_text": text, "difficulty_min": None, "difficulty_max": None,
           "difficulty": None, "difficulty_note": None}
    if not text:
        return out
    parts = re.split(r"\s*[—–]\s*", text, maxsplit=1)
    head = parts[0]
    note = parts[1].strip() if len(parts) > 1 else None
    if "," in head and note is None:                  # "Easy, but long"
        head, note = [p.strip() for p in head.split(",", 1)]
    ranks = []
    low = head.lower()
    for word, rank in _LEVELS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", low):
            ranks.append(rank)
            low = low.replace(word, " ")
    if ranks:
        out["difficulty_min"] = min(ranks)
        out["difficulty_max"] = max(ranks)
        out["difficulty"] = _LEVEL_NAME[max(ranks)]
    out["difficulty_note"] = note or None
    return out


_USAGE = {"very light": 1, "light": 2, "moderate": 3, "heavy": 4, "high": 4}


def parse_usage(text):
    low = (text or "").strip().lower()
    return {"usage_text": text, "usage_rank": _USAGE.get(low)}


# --------------------------------------------------------------------------- #
# Narrative tagging (cheap regex flags; see TAG_RULES for what each means)
# --------------------------------------------------------------------------- #
TAG_RULES = OrderedDict([
    # tag             (regex, where)  where: hike | access | both
    ("camping",       (r"\bcamp(?:site|ing|s)?\b", "hike")),
    ("fishing",       (r"\b(?:fish|fishing|trout|angler|anglers|grayling)\b", "hike")),
    ("grayling",      (r"\bgrayling\b", "hike")),
    ("tiger-trout",   (r"\btiger\b", "hike")),
    ("cross-country", (r"\bcross-country\b|\bno (?:maintained |real )?trail\b|\bbushwhack", "hike")),
    ("navigation",    (r"\bgps\b|\bcompass\b|\bwayfinding\b|\bhard to follow\b|\bunmarked\b|\bcairn", "hike")),
    ("steep",         (r"\bsteep\b", "hike")),
    ("mountain-pass", (r"(?-i:[A-Z][a-z]+ Pass\b)|\bthe pass\b|\bmountain pass|\bover the pass|\bthe divide\b", "hike")),
    ("peak",          (r"\bsummit\b|\bpeak bagg|\bhighest point\b", "hike")),
    ("river-crossing",(r"\b(?:ford|fording|crossing the (?:river|creek)|river crossing|creek crossing|log crossing)", "hike")),
    ("horses",        (r"\bhorse|\bpack trip|\bequestrian|\bstock\b", "hike")),
    ("crowded",       (r"\bcrowd|\bpopular\b|\bheavy (?:use|pressure|traffic)", "hike")),
    ("solitude",      (r"\bsolitude\b|\bnobody else\b|\bseldom\b|\brarely visited\b|\bfew people\b", "hike")),
    ("bugs",          (r"\bmosquito|\bbugs?\b", "hike")),
    ("wildflowers",   (r"\bwildflower", "hike")),
    ("waterfall",     (r"\bwaterfall|(?-i:[A-Z][a-z]+ Falls\b)|\bcascade", "hike")),
    ("family",        (r"\bfamil(?:y|ies)\b|\bkids?\b|\bchildren\b", "hike")),
    ("wilderness",    (r"\bhigh uintas wilderness\b", "hike")),
    ("multi-day",     (r"\bbackpack|\bovernight|\bmulti-?day|\bbase ?camp|\btwo or three days|\bseveral days", "hike")),
    ("4wd",           (r"\b4wd\b|\b4x4\b|\bfour-wheel|\bhigh[- ]clearance|\brough road|\brutted|\brocky road", "access")),
    ("paved-access",  (r"\bpaved\b", "access")),
    ("toilets",       (r"\btoilet|\brestroom|\bouthouse", "access")),
    ("fee-area",      (r"\bfee\b", "access")),
])


def tag_text(hike_text, access_text):
    tags = []
    for tag, (rx, where) in TAG_RULES.items():
        src = hike_text if where == "hike" else access_text
        if src and re.search(rx, src, re.I):
            tags.append(tag)
    return tags


# --------------------------------------------------------------------------- #
# Optional EPUB blurbs
# --------------------------------------------------------------------------- #
def _epub_blurbs():
    """{ChapterNN.xhtml: intro paragraph} — only if the EPUB is present.
    Also stashes {file: 'Highest elevation' text} in _HIGHEST_ELEV for the
    two hikes (70 Highline, 75 Little East Fork) whose field block uses that
    label instead of 'Destination elevation' (which the importer doesn't map)."""
    if not os.path.exists(EPUB_PATH):
        return {}
    out = {}
    with zipfile.ZipFile(EPUB_PATH) as z:
        for name in z.namelist():
            if not (name.endswith(".xhtml") and "/Text/Chapter" in name):
                continue
            body = z.read(name).decode("utf-8")
            he = re.search(r"Highest elevation:\s*</b>\s*(?:<span[^>]*>)?([^<]+)", body)
            if he:
                _HIGHEST_ELEV[os.path.basename(name)] = he.group(1).strip()
            m = re.search(r"</h4>(.*?)<div class=\"boxc\">", body, re.S)
            if not m:
                continue
            paras = [re.sub(r"<[^>]+>", " ", p) for p in
                     re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S)]
            text = " ".join(html.unescape(p) for p in paras)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                out[os.path.basename(name)] = text
    return out


def _epub_sections():
    """{ChapterNN.xhtml: ALL-CAPS section heading it falls under} from the TOC.
    The book nests hikes under trailhead headings; guide_hikes.trailhead_id
    only captures the ones whose 'Start:' text matched a heading. Empty when
    the EPUB is absent."""
    if not os.path.exists(EPUB_PATH):
        return {}
    with zipfile.ZipFile(EPUB_PATH) as z:
        ncx = next((n for n in z.namelist() if n.endswith("toc.ncx")), None)
        if not ncx:
            return {}
        toc = z.read(ncx).decode("utf-8")
    out, cur = {}, None
    for label, src in re.findall(
            r"<navPoint[^>]*>.*?<text>(.*?)</text>.*?<content src=\"(.*?)\"", toc, re.S):
        f = os.path.basename(src.split("#")[0])
        label = html.unescape(label).strip()
        if f.startswith("Part"):
            cur = None
        elif f.startswith("Chapter"):
            if label.isupper():
                cur = label
            elif cur:
                out.setdefault(f, cur)
    return out


_HIGHEST_ELEV = {}


def _first_sentences(text, n=2):
    if not text:
        return None
    sents = re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip())
    return " ".join(sents[:n]).strip() or None


# --------------------------------------------------------------------------- #
# Trailhead access parsing
# --------------------------------------------------------------------------- #
_WORDNUM = {"a dozen": 12, "dozen": 12, "ten": 10, "twelve": 12, "fifteen": 15,
            "twenty": 20, "twenty-five": 25, "thirty": 30, "forty": 40,
            "fifty": 50, "sixty": 60, "seventy": 70, "one hundred": 100}


def parse_access(text):
    """Pull parking capacity + driving origin/miles out of trailhead prose."""
    out = {"parking_capacity": None, "drive_from": None}
    if not text:
        return out
    m = re.search(r"(?:room|space|spots?|parking|places?)\s+for\s+(?:about\s+|around\s+|more than\s+)?"
                  r"(\d+|[a-z-]+(?: [a-z]+)?)\s+(?:cars|vehicles|parking)", text, re.I)
    if not m:
        m = re.search(r"(\d+|[a-z-]+)\s+parking (?:spots|spaces|places)", text, re.I)
    if m:
        tok = m.group(1).lower()
        out["parking_capacity"] = int(tok) if tok.isdigit() else _WORDNUM.get(tok)
    m = re.search(r"From ([A-Z][A-Za-z .]+?)(?:,| \()", text)
    if m:
        out["drive_from"] = m.group(1).strip()
    return out


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def _species_list(fish_species):
    """'Cutthroats*, Tigers' -> [('Cutthroats', True), ('Tigers', False)]"""
    out = []
    for s in (fish_species or "").split(","):
        s = s.strip()
        if not s:
            continue
        hist = s.endswith("*")
        out.append((s.rstrip("*").strip(), hist))
    return out


_REF_SUFFIX = re.compile(
    r"\s+(?:Scenic Byway|Byway|Highway|trailhead|Trailhead|Campground|Road|"
    r"parking|Overlook|Guard Station|Ranger)\b")
_ROUTE_PREFIX = re.compile(
    r"\b(?:to|reach(?:es|ing)?|past|around|along|into|towards?|visit(?:ing)?|"
    r"camp(?:ing)? at|fish(?:ing)?)\s+(?:the\s+)?(?:\w+\s+)?$", re.I)
_REF_SENTENCE = re.compile(
    r"\b(?:starts? (?:at|from)|begins? (?:at|from)|trailheads?|access(?:ed|ible)? "
    r"(?:from|via)|other routes?)\b", re.I)


def mention_context(lake, texts):
    """'route' if the hike's text names this lake as somewhere the hike goes;
    'reference' if EVERY mention is a place-name-drop — "Mirror Lake Scenic
    Byway", "the Crystal Lake trailhead", "the others start at Hoop Lake and
    Spirit Lake". Heuristic; the matcher links on any mention, which inflates
    lake_count for the 'visits N lakes' question. Unknown when we can't find
    the mention at all (alias/manual links)."""
    text = "\n".join(t for t in texts if t).replace("\u2013", "-").replace("\u2014", "-")
    pats = [re.escape(lake["letter_number"])]
    if lake["name"]:
        base = re.sub(r"\s*\([^)]*\)$", "", lake["name"]).strip()
        base = re.sub(r"[,\s]*#?\d+$", "", base).strip()
        if base:
            pats.append(re.escape(base) + r"(?:\s+(?:Lakes?|Reservoir))?")
    found = False
    for pat in pats:
        for m in re.finditer(r"\b" + pat + r"\b", text):
            found = True
            if _REF_SUFFIX.match(text, m.end()):
                continue                      # "Mirror Lake Scenic Byway"
            if _ROUTE_PREFIX.search(text[max(0, m.start() - 40):m.start()]):
                return "route"                # "1.1 miles to Wall Lake"
            # sentence containing the mention
            start = max(text.rfind(". ", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
            end_c = [i for i in (text.find(". ", m.end()), text.find("\n", m.end())) if i >= 0]
            sentence = text[start:(min(end_c) if end_c else len(text))]
            if _REF_SENTENCE.search(sentence):
                continue                      # "the others start at Hoop Lake"
            return "route"
    return "reference" if found else "unknown"


def build(conn):
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    regions = {r["id"]: dict(r) for r in cur.execute("SELECT * FROM guide_regions")}
    ths = {r["id"]: dict(r) for r in cur.execute("SELECT * FROM guide_trailheads")}
    lakes = {r["id"]: dict(r) for r in cur.execute(
        "SELECT id, letter_number, name, drainage, basin, elevation_ft, size_acres, "
        "max_depth_ft, fish_species, fishing_pressure, status, starred, coord_status, "
        "no_fish, cma_notes IS NOT NULL AS has_cma, junesucker_notes IS NOT NULL AS has_js, "
        "jed_notes IS NOT NULL AND jed_notes != '' AS has_jed_notes "
        "FROM lakes")}
    links = defaultdict(list)
    for r in cur.execute("SELECT * FROM guide_hike_lakes"):
        links[r["hike_id"]].append(dict(r))
    blurbs = _epub_blurbs()
    sections = _epub_sections()
    th_by_key = {re.sub(r"[^a-z]", "", t["name"].lower()): tid for tid, t in ths.items()}

    hikes = []
    lake_hikes = defaultdict(list)
    th_hikes = defaultdict(list)
    for r in cur.execute("SELECT * FROM guide_hikes ORDER BY hike_number"):
        h = dict(r)
        region = regions.get(h["region_id"]) or {}
        th = ths.get(h["trailhead_id"]) or {}
        th_inferred = False
        if not th and h["source_file"] in sections:
            key = re.sub(r"[^a-z]", "", sections[h["source_file"]].lower())
            if key in th_by_key:
                th = ths[th_by_key[key]]
                th_inferred = True
        access_text = " ".join(t for t in (h.get("finding_trailhead"),
                                           th.get("description")) if t)

        lake_rows = []
        for l in sorted(links[h["id"]], key=lambda x: (-x["is_primary"], x["lake_id"])):
            lk = lakes[l["lake_id"]]
            sp = _species_list(lk["fish_species"])
            ctx = "route" if l["is_primary"] else mention_context(
                lk, (h.get("narrative"), h.get("finding_trailhead")))
            lake_rows.append(OrderedDict([
                ("letter_number", lk["letter_number"]),
                ("name", lk["name"] or None),
                ("is_primary", bool(l["is_primary"])),
                ("match_method", l["match_method"]),
                ("mention_context", ctx),
                ("drainage", lk["drainage"]),
                ("basin", lk["basin"] or None),
                ("elevation_ft", lk["elevation_ft"]),
                ("size_acres", lk["size_acres"]),
                ("max_depth_ft", lk["max_depth_ft"]),
                ("species_current", [s for s, hist in sp if not hist]),
                ("species_historical", [s for s, hist in sp if hist]),
                ("fishing_pressure", lk["fishing_pressure"]),
                ("no_fish", bool(lk["no_fish"])),
                ("jed_status", lk["status"] or None),
                ("starred", bool(lk["starred"])),
                ("has_coords", lk["coord_status"] in ("confirmed", "manual")),
                ("has_cma_notes", bool(lk["has_cma"])),
                ("has_junesucker_notes", bool(lk["has_js"])),
                ("has_jed_notes", bool(lk["has_jed_notes"])),
            ]))
            lake_hikes[lk["letter_number"]].append((h["hike_number"], bool(l["is_primary"])))

        route_rows = [lr for lr in lake_rows if lr["mention_context"] != "reference"]
        species_cur, species_hist = set(), set()
        for lr in route_rows:
            species_cur.update(lr["species_current"])
            species_hist.update(lr["species_historical"])
        fishable = [lr for lr in route_rows if not lr["no_fish"]]
        elevs = [lr["elevation_ft"] for lr in route_rows if lr["elevation_ft"]]
        acres = [lr["size_acres"] for lr in route_rows if lr["size_acres"]]

        hike = OrderedDict()
        hike["hike_number"] = h["hike_number"]
        hike["name"] = h["name"]
        hike["part"] = region.get("part_number")
        hike["region"] = region.get("name")
        hike["trailhead_section"] = th.get("name")
        hike["trailhead_section_inferred"] = th_inferred
        hike["start_trailhead"] = h["start_trailhead"]
        hike["nearest_town"] = h["nearest_town"]
        hike["book_drainage"] = h["drainage"]
        hike.update(parse_distance(h["distance"]))
        hike["destination_elevation_ft"] = parse_elevation(h["destination_elevation"])
        hike["elevation_field"] = "destination"
        if hike["destination_elevation_ft"] is None and h["source_file"] in _HIGHEST_ELEV:
            hike["destination_elevation_ft"] = parse_elevation(_HIGHEST_ELEV[h["source_file"]])
            hike["elevation_field"] = "highest"
        hike.update(parse_time(h["hiking_time"]))
        hike.update(parse_difficulty(h["difficulty"]))
        hike.update(parse_usage(h["usage"]))
        hike["lake_count"] = len(route_rows)
        hike["lake_count_all_mentions"] = len(lake_rows)
        hike["primary_lakes"] = [lr["letter_number"] for lr in lake_rows if lr["is_primary"]]
        hike["fishable_lake_count"] = len(fishable)
        hike["lakes_caught"] = sum(1 for lr in route_rows if lr["jed_status"] == "CAUGHT")
        hike["lakes_uncaught_fishable"] = sum(
            1 for lr in fishable if lr["jed_status"] != "CAUGHT")
        hike["lakes_starred"] = sum(1 for lr in route_rows if lr["starred"])
        hike["species_current"] = sorted(species_cur)
        hike["species_historical_only"] = sorted(species_hist - species_cur)
        hike["lake_drainages"] = sorted({lr["drainage"] for lr in route_rows if lr["drainage"]})
        hike["lake_elevation_min_ft"] = min(elevs) if elevs else None
        hike["lake_elevation_max_ft"] = max(elevs) if elevs else None
        hike["lake_acres_total"] = round(sum(acres), 1) if acres else None
        hike["largest_lake_acres"] = max(acres) if acres else None
        hike["tags"] = tag_text(h.get("narrative"), access_text)
        hike["summary"] = blurbs.get(h["source_file"]) or _first_sentences(h.get("narrative"))
        hike["summary_source"] = "book-intro" if h["source_file"] in blurbs else "narrative"
        hike["source_pages"] = h["source_pages"]
        hike["book_url"] = f"{BOOK_URL}#hike-{h['hike_number']:02d}"
        hike["narrative"] = h.get("narrative")
        hike["finding_trailhead"] = h.get("finding_trailhead")
        hike["lakes"] = lake_rows
        hikes.append(hike)
        if th:
            th_hikes[th["id"]].append(h["hike_number"])

    trailheads = []
    for tid, th in sorted(ths.items(), key=lambda kv: (regions.get(kv[1]["region_id"], {}).get("part_number") or 0, kv[0])):
        region = regions.get(th["region_id"]) or {}
        t = OrderedDict()
        t["name"] = th["name"]
        t["part"] = region.get("part_number")
        t["region"] = region.get("name")
        t["hikes"] = th_hikes.get(tid, [])
        t.update(parse_access(th.get("description")))
        t["access_tags"] = [tg for tg in tag_text(None, th.get("description"))]
        t["maps"] = th.get("maps")
        t["description"] = th.get("description")
        trailheads.append(t)

    lake_index = []
    for ln, entries in sorted(lake_hikes.items(), key=lambda kv: _ln_sort(kv[0])):
        lk = next(l for l in lakes.values() if l["letter_number"] == ln)
        lake_index.append(OrderedDict([
            ("letter_number", ln),
            ("name", lk["name"] or None),
            ("drainage", lk["drainage"]),
            ("jed_status", lk["status"] or None),
            ("hikes", sorted({n for n, _ in entries})),
            ("primary_destination_of", sorted({n for n, p in entries if p})),
        ]))

    return {
        "source": "Hiking Utah's High Uintas, 3rd ed. (Andrew Dash Gillman, Falcon, 2024)",
        "generated_by": "scripts/build_hike_index.py",
        "field_notes": {
            "distance_mi_min/max": "parsed from the book's Distance field; identical when a single figure. 'one way' routes state one-way miles.",
            "elevation_field": "'destination' = the book's Destination elevation; 'highest' = the book gave 'Highest elevation' instead (hikes 70, 75).",
            "route_types": "subset of ['out and back','loop','one way','shuttle'] as the book words it.",
            "time_hr_min/max": "book's Approximate hiking time in hours; time_variable=true when the book says 'Variable'.",
            "difficulty": "max of the book's rating words (Easy=1, Moderate=2, Difficult=3, Extremely difficult=4); difficulty_min/max cover 'Easy to moderate' style ranges; difficulty_note is the text after the em-dash.",
            "usage_rank": "Very light=1, Light=2, Moderate=3, Heavy/High=4.",
            "trailhead_section": "the book's trailhead chapter the hike sits under; trailhead_section_inferred=true when taken from the book's table of contents because the hike's own 'Start:' text didn't name that section (e.g. 'Lake Fork trailhead before Moon Lake Campground').",
            "lakes": "every DB lake the hike's text names (import_falcon_guide.py matcher); is_primary marks the hike's titled destination(s). mention_context='reference' flags name-drops (\"Mirror Lake Scenic Byway\", \"the others start at Hoop Lake\") that the hike does not actually visit — heuristic, see mention_context() in the script.",
            "lake_count": "lakes with mention_context != 'reference' (the 'visits N lakes' number); lake_count_all_mentions counts every link. All the lakes_*/species_*/lake_* aggregates use the same route-only set.",
            "jed_status": "Jed's own status on the lake ('CAUGHT', 'OTHERS', or null) at build time.",
            "species_current": "union across the hike's lakes of un-asterisked species (recently stocked or wild).",
            "tags": "regex flags on the narrative ('hike' rules) or on finding-the-trailhead + trailhead prose ('access' rules); see TAG_RULES in the script.",
        },
        "counts": {"hikes": len(hikes), "trailheads": len(trailheads),
                   "lakes_linked": len(lake_index)},
        "hikes": hikes,
        "trailheads": trailheads,
        "lakes": lake_index,
    }


def _ln_sort(ln):
    m = re.match(r"([A-Z]+)-(\d+)", ln or "")
    return (m.group(1), int(m.group(2))) if m else (ln, 0)


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _rng(lo, hi, fmt="{:g}"):
    if lo is None:
        return "—"
    return fmt.format(lo) if lo == hi else f"{fmt.format(lo)}–{fmt.format(hi)}"


def _lake_label(lr):
    n = lr["letter_number"] + (f" {lr['name']}" if lr["name"] else "")
    return n


def to_markdown(idx):
    L = []
    L.append("# Falcon guide hike index")
    L.append("")
    L.append(f"Source: *{idx['source']}*. Generated by `{idx['generated_by']}` from the "
             "`guide_*` tables; **do not edit by hand**. Machine-readable twin: "
             "`data/hike_index.json` (same data plus full narratives).")
    L.append("")
    L.append("How to query the JSON (examples):")
    L.append("")
    L.append("```bash")
    L.append("# hikes 8–14 mi round trip that reach ≥3 lakes")
    L.append("jq '.hikes[] | select(.distance_mi_max>=8 and .distance_mi_max<=14 and .lake_count>=3) "
             "| {hike_number,name,distance_text,lake_count,primary_lakes}' data/hike_index.json")
    L.append("# hikes with grayling water, sorted by distance")
    L.append("jq '[.hikes[] | select(.species_current|index(\"Grayling\"))] | sort_by(.distance_mi_max) "
             "| .[] | {hike_number,name,distance_text}' data/hike_index.json")
    L.append("# which hikes reach X-64")
    L.append("jq '.lakes[] | select(.letter_number==\"X-64\")' data/hike_index.json")
    L.append("```")
    L.append("")
    L.append("Columns: **Dist** = round-trip miles as the book states them (a range means the book "
             "gives options; *one way* noted); **Elev** = destination elevation (ft); **Time** = hours; "
             "**Diff** = Easy / Moderate / Difficult / Extreme (note after the dash in the per-hike block); "
             "**Use** = book's usage; **Lakes** = DB lakes the hike's text names, minus pure name-drops like "
             "\"Mirror Lake Scenic Byway\" (fishable ones with no CAUGHT status counted under *Uncaught*); **Primary** = titled destination lake(s).")
    L.append("")
    L.append("## All hikes")
    L.append("")
    L.append("| # | Hike | Part | Trailhead | Dist (mi) | Route | Elev | Time (h) | Diff | Use | Lakes | Uncaught | Primary |")
    L.append("|--:|---|:-:|---|--:|---|--:|--:|---|---|--:|--:|---|")
    for h in idx["hikes"]:
        route = "/".join(r.replace("out and back", "O&B").replace("one way", "1-way")
                         for r in h["route_types"]) or "—"
        diff = (h["difficulty"] or "—").replace("Extremely difficult", "Extreme")
        if h["difficulty_min"] and h["difficulty_min"] != h["difficulty_max"]:
            diff = f"{_LEVEL_NAME[h['difficulty_min']]}–{diff}"
        time = "Var." if h["time_variable"] else _rng(h["time_hr_min"], h["time_hr_max"])
        prim = ", ".join(h["primary_lakes"]) or "—"
        L.append(f"| {h['hike_number']} | {h['name']} | {h['part']} | {h['trailhead_section'] or h['start_trailhead']} | "
                 f"{_rng(h['distance_mi_min'], h['distance_mi_max'])} | {route} | "
                 f"{h['destination_elevation_ft'] or '—'} | {time} | {diff} | {h['usage_text'] or '—'} | "
                 f"{h['lake_count']} | {h['lakes_uncaught_fishable']} | {prim} |")
    L.append("")

    L.append("## Per-hike detail")
    L.append("")
    cur_part = None
    for h in idx["hikes"]:
        if h["part"] != cur_part:
            cur_part = h["part"]
            L.append(f"### Part {cur_part}: {h['region']}")
            L.append("")
        L.append(f"#### {h['hike_number']}. {h['name']}")
        L.append("")
        L.append(f"- **Start:** {h['start_trailhead']}"
                 + (f" (section: {h['trailhead_section']})" if h["trailhead_section"] else "")
                 + f" · **Town:** {h['nearest_town']} · **Drainage:** {h['book_drainage']}")
        L.append(f"- **Distance:** {h['distance_text']} · **Elev:** {h['destination_elevation_ft']} ft · "
                 f"**Time:** {h['time_text']} · **Difficulty:** {h['difficulty_text']} · **Usage:** {h['usage_text']}")
        if h["lakes"]:
            parts = []
            for lr in h["lakes"]:
                bits = []
                if lr["mention_context"] == "reference":
                    bits.append("name-drop only")
                if lr["is_primary"]:
                    bits.append("primary")
                if lr["jed_status"]:
                    bits.append(lr["jed_status"])
                if lr["starred"]:
                    bits.append("★")
                if lr["no_fish"]:
                    bits.append("no fish")
                elif lr["species_current"]:
                    bits.append("/".join(lr["species_current"]))
                if lr["elevation_ft"]:
                    bits.append(f"{lr['elevation_ft']}ft")
                if lr["size_acres"]:
                    bits.append(f"{lr['size_acres']:g}ac")
                parts.append(f"{_lake_label(lr)} ({', '.join(bits)})" if bits else _lake_label(lr))
            L.append(f"- **Lakes ({h['lake_count']} on route"
                     + (f", {h['lake_count_all_mentions'] - h['lake_count']} name-drop only"
                        if h['lake_count_all_mentions'] != h['lake_count'] else "")
                     + "):** " + "; ".join(parts))
            agg = (f"- **Aggregates:** {h['lakes_uncaught_fishable']} fishable & uncaught, "
                   f"{h['lakes_caught']} caught, {h['lakes_starred']} starred; species: "
                   f"{', '.join(h['species_current']) or '—'}")
            if h["species_historical_only"]:
                agg += f" (historical only: {', '.join(h['species_historical_only'])})"
            if h["lake_elevation_min_ft"]:
                agg += f"; lake elev {h['lake_elevation_min_ft']}–{h['lake_elevation_max_ft']} ft"
            if h["lake_acres_total"]:
                agg += f"; {h['lake_acres_total']:g} ac total, largest {h['largest_lake_acres']:g} ac"
            L.append(agg)
        else:
            L.append("- **Lakes:** none linked")
        if h["tags"]:
            L.append(f"- **Tags:** {', '.join(h['tags'])}")
        if h["summary"]:
            L.append(f"- **Summary:** {h['summary']}")
        L.append(f"- **Book:** pp. {h['source_pages'] or '?'} · {h['book_url']}")
        L.append("")

    L.append("## Trailhead sections")
    L.append("")
    L.append("| Trailhead | Part | Hikes | Parking | Directions from | Access tags |")
    L.append("|---|:-:|---|--:|---|---|")
    for t in idx["trailheads"]:
        drive = t["drive_from"] or "—"
        L.append(f"| {t['name']} | {t['part']} | {', '.join(map(str, t['hikes'])) or '—'} | "
                 f"{t['parking_capacity'] or '—'} | {drive} | {', '.join(t['access_tags']) or '—'} |")
    L.append("")

    L.append("## Lake → hikes")
    L.append("")
    L.append("| Lake | Drainage | Jed | Hikes (primary in **bold**) |")
    L.append("|---|---|---|---|")
    for lk in idx["lakes"]:
        prim = set(lk["primary_destination_of"])
        hs = ", ".join(f"**{n}**" if n in prim else str(n) for n in lk["hikes"])
        L.append(f"| {lk['letter_number']}{' ' + lk['name'] if lk['name'] else ''} | "
                 f"{(lk['drainage'] or '').replace(' Drainage', '').replace(' Drainages', '')} | "
                 f"{lk['jed_status'] or ''} | {hs} |")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--stdout", action="store_true", help="print markdown, write nothing")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    idx = build(conn)
    md = to_markdown(idx)
    if args.stdout:
        print(md)
        return
    with open(JSON_OUT, "w") as f:
        json.dump(idx, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(MD_OUT, "w") as f:
        f.write(md)

    hs = idx["hikes"]
    unparsed = [(h["hike_number"], k) for h in hs for k in
                ("distance_mi_max", "destination_elevation_ft", "difficulty", "usage_rank")
                if h[k] is None]
    no_time = [h["hike_number"] for h in hs if h["time_hr_max"] is None and not h["time_variable"]]
    print(f"Wrote {JSON_OUT} and {MD_OUT}: {len(hs)} hikes, "
          f"{len(idx['trailheads'])} trailheads, {len(idx['lakes'])} lakes linked; "
          f"summaries from {'EPUB' if any(h['summary_source']=='book-intro' for h in hs) else 'narrative'}.")
    if unparsed:
        print("Unparsed fields:", unparsed)
    if no_time:
        print("No time parsed for hikes:", no_time)


if __name__ == "__main__":
    main()
