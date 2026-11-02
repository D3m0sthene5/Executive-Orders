"""Plant blind-review controls for one Apollo batch (coordinator tool; no legal judgment).

usage: python3 moon_plant.py BATCH APPLIED_DIR
  Picks max(1, round(n/15)) submitted claims (seeded by batch name), writes a planted version of each with every
  first-end and whole-order-end date moved back by exactly three years (internally consistent, contradicted by
  the cited sources), and writes:
    scratch/moon-review/BATCH/REVIEW_SET.jsonl   claims as the blind reviewer sees them (planted in place)
    scratch/moon-keys/BATCH.json                 private key (outside the repository)
    scratch/moon-review/BATCH/GENUINE_CONTROLS.jsonl  genuine versions, given to the reviewer only after reveal
"""
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad")


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def shift(date):
    if not isinstance(date, str) or len(date) < 10 or not date[:4].isdigit():
        return date
    y = int(date[:4]) - 3
    md = date[4:10]
    if md == "-02-29":
        md = "-02-28"
    return f"{y:04d}{md}{date[10:]}"


def plant(claim):
    p = copy.deepcopy(claim)
    changed = 0
    we = p.get("whole_order_end")
    if isinstance(we, dict) and we.get("date"):
        we["date"] = shift(we["date"]); changed += 1
    for c in p.get("operative_clauses", []):
        fe = c.get("first_end")
        if isinstance(fe, dict) and fe.get("date"):
            fe["date"] = shift(fe["date"]); changed += 1
    return p, changed


def main(batch, applied):
    claims = [json.loads(l) for l in open(Path(applied) / "CLAIMS.proposed.jsonl", encoding="utf-8") if l.strip()]
    eligible = [c for c in claims if c.get("whole_order_status") == "no" and isinstance(c.get("whole_order_end"), dict)]
    n = max(1, round(len(claims) / 15)) if claims else 0
    rng = random.Random(hashlib.sha256(("apollo-controls:" + batch).encode()).hexdigest())
    picks = rng.sample(sorted(eligible, key=lambda c: c["instrument_id"]), min(n, len(eligible)))
    picked = {c["instrument_id"] for c in picks}
    out, key, genuine = [], [], []
    for c in claims:
        if c["instrument_id"] in picked:
            p, changed = plant(c)
            assert changed, c["instrument_id"]
            out.append(p)
            key.append({"instrument_id": c["instrument_id"], "planted": canon(p), "genuine": canon(c),
                        "defect": "every first_end and whole_order_end date moved back three years"})
            genuine.append(c)
        else:
            out.append(c)
    rdir = S / "moon-review" / batch
    rdir.mkdir(parents=True, exist_ok=True)
    with open(rdir / "REVIEW_SET.jsonl", "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    with open(rdir / "GENUINE_CONTROLS.jsonl", "w", encoding="utf-8") as f:
        for c in genuine:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    (S / "moon-keys").mkdir(exist_ok=True)
    (S / "moon-keys" / f"{batch}.json").write_text(json.dumps({"batch": batch, "controls": key}, indent=1))
    print(json.dumps({"batch": batch, "claims": len(claims), "controls": sorted(picked)}))


if __name__ == "__main__":
    main(*sys.argv[1:])
