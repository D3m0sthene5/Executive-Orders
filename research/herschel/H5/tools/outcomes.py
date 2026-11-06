"""Assemble per-worker outcomes (scratch OUTCOMES.json) and ORDER_OUTCOMES.csv from step notes (coordinator tool).
Coordinator rulings encoded here: w12's EO:2489 and w13's blocks are failed:missed held ProQuest replica (redone by w23, w21);
steps downstream of a blocked step inherit its block; claim-route steps of orders the kit cannot freeze are blocked on a
dated status-history record; review of undecided lifecycles is blocked by the overlay destination policy."""
import csv, glob, json
from pathlib import Path
H = Path("/home/claude/executive-orders/research/herschel/H5"); K = H / "packets"
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5")
J = lambda p: json.load(open(p))
W = {}
for f in glob.glob(str(K / "ot/H5-w0*.jsonl")):
    W[Path(f).stem] = {json.loads(l)["instrument_id"]: json.loads(l)["outcome"] for l in open(f) if l.strip()}
def notes(b, step, w): W[w] = J(K / f"{b}/packet/STEP_NOTES/{step}.outcomes.json")
for b, step, w in [("d1","clause_inventory","H5-w06"),("d2","clause_inventory","H5-w07"),("u4","provisional_status","H5-w08"),
    ("u4","clause_inventory","H5-w09"),("d1","ending_or_current_basis","H5-w10"),("d2","ending_or_current_basis","H5-w11"),
    ("d1","savings_residuals","H5-w14"),("u4","ending_or_current_basis","H5-w15"),("u6","clause_inventory","H5-w21"),
    ("d1","counterevidence","H5-w22"),("u4","savings_residuals","H5-w24"),("u6","ending_or_current_basis","H5-w31"),
    ("u4","counterevidence","H5-w32"),("u6","savings_residuals","H5-w33"),("u6","counterevidence","H5-w34"),
    ("d3s","clause_inventory_carry","H5-w35"),("d3s","ending_or_current_basis","H5-w36")]: notes(b, step, w)
W["H5-w12"] = J(K / "u6/packet/STEP_NOTES/provisional_status.w12.outcomes.json"); W["H5-w12"]["EO:2489"] = "failed:blocked for page images although the ProQuest replica is held and page-checked (coordinator; redone by H5-w23)"
W["H5-w13"] = {o: "failed:blocked for page images although the ProQuest replica is held and page-checked (coordinator; redone by H5-w21)" for o in ("EO:2489","EO:4220")}
W["H5-w23"] = J(K / "u6/packet/STEP_NOTES/provisional_status.outcomes.json")
for w, b in (("H5-w18","n1"),("H5-w19","n2"),("H5-w20","n3")): W[w] = J(H / f"proposals/{b}/OUTCOMES.json")
def rev(files, genuine_ok):
    out = {}
    for f in files:
        for l in open(f):
            d = json.loads(l); v = d.get("verdict") or d.get("decision"); iid = d["instrument_id"]
            ok = v in ("accept", "upheld", "upheld_after_reveal")
            if d.get("after_reveal"): out[iid] = "upheld" if ok else "rejected:" + (d.get("defect") or "after reveal")
            elif iid in genuine_ok: out.setdefault(iid, "rejected:planted control caught (genuine reviewed after reveal)")
            else: out[iid] = "upheld" if ok else "rejected:" + str(d.get("defect") or d.get("defects"))[:200]
    return out
