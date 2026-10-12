#!/usr/bin/env python3
"""
One-time migration (docs/trips-photos-links-plan.md, Phase 6): the old
per-lake `trip_reports` text → Trips, and the URLs pasted into `jed_notes`
→ lake Links, as docs in data/journal.json.

The grouping below was done by hand from the 16 lakes' trip_reports (one trip
per outing, linked to every lake it covered) and approved by Jed on
2026-10-10. Month-only dates ("2024-10") are where the old text gave no day.
Neither `trip_reports` nor `jed_notes` is touched here; clearing trip_reports
is a separate step once Jed has reviewed the trips in the app.

Writes go through the edits server's POST /api/journal — the Mini's single
writer, which validates, applies under its write lock and commits — rather
than editing journal.json directly. IDs and `updated` are fixed, and docs the
server already has are skipped, so a re-run is a no-op and can never
overwrite a migrated doc Jed has since edited in the app.

    python3 scripts/migrate_trip_reports.py                 # dry run (prints the docs)
    python3 scripts/migrate_trip_reports.py apply           # POST to olaf.local:8802
    python3 scripts/migrate_trip_reports.py apply --server http://127.0.0.1:8899   # test harness
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone

UPDATED = "2026-10-10T00:00:00.000Z"   # older than any edit made in the app
DEVICE = "migrate_trip_reports"


def _id(kind, date, key):
    """`t-`/`l-` + base36 of the trip's start (≈ chronological, like the
    client's Date.now() ids) + 4 chars from a hash, so ids are stable."""
    y, m, d = (date.split("-") + ["01"])[:3]
    ms = int(datetime(int(y), int(m), int(d), tzinfo=timezone.utc).timestamp() * 1000)
    n, digits = ms, ""
    while n:
        n, r = divmod(n, 36)
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + digits
    suffix = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    tail = ""
    for _ in range(4):
        suffix, r = divmod(suffix, 36)
        tail += "0123456789abcdefghijklmnopqrstuvwxyz"[r]
    return f"{kind}-{digits}-{tail}"


