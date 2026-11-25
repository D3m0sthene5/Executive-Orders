"""Paired-replay gauge for the stateless render mode (Maudslay conveyor).

Question: does making every model stage one request with no tools (stateless mode) keep the quality of the Papinian
agent lane at a fraction of its cost? Papinian measured about $0.64 per attempted order and $4.71 per filed claim
at 170-214k tokens of context per call; the evidence an order needs is about 16.5k tokens (producer) and 9.7k
(reviewer).

The gauge replays Papinian orders and claims through stateless workers and compares them with what the agents did.

  (a) 60 orders (30 that Papinian filed, 30 that it did not; a seeded draw from the y*, c01 and r01b packets) go through
      a stateless Sonnet producer and a stateless Haiku 5.5 producer. Each producer's outcome (submit or not), status
      and end dates are compared with the agent producer's final sheet.
  (b) 40 already-reviewed claims (from reviews/BLIND_REVIEW_{A,B}.jsonl and the applied CLAIMS.proposed.jsonl) plus the
      planted controls, regenerated exactly as research/excavator/claude-papinian-2026-11-10/tools/review_prep.py
      planted them, go through two stateless Opus arms (A then B, so B reads A's cached prefix). A control counts as
      caught only if both arms rejected its exact planted hash and named a date in their defects (the conveyor's rule).

Stop rule (computed and printed here): any missed control, or a stateless-vs-agent verdict disagreement rate above the
agent arms' own 7/85, or a measured list-price cost above $2.50 per filed claim, gives KEEP_AGENT_ROUTE; otherwise
GO_STATELESS with haiku_matches_sonnet true or false.

    python -I jobs/maudslay-conveyor/gauge_stateless.py --dry-run --scratch D:/stateless-scratch   # no model call
    python -I jobs/maudslay-conveyor/gauge_stateless.py --scratch D:/stateless-scratch   # the paid run (cap $25)

Nothing here certifies anything; the gauge writes only GAUGE_RESULTS.json and GAUGE_REPORT.md under --out.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import conveyor as C  # noqa: E402
import stateless as ST  # noqa: E402

REPO = C.REPO
PAPINIAN = "research/excavator/claude-papinian-2026-11-10"
OUT_DEFAULT = "research/stateless-calls-2026-11-24"
SEED_DEFAULT = "stateless-gauge-2026-11-24"
AGENT_ARM_DISAGREEMENT = (7, 85)     # the agent arms' own disagreement (owner's figure): 7 of 85 claims
COST_PER_FILED_LIMIT = 2.50
CAP_DEFAULT = 25.0
N_PRODUCER = 30                       # per stratum (filed, not filed)
N_REVIEWED = 40
BATCH_RE = re.compile(r"^(y\d+|c01|r01b)$")
ROUTES = {"y": "route_yes.txt", "c": "route_correction.txt", "r": "route_recovery.txt"}
MODELS = {"sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5", "opus": "claude-opus-5-5"}
OUT_TOKENS = {"producer": 4000, "reviewer": 2500}   # forecast assumptions (output tokens per request)


def read_jsonl(path):
    return C.read_jsonl(path)


def canon(obj):
    return C.canon(obj)


# ---------------------------------------------------------------------------------------------------------------
# Papinian data


def papinian_batches(repo):
    root = Path(repo) / PAPINIAN
    out = []
    for d in sorted(root.iterdir()):
        packet = d / "packet"
        if (BATCH_RE.match(d.name) and (packet / "completion/COMPLETION.json").exists()
                and (packet / "APPLIED_FOR_REVIEW").exists()):
            out.append(d.name)
    return sorted(out, key=lambda b: (b[0] != "y", b))


def route_file(repo, batch):
    return Path(repo) / PAPINIAN / "tools/prompts" / ROUTES[batch[0]]


def load_batch(repo, b):
    """Everything the replay needs from one Papinian batch (read only)."""
    P = Path(repo) / PAPINIAN / b / "packet"
    applied = (P / "APPLIED_FOR_REVIEW").read_text(encoding="utf-8").strip()
    _, drows = C.read_csv(P / "decisions.csv")
    _, crows = C.read_csv(P / "clauses.csv")
    comp = json.loads((P / "completion/COMPLETION.json").read_text(encoding="utf-8"))
    claims = read_jsonl(P / applied / "CLAIMS.proposed.jsonl")
    assess = {r["id"]: r for r in read_jsonl(P / "ASSESSMENT.jsonl") if isinstance(r, dict) and r.get("id")}
    rev = {a: {r["claim_sha256"]: r for r in read_jsonl(P / f"reviews/BLIND_REVIEW_{a}.jsonl")} for a in "AB"}
    return {"batch": b, "packet": P, "applied": applied,
            "decisions": {r["instrument_id"]: r for r in drows},
            "clauses": {i: [c for c in crows if c["instrument_id"] == i] for i in {r["instrument_id"] for r in drows}},
            "filed": {m["instrument_id"] for m in comp["members"] if m["outcome"] == "submit"},
            "members": [m["instrument_id"] for m in comp["members"]],
            "controls": comp.get("controls") or [], "claims": claims, "assessment": assess, "reviews": rev}


def draw(rng_seed, tag, items, n):
    """Seeded sample of n items (all of them if fewer), independent of the input order."""
    rng = random.Random(hashlib.sha256(f"{rng_seed}:{tag}".encode()).hexdigest())
    pool = sorted(items, key=lambda x: json.dumps(x, sort_keys=True))
    return sorted(rng.sample(pool, min(n, len(pool))), key=lambda x: json.dumps(x, sort_keys=True))


def producer_draw(batches, seed):
    """30 orders Papinian filed and 30 it did not: [{batch, iid, filed}]."""
    filed, unfiled = [], []
    for bd in batches:
        for iid in bd["members"]:
            (filed if iid in bd["filed"] else unfiled).append({"batch": bd["batch"], "iid": iid, "filed": iid in bd["filed"]})
    return draw(seed, "producers-filed", filed, N_PRODUCER) + draw(seed, "producers-unfiled", unfiled, N_PRODUCER)


# ---------------------------------------------------------------------------------------------------------------
# Controls: regenerated exactly as review_prep.py planted them


def has_end(c):
    return C._has_end(c)


def regenerate_controls(batch, claims):
    """review_prep.py's plant step: max(1, round(n/15)) claims among those with an end date (else a later-event date,
    else any), picked with random.Random(sha256('papinian-controls:' + batch)); every end date (event date, signing date)
    moved back three years. Returns (review set in claim order, genuine claims, controls [{instrument_id, planted,
    genuine, defect, type}], mode)."""
    elig, mode = [c for c in claims if C._has_end(c)], "end"
    if not elig:
        elig, mode = [c for c in claims if C._has_event(c)], "event"
    if not elig:
        elig, mode = list(claims), "signing"
    n = max(1, round(len(claims) / 15)) if claims else 0
    rng = random.Random(hashlib.sha256(("papinian-controls:" + batch).encode()).hexdigest())
    picks = {c["instrument_id"] for c in rng.sample(sorted(elig, key=lambda c: c["instrument_id"]), min(n, len(elig)))}
    out, genuine, controls = [], [], []
    for c in claims:
        if c["instrument_id"] in picks:
            p, k = C.plant_one(c, mode)
            if not k:
                raise ValueError(f"cannot plant on {c['instrument_id']}")
            out.append(p)
            genuine.append(c)
            controls.append({"instrument_id": c["instrument_id"], "planted": canon(p), "genuine": canon(c),
                             "defect": C.DEFECT[mode], "type": "date_shift_" + mode})
        else:
            out.append(c)
    return out, genuine, controls, mode


def reviewed_draw(batches, seed):
    """40 already-reviewed genuine claims (both arms' reviews exist for the exact claim bytes): 20 the agent arms filed
    (both upheld) and 20 they did not, a seeded draw that leaves out the claims regenerated as controls. Returns
    [{batch, iid, claim_sha256, agent_A, agent_B}]."""
    filed, other = [], []
    for bd in batches:
        _, _, controls, _ = regenerate_controls(bd["batch"], bd["claims"])
        ctl = {k["instrument_id"] for k in controls}
        for c in bd["claims"]:
            sha = canon(c)
            a, b = bd["reviews"]["A"].get(sha), bd["reviews"]["B"].get(sha)
            if c["instrument_id"] in ctl or not a or not b:
                continue
            row = {"batch": bd["batch"], "iid": c["instrument_id"], "claim_sha256": sha,
                   "agent_A": a["verdict"], "agent_B": b["verdict"]}
            (filed if a["verdict"] == "upheld" and b["verdict"] == "upheld" else other).append(row)
    half = N_REVIEWED // 2
    got_f, got_o = draw(seed, "reviewed-filed", filed, half), draw(seed, "reviewed-other", other, half)
    # a short stratum is filled from the other one so the total stays N_REVIEWED when the data allow
    if len(got_f) < half:
        got_o = draw(seed, "reviewed-other", other, N_REVIEWED - len(got_f))
    elif len(got_o) < half:
        got_f = draw(seed, "reviewed-filed", filed, N_REVIEWED - len(got_o))
    return got_f + got_o


def pair_decision(va, vb, need="upheld"):
    """The both-uphold rule: file only if both arms upheld, block only if both rejected, else split."""
    if va == need and vb == need:
        return "file"
    if va == "rejected" and vb == "rejected":
        return "block"
    return "split"


# ---------------------------------------------------------------------------------------------------------------
# Prepared rows for a replay (the blank sheet the conveyor would have prepared), and comparison with the agent


DEC_FIELDS = ["instrument_id", "dossier_sha256", "agent", "outcome", "approved", "original_confirmed",
              "original_pages_confirmed", "inventory_confirmed", "research_rationale", "savings_state",
              "savings_source_id", "savings_reason", "search_ids", "conflict_resolutions", "unresolved_material_gaps",
              "earlier_end_check", "scope_check", "independent_command_check", "savings_check", "working_text",
              "source_notes", "publication_kind"]
CLAUSE_FIELDS = ["instrument_id", "scope_id", "clause_id", "state", "end_id", "effective_date", "mechanism",
                 "effective_date_confirmed", "current_basis_id", "current_legal_basis", "checked_through",
                 "later_event_ids", "later_events", "reason", "inventory_source_id", "inventory_char_start",
                 "inventory_char_end", "inventory_reason"]


def prepared_rows(view, agent_row, agent="stateless-gauge"):
    """A blank decisions row and blank clause rows for one order: what `kit prepare` writes before any producer works,
    rebuilt from the order's frozen view and the dossier hash (no agent judgment is carried over)."""
    iid = view["instrument_id"]
    row = {k: "" for k in DEC_FIELDS}
    row.update(instrument_id=iid, dossier_sha256=agent_row["dossier_sha256"], agent=agent, outcome="",
               approved="false", original_confirmed="false", original_pages_confirmed="false",
               inventory_confirmed="false", search_ids="[]", conflict_resolutions="{}",
               unresolved_material_gaps=json.dumps(view.get("missing") or [], ensure_ascii=False))
    clauses = []
    for c in (view.get("clause_inventory") or {}).get("clauses") or view.get("clauses") or []:
        r = {k: "" for k in CLAUSE_FIELDS}
        r.update(instrument_id=iid, scope_id=c.get("scope_id"), clause_id=c.get("id"), effective_date_confirmed="false",
                 later_event_ids="[]", later_events="[]")
        clauses.append(r)
    return row, clauses


def sheet_summary(row, clauses, assessment):
    """Outcome class, status and end dates of a sheet (agent's or stateless)."""
    submit = row.get("outcome") == "submit"
    dates = sorted({c["effective_date"] for c in clauses if c.get("state") == "terminated" and c.get("effective_date")}) \
        if submit else []
    a = assessment or {}
    return {"outcome": row.get("outcome"), "submit": submit, "end_dates": dates,
            "claimed_status": a.get("claimed_status"),
            "operative_force_at_cutoff": a.get("operative_force_at_cutoff")}


def compare_producer(agent, stateless):
    """Outcome (submit or not), status and end dates of a stateless sheet against the agent's final sheet."""
    both = agent["submit"] and stateless["submit"]
    status_known = agent.get("operative_force_at_cutoff") is not None and stateless.get("operative_force_at_cutoff") is not None
    return {"outcome_match": agent["submit"] == stateless["submit"],
            "status_match": (agent.get("operative_force_at_cutoff") == stateless.get("operative_force_at_cutoff")
                             and (agent.get("claimed_status") or "") == (stateless.get("claimed_status") or ""))
            if status_known else None,
            "end_dates_match": (agent["end_dates"] == stateless["end_dates"]) if both else None,
            "both_submit": both}


# ---------------------------------------------------------------------------------------------------------------
# Running one request (a stateless `claude -p` process, plus at most one need_more round)


def build_argv(template, program, model, prefix_file, schema):
    mapping = {"prefix_file": str(prefix_file), "schema": ST.schema_text(schema), "model": model}
    argv = C.render_args(template, mapping)
    if program:
        argv[0] = program
    ST.validate_stateless_command(argv)
    return argv


def run_process(argv, suffix, workdir, timeout, env=None):
    Path(workdir).mkdir(parents=True, exist_ok=True)
    e = {k: v for k, v in (env or os.environ).items() if k != "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD"}
    t0 = time.time()
    p = subprocess.run(argv, input=suffix.encode("utf-8"), capture_output=True, cwd=workdir, timeout=timeout, env=e)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace"), time.time() - t0


def run_call(call, ctx):
    """One gauge request: the call is {id, stage, model, prefix, suffix, schema, kind}. ctx: {repo, scratch, template,
    program, prices, timeout, env}. Runs the process, parses the stream, serves one need_more round if asked, prices
    every model call at list price. Returns a JSON-able result (also written to scratch/streams/)."""
    scratch = Path(ctx["scratch"])
    psha = ST.sha256_text(call["prefix"])
    pfile = scratch / "prefixes" / f"{psha[:16]}.txt"
    if not pfile.exists():
        pfile.parent.mkdir(parents=True, exist_ok=True)
        pfile.write_text(call["prefix"], encoding="utf-8", newline="\n")
    argv = build_argv(ctx["template"], ctx.get("program"), call["model"], pfile, call["schema"])
    rounds, suffix, answer, error = [], call["suffix"], None, None
    for rnd in (1, 2):
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rc, out, err, wall = run_process(argv, suffix, scratch / "cwd", ctx.get("timeout", 1800), ctx.get("env"))
        (scratch / "streams").mkdir(parents=True, exist_ok=True)
        (scratch / "streams" / f"{call['id']}.r{rnd}.jsonl").write_text(out, encoding="utf-8")
        parsed = ST.parse_stream(out)
        usd = [ST.call_usd(ctx["prices"], call["model"], c) for c in parsed["calls"]]
        rounds.append({"round": rnd, "exit": rc, "wall_seconds": round(wall, 2), "started_utc": started,
                       "calls": parsed["calls"], "usd": None if any(u is None for u in usd) else round(sum(usd), 6),
                       "answer_from": parsed["answer_from"], "stderr": err[-300:] if rc else ""})
        answer = parsed["answer"]
        if rc or not parsed["result_seen"] or parsed["is_error"] or not isinstance(answer, dict):
            error = f"round {rnd}: exit {rc}, {'no result event' if not parsed['result_seen'] else 'error' if parsed['is_error'] else 'no structured answer'}"
            answer = None
            break
        if answer.get("need_more") and rnd == 1:
            served, report = ST.serve_need_more(ctx["repo"], answer["need_more"], extra_forbidden=[scratch])
            rounds[-1]["need_more"] = report
            suffix = ST.need_more_suffix(call["suffix"], answer["need_more"], served)
            continue
        if answer.get("need_more"):
            error, answer = "need_more in the final round", None
        break
    total = {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0}
    for r in rounds:
        for c in r["calls"]:
            for k in total:
                total[k] += c[k]
    usds = [r["usd"] for r in rounds]
    return {"id": call["id"], "stage": call["stage"], "model": call["model"], "kind": call["kind"],
            "prefix_sha256": psha, "prefix_tokens_est": ST.est_tokens(call["prefix"]),
            "suffix_tokens_est": ST.est_tokens(call["suffix"]), "answer": answer, "error": error, "rounds": rounds,
            "tokens": total, "usd": None if any(u is None for u in usds) else round(sum(usds), 6)}


class Spend:
    """Dollar cap: stops launching when measured spend plus the forecast of calls in flight would pass the cap."""

    def __init__(self, cap):
        self.cap, self.spent, self.inflight, self.lock, self.stopped = float(cap), 0.0, 0.0, threading.Lock(), False

    def start(self, est):
        with self.lock:
            if self.stopped or self.spent + self.inflight + est > self.cap + 1e-9:
                self.stopped = True
                return False
            self.inflight += est
            return True

    def finish(self, est, usd):
        with self.lock:
            self.inflight -= est
            self.spent += float(usd or est)   # an unpriced call counts at its forecast


# ---------------------------------------------------------------------------------------------------------------
# Stop rule


def stop_rule(controls, disagreement, cost_per_filed, haiku_matches_sonnet, complete=True, limit=COST_PER_FILED_LIMIT,
              agent_rate=AGENT_ARM_DISAGREEMENT):
    """controls: [{caught_A, caught_B}]; disagreement: {count, n} (stateless pair verdict vs agent pair verdict on the
    reviewed genuine claims); cost_per_filed: list-price dollars (None when nothing would be filed)."""
    reasons = []
    missed = [c for c in controls if not (c.get("caught_A") and c.get("caught_B"))]
    if missed:
        reasons.append(f"{len(missed)} planted control(s) missed by at least one stateless arm")
    n = disagreement.get("n") or 0
    rate = (disagreement["count"] / n) if n else None
    if rate is not None and rate > agent_rate[0] / agent_rate[1]:
        reasons.append(f"stateless-vs-agent verdict disagreement {disagreement['count']}/{n} = {rate:.3f} exceeds the agent "
                       f"arms' own {agent_rate[0]}/{agent_rate[1]} = {agent_rate[0] / agent_rate[1]:.3f}")
    if cost_per_filed is None:
        reasons.append("no claim would be filed under the replay, so cost per filed claim is unbounded")
    elif cost_per_filed > limit:
        reasons.append(f"measured cost ${cost_per_filed:.2f} per filed claim exceeds ${limit:.2f}")
    if not complete:
        reasons.append("the run is incomplete (dollar cap reached or calls failed), so no GO can be concluded")
    return {"verdict": "KEEP_AGENT_ROUTE" if reasons else "GO_STATELESS", "reasons": reasons,
            "haiku_matches_sonnet": bool(haiku_matches_sonnet)}


# ---------------------------------------------------------------------------------------------------------------
# Rendering


def render_all(repo, scratch, seed, cruden=True, log=print):
    """Draw the orders and claims, regenerate the controls and render every prompt. Returns the plan dict."""
    batches = [load_batch(repo, b) for b in papinian_batches(repo)]
    by = {bd["batch"]: bd for bd in batches}
    pdraw = producer_draw(batches, seed)
    rdraw = reviewed_draw(batches, seed)
    controls = []   # [{batch, iid, planted claim, planted, genuine, mode}]
    for bd in batches:
        review_set, _, ctl, mode = regenerate_controls(bd["batch"], bd["claims"])
        planted = {k["planted"]: k for k in ctl}
        for c in review_set:
            if canon(c) in planted:
                controls.append(dict(planted[canon(c)], batch=bd["batch"], claim=c, mode=mode))
    ids = sorted({p["iid"] for p in pdraw} | {r["iid"] for r in rdraw} | {c["instrument_id"] for c in controls})
    cache = Path(scratch) / "cruden-hits.json"
    hits = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    missing = [i for i in ids if i not in hits]
    if missing and cruden:
        log(f"cruden number search for {len(missing)} orders (measured: about 8 minutes for 99 orders on the build machine; cached in SCRATCH/cruden-hits.json) ...")
        tmp = Path(scratch) / "_cruden_result.json"
        hits.update(ST.run_cruden_numbers(repo, missing, tmp))
        tmp.unlink(missing_ok=True)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(hits), encoding="utf-8")
    texts = ST.Texts(repo)
    prefixes = {}
    producers = []
    for p in pdraw:
        bd = by[p["batch"]]
        slug = ST.slug(p["iid"])
        view = json.loads((bd["packet"] / "views" / f"{slug}.json").read_text(encoding="utf-8"))
        arow = bd["decisions"][p["iid"]]
        prow, pclauses = prepared_rows(view, arow)
        lookups = (json.loads((bd["packet"] / "LOOKUPS.json").read_text(encoding="utf-8")).get("members") or {}).get(p["iid"])
        ev, meta = ST.producer_evidence(repo, p["iid"], view, prow, pclauses, hits.get(p["iid"]) if cruden else None, lookups, texts)
        route = route_file(repo, p["batch"])
        if route.name not in prefixes:
            prefixes[route.name] = ST.producer_prefix(repo, route.stem, route.read_text(encoding="utf-8"))
        producers.append(dict(p, view_rel=None, prepared=(prow, pclauses), suffix=ST.producer_suffix(ev),
                              prefix=prefixes[route.name], route=route.name, meta=meta,
                              agent=sheet_summary(arow, bd["clauses"].get(p["iid"], []), bd["assessment"].get(p["iid"]))))
    reviews = []
    for r in rdraw:
        bd = by[r["batch"]]
        claim = next(c for c in bd["claims"] if canon(c) == r["claim_sha256"])
        reviews.append(dict(r, claim=claim, genuine=True, planted=False))
    for c in controls:
        reviews.append({"batch": c["batch"], "iid": c["instrument_id"], "claim_sha256": c["planted"], "claim": c["claim"],
                        "genuine": False, "planted": True, "control_type": c["type"], "defect": c["defect"],
                        "agent_A": (by[c["batch"]]["reviews"]["A"].get(c["planted"]) or {}).get("verdict"),
                        "agent_B": (by[c["batch"]]["reviews"]["B"].get(c["planted"]) or {}).get("verdict")})
    for r in reviews:
        bd = by[r["batch"]]
        lookups = (json.loads((bd["packet"] / "LOOKUPS.json").read_text(encoding="utf-8")).get("members") or {}).get(r["iid"])
        ev, meta = ST.reviewer_evidence(repo, r["claim"], hits.get(r["iid"]) if cruden else None, lookups, texts)
        r["prefix"] = ST.reviewer_prefix(repo, ev)
        r["meta"] = meta
        r["suffix"] = {a: ST.reviewer_suffix(a, "blind", r["claim"]) for a in "AB"}
    return {"batches": [b["batch"] for b in batches], "producers": producers, "reviews": reviews,
            "controls_regenerated": len(controls), "controls_expected": 18, "batch_data": by}


