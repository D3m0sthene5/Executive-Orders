"""Plant one blind control among a batch's filled status decisions and render per-arm blank review sheets
(coordinator tool; no legal judgment).
usage: python3 -I status_plant.py BATCH ORDER [ORDER ...]
Control: the seeded pick's proposed interval dates move back three years (internally consistent, contradicted by
the cited sources); with no dated interval, its recommended status flips yes<->no. Key stays in scratch only.
Writes REVIEW_DIR/EO_N.STATUS_DECISION.json (planted in place) and PACKET/status_reviews/{A,B}/EO_N.json."""
import copy, hashlib, json, random, subprocess, sys
from pathlib import Path
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5")
R = Path("/home/claude/executive-orders")
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def shift(d):
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit(): return d, False
    md = d[4:10]; md = "-02-28" if md == "-02-29" else md
    return f"{int(d[:4])-3:04d}{md}{d[10:]}", True
def walk(o):
    n = 0
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and ("date" in k or k in ("start", "end", "from", "to")):
                o[k], ch = shift(v); n += ch
            else: n += walk(v)
    elif isinstance(o, list):
        for x in o: n += walk(x)
    return n
batch, orders = sys.argv[1], sys.argv[2:]
P = R / f"research/herschel/H5/packets/{batch}/packet"
rd = S / "review" / f"status-{batch}"; rd.mkdir(parents=True, exist_ok=True)
pool = []
for o in orders:
    d = json.load(open(P / f"undecided/EO_{o[3:]}/STATUS_DECISION.json"))
    if d.get("recommended_provisional_status") in ("yes", "no"): pool.append(o)
rng = random.Random(hashlib.sha256(("herschel-H5-status-controls:" + batch).encode()).hexdigest())
pick = rng.choice(sorted(pool)) if pool else None
key = []
for o in orders:
    n = o[3:]; src = P / f"undecided/EO_{n}/STATUS_DECISION.json"; d = json.load(open(src))
    if o == pick:
        p = copy.deepcopy(d); ch = walk(p.get("proposed_intervals", []))
        how = "proposed interval dates moved back three years"
        if not ch:
            p["recommended_provisional_status"] = {"yes": "no", "no": "yes"}[d["recommended_provisional_status"]]
            how = "recommended status flipped"
        key.append({"instrument_id": o, "planted": canon(p), "genuine": canon(d), "defect": how}); d = p
    out = rd / f"EO_{n}.STATUS_DECISION.json"; out.write_text(json.dumps(d, indent=1, ensure_ascii=False))
    for arm in "AB":
        (P / "status_reviews" / arm).mkdir(parents=True, exist_ok=True)
        subprocess.run(["python3", "jobs/claim-kit/kit.py", "overlay-review-sheet", "--evidence", str(P / f"undecided/EO_{n}/EVIDENCE.json"),
                        "--decision", str(out), "--reviewer", f"claude-blind-status-reviewer-H5-{batch}-{arm}",
                        "--write", str(P / "status_reviews" / arm / f"EO_{n}.json")], cwd=R, check=True, capture_output=True)
(S / "keys").mkdir(exist_ok=True)
(S / "keys" / f"status-{batch}.json").write_text(json.dumps({"batch": batch, "controls": key}, indent=1))
print(json.dumps({"batch": batch, "orders": len(orders), "with_status": len(pool), "controls": [k["instrument_id"] for k in key]}))