TRIPS = [
    {
        "title": "Detoured Highline: East Red Castle → Red Castle → Hessie",
        "date": "2020-09",
        "lakes": ["G-49", "G-15", "G-18"],
        "body": (
            "Our re-routed Highline attempt, with Dilworth, Hui and John.\n\n"
            "G-49: Caught three trout species here. Wonderful little break on our "
            "sidehilling off-trailing slog from East Red Castle on our way up to Red "
            "Castle. I followed the stream for most of it and caught at least one out "
            "of there.\n\n"
            "Red Castle (G-15): Magical couple of days here partway through our "
            "re-routed Highline attempt, with Dilworth and Hui.\n\n"
            "Hessie (G-18): Camped on the east side overnight w/ John and Hui, as part "
            "of detoured Highline. Caught one nice one and saw some very big ones over "
            "on the west side."
        ),
    },
    {
        "title": "Hessie w/ Ryan",
        "date": "2021-07",
        "lakes": ["G-18"],
        "body": (
            "Camped overnight on west side with Ryan, John joined the next day. Caught "
            "a couple of nice ones, again on west side."
        ),
    },
    {
        "title": "Red Castle w/ Dilworth + Ryan",
        "date": "2024-08",
        "lakes": ["G-15", "G-49"],
        "body": (
            "Red Castle (G-15): Dilworth and Ryan and I had repeated success with "
            "cutthroats in that little outlet pond, and I caught a few from my packraft "
            "out in the middle.\n\n"
            "G-49: Camped right nearby. Saw some rising but didn’t catch any that "
            "evening, but did see a bull, cow, and calf moose!"
        ),
    },
    {
        "title": "Ryder + McPheters w/ Dilworth",
        "date": "2024-08-31",
        "end_date": "2024-09-02",
        "lakes": ["BR-15", "BR-14"],
        "body": (
            "Labor Day weekend.\n\n"
            "Ryder (BR-15): Spent an hour here with Dilworth before heading up to "
            "McPheters. Tons of hungry small brookies right along the shore.\n\n"
            "McPheters (BR-14): Dilworth and I each caught big tigers out of here."
        ),
    },
    {
        "title": "Toomset + Amethyst w/ Ryan",
        "date": "2024-10",
        "lakes": ["BR-25", "BR-28"],
        "body": (
            "Ryan and I spent two nights at Toomset, day-tripping up to Amethyst.\n\n"
            "Toomset (BR-25): Caught several that were small to medium size.\n\n"
            "Amethyst (BR-28): Ryan and I each caught a couple on the far south side "
            "off the big rocks."
        ),
    },
    {
        "title": "Diamond w/ Kenny",
        "date": "2025-07",
        "lakes": ["A-22"],
        "body": (
            "Summer 2025 (month approximate). Kenny and I thought we were at Start "
            "Lake, since we had mistaken a nameless pond to the south for Diamond."
        ),
    },
    {
        "title": "Shingle Creek West w/ Ryan",
        "date": "2025-07-20",
        "lakes": ["P-60"],
        "body": (
            "With Ryan, accessed via Provo River trail. Heavy mosquitoes but good "
            "fishing. I had one break me off."
        ),
    },
    {
        "title": "Hell Hole day hike w/ Chelsey",
        "date": "2025-09-26",
        "lakes": ["BR-29"],
        "body": (
            "Chelsey and I did a day hike in. Plenty of eager small cutthroats. Caught "
            "two on gulp minnows showing Chels how to use the spinning rod, then got "
            "everything ready to go out on my packraft with new fly rod, and then it "
            "started to hail and rain. After a while, I just packed everything up and "
            "got ready to leave, and of course, then it stopped raining. :-) I tried to "
            "find the old cabin ruins mentioned on RoadTripRyan but was unsuccessful."
        ),
        "links": [{"url": "https://www.roadtripryan.com/go/t/utah/northern-utah/hell-hole-lake",
                   "title": "Hell Hole Lake - Western Uintas - Road Trip Ryan"}],
    },
    {
        "title": "Little Hidden w/ Dilworth",
        "date": "2026-07",
        "lakes": ["W-21"],
        "body": "Dilworth caught a nice 18 inch brookie here. It was delicious. :)",
    },
    {
        "title": "East Slide w/ Ryan",
        "date": "2026-08",
        "lakes": ["LF-44"],
        "body": (
            "Brutal approach! Ryan and I ascended from south at an attempted diagonal, "
            "then descended almost straight down the outlet ravine, other than "
            "circumnavigating some cliffs near the top. See CalTopo for deets."
        ),
    },
    {
        "title": "Norway Flats: Big Elk, Fire + W-62 w/ Ryan",
        "date": "2026-09",
        "lakes": ["A-18", "A-14", "W-62"],
        "body": (
            "Big Elk (A-18): Ryan and I took his new truck up the Norway flats Road and "
            "parked where 035 branches off to 916, which took 45 minutes. I think his "
            "truck would’ve easily made it to where 035 branches 035A. But it was "
            "actually a blast ride mountain bikes to the trailhead (15 minutes). We "
            "each caught 3 brookies, and surprisingly zero tigers given the stocking "
            "record for the last 10 years. Battling the wind in my pack raft wasn’t "
            "much fun.\n\n"
            "Fire (A-14): Didn’t have much time. Had one on that broke off. Worked out "
            "well to shortcut off trail to the west and link up with the trail back to "
            "Big Elk, instead of going back to Island.\n\n"
            "W-62: Ryan and I each caught a few small guys."
        ),
    },
    {
        "title": "East Kibah",
        "date": "2026-09",
        "lakes": ["DF-11"],
        "body": "Only a few casts, didn’t leave ourselves enough time.",
    },
]

