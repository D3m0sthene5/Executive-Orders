#!/usr/bin/env python3
"""Mountweazel: measure whether a reviewer catches defects that are really there.

Named after the fictitious entry encyclopedias plant to detect copying.  It builds a blinded
practice batch that mixes real, already-upheld items with seeded items carrying one known,
documented defect, keeps a sealed answer key, and scores a reviewer's verdicts against the key.

    python3 -I jobs/mountweazel/mountweazel.py pool
    python3 -I jobs/mountweazel/mountweazel.py seed  --track C --batch-id MW-C1 --seed s1 --n 24
    python3 -I jobs/mountweazel/mountweazel.py score --key <KEY.sealed.json> --verdicts <file>
    python3 -I jobs/mountweazel/mountweazel.py check

Hard rule: a seeded item never exists anywhere a job or ledger reads.  Rendered batches and the
sealed key are written only OUTSIDE the repository (the session scratchpad); flagged fixtures
live only in jobs/mountweazel/fixtures/ with SEEDED=true.  `check` proves the rule.

Standard library only.  Never edits claims, statuses, the codebook, ledgers or reviews.
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("MOUNTWEAZEL_REPO") or HERE.parent.parent).resolve()
SCRATCH = Path(os.environ.get(
    "MOUNTWEAZEL_OUT",
    "/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/mountweazel"))
LEGAL_CUTOFF = "2026-10-14"

SEEDED_MARKERS = (b"SEEDED:", b"mountweazel-seeded", b"SEEDED-eo-", b'"SEEDED": true', b'"SEEDED":true')
# Documents that describe the marker strings may mention them; they are still checked for planted text.
ALLOWED_DOCS = frozenset({"research/plans/MOUNTWEAZEL_DESIGN.md", "jobs/mountweazel/README.md",
                          "jobs/mountweazel/paired.py", "jobs/mountweazel/test_paired.py",
                          "jobs/mountweazel/mountweazel.py", "jobs/mountweazel/test_mountweazel.py"})
ALLOWED_DOC_PREFIXES = ("HANDOFF/",)  # notes may name batch ids and markers; planted text is still checked there
PLANT_ID_RE = re.compile(rb"\bMW-[A-Z]\d+-\d{2}\b")
VERDICTS = ("accept", "reject", "block_justified", "block_not_justified")
FLAG_VERDICTS = ("reject", "block_not_justified")
SCHEMA_BATCH = "review-practice-batch/v1"  # deliberately free of the tool name: reviewers see this file
SCHEMA_KEY = "mountweazel-key/v1"
SCHEMA_FIXTURE = "mountweazel-seeded-item/v1"

TAXONOMY = {
    "D1": "deadline or bound treated as the actual end",
    "D2": "one-time command dated to a later revocation",
    "D3": "quote does not support the claim",
    "D4": "partial-scope end treated as a total end",
    "D5": "missed earlier end (later revocation cited as the end)",
    "D6": "known later event left out",
    "D7": "wrong effective date",
    "D8": "wrong identity (neighbouring order's text)",
    "D9": "search coverage overstated",
    "D10": "wrong target (cited actor does not end this order)",
    "D11": "inferred supersession presented as express",
    "D12": "savings clause ignored",
    "D13": "unjustified block (packet holds the record the block says is missing)",
}
TRACK_CODES = {"C": ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"), "S": ("D10", "D13")}


# ----------------------------------------------------------------------------- helpers
def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def h(*parts):
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def exact_date(v):
    if not isinstance(v, str):
        return False
    try:
        return date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def inside(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def fail(msg):
    sys.exit("mountweazel: " + msg)


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
MONTH_RE = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})")


def date_variants(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    name = MONTHS[m - 1]
    forms = [iso, f"{name} {d}, {y}", f"{name[:3]}. {d}, {y}", f"{name[:3]} {d}, {y}"]
    if name in ("March", "April", "May", "June", "July"):
        forms.append(f"{name} {d}, {y}")
    return sorted(set(forms), key=len, reverse=True)


def find_dates(text):
    out = []
    for mo in MONTH_RE.finditer(text or ""):
        key = mo.group(1)[:3]
        idx = [n[:3] for n in MONTHS].index(key)
        try:
            out.append(date(int(mo.group(3)), idx + 1, int(mo.group(2))).isoformat())
        except ValueError:
            pass
    return out


def actor_variants(actor):
    m = re.match(r"EO:(\d+)$", actor or "")
    return [f"EO {m.group(1)}", f"EO:{m.group(1)}", f"Executive Order {m.group(1)}", f"No. {m.group(1)}"] if m else [actor]


def swap_text(text, olds, news):
    """Replace every old variant by the aligned new variant (first match wins per position)."""
    if not isinstance(text, str):
        return text
    for o, n in zip(olds, news):
        text = text.replace(o, n)
    return text


# ----------------------------------------------------------------------------- Wilson / exact
def wilson(k, n, z=1.959964):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def _cdf_le(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))


def clopper_pearson(k, n, alpha=0.05):
    if n == 0:
        return [None, None]

    def solve(f):  # f is increasing in p; find p with f(p) = alpha/2
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) < alpha / 2 else (lo, mid)
        return (lo + hi) / 2

    # lower: P(X >= k | p) rises with p.  upper: P(X <= k | p) falls with p, so use 1 - cdf.
    lower = 0.0 if k == 0 else solve(lambda p: 1 - _cdf_le(k - 1, n, p))
    upper = 1.0
    if k != n:
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if _cdf_le(k, n, mid) > alpha / 2 else (lo, mid)
        upper = (lo + hi) / 2
    return [round(lower, 4), round(upper, 4)]


def rate(k, n):
    return {"k": k, "n": n, "rate": None if n == 0 else round(k / n, 4), "wilson95": wilson(k, n),
            "clopper_pearson95": clopper_pearson(k, n), "indicative_only": n < 5}


# ----------------------------------------------------------------------------- claim gate
def load_gate():
    code = REPO / "research" / "stage19" / "code"
    if not (code / "claim_gate.py").exists():
        return None
    sys.path.insert(0, str(code))
    try:
        import claim_gate  # noqa: E402
        return claim_gate
    finally:
        sys.path.pop(0)


def seeded_gate_errors(payload):
    """What the production claim gate says about a flagged payload (must include both flag errors)."""
    gate = load_gate()
    if gate is not None:
        return gate.validate_claim(payload)
    errs = []
    if payload.get("schema") != "eo-lifecycle-claim/v1":
        errs.append("schema")
    if not isinstance(payload.get("instrument_id"), str) or not payload["instrument_id"].startswith("EO:"):
        errs.append("instrument_id")
    return errs


# ----------------------------------------------------------------------------- pools
def read_jsonl(path):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def load_claim_pool(repo, gate=True):
    """Real gate-passing lifecycle claims; the latest file in name order wins per order."""
    g = load_gate() if gate else None
    if gate and g is None:
        fail("research/stage19/code/claim_gate.py not found; cannot prove seeded claims pass the mechanical gates")
    pool = {}
    base = Path(repo) / "research" / "readiness" / "claims"
    for f in sorted(base.glob("*.jsonl")):
        for n, claim in enumerate(read_jsonl(f), 1):
            if g is not None and g.validate_claim(claim):
                continue
            pool[claim["instrument_id"]] = {"claim": claim, "path": str(f.relative_to(repo)), "line": n}
    return pool


def load_status_pool(repo):
    """Bowditch Y1 items: accepted NO proposals and justified blocks, as reviewer-facing packets."""
    root = Path(repo) / "research" / "excavator" / "bowditch-2026-10-20"
    pool = {}
    for run in sorted(root.glob("y1_0*")):
        outcomes = {}
        if (run / "OUTCOMES.csv").exists():
            with open(run / "OUTCOMES.csv", newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    outcomes[row["instrument_id"]] = row
        verdict = {}
        if (run / "REVIEW_LOG.csv").exists():
            with open(run / "REVIEW_LOG.csv", newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    verdict[row["instrument_id"]] = row.get("review_decision")
        for iid, row in outcomes.items():
            folder = run / "overlay" / iid.replace(":", "_")
            if row["producer_outcome"] == "proposed" and verdict.get(iid) == "accept":
                dec, evid = folder / "proposal-v1" / "STATUS_DECISION.json", folder / "proposal-v1" / "EVIDENCE.json"
            elif row["producer_outcome"] == "blocked" and verdict.get(iid) == "block_justified":
                dec, evid = folder / "STATUS_DECISION.json", folder / "freeze-v1" / "EVIDENCE.json"
            else:
                continue
            if not (dec.exists() and evid.exists()):
                continue
            d, e = json.loads(dec.read_text(encoding="utf-8")), json.loads(evid.read_text(encoding="utf-8"))
            hp = e.get("history_packet", {})
            events = [{k: ev.get(k) for k in ("id", "actor_id", "target_id", "candidate_date", "mechanism", "quote", "scope")}
                      for ev in hp.get("events", [])]
            decision = {"instrument_id": iid, "producer_outcome": row["producer_outcome"],
                        "recommended_status": d.get("recommended_provisional_status"),
                        "basis_evidence_ids": d.get("basis_evidence_ids", [])}
            if row["producer_outcome"] == "proposed":
                decision["rationale"] = d.get("rationale")
            else:
                decision["blocker"] = row.get("blocker")
                decision["fetch_queue_lines"] = row.get("fetch_queue_lines")
            pool[iid] = {"packet": {"decision": decision, "evidence": {"events": events}},
                         "path": str(dec.relative_to(repo)), "line": 0}
    return pool


# ----------------------------------------------------------------------------- Track C operators
RECURRING_RE = re.compile(r"(?i)\b(annual(ly)?|each (year|fiscal year|month|quarter)|every (year|month)|periodic(ally)?|"
                          r"from time to time|biennial(ly)?|quarterly|monthly|semi-?annual(ly)?|continuing|thereafter)\b")
ONE_TIME_RE = re.compile(r"(?is)\b(shall|is hereby directed to|is directed to|are directed to)\b.{0,120}?\b(report|submit|transmit|"
                         r"study|recommend|prepare|survey|review)\b|\bwithin\s+\w+\s+(days|months)\b")
EARLIER_END_RE = re.compile(r"(?i)\b(term\b|expir|terminat|amend|supersed|partial)")
VERB_RE = re.compile(r"(?i)\b(revok|supersed|terminat|rescind|repeal|delet|abolish|expire)")
COUNT_RE = re.compile(r"(\d+)\s+(title files|titles|volumes|issues)\b")
END_STATES = ("terminated", "never_activated")


def _ended(claim):
    return [i for i, c in enumerate(claim["operative_clauses"])
            if c.get("state_at_cutoff") in END_STATES and isinstance(c.get("first_end"), dict)
            and exact_date(c["first_end"].get("date"))]


def _resync_whole(claim):
    if claim.get("whole_order_status") != "no" or not isinstance(claim.get("whole_order_end"), dict):
        return
    idx = _ended(claim)
    if not idx:
        return
    j = max(idx, key=lambda i: claim["operative_clauses"][i]["first_end"]["date"])
    fe = claim["operative_clauses"][j]["first_end"]
    if claim["whole_order_end"].get("date") != fe["date"]:
        for k in ("date", "actor", "mechanism", "source"):
            claim["whole_order_end"][k] = copy.deepcopy(fe[k])


def _retitle(claim, old_date, new_date, old_actor=None, new_actor=None):
    olds = date_variants(old_date)
    news = date_variants(new_date)
    mapping = list(zip(date_variants(old_date), date_variants(new_date)))
    r = claim.get("research_rationale", "")
    for o, n in mapping:
        r = r.replace(o, n)
    own = claim.get("instrument_id")
    if old_actor and new_actor and old_actor != new_actor and own not in (old_actor, new_actor):
        r = swap_text(r, actor_variants(old_actor), actor_variants(new_actor))
    claim["research_rationale"] = r
    return olds, news


def _swap_safe(claim, i, old_date, old_actor=None, new_actor=None):
    """True when rewriting old_date/old_actor in the rationale cannot touch another clause's history.

    The first trial (MW-C1) showed the tell: a global swap rewrote sentences about sibling clauses
    ("EO 12050 substituted new texts for secs. 101(a), 103 and 201") so the packet contradicted itself.
    A plant whose old date or actor is shared with any other clause, any later event, or the order itself
    is skipped instead of rewritten."""
    own = claim.get("instrument_id")
    if old_actor and new_actor and old_actor != new_actor and own in (old_actor, new_actor):
        return False
    for j, cl in enumerate(claim["operative_clauses"]):
        fe = cl.get("first_end") or {}
        if j != i and (fe.get("date") == old_date or (old_actor and fe.get("actor") == old_actor)):
            return False
        for ev in cl.get("later_events", []):
            if ev.get("effective_date") == old_date or (old_actor and ev.get("actor") == old_actor):
                return False
    return True


def _move_end(claim, i, event):
    cl = claim["operative_clauses"][i]
    old = copy.deepcopy(cl["first_end"])
    fe = {"date": event["effective_date"], "actor": event["actor"], "mechanism": event["mechanism"],
          "source": copy.deepcopy(event["source"])}
    cl["first_end"] = fe
    _retitle(claim, old["date"], fe["date"], old.get("actor"), fe["actor"])
    return old


def _quote_of(end):
    return ((end or {}).get("source") or {}).get("quote") or (end or {}).get("mechanism")


def _pick(items, seed, tag):
    return sorted(items, key=lambda x: h(seed, tag, x[0] if isinstance(x, tuple) else x))


def ops_c(code, claim, pool, seed):
    """Yield (spec_id, apply_fn) pairs; apply_fn(claim_copy) -> mutation record."""
    cls = claim["operative_clauses"]
    ended = _ended(claim)
    if code == "D1":
        for i in ended:
            fe = cls[i]["first_end"]
            nlt = fe.get("not_later_than")
            if exact_date(nlt) and nlt != fe["date"] and _swap_safe(claim, i, fe["date"]):
                def apply(c, i=i, nlt=nlt):
                    f = c["operative_clauses"][i]["first_end"]
                    old = f["date"]
                    f["date"] = nlt
                    _retitle(c, old, nlt)
                    return {"field": f"operative_clauses[{i}].first_end.date", "before": old, "after": nlt,
                            "refuting_quote": _quote_of(f), "locus_terms": ["first_end", "not_later_than", old, nlt]}
                yield f"{i}", apply
    elif code in ("D2", "D5"):
        for i in ended:
            fe = cls[i]["first_end"]
            later = [e for e in cls[i].get("later_events", []) if exact_date(e.get("effective_date"))
                     and e["effective_date"] > fe["date"] and e.get("actor") != fe.get("actor")]
            if not later:
                continue
            ev = max(later, key=lambda e: e["effective_date"])
            txt = cls[i].get("original_operative_text", "")
            one_time = bool(ONE_TIME_RE.search(txt)) and not RECURRING_RE.search(txt + " " + fe.get("mechanism", ""))
            earlier = bool(EARLIER_END_RE.search(fe.get("mechanism", "")))
            if not _swap_safe(claim, i, fe["date"], fe.get("actor"), ev["actor"]):
                continue
            if (code == "D2" and one_time) or (code == "D5" and earlier and not one_time):
                def apply(c, i=i, ev=ev, code=code):
                    old = _move_end(c, i, ev)
                    return {"field": f"operative_clauses[{i}].first_end", "before": old["date"], "after": ev["effective_date"],
                            "refuting_quote": _quote_of(old) or cls[i]["original_operative_text"][:200],
                            "locus_terms": ["first_end", old["date"], ev["effective_date"], ev["actor"], old.get("actor") or ""]}
                yield f"{i}:{ev['actor']}", apply
    elif code == "D3":
        for i in ended:
            q = (cls[i]["first_end"].get("source") or {}).get("quote")
            if not isinstance(q, str):
                continue
            m = VERB_RE.search(q)
            if not m or m.start() < 40:
                continue
            cut = q[:m.start()].rstrip()
            cut = re.sub(r"\s+\S*$", "", cut) if not q[m.start() - 1].isspace() else cut
            if len(cut) < 30:
                continue

            def apply(c, i=i, q=q, cut=cut):
                f = c["operative_clauses"][i]["first_end"]
                f["source"]["quote"] = cut
                w = c.get("whole_order_end")
                if isinstance(w, dict) and (w.get("source") or {}).get("quote") == q:
                    w["source"]["quote"] = cut
                return {"field": f"operative_clauses[{i}].first_end.source.quote", "before": q, "after": cut,
                        "refuting_quote": q[len(cut):][:200], "locus_terms": ["quote", "first_end", "operative"]}
            yield f"{i}", apply
    elif code == "D4":
        if len(ended) >= 2:
            dates = {cls[i]["first_end"]["date"] for i in ended}
            if len(dates) >= 2:
                hi = max(ended, key=lambda i: cls[i]["first_end"]["date"])
                lo = min(ended, key=lambda i: cls[i]["first_end"]["date"])
                f_hi, f_lo = cls[hi]["first_end"], cls[lo]["first_end"]
                if claim.get("whole_order_status") == "no" and _swap_safe(claim, hi, f_hi["date"], f_hi.get("actor"), f_lo.get("actor")):
                    def apply(c, hi=hi, lo=lo):
                        f_old = copy.deepcopy(c["operative_clauses"][hi]["first_end"])
                        f_new = copy.deepcopy(c["operative_clauses"][lo]["first_end"])
                        c["operative_clauses"][hi]["first_end"] = f_new
                        _retitle(c, f_old["date"], f_new["date"], f_old.get("actor"), f_new.get("actor"))
                        _resync_whole(c)
                        return {"field": f"operative_clauses[{hi}].first_end", "before": f_old["date"], "after": f_new["date"],
                                "refuting_quote": _quote_of(f_old) or f_old.get("mechanism"),
                                "locus_terms": ["first_end", "whole_order_end", f_old["date"], f_new["date"], f_old.get("actor") or ""]}
                    yield f"{hi}->{lo}", apply
    elif code == "D6":
        text = canonical(claim)
        whole = claim.get("whole_order_end") or {}
        for i, cl in enumerate(cls):
            for j, ev in enumerate(cl.get("later_events", [])):
                a = ev.get("actor") or ""
                num = re.sub(r"\D", "", a)
                if not num or len(num) < 3:
                    continue
                if a in (cl.get("first_end") or {}).get("actor", "") or a == whole.get("actor"):
                    continue
                if any(a == (c2.get("first_end") or {}).get("actor") for c2 in cls):
                    continue
                if len(cl["later_events"]) < 2:
                    continue
                # refutable: the order number must still appear elsewhere in the packet
                residual = canonical({**claim, "operative_clauses": [
                    {**c2, "later_events": [e for k, e in enumerate(c2.get("later_events", [])) if not (c2 is cl and k == j)]}
                    for c2 in cls]})
                if num in residual:
                    def apply(c, i=i, j=j, ev=ev):
                        gone = c["operative_clauses"][i]["later_events"].pop(j)
                        return {"field": f"operative_clauses[{i}].later_events[{j}]", "before": gone["actor"] + " " + gone["effective_date"],
                                "after": "(entry removed)", "refuting_quote": (gone.get("source") or {}).get("quote") or gone["mechanism"],
                                "locus_terms": ["later_events", gone["actor"], re.sub(r"\D", "", gone["actor"]), gone["effective_date"]]}
                    yield f"{i}.{j}", apply
    elif code == "D7":
        for i in ended:
            fe = cls[i]["first_end"]
            blob = " ".join(str(fe.get(k, "")) for k in ("mechanism", "mechanism_detail", "effective_date_basis", "date_basis", "note"))
            others = sorted({d for d in find_dates(blob) if d != fe["date"] and d <= LEGAL_CUTOFF})
            if others and _swap_safe(claim, i, fe["date"]):
                for new in others:
                    def apply(c, i=i, new=new):
                        f = c["operative_clauses"][i]["first_end"]
                        old = f["date"]
                        f["date"] = new
                        _retitle(c, old, new)
                        _resync_whole(c)
                        return {"field": f"operative_clauses[{i}].first_end.date", "before": old, "after": new,
                                "refuting_quote": f.get("effective_date_basis") or f.get("mechanism_detail") or f.get("mechanism"),
                                "locus_terms": ["first_end", "date", old, new, "effective"]}
                    yield f"{i}:{new}", apply
    elif code == "D8":
        sha0 = claim["original_representation"]["sha256"]
        for oid, rec in pool.items():
            other = rec["claim"]
            if oid != claim["instrument_id"] and other["original_representation"]["sha256"] == sha0:
                for i in range(len(cls)):
                    txt = other["operative_clauses"][0]["original_operative_text"]
                    if txt != cls[i]["original_operative_text"]:
                        def apply(c, i=i, txt=txt, oid=oid):
                            old = c["operative_clauses"][i]["original_operative_text"]
                            c["operative_clauses"][i]["original_operative_text"] = txt
                            return {"field": f"operative_clauses[{i}].original_operative_text", "before": old[:200], "after": txt[:200],
                                    "refuting_quote": old[:200],
                                    "locus_terms": ["original_operative_text", cls[i]["scope_id"], oid, "identity"]}
                        yield f"{i}:{oid}", apply
    elif code == "D9":
        blob_parts = [(k, e) for k, e in enumerate(claim.get("later_source_search", []))]
        for k, e in blob_parts:
            for field in ("repository", "query_or_scope"):
                for mo in COUNT_RE.finditer(e.get(field, "")):
                    n, unit = mo.group(1), mo.group(2)
                    # refutable in-packet only if the same "<n> <unit>" appears somewhere else too (not "49 Stat.")
                    other = len(re.findall(r"(?<!\d)" + n + r"\s+" + re.escape(unit) + r"\b", canonical(claim)))
                    if other >= 2:
                        def apply(c, k=k, field=field, mo=mo, n=n):
                            ee = c["later_source_search"][k]
                            new = str(int(n) + max(3, int(n) // 4))
                            old_txt = ee[field]
                            ee[field] = old_txt[:mo.start(1)] + new + old_txt[mo.end(1):]
                            return {"field": f"later_source_search[{k}].{field}", "before": n, "after": new,
                                    "refuting_quote": old_txt[max(0, mo.start() - 40):mo.end() + 40],
                                    "locus_terms": ["later_source_search", field, n, new, "coverage"]}
                        yield f"{k}.{field}.{n}", apply


# ----------------------------------------------------------------------------- Track S operators
BLOCK_TEMPLATE = ("No held ACT:, TERM: or ACTOR_TEXT: record: no later instrument that revokes, supersedes or terminates "
                  "EO {num} is held. | No held CURRENT: predicate through 2026-10-14 for a YES.")


def ops_s(code, rec, pool, seed):
    pk = rec["packet"]
    dec, events = pk["decision"], pk["evidence"]["events"]
    if dec["producer_outcome"] != "proposed":
        return
    iid = dec["instrument_id"]
    if code == "D13":
        if events:
            def apply(p):
                d = p["decision"]
                old = d.get("rationale")
                num = iid.split(":")[1]
                d["producer_outcome"], d["recommended_status"], d["basis_evidence_ids"] = "blocked", None, []
                d.pop("rationale", None)
                d["blocker"], d["fetch_queue_lines"] = BLOCK_TEMPLATE.format(num=num), "1"
                return {"field": "decision.producer_outcome", "before": "proposed", "after": "blocked",
                        "refuting_quote": f"evidence.events[0].id={events[0]['id']} actor={events[0]['actor_id']}",
                        "locus_terms": ["block", "blocker", "events", "actor_text", "act:", events[0]["actor_id"] or ""]}
            yield "block", apply
    elif code == "D10":
        basis = dec.get("basis_evidence_ids", [])
        actors = [re.search(r"EO:\d+", b) for b in basis]
        actors = [m.group(0) for m in actors if m]
        if not actors:
            return
        true_actor = actors[-1]
        alts = sorted({e["actor_id"] for e in events if e["actor_id"] and e["actor_id"] != true_actor
                       and (e.get("mechanism") or "") != "revocation"})
        for alt in alts:
            def apply(p, alt=alt, true_actor=true_actor):
                d = p["decision"]
                d["basis_evidence_ids"] = [b.replace(true_actor, alt) for b in d["basis_evidence_ids"]]
                d["rationale"] = swap_text(d["rationale"], actor_variants(true_actor), actor_variants(alt))
                altq = next((e["quote"] for e in events if e["actor_id"] == alt), "")
                return {"field": "decision.basis_evidence_ids", "before": true_actor, "after": alt,
                        "refuting_quote": altq, "locus_terms": ["basis", "actor", true_actor, alt, true_actor.split(":")[1], alt.split(":")[1]]}
            yield alt, apply


# ----------------------------------------------------------------------------- pool report
def availability(track, repo):
    out = {}
    if track == "C":
        pool = load_claim_pool(repo)
        for code in TRACK_CODES["C"]:
            bases = sum(1 for oid, r in pool.items() if any(True for _ in ops_c(code, r["claim"], pool, "x")))
            out[code] = bases
        return {"real_pool": len(pool), "plantable_bases": out}
    pool = load_status_pool(repo)
    for code in TRACK_CODES["S"]:
        out[code] = sum(1 for r in pool.values() if any(True for _ in ops_s(code, r, pool, "x")))
    return {"real_pool": len(pool), "plantable_bases": out}


# ----------------------------------------------------------------------------- seed
def share_for(seed):
    return 0.20 + 0.10 * (int(h(seed, "share")[:8], 16) / 0xFFFFFFFF)


def seed_cmd(args):
    track, repo = args.track, Path(args.repo)
    out_root = Path(args.out).resolve()
    if inside(out_root, repo):
        fail(f"refusing to render a batch inside the repository: {out_root}")
    fx_root = Path(args.fixtures_dir).resolve()
    if inside(fx_root, repo) and not inside(fx_root, repo / "jobs" / "mountweazel" / "fixtures"):
        fail("fixtures may only be written under jobs/mountweazel/fixtures/ (or outside the repository)")
    batch_id = args.batch_id
    if not re.fullmatch(r"MW-[A-Z]\d+", batch_id):
        fail("batch id must look like MW-C1 or MW-S2")
    excluded = set(x for x in (args.exclude_orders or "").split(",") if x)
    pool = load_claim_pool(repo) if track == "C" else load_status_pool(repo)
    pool = {k: v for k, v in pool.items() if k not in excluded}
    share = args.share if args.share is not None else share_for(args.seed)
    n_plants = max(1, round(args.n * share))
    codes = [c for c in (args.codes.split(",") if args.codes else TRACK_CODES[track]) if c in TRACK_CODES[track]]
    if not codes:
        fail("no usable defect codes for this track")
    rot = int(h(args.seed, "rot")[:6], 16) % len(codes)
    codes = codes[rot:] + codes[:rot]

    used, plants, tried_empty = set(), [], set()
    guard = 0
    while len(plants) < n_plants and guard < 500:
        guard += 1
        live = [c for c in codes if c not in tried_empty]
        if not live:
            break
        code = live[len(plants) % len(live)]
        cands = []
        for oid in sorted(pool, key=lambda o: h(args.seed, code, o)):
            if oid in used:
                continue
            rec = pool[oid]
            gen = ops_c(code, rec["claim"], pool, args.seed) if track == "C" else ops_s(code, rec, pool, args.seed)
            specs = sorted(gen, key=lambda s: h(args.seed, code, oid, s[0]))
            if specs:
                cands.append((oid, specs[0]))
                break
        if not cands:
            tried_empty.add(code)
            continue
        oid, (spec_id, apply) = cands[0]
        rec = pool[oid]
        if track == "C":
            mutated = copy.deepcopy(rec["claim"])
            record = apply(mutated)
            errs = load_gate().validate_claim(mutated)
            if errs or mutated == rec["claim"]:
                used.add(oid)  # skip this base for this round; keeps loop finite
                continue
            payload, base_obj = mutated, rec["claim"]
        else:
            mutated = {"decision": copy.deepcopy(rec["packet"]["decision"]), "evidence": copy.deepcopy(rec["packet"]["evidence"])}
            record = apply(mutated)
            if mutated == rec["packet"]:
                used.add(oid)
                continue
            payload, base_obj = mutated, rec["packet"]
        used.add(oid)
        plants.append({"code": code, "base_order": oid, "spec": spec_id, "payload": payload, "record": record,
                       "base_path": rec["path"], "base_line": rec["line"], "base_sha256": sha(base_obj),
                       "leak_needles": [n.decode("utf-8") for n in novel_needles(base_obj, payload)]})
    if len(plants) < n_plants and not args.allow_short:
        fail(f"could only seed {len(plants)} of {n_plants} plants from this pool (use --allow-short to accept)")

    n_real = args.n - len(plants)
    reals = []
    for oid in sorted(pool, key=lambda o: h(args.seed, "real", o)):
        if oid in used:
            continue
        reals.append(oid)
        if len(reals) == n_real:
            break
    if len(reals) < n_real:
        fail(f"only {len(reals)} real items available for {n_real} slots")

    entries = [("plant", p) for p in plants] + [("real", oid) for oid in reals]
    entries.sort(key=lambda e: h(args.seed, "order", e[1]["base_order"] if e[0] == "plant" else e[1], e[0]))

    batch_dir, key_dir = out_root / batch_id / "batch", out_root / batch_id / "key"
    (batch_dir / "items").mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    item_files, key_items, fixtures = {}, [], []
    for n, (kind, e) in enumerate(entries, 1):
        item_id = f"{batch_id}-{n:02d}"
        if kind == "real":
            body = pool[e]["claim"] if track == "C" else pool[e]["packet"]
            order = e
        else:
            body, order = e["payload"], e["base_order"]
        if track == "C":
            packet = {"item_id": item_id, "track": "C", "claim": body}
        else:
            packet = {"item_id": item_id, "track": "S", **body}
        text = json.dumps(packet, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
        if "SEEDED" in text or "mountweazel" in text.lower():
            fail("internal: marker leaked into a blinded packet")
        fp = batch_dir / "items" / f"{item_id}.json"
        fp.write_text(text, encoding="utf-8")
        item_files[item_id] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        ki = {"item_id": item_id, "is_seeded": kind == "plant", "base_order": order}
        if kind == "plant":
            r = e["record"]
            ki.update({"defect_code": e["code"], "operator": f"{e['code']}.{e['spec']}", "field": r["field"],
                       "locus_terms": [t for t in r["locus_terms"] if t], "refuting_quote": r["refuting_quote"],
                       "base_sha256": e["base_sha256"]})
            seeded_payload = copy.deepcopy(e["payload"])
            if track == "C":
                seeded_payload["schema"] = "SEEDED-eo-lifecycle-claim/v1"
                seeded_payload["instrument_id"] = "SEEDED:" + seeded_payload["instrument_id"]
            else:
                seeded_payload = {"schema": "SEEDED-eo-status-packet/v1", "instrument_id": "SEEDED:" + order, **seeded_payload}
            fixtures.append((item_id, {
                "schema": SCHEMA_FIXTURE, "SEEDED": True, "instrument_id": "SEEDED:" + order, "batch_id": batch_id,
                "item_id": item_id, "defect_code": e["code"], "track": track,
                "base": {"path": e["base_path"], "line": e["base_line"], "sha256": e["base_sha256"]},
                "mutation": {"operator": ki["operator"], "field": r["field"], "before": r["before"], "after": r["after"],
                             "refuting_span": {"quote": r["refuting_quote"]}},
                "leak_needles": e["leak_needles"], "seeded_payload": seeded_payload}))
        key_items.append(ki)

    manifest = {"schema": SCHEMA_BATCH, "batch_id": batch_id, "track": track, "n_items": len(entries),
                "items": [f"{batch_id}-{n:02d}" for n in range(1, len(entries) + 1)],
                "verdict_format": {"item_id": "id", "decision": list(VERDICTS), "locus": "field path or quote span the verdict rests on",
                                   "reason": "text", "confidence": "0-1"},
                "item_sha256": item_files}
    (batch_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    batch_sha = hashlib.sha256(canonical(item_files).encode()).hexdigest()
    body = {"schema": SCHEMA_KEY, "batch_id": batch_id, "track": track, "seed": args.seed, "batch_sha256": batch_sha,
            "n_items": len(entries), "n_seeded": len(plants), "seeded_share": round(len(plants) / len(entries), 4),
            "items": key_items}
    key = {**body, "key_seal_sha256": sha(body)}
    kp = key_dir / "KEY.sealed.json"
    kp.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(kp, 0o600)
    fdir = fx_root / batch_id
    fdir.mkdir(parents=True, exist_ok=True)
    for item_id, fx in fixtures:
        (fdir / f"{item_id}.seeded.json").write_text(json.dumps(fx, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"batch_dir": str(batch_dir), "key": str(kp), "fixtures": str(fdir), "n_items": len(entries),
                      "n_seeded": len(plants), "defect_codes": sorted({p["code"] for p in plants})}, indent=1))
    return 0


# ----------------------------------------------------------------------------- score
def load_verdicts(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        rows = data if isinstance(data, list) else data.get("verdicts", [])
    except json.JSONDecodeError:
        rows = [json.loads(l) for l in text.splitlines() if l.strip()]
    return rows


GENERIC_TERMS = frozenset({"first_end", "whole_order_end", "later_events", "later_source_search", "quote", "operative",
                           "original_operative_text", "repository", "query_or_scope", "coverage", "date", "effective",
                           "identity", "block", "blocker", "events", "actor_text", "act:", "basis", "actor"})


def specific_terms(it):
    """Terms that pin the reviewer to THIS mutation, not just to a field name every packet has.

    Generic field names ("first_end", "quote") alone never earn a strict catch.  An EO:nnn actor also
    matches as its bare number; the clause path (e.g. operative_clauses[7]) counts; for D3 the first word
    cut off the quote (normally the operative verb) counts."""
    out = set()
    for t in it.get("locus_terms", []):
        t = str(t)
        if len(t) < 3 or t.lower() in GENERIC_TERMS:
            continue
        out.add(t.lower())
        m = re.fullmatch(r"EO:(\d+)", t)
        if m:
            out.add(m.group(1))
    m = re.match(r"(operative_clauses\[\d+\]|later_source_search\[\d+\])", it.get("field", ""))
    if m:
        out.add(m.group(1).lower())
    if it.get("defect_code") == "D3":
        w = re.search(r"[A-Za-z]{4,}", str(it.get("refuting_quote") or ""))
        if w:
            out.add(w.group(0).lower())
    return sorted(out)


def implied_prevalence(flags, n, catch, false_alarm_rate=0.0):
    """Upper 95% bound on the defect rate of a production batch given its flag count and the reviewer's catch rate.

    flags/n is the production review result (e.g. Bowditch Y1: 0 of 15).  With catch rate c and false-alarm
    rate f, P(flag) = pi*c + (1-pi)*f, so pi <= (CP_upper(flags, n) - f) / (c - f).  Uses the point catch rate and
    its lower 95% bound; a bound of 1.0 means the review says nothing about prevalence."""
    up = clopper_pearson(flags, n)[1]
    out = {"production_flags": flags, "production_n": n, "flag_rate_upper95": up}
    for label, c in (("at_point_catch", catch.get("rate")), ("at_catch_lower95", (catch.get("clopper_pearson95") or [None])[0])):
        if c is None or c <= false_alarm_rate:
            out["prevalence_upper95_" + label] = 1.0
        else:
            out["prevalence_upper95_" + label] = round(min(1.0, max(0.0, (up - false_alarm_rate) / (c - false_alarm_rate))), 4)
    out["note"] = ("assumes production defects resemble the planted mix and the same reviewer, prompt and packet format; "
                   "a different track (status proposals vs claims) breaks that assumption")
    return out


def score(key, rows, adjudication=None, voids=None, strict_overrides=None, weights=None, relabel=None, tells=None,
          production=None):
    if key.get("schema") != SCHEMA_KEY:
        fail("not a mountweazel key")
    body = {k: v for k, v in key.items() if k != "key_seal_sha256"}
    if sha(body) != key.get("key_seal_sha256"):
        fail("key seal does not match its contents; the key was edited")
    items = {i["item_id"]: i for i in key["items"]}
    seen = {}
    for r in rows:
        iid = r.get("item_id")
        if iid not in items:
            fail(f"verdict for unknown item {iid}")
        if iid in seen:
            fail(f"duplicate verdict for {iid}")
        if "decision" not in r and "verdict" in r:
            r = dict(r, decision=r["verdict"])
        if r.get("decision") not in VERDICTS:
            fail(f"{iid}: decision must be one of {VERDICTS}")
        seen[iid] = r
    adjudication, voids, strict_overrides = adjudication or {}, set(voids or []), strict_overrides or {}
    relabel, tells = relabel or {}, set(tells or [])
    for iid, code in relabel.items():
        if iid not in items or not items[iid]["is_seeded"] or code not in TAXONOMY:
            fail(f"relabel {iid}->{code}: not a plant or not a taxonomy code")
    noticed, tf_n, tf_l, tf_s = [], 0, 0, 0
    per = {}
    unreviewed = [i for i in items if i not in seen]
    plant_rows, real_flags, n_real = [], [], 0
    confirmed = []
    for iid, it in items.items():
        v = seen.get(iid)
        if v is None:
            continue
        flagged = v["decision"] in FLAG_VERDICTS
        if it["is_seeded"]:
            if iid in voids:
                continue
            terms = specific_terms(it)
            hay = " ".join(str(v.get(k, "")) for k in ("locus", "reason", "defect", "evidence")).lower()
            hits = [t for t in terms if t in hay]
            strict = bool(strict_overrides.get(iid, bool(hits))) and flagged
            if hits and not flagged:
                noticed.append({"item_id": iid, "defect_code": relabel.get(iid, it["defect_code"]), "matched": hits})
            if iid not in tells:
                tf_n, tf_l, tf_s = tf_n + 1, tf_l + flagged, tf_s + strict
            p = per.setdefault(relabel.get(iid, it["defect_code"]), {"n": 0, "lenient": 0, "strict": 0, "items": []})
            p["n"] += 1
            p["lenient"] += flagged
            p["strict"] += strict
            p["items"].append({"item_id": iid, "decision": v["decision"], "caught_lenient": flagged, "caught_strict": strict,
                               "key_code": it["defect_code"], "seeding_tell": iid in tells, "matched_terms": hits})
        else:
            adj = adjudication.get(iid)
            if flagged and adj == "confirmed_real_defect":
                confirmed.append(iid)
                continue
            n_real += 1
            if flagged:
                real_flags.append((iid, adj))
    types = {}
    tot_n = tot_l = tot_s = 0
    for code in sorted(per, key=lambda c: (len(c), c)):
        p = per[code]
        types[code] = {"defect": TAXONOMY.get(code, ""), "n_plants": p["n"], "strict": rate(p["strict"], p["n"]),
                       "lenient": rate(p["lenient"], p["n"]), "right_verdict_wrong_reason": p["lenient"] - p["strict"],
                       "items": p["items"]}
        tot_n += p["n"]
        tot_l += p["lenient"]
        tot_s += p["strict"]
    pooled = {"strict": rate(tot_s, tot_n), "lenient": rate(tot_l, tot_n),
              "noticed_but_accepted": noticed,
              "tell_free": {"strict": rate(tf_s, tf_n), "lenient": rate(tf_l, tf_n),
                            "excluded_items": sorted(tells & set(seen)),
                            "note": "plants whose packet carried a seeding artifact (e.g. a collateral rationale rewrite) removed"}}
    if weights:
        use = {c: weights[c] for c in types if c in weights and types[c]["strict"]["rate"] is not None}
        wsum = sum(use.values())
        if wsum:
            pooled["strict_weighted"] = round(sum(use[c] / wsum * types[c]["strict"]["rate"] for c in use), 4)
            pooled["weights_used"] = {c: round(use[c] / wsum, 4) for c in use}
            pooled["types_without_weight"] = sorted(set(types) - set(use))
    fa_low = sum(1 for _, a in real_flags if a == "false_alarm")
    fa_contest = sum(1 for _, a in real_flags if a == "contestable")
    unadj = sum(1 for _, a in real_flags if a not in ("false_alarm", "contestable"))
    false_alarm = {"n_real_reviewed": n_real, "flags_on_real": len(real_flags), "unadjudicated_flags": unadj,
                   "confirmed_real_defects_excluded": confirmed,
                   "lower_bound": rate(fa_low, n_real), "upper_bound": rate(fa_low + fa_contest + unadj, n_real),
                   "note": "a flag on a real item is not a false alarm until adjudicated; upper bound counts contestable and "
                           "unadjudicated flags as false alarms"}
    implied = None
    if production:
        fa_up = false_alarm["lower_bound"]["rate"] or 0.0
        implied = {basis: implied_prevalence(production[0], production[1], pooled[basis]["strict"] if basis == "tell_free" else pooled["strict"], fa_up)
                   for basis in ("all_plants", "tell_free")}
    return {"schema": "mountweazel-score/v2", "batch_id": key["batch_id"], "track": key["track"],
            "relabelled_by_adjudication": relabel, "implied_for_production": implied,
            "n_items": key["n_items"], "n_reviewed": len(seen), "unreviewed": unreviewed,
            "voided_plants": sorted(voids & {i for i, x in items.items() if x["is_seeded"]}),
            "by_defect_type": types, "pooled": pooled, "false_alarm": false_alarm,
            "caveat": "A result applies only to the reviewer model, prompt and packet version that produced the verdicts."}


def score_cmd(args):
    key = json.loads(Path(args.key).read_text(encoding="utf-8"))
    rows = load_verdicts(args.verdicts)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if p else None  # noqa: E731
    prod = None
    if args.production:
        k, n = (int(x) for x in args.production.split("/"))
        prod = (k, n)
    res = score(key, rows, adjudication=load(args.adjudication), voids=load(args.voids),
                strict_overrides=load(args.strict_overrides), weights=load(args.weights),
                relabel=load(args.relabel), tells=load(args.tells), production=prod)
    text = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if args.out:
        o = Path(args.out).resolve()
        ok_repo = inside(o, REPO / "jobs" / "mountweazel" / "results")
        if inside(o, REPO) and not ok_repo:
            fail("results may be written only outside the repository or under jobs/mountweazel/results/")
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


# ----------------------------------------------------------------------------- check
def iter_files(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__"))
        for f in sorted(files):
            yield Path(dirpath) / f


def scan_roots(repo, fixtures):
    """Everything in the repository except .git and the fixture folder (jobs read their own inputs from
    anywhere under jobs/<name>/, and FETCH_QUEUE, ledgers and tracker inputs live in several places)."""
    return [repo]


def _skip(path, repo, fixtures):
    if inside(path, Path(fixtures)):
        return True
    rel = path.relative_to(repo).parts if inside(path, repo) else ()
    return bool(rel) and rel[0] == ".git"


def _deflag(payload):
    """The blinded, real-format copy of a flagged payload (what a leak would look like)."""
    d = dict(payload)
    if isinstance(d.get("schema"), str) and d["schema"].startswith("SEEDED-"):
        d["schema"] = d["schema"][len("SEEDED-"):]
    if isinstance(d.get("instrument_id"), str) and d["instrument_id"].startswith("SEEDED:"):
        d["instrument_id"] = d["instrument_id"][len("SEEDED:"):]
    return d


def _strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def novel_needles(base, plant, width=28):
    """Byte strings that exist in the plant but nowhere in its real base: a window around each changed
    string, JSON-encoded with its quotes so a truncated quote ("... is hereby") does not match the real,
    longer text.  The first trial's check matched 24 real files because it used raw after-text that a
    D3 cut (a prefix of a real quote) shares with every copy of the real order."""
    old = dict(_strings(base))
    base_blob = canonical(base) + json.dumps(base, ensure_ascii=True)
    out = set()
    for path, new in _strings(plant):
        prev = old.get(path)
        if prev == new or len(new) < 12:
            continue
        for enc in (lambda x: json.dumps(x, ensure_ascii=False), lambda x: json.dumps(x, ensure_ascii=True)):
            n_enc, o_enc = enc(new), enc(prev) if isinstance(prev, str) else ""
            i = next((k for k, (a, b) in enumerate(zip(n_enc, o_enc)) if a != b), min(len(n_enc), len(o_enc)))
            j = 0
            while j < min(len(n_enc), len(o_enc)) - i and n_enc[-1 - j] == o_enc[-1 - j]:
                j += 1
            win = n_enc[max(0, i - width): len(n_enc) - j + width]
            if len(win) >= 24 and win not in base_blob:
                out.add(win.encode("utf-8"))
    return sorted(out)


def _base_object(repo, base):
    try:
        lines = (Path(repo) / base["path"]).read_text(encoding="utf-8").splitlines()
        if base.get("line"):
            return json.loads(lines[base["line"] - 1])
        return json.loads((Path(repo) / base["path"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, IndexError, KeyError, TypeError):
        return None


def scan_file(path, needles, plant_hashes, markers=True):
    hits = []
    try:
        size = path.stat().st_size
    except OSError:
        return hits
    chunk, overlap = 8 << 20, 512
    with open(path, "rb") as fh:
        tail = b""
        while True:
            buf = fh.read(chunk)
            if not buf:
                break
            data = tail + buf
            for m in SEEDED_MARKERS if markers else ():
                if m in data:
                    hits.append("marker " + m.decode())
            if markers and b"MW-" in data and PLANT_ID_RE.search(data):
                hits.append("batch item id " + PLANT_ID_RE.search(data).group(0).decode())
            for nd in needles:
                if nd in data:
                    hits.append("planted text " + nd[:40].decode("utf-8", "replace"))
            tail = data[-overlap:]
    if plant_hashes and path.suffix in (".jsonl", ".json"):
        try:
            text = path.read_text(encoding="utf-8")
            objs = [json.loads(l) for l in text.splitlines() if l.strip().startswith("{")] if path.suffix == ".jsonl" else [json.loads(text)]
            for o in objs:
                if isinstance(o, dict) and sha(o) in plant_hashes:
                    hits.append("exact copy of a planted item")
        except (ValueError, OSError):
            pass
    return sorted(set(hits))


def real_claim_blobs(repo, plant_hashes):
    """JSON text (both encodings) of each real claim under research/readiness/claims, for telling a plant's
    borrowed real wording (a D8 plant reuses a donor order's own text) from a leak.  A claim that is itself an
    exact copy of a plant, or carries a seeded marker, is not real text and is left out."""
    blobs = []
    for f in sorted((Path(repo) / "research" / "readiness" / "claims").glob("*.jsonl")):
        try:
            objs = read_jsonl(f)
        except (OSError, ValueError):
            continue
        for o in objs:
            if not isinstance(o, dict) or sha(o) in plant_hashes:
                continue
            if any(isinstance(v, str) and (v.startswith("SEEDED") or "SEEDED:" in v) for v in (o.get("schema"), o.get("instrument_id"))):
                continue
            blobs.append((json.dumps(o, ensure_ascii=False) + json.dumps(o, ensure_ascii=True)).encode("utf-8"))
    return blobs


def check(repo, fixtures_dir):
    repo, fixtures_dir = Path(repo), Path(fixtures_dir)
    problems, plant_hashes, needles = [], set(), set()
    fixture_files = sorted(fixtures_dir.rglob("*.seeded.json")) if fixtures_dir.is_dir() else []
    for fp in fixture_files:
        try:
            fx = json.loads(fp.read_text(encoding="utf-8"))
        except ValueError:
            problems.append({"where": str(fp), "problem": "fixture is not JSON"})
            continue
        if fx.get("SEEDED") is not True or not str(fx.get("instrument_id", "")).startswith("SEEDED:"):
            problems.append({"where": str(fp), "problem": "fixture lacks SEEDED=true or the SEEDED: id prefix"})
        payload = fx.get("seeded_payload")
        if not isinstance(payload, dict):
            problems.append({"where": str(fp), "problem": "fixture has no seeded_payload"})
            continue
        errs = seeded_gate_errors(payload)
        if "schema" not in errs or "instrument_id" not in errs:
            problems.append({"where": str(fp), "problem": "claim gate does not reject the flagged payload", "gate_errors": errs[:5]})
        plant_hashes.add(sha(payload))
        plant_hashes.add(sha(_deflag(payload)))
        plant_hashes.add(sha({k: v for k, v in payload.items() if k not in ("schema", "instrument_id")}))
        if isinstance(fx.get("leak_needles"), list):
            needles.update(n.encode("utf-8") for n in fx["leak_needles"])
        else:
            base = _base_object(repo, fx.get("base") or {})
            if isinstance(base, dict) and fx.get("track", "C") == "C":
                if sha(base) != (fx.get("base") or {}).get("sha256"):
                    problems.append({"where": str(fp), "problem": "base item changed since seeding; leak needles cannot be derived"})
                else:
                    needles.update(novel_needles(base, _deflag(payload)))
    if needles:
        # A plant may reuse a real donor order's wording verbatim (D8); that text legitimately exists in the
        # repository.  Such a needle cannot show a leak: the plant's marker and exact-item-copy checks still do.
        blobs = real_claim_blobs(repo, plant_hashes)
        needles = {nd for nd in needles if not any(nd in b for b in blobs)}
    scanned = 0
    for root in scan_roots(repo, fixtures_dir):
        for f in iter_files(root):
            if _skip(f, repo, fixtures_dir):
                continue
            scanned += 1
            rel = str(f.relative_to(repo)) if inside(f, repo) else str(f)
            allowed = rel in ALLOWED_DOCS or rel.startswith(ALLOWED_DOC_PREFIXES)
            hits = scan_file(f, needles, plant_hashes, markers=not allowed)
            for hit in hits:
                problems.append({"where": str(f.relative_to(repo)) if inside(f, repo) else str(f), "problem": hit})
    mw_out = repo / "jobs" / "mountweazel" / "output"
    if mw_out.is_dir():
        for f in mw_out.iterdir():
            if f.name not in ("STATUS.json", "SENSITIVITY.json"):
                problems.append({"where": str(f.relative_to(repo)), "problem": "jobs/mountweazel/output may hold only STATUS.json and SENSITIVITY.json"})
    if (repo / "jobs" / "mountweazel" / "data").exists():
        problems.append({"where": "jobs/mountweazel/data", "problem": "no data/ folder allowed (other jobs read jobs/*/data)"})
    return {"ok": not problems, "fixtures_checked": len(fixture_files), "files_scanned": scanned, "leak_needles": len(needles),
            "problems": problems[:200],
            "problem_count": len(problems)}


def check_cmd(args):
    res = check(args.repo, args.fixtures_dir)
    print(json.dumps(res, indent=1))
    if args.write_status:
        out = Path(args.repo) / "jobs" / "mountweazel" / "output"
        out.mkdir(parents=True, exist_ok=True)
        (out / "STATUS.json").write_text(json.dumps({"job": "mountweazel", "ok": res["ok"], "fixtures_checked": res["fixtures_checked"],
                                                       "files_scanned": res["files_scanned"], "problem_count": res["problem_count"]},
                                                      indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if res["ok"] else 1


def pool_cmd(args):
    print(json.dumps({t: availability(t, args.repo) for t in (args.track.split(",") if args.track else ("C", "S"))}, indent=1))
    return 0


# ----------------------------------------------------------------------------- main
def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0]=='pairs':
        spec=importlib.util.spec_from_file_location('mountweazel_pairs',HERE/'paired.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module.main(argv[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed", help="build a blinded batch and sealed key outside the repo")
    s.add_argument("--track", choices=("C", "S"), required=True)
    s.add_argument("--batch-id", required=True)
    s.add_argument("--seed", required=True)
    s.add_argument("--n", type=int, default=24)
    s.add_argument("--share", type=float, default=None, help="seeded share; default 0.20-0.30 derived from the seed")
    s.add_argument("--codes", default=None)
    s.add_argument("--exclude-orders", default="", help="comma list of EO:nnn that must not appear (for crossover batches)")
    s.add_argument("--allow-short", action="store_true")
    s.add_argument("--out", default=str(SCRATCH))
    s.add_argument("--fixtures-dir", default=str(HERE / "fixtures"))
    sc = sub.add_parser("score", help="score reviewer verdicts against the sealed key")
    sc.add_argument("--key", required=True)
    sc.add_argument("--verdicts", required=True)
    sc.add_argument("--adjudication")
    sc.add_argument("--voids")
    sc.add_argument("--strict-overrides")
    sc.add_argument("--weights")
    sc.add_argument("--relabel", help='JSON {"item": "Dn"}: adjudicated true defect type when the operator label is wrong')
    sc.add_argument("--tells", help="JSON list of plant item ids whose packet carried a seeding artifact")
    sc.add_argument("--production", help="k/n flags in a production review (e.g. 0/15) to bound its defect prevalence")
    sc.add_argument("--out")
    c = sub.add_parser("check", help="prove no seeded item exists where a job reads")
    c.add_argument("--fixtures-dir", default=str(HERE / "fixtures"))
    c.add_argument("--write-status", action="store_true")
    p = sub.add_parser("pool", help="how many real bases each defect type can be planted on")
    p.add_argument("--track", default="")
    args = ap.parse_args(argv)
    if args.cmd == "seed":
        return seed_cmd(args)
    if args.cmd == "score":
        return score_cmd(args)
    if args.cmd == "check":
        return check_cmd(args)
    return pool_cmd(args)


if __name__ == "__main__":
    sys.exit(main())
