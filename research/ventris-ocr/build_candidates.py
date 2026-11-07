"""Render the pilot's pages at 300 DPI, split them into columns and line windows, and score each window from the
text layer. Output: WORK/candidates.json (not committed; PASSAGES.csv is the committed selection).
Run: C:/Users/danie/eo-venvs/ocr/Scripts/python.exe -I build_candidates.py
"""
import json, re, subprocess, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/danie/eo-wt/enc-ocr/research/ventris-ocr")
import pagetools as P

REPO = "C:/Users/danie/eo-wt/enc-ocr"
SERIAL_PAGES = {"SERIALSET-08950_00_00-002-0017-0000": [60, 62, 64], "SERIALSET-09097_00_00-002-0377-0000": [79, 81, 83],
                "SERIALSET-09300_00_00-002-0207-0000": [80, 83], "SERIALSET-07878_00_00-002-0867-0000": [139, 141, 143],
                "SERIALSET-07070_00_00-002-0030-0000": [113, 119, 124]}


def jl(path):
    t = subprocess.run(["git", "-C", REPO, "show", "origin/main:" + path], capture_output=True, text=True,
                       encoding="utf-8", check=True).stdout
    return [json.loads(l) for l in t.splitlines() if l.strip()]


def page_list(manifest):
    pages = []
    fp = {r["issue_url"]: r["issue_pdf_pages"] for r in jl("jobs/fr-pages/output/SOURCES.jsonl")}
    fo = {}
    for r in jl("jobs/fr-originals/output/SOURCES.jsonl"):
        m = re.search(r"PDF pages (\d+)-(\d+)", r.get("page_or_item", ""))
        if m:
            fo.setdefault(r["url"], (int(m.group(1)), int(m.group(2))))
    for m in manifest:
        k = m["key"]
        if m["kind"] == "fr_issue":
            rng = fp.get(m["url"]) or fo.get(m["url"])
            for p in range(rng[0], rng[1] + 1):
                pages.append((m, p))
        elif m["kind"] == "statute":
            n = len(P.open_pdf(m["sha256"]))
            for p in range(1, min(n, 3) + 1):
                pages.append((m, p))
        else:
            for p in SERIAL_PAGES[k]:
                pages.append((m, p))
    return pages


def runs(mask, min_len):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        if not v and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    if start is not None and len(mask) - start >= min_len:
        out.append((start, len(mask)))
    return out


def columns(ink, width, split=True):
    """Column x-ranges from the vertical ink profile of the page interior (the scan's black border is ignored):
    a gutter is a run of at least 14 px whose smoothed ink is under 55% of the interior median. The outer edges are the
    first and last x with text ink (so no letter at the margin is clipped). split=False returns one column."""
    lo, hi = int(width * 0.035), int(width * 0.965)
    prof = ink[:, lo:hi].sum(axis=0).astype(float)
    prof = np.convolve(prof, np.ones(9) / 9, mode="same")
    thr = 0.55 * np.median(prof)
    inked = np.where(prof >= thr)[0]
    left, right = int(max(0, inked[0] + lo - 10)), int(min(width, inked[-1] + lo + 10))
    gut = [(a + lo, b + lo) for a, b in runs(prof < thr, 14)] if split else []
    gut = [g for g in gut if left + 40 < (g[0] + g[1]) / 2 < right - 40 and width * 0.15 < (g[0] + g[1]) / 2 < width * 0.85]
    cuts = [left] + [(a + b) // 2 for a, b in gut] + [right]
    cols = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
    return [c for c in cols if c[1] - c[0] > width * 0.15]


FRAC = re.compile(r"[A-Z]{1,3}[y\dl%i/]{1,2}4|\u00bc|\u00bd|\u00be|%4|[A-Z]{1,2}\s?%")
SEC = re.compile(r"\u00a7|\bSec\.|\bSECTION\b")


def score_text(t):
    words = re.findall(r"\S+", t)
    n = max(1, len(words))
    common = sum(1 for w in words if re.fullmatch(r"[a-z]{3,}[.,;:]?", w))
    digits = sum(c.isdigit() for c in t)
    return {"chars": len(t), "frac": len(FRAC.findall(t)), "sec": len(SEC.findall(t)),
            "word_share": round(common / n, 3), "digit_share": round(digits / max(1, len(t)), 3)}


def main():
    manifest = [json.loads(l) for l in open("C:/Users/danie/eo-wt/enc-ocr/research/ventris-ocr/SOURCES_MANIFEST.jsonl")]
    manifest = [m for m in manifest if m.get("sha256")]
    cands = []
    pdfs = {}
    for m, p in page_list(manifest):
        pdf = pdfs.setdefault(m["sha256"], P.open_pdf(m["sha256"]))
        path, w, h = P.render_page(pdf, m["sha256"], p)
        im = np.array(Image.open(path).convert("L"))
        ink = im < 140
        cols = columns(ink[int(h * 0.04):int(h * 0.96)], w, split=m['key'].startswith('FR-'))
        for ci, (cx0, cx1) in enumerate(cols):
            sub = ink[:, cx0:cx1]
            rowp = sub.sum(axis=1)
            bands = runs(rowp > max(10, 0.10 * np.percentile(rowp, 90)), 12)
            # merge bands separated by < 3 px (accents, fractions)
            merged = []
            for b in bands:
                if merged and b[0] - merged[-1][1] < 3:
                    merged[-1] = (merged[-1][0], b[1])
                else:
                    merged.append(b)
            lines = [b for b in merged if b[1] - b[0] >= 14]
            for n in (8, 12, 16):
                step = max(2, n // 2)
                for i in range(0, max(1, len(lines) - n + 1), step):
                    grp = lines[i:i + n]
                    if len(grp) < min(n, 6):
                        continue
                    box = (cx0, max(0, grp[0][0] - 12), cx1, min(h, grp[-1][1] + 12))
                    t = P.layer_text(pdf, p, box)
                    cands.append({"key": m["key"], "sha256": m["sha256"], "page": p, "col": ci, "ncols": len(cols),
                                  "box": box, "nlines": len(grp), **score_text(t)})
        print(m["key"], p, w, h, "cols", len(cols), flush=True)
    json.dump(cands, open(P.WORK + "/candidates.json", "w"))
    print(len(cands), "candidate windows")


if __name__ == "__main__":
    main()
