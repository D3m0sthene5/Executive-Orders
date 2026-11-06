"""Herschel H1 review preparation and control check (coordinator tool; no legal judgment).

usage: python3 -I research/herschel/H1/tools/review_prep.py prep BATCH
         merges each order's step outputs into one proposal, plants max(1, round(n/15)) controls (seeded),
         writes per-arm shuffled review sets and reviewer prompts in scratch; key in scratch/keys only.
       python3 -I research/herschel/H1/tools/review_prep.py check BATCH
         after both blind arms: compares control verdicts with the key; writes scratch/STOP on any miss;
         writes reveal prompts for both arms.
"""
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
H = REPO / "research/herschel/H1"
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1")
STEPS = [("original_text", "ORIGINAL_TEXT.jsonl"), ("provisional_status", "STATUS.jsonl"),
         ("clause_inventory", "INVENTORY.jsonl"), ("ending_or_current_basis", "ENDING.jsonl"),
         ("savings_residuals", "SAVINGS.jsonl"), ("counterevidence", "COUNTER.jsonl"),
         ("replace_original", "REPLACE_ORIGINAL.jsonl")]


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def rows(path):
    out = {}
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                out[r.get("instrument_id")] = r
    return out


def shift(d):
    if not isinstance(d, str) or len(d) < 4 or not d[:4].isdigit():
        return d
    y = int(d[:4]) - 3
    rest = d[4:]
    if rest.startswith("-02-29"):
        rest = "-02-28" + rest[6:]
    return f"{y:04d}{rest}"


def plant(p):
    """Move every first_end and whole_order_end date back three years; else corrupt one inventory quote."""
    q = copy.deepcopy(p)
    e = q.get("ending_or_current_basis") or {}
    n = 0
    for c in e.get("clauses", []) or []:
        fe = c.get("first_end")
        if isinstance(fe, dict) and fe.get("date"):
            fe["date"] = shift(fe["date"]); n += 1
    we = e.get("whole_order_end")
    if isinstance(we, dict) and we.get("date"):
        we["date"] = shift(we["date"]); n += 1
    if n:
        return q, "every first_end and whole_order_end date moved back three years"
    inv = q.get("clause_inventory") or {}
    for c in inv.get("clauses", []) or []:
        s = c.get("quote")
        if isinstance(s, str) and " reserved" in s:
            c["quote"] = s.replace(" reserved", " withdrawn", 1); return q, "inventory quote altered: 'reserved' -> 'withdrawn'"
        if isinstance(s, str) and len(s.split()) > 6:
            w = s.split()
            c["quote"] = s.replace(w[3], w[3] + " not", 1); return q, f"inventory quote altered: inserted 'not' after '{w[3]}'"
    return None, None


