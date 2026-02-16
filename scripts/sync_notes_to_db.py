#!/usr/bin/env python3
"""
sync_notes_to_db.py - Sync Apple Notes → Uintas database using SQLite reader.

Replaces sync_notes_to_db_jxa.js with a hybrid approach:
  - READS notes via SQLite (NoteStore.sqlite protobuf parsing) for full fidelity
  - WRITES *update tag removal via JXA (still needed — can't write to NoteStore)
  - Updates the Uintas SQLite database directly via Python sqlite3

Requires:
  - Full Disk Access for the terminal (for NoteStore.sqlite reading)
  - Automation permission for Notes.app (for *update tag removal)

Usage:
    python3 scripts/sync_notes_to_db.py              # Normal sync
    python3 scripts/sync_notes_to_db.py --dry-run     # Preview without changes
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notes_sqlite_reader import read_uintas_notes_with_update_tag

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
LOG_PATH = os.path.join(PROJECT_DIR, "logs", "notes_sync.log")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(message):
    """Log to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a') as f:
            f.write(entry + '\n')
    except Exception as e:
        print(f"  (log write failed: {e})")


# ---------------------------------------------------------------------------
# JXA: Remove *update tag from a note
# ---------------------------------------------------------------------------

def remove_update_tag_via_jxa(note_title, letter_number):
    """
    Remove '*update' from a note's body via JXA.
    This is the only operation that still requires JXA — we can't write to
    NoteStore.sqlite directly.
    """
    escaped_ln = letter_number.replace("'", "\\'")
    jxa = f"""
    const Notes = Application('Notes');
    const found = Notes.notes.whose({{name: {{_contains: '{escaped_ln}'}}}})();
    let updated = 0;
    for (const note of found) {{
        const body = note.body();
        if (body.includes('*update')) {{
            note.body = body.replace(/\\*update/g, '');
            updated++;
        }}
    }}
    updated;
    """
    try:
        result = subprocess.run(
            ['osascript', '-l', 'JavaScript', '-e', jxa],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True
        else:
            log(f"  JXA error removing *update: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        log(f"  JXA timeout removing *update tag from {note_title}")
        return False
    except Exception as e:
        log(f"  JXA exception: {e}")
        return False


# ---------------------------------------------------------------------------
# Database update
# ---------------------------------------------------------------------------

def update_lake_in_db(conn, letter_number, status, jed_notes, trip_reports):
    """Update the Uintas database with parsed note content."""
    fields = []
    values = []

    if status is not None:
        fields.append('status = ?')
        values.append(status)

    if jed_notes is not None:
        fields.append('jed_notes = ?')
        values.append(jed_notes)

    if trip_reports is not None:
        fields.append('trip_reports = ?')
        values.append(trip_reports)

    if not fields:
        return False

    values.append(letter_number)
    query = f"UPDATE lakes SET {', '.join(fields)} WHERE letter_number = ?"

    cursor = conn.execute(query, values)
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def sync(dry_run=False):
    log("=" * 60)
    log("Starting Notes → Database sync (SQLite reader)")
    log("=" * 60)

    # Step 1: Read notes via SQLite
    log("Step 1: Reading Uintas notes with *update tag from NoteStore.sqlite...")
    try:
        notes = read_uintas_notes_with_update_tag()
    except PermissionError as e:
        log(f"PERMISSION ERROR: {e}")
        log("Falling back to JXA-based sync...")
        log("Run: osascript scripts/sync_notes_to_db_jxa.js")
        return 1

    if not notes:
        log("No notes found with *update tag. Nothing to sync.")
        return 0

    log(f"Found {len(notes)} note(s) to sync.")

    # Step 2: Update database
    if dry_run:
        log("DRY RUN — showing what would be synced:")
        for note in notes:
            log(f"  {note['letter_number']} ({note['title']})")
            log(f"    Status: {note['status'] or '(unchanged)'}")
            log(f"    Jed's Notes: {(note['jed_notes'] or '(unchanged)')[:80]}")
            log(f"    Trip Reports: {(note['trip_reports'] or '(unchanged)')[:80]}")
        return 0

    if not os.path.exists(DB_PATH):
        log(f"ERROR: Database not found at {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    success_count = 0
    error_count = 0

    for note in notes:
        ln = note['letter_number']
        log(f"Processing: {ln} ({note['title']})")

        # Log parsed data
        log(f"  Status: {note['status'] or '(not set)'}")
        if note['jed_notes']:
            log(f"  Jed's Notes: {note['jed_notes'][:80]}...")
        if note['trip_reports']:
            log(f"  Trip Reports: {note['trip_reports'][:80]}...")

        # Update database
        try:
            updated = update_lake_in_db(
                conn, ln, note['status'], note['jed_notes'], note['trip_reports']
            )
            if updated:
                log(f"  ✓ Database updated for {ln}")
            else:
                log(f"  ⚠ No matching lake found for {ln} (or no fields to update)")
                error_count += 1
                continue
        except Exception as e:
            log(f"  ✗ Database error for {ln}: {e}")
            error_count += 1
            continue

        # Remove *update tag via JXA
        log(f"  Removing *update tag from note...")
        if remove_update_tag_via_jxa(note['title'], ln):
            log(f"  ✓ *update tag removed")
            success_count += 1
        else:
            log(f"  ⚠ Could not remove *update tag (note will be re-processed next run)")
            success_count += 1  # DB was still updated successfully

    conn.commit()
    conn.close()

    log(f"Sync complete: {success_count} successful, {error_count} errors")
    return 0 if error_count == 0 else 1


def main():
    dry_run = '--dry-run' in sys.argv
    sys.exit(sync(dry_run=dry_run))


if __name__ == '__main__':
    main()
