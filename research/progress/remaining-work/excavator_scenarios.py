"""What each proposed excavator would save, in the effort model's agent-hours.

Applies each idea in research/plans/EXCAVATOR_SERIES_2026-10-19.md to the
open steps from build_effort.assign(): for the orders and steps it reaches, at
a stated hit rate, a step's minutes fall to the stated new value. Every
coverage set below is computed from committed data; every hit rate and new
minute value is an assumption, written next to it. Ideas are scored alone and
then as the selected series (all applied, the lowest minutes per step kept,
then the review change), so savings are never counted twice.

Writes EXCAVATOR_SCENARIOS.json and EXCAVATOR_SCENARIOS.csv next to this file.
"""
import collections, csv, json, random, re

import build_effort as be
import build_remaining_work as brw

HERE, JOBS = be.HERE, be.JOBS

# Types of pre-1937 orders, from the WPA 1944 summary hint where the project
# has it, else from APP's title.
SPENT = {"civil_service_individual", "retirement_exemption", "mourning_closing", "relief_allotments"}
LAND = {"land_withdrawal", "national_forest", "military_reservation", "lighthouse_navigation",
        "bird_wildlife_refuge", "bird_wildlife", "indian_reservation", "indian"}
SWEPT = {"emergency_war", "nra_codes", "canal_zone"}
TITLE_RULES = [
    ("civil_service_individual", r"without regard to|civil.service (rules|examination)|appointment of|waiv|reinstatement of"),
    ("retirement_exemption", r"retirement"),
    ("land_withdrawal", r"withdraw|public land|power site|oil shale|stock driveway|water reserve|reserv(ation|ing) of land|restoring"),
    ("national_forest", r"national forest"),
    ("indian", r"indian"),
    ("bird_wildlife", r"bird|wild ?life|refuge|game"),
    ("canal_zone", r"canal zone|panama"),
    ("nra_codes", r"code of fair competition|national recovery|industrial recovery|nra\b"),
    ("relief_allotments", r"allocat|allot|emergency relief|works progress|public works|emergency conservation|funds"),
    ("military_reservation", r"military reservation|naval reservation"),
    ("mourning_closing", r"closing of|mourning|half.holiday"),
]


def order_types():
    t = {}
    for r in csv.DictReader(open(JOBS / "indian-reservations-1912/data/wpa_lists_subset/NUMBERED_ENTRIES.csv")):
        if r["family_hint"]:
            t.setdefault(r["id"], r["family_hint"])
    for r in csv.DictReader(open(JOBS / "numbered-early-orders/data/TARGETS.csv")):
        if r["family_hint"]:
            t[r["instrument_id"]] = r["family_hint"]
    for r in csv.DictReader(open(brw.INDEX)):
        iid = r["instrument_id"]
        if not iid or iid in t:
            continue
        n = brw.num(iid)
        if n is None or n >= be.MODERN_FROM:
            continue
        title = r["title"].lower()
        t[iid] = next((k for k, p in TITLE_RULES if re.search(p, title)), "other")
    return t


def cls(typ):
    return "spent" if typ in SPENT else "land" if typ in LAND else "swept" if typ in SWEPT else "other"


# Each idea: (name, applies(record, class) -> bool, hit rate, {step: new minutes}).
# A step not listed keeps its minutes. New minutes are per step before the
# claim-draft multiplier. Old orders = before 1937.
def old(x):
    return not x["modern"]


IDEAS = [
    ("1 Type tribunal", lambda x, c: old(x) and c == "spent", 0.85,
     {"provisional_status": 1, "clause_inventory": 2, "ending_or_current_basis": 3, "savings_residuals": 2}),
    ("2 Extinction-event mapper", lambda x, c: old(x) and c == "swept", 0.8,
     {"provisional_status": 2, "ending_or_current_basis": 6, "savings_residuals": 4}),
    ("3 Public Land Order harvester", lambda x, c: old(x) and c == "land", 0.6,
     {"provisional_status": 3, "ending_or_current_basis": 10, "savings_residuals": 7, "counterevidence": 5}),
    ("4 Living-law back-propagation", lambda x, c: old(x), 1.0,
     {"counterevidence": 5}),
    ("5 Reel-to-text bulk acquisition", lambda x, c: old(x) and x["number"] is not None and x["number"] <= 7403, 0.85,
     {"original_text": 3, "clause_inventory": 3}),
    ("6 Editorial annotation miner", lambda x, c: old(x), 0.1,
     {"ending_or_current_basis": 10, "savings_residuals": 7}),
    ("7 Risk-tiered review", None, None, None),       # multiplier, applied below
    ("8 Look-alike template cloning", lambda x, c: x["in_cluster"], 1.0,
     {"clause_inventory": 1}),
    ("9 Census gap admission line", lambda x, c: x["instrument_id"] is None, 0.7,
     {"admit": 6, "original_text": 3}),
    ("10 Negative-search automaton", lambda x, c: x["step"] == "original_text" and x["tier"] in ("OT4", "OT5"), 0.9,
     {"original_text": 2}),
]
REVIEW_SHARE = 0.30   # reviewer share of agent time (Astra swarm: producers 19-34 min, reviewers 9-15 min)
AUDIT_RATE = 0.20     # rows reviewed in full under risk-tiered review
TEMPLATE_LEGAL = 0.7  # legal-step minutes kept inside a look-alike cluster (idea 8)

