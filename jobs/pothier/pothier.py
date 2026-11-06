#!/usr/bin/env python3
"""Pothier: apply each family doctrine to its members and write per-order STATUS LEADS.

    python3 -I jobs/pothier/pothier.py members            # rebuild output/MEMBERS.jsonl (about 8 s)
    python3 -I jobs/pothier/pothier.py try DOCTRINE.json   # dry run one doctrine: branch counts and examples
    python3 -I jobs/pothier/pothier.py apply               # every doctrine -> output/LEADS.jsonl, COVERAGE.json
    python3 -I jobs/pothier/pothier.py sample --doctrine ID --n 30 --seed TEXT   # pilot draw

A doctrine (research/pothier/doctrines/<ID>.json, schema `pothier-family-doctrine/v1`) names its members,
the legal mechanisms by which they end or persist, the primary sources for each mechanism, and an ordered
decision procedure. The first branch whose conditions all hold decides the member's lead. Each branch states
the lead (`no`, `yes` or `open`), the basis kind the claim kit would need (`TERM` own terms, `ACT` a later
instrument, `CURRENT` a current-law predicate), a date rule, the sources and the evidence gaps.

What a lead is NOT: a lead is never a provisional status, never a claim, never a finding. It changes no status,
no codebook, no census row and no certified count (0). Leads are proposals for the owner to adopt, one decision
per family (Kean asks). A lead of `open` means the doctrine cannot decide the order from the fields held.

Zero tokens, standard library only, deterministic (sorted inputs, sorted outputs, no clock in the leads).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCTRINES = REPO / "research/pothier/doctrines"
SCHEMA = "pothier-family-doctrine/v1"
LEAD_SCHEMA = "pothier-status-lead/v1"
CUTOFF = "2026-10-14"
LEADS = {"no", "yes", "open"}
BASIS = {"TERM", "ACT", "CURRENT", "NONE"}
TEXT_LIMIT = 12000
NOTICE = ("Status lead from a family doctrine proposed for owner adoption. Not a provisional status, claim or "
          "finding; changes no status, codebook, census or certified count (0). The claim kit and its reviewers "
          "decide each order on its own terms.")
# Later-event mechanisms that end or replace an order, and those that show it still operating.
ENDING_MECHS = {"revocation", "supersession", "termination", "abolition", "rescission", "nullification",
                "supersession_or_revocation", "repeal", "voiding", "expiration", "ceased_to_function"}
LIVING_MECHS = {"amendment", "continuation", "extension", "modification", "supplementation", "reinstatement",
                "ratification", "suspension"}
WORD_NUMBERS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
WORD_NUMBERS.update({"twenty-five": 25, "thirty": 30, "forty": 40, "fifty": 50})


# --- loading -------------------------------------------------------------------------------------------

def load_members(path=None):
    path = Path(path or HERE / "output/MEMBERS.jsonl")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_doctrine(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    errs = validate(d)
    if errs:
        raise ValueError(f"{path}: " + "; ".join(errs))
    return d


def load_doctrines(folder=DOCTRINES):
    out = []
    for p in sorted(Path(folder).glob("*.json")):
        out.append((p, load_doctrine(p)))
    return out


_text_cache = {}


def member_text(m):
    p = m.get("primary_text_path")
    if not p:
        return ""
    if p not in _text_cache:
        try:
            with open(REPO / p, encoding="utf-8", errors="replace") as f:
                _text_cache[p] = re.sub(r"\s+", " ", f.read(TEXT_LIMIT))
        except OSError:
            _text_cache[p] = ""
    return _text_cache[p]


# --- validation ----------------------------------------------------------------------------------------

COND_KEYS = {"field", "in", "not_in", "is", "gte", "lt", "lte", "gt", "nonempty", "empty", "contains",
             "text_regex", "summary_regex", "title_regex", "any_regex", "not", "any_of", "all_of",
             "edges", "count_gte", "mechanism_in", "acting_after", "note"}


def _validate_cond(c, where, errs):
    if not isinstance(c, dict) or not c:
        errs.append(f"{where}: condition must be a non-empty object")
        return
    bad = set(c) - COND_KEYS
    if bad:
        errs.append(f"{where}: unknown condition keys {sorted(bad)}")
    for k in ("text_regex", "summary_regex", "title_regex", "any_regex"):
        if k in c:
            try:
                re.compile(c[k])
            except re.error as e:
                errs.append(f"{where}: bad regex {k}: {e}")
    if "not" in c:
        _validate_cond(c["not"], where + ".not", errs)
    for k in ("any_of", "all_of"):
        for i, sub in enumerate(c.get(k, []) or []):
            _validate_cond(sub, f"{where}.{k}[{i}]", errs)


def validate(d):
    errs = []
    if d.get("schema") != SCHEMA:
        errs.append("schema must be " + SCHEMA)
    for k in ("doctrine_id", "family", "members", "mechanisms", "sources", "procedure"):
        if k not in d:
            errs.append("missing " + k)
    if errs:
        return errs
    src_ids = {s.get("id") for s in d["sources"]}
    mech_ids = {m.get("id") for m in d["mechanisms"]}
    for m in d["mechanisms"]:
        for s in m.get("source_ids", []):
            if s not in src_ids:
                errs.append(f"mechanism {m.get('id')}: unknown source {s}")
    for s in d["sources"]:
        if s.get("member_text"):
            continue  # the member's own held text, recorded per lead (COORDINATOR_RULINGS P6)
        if s.get("held") not in (True, False):
            errs.append(f"source {s.get('id')}: held must be true or false")
        if s.get("held") and not s.get("held_path"):
            errs.append(f"source {s.get('id')}: held source needs held_path")
        if s.get("held") and s.get("held_path") and not (REPO / s["held_path"]).exists():
            errs.append(f"source {s.get('id')}: held_path does not exist: {s['held_path']}")
    _validate_cond(d["members"], "members", errs)
    seen = set()
    for i, b in enumerate(d["procedure"]):
        bid = b.get("branch_id")
        if not bid or bid in seen:
            errs.append(f"procedure[{i}]: branch_id missing or duplicate")
        seen.add(bid)
        for c in b.get("when", []):
            _validate_cond(c, f"{bid}.when", errs)
        lead = b.get("lead") or {}
        if lead.get("status_lead") not in LEADS:
            errs.append(f"{bid}: status_lead must be one of {sorted(LEADS)}")
        if lead.get("basis_kind") not in BASIS:
            errs.append(f"{bid}: basis_kind must be one of {sorted(BASIS)}")
        if lead.get("status_lead") == "no" and lead.get("basis_kind") not in {"TERM", "ACT"}:
            errs.append(f"{bid}: a 'no' lead needs basis TERM or ACT")
        if lead.get("status_lead") == "yes" and lead.get("basis_kind") != "CURRENT":
            errs.append(f"{bid}: a 'yes' lead needs basis CURRENT")
        for s in lead.get("source_ids", []):
            if s not in src_ids:
                errs.append(f"{bid}: unknown source {s}")
        for mid in lead.get("mechanism_ids", []):
            if mid not in mech_ids:
                errs.append(f"{bid}: unknown mechanism {mid}")
        if not lead.get("basis"):
            errs.append(f"{bid}: lead needs a plain-language basis")
        if not isinstance(b.get("gaps", []), list):
            errs.append(f"{bid}: gaps must be a list")
        dr = lead.get("date_rule") or {"kind": "none"}
        if dr.get("kind") not in {"none", "fixed", "order_date", "order_date_plus_years", "edge_date",
                                  "interval", "order_year_plus_years", "order_date_plus_days"}:
            errs.append(f"{bid}: unknown date_rule kind {dr.get('kind')}")
        if dr.get("kind") == "order_date_plus_years" and not (dr.get("regex") or dr.get("years")):
            errs.append(f"{bid}: order_date_plus_years needs regex or years")
    if not d["procedure"] or d["procedure"][-1].get("when"):
        errs.append("the last branch must have no conditions (the catch-all)")
    return errs


# --- conditions ----------------------------------------------------------------------------------------

def get_field(m, name):
    cur = m
    for part in name.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _cmp_date(value, bound):
    """Compare ISO date strings; a bare year compares by year only (lenient on the unknown day)."""
    if not value:
        return None
    v, b = str(value), str(bound)
    if len(v) == 4 or len(b) == 4:
        return (v[:4] > b[:4]) - (v[:4] < b[:4])
    return (v > b) - (v < b)


def matched_edges(m, c):
    edges = m.get("later_edges") or []
    mechs = set(c.get("mechanism_in") or [])
    out = []
    for e in edges:
        if mechs and e.get("mechanism") not in mechs:
            continue
        if c.get("acting_after") and not (e.get("date_candidate") or "") > c["acting_after"]:
            continue
        out.append(e)
    return out


def holds(m, c, ctx):
    if "not" in c:
        return not holds(m, c["not"], ctx)
    if "any_of" in c:
        return any(holds(m, s, ctx) for s in c["any_of"])
    if "all_of" in c:
        return all(holds(m, s, ctx) for s in c["all_of"])
    if "edges" in c or "mechanism_in" in c:
        es = matched_edges(m, c)
        if es:
            ctx.setdefault("edges", es)
        return len(es) >= int(c.get("count_gte", 1))
    for key, getter in (("text_regex", lambda: member_text(m)),
                        ("summary_regex", lambda: m.get("wpa_summary") or ""),
                        ("title_regex", lambda: m.get("title") or ""),
                        ("any_regex", lambda: " ".join([m.get("title") or "", m.get("wpa_summary") or "",
                                                        member_text(m)]))):
        if key in c:
            mt = re.search(c[key], getter(), re.I)
            if mt:
                ctx.setdefault("matches", []).append({"key": key, "pattern": c[key], "span": list(mt.span()),
                                                      "text": mt.group(0)[:200], "groups": list(mt.groups())})
            return bool(mt)
    if "field" not in c:
        return True
    v = get_field(m, c["field"])
    if "in" in c:
        return v in c["in"]
    if "not_in" in c:
        return v not in c["not_in"]
    if "is" in c:
        return v == c["is"]
    if "nonempty" in c:
        return bool(v) == bool(c["nonempty"])
    if "empty" in c:
        return (not v) == bool(c["empty"])
    if "contains" in c:
        return isinstance(v, (list, str)) and c["contains"] in v
    for op, ok in (("gte", lambda r: r >= 0), ("gt", lambda r: r > 0), ("lt", lambda r: r < 0),
                   ("lte", lambda r: r <= 0)):
        if op in c:
            r = _cmp_date(v, c[op])
            return r is not None and ok(r)
    return bool(v)


# --- dates ---------------------------------------------------------------------------------------------

def _num(token):
    token = (token or "").strip().lower().strip("()")
    if token.isdigit():
        return int(token)
    return WORD_NUMBERS.get(token)


def _add_years(date, years):
    if not date or len(date) < 4:
        return None
    y = int(date[:4]) + years
    if len(date) >= 10:
        mo, d = int(date[5:7]), int(date[8:10])
        if mo == 2 and d == 29:
            d = 28
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return f"{y:04d}"


def apply_date_rule(rule, m, ctx):
    kind = (rule or {}).get("kind", "none")
    date = m.get("date") or ""
    if kind == "none":
        return {"kind": "none"}
    if kind == "fixed":
        return {"kind": "fixed", "date": rule["date"], "basis": rule.get("basis", "")}
    if kind == "order_date":
        return {"kind": "order_date", "date": date}
    if kind == "interval":
        lo = rule.get("from") or date
        if lo == "order_date":
            lo = date
        return {"kind": "interval", "from": lo, "to": rule.get("to"), "basis": rule.get("basis", "")}
    if kind in ("order_date_plus_years", "order_year_plus_years"):
        years = rule.get("years")
        if rule.get("regex"):
            mt = re.search(rule["regex"], member_text(m) or m.get("wpa_summary") or "", re.I)
            years = _num(mt.group(1)) if mt else None
        if years is None:
            return {"kind": kind, "date": None, "unresolved": "period not parsed"}
        base = date[:4] if kind == "order_year_plus_years" else date
        return {"kind": kind, "date": _add_years(base, int(years)), "years": int(years)}
    if kind == "order_date_plus_days":
        if len(date) < 10 or not isinstance(rule.get("days"), int):
            return {"kind": kind, "date": None, "unresolved": "order date not a full date or days missing"}
        d = dt.date.fromisoformat(date[:10]) + dt.timedelta(days=rule["days"])
        return {"kind": kind, "date": d.isoformat(), "days": rule["days"]}
    if kind == "edge_date":
        es = ctx.get("edges") or []
        ds = sorted(e.get("date_candidate") for e in es if e.get("date_candidate"))
        return {"kind": "edge_date", "date": ds[0] if ds else None,
                "edge_ids": [e.get("edge_id") for e in es]}
    return {"kind": kind}


# --- contradictions with held evidence ------------------------------------------------------------------

def contradictions(m, lead, date):
    """Held evidence that disagrees with the lead. A contradiction never changes the lead; it flags it."""
    out = []
    edges = m.get("later_edges") or []
    end = (date or {}).get("date") or (date or {}).get("to")
    ending = [e for e in edges if e.get("mechanism") in ENDING_MECHS]
    living = [e for e in edges if e.get("mechanism") in LIVING_MECHS]
    if lead["status_lead"] == "yes" and ending:
        out.append({"kind": "yes_lead_but_held_ending_edge", "edge_ids": [e["edge_id"] for e in ending]})
    if lead["status_lead"] in {"yes", "open"} and lead.get("lead_kind", "").startswith("persists") and ending:
        out.append({"kind": "persistence_lead_but_held_ending_edge", "edge_ids": [e["edge_id"] for e in ending]})
    if lead["status_lead"] == "no" and end and len(end) >= 4:
        late = [e for e in living if (e.get("date_candidate") or "")[:len(end)] > end]
        if late:
            out.append({"kind": "acted_on_after_lead_end", "edge_ids": [e["edge_id"] for e in late]})
        nh = [h for h in (m.get("name_later_hits") or []) if (h.get("date_candidate") or "")[:len(end)] > end]
        if nh:
            out.append({"kind": "named_person_in_later_order_after_lead_end",
                        "edge_ids": [h["edge_id"] for h in nh]})
    cl = m.get("current_law") or {}
    if lead["status_lead"] == "no" and (cl.get("usc_predicate_leads") not in (None, "", "0")
                                         or cl.get("ecfr_predicate_leads") not in (None, "", "0")):
        out.append({"kind": "no_lead_but_current_law_predicate_lead",
                    "usc": cl.get("usc_predicate_citations", ""), "cfr": cl.get("cfr_predicate_citations", "")})
    if lead["status_lead"] == "yes" and cl.get("ending_statements_found") not in (None, "", "0"):
        out.append({"kind": "yes_lead_but_current_law_ending_statement"})
    return out


# --- application ---------------------------------------------------------------------------------------

def doctrine_sha(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def decide(m, d):
    """Return the lead record for member m under doctrine d, or None when m is not a member."""
    if not holds(m, d["members"], {}):
        return None
    srcs = {s["id"]: s for s in d["sources"]}
    for b in d["procedure"]:
        ctx = {}
        if all(holds(m, c, ctx) for c in b.get("when", [])):
            lead = dict(b["lead"])
            date = apply_date_rule(lead.get("date_rule"), m, ctx)
            gaps = list(b.get("gaps", []))
            if date.get("unresolved"):
                gaps.append("date rule unresolved: " + date["unresolved"])
            if lead["status_lead"] != "open":
                for sid in lead.get("source_ids", []):
                    if not srcs[sid].get("held") and not srcs[sid].get("member_text"):
                        gaps.append(f"source {sid} ({srcs[sid].get('citation', '')}) is not yet held")
            if not m.get("primary_text_path"):
                gaps.append("no held text of the order")
            elif m.get("primary_text_grade") in {"compiled_transcription_lead", "archival_replica_scan_pending_codebook",
                                                 "mirror_transcription", "transcription"}:
                gaps.append(f"order text is {m.get('primary_text_grade')}, not an authenticated original")
            rec = {
                "schema": LEAD_SCHEMA,
                "instrument_id": m["instrument_id"],
                "doctrine_id": d["doctrine_id"],
                "doctrine_sha256": doctrine_sha(d),
                "branch_id": b["branch_id"],
                "status_lead": lead["status_lead"],
                "lead_kind": lead.get("lead_kind", ""),
                "basis_kind": lead["basis_kind"],
                "basis": lead["basis"],
                "date": date,
                "mechanism_ids": lead.get("mechanism_ids", []),
                "sources": [{"id": s, "citation": srcs[s].get("citation", ""), "held": srcs[s].get("held"),
                             "held_path": srcs[s].get("held_path", ""), "url": srcs[s].get("url", "")}
                            for s in lead.get("source_ids", [])],
                "order_text": {"path": m.get("primary_text_path", ""), "sha256": m.get("primary_text_sha256", ""),
                               "grade": m.get("primary_text_grade", "")},
                "matches": ctx.get("matches", []),
                "edges_used": [e.get("edge_id") for e in ctx.get("edges", [])],
                "gaps": gaps,
                "history_basis": "explicit empty history under owner ruling 2026-11-05 (D-20261105-empty-history)",
                "decides": lead["status_lead"] != "open",
                "notice": NOTICE,
            }
            rec["contradictions"] = contradictions(m, rec, date)
            return rec
    raise AssertionError("catch-all branch missing")


def run(members, doctrines):
    leads, owner = [], {}
    for path, d in doctrines:
        for m in members:
            rec = decide(m, d)
            if rec is None:
                continue
            if m["instrument_id"] in owner:
                rec["also_member_of"] = owner[m["instrument_id"]]
                rec["overlap"] = True
            owner.setdefault(m["instrument_id"], d["doctrine_id"])
            leads.append(rec)
    leads.sort(key=lambda r: (r["instrument_id"], r["doctrine_id"]))
    return leads


def coverage(members, leads, doctrines):
    by_doc = collections.defaultdict(list)
    for r in leads:
        by_doc[r["doctrine_id"]].append(r)
    hint = {m["instrument_id"]: m.get("wpa_family_hint") or "(none)" for m in members}
    covered = {r["instrument_id"] for r in leads}
    out = {"members": len(members), "covered_by_a_doctrine": len(covered),
           "no_doctrine": len(members) - len(covered), "cutoff": CUTOFF, "doctrines": {}, "by_wpa_family_hint": {}}
    for _, d in doctrines:
        rs = by_doc.get(d["doctrine_id"], [])
        out["doctrines"][d["doctrine_id"]] = {
            "family": d["family"],
            "members": len(rs),
            "decides": sum(r["decides"] for r in rs),
            "cannot_decide": sum(not r["decides"] for r in rs),
            "leads": dict(collections.Counter(r["status_lead"] for r in rs)),
            "contradicts_held_evidence": sum(bool(r["contradictions"]) for r in rs),
            "decided_and_contradicted": sum(bool(r["contradictions"]) and r["decides"] for r in rs),
            "branches": dict(sorted(collections.Counter(r["branch_id"] for r in rs).items())),
            "overlaps": sum(bool(r.get("overlap")) for r in rs),
        }
    fam = collections.defaultdict(lambda: collections.Counter())
    first = {}
    for r in leads:
        first.setdefault(r["instrument_id"], r)
    for m in members:
        h = hint[m["instrument_id"]]
        r = first.get(m["instrument_id"])
        fam[h]["members"] += 1
        fam[h]["no_doctrine" if r is None else ("decides" if r["decides"] else "cannot_decide")] += 1
    out["by_wpa_family_hint"] = {k: dict(v) for k, v in sorted(fam.items(), key=lambda kv: -kv[1]["members"])}
    out["decides_total"] = sum(r["decides"] for r in first.values())
    return out


def write_outputs(out_dir, leads, cov, doctrines):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "LEADS.jsonl", "w", encoding="utf-8") as f:
        for r in leads:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    with open(out_dir / "COVERAGE.json", "w", encoding="utf-8") as f:
        json.dump(cov, f, indent=1, sort_keys=True)
    pins = {d["doctrine_id"]: {"path": str(p.relative_to(REPO)), "sha256": doctrine_sha(d)} for p, d in doctrines}
    with open(out_dir / "DOCTRINE_PINS.json", "w", encoding="utf-8") as f:
        json.dump(pins, f, indent=1, sort_keys=True)


# --- commands ------------------------------------------------------------------------------------------

def cmd_try(args):
    d = load_doctrine(args.doctrine)
    members = load_members(args.members)
    leads = [r for r in (decide(m, d) for m in members) if r]
    c = collections.Counter(r["branch_id"] for r in leads)
    print(f"{d['doctrine_id']}: {len(leads)} members; decides {sum(r['decides'] for r in leads)}; "
          f"contradicted {sum(bool(r['contradictions']) for r in leads)}")
    ex = collections.defaultdict(list)
    for r in leads:
        if len(ex[r["branch_id"]]) < args.examples:
            ex[r["branch_id"]].append(r["instrument_id"])
    for b in d["procedure"]:
        bid = b["branch_id"]
        print(f"  {bid:>10} {c.get(bid, 0):5d}  {b['lead']['status_lead']:4} {', '.join(ex.get(bid, []))}")
    hints = collections.Counter(next((m.get("wpa_family_hint") for m in members if m["instrument_id"] == r["instrument_id"]), "")
                                for r in leads) if args.hints else None
    if hints:
        print("  by WPA hint:", dict(hints.most_common()))


def cmd_apply(args):
    members = load_members(args.members)
    doctrines = load_doctrines(args.doctrines)
    leads = run(members, doctrines)
    cov = coverage(members, leads, doctrines)
    out = Path(args.out or os.environ.get("OUTPUT_DIR") or HERE / "output")
    write_outputs(out, leads, cov, doctrines)
    print(json.dumps({k: v for k, v in cov.items() if k not in ("doctrines", "by_wpa_family_hint")}))
    for k, v in cov["doctrines"].items():
        print(f"  {k}: members {v['members']} decides {v['decides']} cannot {v['cannot_decide']} "
              f"contradicted {v['contradicts_held_evidence']}")


def cmd_sample(args):
    leads = []
    with open(Path(args.leads or HERE / "output/LEADS.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["doctrine_id"] == args.doctrine:
                leads.append(r)
    ids = sorted({r["instrument_id"] for r in leads})
    rng = random.Random(f"{args.doctrine}:{args.seed}")
    pick = sorted(rng.sample(ids, min(args.n, len(ids))))
    print("\n".join(pick))


def cmd_members(args):
    sys.path.insert(0, str(HERE))
    import members  # noqa: E402
    members.main()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("members"); s.set_defaults(fn=cmd_members)
    s = sub.add_parser("try"); s.add_argument("doctrine"); s.add_argument("--members")
    s.add_argument("--examples", type=int, default=6); s.add_argument("--hints", action="store_true")
    s.set_defaults(fn=cmd_try)
    s = sub.add_parser("apply"); s.add_argument("--members"); s.add_argument("--doctrines", default=str(DOCTRINES))
    s.add_argument("--out"); s.set_defaults(fn=cmd_apply)
    s = sub.add_parser("sample"); s.add_argument("--doctrine", required=True); s.add_argument("--n", type=int, default=30)
    s.add_argument("--seed", required=True); s.add_argument("--leads"); s.set_defaults(fn=cmd_sample)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
