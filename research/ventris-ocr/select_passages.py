"""Pick the ~60 pilot passages from candidates.json (see build_candidates.py) and write PASSAGES.csv + crop PNGs.

Quotas (design: research/peiresc-tool-survey/04-ocr.md, branch claude/peiresc-tool-survey): 30 hard + 30 clean.
  hard: 14 land-description fractions, 6 section symbols, 6 digit-heavy tables, 4 two-column spans.
  clean: 12 Federal Register, 9 Statutes at Large, 9 Serial Set.
Selection is by CONTENT FEATURES read from the text layer (fraction-like tokens, the section sign, digit share); the
layer's accuracy is not scored here. This does bias "hard" toward places where such tokens exist; the README says so.
At most 2 passages per source file, none overlapping. Ties break by a seeded shuffle (seed 20261106).
Run: C:/Users/danie/eo-venvs/ocr/Scripts/python.exe -I select_passages.py
"""
import csv, json, os, random, re, sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pagetools as P

HERE = os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(20261106)
cands = json.load(open(P.WORK + "/candidates.json"))
manifest = {m["sha256"]: m for m in (json.loads(l) for l in open(HERE + "/SOURCES_MANIFEST.jsonl")) if m.get("sha256")}
used = []
per_key = {}
chosen = []


def overlaps(c):
    for u in used:
        if u["sha256"] == c["sha256"] and u["page"] == c["page"]:
            a, b = u["box"], c["box"]
            if not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]):
                return True
    return False


import numpy as np
from PIL import Image as _Image
_ink = {}


def page_ink(c):
    k = (c["sha256"], c["page"])
    if k not in _ink:
        _ink[k] = np.array(_Image.open(P.page_png_path(*k)).convert("L")) < 140
    return _ink[k]


def snap(c):
    """Move the top and bottom edges to the nearest ink-free row (so no text line is cut) and reject the window when
    text touches its left or right edge (a table or line running past the column cut). Returns a box or None."""
    ink = page_ink(c)
    x0, y0, x1, y1 = [int(v) for v in c["box"]]
    h = ink.shape[0]
    gapmax = max(12, int(0.015 * (x1 - x0)))
    rp = ink[:, x0:x1].sum(axis=1)

    def nearest(y, direction):
        for d in range(0, 45):
            yy = y + direction * d
            if 0 <= yy < h and rp[yy] <= gapmax:
                return yy
        return None

    ny0, ny1 = nearest(y0, -1), nearest(y1, +1)
    if ny0 is None or ny1 is None:
        return None
    w = ink.shape[1]
    if c.get("ncols", 1) > 1:
        # a column cut at a gutter: reject when text touches the cut
        if ink[ny0:ny1, x0:x0 + 3].mean() > 0.004 or ink[ny0:ny1, x1 - 3:x1].mean() > 0.004:
            return None
    else:
        # a single-column page: widen outward to the nearest ink-free strip so no margin letter is clipped
        def free(x):
            return ink[ny0:ny1, max(0, x - 1):x + 2].sum() == 0
        for d in range(0, 90):
            if x0 - d >= 0 and free(x0 - d):
                x0 -= d
                break
        for d in range(0, 90):
            if x1 + d < w and free(x1 + d):
                x1 += d
                break
    return (x0, ny0, x1, ny1)


def take(pool, n, cat, sub, maxper=2, keyfn=None):
    pool = pool[:]
    rnd.shuffle(pool)
    if keyfn:
        pool.sort(key=keyfn)
    got = 0
    for c in pool:
        if got >= n:
            break
        if per_key.get(c["key"], 0) >= maxper or overlaps(c):
            continue
        sb = snap(c)
        if sb is None:
            continue
        c = {**c, "box": sb}
        if overlaps(c):
            continue
        per_key[c["key"]] = per_key.get(c["key"], 0) + 1
        used.append(c)
        chosen.append({**c, "category": cat, "sub": sub})
        got += 1
    return got


def is_fr(x):
    return x["key"].startswith("FR-")


