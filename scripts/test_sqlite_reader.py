#!/usr/bin/env python3
"""
test_sqlite_reader.py - Read Apple Notes directly from NoteStore.sqlite

Prototype/test script to evaluate the SQLite + protobuf approach for reading
Apple Notes without JXA. Uses zero external dependencies - manual protobuf
parsing with gzip + struct.

Usage:
    python3 scripts/test_sqlite_reader.py
"""

import gzip
import os
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path


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
    """
    Decode a protobuf message into a dict of {field_number: [values]}.
    Length-delimited fields (wire type 2) are returned as raw bytes.
    """
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
        elif wire_type == 2:  # Length-delimited (string, bytes, embedded message)
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
            # Unknown wire type - stop parsing this level
            break

        fields.setdefault(field_number, []).append(value)
    return fields


def decode_signed_varint(value):
    """Convert an unsigned varint to a signed int (zigzag or two's complement)."""
    if value > 0x7FFFFFFFFFFFFFFF:
        value -= 0x10000000000000000
    return value


# ---------------------------------------------------------------------------
# Apple Notes protobuf structure parsing
# ---------------------------------------------------------------------------

def parse_note_data(zdata):
    """
    Parse the ZDATA blob from NoteStore.sqlite.
    Returns a dict with: text, attribute_runs, paragraphs, links, checklists,
    attachments, formatting info.

    Key insight: Apple Notes attribute runs are per-formatting-span, NOT per-paragraph.
    A single checklist item like "Buy groceries" might be split across multiple runs
    (e.g., if part is bold). Paragraph boundaries are marked by '\\n' in the text.
    The ParagraphStyle on the run covering a '\\n' determines that paragraph's type
    (checkbox, heading, list, etc.). We must accumulate text across runs within a
    paragraph and only emit checklist/list items at paragraph boundaries.
    """
    result = {
        'text': '',
        'links': [],
        'checklists': [],
        'formatting': {
            'has_bold': False,
            'has_italic': False,
            'has_headings': False,
            'has_lists': False,
            'has_underline': False,
            'has_strikethrough': False,
            'heading_count': 0,
            'list_count': 0,
        },
        'attachments': [],
        'attribute_runs': [],
        'parse_error': None,
    }

    try:
        # Decompress gzip
        try:
            decompressed = gzip.decompress(zdata)
        except Exception:
            # Maybe it's not gzip compressed - try raw
            decompressed = zdata

        # Top level: NoteStoreProto
        top = decode_protobuf(decompressed)

        # Field 2 = Document
        if 2 not in top:
            result['parse_error'] = 'No Document field (2) in top-level proto'
            return result

        doc_data = top[2][0]
        doc = decode_protobuf(doc_data)

        # Field 3 = Note
        if 3 not in doc:
            result['parse_error'] = 'No Note field (3) in Document'
            return result

        note_data = doc[3][0]
        note = decode_protobuf(note_data)

        # Field 2 = note text (string)
        if 2 in note:
            try:
                result['text'] = note[2][0].decode('utf-8', errors='replace')
            except Exception:
                result['text'] = str(note[2][0])

        # ---------------------------------------------------------------
        # Pass 1: Decode all attribute runs and annotate each character
        # position with its formatting metadata.
        # ---------------------------------------------------------------
        text = result['text']
        text_pos = 0
        raw_runs = []  # List of (start, length, run_text, run_meta) tuples

        if 5 in note:
            for attr_raw in note[5]:
                attr = decode_protobuf(attr_raw)
                run = {}

                # Field 1 = length of this run in characters
                length = 0
                if 1 in attr:
                    length = attr[1][0]
                run['length'] = length

                # Extract the text for this run
                end_pos = min(text_pos + length, len(text))
                run_text = text[text_pos:end_pos]
                run['text'] = run_text
                run['start'] = text_pos

                # Field 5 = font_weight (1=bold, 2=italic, 3=both)
                if 5 in attr:
                    fw = attr[5][0]
                    run['font_weight'] = fw
                    if fw in (1, 3):
                        result['formatting']['has_bold'] = True
                    if fw in (2, 3):
                        result['formatting']['has_italic'] = True

                # Field 6 = underlined
                if 6 in attr:
                    run['underlined'] = True
                    result['formatting']['has_underline'] = True

                # Field 7 = strikethrough
                if 7 in attr:
                    run['strikethrough'] = True
                    result['formatting']['has_strikethrough'] = True

                # Field 9 = link URL
                if 9 in attr:
                    try:
                        url = attr[9][0].decode('utf-8', errors='replace')
                        run['link'] = url
                    except Exception:
                        pass

                # Field 2 = ParagraphStyle (embedded message)
                if 2 in attr:
                    para = decode_protobuf(attr[2][0])

                    # ParagraphStyle field 1 = style_type
                    if 1 in para:
                        style_type = decode_signed_varint(para[1][0])
                        run['style_type'] = style_type

                    # ParagraphStyle field 5 = Checklist (only for style_type 103)
                    if 5 in para:
                        checklist_msg = decode_protobuf(para[5][0])
                        if 2 in checklist_msg:
                            run['checklist_done'] = bool(checklist_msg[2][0])
                        else:
                            run['checklist_done'] = False

                # Field 12 = AttachmentInfo
                if 12 in attr:
                    attachment = decode_protobuf(attr[12][0])
                    att_info = {}
                    if 1 in attachment:
                        try:
                            att_info['identifier'] = attachment[1][0].decode('utf-8', errors='replace')
                        except Exception:
                            att_info['identifier'] = str(attachment[1][0])
                    if 2 in attachment:
                        try:
                            att_info['type_uti'] = attachment[2][0].decode('utf-8', errors='replace')
                        except Exception:
                            att_info['type_uti'] = str(attachment[2][0])
                    result['attachments'].append(att_info)

                result['attribute_runs'].append(run)
                raw_runs.append((text_pos, length, run_text, run))
                text_pos += length

        # ---------------------------------------------------------------
        # Pass 2: Walk through text by paragraphs (split on \n).
        # For each paragraph, determine its style from the run that covers
        # the terminating \n (or the last run if no \n). Accumulate the
        # full paragraph text, and emit checklists/links/headings/lists
        # at paragraph granularity.
        # ---------------------------------------------------------------

        # Build a character-level index: for each char position, which run
        # covers it? We need this to look up the style of the \n character.
        char_run_index = []  # char_run_index[i] = index into raw_runs
        for run_idx, (start, length, _, _) in enumerate(raw_runs):
            char_run_index.extend([run_idx] * length)

        # Also build a mapping from character position to link URL
        # (a link run may span only part of a paragraph)
        char_link = [None] * len(text)
        for run_idx, (start, length, _, run_meta) in enumerate(raw_runs):
            if 'link' in run_meta:
                for i in range(start, min(start + length, len(text))):
                    char_link[i] = run_meta['link']

        # Track which paragraphs are headings/lists for formatting stats
        # (deduplicated — one count per paragraph, not per run)
        heading_paras = set()
        list_paras = set()

        # Split text into paragraphs
        para_start = 0
        para_idx = 0
        for i, ch in enumerate(text):
            if ch == '\n':
                para_text = text[para_start:i]

                # The style of this paragraph comes from the run covering
                # the \n character (position i).
                style_type = -1  # default: body
                checklist_done = False
                if i < len(char_run_index):
                    covering_run = raw_runs[char_run_index[i]][3]
                    style_type = covering_run.get('style_type', -1)
                    checklist_done = covering_run.get('checklist_done', False)

                # Track formatting stats per paragraph (not per run)
                if style_type in (0, 1):
                    heading_paras.add(para_idx)
                elif style_type in (100, 101, 102, 103):
                    list_paras.add(para_idx)

                # Emit checklist items
                if style_type == 103:
                    item_text = para_text.strip()
                    if item_text:  # skip empty checklist lines
                        result['checklists'].append({
                            'text': item_text,
                            'done': checklist_done,
                        })

                # Collect links within this paragraph
                # A link may span part of the paragraph; collect unique links
                seen_links = {}
                for pos in range(para_start, i):
                    url = char_link[pos] if pos < len(char_link) else None
                    if url and url not in seen_links:
                        # Find the full display text for this link
                        link_start = pos
                        link_end = pos
                        while link_end < i and link_end < len(char_link) and char_link[link_end] == url:
                            link_end += 1
                        display = text[link_start:link_end].strip()
                        if display:
                            seen_links[url] = display
                            result['links'].append({
                                'display': display,
                                'url': url,
                            })

                para_start = i + 1
                para_idx += 1

        # Handle final paragraph (if text doesn't end with \n)
        if para_start < len(text):
            para_text = text[para_start:]
            # Check for links in final paragraph
            seen_links = {}
            for pos in range(para_start, len(text)):
                url = char_link[pos] if pos < len(char_link) else None
                if url and url not in seen_links:
                    link_start = pos
                    link_end = pos
                    while link_end < len(text) and link_end < len(char_link) and char_link[link_end] == url:
                        link_end += 1
                    display = text[link_start:link_end].strip()
                    if display:
                        seen_links[url] = display
                        result['links'].append({
                            'display': display,
                            'url': url,
                        })

        # Update formatting stats from paragraph-level counts
        result['formatting']['has_headings'] = len(heading_paras) > 0
        result['formatting']['heading_count'] = len(heading_paras)
        result['formatting']['has_lists'] = len(list_paras) > 0
        result['formatting']['list_count'] = len(list_paras)

    except Exception as e:
        result['parse_error'] = f'{type(e).__name__}: {e}'

    return result


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

