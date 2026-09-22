#!/bin/bash
# Proves scripts/auto_commit.py + the pre-commit hook never sweep a dev's
# in-progress work (staged or unstaged) into an unattended commit — and that a
# dev's own commit still ships what they deliberately staged. Runs against a
# shallow throwaway clone of THIS checkout (uses the working-tree versions of
# the hook, the helper and edits_server.py, so it tests uncommitted changes).
#
#   tests/auto_commit_isolation.sh      # from anywhere; needs sqlite3 + python3
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
W=$(mktemp -d "$SRC/../tmp-uintas-ac-XXXX")   # same volume as the repo (hardlink-free clone)
trap 'rm -rf "$W"' EXIT
pass=0; fail=0
ok() { if eval "$2"; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; fail=$((fail+1)); fi; }

git clone -q --no-hardlinks --depth 3 "file://$SRC" "$W/repo"
cd "$W/repo"
git remote remove origin
git config core.hooksPath .githooks
git config user.email t@t; git config user.name t
# Use the working-tree versions of the files under test (uncommitted in SRC).
cp "$SRC/.githooks/pre-commit" .githooks/pre-commit
cp "$SRC/scripts/auto_commit.py" scripts/auto_commit.py
cp "$SRC/scripts/edits_server.py" scripts/edits_server.py
git add .githooks scripts/auto_commit.py scripts/edits_server.py
git commit -q -m "test fixture: isolation hook + helper" >/dev/null
BASE=$(git rev-parse HEAD)

# --- The dev's in-progress state ---------------------------------------
echo "// DEV WORK IN PROGRESS — must not ship" >> service-worker.js      # unstaged
echo "<!-- staged dev edit -->" >> index.html; git add index.html          # staged
echo "unstaged doc edit" >> README.md                                      # unstaged, unrelated

# --- Automation: the edits server applies an edit and commits -----------
sqlite3 uinta_lakes.db "UPDATE lakes SET jed_notes = COALESCE(jed_notes,'') || ' [ac-test]' WHERE letter_number='BR-25';"
echo '{"test":"ac"}' >> data/app_edits_log.jsonl
python3 scripts/auto_commit.py "App edits: test" uinta_lakes.db data/app_edits_log.jsonl >/dev/null

NEW=$(git rev-parse HEAD)
FILES=$(git diff-tree --no-commit-id --name-only -r HEAD | sort | tr '\n' ' ')
ok "a commit was made" '[[ "$NEW" != "$BASE" ]]'
ok "commit contains only owned + derived files (db, log, seeds, lakes_data.json, service-worker.js)" \
   '! (echo "$FILES" | grep -q index.html) && ! (echo "$FILES" | grep -q README) && (echo "$FILES" | grep -q uinta_lakes.db) && (echo "$FILES" | grep -q lakes_data.json) && (echo "$FILES" | grep -q data/seeds/lakes.csv)'
ok "committed worker = HEAD~ worker + version bump only" \
   '[[ $(git diff "$BASE" HEAD -- service-worker.js | grep -c "^[-+]const CACHE_NAME") -eq 2 ]] && [[ $(git diff "$BASE" HEAD -- service-worker.js | grep -c "^[-+][^-+]") -eq 2 ]]'
ok "dev's half-edit to the worker was NOT shipped" '! git show HEAD:service-worker.js | grep -q "DEV WORK IN PROGRESS"'
ok "dev's half-edit is still in the working tree, unstaged" 'grep -q "DEV WORK IN PROGRESS" service-worker.js && git diff --name-only | grep -qx service-worker.js && ! git diff --cached --name-only | grep -qx service-worker.js'
ok "working-tree worker also got the new version line" 'grep -q "$(git show HEAD:service-worker.js | grep "^const CACHE_NAME")" service-worker.js'
ok "dev's staged index.html edit is still staged, not committed" 'git diff --cached --name-only | grep -qx index.html && ! git show HEAD:index.html | grep -q "staged dev edit"'
ok "unrelated unstaged README edit untouched" 'git diff --name-only | grep -qx README.md'
ok "real index matches HEAD for committed paths (no phantom staged changes)" '! git diff --cached --name-only | grep -qE "uinta_lakes.db|lakes_data.json|data/seeds|service-worker.js|app_edits_log"'
ok "no leftover private index files" '! ls /tmp/uintas-auto-index-* >/dev/null 2>&1 && ! ls "${TMPDIR:-/tmp}"/uintas-auto-index-* >/dev/null 2>&1'

# --- Nothing-to-commit path ---------------------------------------------
OUT=$(python3 scripts/auto_commit.py "App edits: none" uinta_lakes.db data/app_edits_log.jsonl)
ok "no-op when owned files are unchanged" '[[ "$OUT" == "nothing to commit" ]] && [[ $(git rev-parse HEAD) == "$NEW" ]]'

# --- A dev commit still ships a deliberately STAGED worker change --------
sleep 1   # the bump is date +%s; two commits in the same second share a version
git add service-worker.js
git commit -q -m "dev: ship worker change" >/dev/null
ok "dev's own commit (worker staged) ships the worker edit + a fresh bump" 'git show HEAD:service-worker.js | grep -q "DEV WORK IN PROGRESS" && [[ $(git show HEAD:service-worker.js | grep "^const CACHE_NAME") != $(git show HEAD~:service-worker.js | grep "^const CACHE_NAME") ]]'
ok "that dev commit also carried the staged index.html (normal git semantics)" 'git show HEAD:index.html | grep -q "staged dev edit"'

echo; echo "passed=$pass failed=$fail   (clone: $W)"
[[ $fail -eq 0 ]]
