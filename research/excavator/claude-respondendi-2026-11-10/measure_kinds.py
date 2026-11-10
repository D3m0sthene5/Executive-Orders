"""Respondendi v2: reachable undecided orders per lot kind, upper bounds from machine leads on main, overlaps removed.

Inputs (all from origin/main 854514831e, claim-kit generation 2026-11-10T10:36Z):
  RBO.csv            = jobs/readiness-tracker/output/READINESS_BY_ORDER.csv (provisional_status empty = undecided)
  acc.json           = claim-kit OVERLAY_INPUTS 'selected' record: [grade, acceptable_as_original]
  ACTING_PROVISIONS* = later-instrument ACT leads; OWN_TERMS* = own-terms TERM leads; STATUS_LEADS = current-law leads
  pothier_leads.jsonl = jobs/pothier/output/LEADS.jsonl
Counts are eligibility upper bounds (machine leads), not findings about any order.
"""
import csv, glob, json, re, collections, sys
S = r"C:\Users\danie\AppData\Local\Temp\claude\9af2ede6b8b702e5\92631b4b-78ae-49d3-abe2-b3e13da19be1\scratchpad"
K = S + r"\kit-test\jobs\claim-kit\output"
CUTOFF = "2026-10-14"
ENDING = {"revoke", "supersede", "terminate", "abolish"}
TRACKER_TEXT = {"archival_replica_checked", "machine_read_government_printed_copy", "official_printing", "government_printed_copy"}
ADOPTED = {"EO:9674", "EO:11957", "EO:12348", "EO:9245", "EO:10679", "EO:11962"}

und = {r["instrument_id"] for r in csv.DictReader(open(S + r"\RBO.csv", encoding="utf-8")) if not r["provisional_status"]}
und -= ADOPTED
acc = json.load(open(S + r"\acc.json", encoding="utf-8"))


def text(iid):
    g, ok = acc.get(iid) or [None, False]
    return "original" if ok else ("working" if g in TRACKER_TEXT else "none")


express, via_parent, act_any = set(), set(), set()
for p in glob.glob(K + r"\ACTING_PROVISIONS*.jsonl"):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        t = r.get("target_id")
        if t not in und:
            continue
        act_any.add(t)
        prov = re.sub(r"\s+", " ", str(r.get("provision_text") or "")).lower()
        num = re.sub(r"\D", "", t)
        real_saving = any((re.sub(r"\s+", " ", str(ph)).lower()[:80] in prov) or re.search(r"(?<!\d)" + num + r"(?!\d)", str(ph))
                          for ph in r.get("savings_phrases") or [])
        if r.get("verb") in ENDING and not real_saving and (r.get("signing_date") or "") <= CUTOFF:
            if r.get("scope") == "whole" and r.get("names_target") and not r.get("reaches_target_via"):
                express.add(t)
            elif r.get("scope") == "whole_via_parent":
                via_parent.add(t)
own_end = set()
for p in glob.glob(K + r"\OWN_TERMS*.jsonl"):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        t = r.get("instrument_id")
        end = r.get("stated_end_date") or r.get("computed_end_candidate")
        if t in und and r.get("kind") in {"fixed_term", "sunset_date", "until_event"} and isinstance(end, str) and end <= CUTOFF:
            own_end.add(t)
current = set()
for l in open(K + r"\STATUS_LEADS.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r["instrument_id"] in und and any(c.get("basis_code") == "printed_eo_text" or "no ending statement" in str(c.get("legal_basis_candidate", ""))
                                         for c in r.get("current_law_leads") or []):
        current.add(r["instrument_id"])
spent, merged, pothier_no_whole, one_person = set(), set(), set(), set()
for l in open(S + r"\pothier_leads.jsonl", encoding="utf-8"):
    r = json.loads(l)
    t = r["instrument_id"]
    if t not in und:
        continue
    basis = (r.get("basis") or "").lower()
    if r.get("status_lead") == "no":
        if "p2" in basis or "merged into" in basis or "merges into the parent" in basis:
            merged.add(t)
        elif "p1" in basis or "exhausted" in basis or "performs one act" in basis or "takes effect when issued" in basis:
            spent.add(t)
        elif "revokes this order as a whole" in basis:
            pothier_no_whole.add(t)
    if "named person" in basis or "permission ended when used" in basis or "designee" in basis:
        one_person.add(t)

# Lot kinds in rule order; an order is counted once, in the first kind that reaches it.
kinds = [
    ("express_named_revocation", "active", lambda i: i in express | pothier_no_whole, "original"),
    ("own_terms_dated", "active", lambda i: i in own_end, "original"),
    ("express_named_revocation", "needs F6 (working text)", lambda i: i in express | pothier_no_whole, "working"),
    ("own_terms_dated", "needs F6 (working text)", lambda i: i in own_end, "working"),
    ("spent_on_issue", "needs F5 (OWN_TEXT basis)", lambda i: i in spent, "original+working"),
    ("follows_parent", "needs F5 (PARENT_END basis)", lambda i: i in via_parent | merged, "original+working"),
    ("yes_current", "needs F3 (CURRENT records)", lambda i: i in current and i not in act_any, "original+working"),
    ("outer_bound_one_person", "needs owner approval of the Ulpian ask", lambda i: i in one_person, "original+working"),
]
seen, rows = set(), []
for name, state, pred, tb in kinds:
    allowed = {"original": {"original"}, "working": {"working"}, "original+working": {"original", "working"}}[tb]
    hit = {i for i in und - seen if pred(i) and text(i) in allowed}
    seen |= hit
    by = collections.Counter("<7532" if int(re.sub(r"\D", "", i) or 0) < 7532 else ">=7532" for i in hit)
    rows.append({"kind": name, "text_basis": tb, "state": state, "orders": len(hit), "below_7532": by["<7532"], "from_7532": by[">=7532"]})
rest = und - seen
rows.append({"kind": "no kind reaches it on held leads", "text_basis": "", "state": "", "orders": len(rest),
             "below_7532": sum(1 for i in rest if int(re.sub(r'\D', '', i) or 0) < 7532), "from_7532": sum(1 for i in rest if int(re.sub(r'\D', '', i) or 0) >= 7532)})
out = {"undecided": len(und), "rows": rows, "notext": sum(1 for i in und if text(i) == "none"),
       "basis": "origin/main 854514831e; claim-kit generation 2026-11-10T10:36Z; machine leads, upper bounds"}
print(json.dumps(out, indent=1))
json.dump(out, open(S + r"\kinds.json", "w"), indent=1)
