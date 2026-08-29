#!/usr/bin/env python3
"""Export Falcon's "Hiking Utah's High Uintas" (3rd ed.) as one anchored HTML page.

Renders the purchased, DRM-stripped EPUB (data/falcon_guide/
hiking-utahs-high-uintas-3e.epub, gitignored) into
data/tailscale_book/falcon_guide/index.html plus an images/ directory —
private output, gitignored, reachable only over Jed's Tailscale VPN via the
edits server's static file serving (same pattern as the CMA book media plan).

It fixes the two Kobo-app pain points:
  1. Navigation — a full Contents section (parts -> trailheads -> hikes, all
     in-page links), stable anchors (id="hike-NN" on every hike heading, from
     the guide_hikes mapping in uinta_lakes.db, read-only), prev/next links
     between sections, a floating "^ Contents" button, EPUB-internal hrefs
     rewritten to in-page anchors, and plain-text cross references ("Hikes 1
     through 20", "See map on pages 55-56") linkified.
  2. Images — every <img> is loading="lazy" (one long page, ~31 MB of maps and
     photos) and wrapped in <a href="images/..." target="_blank"> so any map
     opens as the raw full-resolution file, natively pinch-zoomable. Image
     bytes are copied verbatim from the EPUB — never recompressed.

Deep-link a hike with #hike-NN (NN = the book's hike number, 1-90); printed
pages keep their #page_NN anchors from the EPUB.

Reads the DB read-only for the hike_number <-> source_file mapping; safe to
re-run any time (idempotent — identical input yields byte-identical output).
"""

import html
import os
import re
import sqlite3
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
EPUB_PATH = os.path.join(PROJECT_DIR, "data", "falcon_guide",
                         "hiking-utahs-high-uintas-3e.epub")
DB_PATH = os.path.join(PROJECT_DIR, "uinta_lakes.db")
OUT_DIR = os.path.join(PROJECT_DIR, "data", "tailscale_book", "falcon_guide")
IMG_DIR = os.path.join(OUT_DIR, "images")
OUT_HTML = os.path.join(OUT_DIR, "index.html")

# Friendly labels for spine files the NCX doesn't name (front/back matter).
STEM_LABELS = {
    "Cover": "Cover",
    "HalfTitle": "Half Title",
    "FrontOther01": "Publisher’s Note",
    "TitlePage": "Title Page",
    "Copyright": "Copyright",
    "FrontOther02": "Frontispiece",
    "FrontOther03": "Epigraph",
    "Introduction": "Introduction",
    "HighUintasPortfolio": "High Uintas Portfolio",
    "VisitingResponsibly": "Visiting Responsibly",
    "HowtoUseThisBook": "How to Use This Book",
    "MapLegend": "Map Legend",
    "TheArtofHiking": "The Art of Hiking",
    "AboutAuthors": "About the Authors",
    "BackCover": "Back Cover",
}

STYLE = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Georgia, sans-serif;
       margin: 0; background: #f8fafc; color: #374151; }
