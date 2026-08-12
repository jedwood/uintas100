#!/usr/bin/env python3
"""One-off extraction of CMA book photos -> cma_photos/pNNN-i.jpg.

Reads the original (uncompressed) PDF page by page, extracts embedded JPEG
image objects with pdfimages, drops anything under 200px on either edge
(decorative rules/bullets), resizes the rest to a max longest edge of 1200px
and re-saves at JPEG quality ~70 via sips, named by PRINTED page number
(pdf_page - 15) so export_cma_book.py can match them to <section id="cma-pN">.

Requires pdfimages/pdfinfo (poppler) and sips (macOS). Idempotent (wipes and
rebuilds cma_photos/ each run). Output is gitignored (copyright) — re-run any
time the source PDF is available; see docs/cma-book-media-plan.md.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PDF_PATH = os.path.join(PROJECT_DIR, "data", "the-high-uinta-mountains-by-cma.pdf")
OUT_DIR = os.path.join(PROJECT_DIR, "cma_photos")
PAGE_OFFSET = 15
MIN_DIM = 200
MAX_EDGE = 1200
JPEG_QUALITY = 70

def get_page_count():
    out = subprocess.run(["pdfinfo", PDF_PATH], capture_output=True, text=True, check=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1))

def list_images():
    """page -> list of (obj_num) for jpeg-encoded images >= MIN_DIM."""
    out = subprocess.run(["pdfimages", "-list", PDF_PATH], capture_output=True, text=True, check=True).stdout
    pages = {}
    for line in out.splitlines()[2:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        page, num, typ = parts[0], parts[1], parts[2]
        if typ != "image":
            continue
        try:
            width, height = int(parts[3]), int(parts[4])
        except ValueError:
            continue
        enc = parts[8]
        if enc != "jpeg":
            continue
        if width < MIN_DIM or height < MIN_DIM:
            continue
        pages.setdefault(int(page), []).append(int(num))
    return pages

def sips_dims(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                          capture_output=True, text=True).stdout
    w = h = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            w = int(line.split(":")[1].strip())
        elif line.startswith("pixelHeight:"):
            h = int(line.split(":")[1].strip())
    return w, h

def optimize(src, dst):
    w, h = sips_dims(src)
    if w is None:
        return False
    longest = max(w, h)
    args = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(JPEG_QUALITY)]
    if longest > MAX_EDGE:
        args += ["--resampleHeightWidthMax", str(MAX_EDGE)]
    args += [src, "--out", dst]
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode == 0

def main():
    if not os.path.exists(PDF_PATH):
        sys.exit(f"Book PDF not found at {PDF_PATH} (it is gitignored and "
                 "lives only on the Mini) — nothing to do.")
    for tool in ("pdfinfo", "pdfimages", "sips"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found on PATH")
    total_pages = get_page_count()
    pages = list_images()
    print(f"PDF has {total_pages} pages; {len(pages)} pages carry qualifying (>= {MIN_DIM}px) jpeg photos, "
          f"{sum(len(v) for v in pages.values())} images total", file=sys.stderr)

    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    kept = 0
    kept_bytes = 0
    tmpdir = tempfile.mkdtemp(prefix="cma_extract_")
    try:
        for i, page in enumerate(sorted(pages)):
            printed = page - PAGE_OFFSET
            if printed < 1:
                continue  # front matter, no section to attach to
            page_tmp = os.path.join(tmpdir, "img")
            subprocess.run(["pdfimages", "-j", "-p", "-f", str(page), "-l", str(page),
                             PDF_PATH, page_tmp], check=True, capture_output=True)
            # Only the .jpg outputs matter (jpeg-encoded objects); ppm/pbm are
            # non-jpeg objects (masks/index images) pdfimages also dumps by
            # default -- delete those immediately, they're not photos.
            jpgs = sorted(f for f in os.listdir(tmpdir) if f.endswith(".jpg"))
            idx = 0
            for jf in jpgs:
                src = os.path.join(tmpdir, jf)
                w, h = sips_dims(src)
                if w is None or w < MIN_DIM or h < MIN_DIM:
                    os.unlink(src)
                    continue
                idx += 1
                dst = os.path.join(OUT_DIR, f"p{printed}-{idx}.jpg")
                if optimize(src, dst):
                    kept += 1
                    kept_bytes += os.path.getsize(dst)
                os.unlink(src)
            # clean any leftover non-jpg extraction artifacts for this page
            for f in os.listdir(tmpdir):
                os.unlink(os.path.join(tmpdir, f))
            if (i + 1) % 50 == 0:
                print(f"  ...{i+1}/{len(pages)} pages processed, {kept} photos kept so far, "
                      f"{kept_bytes/1024/1024:.1f} MB", file=sys.stderr)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"Done: {kept} photos, {kept_bytes/1024/1024:.1f} MB in {OUT_DIR}", file=sys.stderr)

if __name__ == "__main__":
    main()
