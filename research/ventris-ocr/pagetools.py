"""Rendering and text-layer access for the Ventris OCR pilot (pypdfium2 only).

DPI is fixed at 300 for every page image. Crop boxes are (x0, y0, x1, y1) pixels on that image, origin top-left.
The GPO text layer for a crop is the PDF's own embedded text, read with pdfium's bounded-text call
(`get_text_bounded`), which returns the characters whose boxes fall inside the crop in the order they appear in the PDF's
content stream. It is never edited.
"""
import hashlib
import os

import pypdfium2 as pdfium

DPI = 300
SCALE = DPI / 72.0
WORK = "C:/Users/danie/eo-ocr-work"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def open_pdf(sha):
    return pdfium.PdfDocument(os.path.join(WORK, "pdf", sha + ".pdf"))


def page_png_path(sha, page1):
    return os.path.join(WORK, "pages", f"{sha[:12]}_p{page1:04d}.png")


def render_page(pdf, sha, page1):
    """Render 1-based page at 300 DPI to PNG (cached). Returns (path, width_px, height_px)."""
    out = page_png_path(sha, page1)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pg = pdf[page1 - 1]
    if not os.path.exists(out):
        pg.render(scale=SCALE).to_pil().convert("RGB").save(out, optimize=False)
    w, h = pg.get_size()
    return out, round(w * SCALE), round(h * SCALE)


def px_to_pdf_box(pg, box):
    """Pixel crop box on the 300-DPI render -> pdfium bounded-text rect (left, bottom, right, top) in page space."""
    w, h = pg.get_size()
    x0, y0, x1, y1 = box
    return (x0 / SCALE, h - y1 / SCALE, x1 / SCALE, h - y0 / SCALE)


def layer_text(pdf, page1, box):
    pg = pdf[page1 - 1]
    tp = pg.get_textpage()
    l, b, r, t = px_to_pdf_box(pg, box)
    return tp.get_text_bounded(left=l, bottom=b, right=r, top=t)


def layer_words_boxes(pdf, page1):
    """Return list of (char, x0, y0, x1, y1) in 300-DPI pixel coordinates for every char in the text layer."""
    pg = pdf[page1 - 1]
    tp = pg.get_textpage()
    w, h = pg.get_size()
    out = []
    n = tp.count_chars()
    txt = tp.get_text_range(0, n)
    for i in range(min(n, len(txt))):
        l, b, r, t = tp.get_charbox(i)
        out.append((txt[i], l * SCALE, (h - t) * SCALE, r * SCALE, (h - b) * SCALE))
    return out
