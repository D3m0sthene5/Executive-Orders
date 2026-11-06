"""Photius Lane 1: page-level text for the twelve GPO bound slip-order volumes.

For every page: the PDF's own text layer (pdfium), a local Tesseract read of a 300-dpi grayscale render, and
the SHA-256 of that render (PNG). Output: one JSONL per chunk of pages under OUT/<stem>/chunk_<start>.jsonl,
resumable (existing chunks are skipped). Runs every CPU thread minus two.
"""
import hashlib
import io
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS / "ocr" / "python"))
sys.path.append(r"C:\Users\danie\AppData\Roaming\Python\Python312\site-packages")
os.environ.setdefault("OMP_THREAD_LIMIT", "1")

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\danie\Downloads")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else TOOLS.parent / "gpo"
CHUNK = 20
DPI = 300
FILES = sorted(p for p in SRC.glob("*.pdf") if p.stem.startswith(("hvd.hl27", "mdp.39015087537612")))


def work(task):
    pdf, start, end = task
    import pypdfium2 as pdfium
    import tesserocr
    rows = []
    doc = pdfium.PdfDocument(str(pdf))
    with tesserocr.PyTessBaseAPI(path=str(TOOLS / "ocr" / "tessdata"), lang="eng") as api:
        for i in range(start, end):
            page = doc[i]
            layer = page.get_textpage().get_text_range()
            img = page.render(scale=DPI / 72, grayscale=True).to_pil()
            buf = io.BytesIO()
            img.save(buf, format="PNG", compress_level=1)
            png_sha = hashlib.sha256(buf.getvalue()).hexdigest()
            api.SetImage(img)
            ocr = api.GetUTF8Text()
            conf = api.MeanTextConf()
            rows.append({"page_index": i, "layer": layer, "ocr": ocr, "ocr_mean_conf": conf,
                         "render_png_sha256": png_sha, "width": img.width, "height": img.height})
    out = OUT / pdf.stem / f"chunk_{start:05d}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out)
    return (pdf.stem, start, end)


def main():
    import pypdfium2 as pdfium
    tasks = []
    for pdf in FILES:
        n = len(pdfium.PdfDocument(str(pdf)))
        (OUT / pdf.stem).mkdir(parents=True, exist_ok=True)
        (OUT / pdf.stem / "PAGES").write_text(str(n))
        for s in range(0, n, CHUNK):
            if not (OUT / pdf.stem / f"chunk_{s:05d}.jsonl").exists():
                tasks.append((pdf, s, min(n, s + CHUNK)))
    print(f"{len(FILES)} volumes, {len(tasks)} chunks to do", flush=True)
    t0 = time.time()
    done = 0
    with Pool(max(2, os.cpu_count() - 2)) as pool:
        for stem, s, e in pool.imap_unordered(work, tasks):
            done += 1
            if done % 10 == 0 or done == len(tasks):
                print(f"{done}/{len(tasks)} chunks, {time.time() - t0:.0f}s, last {stem} {s}-{e}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
