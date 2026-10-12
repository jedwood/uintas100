#!/bin/bash
# Regression suite for trips / photos / links (docs/trips-photos-links-plan.md):
#   1. server-test.sh  — the edits server's journal, media, link-title and
#      static-fence endpoints (curl, fresh harness)
#   2. client-test.js  — index.html's journal state, sync, media store, EXIF +
#      image pipeline, two devices, in Chromium AND WebKit (fresh harness each)
#   3. ImageIO check that no uploaded image file carries GPS / camera / date
#   4. ui-test.js      — the lake modal's journal UI at iPhone size: Trips &
#      photos card, ＋ Photo, lightbox, Links card, Junesucker source link
#   5. trip-test.js    — the trip modal: editor, view, planned + mark as
#      done, lake ↔ trip navigation, deep link, delete keeping photos
#   6. list-test.js    — the journal list (Trips / Planned / Photos), home
#      counts, drainage scoping, Sync panel photo status + save-all
#
#   tests/journal/run.sh               # all of the above
#   tests/journal/run.sh chromium      # client test in one browser only
#   JOURNAL_TEST_ONLY=trip-test.js tests/journal/run.sh chromium   # one UI script
#
# Never touches the real DB, journal or media: the harness runs on :8899 with
# --db/--log/--journal/--media pointed at a temp dir, and the client test
# aborts any request to olaf.local / ts.net (the live server). macOS only
# (sips + swift build the fixtures and read image metadata). Needs
# playwright-cli and network access (two link-title checks).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
W=$(mktemp -d "${TMPDIR:-/tmp}/uintas-journal-test-XXXX")
if [[ $# -gt 0 ]]; then BROWSERS=("$@"); else BROWSERS=(chromium webkit); fi
ONLY="${JOURNAL_TEST_ONLY:-}"   # e.g. JOURNAL_TEST_ONLY=trip-test.js: just that UI script
SERVER=; FIXSRV=
cleanup() {
    { [[ -n "$SERVER" ]] && kill "$SERVER" && wait "$SERVER"; } 2>/dev/null
    { [[ -n "$FIXSRV" ]] && kill "$FIXSRV" && wait "$FIXSRV"; } 2>/dev/null
    playwright-cli -s=uintas-journal-test close >/dev/null 2>&1
    rm -rf "$W"
}
trap cleanup EXIT
fail=0

# The app as the harness serves it: the repo, except a lakes_data.json whose
# published journal is empty, so the UI tests don't depend on Jed's real
# trips/links (which the live data now carries).
mkdir -p "$W/web"
for f in "$ROOT"/* "$ROOT"/.[!.]*; do
    [[ "$(basename "$f")" == lakes_data.json ]] || ln -s "$f" "$W/web/"
done
python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
d["journal"] = {"trips": [], "photos": [], "links": []}
json.dump(d, open(sys.argv[2], "w"))' "$ROOT/lakes_data.json" "$W/web/lakes_data.json" || exit 1

start_harness() {   # fresh scratch state each time
    [[ -n "$SERVER" ]] && { kill "$SERVER" 2>/dev/null; wait "$SERVER" 2>/dev/null; }
    rm -rf "$W/h" && mkdir -p "$W/h" && cp "$ROOT/uinta_lakes.db" "$W/h/x.db"
    python3 "$ROOT/scripts/edits_server.py" --db "$W/h/x.db" --log "$W/h/x.jsonl" \
        --journal "$W/h/j.json" --media "$W/h/media" --web-root "$W/web" \
        --no-git --port 8899 --host 127.0.0.1 \
        >"$W/server.log" 2>&1 &
    SERVER=$!
    curl -s --retry 20 --retry-connrefused --retry-delay 1 http://127.0.0.1:8899/api/ping >/dev/null \
        || { echo "harness did not start — see $W/server.log"; cat "$W/server.log"; exit 1; }
}

python3 "$HERE/make_fixtures.py" "$ROOT/cma_photos/p1-1.jpg" "$W/fixtures" || exit 1
(cd "$W/fixtures" && exec python3 -m http.server 8898 --bind 127.0.0.1 >/dev/null 2>&1) &
FIXSRV=$!

if [[ -z "$ONLY" ]]; then
    echo "== server endpoints"
    start_harness
    bash "$HERE/server-test.sh" "$W/h" || fail=1
fi

# One Playwright script against a fresh harness in a fresh browser.
run_browser_script() {   # <script.js> <browser> <log name>
    start_harness
    playwright-cli -s=uintas-journal-test close >/dev/null 2>&1
    if [[ "$2" == chromium ]]; then playwright-cli -s=uintas-journal-test open >/dev/null 2>&1
    else playwright-cli -s=uintas-journal-test open --browser="$2" >/dev/null 2>&1; fi
    playwright-cli -s=uintas-journal-test run-code --filename="$1" >"$W/$3.log" 2>&1
    python3 - "$W/$3.log" "$3" <<'EOF'
import re, json, sys
s = open(sys.argv[1]).read()
m = re.search(r'### Result\n(".*?")\n', s, re.S)
out = json.loads(m.group(1)) if m else "ERROR  no result from run-code:\n" + s[:3000]
print(out)
bad = out.count("FAIL  ") + out.count("ERROR  ")
print(f"\n{sys.argv[2]}: passed={out.count('PASS  ')} failed={bad}")
sys.exit(1 if bad else 0)
EOF
}

for b in "${BROWSERS[@]}"; do
    if [[ -n "$ONLY" ]]; then
        echo; echo "== $ONLY ($b)"
        run_browser_script "$HERE/$ONLY" "$b" "only-$b" || fail=1
        continue
    fi
    echo; echo "== client data layer ($b)"
    run_browser_script "$HERE/client-test.js" "$b" "client-$b" || fail=1
    # Independent read of what this browser's encoder actually wrote.
    leaks=$(swift "$HERE/imageio_meta.swift" "$W"/h/media/*.jpg 2>/dev/null | grep -v " - - - - - - - -$")
    if [[ -z "$leaks" && -n "$(ls "$W"/h/media/*.jpg 2>/dev/null)" ]]; then
        echo "PASS  ImageIO: no GPS / DateTimeOriginal in any uploaded $b image"
    else
        echo "FAIL  ImageIO found metadata (or no images were uploaded):"; echo "$leaks"; fail=1
    fi
    echo; echo "== lake modal UI ($b)"
    run_browser_script "$HERE/ui-test.js" "$b" "ui-$b" || fail=1
    echo; echo "== trip modal UI ($b)"
    run_browser_script "$HERE/trip-test.js" "$b" "trip-$b" || fail=1
    echo; echo "== journal list UI ($b)"
    run_browser_script "$HERE/list-test.js" "$b" "list-$b" || fail=1
done

echo
if [[ $fail -eq 0 ]]; then echo "all passed"; else echo "FAILURES"; fi
exit $fail
