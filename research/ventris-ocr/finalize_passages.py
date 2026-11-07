"""One-off, idempotent: make PASSAGES.csv safe to commit.

The GPO text layer of a crop contains CR LF line ends. Converting the repository's files to LF (a campaign rule) would
silently edit those characters inside a quoted CSV field. So the column is stored JSON-escaped as `gpo_text_layer_json`
(json.loads gives the exact text, byte for byte) and the CSV uses LF row ends. READINGS.jsonl already stores the same
text JSON-escaped.
Run: C:/Users/danie/eo-venvs/enc/Scripts/python.exe -I finalize_passages.py
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, "PASSAGES.csv")
with open(path, newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
if "gpo_text_layer" in rows[0]:
    for r in rows:
        r["gpo_text_layer_json"] = json.dumps(r.pop("gpo_text_layer"), ensure_ascii=False)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("converted", len(rows))
else:
    print("already converted", len(rows))