def build_calls(plan, models):
    """Every request of the run, in launch order: Haiku producers, Sonnet producers, then reviews (controls first)."""
    calls = []
    for name in ("haiku", "sonnet"):
        for p in plan["producers"]:
            calls.append({"id": f"P-{name}-{ST.slug(p['iid'])}", "stage": f"producer-{name}", "model": models[name],
                          "prefix": p["prefix"], "suffix": p["suffix"], "schema": ST.producer_schema(), "kind": "producer",
                          "iid": p["iid"], "batch": p["batch"]})
    order = sorted(plan["reviews"], key=lambda r: (not r["planted"], r["batch"], r["iid"]))
    for r in order:
        for arm in "AB":
            calls.append({"id": f"R-{arm}-{ST.slug(r['iid'])}-{r['claim_sha256'][:8]}", "stage": f"review-{arm}",
                          "model": models["opus"], "prefix": r["prefix"], "suffix": r["suffix"][arm],
                          "schema": ST.reviewer_schema("blind"), "kind": "reviewer", "iid": r["iid"], "batch": r["batch"],
                          "claim_sha256": r["claim_sha256"], "arm": arm})
    return calls


def forecast(plan, calls, prices, out_tokens=None):
    """List-price forecast: a request's prefix is read from cache when an earlier request in the run wrote it (producers:
    after the first of each model and route; reviewers: arm B after arm A), else written at the 5-minute rate; the
    suffix is written; output tokens are the assumption per kind."""
    out_tokens = out_tokens or OUT_TOKENS
    seen, by_stage, total = set(), {}, 0.0
    rows = []
    for c in calls:
        key = (c["model"], ST.sha256_text(c["prefix"]))
        cached = key in seen
        seen.add(key)
        usd = ST.forecast_usd(prices, c["model"], ST.est_tokens(c["prefix"]), ST.est_tokens(c["suffix"]),
                              out_tokens[c["kind"]], cached)
        by_stage[c["stage"]] = by_stage.get(c["stage"], 0.0) + (usd or 0.0)
        total += usd or 0.0
        rows.append(usd)
    return {"by_stage": {k: round(v, 4) for k, v in by_stage.items()}, "total": round(total, 4), "per_call": rows,
            "assumptions": {"output_tokens": out_tokens, "need_more_rounds": 0,
                            "note": "suffix tokens are priced as cache writes (the dearer case)"}}


