"""Respondendi v2: reachable undecided orders per lot kind on main, upper bounds from machine leads, overlaps removed.

Uses the rule's own zero-token predicates (respondendi.named_end_in and RULE.md parameters) on the compiled leads.
Inputs, all from origin/main 854514831e (claim-kit generation 2026-11-10T10:36Z), copied to a scratch folder:
  RBO.csv             jobs/readiness-tracker/output/READINESS_BY_ORDER.csv (provisional_status empty = undecided)
  acc.json            claim-kit OVERLAY_INPUTS 'selected' record per order: [grade, acceptable_as_original]
  kit-test/jobs/claim-kit/output/{ACTING_PROVISIONS*, OWN_TERMS*, STATUS_LEADS}.jsonl  claim-kit compiled leads
  CATALOG_INDEX.csv   jobs/later-events/output/CATALOG_INDEX.csv (OFR disposition notes, EO 7532 and later only)
  pothier_leads.jsonl jobs/pothier/output/LEADS.jsonl
Counts are eligibility upper bounds (machine leads), not findings about any order: each still needs a producer, a
status review, two blind arms, typed controls, the checker and the audits.
usage: python -I measure_kinds.py SCRATCH_DIR REPO
"""
import csv, glob, json, re, collections, sys
from pathlib import Path

S, REPO = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(REPO / "jobs/respondendi-adoption"))
import respondendi as R  # noqa: E402

K = S / "kit-test/jobs/claim-kit/output"
params = R.parameters(REPO)
EXP, OWN, YES = (params["kinds"][k] for k in ("express_named_revocation", "own_terms", "yes_current"))
CUTOFF = params["cutoff"]
WORKING = set(params["text_bases"]["working"]["grades"])
ADOPTED = {"EO:9674", "EO:11957", "EO:12348", "EO:9245", "EO:10679", "EO:11962"}

und = {r["instrument_id"] for r in csv.DictReader(open(S / "RBO.csv", encoding="utf-8")) if not r["provisional_status"]} - ADOPTED
acc = json.load(open(S / "acc.json", encoding="utf-8"))


def text(iid):
    g, ok = acc.get(iid) or [None, False]
    return "original" if ok else ("working" if g in WORKING else "none")


notes = {r["id"]: R._norm(r.get("disposition_notes")) for r in csv.DictReader(open(S / "CATALOG_INDEX.csv", encoding="utf-8"))}
segs = {i: R._segments([t]) for i, t in notes.items()}
acts = collections.defaultdict(list)
for p in glob.glob(str(K / "ACTING_PROVISIONS*.jsonl")):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("target_id") in und:
            acts[r["target_id"]].append(r)


def express(iid):
    rows = acts.get(iid, [])
    if any(r.get("verb") in ("reinstate", "continue") for r in rows):
        return False
    for r in rows:
        actor = r.get("actor_id") or ""
        if not (r.get("scope") == "whole" and r.get("names_target") and not r.get("reaches_target_via")
                and r.get("verb") in EXP["act_verbs"] and (r.get("signing_date") or "9999") < CUTOFF):
            continue
        if any(x.get("actor_id") == actor and x.get("scope") == "partial" and x.get("verb") in EXP["act_verbs"] for x in rows):
            continue
        prov = str(r.get("provision_text") or "")
        if len(prov) > EXP["max_provision_chars"] or not R.named_end_in(prov, iid, EXP) or r.get("exceptions_text"):
            continue
        flat = R._norm(prov)
        if any(R._norm(ph)[:80] in flat or re.search(r"(?<!\d)" + re.escape(re.sub(r"\D", "", iid)) + r"(?!\d)", R._norm(ph))
               for ph in r.get("savings_phrases") or []):
            continue
        end = R._date(r.get("effective_date")) or R._date(r.get("signing_date"))
        num = re.sub(r"\D", "", actor)
        word = r"(eo|executive order)" if actor.startswith("EO:") else r"(proc|proclamation)"
        wit = re.compile(r"^(revoked|superseded|rescinded|terminated) by: ?" + word + r" ?(no )?" + num + r"\b")
        hits = [g for g in segs.get(iid, []) if wit.match(g) and not re.search(r"\(|\bpart|\bsec|\bsection", g)]
        if hits and not R._later_acts([notes.get(iid, "")], end, skip=hits[0]) and "reinstat" not in notes.get(iid, ""):
            return True
    return False