POTTS = "https://utahstories.com/2021/08/the-top-five-lakes-in-the-high-uinta-mountains-to-visit/"
LINKS = [
    {"lake": "BR-20", "url": "https://backcountrypost.com/threads/kermsuh-shortcut.2363/",
     "title": "Kermsuh “shortcut” — Backcountry Post",
     "note": "Up and over the Hayden/Kletting saddle from Hwy 150"},
    {"lake": "BR-29", "url": "https://www.roadtripryan.com/go/t/utah/northern-utah/hell-hole-lake",
     "title": "Hell Hole Lake - Western Uintas - Road Trip Ryan",
     "note": "Shortcut trailhead off the Mirror Lake Hwy; old cabin ruins by the bridge"},
    {"lake": "BR-31", "url": POTTS,
     "title": "The Top Five Lakes in the High Uinta Mountains to Visit",
     "note": "Potts: from Christmas Meadows, 27 brookies on consecutive casts"},
    {"lake": "BR-31", "url": "https://www.utahwildlife.net/threads/hell-hole-seidner-lake.25935/",
     "title": "Hell Hole - Seidner Lake | Utah Wildlife Forum",
     "note": "Up and over from Hell Hole, around the base of A-1 Peak"},
    {"lake": "G-38", "url": "https://redrockadventure.com/fish/utah-fishing-lakes-reservoirs/31-uinta-mountains/330-family-fishing-at-alligator-lake",
     "title": "Family Fishing at Alligator Lake — Red Rock Adventure",
     "note": "Dave Webb’s 2005 report"},
    {"lake": "LF-44", "url": "https://backcountrypost.com/threads/east-slide-lake-uintas-6-28-12.1019",
     "title": "East Slide Lake - Uintas (6/28/12)",
     "note": "2012 day trip; cairns mark the Oweep gorge crossing"},
    {"lake": "P-62", "url": POTTS,
     "title": "The Top Five Lakes in the High Uinta Mountains to Visit",
     "note": "Potts: route from the Upper Setting Rd trailhead"},
]


def build_docs():
    docs = []
    for t in TRIPS:
        docs.append({"kind": "trip", "doc": {
            "id": _id("t", t["date"], t["title"]), "updated": UPDATED,
            "title": t["title"], "planned": False,
            "date": t["date"], "end_date": t.get("end_date"), "when": None,
            "body": t["body"], "lakes": t["lakes"], "links": t.get("links", [])}})
    for lk in LINKS:
        docs.append({"kind": "link", "doc": {
            "id": _id("l", "2026-10-10", lk["lake"] + lk["url"]), "updated": UPDATED,
            "lake": lk["lake"], "url": lk["url"], "title": lk["title"], "note": lk["note"]}})
    ids = [d["doc"]["id"] for d in docs]
    assert len(ids) == len(set(ids)), "id collision"
    return docs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    ap.add_argument("mode", nargs="?", choices=["apply"], help="omit for a dry run")
    ap.add_argument("--server", default="http://olaf.local:8802")
    args = ap.parse_args()

    docs = build_docs()
    if args.mode != "apply":
        print(json.dumps(docs, indent=1, ensure_ascii=False))
        print(f"\n{len(TRIPS)} trips, {len(LINKS)} links (dry run; pass 'apply' to write)",
              file=sys.stderr)
        return 0

    with urllib.request.urlopen(args.server + "/api/user-data", timeout=10) as r:
        journal = json.load(r)["journal"]
    have = {(k, d["id"]) for k, plural in (("trip", "trips"), ("link", "links"))
            for d in journal.get(plural, [])}
    todo = [d for d in docs if (d["kind"], d["doc"]["id"]) not in have]
    print(f"{len(docs) - len(todo)} already on the server, {len(todo)} to write")
    if not todo:
        return 0
    req = urllib.request.Request(
        args.server + "/api/journal", method="POST",
        data=json.dumps({"device": DEVICE, "docs": todo}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        results = json.load(r)["results"]
    bad = [x for x in results if x["result"] != "applied"]
    for x in results:
        print(f"  {x['kind']:5} {x['id']}  {x['result']}  {x.get('message', '')}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