def token_stats(values):
    v = sorted(values)
    return {"n": len(v), "min": v[0], "median": int(statistics.median(v)), "max": v[-1]} if v else {"n": 0}


def dry_run_summary(plan, calls, fc):
    prod, rev = plan["producers"], plan["reviews"]
    ptoks = [ST.est_tokens(p["suffix"]) for p in prod]
    rtoks = [ST.est_tokens(r["prefix"]) for r in rev]
    over = [c["id"] for c in calls if ST.over_cutoff(c["prefix"], c["suffix"])]
    prefix_ids = {}
    for p in prod:
        prefix_ids.setdefault(p["route"], set()).add(ST.sha256_text(p["prefix"]))
    return {"orders_producer": len(prod), "filed": sum(1 for p in prod if p["filed"]), "reviewed_claims": len(rev),
            "genuine_reviewed": sum(1 for r in rev if r["genuine"]), "controls": sum(1 for r in rev if r["planted"]),
            "controls_expected": plan["controls_expected"], "controls_regenerated": plan["controls_regenerated"],
            "requests": len(calls), "producer_prefix_tokens": {r: ST.est_tokens(next(p["prefix"] for p in prod if p["route"] == r))
                                                            for r in prefix_ids},
            "producer_prefix_identical_per_route": all(len(v) == 1 for v in prefix_ids.values()),
            "producer_evidence_tokens": token_stats(ptoks),
            "reviewer_prefix_tokens_(rules+evidence)": token_stats(rtoks),
            "reviewer_suffix_tokens": token_stats([ST.est_tokens(r["suffix"]["A"]) for r in rev]),
            "over_150k_tokens": over, "forecast_usd": {"by_stage": fc["by_stage"], "total": fc["total"]},
            "forecast_assumptions": fc["assumptions"]}