.wrap { max-width: 46rem; margin: 0 auto; padding: 1.5rem 1.25rem 5rem; }
h1, h2, h3, h4, h5, h6 { color: #1f2937; line-height: 1.25; }
p { line-height: 1.65; margin: .6em 0; }
a { color: #2563eb; }
img { max-width: 100%; height: auto; }
[id] { scroll-margin-top: .5rem; }
:target { background: #fefce8; }

/* header */
.site-title { font-size: 1.5rem; margin: 0 0 .25rem; }
.byline { color: #6b7280; font-size: .875rem; margin-bottom: 1.5rem; }

/* contents */
#contents { background: #fff; border: 1px solid #e2e8f0; border-radius: .5rem;
            padding: 1rem 1.25rem; margin-bottom: 2rem; }
#contents h2 { margin: 0 0 .5rem; font-size: 1.2rem; }
#contents ul { list-style: none; margin: .25rem 0; padding-left: 1rem; }
#contents > ul { padding-left: 0; }
#contents li { margin: .2rem 0; line-height: 1.45; }
#contents a { text-decoration: none; }
#contents a:hover { text-decoration: underline; }
.toc-part { font-weight: 700; margin: .9rem 0 .3rem; font-size: 1.02rem; }
.toc-th > a { font-weight: 600; color: #1f2937; }
.toc-flat li { display: inline; }
.toc-flat li + li::before { content: " · "; color: #94a3b8; }

/* chapters */
section.chapter { border-top: 1px dashed #cbd5e1; margin-top: 1.5rem; padding-top: .5rem; }
.h2k, .h1f { font-size: 1.9rem; margin: 1rem 0 .25rem; }
.h2a { font-size: 1.05rem; margin: 1.6rem 0 .25rem; }
.h3a { font-size: 1.05rem; font-style: italic; margin: 1rem 0 .4rem; }
.h3k { text-align: center; font-size: 1.55rem; margin: 2rem 0 .9rem; }
.h3k1 { text-align: center; font-size: 1.75rem; margin: 2rem 0 .7rem; }
.h4k, .h4f { font-size: .95rem; margin: 1.4rem 0 .3rem; }
.h5k { font-size: 1.15rem; margin: 1.4rem 0 .3rem; }
.half, .title { text-align: center; font-size: 2.2rem; margin: 1.5rem 0 0; }
.title1 { text-align: center; font-size: 1rem; margin: 0 0 2rem; }
.title2 { text-align: center; font-size: .95rem; color: #535554; margin: 1em 0; }
.title3 { text-align: center; font-size: 1.4rem; color: #535554; margin: 1.6em 0 1em; }
.copy { margin-top: 3em; }
.ack, .toc { font-size: 1.9rem; color: #1f2937; }
.h3k a, .h3k1 a, .h2k a { text-decoration: none; }

/* book text classes */
.grey { color: #535554; }
.green { color: #659031; }
.red { color: #b24e2c; }
.white, .color1 { color: #fffff0; }
.center { text-align: center; }
.right { text-align: right; }
.fontsize0 { font-size: .8em; }
.fontsize1 { font-size: .9em; }
.fontsizek1 { font-size: 1.05em; }
.fontsizek { font-size: 1.1em; }
.fontsize2 { font-size: 1.2em; }
.textStyle1a { margin-top: 1.1em; }
.textStyle1b { margin-top: 1.6em; }
.textStyle2, .textStyle2a, .textStyle2b, .textStyle2d, .textStyle2e,
.textStyle2f, .textStyle2f1, .textStyle3a, .textStyle3c
  { display: block; margin: 1.1em 0; text-align: center; }
.textStyle2f, .textStyle2f1 { font-size: .9em; text-align: left; }
.hangingparax { text-indent: -1em; margin-left: 1em; }
.floatparat { margin: .15em 0 .15em 3em; }
.floatstylet { float: left; margin-left: -1.5em; }
.floatstylet1 { float: left; margin-left: -1em; }
span.drop { float: left; font-size: 2.1em; line-height: 1; font-weight: 400;
            margin: .04em .12em 0 0; }
.coverpage { text-align: center; margin: 0; }
.coverpage .caption { display: none; }
img.cover { width: 100%; height: auto; }
.border { border-bottom: 1px solid #b85d3e; margin: 0 0 .3em; }
sup { font-size: .7em; }
blockquote { font-size: .92em; margin: 1em 1.5em; }
ul, ol { line-height: 1.55; }
li { margin: .2em 0; }

/* stat boxes */
div.boxc, div.boxk, div.boxk1 { background: #eceeee; border-radius: 1rem;
  padding: .9rem 1.15rem; margin: 1.1rem 0; font-size: .9rem; }
div.boxc p, div.boxk p, div.boxk1 p { margin: .3em 0; line-height: 1.5; }
div.box  { background: #f59326; color: #fffff0; border-radius: .4rem;
           padding: .8rem 1rem; margin: 1.4rem 0; }
div.boxp { background: #659031; color: #fffff0; border-radius: .4rem;
           padding: .8rem 1rem; margin: 1.4rem 0; }
div.boxr { background: #b24e2c; color: #fffff0; border-radius: .4rem;
           padding: .8rem 1rem; margin: 1.4rem 0; }
div.box a, div.boxp a, div.boxr a { color: #fffff0; }
div.box h1, div.boxp h1, div.boxr h1,
div.box h2, div.boxp h2, div.boxr h2 { color: #fffff0; }

/* images */
.imglink { display: inline-block; max-width: 100%; }
.imglink img { border-radius: .25rem; }
.caption { display: block; font-size: .8rem; color: #6b7280; font-style: italic;
           text-align: center; margin: .35rem auto 0; max-width: 36rem; }

/* printed-page markers */
.pg { font-size: .62rem; color: #b6bcc4; vertical-align: super;
      margin: 0 .18em; user-select: none; }
.pg:target { background: #fde68a; color: #92400e; }

/* prev/next */
.secnav { display: flex; justify-content: space-between; gap: 1rem;
          font-size: .85rem; margin-top: 2rem; padding-top: .6rem;
          border-top: 1px solid #e2e8f0; color: #94a3b8; }
.secnav a { text-decoration: none; }
.secnav .nav-next { text-align: right; margin-left: auto; }

/* floating contents button */
.backtotop { position: fixed; right: .9rem; bottom: .9rem; z-index: 10;
             background: rgba(31,41,55,.82); color: #fff; text-decoration: none;
             font-size: .8rem; padding: .45rem .75rem; border-radius: 9999px; }

@media print {
  .backtotop, .secnav { display: none; }
  a { color: inherit; text-decoration: none; }
  body { background: #fff; }
  section.chapter { break-inside: auto; }
}
"""

# Tags that XHTML may self-close but text/html must not (<span .../> would
# otherwise parse as an unclosed open tag and wreck the DOM nesting).
_NONVOID = r"span|a|div|p|b|i|em|strong|li|ul|ol|h[1-6]|section|nav|small|blockquote"


# --------------------------------------------------------------------------- #
# EPUB reading
# --------------------------------------------------------------------------- #
def read_epub(path):
    """(ordered spine Text filenames, {filename: xhtml}, {img name: bytes}, ncx)."""
    with zipfile.ZipFile(path) as z:
        opf = z.read("OEBPS/content.opf").decode("utf-8")
        manifest = {}
        for item in re.findall(r"<item\b[^>]*>", opf):
            iid = re.search(r'id="([^"]+)"', item)
            href = re.search(r'href="([^"]+)"', item)
            if iid and href:
                manifest[iid.group(1)] = href.group(1)
        spine = []
        for idref in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', opf):
            href = manifest.get(idref, "")
            if href.startswith("Text/") and href.endswith(".xhtml"):
                spine.append(os.path.basename(href))
        texts = {os.path.basename(n): z.read(n).decode("utf-8")
                 for n in z.namelist() if "/Text/" in n and n.endswith(".xhtml")}
        images = {os.path.basename(n): z.read(n)
                  for n in z.namelist() if "/Images/" in n}
        ncx = z.read("OEBPS/toc.ncx").decode("utf-8")
    return spine, texts, images, ncx


def ncx_labels(ncx):
    """{filename: first NCX label}, plus {filename: 'Part N: ...' label}."""
    first, part = {}, {}
    for label, src in re.findall(
            r"<navPoint[^>]*>.*?<text>(.*?)</text>.*?<content src=\"(.*?)\"",
            ncx, re.S):
        fname = os.path.basename(src.split("#")[0])
        label = html.unescape(label).strip()
        first.setdefault(fname, label)
        if re.match(r"Part\s+\d+\s*:", label, re.I):
            part[fname] = label
    return first, part


def hike_map(db_path):
    """{source_file: (hike_number, hike_name)} from guide_hikes (read-only)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT source_file, hike_number, name FROM guide_hikes").fetchall()
    conn.close()
    if not rows:
        sys.exit("guide_hikes is empty — run scripts/import_falcon_guide.py first.")
    return {sf: (num, name) for sf, num, name in rows}


# --------------------------------------------------------------------------- #
# Section classification & labels
# --------------------------------------------------------------------------- #
def title_case(label):
    """CRYSTAL LAKE TRAILHEAD -> Crystal Lake Trailhead (keeps connectives)."""
    small = {"of", "the", "and", "to", "at", "or"}
    out = []
    for w in label.split():
        lw = w.lower()
        if lw in small and out:
            out.append(lw)
        else:
            out.append(re.sub(r"[A-Za-z][a-z']*",
                              lambda m: m.group(0)[0].upper() + m.group(0)[1:],
                              lw))
    return " ".join(out)


def slugify(label):
    s = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return s or "section"


def classify_sections(spine, hikes_by_file, labels, part_labels):
    """Ordered section dicts: {file, stem, kind, anchor, label, toc_label}."""
    sections = []
    for fname in spine:
        stem = fname[:-len(".xhtml")]
        if stem == "nav":                      # EPUB nav — replaced by our TOC
            continue
        if fname in hikes_by_file:
            num, name = hikes_by_file[fname]
            label = f"{num}. {name}"
            sections.append(dict(file=fname, stem=stem, kind="hike",
                                 anchor=f"hike-{num}", label=label,
                                 toc_label=label, hike_number=num))
        elif re.match(r"Part\d+$", stem):
            pnum = int(stem[len("Part"):])
            label = part_labels.get(fname) or labels.get(fname) or f"Part {pnum}"
            sections.append(dict(file=fname, stem=stem, kind="part",
                                 anchor=f"part-{pnum}", label=label,
                                 toc_label=label, part_number=pnum))
        elif stem.startswith("Chapter"):       # un-numbered => trailhead section
            label = labels.get(fname, stem)
            sections.append(dict(file=fname, stem=stem, kind="trailhead",
                                 anchor=f"th-{slugify(label)}",
                                 label=title_case(label),
                                 toc_label=title_case(label)))
        else:                                  # front / back matter
            label = STEM_LABELS.get(stem) or title_case(labels.get(fname, stem))
            sections.append(dict(file=fname, stem=stem, kind="matter",
                                 anchor=f"sec-{stem}", label=label,
                                 toc_label=label))
    return sections


# --------------------------------------------------------------------------- #
# Body cleanup / rewriting
# --------------------------------------------------------------------------- #
def extract_body(xhtml):
    m = re.search(r"<body[^>]*>(.*)</body>", xhtml, re.S)
    body = m.group(1) if m else xhtml
    # drop the EPUB's own <section>/<nav> wrappers; we add our own.
    body = re.sub(r"</?(?:section|nav)\b[^>]*>", "", body)
    body = re.sub(r"<script\b.*?</script>", "", body, flags=re.S)
    return body.strip()


def clean_markup(body):
    # XHTML self-closed non-void tags -> explicit close (text/html safety).
    body = re.sub(rf"<({_NONVOID})\b([^>]*?)\s*/>", r"<\1\2></\1>", body)
    # EPUB/ARIA cruft.
    body = re.sub(r'\s+(?:role|aria-label|epub:type|xml:lang|xmlns(?::\w+)?)'
                  r'="[^"]*"', "", body)
    body = re.sub(r'class="([^"]*)"',
                  lambda m: 'class="{}"'.format(" ".join(
                      t for t in m.group(1).split() if t != "sigil_not_in_toc")),
                  body)
    body = body.replace(' class=""', "")
    # Printed-page markers: keep the anchors, show the page number subtly.
    body = re.sub(r'<span\s+id="page_(\d+)"\s*></span>',
                  r'<span class="pg" id="page_\1" '
                  r'title="printed page \1">\1</span>', body)
    return body


def rewrite_links(body, target_of):
    """EPUB-internal hrefs -> in-page anchors; external links -> new tab."""
    def repl(m):
        fname, frag = m.group(1), m.group(2)
        if fname == "nav.xhtml":
            return 'href="#contents"'
        if frag:                         # ids are preserved verbatim in-page
            return f'href="#{frag}"'
        return f'href="{target_of.get(fname, "#contents")}"'
    body = re.sub(r'href="(?:\.\./)?Text/([A-Za-z0-9]+\.xhtml)(?:#([^"]+))?"',
                  repl, body)
    body = re.sub(r'<a\b([^>]*href="(?:https?:|mailto:)[^"]*"[^>]*)>',
                  lambda m: "<a" + m.group(1) + ' target="_blank" rel="noopener">'
                  if "target=" not in m.group(1) else m.group(0), body)
    return body


def _norm_text(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip().lower()


def rewrite_images(body, images, visible_text):
    """Lazy-load every image and wrap it in a link to the raw file. An alt
    text that is a real caption is rendered visibly — but only when the book
    does NOT already show the same text as a caption paragraph right next to
    the figure (most figures carry the caption twice: alt + <p><b>...</b>)."""
    def repl(m):
        tag = m.group(0)
        src = re.search(r'src="[^"]*?([^"/]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        cls = re.search(r'class="([^"]*)"', tag)
        fname = src.group(1) if src else ""
        if fname not in images:
            return tag
        alt_text = alt.group(1) if alt else ""
        cls_attr = f' class="{cls.group(1)}"' if cls else ""
        out = (f'<a class="imglink" href="images/{fname}" target="_blank" '
               f'title="Open full-resolution image">'
               f'<img loading="lazy" src="images/{fname}" '
               f'alt="{alt_text}"{cls_attr}></a>')
        if (alt_text and alt_text.lower() not in ("image", "cover")
                and _norm_text(alt_text) not in visible_text):
            out += f'<span class="caption">{alt_text}</span>'
        return out
    return re.sub(r"<img\b[^>]*>", repl, body)


# --------------------------------------------------------------------------- #
# Plain-text cross-reference linkification
# --------------------------------------------------------------------------- #
_HIKE_RUN = re.compile(
    r"\b([Hh]ikes?)("
    r"(?:\s*(?:,|and|through|[–—-])?\s*\d{1,3}\b(?!\.\d)"
    r"(?!\s*(?:more\b|mile|hour|minute|foot|feet|percent|km\b)))+"
    r")")
_PAGE_RUN = re.compile(
    r"\b([Pp]ages?)((?:\s*(?:,|and|[–—-])?\s*\d{1,3}\b(?!\.\d))+)")


def _link_numbers(run, valid, prefix):
    return re.sub(
        r"\d{1,3}",
        lambda m: (f'<a class="xref" href="#{prefix}{m.group(0)}">'
                   f"{m.group(0)}</a>") if int(m.group(0)) in valid
        else m.group(0),
        run)


def linkify_text(body, hike_numbers, page_numbers):
    """Linkify "Hike NN" / "page NN" runs in text nodes outside of <a>."""
    out, depth, stats = [], 0, [0, 0]
    for tok in re.split(r"(<[^>]+>)", body):
        if tok.startswith("<"):
            if re.match(r"<a\b", tok):
                depth += 1
            elif tok.startswith("</a"):
                depth = max(0, depth - 1)
            out.append(tok)
            continue
        if depth == 0 and tok:
            def hike_repl(m):
                linked = _link_numbers(m.group(2), hike_numbers, "hike-")
                stats[0] += linked.count("<a ")
                return m.group(1) + linked

            def page_repl(m):
                linked = _link_numbers(m.group(2), page_numbers, "page_")
                stats[1] += linked.count("<a ")
                return m.group(1) + linked
            tok = _HIKE_RUN.sub(hike_repl, tok)
            tok = _PAGE_RUN.sub(page_repl, tok)
        out.append(tok)
    return "".join(out), stats[0], stats[1]


def inject_anchor(body, anchor):
    """Put the section's stable id on its first heading (fallback: none —
    the wrapping <section> carries a sec-<stem> id regardless)."""
    m = re.search(r"<h[1-6]\b[^>]*>", body)
    if not m or re.search(r'\bid="', m.group(0)):
        return body, False
    tag = m.group(0)[:-1] + f' id="{anchor}">'
    return body[:m.start()] + tag + body[m.end():], True


# --------------------------------------------------------------------------- #
# Page assembly
# --------------------------------------------------------------------------- #
def build_toc(sections):
    front, parts, back = [], [], []
    cur_part = cur_th = None
    for s in sections:
        if s["kind"] == "part":
            cur_part = dict(section=s, children=[])
            cur_th = None
            parts.append(cur_part)
        elif s["kind"] == "trailhead":
            cur_th = dict(section=s, hikes=[])
            cur_part["children"].append(cur_th)
        elif s["kind"] == "hike":
            if cur_th:
                cur_th["hikes"].append(s)
            else:
                cur_part["children"].append(dict(section=s, hikes=None))
        else:
            (parts and back or front).append(s)

    def link(s):
        return f'<a href="#{s["anchor"]}">{html.escape(s["toc_label"])}</a>'

    out = ['<nav id="contents">', "<h2>Contents</h2>"]
    out.append('<ul class="toc-flat">')
    out.extend(f"<li>{link(s)}</li>" for s in front)
    out.append("</ul>")
    for p in parts:
        out.append(f'<div class="toc-part">{link(p["section"])}</div>')
        out.append("<ul>")
        for child in p["children"]:
            if child["hikes"] is None:               # hike directly under part
                out.append(f"<li>{link(child['section'])}</li>")
            else:
                out.append(f'<li class="toc-th">{link(child["section"])}')
                if child["hikes"]:
                    out.append("<ul>")
                    out.extend(f"<li>{link(h)}</li>" for h in child["hikes"])
                    out.append("</ul>")
                out.append("</li>")
        out.append("</ul>")
    out.append('<ul class="toc-flat">')
    out.extend(f"<li>{link(s)}</li>" for s in back)
    out.append("</ul>")
    out.append("</nav>")
    return "\n".join(out)


def secnav_html(prev_s, next_s):
    parts = ['<div class="secnav">']
    if prev_s:
        parts.append(f'<a class="nav-prev" href="#{prev_s["anchor"]}">'
                     f'&larr; {html.escape(prev_s["label"][:48])}</a>')
    parts.append('<a href="#contents">&uarr; Contents</a>')
    if next_s:
        parts.append(f'<a class="nav-next" href="#{next_s["anchor"]}">'
                     f'{html.escape(next_s["label"][:48])} &rarr;</a>')
    parts.append("</div>")
    return "".join(parts)


def render(sections, texts, images, hike_numbers, page_numbers):
    target_of = {s["file"]: "#" + s["anchor"] for s in sections}
    n_hike_x = n_page_x = 0
    rendered = []
    for i, s in enumerate(sections):
        body = extract_body(texts[s["file"]])
        body = clean_markup(body)
        body = rewrite_links(body, target_of)
        visible_text = _norm_text(re.sub(r"<[^>]+>", " ", body))
        body = rewrite_images(body, images, visible_text)
        body, hx, px = linkify_text(body, hike_numbers, page_numbers)
        n_hike_x += hx
        n_page_x += px
        body, on_heading = inject_anchor(body, s["anchor"])
        sec_id = s["anchor"] if not on_heading else "sec-" + s["stem"]
        prev_s = sections[i - 1] if i else None
        next_s = sections[i + 1] if i + 1 < len(sections) else None
        rendered.append(f'<section class="chapter" id="{sec_id}">\n{body}\n'
                        f"{secnav_html(prev_s, next_s)}\n</section>")
    return rendered, n_hike_x, n_page_x


def page_html(toc, rendered):
    body = "\n".join(rendered)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Hiking Utah&rsquo;s High Uintas &mdash; 3rd ed.</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
<h1 class="site-title">Hiking Utah&rsquo;s High Uintas &mdash; 3rd ed.</h1>
<div class="byline">Private copy of Jed&rsquo;s purchased book, for personal use
only &mdash; served via Tailscale only. Deep-link a hike with
<code>#hike-&lt;NN&gt;</code>, a printed page with <code>#page_&lt;NN&gt;</code>.
Tap any photo or map to open it full-resolution.</div>
{toc}
<main id="book">
{body}
</main>
</div>
<a class="backtotop" href="#contents">&uarr; Contents</a>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Output writing (idempotent: only touches files whose bytes change)
# --------------------------------------------------------------------------- #
def write_if_changed(path, data):
    if os.path.exists(path):
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def copy_images(images):
    os.makedirs(IMG_DIR, exist_ok=True)
    written = 0
    for fname in sorted(images):
        if write_if_changed(os.path.join(IMG_DIR, fname), images[fname]):
            written += 1
    stale = set(os.listdir(IMG_DIR)) - set(images)
    for fname in stale:
        os.unlink(os.path.join(IMG_DIR, fname))
    return written, len(stale)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    if not os.path.exists(EPUB_PATH):
        sys.exit(f"EPUB not found: {EPUB_PATH}\n"
                 "It is gitignored — decrypt the purchased Kobo copy first.")

    spine, texts, images, ncx = read_epub(EPUB_PATH)
    labels, part_labels = ncx_labels(ncx)
    hikes_by_file = hike_map(DB_PATH)
    sections = classify_sections(spine, hikes_by_file, labels, part_labels)

    hikes = [s for s in sections if s["kind"] == "hike"]
    assert len(hikes) == 90, f"expected 90 hikes, found {len(hikes)}"
    hike_numbers = {s["hike_number"] for s in hikes}
    page_numbers = {int(n) for t in texts.values()
                    for n in re.findall(r'id="page_(\d+)"', t)}

    toc = build_toc(sections)
    rendered, n_hike_x, n_page_x = render(
        sections, texts, images, hike_numbers, page_numbers)
    doc = page_html(toc, rendered).encode("utf-8")

    # Every internal href must resolve to an id on the page.
    ids = set(re.findall(r'id="([^"]+)"', doc.decode("utf-8")))
    internal = re.findall(r'href="#([^"]+)"', doc.decode("utf-8"))
    missing = sorted({h for h in internal if h not in ids})
    assert not missing, f"unresolved in-page anchors: {missing[:10]}"

    os.makedirs(OUT_DIR, exist_ok=True)
    html_changed = write_if_changed(OUT_HTML, doc)
    img_written, img_pruned = copy_images(images)

    total = os.path.getsize(OUT_HTML) + sum(
        os.path.getsize(os.path.join(IMG_DIR, f)) for f in os.listdir(IMG_DIR))
    kinds = {k: sum(1 for s in sections if s["kind"] == k)
             for k in ("matter", "part", "trailhead", "hike")}
    print(f"Sections: {len(sections)} "
          f"({kinds['part']} parts, {kinds['trailhead']} trailheads, "
          f"{kinds['hike']} hikes, {kinds['matter']} front/back matter)")
    print(f"Anchors: {len(ids)} ids; internal links: {len(internal)}, "
          f"all resolved")
    print(f"Cross-refs linkified: {n_hike_x} hike, {n_page_x} page")
    print(f"Images: {len(images)} copied verbatim "
          f"({img_written} written, {img_pruned} stale pruned)")
    print(f"index.html: {os.path.getsize(OUT_HTML):,} bytes "
          f"({'updated' if html_changed else 'unchanged'})")
    print(f"Total output: {total / 1e6:.1f} MB in {OUT_DIR}")


if __name__ == "__main__":
    main()
