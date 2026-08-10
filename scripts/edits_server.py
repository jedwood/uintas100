#!/usr/bin/env python3
"""
App-edits sync server — the write path for the PWA's "My Record" fields
(status / jed_notes / trip_reports), replacing Apple Notes as the way those
fields are edited.

Single-writer model, preserved: edits can ORIGINATE on any device (iPhone in
the mountains, the MacBook, the Mini itself) — each client queues them locally
in the PWA (localStorage, offline-capable) and flushes the queue here when it
can reach this server. Only THIS process, running on the Mini, ever writes
uinta_lakes.db, so the Mini stays the sole DB writer and mirrors stay mirrors.
It refuses to start on a clone carrying the `.db-readonly` marker.

Endpoints (CORS-open, so the MacBook's own localhost:8000 app can call it):
    GET  /api/ping       -> {ok, role:"writer"}   (client's reachability probe)
    GET  /api/user-data  -> current status/jed_notes/trip_reports for all lakes
                            (lets a device fold in edits made from OTHER devices
                            immediately, without waiting for a git pull)
    POST /api/edits      -> {device, edits:[{id, lake, field, value, ts}]}
                            applies each edit last-write-wins by client
                            timestamp; answers per-edit applied/superseded.

Conflict handling: every applied edit is appended to data/app_edits_log.jsonl
(committed — a git-diffable audit trail). An incoming edit older than the
newest already-applied edit for the same (lake, field) is answered
"superseded" with the current value, so a long-offline device can't clobber a
newer edit made elsewhere. The log deliberately lives OUTSIDE the DB so the
seeds/rebuild/verify machinery is untouched.

After a batch applies, the DB (+ log) is committed and pushed in a background
thread — the pre-commit hook regenerates data/seeds/ and lakes_data.json, so
mirrors pick the edits up on their next pull, exactly like a Notes-sync commit
used to.

Usage:
    python3 scripts/edits_server.py                 # 0.0.0.0:8802 (LAN)
    python3 scripts/edits_server.py --port 9000 --host 127.0.0.1
    python3 scripts/edits_server.py --db /tmp/x.db --no-git   # test harness

Runs on the Mini as the com.limechile.uintas-edits-server LaunchAgent
(see deploy/README.md).
"""

import argparse
import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from writer_guard import REPO_ROOT, is_readonly_mirror  # noqa: E402

DEFAULT_DB = os.path.join(REPO_ROOT, "uinta_lakes.db")
DEFAULT_LOG = os.path.join(REPO_ROOT, "data", "app_edits_log.jsonl")
EDIT_LOG = DEFAULT_LOG  # overridden by --log (tests)

EDITABLE_FIELDS = {"status", "jed_notes", "trip_reports"}
VALID_STATUSES = {"CAUGHT", "NONE", "OTHERS"}  # DB CHECK constraint; NULL = unset

# One lock serializes DB writes + log appends across request threads.
_write_lock = threading.Lock()
# (lake, field) -> newest applied client ts (ISO-8601, lexicographically ordered)
_latest = {}

# Debounced background commit: each applied batch pokes the committer; it waits
# for a quiet moment so a burst of flushes lands as one commit.
_commit_signal = threading.Event()
COMMIT_QUIET_SECS = 5


