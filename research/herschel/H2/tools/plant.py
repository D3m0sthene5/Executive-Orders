"""Plant blind-review controls for one H2 review batch (coordinator tool; no legal judgment).

usage: python3 -I plant.py BATCH KIND ITEMS.jsonl
  KIND lifecycle: ITEMS are claim-kit claims (CLAIMS.proposed.jsonl lines). Defect: every first_end and
      whole_order_end date moved back exactly three years (as in the icecore/theophilus plant.py).
  KIND status: ITEMS are status proposals (RESULT.jsonl lines of the provisional_status step). Defect: every end date
      moved back three years; if the proposal has no end date (a YES), the recommendation is flipped to "no" and the
      first command is marked ended on the order's own terms three years after its date, citing its own text.
  KIND text: ITEMS are original_text / replace_original results. Defect: the confirmation (or official printing) of
      one order is re-pointed at another order's held text (identity defect); all other fields unchanged.
  Picks max(1, round(n/15)) items, seeded by batch name. Writes into the H2 scratch directory only:
    review/BATCH/REVIEW_SET.jsonl (what blind reviewers see), review/BATCH/GENUINE_CONTROLS.jsonl (given only after
    reveal), keys/BATCH.json (private key).
"""
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2")


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def shift(date):
    if not isinstance(date, str) or len(date) < 10 or not date[:4].isdigit():
        return date
    md = date[4:10]
    if md == "-02-29":
        md = "-02-28"
    return f"{int(date[:4]) - 3:04d}{md}{date[10:]}"


def plant_lifecycle(c, _items):
    p = copy.deepcopy(c); n = 0
    we = p.get("whole_order_end")
    if isinstance(we, dict) and we.get("date"):
        we["date"] = shift(we["date"]); n += 1
    for cl in p.get("operative_clauses", []):
        fe = cl.get("first_end")
        if isinstance(fe, dict) and fe.get("date"):
            fe["date"] = shift(fe["date"]); n += 1
    return p, n, "every first_end and whole_order_end date moved back three years"


def plant_status(r, _items):
    p = copy.deepcopy(r); n = 0
    for cm in p.get("commands", []):
        e = cm.get("end")
        if isinstance(e, dict) and e.get("date"):
            e["date"] = shift(e["date"]); n += 1
    if n:
        return p, n, "every command end date moved back three years"
    p["recommended_provisional_status"] = "no"
    cm = p["commands"][0]
    d = p.get("order_date") or ""
    cm["state_on_2026_10_14"] = "ended"
    cm["current_predicate"] = None
    cm["end"] = {"date": shift(d) if d else "1940-01-01", "actor": "the order's own terms", "mechanism": "own_terms",
                 "source_path": (p.get("text_source") or {}).get("path"),
                 "source_sha256": (p.get("text_source") or {}).get("sha256_of_file"), "quote": cm.get("quote")}
    if d:
        cm["end"]["date"] = f"{int(d[:4]) + 3:04d}{d[4:10]}"
    return p, 1, "YES flipped to NO with an invented own-terms end three years after the order's date"


def plant_text(r, items):
    p = copy.deepcopy(r)
    donors = [x for x in items if x["instrument_id"] != r["instrument_id"]
              and ((x.get("confirmation") or {}).get("text_path") or ((x.get("official_printing") or {}).get("path")))]
    d = sorted(donors, key=lambda x: x["instrument_id"])[0]
    if p.get("confirmation"):
        dc = d.get("confirmation") or {}
        src = dc if dc.get("text_path") else {"text_path": d["official_printing"]["path"],
                                              "text_sha256": d["official_printing"]["sha256_of_file"]}
        for k in ("text_path", "text_sha256", "sha256", "grade"):
            if src.get(k):
                p["confirmation"][k] = src[k]
    else:
        dp = d.get("official_printing") or {}
        if not dp.get("path"):
            dc = d["confirmation"]; dp = {"path": dc["text_path"], "sha256_of_file": dc["text_sha256"]}
        p["official_printing"]["path"] = dp["path"]; p["official_printing"]["sha256_of_file"] = dp["sha256_of_file"]
    return p, 1, "text re-pointed at another order's held text (%s): identity defect" % d["instrument_id"]


def main(batch, kind, items_path):
    items = [json.loads(l) for l in open(items_path, encoding="utf-8") if l.strip()]
    fn = {"lifecycle": plant_lifecycle, "status": plant_status, "text": plant_text}[kind]
    if kind == "lifecycle":
        eligible = [c for c in items if isinstance(c.get("whole_order_end"), dict) or any(
            isinstance(cl.get("first_end"), dict) and cl["first_end"].get("date") for cl in c.get("operative_clauses", []))]
    elif kind == "status":
        eligible = [r for r in items if r.get("outcome") == "done" and r.get("commands")]
    else:
        eligible = [r for r in items if r.get("outcome") == "done" and (r.get("confirmation") or (r.get("official_printing") or {}).get("held"))]
    n = max(1, round(len(items) / 15)) if items else 0
    rng = random.Random(hashlib.sha256(("herschel-H2-controls:" + batch).encode()).hexdigest())
    picks = {c["instrument_id"] for c in rng.sample(sorted(eligible, key=lambda c: c["instrument_id"]), min(n, len(eligible)))}
    out, key, genuine = [], [], []
    for c in items:
        if c["instrument_id"] in picks:
            p, changed, defect = fn(c, items)
            assert changed, c["instrument_id"]
            out.append(p); genuine.append(c)
            key.append({"instrument_id": c["instrument_id"], "planted": canon(p), "genuine": canon(c), "defect": defect})
        else:
            out.append(c)
    rdir = S / "review" / batch
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "REVIEW_SET.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in out), encoding="utf-8")
    (rdir / "GENUINE_CONTROLS.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in genuine), encoding="utf-8")
    (S / "keys").mkdir(exist_ok=True)
    (S / "keys" / f"{batch}.json").write_text(json.dumps({"batch": batch, "kind": kind, "controls": key}, indent=1))
    for arm in "AB":
        rows = list(out)
        random.Random(f"herschel-H2-{batch}-{arm}").shuffle(rows)
        (rdir / f"REVIEW_SET_{arm}.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in rows), encoding="utf-8")
    print(json.dumps({"batch": batch, "kind": kind, "items": len(items), "controls": len(key)}))


if __name__ == "__main__":
    main(*sys.argv[1:])
