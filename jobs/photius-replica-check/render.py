"""Render the first and last page (and the second when there are three or more) of each replica PDF to PNG,
so a worker can look at the page when the text layer or OCR is poor. Output stays out of git.

    python -I jobs/photius-replica-check/render.py OUT_DIR [--dpi 130]
"""
import csv
import os
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.append(r"C:\Users\danie\AppData\Roaming\Python\Python312\site-packages")
REPO = Path(__file__).resolve().parents[2]
PDF_ROOT = Path(r"C:\Users\danie\Projects\Executive-Orders")  # the clone that holds the ProQuest PDFs
DPI = 130


def one(args):
    pdf, stem, out = args
    import pypdfium2 as pdfium
    try:
        d = pdfium.PdfDocument(str(pdf))
        n = len(d)
        want = {0: "first", n - 1: "last"}
        if n >= 3:
            want[1] = "second"
        for i, tag in want.items():
            p = out / f"{stem}_{tag}.png"
            if p.exists():
                continue
            d[i].render(scale=DPI / 72, grayscale=True).to_pil().save(p, format="PNG", compress_level=3)
        return stem, n, ""
    except Exception as exc:  # noqa: BLE001
        return stem, 0, repr(exc)[:120]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(REPO / "jobs/photius-replica-check/work/CANDIDATES.csv", encoding="utf-8")))
    tasks = [(PDF_ROOT / r["folder"] / r["file"], f"EO_{r['number']}{r['suffix']}", out) for r in rows]
    done = 0
    with Pool(max(2, os.cpu_count() - 2)) as pool:
        for stem, n, err in pool.imap(one, tasks, chunksize=4):
            done += 1
            if err:
                print("ERR", stem, err, flush=True)
            if done % 200 == 0:
                print(done, "rendered", flush=True)
    print("DONE", done)


if __name__ == "__main__":
    main()
