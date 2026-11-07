"""Choose the 15 passages the owner transcribes (Kean D-20261106-encyclopedie-ocr-reference).

Rule, fixed before any engine reading was looked at (it uses only PASSAGES.csv metadata and the crop images' edges):
  - candidates are category 'hard' whose crop has no ink touching the left or right edge (no clipped line ends);
  - strata and quotas: fractions in land description 7, section symbols 3, digit-heavy table 3, two adjacent columns 2;
  - inside a stratum, candidates are ordered by a seeded shuffle (seed 20261106) and the first N taken, at most 2 per
    source file, so the set spans pages and years.
Writes OWNER_SET.json (ids + rule) and adds edge_ink_px to PASSAGES.csv.
Run: C:/Users/danie/eo-venvs/ocr/Scripts/python.exe -I choose_owner_set.py
"""
import csv, json, os, random, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(HERE + "/PASSAGES.csv", newline="", encoding="utf-8")))
for r in rows:
    ink = np.array(Image.open(r["crop_png_path"]).convert("L")) < 140
    r["edge_ink_px"] = str(int(ink[:, :3].sum() + ink[:, -3:].sum()))
fields = list(rows[0].keys())
with open(HERE + "/PASSAGES.csv", "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=fields, lineterminator="
")
    wr.writeheader()
    wr.writerows(rows)

rnd = random.Random(20261106)
quota = [("fractions in land description", 7), ("section symbols", 3), ("digit-heavy table or schedule", 3),
         ("two adjacent columns in one crop", 2)]
chosen, per_key = [], {}
for sub, n in quota:
    pool = [r for r in rows if r["category"] == "hard" and r["subtype"] == sub and int(r["edge_ink_px"]) <= 6]
    rnd.shuffle(pool)
    got = 0
    for r in pool:
        if got >= n:
            break
        if per_key.get(r["source_key"], 0) >= 2:
            continue
        per_key[r["source_key"]] = per_key.get(r["source_key"], 0) + 1
        chosen.append(r["id"])
        got += 1
    print(sub, "wanted", n, "got", got, "pool", len(pool))
json.dump({"rule": __doc__.split("Rule,")[1].split("Writes")[0].strip(), "ids": sorted(chosen)},
          open(HERE + "/OWNER_SET.json", "w"), indent=1)
print(len(chosen), sorted(chosen))
