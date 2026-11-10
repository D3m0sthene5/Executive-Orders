"""F3 reach: which undecided orders get a CURRENT: record from the new current-law extracts.

Proxy (no full claim-kit build): undecided rows of the compiled main kit, leads rebuilt from the new FRAGMENTS, new enrich_current.
In detail: take the undecided rows of the compiled main kit (jobs/claim-kit/output/STATUS_LEADS.jsonl in
the reference worktree), rebuild their current-law leads from the NEW jobs/current-law/output/FRAGMENTS.jsonl
with the claim kit's own collector (inputs._Collector.fragment), and run the NEW
current_evidence.enrich_current over them against this branch's held texts. build.package() and
status_overlay make CURRENT:{iid}#{n} exactly for leads that then carry text, char_start, char_end and
source. Leads from other producers (duodecim-tableiv, claim-drafts) are unchanged by F3 and still carry
no held text.

  python -I measure_f3.py REFERENCE_WORKTREE BRANCH_WORKTREE OUT_DIR
Writes REACH.json and DIAGNOSED.csv. Reads only; decides nothing.
"""
import collections
import csv
import json
import sys
from pathlib import Path

ref, branch, out = (Path(a).resolve() for a in sys.argv[1:4])
sys.path.insert(0, str(branch / "jobs/claim-kit"))
import current_evidence  # noqa: E402  (branch code)
import inputs  # noqa: E402

DIAGNOSED = ["EO:8695", "EO:10624", "EO:11225", "EO:11866", "EO:12661", "EO:13329", "EO:13411", "EO:13505",
             "EO:13647", "EO:13748", "EO:14051", "EO:14191", "EO:14233", "EO:14318", "EO:14435"]


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


undecided, with_any_lead, old_current = set(), set(), 0
for row in jsonl(ref / "jobs/claim-kit/output/STATUS_LEADS.jsonl"):
    if row.get("status") is not None:
        continue
    undecided.add(row["instrument_id"])
    leads = row.get("current_law_leads") or []
    if leads:
        with_any_lead.add(row["instrument_id"])
    old_current += sum(1 for d in leads if all(k in d for k in ("text", "char_start", "char_end", "source")))

universe = {iid: {"id": iid} for iid in undecided}
collector = inputs._Collector(branch, universe, [])
frag_path = branch / "jobs/current-law/output/FRAGMENTS.jsonl"
origin = frag_path.relative_to(branch).as_posix()
for rec in jsonl(frag_path):
    if rec.get("kind") in inputs.CURRENT_KINDS and rec.get("instrument_id") in undecided:
        collector.fragment(rec, frag_path.parent, origin)
keys, flat = [], []
for iid in sorted(collector.current):
    for lead in collector.current[iid]:
        keys.append(iid)
        flat.append(lead)
enriched = current_evidence.enrich_current(branch, flat)

