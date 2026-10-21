"""PDF facts and text for the ProQuest replica scans, shared by Pinakes (ingest) and Lewis.

inspect_pdf reads a file's bytes, hash, signature, page count and embedded text layer (pypdf).
text_quality scores a text layer: a handwritten original's OCR layer is noise (near 0); a typed or
printed order's layer reads as words (0.6 and up). ocr_pdf renders pages with pdftoppm and reads them
with tesseract when those programs are installed; it returns '' and a reason otherwise. Nothing here
decides what a document is.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile

try:
    import pypdf
except Exception:  # pragma: no cover
    pypdf = None

TEXT_QUALITY_MIN = 0.55      # share of tokens shaped like words
COMMON_SHARE_MIN = 0.40      # share of words that are common English or order vocabulary
TEXT_CHARS_MIN = 80
# OCR of handwriting yields word-shaped nonsense ("Clans we tn rehlllon apart"); real prose is 45-60% these words.
COMMON_WORDS = frozenset("""the of and to in a is that by for it as be or are from with this on at which an any such shall
have has not will all their its they may his he was were been under than other upon said hereby order orders executive
president united states section act public land lands reserved reservation war department secretary service civil
following described within between thereof therefore provided herein whereas authority vested me law laws rules rule part
parts no date day year congress government officers officer duties office persons person made make given each above being
further directed house white general navy army territory state county township range east west north south meridian
pursuant amended revoked set apart purposes use same so one two three four five six when until after before""".split())


def text_quality(text):
    """Share of tokens that are plain words of 2+ letters (0-1)."""
    tokens = re.findall(r"\S+", text or "")
    if not tokens:
        return 0.0
    words = sum(1 for t in tokens if re.fullmatch(r"[A-Za-z][a-z]+[.,;:]?", t) and len(t) >= 2)
    return round(words / len(tokens), 3)


def common_share(text):
    """Share of alphabetic tokens that are common English or order vocabulary (0-1)."""
    toks = [t.lower() for t in re.findall(r"[A-Za-z]+", text or "")]
    if not toks:
        return 0.0
    return round(sum(t in COMMON_WORDS for t in toks) / len(toks), 3)


def usable(text_chars, quality, common=None):
    """A text is usable when it is long enough, word-shaped, and (when measured) reads as English."""
    if (quality or 0) < TEXT_QUALITY_MIN or (text_chars or 0) < TEXT_CHARS_MIN:
        return False
    return common is None or common >= COMMON_SHARE_MIN


def inspect_pdf(path, max_pages_text=80):
    with open(path, "rb") as fh:
        data = fh.read()
    info = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "pdf_signature": data[:5] == b"%PDF-",
            "pages": None, "text_chars": None, "text_quality": None, "common_share": None, "text": "", "pdf_error": ""}
    if not info["pdf_signature"]:
        return info
    if pypdf is None:
        info["pdf_error"] = "pypdf not installed; pages and text layer not read"
        return info
    try:
        reader = pypdf.PdfReader(path)
        info["pages"] = len(reader.pages)
        parts = []
        for page in reader.pages[:max_pages_text]:
            try:
                parts.append(page.extract_text() or "")
            except Exception as exc:
                parts.append("")
                info["pdf_error"] = f"page text error: {type(exc).__name__}"
        text = "\n".join(parts).strip()
        info["text_chars"] = len(text)
        info["text_quality"] = text_quality(text)
        info["common_share"] = common_share(text)
        info["text"] = text
    except Exception as exc:
        info["pdf_error"] = f"{type(exc).__name__}: {exc}"[:200]
    return info


def ocr_available():
    return bool(shutil.which("pdftoppm") and shutil.which("tesseract"))


def ocr_pdf(path, max_pages=40, dpi=200, timeout=240):
    """OCR a PDF page by page. Returns (text, pages_done, error)."""
    if not ocr_available():
        return "", 0, "pdftoppm or tesseract not installed"
    work = tempfile.mkdtemp(prefix="eo-ocr-")
    try:
        prefix = os.path.join(work, "p")
        r = subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-l", str(max_pages), "-png", path, prefix],
                           capture_output=True, text=True, timeout=timeout)
        if r.returncode:
            return "", 0, "pdftoppm: " + (r.stderr or "")[-200:]
        pages = sorted(f for f in os.listdir(work) if f.endswith(".png"))
        texts = []
        env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
        for png in pages:
            t = subprocess.run(["tesseract", os.path.join(work, png), "stdout", "-l", "eng", "--psm", "6"],
                               capture_output=True, text=True, timeout=timeout, env=env)
            texts.append(t.stdout if t.returncode == 0 else "")
        text = "\n\f\n".join(texts).strip()
        return text, len(pages), ""
    except subprocess.TimeoutExpired:
        return "", 0, "ocr timeout"
    except Exception as exc:
        return "", 0, f"{type(exc).__name__}: {exc}"[:200]
    finally:
        shutil.rmtree(work, ignore_errors=True)