# ---------------------------------------------------------------------------------------------------------------
# Execution and scoring


def load_state(path):
    return {r["id"]: r for r in read_jsonl(path) if isinstance(r, dict) and "id" in r}


def run_calls(calls, ctx, state_path, cap, parallel, prices, forecasts, log=print):
    """Run the requests (resuming from state_path), the first of each distinct prefix alone so its cache write finishes
    before the others read it. Stops launching at the dollar cap. Returns {id: result}."""
    done = load_state(state_path)
    spend = Spend(cap)
    spend.spent = sum(float(r.get("usd") or 0) for r in done.values())
    lock = threading.Lock()
    results = dict(done)
    skipped = []

    def go(c, est):
        if not spend.start(est):
            skipped.append(c["id"])
            return
        try:
            res = run_call(c, ctx)
        except Exception as exc:   # a crashed request is recorded, not retried (it may have spent)
            res = {"id": c["id"], "stage": c["stage"], "model": c["model"], "kind": c["kind"], "answer": None,
                   "error": f"gauge error: {type(exc).__name__}: {exc}", "usd": None, "rounds": [], "tokens": {},
                   "prefix_sha256": ST.sha256_text(c["prefix"]), "prefix_tokens_est": ST.est_tokens(c["prefix"]),
                   "suffix_tokens_est": ST.est_tokens(c["suffix"])}
        spend.finish(est, res.get("usd"))
        with lock:
            results[c["id"]] = res
            with open(state_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(res, ensure_ascii=False) + "\n")
        log(f"{res['id']}: {'ok' if res.get('answer') else res.get('error')} ${res.get('usd')} (spent ${spend.spent:.2f})")

    est = {c["id"]: forecasts[i] or 1.0 for i, c in enumerate(calls)}
    todo = [c for c in calls if c["id"] not in done]
    # producers: one model at a time; reviewers: waves of claims, arm A first and arm B straight after on the same claims
    groups = {}
    for c in todo:
        groups.setdefault(c["stage"] if c["kind"] == "producer" else "review", []).append(c)
    for name in [n for n in ("producer-haiku", "producer-sonnet", "review") if n in groups]:
        group = groups[name]
        if spend.stopped:
            break
        if name != "review":
            for c in group[:1]:   # the first request writes the prefix cache; the rest read it
                go(c, est[c["id"]])
            with cf.ThreadPoolExecutor(max_workers=parallel) as ex:
                list(ex.map(lambda c: go(c, est[c["id"]]), group[1:]))
        else:
            wave = max(1, parallel) * 2
            by_arm = {a: [c for c in group if c["arm"] == a] for a in "AB"}
            for k in range(0, len(by_arm["A"]), wave):
                for a in "AB":
                    with cf.ThreadPoolExecutor(max_workers=parallel) as ex:
                        list(ex.map(lambda c: go(c, est[c["id"]]), by_arm[a][k:k + wave]))
                if spend.stopped:
                    break
    return results, spend, skipped