ending = {}
with open(ref / "jobs/current-law/output/ORDERS_CURRENT_LAW.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        ending[r["instrument_id"]] = r.get("ending_statements_found") or ""

per_order = collections.defaultdict(list)
lead_counts = collections.Counter()
for iid, lead in zip(keys, enriched):
    ok = all(k in lead for k in ("text", "char_start", "char_end", "source"))
    lead_counts[(lead.get("basis_code"), ok)] += 1
    if ok:
        per_order[iid].append(lead)
cl_orders = set(collector.current)
reached = set(per_order)
by_basis = collections.Counter()
for iid, leads in per_order.items():
    for b in sorted({l.get("basis_code") for l in leads}):
        by_basis[b] += 1
printed = {i for i, ls in per_order.items() if any(l.get("basis_code") == "printed_eo_text" for l in ls)}
printed_no_end = {i for i in printed if not ending.get(i)}
other_only = reached - printed

report = {
    "proxy": __doc__.strip().splitlines()[2],
    "undecided_orders": len(undecided),
    "undecided_with_any_current_law_lead_on_main": len(with_any_lead),
    "current_records_on_main_before": old_current,
    "undecided_with_current_law_fragment_leads": len(cl_orders),
    "undecided_with_at_least_one_CURRENT_record_after": len(reached),
    "orders_by_basis_code_with_a_CURRENT_record": dict(sorted(by_basis.items())),
    "orders_with_printed_note_CURRENT": len(printed),
    "orders_with_printed_note_CURRENT_and_no_ending_statement_found": len(printed_no_end),
    "orders_with_printed_note_CURRENT_but_ending_statement_found": len(printed - printed_no_end),
    "orders_reached_only_by_other_kinds": len(other_only),
    "orders_reached_only_by_other_kinds_by_basis": dict(sorted(collections.Counter(
        b for i in other_only for b in sorted({l.get("basis_code") for l in per_order[i]})).items())),
    "leads_by_basis_and_CURRENT": {f"{b}|{'current' if ok else 'gap'}": n
                                   for (b, ok), n in sorted(lead_counts.items(), key=str)},
    "held_text_roots_used": dict(collections.Counter(
        l["source"]["text_path"].split("/output/")[0] for ls in per_order.values() for l in ls)),
}


def theophilus_texts(path):
    """Text representations the claim kit's walk_texts makes from one theophilus SOURCES.jsonl."""
    c = inputs._Collector(branch, {}, [])
    c.identity = lambda value: value if isinstance(value, str) and value.startswith("EO:") else None
    c.repo = path.parents[3]
    for rec in jsonl(path):
        c.walk_texts(rec, path.parent, "theophilus")
    return c.texts


def section_texts(texts):
    return [t for t in texts if "/texts/usc-" in t["text_path"] or "/texts/cfr-" in t["text_path"]]


old = section_texts(theophilus_texts(ref / "jobs/theophilus-sources/output/SOURCES.jsonl"))
new = section_texts(theophilus_texts(branch / "jobs/theophilus-sources/output/SOURCES.jsonl"))
acts, act_pairs = 0, collections.Counter()
for name in ("ACTING_PROVISIONS.jsonl", "ACTING_PROVISIONS.part0001.jsonl"):
    p = ref / "jobs/claim-kit/output" / name
    if p.is_file():
        for r in jsonl(p):
            tp = (r.get("actor_source") or {}).get("text_path") or ""
            if "theophilus-sources/output/texts/cfr-" in tp or "theophilus-sources/output/texts/usc-" in tp:
                acts += 1
                act_pairs[f"ACT:{r.get('target_id') or r.get('instrument_id')}>{r.get('actor_id')}"] += 1
report["theophilus_section_texts_declared_as_an_order_text_before"] = len(old)
report["theophilus_section_texts_declared_as_an_order_text_after"] = len(new)
report["main_ACTING_PROVISIONS_rows_with_a_theophilus_section_as_actor_text"] = acts
report["main_distinct_ACT_pairs_with_a_theophilus_section_as_actor_text"] = len(act_pairs)
report["example_ACT_pairs"] = act_pairs.most_common(8)

rows = []
for iid in DIAGNOSED:
    leads = per_order.get(iid, [])
    printed_leads = [l for l in leads if l.get("basis_code") == "printed_eo_text"]
    first = (printed_leads or leads or [None])[0]
    rows.append({"instrument_id": iid, "undecided": iid in undecided,
                 "current_law_leads": len(collector.current.get(iid, [])), "current_records": len(leads),
                 "basis_codes": ";".join(sorted({l.get("basis_code") for l in leads})),
                 "ending_statements_found": ending.get(iid, ""),
                 "first_where": first.get("where") if first else "",
                 "first_text_path": first["source"]["text_path"] if first else "",
                 "first_quote": (first["text"].replace("\n", " / ")[:300] if first else "")})
out.mkdir(parents=True, exist_ok=True)
(out / "REACH.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
with open(out / "DIAGNOSED.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print(json.dumps(report, indent=1, ensure_ascii=False))
for r in rows:
    print(r["instrument_id"], r["current_records"], r["basis_codes"], "|", r["first_quote"][:140])
