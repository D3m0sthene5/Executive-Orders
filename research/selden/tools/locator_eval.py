"""Measure the Selden locator on real held texts, offline: OFR editorial notes (jobs/later-events, evidence types
ofr_note_on_target / ofr_note_on_acting) say acting order A revoked, superseded or amended target T; the locator must
find a sentence citing T in A's own official text (jobs/fr-originals, OCR of the printed Federal Register), and must
not find near-miss numbers or another pair's target there. Writes research/selden/census/LOCATOR_EVAL.json."""
import csv, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "jobs/selden-common"))
import selden_common as S
texts = {}
for base in ("jobs/fr-originals/output", "jobs/fr-originals/data/full_run"):
    for line in (ROOT / base / "FRAGMENTS.jsonl").read_text().splitlines():
        d = json.loads(line)
        tp = (d.get("data") or {}).get("text_path")
        if tp and (ROOT / base / tp).is_file():
            texts.setdefault(d["instrument_id"], ROOT / base / tp)
pairs, seen = [], set()
for r in csv.DictReader(open(ROOT / "jobs/later-events/output/EDGES.csv", encoding="utf-8")):
    a, t = r["acting_id"], r["target_id"]
    if r["evidence_type"] in ("ofr_note_on_target", "ofr_note_on_acting") and a in texts and t.startswith("EO:") \
            and S.mech_class(r["mechanism"]) in ("ending", "modifying") and (a, t) not in seen:
        seen.add((a, t)); pairs.append((t, a, S.mech_class(r["mechanism"]), a))
random.Random(1584).shuffle(pairs)
pairs = pairs[: int(sys.argv[1]) if len(sys.argv) > 1 else 1500]
tx = {}
cut = 0
for _, a, _, _ in pairs:
    t = texts[a].read_text(encoding="utf-8", errors="replace")
    lo, hi, found = S.own_span(t, a)   # cut neighbouring documents, as selden-fr-acting does
    cut += found
    tx[a] = t[lo:hi]
res = S.run_controls(pairs, tx)
agree_class = res["positive_class_agreement"]
res["own_span_found"] = cut
res["note"] = ("Positives are OFR editorial pairs; a miss can be OCR damage to the number, a citation by date or title, "
               "or an OFR note the text does not support. Class agreement counts the located sentence's relation class "
               "equal to OFR's (ending/modifying).")
(ROOT / "research/selden/census/LOCATOR_EVAL.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: v for k, v in res.items() if k not in ("misses", "false_hits")}, indent=1))