def score(plan, results, prices):
    """Everything the stop rule and the report need, from the results (a pure function of plan and results)."""
    by = plan["batch_data"]
    out = {"producers": {}, "reviews": [], "controls": []}
    # producers
    for name in ("haiku", "sonnet"):
        rows = []
        for p in plan["producers"]:
            res = results.get(f"P-{name}-{ST.slug(p['iid'])}")
            row = {"batch": p["batch"], "iid": p["iid"], "agent_filed": p["filed"], "agent": p["agent"],
                   "ran": res is not None, "usd": (res or {}).get("usd"), "error": (res or {}).get("error")}
            ans = (res or {}).get("answer")
            if ans:
                with tempfile.TemporaryDirectory() as td:
                    try:
                        prow, pclauses = p["prepared"]
                        ST.write_answer_sheet(ans, p["iid"], td, DEC_FIELDS, prow, CLAUSE_FIELDS, pclauses, "stateless-gauge")
                        r, cl, _, asm = ST.validate_sheet_folder(td, p["iid"], DEC_FIELDS, prow, CLAUSE_FIELDS)
                        row["sheet_valid"] = True
                        row["stateless"] = sheet_summary(r, cl, asm)
                        row["compare"] = compare_producer(p["agent"], row["stateless"])
                    except (ValueError, OSError) as exc:
                        row["sheet_valid"] = False
                        row["sheet_error"] = str(exc)[:300]
                        row["stateless"] = None
            rows.append(row)
        out["producers"][name] = rows
    # reviews
    for r in plan["reviews"]:
        ra = (results.get(f"R-A-{ST.slug(r['iid'])}-{r['claim_sha256'][:8]}") or {})
        rb = (results.get(f"R-B-{ST.slug(r['iid'])}-{r['claim_sha256'][:8]}") or {})
        va, vb = (ra.get("answer") or {}).get("verdict"), (rb.get("answer") or {}).get("verdict")
        row = {"batch": r["batch"], "iid": r["iid"], "claim_sha256": r["claim_sha256"], "planted": r["planted"],
               "agent_A": r.get("agent_A"), "agent_B": r.get("agent_B"), "stateless_A": va, "stateless_B": vb,
               "usd_A": ra.get("usd"), "usd_B": rb.get("usd"), "ran": bool(ra) and bool(rb)}
        row["agent_pair"] = pair_decision(r.get("agent_A"), r.get("agent_B")) if r.get("agent_A") and r.get("agent_B") else None
        row["stateless_pair"] = pair_decision(va, vb) if va and vb else None
        if r["planted"]:
            terms = frozenset(C.DATE_TERMS)
            ca = C.caught({"verdict": va, "defects": (ra.get("answer") or {}).get("defects")}, terms) if va else False
            cb = C.caught({"verdict": vb, "defects": (rb.get("answer") or {}).get("defects")}, terms) if vb else False
            row.update(caught_A=ca, caught_B=cb, control_type=r.get("control_type"))
            out["controls"].append({"batch": r["batch"], "instrument_id": r["iid"], "caught_A": ca, "caught_B": cb,
                                    "ran": row["ran"], "agent_caught_both": r.get("agent_A") == "rejected"
                                    and r.get("agent_B") == "rejected"})
        else:
            row["pair_agrees_with_agent"] = (row["stateless_pair"] == row["agent_pair"]) if row["stateless_pair"] else None
            row["arm_A_agrees"] = (va == r.get("agent_A")) if va else None
            row["arm_B_agrees"] = (vb == r.get("agent_B")) if vb else None
        out["reviews"].append(row)
    return out


