#!/usr/bin/env python3
"""Export Cordell M. Andersen's book as a single anchored HTML file.

Renders the full text layer of data/the-high-uinta-mountains-by-cma.pdf
(gitignored, Mini-only) into cma_book.html at the repo root — one <section>
per printed page, each with id="cma-p<printed>" so the PWA's lake modal (and
plain links like cma_book.html#cma-p356) can jump straight to a cited page.

The file is both a standalone readable page and the fetch source for the
in-modal book viewer in index.html (which extracts <main id="book">).

Requires pdftotext (poppler) and the PDF; safe to re-run any time (idempotent,
touches nothing but cma_book.html).
"""

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PDF_PATH = os.path.join(PROJECT_DIR, "data", "the-high-uinta-mountains-by-cma.pdf")
OUT_PATH = os.path.join(PROJECT_DIR, "cma_book.html")

PAGE_OFFSET = 15  # printed page N = PDF page N + 15 (same as import_cma_book.py)
PHOTOS_DIR = os.path.join(PROJECT_DIR, "cma_photos")  # gitignored; scripts/extract_cma_photos.py builds it

STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 0; background: #f8fafc; color: #374151; }
.wrap { max-width: 46rem; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; }
h1 { font-size: 1.5rem; color: #1f2937; margin: 0 0 .25rem; }
.byline { color: #6b7280; font-size: .875rem; margin-bottom: 2rem; }
.cma-page { border-top: 1px dashed #cbd5e1; padding-top: .75rem; margin-top: .75rem; }
.cma-page-num { font-size: .75rem; color: #94a3b8; font-weight: 600; }
.cma-page p { margin: .5rem 0 .75rem; line-height: 1.6; }
.cma-empty { color: #9ca3af; font-style: italic; }
.cma-photo { display: block; max-width: 100%; height: auto; margin: .5rem 0; border-radius: .25rem; }
:target { background: #fefce8; }
"""


def extract_pages():
    if not os.path.exists(PDF_PATH):
        sys.exit(f"Book PDF not found at {PDF_PATH} (it is gitignored and "
                 "lives only on the Mini) — nothing to do.")
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext (poppler) not found on PATH — brew install poppler")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tmp = tf.name
    try:
        subprocess.run(["pdftotext", PDF_PATH, tmp], check=True)
        with open(tmp, encoding="utf-8") as f:
            return f.read().split("\f")
    finally:
        os.unlink(tmp)


def page_paragraphs(page_text, printed):
    """Blank-line blocks, whitespace-collapsed — same shaping as the cma_notes
    excerpts in import_cma_book.py, so the book reads like the excerpts do."""
    lines = page_text.rstrip().splitlines()
    # Drop the bare printed-page-number line pdftotext leaves at the bottom.
    if lines and lines[-1].strip() == str(printed):
        lines = lines[:-1]
    out = []
    for block in re.split(r"\n\s*\n", "\n".join(lines)):
        p = re.sub(r"\s+", " ", block).strip()
        if p:
            out.append(p)
    return out


def page_photos(printed):
    """Sorted cma_photos/p<printed>-<i>.jpg filenames (extract_cma_photos.py
    names them by printed page so they line up with each page's section)."""
    if printed < 1 or not os.path.isdir(PHOTOS_DIR):
        return []
    pattern = re.compile(rf"^p{printed}-(\d+)\.jpg$")
    matches = []
    for fname in os.listdir(PHOTOS_DIR):
        m = pattern.match(fname)
        if m:
            matches.append((int(m.group(1)), fname))
    return [fname for _, fname in sorted(matches)]


def section_html(pdf_page, page_text):
    printed = pdf_page - PAGE_OFFSET
    if printed >= 1:
        sec_id, label = f"cma-p{printed}", f"p. {printed}"
    else:
        sec_id, label = f"cma-front-{pdf_page}", f"front matter ({pdf_page})"
    paras = page_paragraphs(page_text, printed)
    body = ("".join(f"<p>{html.escape(p)}</p>" for p in paras)
            or '<p class="cma-empty">(photos / maps — no text on this page)</p>')
    photos_html = "".join(
        f'<img loading="lazy" class="cma-photo" '
        f'src="cma_photos/{html.escape(fname)}" alt="Photo, p. {printed}">'
        for fname in page_photos(printed))
    return (f'<section class="cma-page" id="{sec_id}">'
            f'<div class="cma-page-num">{label}</div>{body}{photos_html}</section>')


def main():
    pages = extract_pages()
    sections = [section_html(i + 1, text) for i, text in enumerate(pages) if text.strip() or i + 1 - PAGE_OFFSET >= 1]
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The High Uinta Mountains — Cordell M. Andersen</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
<h1>The High Uinta Mountains</h1>
<div class="byline">Cordell M. Andersen — text extracted from the author's self-published book.
Link to a page with <code>#cma-p&lt;printed page&gt;</code>.</div>
<main id="book">
{chr(10).join(sections)}
</main>
</div>
</body>
</html>
"""
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(doc)
    printed_pages = sum(1 for i in range(len(pages)) if i + 1 - PAGE_OFFSET >= 1)
    print(f"Wrote {OUT_PATH}: {len(sections)} sections "
          f"({printed_pages} printed pages), {os.path.getsize(OUT_PATH):,} bytes")


if __name__ == "__main__":
    main()
