"""Build Opus adjudication packets for Lane 4: every reader fail/unsure plus the seeded 5% sample of passes
(output/ADJUDICATION_QUEUE.csv from assemble.py --queue-only). Skips orders that already have an adjudication.

    python -I jobs/photius-replica-check/adjudicate_packets.py RENDERS_DIR [--batch 10]
"""
import argparse
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PK = REPO / "research/excavator/photius-replica/packets"
ADJ = REPO / "research/excavator/photius-replica/adjudication"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("renders")
    ap.add_argument("--batch", type=int, default=10)
    a = ap.parse_args()
    ADJ.mkdir(parents=True, exist_ok=True)
    done = set()
    for f in ADJ.glob("*/RESULT.jsonl"):
        for line in open(f, encoding="utf-8"):
            try:
                done.add(json.loads(line)["instrument_id"])
            except Exception:  # noqa: BLE001
                pass
    queued_already = set()
    for f in ADJ.glob("*/ORDERS.jsonl"):
        for line in open(f, encoding="utf-8"):
            queued_already.add(json.loads(line)["instrument_id"])
    queue = [r for r in csv.DictReader(open(REPO / "jobs/photius-replica-check/output/ADJUDICATION_QUEUE.csv", encoding="utf-8"))
             if r["instrument_id"] not in done and r["instrument_id"] not in queued_already]
    # the packet's order object and the reader's result
    items = []
    for q in queue:
        pk = PK / q["packet"]
        order = next((json.loads(l) for l in open(pk / "ORDERS.jsonl", encoding="utf-8") if json.loads(l)["instrument_id"] == q["instrument_id"]), None)
        reader = next((json.loads(l) for l in open(pk / "RESULT.jsonl", encoding="utf-8") if l.strip() and json.loads(l).get("instrument_id") == q["instrument_id"]), None)
        if not order:
            continue
        stem = f"EO_{order['expected_number']}"
        renders = [str(p) for p in sorted(Path(a.renders).glob(stem + "_*.png"))]
        items.append({**order, "renders": renders, "reader_result": reader, "why_adjudicated": q["why"]})
    existing = len(list(ADJ.glob("a*")))
    for b0 in range(0, len(items), a.batch):
        d = ADJ / f"a{existing + b0 // a.batch + 1:03d}"
        d.mkdir(exist_ok=True)
        with open(d / "ORDERS.jsonl", "w", encoding="utf-8") as f:
            for it in items[b0:b0 + a.batch]:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print("new adjudication items", len(items), "packets", (len(items) + a.batch - 1) // a.batch, "starting at a%03d" % (existing + 1))


if __name__ == "__main__":
    main()
