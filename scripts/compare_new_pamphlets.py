#!/usr/bin/env python3
"""
Compare new DWR pamphlet text with existing database entries.
Parses the pdftotext output from the 2025 revised pamphlets and compares
against the current dwr_notes in the database.

Usage:
    python3 scripts/compare_new_pamphlets.py          # Dry run - show what would change
    python3 scripts/compare_new_pamphlets.py apply     # Apply updates to the database
"""

import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
NEW_PAMPHLETS_DIR = os.path.join(PROJECT_DIR, "data", "dwr_new_pamphlets")

# Map text file -> drainage prefix patterns for validation
PAMPHLET_FILES = {
    "bear-river-text.txt": ["BR-"],
    "blacks-fork-text.txt": ["G-"],
    "whiterocks-text.txt": ["WR-"],
}


def is_table_data(body):
    """Detect if body text is summary table data rather than a real lake description.

    Table rows in the PDFs have patterns like:
        Stillwater Fork – Middle Basin
        Christmas Meadows TH to Middle Basin
        8.3  10,610  1.3  5  Y  N  limited  Brook
    Real descriptions start with full sentences about the lake.
    """
    # Collapse to single string for pattern matching
    flat = ' '.join(body.split())

    # Table data contains Y/N flag sequences (access/campsite/horse flags)
    yn_flags = len(re.findall(r'\b[YN]\b', flat[:300]))
    if yn_flags >= 3:
        return True

    # Table data starts with drainage sub-location names followed by tabular fragments
    drainage_starts = [
        'Hayden Fork', 'Stillwater Fork', 'East Fork', 'West Fork',
        'Middle Fork', 'Little East Fork', 'Boundary Creek',
        'Mill Creek', 'Main Basin',
    ]
    first_line = body.split('\n')[0].strip()
    if any(first_line.startswith(d) for d in drainage_starts):
        return True

    # Table data has lots of very short lines (numbers, single words)
    lines = [l.strip() for l in body.split('\n') if l.strip()][:10]
    short_lines = sum(1 for l in lines if len(l) < 15)
    if len(lines) >= 4 and short_lines / len(lines) > 0.6:
        return True

    return False


def parse_lake_entries(text):
    """Parse pdftotext output into individual lake entries.

    Entries look like:
        Lake Name, BR-42
        Description paragraph...

    Or for unnamed lakes:
        BR-4
        This lake does not sustain fish life.
    """
    raw_entries = []

    # Strip form feed characters (page breaks from pdftotext)
    text = text.replace('\x0c', '\n')

    # Remove spaced-out page headers like "B E A R R I V E R D R A I N A G E" or similar
    text = re.sub(r'\n[A-Z](?: [A-Z]){5,}[A-Z \d\|]*\n', '\n', text)

    # Remove normal page headers like "BLACKS FORK DRAINAGE | 9"
    text = re.sub(r'\n[A-Z][A-Z ]+ DRAINAGE \| \d+\n', '\n', text)

    # Match lake description headers in multiple formats:
    # Format 1: "Lake Name, BR-42" or just "BR-42" (most common)
    # Note: use [ ] (space only) instead of \s in name group to prevent matching across lines
    header_pattern1 = re.compile(
        r'^(?:([A-Z][A-Za-z \'\-\(\)\.]+?),?[ ]+)?'   # Optional name with comma (single line)
        r'([A-Z]{1,3}-\d+[A-Za-z]?)[ ]*$',             # Designation like BR-42, G-15, WR-74
        re.MULTILINE
    )
    # Format 2: "G-105 (Wagonwheel Lake)" - designation then name in parens
    header_pattern2 = re.compile(
        r'^([A-Z]{1,3}-\d+[A-Za-z]?)\s+\(([A-Z][A-Za-z\s\'\-\.]+)\)\s*$',
        re.MULTILINE
    )

    # Merge and sort all header matches by position
    headers = []
    for m in header_pattern1.finditer(text):
        name_val = (m.group(1) or "").strip().rstrip(",").strip()
        headers.append((m.start(), m.end(), m.group(2).strip(), name_val, m))
    for m in header_pattern2.finditer(text):
        headers.append((m.start(), m.end(), m.group(1).strip(), m.group(2).strip(), m))
    headers.sort(key=lambda x: x[0])

    for i, (h_start, h_end, designation, name, match) in enumerate(headers):

        # Skip table entries: in the summary tables, designations appear in parens like "(BR-26)"
        # Check if this designation appears in parentheses in the surrounding text
        ctx_start = max(0, h_start - 30)
        context_before = text[ctx_start:h_start]
        if f'({designation})' in context_before or f'({designation})' in text[ctx_start:h_end + 5]:
            continue

        # Extract text between this header and the next (or end of file)
        start = h_end
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        body = text[start:end].strip()

        # Clean up any remaining page headers in body
        body = re.sub(r'\n[A-Z][A-Z ]+ DRAINAGE \| \d+\n', '\n', body)
        # Collapse multiple newlines
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = body.strip()

        if not body:
            continue

        # Skip table row data
        if is_table_data(body):
            continue

        raw_entries.append({
            "designation": designation,
            "name": name,
            "text": body,
        })

    # Deduplicate: if same designation appears multiple times, keep the entry
    # with the longest description (real narratives are always longer than table scraps)
    seen = {}
    for entry in raw_entries:
        d = entry["designation"]
        if d not in seen or len(entry["text"]) > len(seen[d]["text"]):
            seen[d] = entry

    return list(seen.values())