fr_land = [c for c in cands if is_fr(c) and c["frac"] >= 3 and 8 <= c["nlines"] <= 12 and int(c["key"][3:7]) >= 1949]
take(fr_land, 14, "hard", "fractions in land description", keyfn=lambda c: -c["frac"])
sec = [c for c in cands if c["frac"] < 3 and c["nlines"] <= 12 and c["key"] not in ()]
# the section sign: require the text layer to carry it at least twice
import pagetools
pdfs = {}
sec_pool = []
for c in cands:
    if c["sec"] >= 2 and c["nlines"] <= 12 and c["frac"] < 3:
        pdf = pdfs.setdefault(c["sha256"], P.open_pdf(c["sha256"]))
        if P.layer_text(pdf, c["page"], tuple(c["box"])).count("\u00a7") >= 2:
            sec_pool.append(c)
take(sec_pool, 6, "hard", "section symbols")
tab = [c for c in cands if c["digit_share"] >= 0.18 and c["frac"] < 3 and c["nlines"] <= 16]
take(tab, 6, "hard", "digit-heavy table or schedule", maxper=3)
# clean
clean = [c for c in cands if c["frac"] == 0 and c["sec"] == 0 and c["digit_share"] < 0.06 and c["word_share"] >= 0.55
         and c["nlines"] in (8, 12)]
take([c for c in clean if is_fr(c)], 12, "clean", "plain prose", maxper=3)
take([c for c in clean if c["key"].startswith("STATUTE")], 9, "clean", "plain prose")
take([c for c in clean if c["key"].startswith("SERIAL")], 9, "clean", "plain prose", maxper=3)

# two-column spans: same line window across two adjacent columns of a 3-column FR page
by_page = {}
for c in cands:
    if is_fr(c) and c["ncols"] == 3 and c["nlines"] == 8 and int(c["key"][3:7]) >= 1949:
        by_page.setdefault((c["sha256"], c["page"]), {}).setdefault(c["col"], []).append(c)
pool = []
for (sha, pg), cols in by_page.items():
    for a in cols.get(0, []):
        for b in cols.get(1, []):
            if abs(a["box"][1] - b["box"][1]) < 30 and a["frac"] + b["frac"] >= 1:
                pool.append({**a, "box": (a["box"][0], min(a["box"][1], b["box"][1]), b["box"][2],
                                          max(a["box"][3], b["box"][3])), "ncols": 2, "col": "0+1"})
take(pool, 4, "hard", "two adjacent columns in one crop", maxper=3)

rows = []
for i, c in enumerate(sorted(chosen, key=lambda c: (c["category"], c["key"], c["page"], c["box"][1])), 1):
    pid = f"P{i:03d}"
    m = manifest[c["sha256"]]
    pdf = pdfs.setdefault(c["sha256"], P.open_pdf(c["sha256"]))
    png, w, h = P.render_page(pdf, c["sha256"], c["page"])
    box = tuple(int(v) for v in c["box"])
    os.makedirs(P.WORK + "/crops", exist_ok=True)
    cpath = P.WORK + f"/crops/{pid}.png"
    Image.open(png).crop(box).save(cpath)
    layer = P.layer_text(pdf, c["page"], box)
    rows.append({"id": pid, "category": c["category"], "subtype": c["sub"], "source_key": c["key"],
                 "source_kind": m["kind"], "source_url": m["final_url"] if m["kind"] == "statute" else m["url"],
                 "source_sha256": c["sha256"], "pdf_page": c["page"], "dpi": P.DPI,
                 "page_png_sha256": P.sha256_file(png), "crop_box_px": ",".join(map(str, box)),
                 "crop_png_sha256": P.sha256_file(cpath), "crop_png_path": cpath,
                 "why_chosen": f"{c['sub']}; {c['nlines']} lines; layer features frac={c['frac']} sec={c['sec']} "
                               f"digit_share={c['digit_share']} word_share={c['word_share']}",
                 "gpo_text_layer": layer})  # converted to JSON-escaped form by finalize_passages.py
with open(HERE + "/PASSAGES.csv", "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    wr.writeheader()
    wr.writerows(rows)
print(len(rows), "passages", {k: sum(r["category"] == k for r in rows) for k in ("hard", "clean")})
for r in rows:
    print(r["id"], r["category"], r["source_key"], r["pdf_page"], r["crop_box_px"], r["subtype"][:25])