def prep(batch):
    ids = json.load(open(H / "tools/batches.json"))[batch]
    sd = H / "packets" / batch / "steps"
    data = {k: rows(sd / f) for k, f in STEPS}
    props = []
    for i in ids:
        p = {"instrument_id": i}
        for k, _ in STEPS:
            if i in data[k]:
                r = dict(data[k][i]); r.pop("instrument_id", None); p[k] = r
        props.append(p)
    eligible = [p for p in props if any(isinstance((c or {}).get("first_end"), dict) and c["first_end"].get("date")
                                       for c in (p.get("ending_or_current_basis") or {}).get("clauses", []) or [])]
    rng = random.Random(hashlib.sha256(("herschel-H1-controls:" + batch).encode()).hexdigest())
    n = max(1, round(len(props) / 15))
    pool = sorted(eligible or props, key=lambda p: p["instrument_id"])
    key, out, genuine = [], [], []
    picks = set()
    for p in rng.sample(pool, len(pool)):
        if len(picks) >= n:
            break
        q, defect = plant(p)
        if q is not None:
            picks.add(p["instrument_id"]); key.append({"instrument_id": p["instrument_id"], "planted": canon(q),
                                                        "genuine": canon(p), "defect": defect, "planted_obj": q})
    planted = {k["instrument_id"]: k["planted_obj"] for k in key}
    for p in props:
        out.append(planted.get(p["instrument_id"], p))
        if p["instrument_id"] in planted:
            genuine.append(p)
    rd = S / "review" / batch
    rd.mkdir(parents=True, exist_ok=True)
    (H / "packets" / batch / "reviews").mkdir(parents=True, exist_ok=True)
    (rd / "GENUINE_CONTROLS.jsonl").write_text("".join(json.dumps(g, ensure_ascii=False) + "\n" for g in genuine))
    (H / "packets" / batch / "PROPOSALS.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in props))
    (S / "keys").mkdir(exist_ok=True)
    (S / "keys" / f"{batch}.json").write_text(json.dumps({"batch": batch, "controls": [
        {k2: v for k2, v in k.items() if k2 != "planted_obj"} for k in key]}, indent=1))
    tmpl = (H / "tools/prompts/reviewer.txt").read_text()
    for arm in "AB":
        rows_ = [json.dumps(o, ensure_ascii=False) + "\n" for o in out]
        random.Random(f"herschel-H1-{batch}-{arm}").shuffle(rows_)
        (rd / f"REVIEW_SET_{arm}.jsonl").write_text("".join(rows_))
        name = f"rev-{batch}-{arm}"
        t = (tmpl.replace("REVIEWSET", str(rd / f"REVIEW_SET_{arm}.jsonl"))
             .replace("BATCHDIR", str(H / "packets" / batch))
             .replace("OUTFILE", str(H / "packets" / batch / "reviews" / f"BLIND_REVIEW_{arm}.jsonl")))
        (S / "prompts" / f"{name}.txt").write_text(t.replace("WORKER", name))
    print(json.dumps({"batch": batch, "proposals": len(props), "controls": sorted(picks)}))


def check(batch):
    key = json.load(open(S / "keys" / f"{batch}.json"))["controls"]
    res = {"batch": batch, "controls": []}
    miss = False
    for arm in "AB":
        rv = rows(H / "packets" / batch / "reviews" / f"BLIND_REVIEW_{arm}.jsonl")
        for k in key:
            r = rv.get(k["instrument_id"]) or {}
            caught = r.get("verdict") == "rejected"
            miss |= not caught
            res["controls"].append({"arm": arm, "instrument_id": k["instrument_id"], "defect": k["defect"],
                                    "blind_verdict": r.get("verdict"), "caught": caught,
                                    "sha_matches_planted": r.get("proposal_sha256") == k["planted"]})
    if miss:
        (S / "STOP").write_text(json.dumps(res))
    ids = ", ".join(k["instrument_id"] for k in key)
    for arm in "AB":
        name = f"rev-{batch}-{arm}"
        msg = (f"After-reveal step for batch {batch}. The proposal(s) for {ids} in your review set were planted controls: "
               + "; ".join(f"{k['instrument_id']}: {k['defect']}" for k in key)
               + f". The genuine version(s) are in {S}/review/{batch}/GENUINE_CONTROLS.jsonl (one JSON object per line). "
               "Review each genuine version on its merits with the same blinding and the same standard as your blind review "
               "(do not uphold it because it is the genuine one). Write one JSON object per genuine proposal to "
               f"{H}/packets/{batch}/reviews/AFTER_REVEAL_{arm}.jsonl in the same format as your blind records, with "
               "proposal_sha256 over the genuine object, verdict \"upheld_after_reveal\" or \"rejected\" with defects. "
               f"Do not change BLIND_REVIEW_{arm}.jsonl. Reply in at most 60 words.")
        (S / "prompts" / f"reveal-{batch}-{arm}.txt").write_text(msg)
    (S / "review" / batch / "CONTROL_CHECK.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res))


if __name__ == "__main__":
    {"prep": prep, "check": check}[sys.argv[1]](sys.argv[2])
