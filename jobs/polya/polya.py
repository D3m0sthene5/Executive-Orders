#!/usr/bin/env python3
"""POLYA: alternative formulations of the problem, and the measured leverage of each.

Standard library only.  Run from anywhere:  python3 -I jobs/polya/polya.py <command>

  frames                      list the formulations ("frames") and what each treats as the unit of work
  leverage <frame> [--top N]  units of that frame ranked by not-ready orders reached, and the step advanced
  compare                     every frame side by side: reach, concentration (Gini), top-20, top-10/100 coverage
  export [--top N]            candidate actions for Llull's `voi --actions` (output/CANDIDATE_ACTIONS.json)

Everything is a count over committed job outputs.  Reach is the number of not-ready orders a unit
could move forward one step.  It is NOT a yield: orders made ready are not estimated here.  Reads
only; writes only jobs/polya/output/ (aggregate counts and unit ids, no per-order lists).
Never changes the codebook, a status, a tier or the certified count (0).
"""
import argparse, collections, csv, glob, hashlib, json, os, subprocess, sys

sys.dont_write_bytecode = True
csv.field_size_limit(1 << 28)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(os.path.dirname(HERE))
STEPS = ["provisional_status", "original_text", "clause_inventory", "ending_or_current_basis",
         "savings_residuals", "counterevidence", "shared_sources", "opus_media"]
END = {"revocation", "supersession", "supersession_or_revocation", "termination", "abolition",
       "rescission", "nullification", "expiration", "authority_repeal", "ceased_to_function"}
SCHEMA = "polya/1"
RULES = ["counts are measured from committed job outputs at repo_head",
         "reach is not yield: orders a unit could advance one step, not orders made ready",
         "AI statuses are hypotheses; no codebook change; no tier promotion; certified stays 0"]


# ------------------------------------------------------------------ pure statistics
def gini(values):
    """Gini coefficient of non-negative leverage values (0 = all units equal, toward 1 = one unit has all)."""
    v = sorted(x for x in values if x >= 0)
    n, s = len(v), sum(v)
    if n == 0 or s == 0:
        return 0.0
    return round((2 * sum((i + 1) * x for i, x in enumerate(v)) - (n + 1) * s) / (n * s), 4)


def ranked(units):
    """[(unit, set)] by leverage desc, then unit name (deterministic)."""
    return sorted(((u, o) for u, o in units.items() if o), key=lambda x: (-len(x[1]), x[0]))


def coverage(units, pool, ks=(10, 100)):
    """Share of `pool` reached by the union of the top-k units ranked by leverage ("topK"), and by a
    greedy max-coverage choice of k units ("greedyK": marginal gain each step, the best k units can do)."""
    rk = ranked({u: set(o) & pool for u, o in units.items()})
    out = {}
    for k in ks:
        top = set().union(*[o for _, o in rk[:k]]) if rk else set()
        out["top%d" % k] = round(len(top) / len(pool), 4) if pool else 0.0
    covered, got = set(), {}
    for j in range(1, max(ks) + 1):
        best, bg = None, 0
        for u, o in rk:
            g = len(o - covered)
            if g > bg:
                best, bg = o, g
        if best is None:
            break
        covered |= best
        if j in ks:
            got["greedy%d" % j] = round(len(covered) / len(pool), 4)
    for k in ks:
        got.setdefault("greedy%d" % k, round(len(covered) / len(pool), 4) if pool else 0.0)
    out.update(got)
    return out


def dist(units, pool):
    """Leverage distribution of one view; `pool` restricts to the orders that count."""
    cl = {u: set(o) & pool for u, o in units.items()}
    rk = ranked(cl)
    vals = [len(o) for _, o in rk]
    tot = sum(vals)
    union = set().union(*[o for _, o in rk]) if rk else set()
    q = lambda p: vals[min(len(vals) - 1, int(p * len(vals)))] if vals else 0
    return {
        "units": len(vals), "distinct_orders_reached": len(union), "sum_leverage": tot,
        "overlap_factor": round(tot / len(union), 3) if union else 0,
        "max": vals[0] if vals else 0, "median": q(0.5), "p90": q(0.10),
        "units_ge_10": sum(v >= 10 for v in vals), "units_ge_50": sum(v >= 50 for v in vals),
        "gini": gini(vals),
        "top10_share_of_sum": round(sum(vals[:10]) / tot, 3) if tot else 0,
        "pct_of_pool_reached": round(len(union) / len(pool), 4) if pool else 0,
        "coverage": coverage(cl, pool),
    }