def summarize(plan, results, scored, prices, cap, spent, skipped, models):
    """Aggregates, cost per filed claim, cache evidence and the stop rule."""
    gen = [r for r in scored["reviews"] if not r["planted"]]
    ran_gen = [r for r in gen if r["stateless_pair"]]
    disagree = sum(1 for r in ran_gen if r["stateless_pair"] != r["agent_pair"])
    arm_dis = {a: sum(1 for r in gen if r.get(f"arm_{a}_agrees") is False) for a in "AB"}
    agent_ab = sum(1 for r in gen if r["agent_A"] != r["agent_B"])
    # population weights from the whole Papinian corpus (the sample is 50% filed; the corpus is not)
    att = sum(len(bd["members"]) for bd in plan["batch_data"].values())
    filed = sum(len(bd["filed"]) for bd in plan["batch_data"].values())
    w_f = filed / att if att else 0.0
    gen_total = file_total = 0
    for bd in plan["batch_data"].values():
        _, _, ctl, _ = regenerate_controls(bd["batch"], bd["claims"])
        cset = {k["instrument_id"] for k in ctl}
        for c in bd["claims"]:
            sha = canon(c)
            a, b = bd["reviews"]["A"].get(sha), bd["reviews"]["B"].get(sha)
            if c["instrument_id"] in cset or not a or not b:
                continue
            gen_total += 1
            file_total += (a["verdict"] == "upheld" and b["verdict"] == "upheld")
    w_rf = file_total / gen_total if gen_total else 0.0

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    stage_usd = {}
    for res in results.values():
        stage_usd[res["stage"]] = round(stage_usd.get(res["stage"], 0.0) + float(res.get("usd") or 0.0), 6)
    prod = {}
    for name, rows in scored["producers"].items():
        ran = [r for r in rows if r["ran"] and r.get("stateless")]
        f_rows, u_rows = [r for r in rows if r["agent_filed"]], [r for r in rows if not r["agent_filed"]]
        sub = lambda rs: mean([1.0 if (r.get("stateless") or {}).get("submit") else 0.0 for r in rs if r.get("stateless")])
        cost = lambda rs: mean([r["usd"] for r in rs if r["usd"] is not None])
        cmp_ = [r["compare"] for r in ran]
        prod[name] = {
            "n_ran": len(ran), "n_valid_sheet": sum(1 for r in rows if r.get("sheet_valid")),
            "outcome_match": sum(1 for c in cmp_ if c["outcome_match"]), "outcome_n": len(cmp_),
            "status_match": sum(1 for c in cmp_ if c["status_match"]), "status_n": sum(1 for c in cmp_ if c["status_match"] is not None),
            "end_dates_match": sum(1 for c in cmp_ if c["end_dates_match"]), "end_dates_n": sum(1 for c in cmp_ if c["end_dates_match"] is not None),
            "submit_rate_filed": sub(f_rows), "submit_rate_unfiled": sub(u_rows),
            "usd_total": round(sum(r["usd"] or 0 for r in rows), 4), "usd_mean": cost(rows),
            "usd_mean_filed": cost(f_rows), "usd_mean_unfiled": cost(u_rows)}
        pr = prod[name]
        pr["submit_rate_population"] = (w_f * (pr["submit_rate_filed"] or 0) + (1 - w_f) * (pr["submit_rate_unfiled"] or 0))
        pr["usd_per_order_population"] = (w_f * (pr["usd_mean_filed"] or 0) + (1 - w_f) * (pr["usd_mean_unfiled"] or 0))
    # reviewer cost and pass rates
    pair_cost = mean([(r["usd_A"] or 0) + (r["usd_B"] or 0) for r in gen if r["ran"]])
    up_f = mean([1.0 if r["stateless_pair"] == "file" else 0.0 for r in ran_gen if r["agent_pair"] == "file"])
    up_o = mean([1.0 if r["stateless_pair"] == "file" else 0.0 for r in ran_gen if r["agent_pair"] != "file"])
    upheld_rate = w_rf * (up_f or 0) + (1 - w_rf) * (up_o or 0)
    cpf = {}
    for name, pr in prod.items():
        sr = pr["submit_rate_population"]
        if pair_cost is None or not sr or not upheld_rate:
            cpf[name] = None
            continue
        reveal_overhead = pair_cost / 15.0   # one planted control per 15 claims gets a reveal pass of two requests
        cpf[name] = round((pr["usd_per_order_population"] + sr * (pair_cost + reveal_overhead)) / (sr * upheld_rate), 4)
    # haiku vs sonnet: haiku agrees with the agent at least as often as sonnet, within one order of 60
    def agree(name):
        p = prod.get(name) or {}
        return (p.get("outcome_match", 0), p.get("end_dates_match", 0))
    hm = bool(prod.get("haiku") and prod.get("sonnet") and prod["haiku"]["n_ran"] and prod["sonnet"]["n_ran"]
              and agree("haiku")[0] >= agree("sonnet")[0] - 1 and agree("haiku")[1] >= agree("sonnet")[1] - 1)
    planned = sum(1 for _ in results) + len(skipped)
    failed = [r["id"] for r in results.values() if not r.get("answer")]
    complete = not skipped and not failed and all(r["ran"] for r in scored["reviews"]) \
        and all(p["ran"] for rows in scored["producers"].values() for p in rows)
    rule = stop_rule(scored["controls"], {"count": disagree, "n": len(ran_gen)}, cpf.get("sonnet"), hm, complete)
    caches = []
    for res in results.values():
        if res.get("rounds"):
            caches.append({"label": res["id"], "started_utc": res["rounds"][0]["started_utc"],
                           "stateless": {"prefix_sha256": res["prefix_sha256"], "prefix_tokens_est": res["prefix_tokens_est"],
                                         "calls": res["rounds"][0]["calls"]}})
    return {"models": models, "cap_usd": cap, "spent_usd": round(spent, 4), "skipped_calls": skipped, "failed_calls": failed,
            "complete": complete, "stage_usd": stage_usd, "producers": prod,
            "controls": {"expected": plan["controls_expected"], "regenerated": plan["controls_regenerated"],
                         "caught_A": sum(1 for c in scored["controls"] if c["caught_A"]),
                         "caught_B": sum(1 for c in scored["controls"] if c["caught_B"]),
                         "caught_both": sum(1 for c in scored["controls"] if c["caught_A"] and c["caught_B"]),
                         "n_reviewed": sum(1 for c in scored["controls"] if c["ran"]), "n": len(scored["controls"]),
                         "agent_arms_caught_both": sum(1 for c in scored["controls"] if c["agent_caught_both"])},
            "review_agreement": {"genuine_claims": len(gen), "compared": len(ran_gen),
                                 "pair_disagreements": disagree, "arm_A_disagreements": arm_dis["A"],
                                 "arm_B_disagreements": arm_dis["B"],
                                 "agent_arms_own_disagreement_this_sample": f"{agent_ab}/{len(gen)}",
                                 "agent_arms_own_disagreement_owner_figure": f"{AGENT_ARM_DISAGREEMENT[0]}/{AGENT_ARM_DISAGREEMENT[1]}"},
            "cost": {"reviewer_pair_usd_mean": pair_cost, "upheld_rate_population": upheld_rate,
                     "population_weights": {"order_filed_share": w_f, "reviewed_genuine_filed_share": w_rf,
                                            "orders_attempted": att, "orders_filed": filed},
                     "usd_per_filed_claim": cpf,
                     "formula": "(producer usd per order + submit_rate x (reviewer pair usd x (1 + 1/15 reveal))) / "
                                "(submit_rate x upheld_rate); strata reweighted to the Papinian corpus",
                     "agent_reference_usd_per_filed": 4.71},
            "cache": ST.cache_evidence(caches), "stop_rule": rule, "planned_requests": planned}


