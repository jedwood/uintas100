#!/usr/bin/env python3
"""Ad-hoc lake finder: one flat table, one SQL query.

    python3 scripts/lakes.py "SELECT designation, name FROM lake_search WHERE ..."
    python3 scripts/lakes.py --columns          # what you can filter on
    python3 scripts/lakes.py --rebuild          # force a refresh

Builds a denormalized cache at data/cache/lake_search.db (gitignored,
~1s) so a "find me lakes that ..." question is a single SELECT instead of
a six-table join. The cache auto-rebuilds whenever uinta_lakes.db, the
hike index, collections.json, the trail-distance cache, or this script is
newer than it.

Two tables in the cache:
  lake_search   one row per lake (746) - every filterable attribute
  lake_species  one row per (lake, species) - per-species stocking timing

The canonical DB is ATTACHed as `raw`, so a query can still reach the
untouched tables for anything the flat table doesn't carry:
  raw.lakes, raw.stocking_records, raw.guide_hikes, raw.guide_hike_lakes,
  raw.dwr_lake_summary, raw.dwr_gillnet_samples, raw.trailheads, ...

Read-only. It never writes to uinta_lakes.db (single-writer model).
"""
import argparse
import csv
import datetime
import json
import os
import re
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(REPO, "uinta_lakes.db")
CACHE_DIR = os.path.join(REPO, "data", "cache")
CACHE = os.path.join(CACHE_DIR, "lake_search.db")
HIKE_INDEX = os.path.join(REPO, "data", "hike_index.json")
COLLECTIONS = os.path.join(REPO, "data", "collections.json")
TRAIL_DIST = os.path.join(CACHE_DIR, "lake_trail_distance.json")
APP = "https://jedwood.github.io/uintas100/#"

SOURCES = [DB, HIKE_INDEX, COLLECTIONS, TRAIL_DIST, os.path.abspath(__file__)]
M_PER_MI = 1609.344


def stale():
    if not os.path.exists(CACHE):
        return True
    built = os.path.getmtime(CACHE)
    return any(os.path.exists(p) and os.path.getmtime(p) > built for p in SOURCES)


def split_species(raw):
    """'Brookies, Cutthroats*' -> (['Brookies'], ['Cutthroats']).

    A trailing asterisk means historical: present in the record but not
    recently stocked. See scripts/species_utils.py.
    """
    current, historical = [], []
    for part in (raw or "").split(","):
        s = part.strip()
        if not s:
            continue
        (historical if s.endswith("*") else current).append(s.rstrip("*").strip())
    return current, historical


def csvj(values):
    return ", ".join(str(v) for v in values) if values else None


