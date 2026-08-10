#!/usr/bin/env python3
"""Scrape junesucker.com Uinta lake pages into `lakes.junesucker_notes`.

Replaces the one-off `data/process_all_lake_pages.py`. Two things it does that
the original didn't:

1. **Section-aware extraction.** The pages are laid out as `<h4>` sections
   ("Directions", "The Hike", "Fish Species", ...). We keep the section
   structure as markdown headings and DROP the sections that duplicate data we
   already hold: "Historical DWR Info" (same pamphlet text as `dwr_notes`) and
   "Nearby Places to Fish" (a list of other lakes, useless inside one lake's
   note). See SKIP_SECTION_RE.

2. **Designation-only matching.** A page is credited to a lake only on an exact
   letter-number designation, never on a fuzzy name — same rule the stocking
   matcher learned the hard way (see CLAUDE.md). Pages we can't match are
   reported, not guessed at.

Usage:
    python3 scripts/scrape_junesucker.py --dry-run     # report, write nothing
    python3 scripts/scrape_junesucker.py               # scrape + update the DB
    python3 scripts/scrape_junesucker.py --only A-11   # single lake
"""

import argparse
import csv
import html as htmllib
import os
import re
import sqlite3
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import writer_guard  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO, 'uinta_lakes.db')
PAGES_DIR = os.path.join(REPO, 'data', 'junesucker_pages')
LINKS_CSV = os.path.join(REPO, 'data', 'uinta_lake_links.csv')

INDEX_URL = 'https://junesucker.com/lakes/uintas/'

# Cloudflare 403s a bare curl/urllib UA.
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Sections we deliberately do not store. The DWR ones repeat the pamphlet text
# already in dwr_notes -- and the heading wording varies across the site's
# vintages ("Historical DWR Info", "DWR Historical Data", "DWR Info",
# "Historical Information"), hence the loose pattern. "Nearby Areas to Fish" is
# a directory of OTHER lakes (and its stray designations would poison matching).
SKIP_SECTION_RE = re.compile(
    r'\bdwr\b|historical\s+(info|information|data)|'
    r'nearby\s+(places|areas|lakes)|other\s+nearby', re.I)

# Site chrome that lives in the same <p>/<li> soup as the prose.
NAV_RE = re.compile(
    r'^(home|about|faq|log ?in|contact|search for:?|privacy.*|'
    r'utah fishing and outdoor index|©.*)$', re.I)

# Older pages don't use <h4>; they lead a paragraph with a bold label:
# "Historical DWR Info: This lake is ...". Same sections, different markup.
LABEL_RE = re.compile(r'^([A-Z][A-Za-z0-9 /\'&?-]{2,45}?):\s+(\S.*)$', re.S)

# Drainage/index/feed pages are not lakes.
NON_LAKE_RE = re.compile(r'/(feed|.*-drainage)/$', re.I)

DESIGNATION_RE = re.compile(r'\b([A-Z]{1,2}-\d{1,3})\b')


def fetch(url, pause=2.0):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        body = r.read().decode('utf-8', 'replace')
    time.sleep(pause)  # be a polite guest on someone else's blog
    return body


def strip_tags(fragment):
    fragment = re.sub(r'<br\s*/?>', '\n', fragment, flags=re.I)
    text = re.sub(r'<[^>]+>', '', fragment)
    text = htmllib.unescape(text)
    text = text.replace('\xa0', ' ')
    return re.sub(r'[ \t]+', ' ', text).strip()


def find_lake_links(index_html):
    """Return ordered (url, link_text) for every Uinta lake page on the index."""
    found = {}
    for m in re.finditer(
            r'<a[^>]+href="(https://junesucker\.com/lakes/uintas/[^"]+/)"[^>]*>(.*?)</a>',
            index_html, re.S):
        url, text = m.group(1), strip_tags(m.group(2))
        if url == INDEX_URL or NON_LAKE_RE.search(url):
            continue
        if url not in found or (not found[url] and text):
            found[url] = text
    return sorted(found.items())


def extract_page(page_html):
    """-> (title, [(heading|None, [paragraph, ...]), ...]) with skipped sections removed."""
    title = ''
    m = re.search(r'<h1[^>]*>(.*?)</h1>', page_html, re.S)
    if m:
        title = strip_tags(m.group(1))

    m = re.search(r'<div[^>]+class="[^"]*\bentry-content\b[^"]*"[^>]*>(.*)',
                  page_html, re.S)
    body = m.group(1) if m else page_html

    sections = [(None, [])]
    for blk in re.finditer(r'<(h[2-4]|p|li)\b[^>]*>(.*?)</\1>', body, re.S):
        tag, text = blk.group(1).lower(), strip_tags(blk.group(2))
        if not text:
            continue
        if NAV_RE.match(text):
            continue
        if tag.startswith('h'):
            sections.append((text, []))
            continue
        m = LABEL_RE.match(text)
        if m and len(m.group(1).split()) <= 6:
            sections.append((m.group(1).strip(), [m.group(2).strip()]))
        else:
            sections[-1][1].append(text)

    kept = []
    for heading, paras in sections:
        if heading and SKIP_SECTION_RE.search(heading):
            continue
        if not paras:
            continue
        kept.append((heading, paras))
    return title, kept


