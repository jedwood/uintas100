#!/bin/bash
# Offline-guarantee regression suite for the PWA service worker.
#
# Drives Chromium (playwright-cli) against a fault-injecting static server
# (tests/offline/testserver.py) through the scenarios that bit us on
# 2026-09-21: first load → offline reload → a version bump whose precache
# fails (must NOT take over) → offline again → successful update → captive
# portal → lost data entry (IndexedDB fallback + Repair) → nothing left
# (honest error + Try again). Prints one PASS/FAIL line per assertion.
#
#   tests/offline/run.sh            # from the repo root
#
# Needs: python3, playwright-cli (npm i -g @playwright/cli). Port 8813.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PORT=8813
SESSION=uintas-offline-test

cleanup() {
    playwright-cli -s="$SESSION" close >/dev/null 2>&1 || true
    [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

rm -f "$HERE/results.txt"
python3 "$HERE/testserver.py" "$ROOT" "$PORT" >/dev/null 2>&1 &
SERVER_PID=$!
sleep 1
curl -sf "http://127.0.0.1:$PORT/__ctl?status" >/dev/null || { echo "server did not start"; exit 1; }

playwright-cli -s="$SESSION" close >/dev/null 2>&1 || true
playwright-cli -s="$SESSION" open --mobile >/dev/null 2>&1
if ! playwright-cli -s="$SESSION" run-code --filename="$HERE/offline-test.js" >"$HERE/last-run.log" 2>&1; then
    echo "run-code failed — see $HERE/last-run.log"
fi

cat "$HERE/results.txt" 2>/dev/null || { echo "no results written — see $HERE/last-run.log"; exit 1; }
if grep -q '^FAIL' "$HERE/results.txt"; then
    echo; echo "FAILURES — see $HERE/last-run.log"; exit 1
fi
echo; echo "all passed"
