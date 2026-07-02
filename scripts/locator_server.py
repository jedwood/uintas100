#!/usr/bin/env python3
"""
Lake Locator — a local tool for placing/verifying lake coordinates.

Serves the repo (so locator.html, drainage maps, and pamphlet PDFs load) and
exposes a tiny JSON API that writes coordinates straight back into
uinta_lakes.db. This is a LOCAL admin tool, not part of the deployed PWA.

Because it WRITES the DB, it obeys the single-writer model: it refuses to start
on a read-only mirror (a clone with the `.db-readonly` marker). Run it on the
writer machine (the Mac Mini) and browse to it from anywhere on the LAN.

Usage:
    python3 scripts/locator_server.py                  # then open http://localhost:8777/locator.html
    python3 scripts/locator_server.py --port 9000
    python3 scripts/locator_server.py --host 0.0.0.0   # allow LAN access (run on the Mini,
                                                       # click from the MacBook's browser)

Workflow:
    1. (optional) python3 scripts/seed_coordinates.py   # pre-place ~70% of pins
    2. python3 scripts/locator_server.py                # confirm seeds, place the rest
    3. python3 scripts/export_web_data.py               # push coords into the PWA data
"""

import argparse
import json
import socket
import sqlite3
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from coord_utils import DB_PATH, REPO_ROOT, ensure_coord_columns
from writer_guard import is_readonly_mirror

# Each drainage -> the DWR pamphlet PDF(s) whose maps show its lake designations.
# (Several drainages share a pamphlet.)
DRAINAGE_PAMPHLETS = {
    "Ashley Creek Drainage": ["dwr-ashley-creek.pdf"],
    "Bear River Drainage": ["dwr-bear-blacks-fork.pdf"],
    "Blacks Fork Drainage": ["dwr-bear-blacks-fork.pdf"],
    "Dry Gulch Drainage": ["dwr-dry-gulch-and-uinta.pdf"],
    "Uinta River Drainage": ["dwr-dry-gulch-and-uinta.pdf", "dwr-uintas-rock-creek.pdf"],
    "Duchesne River Drainage": ["dwr-duchesne.pdf"],
    "Provo River Drainage": ["dwr-provo-weber.pdf"],
    "Weber River Drainage": ["dwr-provo-weber.pdf"],
    "Sheep/Carter Creek Drainages": ["dwr-sheep-carter-burnt-fork.pdf"],
    "Burnt Fork Drainage": ["dwr-sheep-carter-burnt-fork.pdf"],
    "Smiths Fork Drainage": ["dwr-smith-henry-beaver.pdf"],
    "Henrys Fork Drainage": ["dwr-smith-henry-beaver.pdf"],
    "Beaver Creek Drainage": ["dwr-smith-henry-beaver.pdf"],
    "Rock Creek Drainage": ["dwr-uintas-rock-creek.pdf"],
    "White Rocks Drainage": ["dwr-whiterocks.pdf"],
    "Yellowstone Drainage": ["dwr-yellowstone-lake-fork-swift.pdf"],
    "Lake Fork Drainage": ["dwr-yellowstone-lake-fork-swift.pdf"],
    "Swift Creek Drainage": ["dwr-yellowstone-lake-fork-swift.pdf"],
}
PAMPHLET_DIR = "data/dwr_original_pamphlets"

VALID_STATUSES = {"confirmed", "manual", "seed_unverified", "seed_suspect", "cant_find"}


def get_lakes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_coord_columns(conn)
    # drainage -> overview map image
    drainage_map = {
        row["name"]: row["map"]
        for row in conn.execute("SELECT name, map FROM drainages")
    }
    lakes = []
    for r in conn.execute(
        """SELECT id, letter_number, name, drainage, size_acres, max_depth_ft,
                  elevation_ft, fish_species, dwr_notes, junesucker_notes,
                  lat, lng, coord_source, coord_status
           FROM lakes ORDER BY drainage, letter_number"""
    ):
        lakes.append({
            "id": r["id"],
            "letter_number": r["letter_number"],
            "name": r["name"],
            "drainage": r["drainage"],
            "size_acres": r["size_acres"],
            "max_depth_ft": r["max_depth_ft"],
            "elevation_ft": r["elevation_ft"],
            "fish_species": r["fish_species"],
            "dwr_notes": r["dwr_notes"],
            "junesucker_notes": r["junesucker_notes"],
            "lat": r["lat"],
            "lng": r["lng"],
            "coord_source": r["coord_source"],
            "coord_status": r["coord_status"],
            "drainage_map": drainage_map.get(r["drainage"]),
            "pamphlets": [f"{PAMPHLET_DIR}/{p}" for p in DRAINAGE_PAMPHLETS.get(r["drainage"], [])],
        })
    conn.close()
    return lakes


def save_lake(payload):
    letter_number = payload.get("letter_number")
    status = payload.get("status")
    if not letter_number or status not in VALID_STATUSES:
        return False, "missing/invalid letter_number or status"

    lat, lng = payload.get("lat"), payload.get("lng")
    if status in ("confirmed", "manual", "seed_unverified", "seed_suspect") and (lat is None or lng is None):
        return False, "coordinates required for this status"

    conn = sqlite3.connect(DB_PATH)
    ensure_coord_columns(conn)
    if status == "cant_find":
        conn.execute(
            "UPDATE lakes SET coord_status='cant_find' WHERE letter_number=?",
            (letter_number,),
        )
    else:
        # A human placing/confirming a pin: mark its source 'manual' so a future
        # re-seed never clobbers it.
        source = "manual" if status in ("confirmed", "manual") else payload.get("coord_source")
        conn.execute(
            "UPDATE lakes SET lat=?, lng=?, coord_status=?, coord_source=? WHERE letter_number=?",
            (lat, lng, status, source, letter_number),
        )
    changed = conn.total_changes
    conn.commit()
    conn.close()
    return (changed > 0), ("ok" if changed else "no lake with that designation")


class LocatorHandler(SimpleHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/lakes":
            return self._json({"lakes": get_lakes()})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/save":
            return self._json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "bad json"}, 400)
        ok, msg = save_lake(payload)
        return self._json({"ok": ok, "message": msg}, 200 if ok else 400)

    def log_message(self, fmt, *args):
        # Quieter: only log the API writes, not every tile/asset request
        if "api/save" in (args[0] if args else ""):
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8777)
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="bind address; use 0.0.0.0 to allow LAN access (run on the Mini, browse from another machine)",
    )
    args = parser.parse_args()

    if is_readonly_mirror():
        print("[writer-guard] .db-readonly present — this clone is a read-only mirror.")
        print("The Locator writes uinta_lakes.db, so it must run on the writer machine (the Mini):")
        print("    python3 scripts/locator_server.py --host 0.0.0.0")
        print("then open the LAN URL it prints from this machine's browser.")
        sys.exit(1)

    handler = partial(LocatorHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Lake Locator running:  http://localhost:{args.port}/locator.html")
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"LAN access:            http://{socket.gethostname()}:{args.port}/locator.html")
    print("Coordinates are written straight into uinta_lakes.db. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
