#!/bin/bash
#
# Mini-only: sync Apple Notes -> DB, then PERSIST any DB change to git.
#
# sync_notes_to_db.sh writes the database but never commits, so on the
# single-writer Mini those edits would be discarded by the next clean-tree pull.
# This wrapper commits + pushes them so the Notes->DB direction is durable.
#
# Intentionally does NOT run DB->Notes: the current sync_db_to_notes_jxa.js
# rebuilds the whole note body and wipes anything above the ═══ delimiter
# (un-captured trip reports / status) — a known data-loss bug. Run that by hand
# only, until a wipe-safe version exists.
#
# The pre-commit hook (git config core.hooksPath .githooks) regenerates
# data/seeds/ and lakes_data.json from the DB on commit, so we never do that here.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO"

# Single-writer guard: a read-only mirror must never commit/push.
if [ -f "$REPO/.db-readonly" ]; then
    echo "[writer-guard] .db-readonly present — read-only mirror; skipping Notes sync + commit."
    exit 0
fi

# 1. Apple Notes -> DB (this script self-guards and may write uinta_lakes.db)
"$SCRIPT_DIR/sync_notes_to_db.sh" "$@"

# 2. Persist to git only if the sync actually changed the DB.
#    (git diff --quiet exits non-zero when there IS a change; the `if` consumes
#    that exit code so `set -e` does not abort here.)
if git diff --quiet -- uinta_lakes.db; then
    echo "No DB changes from Notes sync; nothing to commit."
    exit 0
fi

echo "Notes sync changed the DB — committing and pushing..."
# Stage only the DB; the pre-commit hook adds data/seeds/ + lakes_data.json.
# (The stocking CSV is owned by the fetch path, not Notes sync, so it is not
# touched here.)
git add uinta_lakes.db
git commit -m "Notes sync: apply Apple Notes edits to DB"
git push
echo "Pushed Notes-driven DB changes."
