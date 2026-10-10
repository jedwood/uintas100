#!/usr/bin/env python3
"""
data/journal.json — the user-authored trips, photo metadata and lake links the
PWA creates (docs/trips-photos-links-plan.md).

Lives OUTSIDE uinta_lakes.db for the same reason data/collections.json and
data/app_edits_log.jsonl do: the seeds / rebuild / verify machinery stays
untouched, and the file is trivially diffable. Only the edits server on the
Mini writes it (single-writer model); the exporter reads it.

    {"version": 1, "trips": [...], "photos": [...], "links": [...]}

Every doc carries a client-generated `id` (`t-`/`p-`/`l-` + base36 time + 4
random) and an ISO-8601 `updated` stamp. Sync is per-document
last-write-wins on `updated`; deletes are tombstones
(`{"id", "updated", "deleted": true}`) so they propagate like any other write.
The exporter drops tombstones.

Photo IMAGE files and their private GPS sidecars are NOT here — they live in
the gitignored data/media/ on the Mini (see validate_sidecar / MEDIA_ID_RE).
"""

import json
import math
import os
import re
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_JOURNAL = os.path.join(REPO_ROOT, "data", "journal.json")
DEFAULT_MEDIA = os.path.join(REPO_ROOT, "data", "media")

KINDS = {"trip": "trips", "photo": "photos", "link": "links"}
ID_RE = {
    "trip": re.compile(r"^t-[a-z0-9]+-[a-z0-9]{4}$"),
    "photo": re.compile(r"^p-[a-z0-9]+-[a-z0-9]{4}$"),
    "link": re.compile(r"^l-[a-z0-9]+-[a-z0-9]{4}$"),
}
MEDIA_ID_RE = ID_RE["photo"]
UPDATED_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d{1,6})?Z$")
DATE_RE = re.compile(r"^\d{4}-\d\d-\d\d$")
TAKEN_RE = re.compile(r"^\d{4}-\d\d-\d\d(T\d\d:\d\d(:\d\d(\.\d+)?)?)?$")

MAX_TITLE, MAX_BODY, MAX_CAPTION, MAX_NOTE, MAX_WHEN = 200, 50_000, 2_000, 2_000, 100
MAX_LAKES, MAX_LINKS, MAX_URL = 100, 50, 2_000
SIDECAR_FIELDS = ("lat", "lng", "alt", "gps_time", "taken", "make", "model")


class DocError(ValueError):
    pass


def empty():
    return {"version": 1, "trips": [], "photos": [], "links": []}


def load(path=DEFAULT_JOURNAL):
    if not os.path.exists(path):
        return empty()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = empty()
    for plural in KINDS.values():
        out[plural] = [d for d in data.get(plural, []) if isinstance(d, dict) and d.get("id")]
    return out


def save(data, path=DEFAULT_JOURNAL):
    """Sorted by id (≈ chronological), indent 1, atomic tmp + rename."""
    out = {"version": 1}
    for plural in KINDS.values():
        out[plural] = sorted(data.get(plural, []), key=lambda d: d["id"])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".journal-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --- validation ------------------------------------------------------------

def _str(v, name, cap):
    if v is None or v == "":
        return ""
    if not isinstance(v, str):
        raise DocError(f"{name} must be a string")
    v = v.strip()
    if len(v) > cap:
        raise DocError(f"{name} longer than {cap} chars")
    return v


def _opt(v, name, regex):
    if v in (None, ""):
        return None
    if not isinstance(v, str) or not regex.match(v):
        raise DocError(f"bad {name} {v!r}")
    return v


def check_url(url):
    if not isinstance(url, str):
        raise DocError("url must be a string")
    url = url.strip()
    if len(url) > MAX_URL:
        raise DocError(f"url longer than {MAX_URL} chars")
    if not re.match(r"^https?://[^\s/?#]+", url, re.I):
        raise DocError(f"url must be http(s): {url[:80]!r}")
    return url


def _lakes(v, known):
    if v is None:
        return []
    if not isinstance(v, list) or len(v) > MAX_LAKES:
        raise DocError(f"lakes must be a list of at most {MAX_LAKES}")
    out = []
    for ln in v:
        if not isinstance(ln, str) or ln not in known:
            raise DocError(f"no lake {ln!r}")
        if ln not in out:
            out.append(ln)
    return out


def _int(v, name):
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 20_000:
        raise DocError(f"bad {name} {v!r}")
    return v


