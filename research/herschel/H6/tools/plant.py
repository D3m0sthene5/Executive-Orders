"""H6 planted controls (coordinator tool; no legal judgment). Adapted from Theophilus plant.py.
usage: python3 -I plant.py BATCH SETFILE
  SETFILE: JSONL review records, each either a lifecycle claim (has operative_clauses) or a sheet record
  {"instrument_id", "status_decision", "decision_row", "clause_rows"}. Picks max(1, round(n/15)) records with a dated
  end, moves every end date back exactly three years (internally consistent, contradicted by the cited sources), and writes
  scratch review/BATCH/REVIEW_SET.jsonl (planted in place), review/BATCH/GENUINE_CONTROLS.jsonl, keys/BATCH.json."""
import copy, hashlib, json, random, re, sys
from pathlib import Path
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
canon = lambda o: hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def shift(d):
    if not isinstance(d, str) or not re.match(r"^\d{4}-\d\d-\d\d", d): return d
    md = d[4:10]; md = "-02-28" if md == "-02-29" else md
    return f"{int(d[:4]) - 3:04d}{md}{d[10:]}"
def dated(r):
    if "operative_clauses" in r:
        return bool((r.get("whole_order_end") or {}).get("date")) or any((c.get("first_end") or {}).get("date") for c in r["operative_clauses"])
    return any(re.match(r"^\d{4}-", c.get("effective_date") or "") for c in r.get("clause_rows", [])) or \
        any(re.match(r"^\d{4}-", str(i.get("to") or "")) for i in (r.get("status_decision") or {}).get("proposed_intervals") or [])
def plant(r):
    p = copy.deepcopy(r); n = 0
    if "operative_clauses" in p:
        we = p.get("whole_order_end")
        if isinstance(we, dict) and we.get("date"): we["date"] = shift(we["date"]); n += 1
        for c in p["operative_clauses"]:
            fe = c.get("first_end")
            if isinstance(fe, dict) and fe.get("date"): fe["date"] = shift(fe["date"]); n += 1
    else:
        for c in p.get("clause_rows", []):
            if re.match(r"^\d{4}-", c.get("effective_date") or ""): c["effective_date"] = shift(c["effective_date"]); n += 1
        for i in (p.get("status_decision") or {}).get("proposed_intervals") or []:
            if re.match(r"^\d{4}-", str(i.get("to") or "")): i["to"] = shift(i["to"]); n += 1
        sd = p.get("status_decision") or {}
        for k in ("rationale",):
            pass  # prose is left unchanged: the defect is the dates, as in the Theophilus controls
    return p, n
def main(batch, setfile):
    recs = [json.loads(l) for l in open(setfile, encoding="utf-8") if l.strip()]
    elig = sorted([r for r in recs if dated(r)], key=lambda r: r["instrument_id"])
    n = max(1, round(len(recs) / 15)) if recs else 0
    rng = random.Random(hashlib.sha256(("herschel-H6-controls:" + batch).encode()).hexdigest())
    flip = False
    if not elig:  # no dated end anywhere: flip a proposed status instead (contradicted by the cited sources)
        elig = sorted([r for r in recs if (r.get("status_decision") or {}).get("recommended_provisional_status") in ("yes", "no")], key=lambda r: r["instrument_id"]); flip = True
    picks = {r["instrument_id"] for r in rng.sample(elig, min(n, len(elig)))}
    out, key, gen = [], [], []
    for r in recs:
        if r["instrument_id"] in picks:
            if flip:
                p = copy.deepcopy(r); sd = p["status_decision"]; sd["recommended_provisional_status"] = {"yes": "no", "no": "yes"}[sd["recommended_provisional_status"]]; k = 1
            else: p, k = plant(r)
            assert k, r["instrument_id"]
            out.append(p); gen.append(r)
            key.append({"instrument_id": r["instrument_id"], "planted": canon(p), "genuine": canon(r), "defect": "recommended status flipped" if flip else "every end date moved back three years"})
        else: out.append(r)
    d = S / "review" / batch; d.mkdir(parents=True, exist_ok=True)
    (d / "REVIEW_SET.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    (d / "GENUINE_CONTROLS.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in gen))
    (S / "keys").mkdir(exist_ok=True); (S / "keys" / f"{batch}.json").write_text(json.dumps({"batch": batch, "controls": key}, indent=1))
    for arm in "AB":
        rows = list(out); random.Random(f"herschel-H6-{batch}-{arm}").shuffle(rows)
        (d / f"REVIEW_SET_{arm}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(json.dumps({"batch": batch, "records": len(recs), "controls": sorted(picks), "eligible": len(elig)}))
if __name__ == "__main__": main(*sys.argv[1:])