def write_report(out, summary, plan, scored, dry=None):
    s, r = summary, summary["stop_rule"]
    L = [f"# Stateless gauge report", "",
         f"Verdict: **{r['verdict']}**; haiku_matches_sonnet: **{str(r['haiku_matches_sonnet']).lower()}**.", ""]
    L += ["Reasons: " + ("; ".join(r["reasons"]) if r["reasons"] else "none (every stop-rule test passed)."), "",
          f"Spent ${s['spent_usd']:.2f} of the ${s['cap_usd']:.2f} cap at list price (jobs/necker-costs/PRICES.json). "
          f"Run complete: {s['complete']}.", "", "## Planted controls", "",
          f"Regenerated {s['controls']['regenerated']} of the {s['controls']['expected']} Papinian controls (review_prep.py "
          "seeding; the u* batches left no reviewable packet in the checkout). Stateless arm A caught "
          f"{s['controls']['caught_A']}/{s['controls']['n']}, arm B {s['controls']['caught_B']}/{s['controls']['n']}, both "
          f"{s['controls']['caught_both']}/{s['controls']['n']} (agent arms caught both on "
          f"{s['controls']['agent_arms_caught_both']}).", "", "## Review agreement", "",
          f"On {s['review_agreement']['genuine_claims']} genuine reviewed claims the stateless pair disagreed with the agent "
          f"pair on {s['review_agreement']['pair_disagreements']} of {s['review_agreement']['compared']} compared "
          f"(limit: the agent arms' own {s['review_agreement']['agent_arms_own_disagreement_owner_figure']}); arm A "
          f"{s['review_agreement']['arm_A_disagreements']}, arm B {s['review_agreement']['arm_B_disagreements']}. In this "
          f"sample the agent arms disagreed with each other on {s['review_agreement']['agent_arms_own_disagreement_this_sample']}.",
          "", "## Producers", "", "| model | ran | valid sheets | outcome match | status match | end dates match | list-price USD |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for name, p in s["producers"].items():
        L.append(f"| {name} | {p['n_ran']} | {p['n_valid_sheet']} | {p['outcome_match']}/{p['outcome_n']} | "
                 f"{p['status_match']}/{p['status_n']} | {p['end_dates_match']}/{p['end_dates_n']} | {p['usd_total']:.2f} |")
    L += ["", "## Cost", "", f"List-price cost per stage: {json.dumps(s['stage_usd'])}.", "",
          f"Cost per filed claim: {json.dumps(s['cost']['usd_per_filed_claim'])} (Papinian agent lane: $4.71). "
          f"Formula: {s['cost']['formula']}.", "", "## Cache evidence", ""]
    for c in s["cache"][:6]:
        L.append(f"- prefix {c['prefix_sha256'][:12]} (about {c['prefix_tokens_est']} tokens): {c['processes']} processes; "
                 f"{c['later_processes_with_cache_read_near_prefix']} of {c['later_processes']} later processes read at least "
                 "80% of the prefix from cache on their first call.")
    L += ["", "The run is a replay: reviewers see Papinian's claims, not the stateless producers' claims, and the cost per "
          "filed claim combines the two stages' measured costs with Papinian's corpus rates. Nothing here certifies anything."]
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "GAUGE_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, default=REPO)
    ap.add_argument("--out", default=OUT_DEFAULT, help="repo-relative folder for GAUGE_RESULTS.json and GAUGE_REPORT.md")
    ap.add_argument("--scratch", type=Path, help="durable folder outside the repository for prefixes, streams and state "
                                                 "(required for a paid run; a dry run uses a temp folder)")
    ap.add_argument("--seed", default=SEED_DEFAULT)
    ap.add_argument("--cap-usd", type=float, default=CAP_DEFAULT, help="stop launching when list-price spend would pass this")
    ap.add_argument("--dry-run", action="store_true", help="render every prompt, prefix and schema; call no model")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--program", default="claude", help="the claude executable")
    ap.add_argument("--template", help="JSON file with the worker command template (default: the stateless template)")
    ap.add_argument("--sonnet-model", default=MODELS["sonnet"])
    ap.add_argument("--haiku-model", default=MODELS["haiku"])
    ap.add_argument("--opus-model", default=MODELS["opus"])
    ap.add_argument("--no-cruden", action="store_true", help="skip the cruden number search (testing only)")
    a = ap.parse_args(argv)
    repo = a.repo.resolve()
    models = {"sonnet": a.sonnet_model, "haiku": a.haiku_model, "opus": a.opus_model}
    prices = ST.load_prices(repo)
    for m in models.values():
        if ST.price_row(prices, m) is None:
            print(f"model {m} is not in jobs/necker-costs/PRICES.json", file=sys.stderr)
            return 1
    if a.scratch is None and not a.dry_run:
        print("--scratch is required for a paid run (a durable folder outside the repository)", file=sys.stderr)
        return 1
    tmp = None
    if a.scratch is None:
        tmp = tempfile.TemporaryDirectory()
        scratch = Path(tmp.name)
    else:
        scratch = a.scratch.resolve()
        if scratch.is_relative_to(repo) or repo.is_relative_to(scratch):
            print("--scratch must be outside the repository", file=sys.stderr)
            return 1
    scratch.mkdir(parents=True, exist_ok=True)
    template = json.loads(Path(a.template).read_text(encoding="utf-8")) if a.template else list(ST.STATELESS_TEMPLATE)
    plan = render_all(repo, scratch, a.seed, cruden=not a.no_cruden)
    calls = build_calls(plan, models)
    fc = forecast(plan, calls, prices)
    summ = dry_run_summary(plan, calls, fc)
    rend = scratch / "rendered"
    rend.mkdir(exist_ok=True)
    for c in calls:
        d = rend / c["stage"]
        d.mkdir(exist_ok=True)
        (d / f"{c['id']}.suffix.txt").write_text(c["suffix"], encoding="utf-8", newline="\n")
        pf = rend / "prefixes" / f"{ST.sha256_text(c['prefix'])[:16]}.txt"
        pf.parent.mkdir(exist_ok=True)
        if not pf.exists():
            pf.write_text(c["prefix"], encoding="utf-8", newline="\n")
    (rend / "schemas.json").write_text(json.dumps({"producer": ST.producer_schema(), "reviewer_blind": ST.reviewer_schema()},
                                                  indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))
    print(f"worker command: {' '.join(template[:6])} ... (template configurable with --template)")
    if a.dry_run:
        print(f"DRY RUN: rendered {len(calls)} requests under {rend}; no model was called. Forecast ${fc['total']:.2f} "
              f"at list price against the ${a.cap_usd:.2f} cap.")
        return 0
    if fc["total"] > a.cap_usd:
        print(f"the forecast ${fc['total']:.2f} already exceeds the cap ${a.cap_usd:.2f}; raise --cap-usd or cut the run",
              file=sys.stderr)
    ctx = {"repo": repo, "scratch": scratch, "template": template, "program": a.program, "prices": prices,
           "timeout": a.timeout}
    results, spend, skipped = run_calls(calls, ctx, scratch / "gauge-state.jsonl", a.cap_usd, a.parallel, prices, fc["per_call"])
    scored = score(plan, results, prices)
    summary = summarize(plan, results, scored, prices, a.cap_usd, spend.spent, skipped, models)
    out = (repo / a.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = {"schema": "stateless-gauge/v1", "seed": a.seed, "summary": summary, "dry_run_forecast": summ,
           "producers": scored["producers"], "reviews": scored["reviews"],
           "prefix_checks": {"producer_prefix_identical_per_route": summ["producer_prefix_identical_per_route"]}}
    (out / "GAUGE_RESULTS.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(out, summary, plan, scored)
    r = summary["stop_rule"]
    print(json.dumps({"verdict": r["verdict"], "haiku_matches_sonnet": r["haiku_matches_sonnet"], "reasons": r["reasons"],
                      "spent_usd": summary["spent_usd"], "usd_per_filed_claim": summary["cost"]["usd_per_filed_claim"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