# ------------------------------------------------------------------ data
def jsonl(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def git_head(repo):
    try:
        r = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or None
    except Exception:
        return None


class Missing(Exception):
    pass


class Ctx:
    """Readiness pool plus file access.  A missing input makes that frame 'unavailable', not a crash."""

    def __init__(self, repo):
        self.repo = repo
        self.consumed = {}
        self.rows = {}
        self.need('jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')
        with open(self.p("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"), encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                self.rows[r["instrument_id"]] = r
        R = self.rows
        self.notready = {k for k, r in R.items() if r["ready_for_human_review"] != "yes"}
        self.decided = {k for k, r in R.items() if r["provisional_status"] in ("yes", "no")}
        self.dec_nr = self.notready & self.decided
        self.undec = self.notready - self.decided
        self.head = git_head(repo)

    def p(self, rel):
        return os.path.join(self.repo, rel)

    def open_steps(self, i):
        return [s for s in STEPS if self.rows[i].get("step_" + s) == "open"]

    def blockers(self, i):
        return [b for b in self.rows[i].get("blockers", "").split("|") if b]

    def need(self, *rels):
        matched = {r: sorted(glob.glob(self.p(r))) for r in rels}
        for path in (p for paths in matched.values() for p in paths if os.path.isfile(p)):
            sha = self.file_sha(path)
            if path in self.consumed and self.consumed[path] != sha:
                raise RuntimeError('Input changed during Polya calculation: ' + path)
            self.consumed[path] = sha
        miss = [r for r, paths in matched.items() if not paths]
        if miss:
            raise Missing(miss)

    @staticmethod
    def file_sha(path):
        h = hashlib.sha256()
        with open(path, 'rb') as fh:
            for block in iter(lambda: fh.read(1 << 20), b''): h.update(block)
        return h.hexdigest()

    def snapshot(self):
        files = {}
        for path, sha in sorted(self.consumed.items()):
            if self.file_sha(path) != sha:
                raise RuntimeError('Input changed during Polya calculation: ' + path)
            files[os.path.relpath(path, self.repo)] = sha
        payload = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
        return {'repo_head': self.head, 'input_files_sha256': files,
                'snapshot_sha256': hashlib.sha256(payload).hexdigest(),
                'basis': 'Exact consumed bytes; repo_head alone does not establish output freshness.'}


def view(name, units, pool, steps, label="", note="", aggregate_only=False, difficulty=None):
    """One leverage view: unit -> set(orders).  `steps` = tracker steps a unit advances (None = not a step)."""
    return {"name": name, "units": units, "pool": pool, "steps": steps, "label": label,
            "note": note, "aggregate_only": aggregate_only, "difficulty": difficulty}


# ------------------------------------------------------------------ frames (each returns a list of views)
def f0(c):
    units = {i: {i} for i in c.notready}
    return [view("orders", units, c.notready, None, "all steps of the order",
                 "baseline: every plan so far; leverage is 1 for every unit", True)]


def f1(c):
    c.need("jobs/later-events/output/EDGES.csv")
    ed, eu = collections.defaultdict(set), collections.defaultdict(set)
    with open(c.p("jobs/later-events/output/EDGES.csv"), encoding="utf-8", newline="") as fh:
        for e in csv.DictReader(fh):
            a, t = e["acting_id"], e["target_id"]
            if e["mechanism"] not in END or not a or not t or t not in c.rows:
                continue
            if t in c.dec_nr and c.rows[t]["provisional_status"] == "no" and c.rows[t]["step_ending_or_current_basis"] == "open":
                ed[a].add(t)
            elif t in c.undec:
                eu[a].add(t)
    cav = "upper bound: an edge is an editorial lead and need not be the target's FIRST end (X1 lesson)"
    return [view("ending_of_decided_NO", ed, c.dec_nr, ["ending_or_current_basis"], "cite the end of decided-NO targets", cav),
            view("NO_hypothesis_for_undecided", eu, c.undec, ["provisional_status"], "propose NO status (hypothesis) for undecided targets", cav)]


def f2(c):
    c.need("jobs/claim-kit/output/MISSING_SOURCES.jsonl")
    by, n, xref = collections.defaultdict(set), 0, 0
    for r in jsonl(c.p("jobs/claim-kit/output/MISSING_SOURCES.jsonl")):
        if r.get("target_id") in c.dec_nr:
            by[r["actor_id"]].add(r["target_id"])
            n += 1
            xref += (r.get("source_event") or {}).get("mechanism") == "cross_reference"
    return [view("actor_provision_record", by, c.dec_nr, ["ending_or_current_basis"],
                 "locate the actor's target-naming provision (ACT/TERM record)",
                 "STATUS_LEADS can show spurious actors for low numbers (e.g. EO:1); check edge_ids. "
                 "%d of %d actor-target records are 'See:' cross_references, which locate a mention, not an end; "
                 "same work as F1 when the actor also has an ending edge (e.g. EO:12553)" % (xref, n))]


def families(c):
    c.need("jobs/claim-kit/output/FAMILIES.json")
    with open(c.p("jobs/claim-kit/output/FAMILIES.json"), encoding="utf-8") as fh:
        return json.load(fh)


def f3(c):
    fams = families(c)
    src = {f["family_id"]: set(f["instrument_ids"]) & c.notready for f in fams if f["family_id"].startswith("source:")}
    shared = collections.defaultdict(set)
    for i in c.notready:
        for b in c.blockers(i):
            if b.startswith("SHARED_SOURCE_NOT_RETRIEVED"):
                shared[b.split(":", 1)[1] if ":" in b else b].add(i)
    return [view("claim_kit_source_family", src, c.notready, ["original_text"], "read one held source for all orders it serves",
                 "flat: sources mostly serve 1-2 orders"),
            view("tracker_shared_source", shared, c.notready, ["shared_sources"], "retrieve one shared source")]


def f4(c):
    fams = families(c)
    fam = {f["family_id"]: set(f["instrument_ids"]) & c.dec_nr for f in fams
           if f["family_id"].split(":")[0] in ("own_term", "parent", "actor")}
    out = [view("claim_kit_family", fam, c.dec_nr, ["ending_or_current_basis"], "prove the family rule once, check members",
                "own_term wording is a lead (a report deadline never ends an order); families overlap")]
    if glob.glob(c.p("jobs/x1-class-engine/output/CLUSTER_MEMBERS.csv")):
        c.need('jobs/x1-class-engine/output/CLUSTER_MEMBERS.csv')
        x1 = collections.defaultdict(set)
        with open(c.p("jobs/x1-class-engine/output/CLUSTER_MEMBERS.csv"), encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["instrument_id"] in c.notready:
                    x1[r["cluster_id"] + ":" + r["type"]].add(r["instrument_id"])
        out.append(view("x1_text_cluster", x1, c.notready, ["clause_inventory"], "clone one cluster's clause inventory"))
    return out


def f5(c):
    pre1937 = {i for i in c.notready if i.split(":")[1].isdigit() and int(i.split(":")[1]) < 7532}

    def having(b):
        return {i for i in c.notready if any(x == b or x.startswith(b + ":") for x in c.blockers(i))}
    try:
        fam = {f["family_id"]: set(f["instrument_ids"]) & c.dec_nr for f in families(c)}
    except Missing:
        fam = {}
    u = {
        "Q_compiled_transcription_as_acceptable_copy (codebook reading only)": having("ONLY_COMPILED_TRANSCRIPTION_FOUND"),
        "Q_batch_adoption_of_reviewed_status_overlays (owner yes/no)": set(c.undec),
        "Q_send_ProQuest_NYU_access_request (owner; ceiling)": having("NO_OFFICIAL_SOURCE_LOCATED") & pre1937,
        "Q_medium_low_confidence_page_location_rule": having("ORIGINAL_FOUND_NEEDS_PAGE_CHECK"),
        "Q_contrary_machine_lead_disposition_rule": having("MACHINE_SEARCH_FOUND_CONTRARY_LEAD"),
        "Q_report_deadline_own_term_end_reading": fam.get("own_term:report_deadline", set()),
    }
    return [view("owner_or_codebook_question", u, c.notready, None, "a ruling gates the blocker behind it (never a codebook change)",
                 "reach is a ceiling: a decision unlocks work, the answer may be no; per-order work remains")]


def classify_missing(m):
    if m.startswith("target provision not located") or m.startswith("acting text absent"):
        return "ACT_actor_provision"
    if "Current" in m or "current-law" in m or "legal-text slice" in m:
        return "CURRENT_predicate"
    if "Held representation is a lead" in m or "No attributed held text" in m or "page location" in m:
        return "ORIGINAL_text"
    if "clause inventory" in m:
        return "INVENTORY"
    if "Large actor context" in m:
        return "LARGE_ACTOR_CONTEXT_read"
    return "OTHER"


def f6(c):
    c.need("jobs/claim-kit/output/dossiers/*.json")
    typ, sole = collections.defaultdict(set), collections.defaultdict(set)
    seen = set()
    for f in sorted(glob.glob(c.p("jobs/claim-kit/output/dossiers/*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        i = d.get("instrument_id")
        if i not in c.dec_nr:
            continue
        seen.add(i)
        ts = {classify_missing(m) for m in d.get("missing") or []}
        for t in ts:
            typ[t].add(i)
        if not ts:
            sole["NONE_listed_missing (judgment only)"].add(i)
        elif len(ts) == 1:
            sole["ONLY_" + next(iter(ts))].add(i)
    if c.dec_nr - seen:
        raise Missing(['complete decided not-ready dossier population (%d missing)' % len(c.dec_nr - seen)])
    return [view("missing_input_type", dict(typ), c.dec_nr, None, "build each input type's producer once",
                 "step by type: ORIGINAL->original_text, ACT/CURRENT->ending_or_current_basis, INVENTORY->clause_inventory"),
            view("sole_missing_type", dict(sole), c.dec_nr, None, "orders whose ONLY listed gap is this type (or none)",
                 "NONE_listed_missing means the dossier lists nothing missing: a reading of the dossier, not proof")]


def f7(c):
    c.need("jobs/current-law/output/MENTIONS.csv")
    yes_nr = {i for i in c.dec_nr if c.rows[i]["provisional_status"] == "yes"}
    pred = collections.defaultdict(set)
    with open(c.p("jobs/current-law/output/MENTIONS.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["instrument_id"] in yes_nr and r["is_predicate_lead"] == "yes":
                pred[r["citation"]].add(r["instrument_id"])
    return [view("current_law_citation", pred, yes_nr, ["ending_or_current_basis"],
                 "hold one USC/CFR slice with sha256, checked to cutoff", "a mention is a pointer; the predicate needs judgment")]


def urls_in(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "url" and isinstance(v, str):
                acc.add(v)
            else:
                urls_in(v, acc)
    elif isinstance(o, list):
        for v in o:
            urls_in(v, acc)


def f8(c):
    c.need("research/readiness/claims/*.jsonl")
    latest = {}
    for f in sorted(glob.glob(c.p("research/readiness/claims/*.jsonl"))):
        for cl in jsonl(f):
            latest[cl.get("instrument_id")] = cl
    cites = collections.defaultdict(set)
    for i, cl in latest.items():
        acc = set()
        urls_in(cl, acc)
        for u in acc:
            cites[u].add(i)
    near = collections.defaultdict(set)
    for i in c.dec_nr:
        o = c.open_steps(i)
        if len(o) in (1, 2):
            near["+".join(sorted(o))].add(i)
    return [view("reviewer_source_url", cites, set(latest), None, "a source the independent reviewer reads once for many claims",
                 "pool = orders with a claim record (not a not-ready pool)"),
            view("near_ready_open_step_set", near, c.dec_nr, None, "decided orders with 1-2 open steps, by step set",
                 "frontier: closes to ready if the steps are done")]


def f9(c):
    sb = collections.defaultdict(set)
    for i in c.notready:
        b = c.blockers(i)
        if len(b) == 1:
            sb[b[0]].add(i)
    return [view("sole_blocker", sb, c.notready, None, "orders where this is the ONLY blocker",
                 "blocker codes do not track every open step: clearing a sole blocker does NOT by itself make an order "
                 "ready (NO_PROVISIONAL_STATUS orders still have 5 open steps); see reached_with_le2_open_steps")]


FRAMES = [
    ("F0_order", "baseline: the formulation every prior plan used", "one executive order", "all steps of that order", f0),
    ("F1_ending_instrument", "change the unknown: solve the actor, not the target", "one acting instrument that revokes/supersedes/terminates others", "ending_or_current_basis (decided NO) / provisional_status (undecided)", f1),
    ("F2_actor_provision_record", "auxiliary element: the missing link is the actor's located provision", "one acting order whose target-naming provision is not located", "ending_or_current_basis", f2),
    ("F3_source_document", "generalize: one document read serves every order it contains or cites", "one held source document", "original_text / shared_sources", f3),
    ("F4_legal_family_template", "analogy: prove the rule once, check each member briefly", "one legal family or X1 text cluster", "ending_or_current_basis / clause_inventory", f4),
    ("F5_owner_or_codebook_decision", "work backwards to the precondition nobody can compute: a human ruling", "one owner decision or codebook reading question", "the gated blocker (reach is a ceiling)", f5),
    ("F6_missing_input_type", "decompose the unknown by data type; build each producer once", "one missing input type", "original_text / ending_or_current_basis / clause_inventory", f6),
    ("F7_aux_current_predicate_table", "auxiliary problem: build the current-law predicate table once", "one USC/CFR provision slice", "ending_or_current_basis for YES orders", f7),
    ("F8_work_backwards_reviewer", "work backwards: start from what the independent human must check", "one source URL the reviewer reads, or one near-ready step set", "reviewer cost / ready", f8),
    ("F9_single_blocker_frontier", "specialize: inspect cases sharing one recorded blocker category", "one blocker category (possibly many research actions)", "research grouping; no readiness implication", f9),
]
BYID = {f[0]: f for f in FRAMES}


def resolve(name):
    n = name.strip().lower()
    for k in BYID:
        if n == k.lower() or n == k.split("_")[0].lower():
            return k
    hits = [k for k in BYID if n in k.lower()]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit("unknown frame %r; try: %s" % (name, ", ".join(BYID)))


def step_filter(c, views):
    """A unit only advances an order whose advanced step is still OPEN: drop orders where every step the
    view advances is already done/n.a. (adversarial review: held-source families mostly hit orders whose
    original_text is done).  The number dropped is kept on the view so the filter stays visible."""
    for v in views:
        if not v["steps"]:
            continue
        kept, dropped = {}, set()
        for u, o in v["units"].items():
            ok = {i for i in o if i in c.rows and any(c.rows[i].get("step_" + s) == "open" for s in v["steps"])}
            dropped |= set(o) - ok
            if ok:
                kept[u] = ok
        v["units"], v["dropped_orders_step_not_open"] = kept, len(dropped & v["pool"])
    return views


def build(c, fid):
    """-> (views, None) or (None, reason)."""
    try:
        return step_filter(c, BYID[fid][4](c)), None
    except Missing as m:
        return None, "unavailable: missing input " + ", ".join(m.args[0])


def would_complete(c, orders, steps):
    """Upper bound: reached orders whose ONLY open steps are the ones this view's units advance."""
    if not steps:
        return None
    s = set(steps)
    return sum(1 for i in orders if i in c.rows and c.open_steps(i) and set(c.open_steps(i)) <= s)


def closeness(c, orders):
    """How near to ready the reached orders are: counts of open tracker steps (blockers are a weaker proxy)."""
    n = [len(c.open_steps(i)) for i in orders if i in c.rows]
    n.sort()
    return {"reached_with_le2_open_steps": sum(x <= 2 for x in n), "median_open_steps_of_reached": n[len(n) // 2] if n else None}


def remaining_prerequisites(c, orders, steps):
    """Counts of existing tracker steps outside a proposed advance, without replaying readiness."""
    proposed = set(steps or [])
    remaining = collections.Counter(st for i in set(orders) if i in c.rows
                                    for st in c.open_steps(i) if st not in proposed)
    return {'remaining_open_steps_by_kind': dict(sorted(remaining.items())),
            'hypothetical_completion_potential': would_complete(c, orders, steps),
            'realized_integrated_ready_change': None,
            'completion_potential_basis': 'Assumes the proposed steps are fully satisfied for every affected clause; no action or legal review has been executed.'}


def view_report(c, v, top=20):
    pool = v["pool"]
    d = dist(v["units"], pool)
    union = set().union(*[set(o) & pool for o in v["units"].values()]) if v["units"] else set()
    rep = {"view": v["name"], "advances_step": v["steps"] if v["steps"] else "n/a (see note)", "what": v["label"], "note": v["note"],
           "pool_size": len(pool), "dropped_orders_step_not_open": v.get("dropped_orders_step_not_open", 0),
           "pool_already_ready": len(pool) - len(pool & c.notready), **d, **closeness(c, union), "reached_with_no_other_open_step_upper_bound": would_complete(c, union, v["steps"])}
    rep.update(remaining_prerequisites(c, union, v['steps']))
    if v["aggregate_only"]:
        rep["top"] = []
        rep["open_steps_histogram_not_ready"] = {str(k): n for k, n in sorted(collections.Counter(len(c.open_steps(i)) for i in c.notready).items())}
        rep["open_steps_histogram_decided_not_ready"] = {str(k): n for k, n in sorted(collections.Counter(len(c.open_steps(i)) for i in c.dec_nr).items())}
        return rep
    rep["top"] = [{"unit": u, "orders": len(o), "step": v["steps"], "steps_complete_if_done_upper_bound": would_complete(c, o, v["steps"])}
                  for u, o in ranked({k: set(x) & pool for k, x in v["units"].items()})[:top]]
    return rep


# ------------------------------------------------------------------ commands
def pool_block(c):
    return {"orders": len(c.rows), "ready": len(c.rows) - len(c.notready), "not_ready": len(c.notready),
            "decided_not_ready": len(c.dec_nr), "undecided": len(c.undec)}


def write(out, name, obj):
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, name)
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    return path


def rel(c, p):
    return os.path.relpath(p, c.repo) if p.startswith(c.repo) else p


def cmd_frames(a, c):
    rows = [{"frame": f[0], "polya_move": f[1], "unit": f[2], "advances_step": f[3]} for f in FRAMES]
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            print("%-32s unit: %s\n%32s move: %s | advances: %s" % (r["frame"], r["unit"], "", r["polya_move"], r["advances_step"]))
    return 0


def cmd_leverage(a, c):
    fid = resolve(a.frame)
    views, why = build(c, fid)
    if why:
        print(fid, why)
        return 1
    rep = {"schema": SCHEMA, "repo_head": c.head, "frame": fid, "unit": BYID[fid][2], "polya_move": BYID[fid][1],
           "pool": pool_block(c), "rules": RULES, "views": [view_report(c, v, a.top) for v in views]}
    rep['input_snapshot'] = c.snapshot()
    path = write(a.output, "LEVERAGE_%s.json" % fid, rep)
    for v in rep["views"]:
        print("%s / %s: units=%d reach=%d (%.1f%% of pool %d) max=%d gini=%.3f top10/100 cover %.1f%%/%.1f%%  step=%s" % (
            fid, v["view"], v["units"], v["distinct_orders_reached"], 100 * v["pct_of_pool_reached"], v["pool_size"],
            v["max"], v["gini"], 100 * v["coverage"]["top10"], 100 * v["coverage"]["top100"], v["advances_step"]))
        for t in v["top"][: a.top]:
            ub = t["steps_complete_if_done_upper_bound"]
            print("   %6d  %-60s %s" % (t["orders"], t["unit"][:60], "" if ub is None else "(%d of them have no other open step)" % ub))
    print("wrote", rel(c, path))
    return 0


def cmd_compare(a, c):
    frames = []
    reached_union = set()
    nr, dnr = c.notready, c.dec_nr
    matrix = {st: {"open_in_not_ready": sum(1 for i in nr if c.rows[i].get("step_" + st) == "open"),
                   "open_in_decided_not_ready": sum(1 for i in dnr if c.rows[i].get("step_" + st) == "open"),
                   "views_that_reach_orders_with_this_step_open": {}} for st in STEPS}
    covered_steps = collections.defaultdict(set)   # order -> steps some non-baseline frame unit can advance
    for fid, move, unit, step, _ in FRAMES:
        views, why = build(c, fid)
        if why:
            frames.append({"frame": fid, "status": why})
            continue
        if fid != "F0_order":
            for v in views:
                for o in (set().union(*v["units"].values()) & nr if v["units"] else set()):
                    covered_steps[o] |= set(v["steps"] or [])
        units_all, reached = {}, set()
        for v in views:
            for st in (v["steps"] or []):
                union_v = set().union(*[set(o) & nr for o in v["units"].values()]) if v["units"] else set()
                n = sum(1 for i in union_v if c.rows[i].get("step_" + st) == "open")
                if fid != "F0_order":
                    matrix[st]["views_that_reach_orders_with_this_step_open"][fid.split("_")[0] + "/" + v["name"]] = n
            for u, o in v["units"].items():
                units_all.setdefault(v["name"] + "|" + u, set()).update(set(o) & nr)
        for o in units_all.values():
            reached |= o
        if fid != 'F0_order': reached_union |= reached
        merged = dist(units_all, nr)
        vrep = [view_report(c, v, 20) for v in views]
        frames.append({
            "frame": fid, "status": "measured", "unit": unit, "polya_move": move, "advances_step": step,
            "orders_reachable": len(reached), "pct_not_ready_reachable": round(len(reached) / len(nr), 4),
            "decided_not_ready_reachable": len(reached & dnr), "pct_decided_not_ready_reachable": round(len(reached & dnr) / len(dnr), 4),
            "units": merged["units"], "gini": merged["gini"], "max_unit": merged["max"], "overlap_factor": merged["overlap_factor"],
            "coverage_all_views": merged["coverage"],
            **{k: v for k, v in closeness(c, reached).items()},
            "reached_with_no_other_open_step_upper_bound": [(r["view"], r["reached_with_no_other_open_step_upper_bound"]) for r in vrep],
            "top20_units": ("aggregate only (one order per unit)" if fid == "F0_order"
                            else [{"unit": u, "orders": len(o)} for u, o in ranked(units_all)[:20]]),
            "views": [{k: r[k] for k in ("view", "advances_step", "pool_size", "units", "distinct_orders_reached", "gini", "max", "median", "coverage", "reached_with_le2_open_steps", "reached_with_no_other_open_step_upper_bound", "remaining_open_steps_by_kind", "hypothetical_completion_potential", "realized_integrated_ready_change")} for r in vrep],
        })
    uncovered = collections.Counter()
    for i in dnr:
        miss = tuple(st for st in c.open_steps(i) if st not in covered_steps.get(i, ()))
        uncovered[miss] += 1
    stack = {"decided_not_ready": len(dnr), "all_open_steps_have_a_frame_unit": uncovered.get((), 0),
             "uncovered_step_sets_top": [{"steps_no_frame_reaches": list(k), "orders": n} for k, n in uncovered.most_common(6)],
             "reading": "an order can only be made ready by stacking units from several frames; steps no frame reaches stay per-order work"}
    doc = {"schema": SCHEMA, "repo_head": c.head, "pool": pool_block(c), "rules": RULES,
           "stack": stack,
           "reading": ("Reach counts are upper bounds on one-step advances.  Frames overlap, so reaches must not be added.  "
                       "A frame beats the order baseline only if few units reach many orders (high Gini, top-10/100 coverage) "
                       "AND the step they advance is the one that blocks readiness.  Yield is not estimated here."),
           "step_matrix": matrix,
           "step_matrix_reading": "steps with an empty views map have no frame that places a unit on them (a measured gap, not a judgement)",
           "frames": frames}
    doc.update(input_snapshot=c.snapshot(), distinct_not_ready_orders_reached_across_nonbaseline_frames=len(reached_union),
               realized_integrated_ready_change=None)
    p = write(a.output, "COMPARE.json", doc)
    lines = ["# POLYA compare (generated; repo_head %s)" % c.head, "",
             "Pool: %d orders, %d ready, %d not ready (%d decided, %d undecided). Reach is not yield." % (
                 doc["pool"]["orders"], doc["pool"]["ready"], doc["pool"]["not_ready"], doc["pool"]["decided_not_ready"], doc["pool"]["undecided"]), "",
             "| frame | units | orders reachable | % not-ready | Gini | max unit | top10 covers | top100 covers | greedy top10 | reached with <=2 open steps | median open steps |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for f in frames:
        if f["status"] != "measured":
            lines.append("| %s | %s |  |  |  |  |  |  |  |  |  |" % (f["frame"], f["status"]))
            continue
        cv = f["coverage_all_views"]
        lines.append("| %s | %d | %d | %.1f%% | %.2f | %d | %.1f%% | %.1f%% | %.1f%% | %d | %s |" % (
            f["frame"], f["units"], f["orders_reachable"], 100 * f["pct_not_ready_reachable"], f["gini"], f["max_unit"],
            100 * cv["top10"], 100 * cv["top100"], 100 * cv["greedy10"], f["reached_with_le2_open_steps"], f["median_open_steps_of_reached"]))
    lines += ['', 'Distinct not-ready orders reached across nonbaseline frames: %d (deduplicated union).' % len(reached_union),
              'Potential is conditional on completing all affected clauses. Realized readiness change is unmeasured. A single blocker category can require several research actions.',
              'Input snapshot SHA-256: ' + doc['input_snapshot']['snapshot_sha256'],
              "", "| step | open (not ready) | open (decided, not ready) | views reaching orders with it open |", "|---|---:|---:|---|"]
    for st, m in matrix.items():
        vs = m["views_that_reach_orders_with_this_step_open"]
        lines.append("| %s | %d | %d | %s |" % (st, m["open_in_not_ready"], m["open_in_decided_not_ready"],
                                               ", ".join("%s %d" % kv for kv in sorted(vs.items(), key=lambda x: -x[1])) or "NONE"))
    lines += ["", "Stack: %d of %d decided not-ready orders have every open step reachable by some frame's unit; the rest need steps no frame covers." % (
        stack["all_open_steps_have_a_frame_unit"], stack["decided_not_ready"])]
    for u in stack["uncovered_step_sets_top"]:
        lines.append("- %d orders: no frame reaches %s" % (u["orders"], ", ".join(u["steps_no_frame_reaches"]) or "(none)"))
    write(a.output, "COMPARE.md", "\n".join(lines) + "\n")
    print("\n".join(lines))
    print("wrote", rel(c, p))
    return 0


def cmd_export(a, c):
    acts, seen = [], collections.defaultdict(list)
    for fid, move, unit, step, _ in FRAMES:
        if fid == "F0_order":
            continue
        views, why = build(c, fid)
        if why:
            continue
        for v in views:
            for rank, (u, o) in enumerate(ranked({k: set(x) & v["pool"] for k, x in v["units"].items()})[: a.top], 1):
                n = len(o)
                if n < a.min_reach:
                    break
                nr = o & c.notready
                seen[u].append("POLYA:%s:%s:%s" % (fid.split("_")[0], v["name"], u))
                acts.append({
                    "action_id": "POLYA:%s:%s:%s" % (fid.split("_")[0], v["name"], u),
                    "frame": fid, "view": v["name"], "unit": u, "rank_in_view": rank,
                    "title": "%s: %s" % (v["label"] or unit, u),
                    "tier_hint": "agent_probe", "advances_step": v["steps"],
                    "reach_orders": n, "reach_decided_not_ready": len(o & c.dec_nr), "reach_undecided": len(o & c.undec),
                    "reach_already_ready": n - len(nr),
                    "steps_complete_if_done_upper_bound": would_complete(c, nr, v["steps"]),
                    **remaining_prerequisites(c, nr, v['steps']),
                    "ceiling_orders": len(nr),
                    "cost_usd": None, "E_ready": None, "reference_class": None,
                    "requires_unmeasured": ["conversion of reach to accepted claims", "cost per accepted claim for this unit type"],
                    "status": "hypothesis", "caveat": v["note"] or None, "repo_head": c.head,
                })
    for x in acts:   # the same unit (e.g. EO:12553) can appear in several frames: one piece of work, not several
        x["same_unit_actions"] = [y for y in seen[x["unit"]] if y != x["action_id"]]
    doc = {"schema": "polya.actions/1", "consumer": "llull voi --actions (see research/plans/POLYA_DESIGN.md section 5)",
           "repo_head": c.head, "pool": pool_block(c), "rules": RULES,
           "note": ("ceiling_orders is not-ready reach (a Domesday-style ceiling), never a forecast; already-ready orders are "
                    "excluded from it. Reach must not be summed across actions: frames overlap and same_unit_actions "
                    "lists the same unit under another frame. cost_usd, E_ready and "
                    "reference_class are null on purpose: Llull fills them from measured reference classes."),
           "actions": acts}
    doc['input_snapshot'] = c.snapshot()
    p = write(a.output, "CANDIDATE_ACTIONS.json", doc)
    print("exported %d candidate actions -> %s" % (len(acts), rel(c, p)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="polya", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--output", default=None, help="default <repo>/jobs/polya/output")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("frames")
    s.add_argument("--json", action="store_true")
    s = sp.add_parser("leverage")
    s.add_argument("frame")
    s.add_argument("--top", type=int, default=20)
    sp.add_parser("compare")
    s = sp.add_parser("export")
    s.add_argument("--top", type=int, default=10)
    s.add_argument("--min-reach", type=int, default=2)
    a = ap.parse_args(argv)
    a.output = a.output or os.path.join(a.repo, "jobs", "polya", "output")
    if a.cmd == "frames":
        return cmd_frames(a, None)
    try:
        c = Ctx(a.repo)
    except FileNotFoundError as e:
        print("cannot read readiness tracker output:", e)
        return 2
    return {"leverage": cmd_leverage, "compare": cmd_compare, "export": cmd_export}[a.cmd](a, c)


if __name__ == "__main__":
    sys.exit(main())