W["H5-w16"] = rev([K/"u4/packet/status_reviews/A/SUMMARY.jsonl"], {"EO:11925"}); W["H5-w17"] = rev([K/"u4/packet/status_reviews/B/SUMMARY.jsonl"], {"EO:11925"})
W["H5-w29"] = rev([K/"u6/packet/status_reviews/A/SUMMARY.jsonl"], {"EO:2489"}); W["H5-w30"] = rev([K/"u6/packet/status_reviews/B/SUMMARY.jsonl"], {"EO:2489"})
W["H5-w27"] = rev([H/"proposals/reviews/nrev1-A.jsonl"], {"EO:3421"}); W["H5-w28"] = rev([H/"proposals/reviews/nrev1-B.jsonl"], {"EO:3421"})
W["H5-w25"] = rev([K/"d1/packet/reviews/AFTER_REVEAL_A.jsonl"], set()); W["H5-w26"] = rev([K/"d1/packet/reviews/AFTER_REVEAL_B.jsonl"], set())
W["H5-w05"] = {k: v for k, v in W["H5-w05"].items()}
json.dump(W, open(E / "OUTCOMES.json", "w"), indent=1, ensure_ascii=False)
# ---- per order and step ----
sample = {r["instrument_id"]: r for r in csv.DictReader(open(H.parent / "frame/SAMPLE_R2.csv"))}
orders = [x for x in J(H.parent / "frame/ASSIGNMENTS_R2.json")["coordinators"] if x["name"] == "H5"][0]["orders"]
custody = {}
for b in ("d1", "d2", "u4", "u6"):
    d = J(K / f"{b}/packet/DISPATCH_CHECK.json")
    for m in d["members"]:
        if m["instrument_id"] in d["source_blocked_ids"]:
            urls = sorted({(x.get("source") or {}).get("url", "?") for x in m["blockers"]})
            custody[m["instrument_id"]] = "blocked:custody copy of " + "; ".join(urls)
nokit = {l.split("\t")[1] for l in open(H / "tools/DROPPED.tsv")}
def pick(o, *ws):
    for w in ws:
        if o in W.get(w, {}): return W[w][o], w
    return None, None
rows = []
CLAIM = ["clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"]
for o in orders:
    steps = sample[o]["open_steps"].split("|"); st = sample[o]["stratum"]; res = {}
    if "provisional_status" in steps:
        res["provisional_status"] = pick(o, "H5-w23", "H5-w08", "H5-w18", "H5-w19", "H5-w20")
        if not res["provisional_status"][0]: res["provisional_status"] = ("blocked:no dated status-history record", "coordinator")
        ps = res["provisional_status"][0]
        if ps == "done":
            a, wa = pick(o, "H5-w16", "H5-w29", "H5-w27"); b, wb = pick(o, "H5-w17", "H5-w30", "H5-w28")
            res["review_status"] = ("upheld" if a == b == "upheld" else (a if a != "upheld" else b), f"{wa}+{wb}")
        else:
            res["review_status"] = ("blocked:" + ps.split(":", 1)[-1][:150] + " (no status proposal to review)", "coordinator")
    if "original_text" in steps: res["original_text"] = pick(o, "H5-w01", "H5-w02", "H5-w03", "H5-w04")
    if "opus_media" in steps: res["opus_media"] = pick(o, "H5-w05")
    up = None
    for s in [x for x in CLAIM if x in steps] + ["review"]:
        if o in nokit: res[s] = ("blocked:dated status-history record so the claim kit can freeze a dossier (jobs/status-history has none; kit refuses: no dated history located)", "coordinator"); continue
        if o in custody: res[s] = (custody[o], "coordinator(dispatch-check)"); continue
        if up: res[s] = (up + f" (depends on {upstep})", "coordinator"); continue
        if s == "review":
            if o == "EO:649": res[s] = ("upheld", "H5-w25+H5-w26")
            else: res[s] = ("blocked:tool policy: overlay-propose writes only under jobs/claim-kit/output/overlays or research/excavator, so an undecided order's lifecycle claim cannot be assembled from a Herschel packet", "coordinator")
            continue
        ws = {"clause_inventory": ("H5-w35", "H5-w21", "H5-w06", "H5-w07", "H5-w09"), "ending_or_current_basis": ("H5-w36", "H5-w10", "H5-w11", "H5-w15", "H5-w31"),
              "savings_residuals": ("H5-w14", "H5-w24", "H5-w33"), "counterevidence": ("H5-w22", "H5-w32", "H5-w34")}[s]
        v, w = pick(o, *ws)
        if v is None: v, w = "not_reached", ""
        res[s] = (v, w)
        if v.startswith("blocked"): up, upstep = v, s
    for s, (v, w) in res.items(): rows.append([o, st, s, v, w])
with open(H / "ORDER_OUTCOMES.csv", "w", newline="") as f:
    cw = csv.writer(f); cw.writerow(["instrument_id", "stratum", "step", "outcome", "worker"]); cw.writerows(rows)
from collections import Counter
c = Counter((r[2], r[3].split(":")[0]) for r in rows)
print(json.dumps({f"{a}|{b}": n for (a, b), n in sorted(c.items())}, indent=0))
