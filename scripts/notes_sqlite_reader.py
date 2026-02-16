#!/usr/bin/env python3
"""
notes_sqlite_reader.py - Read Apple Notes from NoteStore.sqlite for Uintas sync.

Replaces the JXA-based note reading in sync_notes_to_db_jxa.js with a direct
SQLite + protobuf approach that provides:
  - Full fidelity: links, formatting, checklists preserved perfectly
  - No dependency on Notes.app running
  - Faster reads (no Apple Events overhead)
  - Cleaner text extraction (no HTML parsing gymnastics)

Requires: Full Disk Access for the terminal running this script.
Zero external dependencies — uses only Python stdlib.

Usage:
    # As a module (imported by sync_notes_to_db.py):
    from notes_sqlite_reader import read_uintas_notes_with_update_tag

    # As a standalone script (dry run - shows what would sync):
    python3 scripts/notes_sqlite_reader.py
"""

import gzip
import os
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NOTESTORE_PATH = os.path.expanduser(
    "~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
)

UINTAS_FOLDER_NAME = "Uintas 💯"


# ---------------------------------------------------------------------------
# Protobuf decoder (zero dependencies)
# ---------------------------------------------------------------------------

def decode_varint(data, pos):
    """Decode a protobuf varint starting at pos. Returns (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if byte < 0x80:
            return result, pos
        shift += 7
    return result, pos


def decode_protobuf(data):
    """Decode a protobuf message into {field_number: [values]}."""
    pos = 0
    fields = {}
    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
        except (IndexError, ValueError):
            break
        field_number = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:  # Varint
            value, pos = decode_varint(data, pos)
        elif wire_type == 1:  # 64-bit fixed
            if pos + 8 > len(data):
                break
            value = struct.unpack_from('<d', data, pos)[0]
            pos += 8
        elif wire_type == 2:  # Length-delimited
            length, pos = decode_varint(data, pos)
            if pos + length > len(data):
                break
            value = data[pos:pos + length]
            pos += length
        elif wire_type == 5:  # 32-bit fixed
            if pos + 4 > len(data):
                break
            value = struct.unpack_from('<f', data, pos)[0]
            pos += 4
        else:
            break

        fields.setdefault(field_number, []).append(value)
    return fields


def decode_signed_varint(value):
    """Convert unsigned varint to signed int."""
    if value > 0x7FFFFFFFFFFFFFFF:
        value -= 0x10000000000000000
    return value


# ---------------------------------------------------------------------------
# Apple Notes protobuf parsing
# ---------------------------------------------------------------------------

def parse_note_protobuf(zdata):
    """
    Parse a ZDATA blob from NoteStore.sqlite.

    Returns dict with:
        text: str - full plain text of the note
        paragraphs: list of dicts, each with:
            text: str
            style: str ('body', 'title', 'heading', 'checkbox', etc.)
            checklist_done: bool (only for checkbox style)
        links: list of dicts with 'display' and 'url'
    """
    try:
        decompressed = gzip.decompress(zdata)
    except Exception:
        decompressed = zdata

    top = decode_protobuf(decompressed)
    if 2 not in top:
        return None

    doc = decode_protobuf(top[2][0])
    if 3 not in doc:
        return None

    note = decode_protobuf(doc[3][0])

    # Extract text
    text = ""
    if 2 in note:
        try:
            text = note[2][0].decode('utf-8', errors='replace')
        except Exception:
            text = str(note[2][0])

    # Decode attribute runs
    raw_runs = []
    text_pos = 0
    if 5 in note:
        for attr_raw in note[5]:
            attr = decode_protobuf(attr_raw)
            run = {}

            length = attr[1][0] if 1 in attr else 0
            run['length'] = length
            run['start'] = text_pos
            run['text'] = text[text_pos:text_pos + length]

            # Link URL (field 9)
            if 9 in attr:
                try:
                    run['link'] = attr[9][0].decode('utf-8', errors='replace')
                except Exception:
                    pass

            # ParagraphStyle (field 2)
            if 2 in attr:
                para = decode_protobuf(attr[2][0])
                if 1 in para:
                    run['style_type'] = decode_signed_varint(para[1][0])
                if 5 in para:
                    checklist_msg = decode_protobuf(para[5][0])
                    run['checklist_done'] = bool(checklist_msg.get(2, [0])[0]) if 2 in checklist_msg else False

            raw_runs.append(run)
            text_pos += length

    # Build character-level indices
    char_run_index = []
    for idx, run in enumerate(raw_runs):
        char_run_index.extend([idx] * run['length'])

    char_link = [None] * len(text)
    for run in raw_runs:
        if 'link' in run:
            for i in range(run['start'], min(run['start'] + run['length'], len(text))):
                char_link[i] = run['link']

    # Walk paragraphs
    paragraphs = []
    links = []
    para_start = 0

    for i, ch in enumerate(text):
        if ch == '\n':
            para_text = text[para_start:i]

            # Get style from the run covering the \n
            style_type = -1
            checklist_done = False
            if i < len(char_run_index):
                covering = raw_runs[char_run_index[i]]
                style_type = covering.get('style_type', -1)
                checklist_done = covering.get('checklist_done', False)

            style_names = {
                -1: 'body', 0: 'title', 1: 'heading', 2: 'subheading',
                4: 'monospaced', 100: 'dotted_list', 101: 'dashed_list',
                102: 'numbered_list', 103: 'checkbox',
            }

            paragraphs.append({
                'text': para_text,
                'style': style_names.get(style_type, f'style_{style_type}'),
                'checklist_done': checklist_done,
            })

            # Collect links in this paragraph
            seen_urls = set()
            pos = para_start
            while pos < i:
                url = char_link[pos] if pos < len(char_link) else None
                if url and url not in seen_urls:
                    link_end = pos
                    while link_end < i and link_end < len(char_link) and char_link[link_end] == url:
                        link_end += 1
                    display = text[pos:link_end].strip()
                    if display:
                        links.append({'display': display, 'url': url})
                        seen_urls.add(url)
                    pos = link_end
                else:
                    pos += 1

            para_start = i + 1

    # Handle final paragraph without trailing \n
    if para_start < len(text):
        paragraphs.append({
            'text': text[para_start:],
            'style': 'body',
            'checklist_done': False,
        })

    return {
        'text': text,
        'paragraphs': paragraphs,
        'links': links,
    }


# ---------------------------------------------------------------------------
# Uintas-specific: extract status, notes, trip reports from note content
# ---------------------------------------------------------------------------

def extract_lake_identifier(note_title):
    """Extract letter-number designation (A-42, BR-25, etc.) from note title."""
    if not note_title:
        return None

    # Try parentheses format: "Lake Name (A-42) 🎣"
    match = re.search(r'\(([A-Z]+-?\d+)\)', note_title)
    if match:
        return match.group(1)

    # Try standalone: "A-42" or "A-42 🎣"
    match = re.match(r'^([A-Z]+-?\d+)(?:\s|$)', note_title)
    if match:
        return match.group(1)

    # Try word boundary anywhere
    match = re.search(r'\b([A-Z]+-?\d+)\b', note_title)
    if match:
        return match.group(1)

    return None


def parse_uintas_note(parsed):
    """
    Extract status, Jed's Notes, and Trip Reports from a parsed Uintas lake note.

    The note structure uses a visual delimiter (═════) to separate user-editable
    content (above) from auto-generated data (below). We only care about content
    above the delimiter.

    Returns dict with: status, jed_notes, trip_reports (any may be None).
    """
    if not parsed or not parsed.get('paragraphs'):
        return {'status': None, 'jed_notes': None, 'trip_reports': None}

    paragraphs = parsed['paragraphs']

    # Find the delimiter paragraph
    delimiter_idx = None
    for idx, para in enumerate(paragraphs):
        if re.match(r'═{5,}', para['text']):
            delimiter_idx = idx
            break

    # Only look at paragraphs above the delimiter
    if delimiter_idx is not None:
        paragraphs = paragraphs[:delimiter_idx]

    # Find section boundaries by looking for headings/titles
    section_starts = {}
    for idx, para in enumerate(paragraphs):
        text_lower = para['text'].strip().lower()
        if "status" in text_lower and ":" in para['text']:
            section_starts['status_line'] = idx
        elif "jed" in text_lower and "note" in text_lower:
            section_starts['jed_notes'] = idx
        elif "trip" in text_lower and "report" in text_lower:
            section_starts['trip_reports'] = idx

    # Extract status
    status = None
    if 'status_line' in section_starts:
        status_para = paragraphs[section_starts['status_line']]
        status_match = re.search(r'Status:\s*(\w+)', status_para['text'], re.IGNORECASE)
        if status_match:
            val = status_match.group(1).upper()
            if val in ('CAUGHT', 'NONE', 'OTHERS'):
                status = val

    # Extract Jed's Notes - content between "Jed's Notes" header and next section/delimiter
    jed_notes = None
    if 'jed_notes' in section_starts:
        start = section_starts['jed_notes'] + 1  # Skip the header itself
        # Find end: next section header or end of above-delimiter content
        end = len(paragraphs)
        for section_name, section_idx in section_starts.items():
            if section_idx > section_starts['jed_notes'] and section_idx < end:
                end = section_idx

        content_parts = []
        for para in paragraphs[start:end]:
            t = para['text'].strip()
            if t and t != "Add your notes here...":
                content_parts.append(t)

        if content_parts:
            jed_notes = '\n'.join(content_parts)

    # Extract Trip Reports
    trip_reports = None
    if 'trip_reports' in section_starts:
        start = section_starts['trip_reports'] + 1
        end = len(paragraphs)
        for section_name, section_idx in section_starts.items():
            if section_idx > section_starts['trip_reports'] and section_idx < end:
                end = section_idx

        content_parts = []
        for para in paragraphs[start:end]:
            t = para['text'].strip()
            if t and t != "Add trip reports here...":
                content_parts.append(t)

        if content_parts:
            trip_reports = '\n'.join(content_parts)

    return {
        'status': status,
        'jed_notes': jed_notes,
        'trip_reports': trip_reports,
    }


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def open_notestore(notestore_path=None):
    """
    Open NoteStore.sqlite safely. Copies to temp dir first for consistency.
    Returns (connection, temp_dir_path) — caller must clean up temp dir.
    """
    src_path = notestore_path or NOTESTORE_PATH
    src_dir = os.path.dirname(src_path)
    db_name = os.path.basename(src_path)

    tmpdir = tempfile.mkdtemp(prefix='apple_notes_')
    files = [db_name, f'{db_name}-wal', f'{db_name}-shm']

    try:
        for fname in files:
            src = os.path.join(src_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(tmpdir, fname))
    except PermissionError:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise PermissionError(
            "Cannot read NoteStore.sqlite. Grant Full Disk Access to your terminal "
            "in System Settings > Privacy & Security > Full Disk Access."
        )

    db_path = os.path.join(tmpdir, db_name)
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn, tmpdir


def find_uintas_notes_with_update_tag(conn):
    """
    Find all notes in the Uintas folder structure that contain '*update' in their text.
    Returns list of dicts with note metadata and parsed content.
    """
    # Find notes whose text contains '*update' within Uintas folders
    query = """
    SELECT
        n.Z_PK as pk,
        c1.ZTITLE1 as title,
        c2.ZTITLE2 as folder_name,
        c3.ZTITLE2 as parent_folder_name,
        n.ZDATA as data,
        datetime(c1.ZMODIFICATIONDATE1 + 978307200, 'unixepoch') as modified
    FROM ZICNOTEDATA as n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT as c1 ON c1.ZNOTEDATA = n.Z_PK
    LEFT JOIN ZICCLOUDSYNCINGOBJECT as c2 ON c2.Z_PK = c1.ZFOLDER
    LEFT JOIN ZICCLOUDSYNCINGOBJECT as c3 ON c3.Z_PK = c2.ZPARENT
    WHERE n.ZDATA IS NOT NULL
        AND n.ZCRYPTOTAG IS NULL
        AND (c2.ZTITLE2 = ? OR c3.ZTITLE2 = ?)
    ORDER BY c1.ZMODIFICATIONDATE1 DESC
    """

    results = []
    for row in conn.execute(query, (UINTAS_FOLDER_NAME, UINTAS_FOLDER_NAME)):
        data = row['data']
        if not data:
            continue

        parsed = parse_note_protobuf(data)
        if not parsed:
            continue

        # Check if note text contains *update
        if '*update' not in parsed['text']:
            continue

        letter_number = extract_lake_identifier(row['title'])
        if not letter_number:
            continue

        # Extract Uintas-specific fields
        uintas_data = parse_uintas_note(parsed)

        results.append({
            'pk': row['pk'],
            'title': row['title'],
            'folder': row['folder_name'],
            'letter_number': letter_number,
            'modified': row['modified'],
            'status': uintas_data['status'],
            'jed_notes': uintas_data['jed_notes'],
            'trip_reports': uintas_data['trip_reports'],
            'full_text': parsed['text'],
            'links': parsed['links'],
        })

    return results


def read_uintas_notes_with_update_tag(notestore_path=None):
    """
    High-level API: Find and parse all Uintas notes tagged with *update.

    Returns list of dicts ready for database update:
        letter_number, status, jed_notes, trip_reports, title, folder, modified

    Raises PermissionError if Full Disk Access is not granted.
    """
    conn, tmpdir = open_notestore(notestore_path)
    try:
        return find_uintas_notes_with_update_tag(conn)
    finally:
        conn.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Standalone: dry run showing what would be synced
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Apple Notes SQLite Reader - Uintas Sync Preview")
    print("=" * 70)
    print()

    try:
        notes = read_uintas_notes_with_update_tag()
    except PermissionError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not notes:
        print("No notes found with *update tag in Uintas folders.")
        print("(This is normal if no notes are pending sync.)")
        return

    print(f"Found {len(notes)} note(s) with *update tag:\n")

    for note in notes:
        print(f"  Lake: {note['letter_number']}")
        print(f"  Title: {note['title']}")
        print(f"  Folder: {note['folder']}")
        print(f"  Modified: {note['modified']}")
        print(f"  Status: {note['status'] or '(not set)'}")
        if note['jed_notes']:
            preview = note['jed_notes'][:100]
            if len(note['jed_notes']) > 100:
                preview += '...'
            print(f"  Jed's Notes: {preview}")
        else:
            print(f"  Jed's Notes: (empty)")
        if note['trip_reports']:
            preview = note['trip_reports'][:100]
            if len(note['trip_reports']) > 100:
                preview += '...'
            print(f"  Trip Reports: {preview}")
        else:
            print(f"  Trip Reports: (empty)")
        if note['links']:
            print(f"  Links: {len(note['links'])}")
            for lnk in note['links'][:3]:
                print(f"    {lnk['display']} -> {lnk['url']}")
        print()

    print("(Dry run — no database changes made.)")
    print("To actually sync, run: python3 scripts/sync_notes_to_db.py")


if __name__ == '__main__':
    main()