def to_markdown(sections):
    """Markdown body only -- no page title. The lake modal (and the Apple Note)
    already carry the lake's name, and index.html only styles `## ` headings."""
    out = []
    for heading, paras in sections:
        if heading:
            out.append(f'## {heading}')
        out.extend(paras)
    return '\n\n'.join(out).strip()


def normalize_name(text):
    text = re.sub(r'\b(lake|reservoir)\b', '', (text or '').lower())
    return re.sub(r'[^a-z0-9]+', '', text)


def designation_for(title, link_text, sections, valid, by_name):
    """Exact designation match, most-trustworthy source first; exact name last.

    Returns (designation, how) or (None, None).
    """
    def hit(text):
        for d in DESIGNATION_RE.findall(text or ''):
            if d in valid:
                return d
        return None

    for source, how in ((title, 'title'), (link_text, 'index link')):
        d = hit(source)
        if d:
            return d, how
    # Fall back to the cleaned body, but only if it names exactly one lake --
    # ambiguity here is how pages get credited to the wrong water.
    body = ' '.join(p for _, paras in sections for p in paras)
    found = {d for d in DESIGNATION_RE.findall(body) if d in valid}
    if len(found) == 1:
        return found.pop(), 'body'
    # Last resort: the page never states a designation (junesucker doesn't
    # always). Accept only an EXACT whole-name match that is unique in the DB --
    # no substrings. This is what keeps "Beaver Cr"-class mis-files out.
    key = normalize_name(title) or normalize_name(link_text)
    if key and len(by_name.get(key, [])) == 1:
        return by_name[key][0], 'exact name'
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true',
                    help='scrape and report, but do not touch the DB')
    ap.add_argument('--only', help='limit to one designation (e.g. A-11)')
    ap.add_argument('--pause', type=float, default=2.0, help='seconds between requests')
    args = ap.parse_args()

    if not args.dry_run:
        writer_guard.exit_if_readonly('scrape_junesucker.py')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT letter_number, name, junesucker_notes FROM lakes')
    rows = cur.fetchall()
    valid = {r[0] for r in rows if r[0]}
    names = {r[0]: r[1] for r in rows}
    existing = {r[0]: (r[2] or '') for r in rows}
    by_name = {}
    for ln, nm, _ in rows:
        if ln and nm:
            by_name.setdefault(normalize_name(nm), []).append(ln)

    print(f'Fetching index: {INDEX_URL}')
    links = find_lake_links(fetch(INDEX_URL, args.pause))
    print(f'{len(links)} lake pages listed\n')

    os.makedirs(PAGES_DIR, exist_ok=True)
    if not args.dry_run:
        # Keep the committed link list current so the next run can diff it.
        with open(LINKS_CSV, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['url', 'text'])
            w.writerows(links)
    updated, unchanged, unmatched, failed = [], [], [], []

    for url, link_text in links:
        slug = url.rstrip('/').rsplit('/', 1)[-1]
        try:
            page_html = fetch(url, args.pause)
        except Exception as e:  # network/Cloudflare hiccup: report, keep going
            print(f'  !! {slug}: {e}')
            failed.append((slug, str(e)))
            continue

        title, sections = extract_page(page_html)
        markdown = to_markdown(sections)
        if not markdown:
            failed.append((slug, 'no content extracted'))
            continue

        with open(os.path.join(PAGES_DIR, f'{slug}.md'), 'w') as f:
            f.write(markdown + '\n')

        d, how = designation_for(title, link_text, sections, valid, by_name)
        if not d:
            unmatched.append((slug, title or link_text))
            print(f'  -- {slug}: no designation match ({title or link_text})')
            continue
        if args.only and d != args.only:
            continue

        if existing.get(d, '') == markdown:
            unchanged.append(d)
            continue
        updated.append((d, names.get(d), len(existing.get(d, '')), len(markdown)))
        print(f'  ++ {d} {names.get(d) or ""}: '
              f'{len(existing.get(d, ""))} -> {len(markdown)} chars  [{how}]')
        if not args.dry_run:
            cur.execute('UPDATE lakes SET junesucker_notes = ? WHERE letter_number = ?',
                        (markdown, d))

    if not args.dry_run:
        conn.commit()
    conn.close()

    print(f'\n=== {"DRY RUN " if args.dry_run else ""}Summary ===')
    print(f'pages listed:      {len(links)}')
    print(f'lakes updated:     {len(updated)}')
    print(f'already current:   {len(unchanged)}')
    print(f'unmatched pages:   {len(unmatched)}')
    for slug, label in unmatched:
        print(f'    {slug:38s} {label}')
    if failed:
        print(f'failed:            {len(failed)}')
        for slug, err in failed:
            print(f'    {slug:38s} {err}')


if __name__ == '__main__':
    main()