def clean_doc(kind, doc, known_lakes):
    """Validate one incoming doc; return the whitelisted copy to store.

    Unknown fields are dropped — the server is the schema authority."""
    if kind not in KINDS:
        raise DocError(f"bad kind {kind!r}")
    if not isinstance(doc, dict):
        raise DocError("doc must be an object")
    doc_id = doc.get("id")
    if not isinstance(doc_id, str) or not ID_RE[kind].match(doc_id):
        raise DocError(f"bad {kind} id {doc_id!r}")
    updated = doc.get("updated")
    if not isinstance(updated, str) or not UPDATED_RE.match(updated):
        raise DocError(f"bad updated {updated!r}")
    base = {"id": doc_id, "updated": updated}
    if doc.get("deleted"):
        return {**base, "deleted": True}

    if kind == "trip":
        planned = bool(doc.get("planned"))
        links = doc.get("links") or []
        if not isinstance(links, list) or len(links) > MAX_LINKS:
            raise DocError(f"links must be a list of at most {MAX_LINKS}")
        clean_links = []
        for lk in links:
            if not isinstance(lk, dict):
                raise DocError("each link must be an object")
            clean_links.append({"url": check_url(lk.get("url")),
                                "title": _str(lk.get("title"), "link title", MAX_TITLE)})
        return {**base,
                "title": _str(doc.get("title"), "title", MAX_TITLE),
                "planned": planned,
                "date": None if planned else _opt(doc.get("date"), "date", DATE_RE),
                "end_date": None if planned else _opt(doc.get("end_date"), "end_date", DATE_RE),
                "when": (_str(doc.get("when"), "when", MAX_WHEN) or None) if planned else None,
                "body": _str(doc.get("body"), "body", MAX_BODY),
                "lakes": _lakes(doc.get("lakes"), known_lakes),
                "links": clean_links}

    if kind == "photo":
        return {**base,
                # May name a trip not synced yet — allowed (the trip doc can
                # arrive in a later batch).
                "trip": _opt(doc.get("trip"), "trip", ID_RE["trip"]),
                "lakes": _lakes(doc.get("lakes"), known_lakes),
                "caption": _str(doc.get("caption"), "caption", MAX_CAPTION),
                "taken": _opt(doc.get("taken"), "taken", TAKEN_RE),
                "w": _int(doc.get("w"), "w"),
                "h": _int(doc.get("h"), "h")}

    # link
    lake = doc.get("lake")
    if not isinstance(lake, str) or lake not in known_lakes:
        raise DocError(f"no lake {lake!r}")
    return {**base,
            "lake": lake,
            "url": check_url(doc.get("url")),
            "title": _str(doc.get("title"), "title", MAX_TITLE),
            "note": _str(doc.get("note"), "note", MAX_NOTE)}


def validate_sidecar(obj):
    """The private per-photo location record (data/media/<id>.json). Only
    these keys, lat/lng finite and in range; returns the normalized dict."""
    if not isinstance(obj, dict):
        raise DocError("sidecar must be an object")
    extra = set(obj) - set(SIDECAR_FIELDS)
    if extra:
        raise DocError(f"unexpected sidecar keys {sorted(extra)}")

    def num(v, name, lo, hi, required):
        if v is None and not required:
            return None
        if isinstance(v, bool) or not isinstance(v, (int, float)) \
                or not math.isfinite(v) or not lo <= v <= hi:
            raise DocError(f"bad {name} {v!r}")
        return v

    def short(v, name):
        if v is None:
            return None
        if not isinstance(v, str) or len(v) > 64:
            raise DocError(f"bad {name}")
        return v

    return {"lat": num(obj.get("lat"), "lat", -90, 90, True),
            "lng": num(obj.get("lng"), "lng", -180, 180, True),
            "alt": num(obj.get("alt"), "alt", -500, 9000, False),
            "gps_time": short(obj.get("gps_time"), "gps_time"),
            "taken": short(obj.get("taken"), "taken"),
            "make": short(obj.get("make"), "make"),
            "model": short(obj.get("model"), "model")}


# --- apply / read ----------------------------------------------------------

def apply_doc(data, kind, clean):
    """Last-write-wins: store `clean` iff its `updated` >= the stored copy's.
    Returns (True, None) when applied, (False, current) when superseded."""
    docs = data[KINDS[kind]]
    for i, cur in enumerate(docs):
        if cur["id"] == clean["id"]:
            if clean["updated"] < cur.get("updated", ""):
                return False, cur
            docs[i] = clean
            return True, None
    docs.append(clean)
    return True, None


def public_view(data, known_lakes, warn=None):
    """What the PWA's published lakes_data.json carries: tombstones dropped,
    unknown lake designations dropped with a warning (never raised — this runs
    inside unattended commits)."""
    warn = warn or (lambda m: print("WARNING: " + m, file=sys.stderr))
    out = {}
    for kind, plural in KINDS.items():
        rows = []
        for d in data.get(plural, []):
            if d.get("deleted"):
                continue
            d = dict(d)
            if kind == "link":
                if d.get("lake") not in known_lakes:
                    warn(f"journal.json: link {d['id']} names unknown lake {d.get('lake')!r}; dropped")
                    continue
            else:
                bad = [ln for ln in d.get("lakes", []) if ln not in known_lakes]
                if bad:
                    warn(f"journal.json: {kind} {d['id']} names unknown lake(s) {bad}; dropped them")
                    d["lakes"] = [ln for ln in d.get("lakes", []) if ln in known_lakes]
            rows.append(d)
        out[plural] = sorted(rows, key=lambda d: d["id"])
    return out
