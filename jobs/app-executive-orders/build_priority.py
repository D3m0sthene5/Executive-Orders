"""Write data/PRIORITY.txt: numbered census orders with no saved text of any kind.

Offline. Held = claim-kit's loaded texts, readiness-tracker step_original_text=done, and this
job's own texts (live FRAGMENTS.jsonl and the archive lane's MIRROR_FRAGMENTS.jsonl, which
claim-kit's FRAGMENTS*.jsonl discovery does not match), each verified against its recorded hash.
The documents phase fetches these first (--ids-file); everything else follows.
"""
import csv
import hashlib
import json
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
print(f"held: {len(held)} via claim-kit texts and readiness tracker", file=sys.stderr)
job_out = Path(__file__).resolve().parent / "output"
for name in ("FRAGMENTS.jsonl", "MIRROR_FRAGMENTS.jsonl"):
    path = job_out / name
    if not path.is_file():
        continue
    added = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        data = rec.get("data") or {}
        text = job_out / data.get("text_path", "")
        if (rec.get("instrument_id") and rec["instrument_id"] not in held and text.is_file()
                and hashlib.sha256(text.read_bytes()).hexdigest() == data.get("text_sha256")):
            held.add(rec["instrument_id"])
            added += 1
    print(f"held: +{added} via {name}", file=sys.stderr)
missing = sorted((i for i in corpus["universe"] if re.fullmatch(r"EO:\d+[A-Z]?", i) and i not in held),
                 key=lambda i: (int(re.search(r"\d+", i).group()), i))
out = Path(__file__).resolve().parent / "data/PRIORITY.txt"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(missing) + "\n", encoding="utf-8", newline="\n")
print(f"{len(missing)} numbered orders without saved text -> {out.relative_to(ROOT)}")