def extract_lake_data_from_text(text):
    """Extract size, depth, elevation from DWR description text."""
    text_clean = ' '.join(text.split())

    # Size in acres - look for "X.X surface acres" or "X.X acres"
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:surface\s+)?acres?', text_clean, re.IGNORECASE)
    size_acres = float(size_match.group(1)) if size_match else None

    # Elevation
    elevation_ft = None
    elev_match = re.search(r'(\d+(?:,\d+)?)\s*feet?\s*(?:in\s*)?elevation', text_clean, re.IGNORECASE)
    if not elev_match:
        elev_match = re.search(r'elevation\s+(\d+(?:,\d+)?)\s*feet?', text_clean, re.IGNORECASE)
    if elev_match:
        elevation_ft = int(elev_match.group(1).replace(',', ''))

    # Max depth
    depth_match = re.search(r'(\d+)\s*feet?\s*maximum\s*depth', text_clean, re.IGNORECASE)
    max_depth_ft = int(depth_match.group(1)) if depth_match else None

    # No fish
    no_fish = 'does not sustain fish' in text_clean.lower() or 'not capable of sustaining' in text_clean.lower()

    return {
        'size_acres': size_acres,
        'elevation_ft': elevation_ft,
        'max_depth_ft': max_depth_ft,
        'no_fish': no_fish,
    }


def normalize_text(text):
    """Normalize text for comparison - collapse whitespace, lowercase."""
    return ' '.join(text.lower().split())


def compare_entries(new_entries, conn):
    """Compare new pamphlet entries against database and report differences."""
    cursor = conn.cursor()

    results = {
        "updated_notes": [],      # Entries with changed descriptions
        "new_notes": [],          # Entries for lakes with no existing dwr_notes
        "unchanged": [],          # Entries that match existing notes
        "not_in_db": [],          # Designations not found in database
        "data_updates": [],       # Lakes where size/depth/elevation differs
    }

    for entry in new_entries:
        designation = entry["designation"]
        new_text = entry["text"]

        cursor.execute('''
            SELECT id, name, dwr_notes, size_acres, max_depth_ft, elevation_ft, no_fish, notes_needs_update
            FROM lakes WHERE letter_number = ?
        ''', (designation,))
        row = cursor.fetchone()

        if not row:
            results["not_in_db"].append(entry)
            continue

        lake_id, db_name, db_notes, db_size, db_depth, db_elev, db_no_fish, _ = row

        # Extract data from new text
        extracted = extract_lake_data_from_text(new_text)

        # Check for data value changes
        data_diffs = []
        if extracted['size_acres'] and db_size and abs(extracted['size_acres'] - db_size) > 0.05:
            data_diffs.append(f"size: {db_size} -> {extracted['size_acres']}")
        if extracted['elevation_ft'] and db_elev and extracted['elevation_ft'] != db_elev:
            data_diffs.append(f"elevation: {db_elev} -> {extracted['elevation_ft']}")
        if extracted['max_depth_ft'] and db_depth and extracted['max_depth_ft'] != db_depth:
            data_diffs.append(f"depth: {db_depth} -> {extracted['max_depth_ft']}")

        if data_diffs:
            results["data_updates"].append({
                **entry,
                "extracted": extracted,
                "diffs": data_diffs,
                "db_name": db_name,
            })

        if not db_notes or db_notes.strip() == '':
            results["new_notes"].append({**entry, "extracted": extracted, "db_name": db_name})
        else:
            # Compare normalized text (ignore minor whitespace/formatting diffs)
            # Strip any rotenone warnings we added before comparing
            clean_db_notes = re.sub(r'^⚠️ ROTENONE.*?\n\n', '', db_notes, flags=re.DOTALL).strip()
            if normalize_text(new_text) == normalize_text(clean_db_notes):
                results["unchanged"].append(entry)
            else:
                results["updated_notes"].append({
                    **entry,
                    "extracted": extracted,
                    "db_name": db_name,
                    "old_notes": clean_db_notes,
                })

    return results