NOTES_DB_PATH = os.path.expanduser(
    '~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite'
)

QUERY = """
SELECT
    n.Z_PK,
    c1.ZTITLE1 as title,
    c1.ZSNIPPET as snippet,
    c2.ZTITLE2 as folder_name,
    c5.ZNAME as account_name,
    n.ZDATA as data,
    datetime(c1.ZCREATIONDATE1 + 978307200, 'unixepoch') as created,
    datetime(c1.ZMODIFICATIONDATE1 + 978307200, 'unixepoch') as modified
FROM ZICNOTEDATA as n
LEFT JOIN ZICCLOUDSYNCINGOBJECT as c1 ON c1.ZNOTEDATA = n.Z_PK
LEFT JOIN ZICCLOUDSYNCINGOBJECT as c2 ON c2.Z_PK = c1.ZFOLDER
LEFT JOIN ZICCLOUDSYNCINGOBJECT as c5 ON c5.Z_PK = c1.ZACCOUNT2
WHERE n.ZDATA IS NOT NULL
    AND n.ZCRYPTOTAG IS NULL
ORDER BY c1.ZMODIFICATIONDATE1 DESC
"""


def copy_database_snapshot(src_dir, db_name='NoteStore.sqlite'):
    """
    Copy the database + WAL + SHM files to a temp directory for a consistent
    snapshot without disturbing Notes.app.

    Tries multiple approaches:
    1. Python shutil.copy2 (requires Full Disk Access for Python/terminal)
    2. subprocess cp command (may have different permissions)
    3. Direct read-only open of original (last resort, no WAL consistency)
    """
    tmpdir = tempfile.mkdtemp(prefix='apple_notes_')
    files_to_copy = [db_name, f'{db_name}-wal', f'{db_name}-shm']
    src_db = os.path.join(src_dir, db_name)

    # Approach 1: Python shutil
    try:
        for fname in files_to_copy:
            src = os.path.join(src_dir, fname)
            dst = os.path.join(tmpdir, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        # Verify the copy worked
        if os.path.exists(os.path.join(tmpdir, db_name)):
            print('  Method: Python shutil.copy2')
            return os.path.join(tmpdir, db_name), tmpdir
    except PermissionError:
        pass  # Try next approach
    except Exception as e:
        print(f'  shutil copy failed: {e}')

    # Approach 2: subprocess cp (may have different TCC permissions)
    try:
        for fname in files_to_copy:
            src = os.path.join(src_dir, fname)
            dst = os.path.join(tmpdir, fname)
            if os.path.exists(src):
                result = subprocess.run(
                    ['cp', src, dst],
                    capture_output=True, timeout=10
                )
                if result.returncode != 0:
                    # cp failed for this file, but WAL/SHM are optional
                    if fname == db_name:
                        raise PermissionError(f'cp failed: {result.stderr.decode()}')
        if os.path.exists(os.path.join(tmpdir, db_name)):
            print('  Method: subprocess cp')
            return os.path.join(tmpdir, db_name), tmpdir
    except PermissionError:
        pass
    except Exception as e:
        print(f'  subprocess cp failed: {e}')

    # Approach 3: Use sqlite3 CLI to dump and re-import (sometimes has access)
    try:
        dump_path = os.path.join(tmpdir, 'dump.sql')
        result = subprocess.run(
            ['sqlite3', src_db, '.dump'],
            capture_output=True, timeout=60
        )
        if result.returncode == 0 and len(result.stdout) > 100:
            dst_db = os.path.join(tmpdir, db_name)
            with open(dump_path, 'wb') as f:
                f.write(result.stdout)
            result2 = subprocess.run(
                ['sqlite3', dst_db],
                input=result.stdout, capture_output=True, timeout=60
            )
            if os.path.exists(dst_db) and os.path.getsize(dst_db) > 0:
                print('  Method: sqlite3 CLI dump/restore')
                return dst_db, tmpdir
    except Exception as e:
        print(f'  sqlite3 CLI dump failed: {e}')

    # Approach 4: Direct read-only open (no copy, returns original path)
    try:
        conn = sqlite3.connect(f'file:{src_db}?mode=ro', uri=True)
        conn.execute('SELECT 1')
        conn.close()
        print('  Method: Direct read-only open (no copy)')
        return src_db, tmpdir
    except Exception as e:
        print(f'  Direct RO open failed: {e}')

    # All approaches failed
    shutil.rmtree(tmpdir, ignore_errors=True)
    raise PermissionError(
        'All database access methods failed. Full Disk Access is required.'
    )


def query_notes(db_path):
    """Query the NoteStore database and return rows."""
    # If this is the original path (not a copy), use read-only URI mode
    if 'Group Containers' in db_path:
        uri = f'file:{db_path}?mode=ro'
    else:
        uri = f'file:{db_path}?mode=ro'

    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(QUERY)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        if 'unable to open' in str(e).lower() or 'readonly' in str(e).lower():
            raise
        raise


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

STYLE_NAMES = {
    -1: 'body',
    0: 'title',
    1: 'heading',
    100: 'dotted-list',
    101: 'dashed-list',
    102: 'numbered-list',
    103: 'checkbox',
}


def format_note_summary(row, parsed, max_text=200):
    """Format a note for summary display."""
    lines = []
    title = row['title'] or '(untitled)'
    folder = row['folder_name'] or '(no folder)'
    account = row['account_name'] or '(no account)'

    lines.append(f'  Title:    {title}')
    lines.append(f'  Folder:   {folder} ({account})')
    lines.append(f'  Created:  {row["created"]}')
    lines.append(f'  Modified: {row["modified"]}')

    # Plain text preview
    text = parsed['text'].strip()
    if text:
        # Skip the first line if it matches the title (Notes puts title as first line)
        text_lines = text.split('\n')
        if text_lines and text_lines[0].strip() == (row['title'] or '').strip():
            text = '\n'.join(text_lines[1:]).strip()
        preview = text[:max_text]
        if len(text) > max_text:
            preview += '...'
        lines.append(f'  Text:     {preview}')

    if parsed['parse_error']:
        lines.append(f'  ERROR:    {parsed["parse_error"]}')

    # Links
    if parsed['links']:
        lines.append(f'  Links ({len(parsed["links"])}):')
        for lnk in parsed['links'][:5]:
            lines.append(f'    "{lnk["display"]}" -> {lnk["url"]}')
        if len(parsed['links']) > 5:
            lines.append(f'    ... and {len(parsed["links"]) - 5} more')

    # Checklists
    if parsed['checklists']:
        lines.append(f'  Checklist ({len(parsed["checklists"])} items):')
        for item in parsed['checklists'][:5]:
            marker = '[x]' if item['done'] else '[ ]'
            lines.append(f'    {marker} {item["text"]}')
        if len(parsed['checklists']) > 5:
            lines.append(f'    ... and {len(parsed["checklists"]) - 5} more')

    # Formatting
    fmt = parsed['formatting']
    fmt_parts = []
    if fmt['has_bold']:
        fmt_parts.append('bold')
    if fmt['has_italic']:
        fmt_parts.append('italic')
    if fmt['has_underline']:
        fmt_parts.append('underline')
    if fmt['has_strikethrough']:
        fmt_parts.append('strikethrough')
    if fmt['has_headings']:
        fmt_parts.append(f'headings({fmt["heading_count"]})')
    if fmt['has_lists']:
        fmt_parts.append(f'lists({fmt["list_count"]})')
    if fmt_parts:
        lines.append(f'  Format:   {", ".join(fmt_parts)}')

    # Attachments
    if parsed['attachments']:
        lines.append(f'  Attachments ({len(parsed["attachments"])}):')
        for att in parsed['attachments'][:3]:
            uti = att.get('type_uti', 'unknown')
            lines.append(f'    type={uti}')

    return '\n'.join(lines)


def format_note_full(row, parsed):
    """Format a note with full details."""
    lines = []
    title = row['title'] or '(untitled)'
    folder = row['folder_name'] or '(no folder)'
    account = row['account_name'] or '(no account)'

    lines.append(f'  Title:    {title}')
    lines.append(f'  Folder:   {folder} ({account})')
    lines.append(f'  Created:  {row["created"]}')
    lines.append(f'  Modified: {row["modified"]}')
    lines.append(f'  DB PK:    {row["Z_PK"]}')

    if parsed['parse_error']:
        lines.append(f'  PARSE ERROR: {parsed["parse_error"]}')

    # Full text
    text = parsed['text'].strip()
    if text:
        lines.append(f'  --- Full Text ({len(text)} chars) ---')
        for tl in text.split('\n')[:50]:
            lines.append(f'  | {tl}')
        if len(text.split('\n')) > 50:
            lines.append(f'  | ... ({len(text.split(chr(10)))} total lines)')

    # All links
    if parsed['links']:
        lines.append(f'  --- Links ({len(parsed["links"])}) ---')
        for lnk in parsed['links']:
            lines.append(f'  "{lnk["display"]}" -> {lnk["url"]}')

    # All checklists
    if parsed['checklists']:
        lines.append(f'  --- Checklist ({len(parsed["checklists"])} items) ---')
        for item in parsed['checklists']:
            marker = '[x]' if item['done'] else '[ ]'
            lines.append(f'  {marker} {item["text"]}')

    # Attachments
    if parsed['attachments']:
        lines.append(f'  --- Attachments ({len(parsed["attachments"])}) ---')
        for att in parsed['attachments']:
            ident = att.get('identifier', '?')
            uti = att.get('type_uti', 'unknown')
            lines.append(f'  id={ident} type={uti}')

    # Paragraph-level formatting summary (collapsed from per-character runs)
    # Walk text by paragraphs, summarize formatting per paragraph
    text_full = parsed['text']
    runs = parsed['attribute_runs']
    if runs and text_full:
        # Build paragraph info by walking text + runs together
        para_summaries = []
        para_start = 0
        run_idx = 0
        run_char_offset = 0  # chars consumed within current run

        for i, ch in enumerate(text_full):
            if ch == '\n':
                para_text = text_full[para_start:i]
                if para_text.strip():
                    # Collect formatting flags across all runs in this paragraph
                    fmt_flags = set()
                    links_in_para = []
                    # Find runs covering [para_start, i)
                    pos = 0
                    for r in runs:
                        r_start = pos
                        r_end = pos + r.get('length', 0)
                        if r_end > para_start and r_start < i:
                            if r.get('font_weight') in (1, 3):
                                fmt_flags.add('bold')
                            if r.get('font_weight') in (2, 3):
                                fmt_flags.add('italic')
                            if r.get('underlined'):
                                fmt_flags.add('underline')
                            if r.get('strikethrough'):
                                fmt_flags.add('strike')
                            if r.get('link'):
                                links_in_para.append(r['link'])
                            st = r.get('style_type')
                            if st is not None and st != -1:
                                fmt_flags.add(STYLE_NAMES.get(st, f'style_{st}'))
                        pos = r_end

                    if fmt_flags or links_in_para:
                        preview = para_text[:80].strip()
                        tag = ','.join(sorted(fmt_flags))
                        if links_in_para:
                            tag += (', ' if tag else '') + f'{len(links_in_para)} link(s)'
                        para_summaries.append(f'  [{tag}] "{preview}"')
                para_start = i + 1

        if para_summaries:
            lines.append(f'  --- Paragraph Formatting ({len(para_summaries)} styled) ---')
            for ps in para_summaries[:15]:
                lines.append(ps)
            if len(para_summaries) > 15:
                lines.append(f'  ... and {len(para_summaries) - 15} more')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 80)
    print('Apple Notes SQLite Reader - Prototype Test')
    print('=' * 80)
    print()

    # Check if source database exists
    src_dir = os.path.dirname(NOTES_DB_PATH)
    if not os.path.exists(NOTES_DB_PATH):
        print(f'ERROR: NoteStore.sqlite not found at:')
        print(f'  {NOTES_DB_PATH}')
        print()
        print('This could mean:')
        print('  - Apple Notes has never been used on this Mac')
        print('  - The path has changed in a newer macOS version')
        sys.exit(1)

    print(f'Source database: {NOTES_DB_PATH}')
    src_size = os.path.getsize(NOTES_DB_PATH)
    print(f'Database size: {src_size / 1024 / 1024:.1f} MB')

    # Check for WAL/SHM
    wal_path = NOTES_DB_PATH + '-wal'
    shm_path = NOTES_DB_PATH + '-shm'
    if os.path.exists(wal_path):
        print(f'WAL file: {os.path.getsize(wal_path) / 1024:.1f} KB')
    if os.path.exists(shm_path):
        print(f'SHM file: {os.path.getsize(shm_path) / 1024:.1f} KB')
    print()

    # Step 1: Copy to temp directory
    print('Step 1: Copying database to temp directory for safe read...')
    try:
        tmp_db_path, tmpdir = copy_database_snapshot(src_dir)
        print(f'  Snapshot copied to: {tmpdir}')
    except PermissionError:
        print()
        print('ERROR: Permission denied when copying NoteStore.sqlite!')
        print()
        print('This means Full Disk Access has NOT been granted to Terminal')
        print('(or whatever app is running this script).')
        print()
        print('To fix this:')
        print('  1. Open System Settings > Privacy & Security > Full Disk Access')
        print('  2. Enable access for Terminal.app (or your terminal emulator)')
        print('  3. Restart your terminal and try again')
        sys.exit(1)
    except Exception as e:
        print(f'ERROR copying database: {e}')
        sys.exit(1)

    try:
        # Step 2: Query the database
        print()
        print('Step 2: Querying NoteStore database...')
        try:
            rows = query_notes(tmp_db_path)
        except sqlite3.OperationalError as e:
            print(f'ERROR querying database: {e}')
            if 'no such table' in str(e).lower():
                print('  The database schema may have changed in this macOS version.')
            sys.exit(1)

        print(f'  Found {len(rows)} notes with data')
        print()

        # Step 3: Parse all notes
        print('Step 3: Parsing protobuf data for all notes...')
        parsed_notes = []
        parse_errors = 0
        for row in rows:
            p = parse_note_data(row['data'])
            parsed_notes.append((row, p))
            if p['parse_error']:
                parse_errors += 1

        print(f'  Parsed {len(parsed_notes)} notes ({parse_errors} with parse errors)')
        print()

        # Step 4: Summary grouped by folder
        print('=' * 80)
        print('ALL NOTES BY FOLDER')
        print('=' * 80)

        by_folder = defaultdict(list)
        for row, p in parsed_notes:
            folder = row['folder_name'] or '(no folder)'
            account = row['account_name'] or '(no account)'
            key = f'{folder} ({account})'
            by_folder[key].append((row, p))

        for folder_key in sorted(by_folder.keys()):
            notes_in_folder = by_folder[folder_key]
            print()
            print(f'--- {folder_key} ({len(notes_in_folder)} notes) ---')
            for row, p in notes_in_folder:
                print()
                print(format_note_summary(row, p))

        # Step 5: Deep dive - Uinta notes
        print()
        print('=' * 80)
        print('DEEP DIVE: Notes in Uinta-related folders')
        print('=' * 80)

        uinta_notes = [(r, p) for r, p in parsed_notes
                       if (r['folder_name'] and 'uinta' in r['folder_name'].lower())
                       or (r['title'] and 'uinta' in r['title'].lower())]

        if uinta_notes:
            print(f'\nFound {len(uinta_notes)} Uinta-related notes:')
            for row, p in uinta_notes[:10]:
                print()
                print(format_note_full(row, p))
                print()
            if len(uinta_notes) > 10:
                print(f'... showing first 10 of {len(uinta_notes)} Uinta notes')
        else:
            print('\nNo notes found with "Uinta" in folder or title.')

        # Step 6: Deep dive - Checklist notes
        print()
        print('=' * 80)
        print('DEEP DIVE: Notes with Checklists')
        print('=' * 80)

        checklist_notes = [(r, p) for r, p in parsed_notes if p['checklists']]
        if checklist_notes:
            print(f'\nFound {len(checklist_notes)} notes with checklists:')
            for row, p in checklist_notes[:5]:
                print()
                title = row['title'] or '(untitled)'
                folder = row['folder_name'] or '(no folder)'
                print(f'  "{title}" in {folder}')
                print(f'  Modified: {row["modified"]}')
                total = len(p['checklists'])
                done = sum(1 for c in p['checklists'] if c['done'])
                print(f'  Progress: {done}/{total} completed')
                for item in p['checklists']:
                    marker = '[x]' if item['done'] else '[ ]'
                    print(f'    {marker} {item["text"]}')
                print()
            if len(checklist_notes) > 5:
                print(f'... showing first 5 of {len(checklist_notes)} checklist notes')
        else:
            print('\nNo notes with checklists found.')

        # Step 7: Deep dive - Notes with links
        print()
        print('=' * 80)
        print('DEEP DIVE: Notes with Hyperlinks')
        print('=' * 80)

        link_notes = [(r, p) for r, p in parsed_notes if p['links']]
        if link_notes:
            print(f'\nFound {len(link_notes)} notes with hyperlinks:')
            for row, p in link_notes[:5]:
                print()
                title = row['title'] or '(untitled)'
                folder = row['folder_name'] or '(no folder)'
                print(f'  "{title}" in {folder}')
                print(f'  Modified: {row["modified"]}')
                print(f'  Links:')
                for lnk in p['links'][:10]:
                    print(f'    "{lnk["display"]}" -> {lnk["url"]}')
                if len(p['links']) > 10:
                    print(f'    ... and {len(p["links"]) - 10} more links')
                print()
            if len(link_notes) > 5:
                print(f'... showing first 5 of {len(link_notes)} link notes')
        else:
            print('\nNo notes with hyperlinks found.')

        # Step 8: Statistics
        print()
        print('=' * 80)
        print('STATISTICS')
        print('=' * 80)
        print()

        total = len(parsed_notes)
        print(f'Total notes found:         {total}')
        print(f'Parse errors:              {parse_errors}')
        print()

        # Notes per folder
        print(f'Notes per folder:')
        for folder_key in sorted(by_folder.keys()):
            count = len(by_folder[folder_key])
            print(f'  {folder_key}: {count}')
        print()

        # Feature counts
        with_links = sum(1 for _, p in parsed_notes if p['links'])
        with_checklists = sum(1 for _, p in parsed_notes if p['checklists'])
        with_bold = sum(1 for _, p in parsed_notes if p['formatting']['has_bold'])
        with_italic = sum(1 for _, p in parsed_notes if p['formatting']['has_italic'])
        with_headings = sum(1 for _, p in parsed_notes if p['formatting']['has_headings'])
        with_lists = sum(1 for _, p in parsed_notes if p['formatting']['has_lists'])
        with_underline = sum(1 for _, p in parsed_notes if p['formatting']['has_underline'])
        with_strikethrough = sum(1 for _, p in parsed_notes if p['formatting']['has_strikethrough'])
        with_attachments = sum(1 for _, p in parsed_notes if p['attachments'])
        with_attachment_char = sum(1 for _, p in parsed_notes if '\ufffc' in p['text'])

        print(f'Notes with links:          {with_links}')
        print(f'Notes with checklists:     {with_checklists}')
        print(f'Notes with bold:           {with_bold}')
        print(f'Notes with italic:         {with_italic}')
        print(f'Notes with underline:      {with_underline}')
        print(f'Notes with strikethrough:  {with_strikethrough}')
        print(f'Notes with headings:       {with_headings}')
        print(f'Notes with lists:          {with_lists}')
        print(f'Notes with attachments:    {with_attachments} (protobuf)')
        print(f'Notes with U+FFFC char:    {with_attachment_char} (attachment placeholder)')
        print()

        # Total links / checklists
        total_links = sum(len(p['links']) for _, p in parsed_notes)
        total_checklist_items = sum(len(p['checklists']) for _, p in parsed_notes)
        total_done = sum(sum(1 for c in p['checklists'] if c['done']) for _, p in parsed_notes)
        print(f'Total hyperlinks:          {total_links}')
        print(f'Total checklist items:     {total_checklist_items} ({total_done} done, {total_checklist_items - total_done} pending)')
        print()

        print('=' * 80)
        print('TEST COMPLETE')
        print('=' * 80)

    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(tmpdir)
            print(f'\nCleaned up temp directory: {tmpdir}')
        except Exception as e:
            print(f'\nWarning: Could not clean up {tmpdir}: {e}')


if __name__ == '__main__':
    main()
