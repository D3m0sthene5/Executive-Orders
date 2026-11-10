"""Build the blind reading packet for the Jacquard L1 correction (D-20261110-ulpian-jacquard-l1-correction).

The 42 Jacquard L1 provisional NO statuses dated on or after 1904-05-03 (research/ulpian/JACQUARD_L1.csv, required
age above 0) plus three planted controls, shuffled under neutral item ids with a fixed seed. Each item carries the
order date and the held text exactly as read from the repository. CONTROL_KEY.json maps items to orders and marks
the controls; it is not given to the readers.

    python -I research/ulpian/jacquard-l1-correction/build_packet.py
"""
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
SEED = "ulpian-jacquard-l1-correction-2026-11-10"

# Planted controls: real undecided one-person waivers (not in L1) with one sentence appended. Each has a known answer.
CONTROLS = [
    {"instrument_id": "EO:1854", "kind": "fact_about_another_person", "expected": "RETURN",
     "append": " Her husband, the late Mr. Kugler, entered the service of the Government on March 1, 1889."},
    {"instrument_id": "EO:2077", "kind": "fact_too_late", "expected": "RETURN",
     "append": " Mr. Bateman has been employed temporarily at the navy yard since July 1, 1906."},
    {"instrument_id": "EO:2102", "kind": "genuine_sufficient_fact", "expected": "KEEP",
     "append": " Miss Happersett was appointed a copyist in the War Department on June 15, 1893, and served until 1905."},
]


def text_of(rel):
    return re.sub(r"\s+", " ", (REPO / rel).read_text(encoding="utf-8", errors="replace")).strip()


def main():
    lots = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/excavator/jacquard-2026-10-31/LOTS.csv",
                                                                encoding="utf-8", newline=""))}
    rows = [r for r in csv.DictReader(open(REPO / "research/ulpian/JACQUARD_L1.csv", encoding="utf-8", newline=""))
            if r["required_age"] not in ("", "0")]
    assert len(rows) == 42, len(rows)
    klass = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/ulpian/CLASS.csv", encoding="utf-8",
                                                                 newline=""))}
    items = []
    for r in rows:
        rel = lots[r["instrument_id"]]["text_path"]
        items.append({"instrument_id": r["instrument_id"], "date": r["date"], "text_path": rel,
                      "text_sha256": hashlib.sha256((REPO / rel).read_bytes()).hexdigest(),
                      "text": text_of(rel), "control": None})
    for c in CONTROLS:
        k = klass[c["instrument_id"]]
        items.append({"instrument_id": c["instrument_id"], "date": k["date"], "text_path": k["text_path"],
                      "text_sha256": hashlib.sha256((REPO / k["text_path"]).read_bytes()).hexdigest(),
                      "text": text_of(k["text_path"]) + c["append"], "control": c})
    random.Random(SEED).shuffle(items)
    packet, key = [], []
    for n, item in enumerate(items, 1):
        pid = f"P{n:02d}"
        packet.append({"item": pid, "order_date": item["date"], "text": item["text"]})
        key.append({"item": pid, "instrument_id": item["instrument_id"], "order_date": item["date"],
                    "text_path": item["text_path"], "text_sha256": item["text_sha256"],
                    "control": item["control"]})
    with open(HERE / "PACKET.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for p in packet:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    (HERE / "CONTROL_KEY.json").write_text(json.dumps({"seed": SEED, "items": key}, indent=1, ensure_ascii=False) + "\n",
                                           encoding="utf-8", newline="\n")
    print(json.dumps({"items": len(packet), "controls": len(CONTROLS),
                      "packet_sha256": hashlib.sha256((HERE / "PACKET.jsonl").read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