def print_report(results):
    """Print a human-readable comparison report."""
    print("=" * 70)
    print("DWR PAMPHLET COMPARISON REPORT (2025 Revised vs. Current DB)")
    print("=" * 70)

    print(f"\n  Unchanged:        {len(results['unchanged'])}")
    print(f"  Updated text:     {len(results['updated_notes'])}")
    print(f"  New (no notes):   {len(results['new_notes'])}")
    print(f"  Data value diffs: {len(results['data_updates'])}")
    print(f"  Not in DB:        {len(results['not_in_db'])}")

    if results["new_notes"]:
        print(f"\n{'='*70}")
        print("LAKES WITH NO EXISTING DWR NOTES (will add):")
        print("=" * 70)
        for e in results["new_notes"]:
            print(f"\n  {e['designation']} ({e.get('db_name', e['name'])})")
            print(f"    {e['text'][:120]}...")

    if results["updated_notes"]:
        print(f"\n{'='*70}")
        print("LAKES WITH CHANGED DESCRIPTIONS:")
        print("=" * 70)
        for e in results["updated_notes"]:
            print(f"\n  {e['designation']} ({e.get('db_name', e['name'])})")
            old_preview = e['old_notes'][:100].replace('\n', ' ')
            new_preview = e['text'][:100].replace('\n', ' ')
            print(f"    OLD: {old_preview}...")
            print(f"    NEW: {new_preview}...")

    if results["data_updates"]:
        print(f"\n{'='*70}")
        print("LAKES WITH NUMERIC DATA CHANGES:")
        print("=" * 70)
        for e in results["data_updates"]:
            print(f"  {e['designation']} ({e.get('db_name', e['name'])}): {', '.join(e['diffs'])}")

    if results["not_in_db"]:
        print(f"\n{'='*70}")
        print("DESIGNATIONS NOT FOUND IN DATABASE:")
        print("=" * 70)
        for e in results["not_in_db"]:
            print(f"  {e['designation']} ({e['name']})")


def apply_updates(results, conn):
    """Apply the new/updated entries to the database."""
    cursor = conn.cursor()
    count = 0

    # Add notes for lakes that had none
    for entry in results["new_notes"]:
        extracted = entry["extracted"]
        designation = entry["designation"]

        updates = ["dwr_notes = ?", "notes_needs_update = TRUE"]
        values = [entry["text"]]

        if extracted["no_fish"]:
            updates.append("no_fish = 1")

        sql = f"UPDATE lakes SET {', '.join(updates)} WHERE letter_number = ?"
        values.append(designation)
        cursor.execute(sql, values)
        count += 1
        print(f"  Added notes for {designation}")

    # Update existing notes with new text
    for entry in results["updated_notes"]:
        designation = entry["designation"]
        new_text = entry["text"]

        # Preserve any rotenone warnings we've added
        cursor.execute("SELECT dwr_notes FROM lakes WHERE letter_number = ?", (designation,))
        row = cursor.fetchone()
        if row and row[0]:
            rotenone_match = re.match(r'(⚠️ ROTENONE.*?\n\n)', row[0], re.DOTALL)
            if rotenone_match:
                new_text = rotenone_match.group(1) + new_text

        cursor.execute(
            "UPDATE lakes SET dwr_notes = ?, notes_needs_update = TRUE WHERE letter_number = ?",
            (new_text, designation)
        )
        count += 1
        print(f"  Updated notes for {designation}")

    # Update numeric data where the new pamphlet has better info
    for entry in results["data_updates"]:
        designation = entry["designation"]
        extracted = entry["extracted"]

        updates = []
        values = []
        if extracted["size_acres"]:
            updates.append("size_acres = ?")
            values.append(extracted["size_acres"])
        if extracted["elevation_ft"]:
            updates.append("elevation_ft = ?")
            values.append(extracted["elevation_ft"])
        if extracted["max_depth_ft"]:
            updates.append("max_depth_ft = ?")
            values.append(extracted["max_depth_ft"])

        if updates:
            updates.append("notes_needs_update = TRUE")
            sql = f"UPDATE lakes SET {', '.join(updates)} WHERE letter_number = ?"
            values.append(designation)
            cursor.execute(sql, values)
            print(f"  Updated data for {designation}: {', '.join(entry['diffs'])}")

    conn.commit()
    print(f"\nApplied {count} note updates + {len(results['data_updates'])} data updates")


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"

    conn = sqlite3.connect(DB_PATH)
    all_entries = []

    for filename, prefixes in PAMPHLET_FILES.items():
        filepath = os.path.join(NEW_PAMPHLETS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping")
            continue

        with open(filepath, 'r') as f:
            text = f.read()

        entries = parse_lake_entries(text)
        # Validate that entries have expected prefixes
        valid_entries = []
        for e in entries:
            if any(e["designation"].startswith(p) for p in prefixes):
                valid_entries.append(e)

        print(f"Parsed {len(valid_entries)} lake entries from {filename}")
        all_entries.extend(valid_entries)

    print(f"\nTotal new entries: {len(all_entries)}")

    results = compare_entries(all_entries, conn)
    print_report(results)

    if apply:
        print(f"\n{'='*70}")
        print("APPLYING UPDATES...")
        print("=" * 70)
        apply_updates(results, conn)
    else:
        total_changes = len(results["new_notes"]) + len(results["updated_notes"]) + len(results["data_updates"])
        if total_changes > 0:
            print(f"\n*** DRY RUN - {total_changes} changes found. Run with 'apply' to update the database ***")

    conn.close()


if __name__ == "__main__":
    main()