def build(verbose=True):
    os.makedirs(CACHE_DIR, exist_ok=True)
    src = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    this_year = datetime.date.today().year

    lakes = {r["letter_number"]: dict(r) for r in src.execute("SELECT * FROM lakes")}

    # ---- stocking, per lake and per (lake, species) --------------------
    stock, stock_sp = {}, {}
    for r in src.execute(
        """SELECT l.letter_number ln, s.species, s.stock_date, s.quantity
             FROM stocking_records s JOIN lakes l ON l.id = s.lake_id
            WHERE s.stock_date IS NOT NULL"""
    ):
        yr = int(r["stock_date"][:4])
        d = stock.setdefault(r["ln"], {"years": set(), "events": 0, "qty": 0,
                                       "last": "", "last_sp": set()})
        d["years"].add(yr)
        d["events"] += 1
        d["qty"] += r["quantity"] or 0
        if r["stock_date"] > d["last"]:
            d["last"], d["last_sp"] = r["stock_date"], {r["species"]}
        elif r["stock_date"] == d["last"]:
            d["last_sp"].add(r["species"])
        k = (r["ln"], r["species"])
        sp = stock_sp.setdefault(k, {"years": set(), "events": 0, "qty": 0})
        sp["years"].add(yr)
        sp["events"] += 1
        sp["qty"] += r["quantity"] or 0

    # ---- DWR 2025 survey tables ---------------------------------------
    summary = {}
    for r in src.execute(
        "SELECT l.letter_number ln, s.* FROM dwr_lake_summary s "
        "JOIN lakes l ON l.id = s.lake_id"
    ):
        summary[r["ln"]] = dict(r)
    gill = {}
    for r in src.execute(
        "SELECT l.letter_number ln, g.* FROM dwr_gillnet_samples g "
        "JOIN lakes l ON l.id = g.lake_id"
    ):
        g = gill.setdefault(r["ln"], {"species": [], "max_len": None,
                                      "mean_len": None, "max_wt": None, "n": 0})
        g["species"].append(r["species"])
        g["n"] += r["n_sampled"] or 0
        for key, col in (("max_len", "max_length_in"), ("mean_len", "mean_length_in"),
                         ("max_wt", "max_weight_lb")):
            v = r[col]
            if v is not None and (g[key] is None or v > g[key]):
                g[key] = v

    # ---- chemical reclamation projects ---------------------------------
    treat = {}
    for r in src.execute(
        "SELECT l.letter_number ln, t.* FROM lake_treatments t "
        "JOIN lakes l ON l.id = t.lake_id"
    ):
        e = treat.setdefault(r["ln"], {"years": [], "projects": [], "restored": []})
        if r["start_date"]:
            e["years"].append(int(r["start_date"][:4]))
        e["projects"].append(r["project_name"])
        if r["restored_species"]:
            e["restored"].append(r["restored_species"])

    # ---- photos --------------------------------------------------------
    photos = {r["ln"]: r["n"] for r in src.execute(
        "SELECT l.letter_number ln, COUNT(*) n FROM photos p "
        "JOIN lakes l ON l.id = p.lake_id GROUP BY 1")}

    # ---- Falcon guide hikes (route mentions only, not name-drops) ------
    hikes = {}
    if os.path.exists(HIKE_INDEX):
        idx = json.load(open(HIKE_INDEX))
        for h in idx["hikes"]:
            for lr in h.get("lakes", []):
                if lr.get("mention_context") == "reference":
                    continue
                e = hikes.setdefault(lr["letter_number"], {
                    "nums": [], "names": [], "ths": set(), "primary": [],
                    "mi": [], "diff": [], "use": [], "hrs": []})
                e["nums"].append(h["hike_number"])
                e["names"].append(h["name"])
                if h.get("start_trailhead"):
                    e["ths"].add(h["start_trailhead"])
                if lr.get("is_primary"):
                    e["primary"].append(h["hike_number"])
                for key, col in (("mi", "distance_mi_max"), ("diff", "difficulty_max"),
                                 ("use", "usage_rank"), ("hrs", "time_hr_max")):
                    if h.get(col) is not None:
                        e[key].append(h[col])

    # ---- distance to the nearest mapped route (OSM) --------------------
    trail = {}
    if os.path.exists(TRAIL_DIST):
        for r in json.load(open(TRAIL_DIST)):
            trail[r["letter_number"]] = r

    # ---- curated collections ------------------------------------------
    colls = {}
    if os.path.exists(COLLECTIONS):
        for c in json.load(open(COLLECTIONS))["collections"]:
            for entry in c["lakes"]:
                e = colls.setdefault(entry["letter_number"],
                                     {"keys": [], "labels": [], "notes": []})
                e["keys"].append(c["key"])
                e["labels"].append(c["label"])
                if entry.get("note"):
                    e["notes"].append(f"[{c['label']}] {entry['note']}")

    # ---- assemble -------------------------------------------------------
    rows, sp_rows = [], []
    for ln, L in lakes.items():
        cur, hist = split_species(L["fish_species"])
        st = stock.get(ln)
        years = sorted(st["years"]) if st else []
        interval = round((years[-1] - years[0]) / (len(years) - 1), 1) if len(years) > 1 else None
        h = hikes.get(ln)
        t = trail.get(ln)
        s = summary.get(ln)
        g = gill.get(ln)
        c = colls.get(ln)

        rows.append({
            "designation": ln,
            "name": L["name"] or None,
            "drainage": L["drainage"],
            "basin": L["basin"] or None,
            "elevation_ft": L["elevation_ft"],
            "size_acres": L["size_acres"],
            "max_depth_ft": L["max_depth_ft"],
            "fishing_pressure": L["fishing_pressure"],
            "status": L["status"],
            "starred": 1 if L["starred"] else 0,
            "no_fish": 1 if L["no_fish"] else 0,
            "fishable": 0 if L["no_fish"] else 1,
            "lat": L["lat"],
            "lng": L["lng"],
            "app_url": APP + ln,

            "species": L["fish_species"],
            "species_current": csvj(cur),
            "species_historical": csvj(hist),
            "n_species_current": len(cur),

            "ever_stocked": 1 if st else 0,
            "last_stocked": st["last"] if st else None,
            "last_stocked_year": years[-1] if years else None,
            "years_since_stocked": (this_year - years[-1]) if years else None,
            "last_stocked_species": csvj(sorted(st["last_sp"])) if st else None,
            "first_stocked_year": years[0] if years else None,
            "stock_years": len(years),
            "stock_events": st["events"] if st else 0,
            "stock_total_fish": st["qty"] if st else 0,
            "stock_interval_yr": interval,
            "stocked_years": csvj(years),

            "trail_m": t and t.get("d_trail_m"),
            "trail_mi": round(t["d_trail_m"] / M_PER_MI, 2) if t and t.get("d_trail_m") is not None else None,
            "nearest_trail": t and csvj(t.get("near_trail") or []),
            "route_m": t and t.get("d_any_m"),
            "route_mi": round(t["d_any_m"] / M_PER_MI, 2) if t and t.get("d_any_m") is not None else None,
            "nearest_route": t and csvj(t.get("near_any") or []),
            "road_m": t and t.get("d_drive_m"),
            "rough_road_m": t and t.get("d_rough_m"),
            "nearest_road": t and csvj(t.get("near_drive") or []),

            "dwr_trail_miles": s and s.get("trail_miles"),
            "dwr_access": s and s.get("access"),
            "dwr_campsites": s and s.get("campsites"),
            "dwr_spring_water": s and s.get("spring_water"),
            "dwr_horse_feed": s and s.get("horse_feed"),
            "dwr_stocking_cycle": s and s.get("stocking_cycle"),

            "hike_count": len(h["nums"]) if h else 0,
            "hike_numbers": csvj(sorted(h["nums"])) if h else None,
            "hike_names": csvj(h["names"]) if h else None,
            "primary_of_hikes": csvj(sorted(h["primary"])) if h and h["primary"] else None,
            "min_hike_mi": min(h["mi"]) if h and h["mi"] else None,
            "max_hike_mi": max(h["mi"]) if h and h["mi"] else None,
            "min_hike_hours": min(h["hrs"]) if h and h["hrs"] else None,
            "min_hike_difficulty": min(h["diff"]) if h and h["diff"] else None,
            "min_hike_usage": min(h["use"]) if h and h["use"] else None,
            "trailheads": csvj(sorted(h["ths"])) if h else None,

            "gillnet_species": csvj(g["species"]) if g else None,
            "gillnet_n_sampled": g["n"] if g else None,
            "gillnet_mean_length_in": g["mean_len"] if g else None,
            "gillnet_max_length_in": g["max_len"] if g else None,
            "gillnet_max_weight_lb": g["max_wt"] if g else None,

            "collections": csvj(c["keys"]) if c else None,
            "collection_labels": csvj(c["labels"]) if c else None,
            "collection_notes": " | ".join(c["notes"]) if c and c["notes"] else None,

            "has_dwr_notes": 1 if (L["dwr_notes"] or "").strip() else 0,
            "dwr_edition": L["dwr_edition"],
            "has_junesucker_notes": 1 if (L["junesucker_notes"] or "").strip() else 0,
            "has_cma_notes": 1 if (L["cma_notes"] or "").strip() else 0,
            "has_jed_notes": 1 if (L["jed_notes"] or "").strip() else 0,
            "has_trip_reports": 1 if (L["trip_reports"] or "").strip() else 0,
            "n_photos": photos.get(ln, 0),

            "treated": 1 if ln in treat else 0,
            "treatment_year": max(treat[ln]["years"]) if treat.get(ln, {}).get("years") else None,
            "treatment_project": csvj(list(dict.fromkeys(treat[ln]["projects"]))) if ln in treat else None,
            "treatment_restored": csvj(list(dict.fromkeys(treat[ln]["restored"]))) if ln in treat else None,
            "n_treatments": len(treat[ln]["projects"]) if ln in treat else 0,
        })

        listed = {s_: False for s_ in cur} | {s_: True for s_ in hist}
        for species in sorted(set(listed) | {k[1] for k in stock_sp if k[0] == ln}):
            d = stock_sp.get((ln, species))
            yrs = sorted(d["years"]) if d else []
            sp_rows.append({
                "designation": ln,
                "name": L["name"] or None,
                "drainage": L["drainage"],
                "species": species,
                "listed": 1 if species in listed else 0,
                "listed_historical": 1 if listed.get(species) else 0,
                "stock_events": d["events"] if d else 0,
                "stock_first_year": yrs[0] if yrs else None,
                "stock_last_year": yrs[-1] if yrs else None,
                "years_since_stocked": (this_year - yrs[-1]) if yrs else None,
                "stock_total_fish": d["qty"] if d else 0,
                "stocked_years": csvj(yrs),
            })
    src.close()

    tmp = CACHE + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    out = sqlite3.connect(tmp)
    for table, data, key in (("lake_search", rows, "designation"),
                             ("lake_species", sp_rows, None)):
        cols = list(data[0])
        decl = ", ".join(f'"{c}"' + (" PRIMARY KEY" if c == key else "") for c in cols)
        out.execute(f"CREATE TABLE {table} ({decl})")
        out.executemany(
            f"INSERT INTO {table} VALUES ({','.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in data])
    out.execute("CREATE INDEX i_sp ON lake_species(species)")
    out.execute("CREATE INDEX i_sp_lake ON lake_species(designation)")
    out.execute("CREATE TABLE _meta (built_at TEXT, lakes INT, trail_data INT)")
    out.execute("INSERT INTO _meta VALUES (?,?,?)",
                (datetime.datetime.now().isoformat(timespec="seconds"),
                 len(rows), 1 if trail else 0))
    out.commit()
    out.close()
    os.replace(tmp, CACHE)
    if verbose:
        note = "" if trail else "  (no trail-distance cache: trail_*/route_*/road_* are NULL; " \
                               "run scripts/fetch_osm_routes.py then scripts/lake_trail_distance.py)"
        print(f"built {CACHE}: {len(rows)} lakes, {len(sp_rows)} lake-species rows{note}",
              file=sys.stderr)


def connect():
    if stale():
        build()
    conn = sqlite3.connect(f"file:{CACHE}?mode=ro", uri=True)
    conn.execute(f"ATTACH DATABASE 'file:{DB}?mode=ro' AS raw")
    conn.row_factory = sqlite3.Row
    return conn


def render(rows, headers, fmt):
    if fmt == "json":
        json.dump([dict(r) for r in rows], sys.stdout, indent=1, default=str)
        print()
        return
    if fmt == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(headers)
        w.writerows(rows)
        return
    cells = [[("" if v is None else str(v)) for v in r] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) if cells else len(h)
              for i, h in enumerate(headers)]
    widths = [min(w, 60) for w in widths]

    def line(vals):
        out = []
        for i, v in enumerate(vals):
            v = v if len(v) <= widths[i] else v[:widths[i] - 1] + "…"
            out.append(v.ljust(widths[i]))
        return ("| " + " | ".join(out) + " |") if fmt == "md" else "  ".join(out).rstrip()

    print(line(headers))
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|" if fmt == "md"
          else "  ".join("-" * w for w in widths))
    for c in cells:
        print(line(c))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sql", nargs="?", help="a SELECT against lake_search / lake_species / raw.*")
    p.add_argument("--format", "-f", choices=("table", "md", "json", "csv"), default="table")
    p.add_argument("--columns", action="store_true", help="list the columns and exit")
    p.add_argument("--rebuild", action="store_true", help="force a cache rebuild")
    a = p.parse_args()

    if a.rebuild:
        build()
        if not a.sql and not a.columns:
            return

    if a.columns:
        conn = connect()
        for t in ("lake_search", "lake_species"):
            print(f"\n{t}:")
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
            for i in range(0, len(cols), 4):
                print("  " + "".join(c.ljust(26) for c in cols[i:i + 4]).rstrip())
        print("\nraw.* (canonical DB, read-only): " + ", ".join(
            r[0] for r in conn.execute(
                "SELECT name FROM raw.sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY 1")))
        return

    if not a.sql:
        p.error("give a SQL query, --columns, or --rebuild")
    if not re.match(r"\s*(select|with)\b", a.sql, re.I):
        p.error("read-only tool: the query must start with SELECT or WITH")

    conn = connect()
    cur = conn.execute(a.sql)
    rows = cur.fetchall()
    headers = [d[0] for d in cur.description]
    render(rows, headers, a.format)
    sys.stdout.flush()
    if a.format in ("table", "md"):
        print(f"\n{len(rows)} row{'' if len(rows) == 1 else 's'}", file=sys.stderr)


if __name__ == "__main__":
    main()
