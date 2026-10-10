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
    POST /api/journal    -> {device, docs:[{kind, doc}]}  trips / photo metadata
                            / lake links into data/journal.json, per-doc LWW on
                            doc.updated (scripts/journal_store.py)
    PUT  /api/media/<id>.jpg | <id>_t.jpg | <id>.json
                            photo full / thumbnail / private GPS sidecar into
                            the gitignored data/media/ (never committed)
    GET  /api/media/<id>.jpg | <id>_t.jpg
    GET  /api/link-title?url=…  -> {title}  (the client can't fetch cross-origin)

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
    python3 scripts/edits_server.py --db /tmp/x.db --log /tmp/x.jsonl \
        --journal /tmp/j.json --media /tmp/media --no-git --port 8899  # test harness

Runs on the Mini as the com.limechile.uintas-edits-server LaunchAgent
(see deploy/README.md).
"""

import argparse
import html
import ipaddress
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from writer_guard import REPO_ROOT, is_readonly_mirror  # noqa: E402
import push_utils  # noqa: E402  (Web Push subscribe/unsubscribe + VAPID public key)
import journal_store  # noqa: E402  (data/journal.json: trips, photo metadata, links)

DEFAULT_DB = os.path.join(REPO_ROOT, "uinta_lakes.db")
DEFAULT_LOG = os.path.join(REPO_ROOT, "data", "app_edits_log.jsonl")
EDIT_LOG = DEFAULT_LOG  # overridden by --log (tests)
JOURNAL_PATH = journal_store.DEFAULT_JOURNAL  # --journal (tests)
MEDIA_DIR = journal_store.DEFAULT_MEDIA       # --media (tests)

# /api/media/<photo id><suffix>; suffix -> (max bytes, content type)
MEDIA_PATH_RE = re.compile(r"^/api/media/(p-[a-z0-9]+-[a-z0-9]{4})(\.jpg|_t\.jpg|\.json)$")
MEDIA_LIMITS = {".jpg": 12 * 1024 * 1024, "_t.jpg": 12 * 1024 * 1024, ".json": 4096}
MAX_JOURNAL_BODY = 8 * 1024 * 1024
LINK_TITLE_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                 "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")

EDITABLE_FIELDS = {"status", "jed_notes", "trip_reports", "starred"}
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
            if "kind" in e:
                continue  # a journal-doc entry; its LWW state is journal.json itself
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
                if field == "starred" and value not in (None, 0, 1):
                    results.append({"id": edit_id, "result": "error",
                                    "message": f"bad starred {value!r}"})
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


def known_lakes(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {r[0] for r in conn.execute("SELECT letter_number FROM lakes")}
    finally:
        conn.close()


def apply_journal(db_path, device, docs):
    """Apply a batch of journal docs under the write lock; per-doc results.

    journal.json is re-read on every batch rather than cached, so a one-off
    script that edits it on the Mini (e.g. the Phase-6 migration) isn't
    clobbered by a stale in-memory copy."""
    lakes = known_lakes(db_path)
    results, applied_any = [], False
    with _write_lock:
        data = journal_store.load(JOURNAL_PATH)
        for item in docs:
            item = item if isinstance(item, dict) else {}
            kind, doc = item.get("kind"), item.get("doc")
            doc_id = doc.get("id") if isinstance(doc, dict) else None
            try:
                clean = journal_store.clean_doc(kind, doc, lakes)
            except journal_store.DocError as e:
                results.append({"kind": kind, "id": doc_id, "result": "error", "message": str(e)})
                continue
            applied, current = journal_store.apply_doc(data, kind, clean)
            if not applied:
                results.append({"kind": kind, "id": doc_id, "result": "superseded",
                                "current": current})
                continue
            append_log({
                "kind": kind, "id": doc_id, "ts": clean["updated"], "device": device,
                "applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
            results.append({"kind": kind, "id": doc_id, "result": "applied"})
            applied_any = True
        if applied_any:
            journal_store.save(data, JOURNAL_PATH)
    return results, applied_any


def get_journal():
    """Everything incl. tombstones, so other devices learn about deletes."""
    data = journal_store.load(JOURNAL_PATH)
    return {plural: data[plural] for plural in journal_store.KINDS.values()}


def get_media_meta():
    """Private location sidecars, served only by the Mini (never exported)."""
    out = {}
    if not os.path.isdir(MEDIA_DIR):
        return out
    for name in os.listdir(MEDIA_DIR):
        if name.endswith(".json") and journal_store.MEDIA_ID_RE.match(name[:-5]):
            try:
                with open(os.path.join(MEDIA_DIR, name), encoding="utf-8") as f:
                    out[name[:-5]] = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
    return out


def write_media(name, body):
    """Atomic write into MEDIA_DIR (tmp + rename); idempotent."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    tmp = os.path.join(MEDIA_DIR, f".{name}.{threading.get_ident()}.tmp")
    with open(tmp, "wb") as f:
        f.write(body)
    os.replace(tmp, os.path.join(MEDIA_DIR, name))


def _is_public_host(host):
    """Refuse link-title fetches aimed at the Mini's own network."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved \
                or ip.is_multicast or ip.is_unspecified:
            return False
    return True


def fetch_link_title(url):
    """og:title, else <title>, of a page — '' when unreachable or absent."""
    host = urlsplit(url).hostname or ""
    if not _is_public_host(host):
        return ""
    req = urllib.request.Request(url, headers={
        "User-Agent": LINK_TITLE_UA,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "xml" not in ctype:
                return ""
            raw = resp.read(300 * 1024)
            charset = resp.headers.get_content_charset() or "utf-8"
    except Exception:  # network, TLS, HTTP error, timeout: blank title
        return ""
    text = raw.decode(charset, errors="replace")
    for pattern in (
        r"<meta[^>]+property=[\"']og:title[\"'][^>]*content=[\"']([^\"']*)[\"']",
        r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]*property=[\"']og:title[\"']",
        r"<title[^>]*>(.*?)</title>",
    ):
        m = re.search(pattern, text, re.I | re.S)
        if m:
            title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
            if title:
                return title[:journal_store.MAX_TITLE]
    return ""


def committer_loop():
    """Background thread: after a batch applies, wait for a quiet gap, then
    commit + push. The pre-commit hook regenerates seeds + lakes_data.json.

    Goes through auto_commit.commit_own_files so ONLY the DB, the edit log and
    the journal (plus what the hook derives from them) are committed — never
    whatever a dev session has staged or half-edited in this same working
    tree. data/media/ is gitignored and never named here."""
    from auto_commit import commit_own_files
    while True:
        _commit_signal.wait()
        time.sleep(COMMIT_QUIET_SECS)
        _commit_signal.clear()
        # `git add` fails on a missing pathspec, and journal.json only exists
        # once the first doc has been saved.
        paths = [p for p in ("uinta_lakes.db", "data/app_edits_log.jsonl", "data/journal.json")
                 if os.path.exists(os.path.join(REPO_ROOT, p))]
        try:
            with _write_lock:
                commit_own_files(paths, "App edits: updates from the PWA",
                                 log=lambda m: print("[edits-server] " + m))
        except subprocess.CalledProcessError as e:
            print(f"[edits-server] WARNING: git commit failed: {e.stderr or e}")
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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parts = urlsplit(self.path)
        if self.path == "/api/ping":
            return self._json({"ok": True, "role": "writer"})
        if self.path == "/api/user-data":
            return self._json({"lakes": get_user_data(self.db_path),
                               "journal": get_journal(),
                               "media_meta": get_media_meta()})
        if parts.path == "/api/link-title":
            url = (parse_qs(parts.query).get("url") or [""])[0]
            try:
                url = journal_store.check_url(url)
            except journal_store.DocError as e:
                return self._json({"error": str(e)}, 400)
            return self._json({"title": fetch_link_title(url)})
        m = MEDIA_PATH_RE.match(parts.path)
        if m and m.group(2) != ".json":
            return self._get_media(m.group(1) + m.group(2))
        if self.path == "/api/push/public-key":
            # The VAPID application server key the PWA passes to
            # pushManager.subscribe(). Public by design; also embedded in
            # index.html, but serving it lets the app confirm the live key.
            try:
                return self._json({"key": push_utils.application_server_key()})
            except FileNotFoundError:
                return self._json({"error": "no vapid key on server"}, 503)
        if parts.path.startswith("/api/") or self._is_private():
            return self._json({"error": "not found"}, 404)
        return super().do_GET()  # also serves the repo statically (test harness)

    def do_HEAD(self):
        if self._is_private():
            return self._json({"error": "not found"}, 404)
        return super().do_HEAD()

    def _is_private(self):
        """The static fallback serves the whole repo, so fence off the Web
        Push secrets and the private photos it would otherwise expose.
        Resolved through translate_path (the same mapping the fallback uses,
        so `//data/push`, `%2e%2e` tricks etc. land in the same place) and
        compared lower-cased: the Mini's volume is case-insensitive."""
        target = os.path.realpath(self.translate_path(self.path)).lower()
        for private in (os.path.join(REPO_ROOT, "data", "push"),
                        os.path.join(REPO_ROOT, "data", "media"), MEDIA_DIR):
            private = os.path.realpath(private).lower()
            if target == private or target.startswith(private + os.sep):
                return True
        return False

    def _get_media(self, name):
        path = os.path.join(MEDIA_DIR, name)
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            return self._json({"error": "not found"}, 404)
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, max-age=31536000, immutable")
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        m = MEDIA_PATH_RE.match(urlsplit(self.path).path)
        if not m:
            return self._json({"error": "not found"}, 404)
        photo_id, suffix = m.groups()
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self._json({"error": "Content-Length required"}, 411)
        if length <= 0:
            return self._json({"error": "empty body"}, 400)
        if length > MEDIA_LIMITS[suffix]:
            self.close_connection = True  # don't drain a huge body
            return self._json({"error": f"too large (max {MEDIA_LIMITS[suffix]} bytes)"}, 413)
        body = self.rfile.read(length)
        if suffix == ".json":
            try:
                sidecar = journal_store.validate_sidecar(json.loads(body))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._json({"error": "bad json"}, 400)
            except journal_store.DocError as e:
                return self._json({"error": str(e)}, 400)
            body = json.dumps(sidecar, ensure_ascii=False).encode()
        else:
            ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if ctype != "image/jpeg" or not body.startswith(b"\xff\xd8\xff"):
                return self._json({"error": "body must be image/jpeg"}, 415)
        write_media(photo_id + suffix, body)
        return self._json({"ok": True, "id": photo_id, "bytes": len(body)})

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def do_POST(self):
        if self.path == "/api/edits":
            return self._post_edits()
        if self.path == "/api/journal":
            return self._post_journal()
        if self.path == "/api/push/subscribe":
            return self._post_subscribe()
        if self.path == "/api/push/unsubscribe":
            return self._post_unsubscribe()
        if self.path == "/api/push/test":
            return self._post_test()
        return self._json({"error": "not found"}, 404)

    def _post_edits(self):
        payload = self._read_json()
        if payload is None:
            return self._json({"error": "bad json"}, 400)
        edits = payload.get("edits") or []
        if not isinstance(edits, list) or len(edits) > 500:
            return self._json({"error": "bad edits"}, 400)
        results, applied_any = apply_edits(
            self.db_path, str(payload.get("device", ""))[:80], edits)
        if applied_any and self.use_git:
            _commit_signal.set()
        return self._json({"results": results})

    def _post_journal(self):
        if int(self.headers.get("Content-Length", 0) or 0) > MAX_JOURNAL_BODY:
            self.close_connection = True
            return self._json({"error": "too large"}, 413)
        payload = self._read_json()
        if not isinstance(payload, dict):
            return self._json({"error": "bad json"}, 400)
        docs = payload.get("docs") or []
        if not isinstance(docs, list) or len(docs) > 500:
            return self._json({"error": "bad docs"}, 400)
        results, applied_any = apply_journal(
            self.db_path, str(payload.get("device", ""))[:80], docs)
        if applied_any and self.use_git:
            _commit_signal.set()
        return self._json({"results": results})

    def _post_subscribe(self):
        # Store a device's Web Push subscription so the stocking job can notify
        # it. Subscriptions are secrets kept OUT of git (data/push/), so this
        # touches nothing the commit/seed machinery cares about.
        payload = self._read_json()
        if payload is None:
            return self._json({"error": "bad json"}, 400)
        try:
            count = push_utils.add_subscription(
                payload.get("subscription"), device=payload.get("device", ""))
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        return self._json({"ok": True, "subscriptions": count})

    def _post_unsubscribe(self):
        payload = self._read_json()
        if payload is None:
            return self._json({"error": "bad json"}, 400)
        removed = push_utils.remove_subscription(payload.get("endpoint", ""))
        return self._json({"ok": True, "removed": removed})

    def _post_test(self):
        # "Send test" button in the app: fire a real push to every subscribed
        # device so a fresh install can confirm delivery + badging end to end.
        payload = self._read_json() or {}
        msg = str(payload.get("message") or "Test push from the Uintas Mini 🏔️")[:200]
        result = push_utils.broadcast(
            title="🏔️ Uintas test", body=msg, badge=1,
            report={"when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "total": 0, "items": [], "test": True, "message": msg})
        return self._json({"ok": True, **result})

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
    parser.add_argument("--journal", default=journal_store.DEFAULT_JOURNAL,
                        help="journal.json path (tests point this at a scratch file)")
    parser.add_argument("--media", default=journal_store.DEFAULT_MEDIA,
                        help="photo media dir (tests point this at a scratch dir)")
    args = parser.parse_args()
    global EDIT_LOG, JOURNAL_PATH, MEDIA_DIR
    EDIT_LOG = args.log
    JOURNAL_PATH = args.journal
    MEDIA_DIR = args.media

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