terms = collections.defaultdict(list)
for p in glob.glob(str(K / "OWN_TERMS*.jsonl")):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("instrument_id") in und:
            terms[r["instrument_id"]].append(r)


def own_terms(iid):
    if acts.get(iid) or actors.get(iid) or missing_named.get(iid):
        return False
    if any(re.match(r"(amended|continued|revoked|superseded|extended|modified|suspended) by", g) for g in segs.get(iid, [])):
        return False
    whole = {iid, iid + "#whole"}
    return any(t.get("kind") in OWN["term_kinds"] and (t.get("stated_end_date") or "9999") < CUTOFF and t.get("scope_id") in whole
               and re.search(OWN["term_text_pattern"], R._norm(t.get("text")))
               and not any(w in R._norm(t.get("text")) for w in OWN["extension_words"]) for t in terms.get(iid, []))


current, actors, missing_named, missing_any = set(), {}, {}, {}
for l in open(K / "STATUS_LEADS.jsonl", encoding="utf-8"):
    r = json.loads(l)
    iid = r["instrument_id"]
    if iid not in und:
        continue
    actors[iid] = r.get("lead_actor_ids") or []
    missing_any[iid] = r.get("missing") or []
    missing_named[iid] = [m for m in missing_any[iid] if re.search(r"\b(eo|proc|plo):", str(m).lower())]
    leads = r.get("current_law_leads") or []
    if any(c.get("basis_code") == "printed_eo_text" for c in leads) and not any(
            w in R._norm(json.dumps(leads)) for w in YES["ending_signals"]):
        current.add(iid)


def yes(iid):
    if iid not in current or acts.get(iid) or actors.get(iid) or missing_any.get(iid):
        return False
    if any(t.get("kind") in YES["ending_term_kinds"] for t in terms.get(iid, [])):
        return False
    labels = [(R.LABELS.match(g) or [None, ""])[1].strip() for g in segs.get(iid, [])]
    return all(l in YES["allowed_labels"] for l in labels) and not any(w in notes.get(iid, "") for w in YES["ending_signals"])


spent = set()
for l in open(S / "pothier_leads.jsonl", encoding="utf-8"):
    r = json.loads(l)
    basis = (r.get("basis") or "").lower()
    if r["instrument_id"] in und and r.get("status_lead") == "no" and (
            "p1" in basis or "p2" in basis or "merged into" in basis or "merges into the parent" in basis
            or "exhausted" in basis or "performs one act" in basis or "takes effect when issued" in basis):
        spent.add(r["instrument_id"])

kinds = [("express_named_revocation", "active", express), ("own_terms", "active", own_terms),
         ("spent_on_issue", "needs F5 (route own_text)", lambda i: i in spent), ("yes_current", "needs F3 (route current)", yes)]
seen, rows = set(), []


def band(ids):
    return collections.Counter("<7532" if int(re.sub(r"\D", "", i) or 0) < 7532 else ">=7532" for i in ids)


for name, state, pred in kinds:
    hit = {i for i in und - seen if text(i) != "none" and pred(i)}
    seen |= hit
    for tb in ("original", "working"):
        sub = {i for i in hit if text(i) == tb}
        b = band(sub)
        rows.append({"kind": name, "text_basis": tb, "state": state if tb == "original" else state + "; working text needs F6",
                     "orders": len(sub), "below_7532": b["<7532"], "from_7532": b[">=7532"]})
rest = und - seen
b = band(rest)
rows.append({"kind": "no kind reaches it on held leads", "text_basis": "", "state": "", "orders": len(rest),
             "below_7532": b["<7532"], "from_7532": b[">=7532"]})
out = {"undecided": len(und), "rows": rows, "rule_sha256": R.rule_sha(REPO),
       "limits": ["second witness read only from the OFR catalog (EO 7532 and later); older orders need another catalog note in their frozen history",
                  "spent_on_issue counted from Pothier P1/P2 leads only (all below EO 7532); the F5 classifier itself reaches 763 undecided orders (246 spent_on_issue, 517 amends_parent; Accursius, branch accursius/f5-f6-overlay, measured precision 42 of 50)",
                  "dossier ACTOR_TEXT records are approximated by the compiled lead_actor_ids",
                  "machine leads: upper bounds, not findings"],
       "basis": "origin/main 854514831e; claim-kit generation 2026-11-10T10:36Z"}
print(json.dumps(out, indent=1))