def load_log_index():
    """Rebuild the (lake, field) -> newest-ts index from the committed log."""
    _latest.clear()
    if not os.path.exists(EDIT_LOG):
        return
    with open(EDIT_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (e.get("lake"), e.get("field"))
            ts = e.get("ts", "")
            if ts > _latest.get(key, ""):
                _latest[key] = ts


def append_log(entry):
    os.makedirs(os.path.dirname(EDIT_LOG), exist_ok=True)
    with open(EDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def apply_edits(db_path, device, edits):
    """Apply a batch under the write lock; return per-edit results."""
    results = []
    applied_any = False
    with _write_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            for e in edits:
                edit_id = e.get("id")
                lake = e.get("lake")
                field = e.get("field")
                ts = e.get("ts") or ""
                value = e.get("value")
                if isinstance(value, str):
                    value = value.strip()
                if value == "":
                    value = None  # status CHECK forbids ''; blank notes -> NULL

                if field not in EDITABLE_FIELDS:
                    results.append({"id": edit_id, "result": "error",
                                    "message": f"field {field!r} not editable"})
                    continue
                if field == "status" and value is not None and value not in VALID_STATUSES:
                    results.append({"id": edit_id, "result": "error",
                                    "message": f"bad status {value!r}"})
                    continue
                row = conn.execute(
                    f"SELECT {field} AS v FROM lakes WHERE letter_number = ?", (lake,)
                ).fetchone()
                if row is None:
                    results.append({"id": edit_id, "result": "error",
                                    "message": f"no lake {lake!r}"})
                    continue

                newest = _latest.get((lake, field), "")
                if ts < newest:
                    # A newer edit (likely from another device) already won.
                    results.append({"id": edit_id, "result": "superseded",
                                    "current": row["v"]})
                    continue

                conn.execute(
                    f"UPDATE lakes SET {field} = ? WHERE letter_number = ?",
                    (value, lake),
                )
                _latest[(lake, field)] = ts
                append_log({
                    "id": edit_id, "lake": lake, "field": field, "value": value,
                    "ts": ts, "device": device,
                    "applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                results.append({"id": edit_id, "result": "applied"})
                applied_any = True
            conn.commit()
        finally:
            conn.close()
    return results, applied_any


def get_user_data(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    out = {}
    for r in conn.execute(
        """SELECT letter_number, status, jed_notes, trip_reports FROM lakes
           WHERE status IS NOT NULL OR jed_notes IS NOT NULL OR trip_reports IS NOT NULL"""
    ):
        out[r["letter_number"]] = {
            "status": r["status"],
            "jed_notes": r["jed_notes"],
            "trip_reports": r["trip_reports"],
        }
    conn.close()
    return out


def committer_loop():
    """Background thread: after a batch applies, wait for a quiet gap, then
    commit + push. The pre-commit hook regenerates seeds + lakes_data.json."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=REPO_ROOT,
                              capture_output=True, text=True)
    while True:
        _commit_signal.wait()
        time.sleep(COMMIT_QUIET_SECS)
        _commit_signal.clear()
        with _write_lock:
            changed = git("diff", "--quiet", "--",
                          "uinta_lakes.db", "data/app_edits_log.jsonl").returncode != 0
            untracked_log = (not changed and
                             git("ls-files", "--error-unmatch",
                                 "data/app_edits_log.jsonl").returncode != 0
                             and os.path.exists(EDIT_LOG))
            if not changed and not untracked_log:
                continue
            git("add", "uinta_lakes.db", "data/app_edits_log.jsonl")
            c = git("commit", "-m", "App edits: status/notes updates from the PWA")
            sys.stdout.write(c.stdout + c.stderr)
        p = git("push")
        if p.returncode != 0:
            print("[edits-server] WARNING: git push failed (committed locally).")
        sys.stdout.flush()


class EditsHandler(SimpleHTTPRequestHandler):
    db_path = DEFAULT_DB
    use_git = True

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/ping":
            return self._json({"ok": True, "role": "writer"})
        if self.path == "/api/user-data":
            return self._json({"lakes": get_user_data(self.db_path)})
        return super().do_GET()  # also serves the repo statically (test harness)

    def do_POST(self):
        if self.path != "/api/edits":
            return self._json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "bad json"}, 400)
        edits = payload.get("edits") or []
        if not isinstance(edits, list) or len(edits) > 500:
            return self._json({"error": "bad edits"}, 400)
        results, applied_any = apply_edits(
            self.db_path, str(payload.get("device", ""))[:80], edits)
        if applied_any and self.use_git:
            _commit_signal.set()
        return self._json({"results": results})

    def log_message(self, fmt, *args):
        first = args[0] if args else ""
        if isinstance(first, str) and "/api/" in first and "/api/ping" not in first:
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8802)
    parser.add_argument("--host", default="0.0.0.0",
                        help="bind address (default 0.0.0.0: the whole point is LAN access)")
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="database path (tests point this at a scratch copy)")
    parser.add_argument("--no-git", action="store_true",
                        help="don't commit/push after edits (tests)")
    parser.add_argument("--log", default=DEFAULT_LOG,
                        help="edit-log path (tests point this at a scratch file)")
    args = parser.parse_args()
    global EDIT_LOG
    EDIT_LOG = args.log

    if is_readonly_mirror():
        print("[writer-guard] .db-readonly present — this clone is a read-only mirror.")
        print("The edits server writes uinta_lakes.db, so it runs ONLY on the Mini.")
        print("Point the app's sync at the Mini instead (Sync panel -> http://olaf.local:8802).")
        sys.exit(1)
    if not os.path.exists(args.db):
        print(f"[edits-server] {args.db} missing (external volume not mounted?); exiting.")
        sys.exit(1)

    load_log_index()
    EditsHandler.db_path = args.db
    EditsHandler.use_git = not args.no_git
    if not args.no_git:
        threading.Thread(target=committer_loop, daemon=True).start()

    handler = partial(EditsHandler, directory=str(REPO_ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"App-edits sync server on http://{socket.gethostname()}:{args.port}/api/ping"
          f"  (db={args.db}, git={'off' if args.no_git else 'on'})")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
