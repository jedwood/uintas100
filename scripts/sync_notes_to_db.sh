#!/bin/bash

# Wrapper script to sync Apple Notes back to database
# Uses SQLite reader (primary) with JXA fallback
# Usage: ./sync_notes_to_db.sh

SCRIPT_DIR="$(dirname "$0")"

echo "Starting Apple Notes → Database sync..."

# Try the new SQLite-based reader first (requires Full Disk Access)
if python3 "$SCRIPT_DIR/sync_notes_to_db.py" "$@"; then
    exit 0
fi

# If Python script fails (e.g., no Full Disk Access), fall back to pure JXA
echo ""
echo "SQLite reader failed, falling back to JXA-based sync..."
result=$(osascript "$SCRIPT_DIR/sync_notes_to_db_jxa.js")
echo "$result"

# Show recent log entries
log_file="$SCRIPT_DIR/../logs/notes_sync.log"
if [[ -f "$log_file" ]]; then
    echo ""
    echo "Recent log entries:"
    tail -10 "$log_file"
fi
