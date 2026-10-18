"""Write data/PRIORITY.txt: numbered census orders with no saved text of any kind.

Offline. Held = claim-kit's loaded texts plus readiness-tracker step_original_text=done.
The documents phase fetches these first (--ids-file); everything else follows.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "jobs/claim-kit"))
import inputs

corpus = inputs.load_corpus(str(ROOT))
held = {t["instrument_id"] for t in corpus["texts"]}
with open(ROOT / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", encoding="utf-8") as fh:
    held |= {r["instrument_id"] for r in csv.DictReader(fh) if r["step_original_text"] == "done"}
missing = sorted((i for i in corpus["universe"] if re.fullmatch(r"EO:\d+[A-Z]?", i) and i not in held),
                 key=lambda i: (int(re.search(r"\d+", i).group()), i))
out = Path(__file__).resolve().parent / "data/PRIORITY.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(missing) + "\n", encoding="utf-8", newline="\n")
print(f"{len(missing)} numbered orders without saved text -> {out.relative_to(ROOT)}")