SERIES = {
    "X1 Lifecycle class engine": ["1 Type tribunal", "2 Extinction-event mapper", "8 Look-alike template cloning", "7 Risk-tiered review"],
    "X2 Land ledger excavator": ["3 Public Land Order harvester"],
    "X3 Reel-to-text excavator": ["5 Reel-to-text bulk acquisition", "10 Negative-search automaton"],
    "X4 Living-law counter-search": ["4 Living-law back-propagation", "6 Editorial annotation miner"],
    "X5 Census gap admission line": ["9 Census gap admission line"],
}


def main():
    records, model = be.assign()
    types = order_types()
    # Look-alike clusters: modern orders sharing one acting or parent order in a
    # claim-kit family of 5+, or old orders of a templated type (spent, land, swept).
    in_family = {i for f in json.load(open(JOBS / "claim-kit/output/FAMILIES.json"))
                 if f["family_id"].split(":")[0] in ("actor", "parent") and len(f["instrument_ids"]) >= 5
                 for i in f["instrument_ids"]}
    for x in records:
        iid = x["instrument_id"]
        x["number"] = brw.num(iid) if iid else None
        x["cls"] = cls(types.get(iid, "land" if iid is None else "other"))
        x["in_cluster"] = bool(iid) and (iid in in_family or (old(x) and x["cls"] in ("spent", "land", "swept")))
        x["base"] = float(model[x["tier"]]["minutes"]) * x["mult"] * x["count"]
    base = sum(x["base"] for x in records)
    rng = random.Random(20261019)
    hit_draw = {id(x): rng.random() for x in records}

    def new_minutes(x, idea_names):
        best = x["base"]
        for name, applies, hit, new in IDEAS:
            if name not in idea_names or applies is None or x["step"] not in new:
                continue
            if not applies(x, x["cls"]):
                continue
            # A census-gap record stands for many orders: apply the hit rate as a share.
            share = hit if x["count"] > 1 else (1.0 if hit_draw[id(x)] < hit else 0.0)
            cand = (new[x["step"]] * x["mult"] * x["count"]) * share + x["base"] * (1 - share)
            best = min(best, cand)
        if "8 Look-alike template cloning" in idea_names and x["in_cluster"] and x["step"] in be.LEGAL - {"clause_inventory"}:
            best *= TEMPLATE_LEGAL
        if "7 Risk-tiered review" in idea_names and x["in_cluster"]:
            best *= 1 - REVIEW_SHARE * (1 - AUDIT_RATE)
        return best

    def run(names):
        return sum(new_minutes(x, names) for x in records)

    out = {"baseline_hours": round(base / 60), "ideas": [], "series": []}
    for name, *_ in IDEAS:
        after = run({name})
        out["ideas"].append({"idea": name, "hours_saved": round((base - after) / 60),
                             "share_of_total": round((base - after) / base, 3)})
    done = set()
    prev = base
    for x_name, members in SERIES.items():
        done |= set(members)
        after = run(done)
        out["series"].append({"excavator": x_name, "ideas": members, "marginal_hours_saved": round((prev - after) / 60),
                              "hours_left_after": round(after / 60)})
        prev = after
    out["series_total_saved"] = round((base - prev) / 60)
    out["series_share_saved"] = round((base - prev) / base, 3)
    # Context for the plan: where the hours sit, by era and class.
    by = collections.defaultdict(float)
    for x in records:
        by["modern" if x["modern"] else "old:" + x["cls"]] += x["base"] / 60
    out["baseline_hours_by_group"] = {k: round(v) for k, v in sorted(by.items(), key=lambda kv: -kv[1])}
    orders = collections.Counter()
    for x in records:
        if x["step"] == "ending_or_current_basis" or x["step"] == "admit":
            orders["modern" if x["modern"] else "old:" + x["cls"]] += x["count"]
    out["open_orders_by_group"] = dict(orders)
    (HERE / "EXCAVATOR_SCENARIOS.json").write_text(json.dumps(out, indent=1) + "\n")
    with open(HERE / "EXCAVATOR_SCENARIOS.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "name", "hours_saved", "hours_left_after"])
        for i in out["ideas"]:
            w.writerow(["idea", i["idea"], i["hours_saved"], ""])
        for s in out["series"]:
            w.writerow(["series", s["excavator"], s["marginal_hours_saved"], s["hours_left_after"]])
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
