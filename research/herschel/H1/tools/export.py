"""Herschel H1 evidence export (coordinator tool; read-only; no legal judgment).

usage: python3 -I research/herschel/H1/tools/export.py BATCH

Why: `kit.py prepare` / `dossier` refuse undecided orders that have no status-history record
("no dated history located"; jobs/status-history/output/INDEX.json history=null, flag
NO_STATUS_OBSERVATION_LOCATED). 30 of H1's 32 orders are such orders. This script copies, unchanged, the
compiled claim-kit records the overlay freeze would have consumed (OVERLAY_INPUTS, STATUS_LEADS, OWN_TERMS,
ACTING_PROVISIONS, CHAINS, CLAUSES, TEXT_REPRESENTATIONS), the census/readiness rows, held text files and
their hashes, any held ProQuest page PDF, and a held-text number search (cruden), into
research/herschel/H1/packets/BATCH/evidence/EO_N.json. It is research-only evidence export: it authorizes no
production, writes nothing outside the packets folder, and changes no jobs output.
"""
import csv
import glob
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
OUT = REPO / "jobs/claim-kit/output"
H = REPO / "research/herschel/H1"
STEMS = {"OVERLAY_INPUTS": "instrument_id", "STATUS_LEADS": "instrument_id", "OWN_TERMS": "instrument_id",
         "ACTING_PROVISIONS": "target_id", "CHAINS": "target_id", "CLAUSES": "instrument_id",
         "TEXT_REPRESENTATIONS": "instrument_id"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(batch):
    ids = json.load(open(H / "tools/batches.json"))[batch]
    want = set(ids)
    found = {i: {s: [] for s in STEMS} for i in ids}
    for stem, field in STEMS.items():
        for path in sorted(glob.glob(str(OUT / (stem + "*.jsonl")))):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    key = None
                    for i in want:  # cheap prefilter before parsing
                        if f'"{i}"' in line:
                            key = i
                            break
                    if key is None:
                        continue
                    row = json.loads(line)
                    if row.get(field) in want:
                        found[row[field]][stem].append(row)
    orders = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "research/herschel/frame/ORDERS.csv"))}
    ready = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"))}
    hist = {r["instrument_id"]: r for r in json.load(open(REPO / "jobs/status-history/output/INDEX.json"))}
    dest = H / "packets" / batch / "evidence"
    dest.mkdir(parents=True, exist_ok=True)
    for i in ids:
        n = i.split(":", 1)[1]
        texts = {}
        for p in sorted(glob.glob(str(REPO / "jobs/*/output/texts" / f"EO_{n}.txt"))):
            rel = os.path.relpath(p, REPO)
            texts[rel] = {"sha256": sha(p), "chars": len(Path(p).read_text("utf-8", errors="replace"))}
        pdfs = [os.path.relpath(p, REPO) for p in glob.glob(str(REPO / "ProQuest Pre-1937 Orders" / f"*-EO-{n}.pdf"))]
        num = dest / f"EO_{n}.number_search.json"
        r = subprocess.run([sys.executable, "-I", str(REPO / "research/excavator/claude-nira-sweep-2026-10-29/cruden.py"),
                            "number", i, "--write", str(num)], cwd=REPO, capture_output=True, text=True)
        rec = {"schema": "herschel-h1-evidence-export/v1", "instrument_id": i,
               "why": "kit prepare refuses: " + ("no status-history record" if not (hist.get(i) or {}).get("history") else "see prep log"),
               "census_row": orders.get(i), "readiness_row": ready.get(i), "status_history_index": hist.get(i),
               "compiled_records": found[i], "held_texts": texts, "proquest_pdfs": pdfs,
               "number_search": os.path.relpath(num, REPO) if num.exists() else None,
               "number_search_error": (r.stderr[-500:] if r.returncode else None)}
        (dest / f"EO_{n}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(i, {k: len(v) for k, v in found[i].items()}, list(texts), pdfs, r.returncode)


if __name__ == "__main__":
    main(sys.argv[1])
