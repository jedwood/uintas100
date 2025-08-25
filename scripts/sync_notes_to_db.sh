#!/bin/bash

# Wrapper script to sync Apple Notes back to database
# Looks for notes containing *update tag and syncs content to database
# Usage: ./sync_notes_to_db.sh

echo "Starting Apple Notes → Database sync (looking for *update tags)..."
result=$(osascript "$(dirname "$0")/sync_notes_to_db_jxa.js")
echo "$result"

# Check if log file exists and show recent entries
log_file="$(dirname "$0")/../logs/notes_sync.log"
if [[ -f "$log_file" ]]; then
    echo ""
    echo "Recent log entries:"
    tail -10 "$log_file"
fi