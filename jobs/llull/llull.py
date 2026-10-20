#!/usr/bin/env python3
"""Llull: checks a research plan before money is spent on it.

Named for Ramon Llull's Ars Magna (c. 1305), paper wheels that cross every term with every other
term and list the questions to ask. Design: research/plans/LLULL_DESIGN.md.

Subcommands (standard library only; run with `python3 -I jobs/llull/llull.py ...`):
  forecast   BRIER: register a numeric forecast (80% interval or a probability) before the run
  outcome    BRIER: record the measured value that resolves a forecast (from a committed file)
  score      Brier / interval score / coverage per planner -> output/CALIBRATION.json
  census     Domesday: zero-agent count of items that hold every required input for a named pool
  premortem  Wheel: plan step x failure mode -> at most 12 questions, mechanical checks first
  rank       Raiffa: rank next actions by (expected ready orders + value of information) per cost
  baserate   turn a resolved Llull outcome into a base-rate row (source = the outcome id)
  selfscore  Juvenal (part): share of resolved misses that were flagged in advance, out-of-sample only
  check      validate the ledger (schemas, measured base rates, registration order, privacy);
             a forecast that cannot be proven first is marked not_preregistered, not failed

Hard rule (as in Junto): Llull earns trust only from measured outcomes. A base rate must be a
measured value with a source path, a forecast is scored only against a recorded measurement, and
Llull never changes the codebook, any claim status, any tier, or the certified count (0).
It reads committed outputs and writes only under jobs/llull/.

Exit codes: 0 ok; 2 bad input or refused request; 3 flagged (needs --accept-flag); 4 check failed.
Append-only ledgers: forecasts.jsonl, outcomes.jsonl, censuses.jsonl and registration.jsonl are never edited.
"""
import argparse, csv, glob, hashlib, json, math, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
WRITTEN_BY = "claude"

# quantity -> (category, cap): cap is "count" or "share" when the Domesday ceiling bounds p90.
QUANTITIES = {
    "ready_orders_gained": ("count", "count"), "accepted_items": ("count", "count"),
    "items_reached": ("count", "count"), "usd_total": ("cost", None),
    "usd_per_ready_order": ("cost", None), "minutes_per_accepted": ("cost", None),
    "upheld_per_attempt": ("rate", "share"), "accepted_per_attempt": ("rate", "share"),
    "accepted_per_target": ("rate", "share"),
    # hit_rate is conditional on a finder's own selection (X1 ran only its 52 eligible orders), so a pool share
    # does not bound it: the review found the X1 tribunal's measured 0.19 at 47x the 0.004 pool share
    "hit_rate": ("rate", None),
    "eligible_share": ("rate", "share"), "cleared_per_queued": ("rate", "share"),
    "items_per_planned": ("rate", "share"), "rejected_per_submitted": ("rate", None),
    "complete_per_accepted": ("rate", None),
}
PROXY_WORDS = ("token", "payload", "byte", "packet", "certificate", "agent_hour", "agent-hour")
FLOOR = {"count": 0.5, "rate": 0.005, "cost": 0.01}   # log-ratio floors per unit category
SCALE = {"count": 1.0, "rate": 0.01, "cost": 1.0}     # interval score is divided by max(|y|, SCALE)
CLASS_FALLBACK = "measured_over_forecast.all_misses"
SECRET_RES = [re.compile(p) for p in (
    r"ghp_[A-Za-z0-9]{6,}", r"github_pat_", r"\bsk-[A-Za-z0-9_-]{8,}", r"\bxox[abprs]-", r"AKIA[0-9A-Z]{8,}",
    r"Bearer\s+\S", r"-----BEGIN", r"\b(token|key|sig|password|secret)=", r"@[A-Za-z0-9-]+\.[A-Za-z]{2,}")]
ABS_PATH_RE = re.compile(r"(^|[\s\"'(])(/(home|tmp|root|Users|var|etc|mnt)/|[A-Za-z]:\\)")


class Refusal(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- small helpers

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args):
    try:
        r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def head():
    return git("rev-parse", "--short", "HEAD")


def read_jsonl(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def append_jsonl(path, rec):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def latest(lines, key):
    """Current state of an id: the line with the highest rev."""
    cur = {}
    for l in lines:
        if l[key] not in cur or l.get("rev", 1) >= cur[l[key]].get("rev", 1):
            cur[l[key]] = l
    return cur


def privacy_problem(text):
    for r in SECRET_RES:
        if r.search(text):
            return "secret-like text (%s)" % r.pattern
    if ABS_PATH_RE.search(text):
        return "absolute path"
    return None


def repo_path_ok(p):
    """A repository-relative path of an existing file. Returns an error string or None."""
    if not p or p.startswith("/") or ".." in Path(p).parts:
        return "source must be a repository-relative path"
    if not (REPO / p).exists():
        return "source file does not exist in the repository: %s" % p
    return None


def new_id(prefix, lines, key):
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    n = sum(1 for l in lines if l.get(key, "").startswith("%s-%s-" % (prefix, day))) + 1
    return "%s-%s-%d" % (prefix, day, n)


class Ledger:
    def __init__(self, d):
        self.dir = Path(d)
        self.out = self.dir.parent / "output"
        self.forecasts = self.dir / "forecasts.jsonl"
        self.outcomes = self.dir / "outcomes.jsonl"
        self.censuses = self.dir / "censuses.jsonl"
        self.base_rates = self.dir / "base_rates.json"
        self.postmortems = self.dir / "postmortems.json"
        self.pools = self.dir / "pools.json"
        self.registration = self.dir / "registration.jsonl"   # append-only marks written by `check --mark`


# ---------------------------------------------------------------- scoring math (pure)

def brier(probs, outcomes):
    """Brier score: mean (p - o)^2 for binary outcomes o in {0, 1}."""
    if not probs or len(probs) != len(outcomes):
        raise ValueError("need equal, non-empty lists")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def murphy(probs, outcomes, bins=5):
    """Murphy (1973) decomposition BS = reliability - resolution + uncertainty (equal-width bins).
    Exact when every forecast in a bin has the same value; otherwise within-bin variance remains."""
    n = len(probs)
    obar = sum(outcomes) / n
    groups = {}
    for p, o in zip(probs, outcomes):
        groups.setdefault(min(bins - 1, int(p * bins)), []).append((p, o))
    rel = res = 0.0
    for g in groups.values():
        fk = sum(p for p, _ in g) / len(g)
        ok = sum(o for _, o in g) / len(g)
        rel += len(g) * (fk - ok) ** 2
        res += len(g) * (ok - obar) ** 2
    return {"reliability": rel / n, "resolution": res / n, "uncertainty": obar * (1 - obar)}


def interval_score(p10, p90, y, alpha=0.2):
    """Winkler/Gneiting-Raftery interval score for the central (1-alpha) interval: width plus
    (2/alpha) x the distance by which the outcome falls outside it."""
    return (p90 - p10) + (2 / alpha) * max(0.0, p10 - y) + (2 / alpha) * max(0.0, y - p90)


def norm_interval_score(p10, p90, y, category):
    return interval_score(p10, p90, y) / max(abs(y), SCALE[category])


def log_ratio(y, p50, category):
    f = FLOOR[category]
    return math.log(max(y, f) / max(p50, f))


# ---------------------------------------------------------------- base rates and forecasts

def load_base_rates(path):
    d = json.loads(Path(path).read_text())
    return {r["key"]: r for r in d["rows"]}


def measured_problem(row):
    """None if the base-rate row is a measured value with a source; else the reason it is not."""
    if row is None:
        return "no such reference class"
    v = row.get("value")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return "value is not a measured number"
    if not row.get("source"):
        return "no source path"
    if row.get("den") is not None:
        if not row["den"] or abs(row["num"] / row["den"] - v) > 0.0006:
            return "value does not equal num/den"
    return None


def class_quantity(key):
    return key.split(".", 1)[0]


def ceiling_flags(quantity, p90, census, unlock_p90=0.0):
    """Flags for a forecast whose p90 may exceed the Domesday ceiling (design 2.3 rule 3).
    census: {'pool_size', 'ceiling_strict', 'ceiling_leads'} in item counts."""
    cap_kind = QUANTITIES[quantity][1]
    if not census or cap_kind is None:
        return []
    size = census["pool_size"] or 1
    strict, leads = census["ceiling_strict"], census["ceiling_leads"]
    if cap_kind == "share":
        strict, leads = strict / size, leads / size
    flags = []
    if p90 > strict + unlock_p90 + 1e-12:
        flags.append("CEILING_EXCEEDED")
        if p90 > leads + unlock_p90 + 1e-12:
            flags.append("CEILING_EXCEEDED_EVEN_COUNTING_LEADS")
    return flags


def validate_forecast(spec, rates, census=None):
    """Return (record, flags). Raises Refusal for anything that must not be registered at all."""
    q = spec["quantity"]
    if any(w in q.lower() for w in PROXY_WORDS) or q not in QUANTITIES:
        raise Refusal("quantity %r is not an allowed outcome unit (proxy units such as tokens, bytes, packets, "
                      "certificates, agent-hours are refused). Allowed: %s" % (q, ", ".join(sorted(QUANTITIES))))
    cat = QUANTITIES[q][0]
    kind = spec["kind"]
    rc = spec.get("reference_class") or ""
    outside, fallback = None, None
    if rc.startswith("new:"):
        if not (spec.get("reason") or "").strip():
            raise Refusal("a new: reference class needs --reason")
    else:
        row = rates.get(rc)
        why = measured_problem(row)
        if why:
            raise Refusal("reference class %r is refused, it has no measured base rate (%s). Measure it first, "
                          "or use new:<key> with --reason." % (rc, why))
        if kind == "interval" and class_quantity(rc) != q and class_quantity(rc) != "measured_over_forecast":
            raise Refusal("reference class %r measures %s, not %s" % (rc, class_quantity(rc), q))
        if class_quantity(rc) == q:
            outside = row["value"]
    rec = {"quantity": q, "kind": kind, "reference_class": rc, "outside_view": outside,
           "n_studies_in_class": None if rc.startswith("new:") else rates[rc].get("n_studies", 1)}
    flags = []
    if kind == "interval":
        p10, p50, p90 = spec["p10"], spec["p50"], spec["p90"]
        if None in (p10, p50, p90) or not (p10 <= p50 <= p90):
            raise Refusal("interval needs p10 <= p50 <= p90 (an 80% central interval)")
        rec.update(p10=p10, p50=p50, p90=p90)
        if cat == "rate" and not (0.0 <= p10 and p90 <= 1.0):
            raise Refusal("%s is a share: p10..p90 must lie in [0, 1]" % q)
        few = rc.startswith("new:") or rec["n_studies_in_class"] < 3
        hi = min(2 * p50, 1.0) if cat == "rate" else 2 * p50
        if few and p50 > 0 and not (p10 <= 0.1 * p50 and p90 >= hi):
            raise Refusal("class has fewer than 3 studies: the interval must be at least [0.1 x p50, 2 x p50] = "
                          "[%g, %g]" % (0.1 * p50, hi))
        if outside is not None and outside > 0 and not (0.5 <= p50 / outside <= 2.0) \
                and not (spec.get("deviation") or "").strip():
            raise Refusal("p50 %g departs from the measured outside view %g by more than 2x: give --deviation"
                          % (p50, outside))
        if (rc.startswith("new:") or outside is None) and cat != "cost":
            # the all-misses ratio measures outputs that fell short; applied to a cost it would cut the cost
            shrink = rates.get(CLASS_FALLBACK)
            if shrink and not measured_problem(shrink):
                fallback = round(shrink["value"] * p50, 6)
                rec["shrunk_p50_from_all_misses"] = fallback
        flags += ceiling_flags(q, p90, census, spec.get("unlock_p90") or 0.0)
    else:
        prob = spec.get("prob")
        if prob is None or not 0.0 <= prob <= 1.0 or not (spec.get("event") or "").strip():
            raise Refusal("binary needs --event text and --prob in [0, 1]")
        rec.update(event=spec["event"], prob=prob)
    if spec.get("deviation"):
        rec["deviation"] = spec["deviation"]
    return rec, flags


def planner_key(p):
    return "%s:%s" % (p.get("agent", "?"), p.get("model", "?"))


# ---------------------------------------------------------------- Domesday census

POOL_DEFS = {
    "Y1": {
        "title": "Y1 modern no-status",
        "describe": "numeric EO >= 7532, no provisional YES/NO, not ready",
        "default_requires": ["original_text_held", "status_evidence_held"],
        "reference": "plan EXCAVATOR_FUNNEL_2026-10-20: 4,274 no-status modern orders, 4,273 with status-history/OFR records, "
                     "3,952 with official text (counted by date, main f57cffe8)",
    },
    "Y2": {
        "title": "Y2 modern status+text",
        "describe": "numeric EO >= 7532, status yes/no, original text done, not ready, no claim",
        "default_requires": ["status_present", "original_text_held", "ending_or_current_held"],
        "reference": "scratch y2_predictor (ACTING_PROVISIONS main file only): pool 2,063; strict 64; leads counted 389 (18.9%)",
    },
    "X1": {
        "title": "pre-1937 X1 pool",
        "describe": "everything that is not numeric EO >= 7532 (numbered before 7532 or unnumbered)",
        "default_requires": ["status_present", "original_text_held"],
        "reference": "X1 pilot (research/production/x1-2026-10-19/REPORT.md): 52 of 8,014 past prerequisites, counted by signing date",
    },
}


ENDING_VERBS = ("revoke", "supersede", "terminate", "abolish")
GATES_REV = 2   # rev 2 (2026-10-20 review): ending verbs only and whole-scope TERMs only; rev 1 counted any
                # whole-scope ACT verb (transfer, other) and section-level TERM end dates


def eo_num(iid):
    m = re.match(r"EO:(\d+)", iid)  # prefix match, as the Y2 predictor: EO:7600-2 counts as 7600
    return int(m.group(1)) if m else None


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


class Data:
    """Lazy readers over committed outputs. Each returns plain sets or dicts."""

    def __init__(self, repo=REPO):
        self.repo = Path(repo)
        self._c = {}

    def _memo(self, k, fn):
        if k not in self._c:
            self._c[k] = fn()
        return self._c[k]

    def tracker(self):
        return self._memo("tracker", lambda: read_csv(self.repo / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"))

    def _jsonl_parts(self, rel):
        base = self.repo / rel
        files = [base] + sorted(Path(p) for p in glob.glob(str(base).replace(".jsonl", ".part*.jsonl")))
        for f in files:
            with open(f) as fh:
                for l in fh:
                    if l.strip():
                        yield json.loads(l)

    def acting(self):
        def build():
            whole, named = set(), set()
            for a in self._jsonl_parts("jobs/claim-kit/output/ACTING_PROVISIONS.jsonl"):
                if a.get("names_target"):
                    named.add(a["target_id"])
                    # an ending verb only: a whole-scope amend, transfer or "other" does not end the order
                    if a.get("scope") == "whole" and a.get("effective_date") and a.get("verb") in ENDING_VERBS:
                        whole.add(a["target_id"])
            return whole, named
        return self._memo("acting", build)

    def term_end(self):
        # whole-order terms only: a section's own end date (scope_id "...#sec4-b") does not end the order
        return self._memo("term", lambda: {t["instrument_id"] for t in self._jsonl_parts(
            "jobs/claim-kit/output/OWN_TERMS.jsonl") if t.get("computed_end_candidate")
            and str(t.get("scope_id", "")).endswith("#whole")})

    def own_terms_any(self):
        return self._memo("terms_any", lambda: {t["instrument_id"] for t in self._jsonl_parts(
            "jobs/claim-kit/output/OWN_TERMS.jsonl")})

    def current_leads(self):
        def build():
            out = set()
            for r in read_csv(self.repo / "jobs/current-law/output/ORDERS_CURRENT_LAW.csv"):
                if int(r["usc_predicate_leads"] or 0) + int(r["ecfr_predicate_leads"] or 0) > 0:
                    out.add(r["instrument_id"])
            return out
        return self._memo("cur", build)

    def status_evidence(self):
        def build():
            out = set()
            with open(self.repo / "jobs/status-history/output/INDEX.json") as f:
                index = json.load(f)
            for x in index:
                if (x.get("observations") or 0) > 0 or (x.get("events") or 0) > 0:
                    out.add(x["instrument_id"])
            for r in read_csv(self.repo / "jobs/later-events/output/CATALOG_INDEX.csv"):
                if (r.get("disposition_notes") or "").strip():
                    out.add(r["id"])
            return out
        return self._memo("statev", build)

    def drafts(self):
        def build():
            out = set()
            with open(self.repo / "jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl") as f:
                for l in f:
                    if l.strip():
                        out.add(json.loads(l)["instrument_id"])
            return out
        return self._memo("drafts", build)

    def todo(self):
        return self._memo("todo", lambda: {r["instrument_id"]: r for r in read_csv(
            self.repo / "jobs/claim-drafts/output/TODO_BY_ORDER.csv")})


def _held(b):
    return "held" if b else "no"


def g_ending_instrument(row, D):
    if row["provisional_status"] != "no":
        return "na"
    whole, _ = D.acting()
    return _held(row["instrument_id"] in whole or row["instrument_id"] in D.term_end())


def g_current_predicate(row, D):
    # No source in the repository holds a CURRENT predicate yet: a predicate lead is only a lead.
    if row["provisional_status"] != "yes":
        return "na"
    return "lead" if row["instrument_id"] in D.current_leads() else "no"


def g_ending_or_current(row, D):
    return g_ending_instrument(row, D) if row["provisional_status"] == "no" else g_current_predicate(row, D)


def g_ending_held_if_no(row, D):
    """Status-free version for pools that have no status yet: held if a whole ending ACT/TERM exists, lead if any
    ACT names the order or any OWN_TERMS row exists."""
    whole, named = D.acting()
    i = row["instrument_id"]
    if i in whole or i in D.term_end():
        return "held"
    return "lead" if (i in named or i in D.own_terms_any()) else "no"


def g_ending_or_current_lead2(row, D):
    """NO: g_ending_held_if_no; YES: a CURRENT predicate lead; no status: na."""
    st = row["provisional_status"]
    if st == "no":
        return g_ending_held_if_no(row, D)
    if st == "yes":
        return "lead" if row["instrument_id"] in D.current_leads() else "no"
    return "na"


GATES = {
    "status_present": ("provisional_status is yes or no (readiness tracker)",
                       lambda r, D: _held(r["provisional_status"] in ("yes", "no"))),
    "original_text_held": ("step_original_text = done (readiness tracker)",
                           lambda r, D: _held(r["step_original_text"] == "done")),
    "status_evidence_held": ("a status-history observation/event or an OFR catalog disposition note",
                             lambda r, D: _held(r["instrument_id"] in D.status_evidence())),
    "ending_instrument_held": ("NO orders: whole-scope revoke/supersede/terminate/abolish ACT with effective date, "
                               "or whole-scope TERM with computed end (claim-kit)",
                               g_ending_instrument),
    "current_predicate_held": ("YES orders: a CURRENT predicate; leads are not held (current-law)", g_current_predicate),
    "ending_or_current_held": ("ending_instrument_held for NO orders, current_predicate_held for YES orders",
                               g_ending_or_current),
    "ending_held_if_no": ("ending ACT/TERM held whatever the status; lead if an ACT names the order or an OWN_TERMS row "
                          "exists (for pools with no status yet)", g_ending_held_if_no),
    "ending_or_current_lead2": ("NO: ending_held_if_no; YES: CURRENT lead; no status: na", g_ending_or_current_lead2),
    "ending_step_done": ("tracker step_ending_or_current_basis = done",
                         lambda r, D: _held(r["step_ending_or_current_basis"] == "done")),
    "claim_draft_present": ("a machine claim draft exists (claim-drafts)",
                            lambda r, D: _held(r["instrument_id"] in D.drafts())),
    "no_evidence_conflict": ("claim-drafts TODO row exists with an empty conflicts column",
                             lambda r, D: _held(r["instrument_id"] in D.todo()
                                                and not D.todo()[r["instrument_id"]]["conflicts"])),
    "only_judgment_left": ("claim-drafts TODO says only judgment is left",
                           lambda r, D: _held(D.todo().get(r["instrument_id"], {}).get("only_judgment_left") == "yes")),
}


POOL_KEYS = {"title", "describe", "from", "where", "eo_gte", "eo_lt", "open_steps_max", "open_steps_min",
             "ids_file", "gate_states", "default_requires", "reference"}


def load_pools(path):
    """Custom pools from a pools file (JSON, declarative; no code runs). Y1, Y2 and X1 are built in and cannot be
    redefined. Returns {name: definition}."""
    p = Path(path) if path else None
    if not p or not p.exists():
        return {}
    d = json.loads(p.read_text())
    out = {}
    for name, df in d.get("pools", {}).items():
        if name in POOL_DEFS:
            raise Refusal("pools file may not redefine the built-in pool %s" % name)
        bad = set(df) - POOL_KEYS
        if bad:
            raise Refusal("pool %s: unknown keys %s (known: %s)" % (name, sorted(bad), sorted(POOL_KEYS)))
        for g in df.get("default_requires", []) + list(df.get("gate_states", {})):
            if g not in GATES:
                raise Refusal("pool %s: unknown gate %r" % (name, g))
        if not df.get("default_requires"):
            raise Refusal("pool %s needs default_requires (the gates its census counts)" % name)
        out[name] = df
    return out


def pool_def(pool, pools):
    if pool in POOL_DEFS:
        return POOL_DEFS[pool]
    if pools and pool in pools:
        return pools[pool]
    raise Refusal("unknown pool %r (known: %s)" % (pool, ", ".join(list(POOL_DEFS) + sorted(pools or {}))))


def ids_from_file(rel):
    err = repo_path_ok(rel)
    if err:
        raise Refusal("ids_file: " + err)
    text = (REPO / rel).read_text()
    try:
        v = json.loads(text)
        return set(v if isinstance(v, list) else v["ids"]), hashlib.sha256(text.encode()).hexdigest()[:16]
    except ValueError:
        return {l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")}, \
            hashlib.sha256(text.encode()).hexdigest()[:16]


def _col_match(v, want):
    if isinstance(want, dict):
        return not _col_match(v, want["not"])
    return v in want if isinstance(want, list) else v == want


def custom_pool_rows(pool, df, D, pools, seen=()):
    if pool in seen:
        raise Refusal("pool %s: circular 'from'" % pool)
    src = df.get("from", "all")
    rows = D.tracker() if src == "all" else pool_rows(src, D, pools, seen + (pool,))
    ids = ids_from_file(df["ids_file"])[0] if df.get("ids_file") else None
    out = []
    for r in rows:
        if ids is not None and r["instrument_id"] not in ids:
            continue
        n = eo_num(r["instrument_id"]) or 0
        if "eo_gte" in df and not n >= df["eo_gte"]:
            continue
        if "eo_lt" in df and not n < df["eo_lt"]:
            continue
        if any(not _col_match(r.get(c), w) for c, w in df.get("where", {}).items()):
            continue
        if "open_steps_max" in df or "open_steps_min" in df:
            k = sum(1 for c, v in r.items() if c.startswith("step_") and v == "open")
            if k > df.get("open_steps_max", 10 ** 6) or k < df.get("open_steps_min", 0):
                continue
        if any(GATES[g][1](r, D) not in st for g, st in df.get("gate_states", {}).items()):
            continue
        out.append(r)
    return out


def pool_rows(pool, D, pools=None, seen=()):
    rows = D.tracker()
    if pool not in POOL_DEFS:
        return custom_pool_rows(pool, pool_def(pool, pools), D, pools, seen)
    if pool == "Y1":
        return [r for r in rows if (eo_num(r["instrument_id"]) or 0) >= 7532 and r["provisional_status"] == ""
                and r["ready_for_human_review"] == "no"]
    if pool == "Y2":
        return [r for r in rows if (eo_num(r["instrument_id"]) or 0) >= 7532
                and r["provisional_status"] in ("yes", "no") and r["step_original_text"] == "done"
                and r["ready_for_human_review"] == "no" and r["claim_present"] == "no"]
    if pool == "X1":
        return [r for r in rows if not ((eo_num(r["instrument_id"]) or 0) >= 7532)]
    raise Refusal("unknown pool %r (known: %s)" % (pool, ", ".join(POOL_DEFS)))


def run_census(pool, requires=None, D=None, rows=None, pools=None):
    """Joint, per-item prerequisite count. Strict ceiling: every gate 'held' (or 'na').
    Leads ceiling: every gate held, na or lead."""
    D = D or Data()
    df = POOL_DEFS.get(pool) or (pools or {}).get(pool) or {}
    requires = requires or df.get("default_requires")
    if not requires:
        raise Refusal("pool %r has no default gates: pass --requires" % pool)
    for g in requires:
        if g not in GATES:
            raise Refusal("unknown gate %r (known: %s)" % (g, ", ".join(GATES)))
    if rows is None:
        pool_def(pool, pools)   # refuses an unknown pool by name
        rows = pool_rows(pool, D, pools)
    n = len(rows)
    alone = {g: {"held": 0, "lead": 0, "na": 0, "no": 0} for g in requires}
    cum = {g: 0 for g in requires}
    strict = leads = 0
    for r in rows:
        states = [GATES[g][1](r, D) for g in requires]
        for g, s in zip(requires, states):
            alone[g][s] += 1
        for i, g in enumerate(requires):
            if all(s in ("held", "na") for s in states[:i + 1]):
                cum[g] += 1
        if all(s in ("held", "na") for s in states):
            strict += 1
        if all(s in ("held", "na", "lead") for s in states):
            leads += 1
    expected = n
    for g in requires:
        expected *= (alone[g]["held"] + alone[g]["na"]) / n if n else 0
    flags = []
    if expected >= 1.5 * max(strict, 1) and expected >= 1.5:
        flags.append("ASSUMED_INDEPENDENCE")  # fewer items hold every gate than independence predicts: multiplying marginal rates overstates
    rec = {"schema": "llull.census/1", "pool": pool, "pool_title": df.get("title", pool),
            "describe": df.get("describe"), "pool_kind": "builtin" if pool in POOL_DEFS else "custom",
            "pool_size": n, "requires": requires, "alone": alone, "cumulative_strict": cum,
            "ceiling_strict": strict, "ceiling_leads": leads,
            "share_strict": round(strict / n, 4) if n else 0.0, "share_leads": round(leads / n, 4) if n else 0.0,
            "product_of_marginals": round(expected, 2), "flags": flags,
            "reference": df.get("reference"), "gates_rev": GATES_REV,
            "commit": head(), "written_at": now()}
    if pool not in POOL_DEFS and df:
        rec["pool_def"] = df   # the definition used, so a sub-pool census can be reproduced from the record alone
        if df.get("ids_file"):
            rec["ids_sha256_16"] = ids_from_file(df["ids_file"])[1]
    return rec


def census_table(c):
    lines = ["pool %s: %s items (%s)" % (c["pool"], format(c["pool_size"], ","),
                                         c.get("describe") or POOL_DEFS.get(c["pool"], {}).get("describe", "")),
             "%-26s %8s %8s %8s %12s" % ("gate", "held", "lead", "na", "cumulative")]
    for g in c["requires"]:
        a = c["alone"][g]
        lines.append("%-26s %8d %8d %8d %12d" % (g, a["held"], a["lead"], a["na"], c["cumulative_strict"][g]))
    lines.append("CEILING strict       %6d = %.1f%% of pool" % (c["ceiling_strict"], 100 * c["share_strict"]))
    lines.append("CEILING leads counted%6d = %.1f%% of pool" % (c["ceiling_leads"], 100 * c["share_leads"]))
    lines.append("product of marginals %.1f vs joint %d%s" % (c["product_of_marginals"], c["ceiling_strict"],
                 "  -> ASSUMED_INDEPENDENCE flag" if c["flags"] else ""))
    if c.get("reference"):
        lines.append("reference: " + c["reference"])
    return "\n".join(lines)


# ---------------------------------------------------------------- Wheel (premortem)

def load_modes():
    return json.loads((ROOT / "failure_modes.json").read_text())["modes"]


def plan_steps(path):
    """Steps of a plan file. JSON spec: its 'steps'. Markdown/text: headings, list items, table rows."""
    p = Path(path)
    text = p.read_text()
    if p.suffix == ".json":
        spec = json.loads(text)
        return spec, [{"step": s.get("step") or s.get("name", "?"), "text": json.dumps(s, sort_keys=True), "raw": s,
                       "requires_unmeasured": list(s.get("requires_unmeasured", [])) + [
                           "%s (not a registered gate)" % g for g in s.get("requires", []) if g not in GATES]}
                      for s in spec.get("steps", [])]
    steps = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^\|[\s:-]+\|", s):
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            label = " ".join(cells[:2])
        elif re.match(r"^(#{1,4}\s|[-*]\s|\d+[.)]\s)", s):
            label = re.sub(r"^(#{1,4}\s|[-*]\s|\d+[.)]\s)", "", s)
        else:
            # a paragraph line continues the step above it: targets and forecasts are often stated in
            # plain prose under a heading ("## Probe pass test" / "upheld per attempted order >= 50%")
            if s and steps and len(steps[-1]["text"]) < 1500:
                steps[-1]["text"] += " " + s
            continue
        if len(label) >= 12:
            steps.append({"step": label[:90], "text": s, "raw": None, "requires_unmeasured": []})
    return {}, steps[:40]


NUM_NEAR_READY = re.compile(r"(\d[\d,]{2,})\s+(?:[a-z-]+\s+){0,2}(?:ready|upheld|accepted|claims)", re.I)
# a stated per-attempt rate for the outcome unit: "upheld ... >= 50%" or "upheld per attempt at p10 0.015, p50 0.15"
RATE_TARGET = re.compile(r"\b(upheld|accepted|ready)\b[^\n%;]{0,60}?(?:\bp50\s+(0?\.\d+)|(\d+(?:\.\d+)?)\s?%)", re.I)
NEGATED = re.compile(r"\b(never|not|no|don't|do not)\b[^.;]{0,25}$", re.I)
NUM_ORDERS = re.compile(r"(\d[\d,]{2,})\s+(?:[a-z-]+\s+){0,2}orders", re.I)
RATE_NUMBER = re.compile(r"\d+(?:\.\d+)?\s?%|\b(?:rate|share|probability|chance)\b[^.\n]{0,25}?\b0?\.\d+", re.I)
SAVING = re.compile(r"\b(sav(?:e|es|ing|ings)|cheaper|cut|reduc\w+|fewer|faster|speed\w*)\b", re.I)
REVIEWER_COST = re.compile(r"review\w*[^.;]{0,40}(cost|minute|\$|usd)|(cost|minute|\$|usd)[^.;]{0,40}review", re.I)
SOURCE_CITE = re.compile(r"[\w/.-]+\.(?:md|csv|json|jsonl)\b|\b[a-z_]+\.[a-z_]+\b(?=.*(?:measured|base rate))", re.I)
OWNER_WORDS = re.compile(r"\b(owner|approv\w+|waive\w*|rule change|policy)\b", re.I)
HOST_RE = re.compile(r"https?://[^\s\"')]+|\b[\w-]+\.(?:gov|org|com|edu)\b|\b(?:govinfo|hathitrust|archive\.org|proquest)\b", re.I)


def _nums(rx, text):
    return [int(x.replace(",", "")) for x in rx.findall(text)]


def _model_family(m):
    return str(m).lower().replace("_", "-").split("-")[0]


def mode_check(key, step, ctx):
    """Run one failure mode's mechanical check on one step. Returns (state, evidence) with state in
    auto_fail (definite defect in a structured plan), fires (the check matched), cannot_run (the check needs
    something the plan or the ledger does not supply) or quiet (check ran and passed, or does not apply)."""
    text, raw, census, rates = step["text"], step.get("raw"), ctx["census"], ctx["rates"]
    structured = raw is not None

    if key == "UNMEASURED_PREREQUISITE":
        if step["requires_unmeasured"]:
            return "auto_fail", "requires_unmeasured: %s" % ", ".join(step["requires_unmeasured"])
        ready = _nums(NUM_NEAR_READY, text)
        orders = _nums(NUM_ORDERS, text)
        if census:
            for n in ready:
                if n > census["ceiling_strict"]:
                    return ("auto_fail" if structured else "fires"), (
                        "%s is above the %s joint ceiling of %d (%d leads counted, pool %d)" % (
                            format(n, ","), census["pool"], census["ceiling_strict"], census["ceiling_leads"],
                            census["pool_size"]))
            for n in orders:
                if n > census["pool_size"]:
                    return ("auto_fail" if structured else "fires"), "%s orders named but pool %s holds %d" % (
                        format(n, ","), census["pool"], census["pool_size"])
            share = census["ceiling_strict"] / census["pool_size"] if census.get("pool_size") else None
            for m in RATE_TARGET.finditer(text):
                r = float(m.group(2)) if m.group(2) else float(m.group(3)) / 100
                if share is not None and r > share:
                    return ("auto_fail" if structured else "fires"), (
                        "stated %s rate %s is above pool %s's strict prerequisite share %.1f%% (%d of %d; %.1f%% "
                        "counting leads)" % (m.group(1).lower(), "%s (p50)" % m.group(2) if m.group(2) else m.group(3) + "%",
                                             census["pool"], 100 * share,
                                             census["ceiling_strict"], census["pool_size"],
                                             100 * census["ceiling_leads"] / census["pool_size"]))
            return "quiet", ""
        if ready or orders:
            return "cannot_run", "step sizes %s but no census was given (pass --pool) to compare with the joint ceiling" % (
                ", ".join(format(n, ",") for n in ready + orders))
        return "quiet", ""

    if key == "SELECTION_BIAS":
        rc = (raw or {}).get("reference_class")
        if rc:
            row = rates.get(rc)
            if measured_problem(row):
                return "quiet", ""   # an unmeasured class is INVENTED_RATE's case
            pop, pool = row.get("population"), (raw.get("pool") or (census or {}).get("pool"))
            if not pop:
                return "cannot_run", "class %s records no population, so it cannot be compared with this step's pool" % rc
            if not pool:
                return "cannot_run", "class %s was measured on %s but the step names no pool" % (rc, pop)
            if pop != pool:
                return "fires", "class %s was measured on pool %s (n=%s), this step runs on %s" % (
                    rc, pop, row.get("n_studies", "?"), pool)
            return "quiet", ""
        hit = re.search(r"\b(pilot|sample|swarm|easiest|reuse[sd]?|transfer\w*|same rate|anchor)\b", text, re.I)
        if hit and RATE_NUMBER.search(text):
            return "cannot_run", "step carries a rate over from a %r but names no reference_class, so the populations cannot be compared" % hit.group(0)
        return "quiet", ""

    if key == "INVENTED_RATE":
        m = RATE_NUMBER.search(text)
        if not m:
            return "quiet", ""
        rc = (raw or {}).get("reference_class")
        if structured:
            if rc and not measured_problem(rates.get(rc)):
                return "quiet", ""
            return "fires", "rate %r has %s" % (m.group(0).strip(), "no measured reference_class" if not rc else
                                                  "reference_class %r that is not a measured base rate" % rc)
        if any(k in text for k in rates) or re.search(r"[\w/.-]+\.(?:md|csv|json|jsonl)\b", text):
            return "quiet", ""
        return "fires", "rate %r is stated with no base-rate key or source path" % m.group(0).strip()

    if key == "COST_SHIFT":
        m = SAVING.search(text)
        if not m:
            return "quiet", ""
        if (raw or {}).get("reviewer_cost") is not None or REVIEWER_COST.search(text):
            return "quiet", ""
        return "fires", "step claims a saving (%r) and names no reviewer cost" % m.group(0)

    if key == "PROXY_UNIT":
        q = (raw or {}).get("quantity")
        if q is not None and (q not in QUANTITIES or any(w in q.lower() for w in PROXY_WORDS)):
            return "auto_fail", "quantity %r is not an allowed outcome unit" % q
        m = re.search(r"\b(payload|tokens?|bytes|packets?|certificates?|agent-?hours?)\b", text, re.I)
        if m:
            return ("auto_fail", "proxy unit %r named as a result" % m.group(0)) if structured else (
                "fires", "text match %r (prose plans are never auto_fail; register the number as a forecast)" % m.group(0))
        return "quiet", ""

    if key == "ASSUMED_INDEPENDENCE":
        gates = (raw or {}).get("requires", [])
        kw = re.search(r"\b(independent\w*|upper bound|lower bound|guarantee\w*|union|sum of)\b", text, re.I)
        if census is not None:
            if "ASSUMED_INDEPENDENCE" in census.get("flags", []) and (len(gates) >= 2 or kw):
                return "fires", "census %s: multiplying marginal rates overstates (product %.1f vs joint %d)" % (
                    census["pool"], census["product_of_marginals"], census["ceiling_strict"])
            return "quiet", ""
        if len(gates) >= 2 or kw:
            return "cannot_run", "%s, but no census was given to compare the product of marginals with the joint count" % (
                "requires %d gates (%s)" % (len(gates), ", ".join(gates)) if len(gates) >= 2 else "text says %r" % kw.group(0))
        return "quiet", ""

    if key == "ACCESS_ASSUMPTION":
        m = next((x for x in re.finditer(r"\b(fetch\w*|download\w*|crawl\w*|robots|scrap\w+|hathitrust|govinfo|archive\.org)\b|https?://",
                                         text, re.I) if not NEGATED.search(text[:x.start()])), None)
        if not m:
            return "quiet", ""
        if (raw or {}).get("access_checked"):
            return "quiet", ""
        hosts = sorted({h.lower() for h in HOST_RE.findall(text)})[:3]
        return "cannot_run", "step names %r%s; no one-request access check is recorded (no access_checked), and Llull runs offline" % (
            m.group(0), " (hosts: %s)" % ", ".join(hosts) if hosts else "")

    if key == "REVIEW_LENIENCY":
        m = re.search(r"\b(review\w*|pass rate|same model|single pass|agree\w*)\b", text, re.I)
        if not m:
            return "quiet", ""
        pm, rm = (raw or {}).get("producer_model"), (raw or {}).get("reviewer_model")
        if pm and rm:
            if _model_family(pm) == _model_family(rm) and (raw or {}).get("review_passes", 1) <= 1:
                return "fires", "producer %s and reviewer %s are one family in a single pass" % (pm, rm)
            return "quiet", ""
        return "cannot_run", "step mentions %r but names no producer_model and reviewer_model to compare" % m.group(0)

    if key == "UNCONSIDERED_ROUTE":
        m = next((x for x in re.finditer(r"\b(crawl\w*|scrap\w+|manual\w*|by hand|build a|new job|download all)\b", text, re.I)
                  if not NEGATED.search(text[:x.start()])), None)
        if m and not (raw or {}).get("routes_considered"):
            return "cannot_run", "step builds or crawls (%r); whether a zero-agent job already yields the input is not checked offline" % m.group(0)
        return "quiet", ""

    if key == "POLICY_COUNTED_UNAPPROVED":
        m = OWNER_WORDS.search(text)
        if not m:
            return "quiet", ""
        cite = (raw or {}).get("approval") if structured else (re.search(r"HANDOFF/\S+", text) or [None])[0]
        if not cite:
            return "fires", "step depends on an owner decision (%r) and cites no approval line in HANDOFF/" % m.group(0)
        return "quiet", ""

    return "quiet", ""


def run_wheel(path, census=None, max_q=12, rates=None):
    """Plan step x failure mode. A question is emitted only when the mode's mechanical check fires or cannot run on
    that step; cells where it ran and passed are counted, not asked. Questions are ranked by how often the mode
    caused a past miss (auto_fail first), and each carries the plan-specific evidence."""
    spec, steps = plan_steps(path)
    modes = load_modes()
    ctx = {"census": census, "rates": rates or {}}
    cells, quiet = [], 0
    for si, s in enumerate(steps):
        for m in modes:
            state, evidence = mode_check(m["key"], s, ctx)
            if state == "quiet":
                quiet += 1
                continue
            cells.append({"step_index": si, "step": s["step"], "mode": m["key"], "state": state, "evidence": evidence,
                          "question": m["question"], "past_misses": m["misses"]})
    order = {"auto_fail": 0, "fires": 1, "cannot_run": 1}
    cells.sort(key=lambda c: (order[c["state"]], -c["past_misses"], c["step_index"]))
    # at most 12 questions, at most 2 per mode so the wheel does not collapse onto one failure mode
    chosen, per_mode = [], {}
    for c in cells:
        if per_mode.get(c["mode"], 0) >= (2 if c["state"] != "auto_fail" else 12):
            continue
        chosen.append(c)
        per_mode[c["mode"]] = per_mode.get(c["mode"], 0) + 1
        if len(chosen) >= max_q:
            break
    return {"plan": str(path), "steps": len(steps), "cells": len(steps) * len(modes), "quiet": quiet,
            "questions": chosen, "auto_fail": sum(1 for c in chosen if c["state"] == "auto_fail"),
            "modes_raised": sorted({c["mode"] for c in chosen})}


# ---------------------------------------------------------------- Raiffa (value of information)

def _lbeta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def betabinom_pmf(x, m, a, b):
    return math.exp(math.lgamma(m + 1) - math.lgamma(x + 1) - math.lgamma(m - x + 1) + _lbeta(x + a, m - x + b) - _lbeta(a, b))


def evsi_probe(m, a, b, util):
    """Expected value of sample information for a probe of m attempts. util(q) is the net value of scaling
    when the conversion rate is q; it is linear in q, so the posterior mean is sufficient.
    Returns (prior_value, preposterior_value, evsi)."""
    q0 = a / (a + b)
    v0 = max(0.0, util(q0))
    v1 = sum(betabinom_pmf(x, m, a, b) * max(0.0, util((a + x) / (a + b + m))) for x in range(m + 1))
    return v0, v1, max(0.0, v1 - v0)


def evpi(a, b, util, grid=2000):
    """Expected value of perfect information about q ~ Beta(a, b), by midpoint integration."""
    tot = norm = 0.0
    for i in range(grid):
        q = (i + 0.5) / grid
        w = math.exp((a - 1) * math.log(q) + (b - 1) * math.log(1 - q))
        tot += w * max(0.0, util(q))
        norm += w
    return max(0.0, tot / norm - max(0.0, util(a / (a + b))))


def prior_beta(row):
    """Beta prior from a measured base rate: mean = value, strength = its denominator (2 to 50)."""
    k = min(50.0, max(2.0, float(row.get("den") or 2)))
    v = min(max(row["value"], 0.01), 0.99)
    return v * k, (1 - v) * k


def rank_actions(spec, rates, censuses):
    """spec: {'planning': {'max_cost_per_ready', 'cost_unit'}, 'actions': [...]}. Returns (ranked, unranked)."""
    lam = spec["planning"]["max_cost_per_ready"]
    ranked, unranked = [], []
    by_id = {a["id"]: a for a in spec["actions"]}

    inherited = {}   # a run with no reference_class of its own uses the class of the probe that informs it

    def rate_row(a):
        return rates.get(a.get("reference_class", "")) or inherited.get(a["id"])

    def share_info(a):
        """(share, basis). A base rate measured on random draws from pool P already contains P's gate failures, so on
        pool P the share is 1.0. The census strict share applies only when the action's pool differs from the
        population the rate was measured on (or that population was not recorded)."""
        pool, row = a.get("pool"), rate_row(a)
        pop = (row or {}).get("population")
        c, cp = censuses.get(pool), censuses.get(pop)
        if pool and pop and pop == pool:
            return 1.0, "rate measured on pool %s itself: gate failures are already inside the rate" % pool
        if c and c["pool_size"] and pop and cp and cp["pool_size"]:
            # the rate already contains its own population's gate failures: move it to the action's pool by the
            # ratio of strict shares, never above 1 (the strict gate is not a true ceiling, so it must not inflate
            # a measured rate; it may only discount it for a pool that holds its prerequisites less often)
            s_act, s_pop = c["ceiling_strict"] / c["pool_size"], cp["ceiling_strict"] / cp["pool_size"]
            if s_pop == 0:
                return None, "rate's population %s has a strict share of 0: the share ratio is undefined" % pop
            return min(1.0, s_act / s_pop), "strict share of pool %s / of the rate's population %s = %.4f / %.4f%s" % (
                pool, pop, s_act, s_pop, ", capped at 1" if s_act > s_pop else "")
        if c and c["pool_size"]:
            return c["ceiling_strict"] / c["pool_size"], "census strict share of pool %s (rate measured on %s)" % (
                pool, pop or "an unrecorded population")
        if a.get("share") is not None:
            return a["share"], "explicit share in the actions file"
        return None, "no pool census and no share"

    def share_of(a):
        return share_info(a)[0]

    def util_for(run):
        sh, rps, cpa, n = share_of(run), run["ready_per_success"], run["cost_per_attempt"], run["n_attempts"]
        return lambda q: n * (sh * rps * q - cpa / lam)

    for a in spec["actions"]:
        why = []
        tier = a.get("tier")
        if tier == "zero_agent" and a.get("measures"):
            # Design 5, rule 1: a zero-agent check that measures a missing input runs before any agent action.
            ranked.append({"id": a["id"], "tier": tier, "informs": a.get("informs"), "cost": a.get("cost", 0.0),
                           "e_ready": 0.0, "evsi": None, "evpi": None, "rank": None,
                           "note": "measures %s: runs first" % a["measures"]})
            continue
        row = rate_row(a)
        if measured_problem(row):
            why.append("reference class has no measured base rate")
        run = a if tier == "run" else by_id.get(a.get("informs", ""))
        if run is not None and not measured_problem(row):
            inherited.setdefault(run["id"], row)
        if tier in ("probe", "run", "zero_agent") and run:
            if run.get("ready_per_success") is None or not run.get("ready_per_success_source"):
                why.append("ready_per_success is unmeasured (needs a value and a source)")
            if run.get("cost_per_attempt") is None or not run.get("cost_source"):
                why.append("cost_per_attempt is unmeasured (needs a value and a source)")
            if share_of(run) is None:
                why.append("no census share for pool: %s" % share_info(run)[1])
        else:
            why.append("action has no run it informs")
        if tier != "zero_agent" and a.get("cost") is None and a.get("n_attempts") and not why:
            a["cost"] = a["n_attempts"] * a["cost_per_attempt"]
        if why:
            unranked.append({"id": a["id"], "tier": tier, "reasons": why})
            continue
        a_, b_ = prior_beta(row)
        util = util_for(run)
        sh = share_of(run)
        q0 = a_ / (a_ + b_)
        out = {"id": a["id"], "tier": tier, "informs": run["id"], "share": sh, "share_basis": share_info(run)[1]}
        if tier == "zero_agent":
            known = a.get("pool") in censuses and a.get("already_measured")
            lo, hi = a.get("share_range", [sh, sh])
            if known or lo == hi:
                evsi = 0.0
            else:
                grid = [lo + (hi - lo) * i / 20 for i in range(21)]
                u = lambda s: run["n_attempts"] * (s * run["ready_per_success"] * q0 - run["cost_per_attempt"] / lam)
                evsi = max(0.0, sum(max(0.0, u(s)) for s in grid) / len(grid) - max(0.0, sum(u(s) for s in grid) / len(grid)))
            out.update(cost=a.get("cost", 0.0), e_ready=0.0, evsi=evsi, evpi=None,
                       rank=evsi / max(a.get("cost", 0.0), 0.01), note="zero-agent check: runs first")
        elif tier == "probe":
            m = a["n_attempts"]
            v0, v1, evsi = evsi_probe(m, a_, b_, util)
            ev = evpi(a_, b_, util)
            cost = a["cost"]
            e_ready = m * sh * run["ready_per_success"] * q0
            out.update(cost=cost, e_ready=e_ready, evsi=evsi, evpi=ev, rank=(e_ready + evsi) / cost)
            if ev < cost / lam:
                out["note"] = "skip: EVPI %.3f ready orders is worth less than the probe's cost" % ev
        else:
            cost = a["cost"]
            e_ready = a["n_attempts"] * sh * run["ready_per_success"] * q0
            out.update(cost=cost, e_ready=e_ready, evsi=0.0, evpi=None, rank=e_ready / cost)
        ranked.append(out)
    tier_order = {"zero_agent": 0, "probe": 1, "run": 2}
    ranked.sort(key=lambda r: (tier_order.get(r["tier"], 3), 0 if r["rank"] is None else 1, -(r["rank"] or 0)))
    return ranked, unranked


# ---------------------------------------------------------------- commands

def get_pools(a, L):
    return load_pools(a.pools if getattr(a, "pools", None) else L.pools)


def cmd_census(a, L):
    D = Data()
    pools = get_pools(a, L)
    reqs = [x for x in a.requires.split(",") if x] if a.requires else None
    if a.list:
        for k, v in list(POOL_DEFS.items()) + sorted(pools.items()):
            print("pool %-8s %s | default requires: %s%s" % (k, v.get("describe") or v.get("title"),
                  ",".join(v["default_requires"]), "" if k in POOL_DEFS else "  [custom]"))
        for k, (d, _) in GATES.items():
            print("gate %-24s %s" % (k, d))
        return 0
    c = run_census(a.pool, reqs, D, pools=pools)
    print(census_table(c))
    if a.record:
        c["census_id"] = new_id("D", read_jsonl(L.censuses), "census_id")
        c["written_by"] = WRITTEN_BY
        append_jsonl(L.censuses, c)
        print("recorded", c["census_id"])
    if a.json:
        print(json.dumps(c, indent=1))
    return 0


def find_census(L, a):
    if a.census_id:
        rec = latest(read_jsonl(L.censuses), "census_id").get(a.census_id)
        if not rec:
            raise Refusal("no census %s in %s" % (a.census_id, L.censuses))
        return rec
    if a.pool:
        c = run_census(a.pool, [x for x in a.requires.split(",") if x] if a.requires else None, pools=get_pools(a, L))
        c["census_id"] = new_id("D", read_jsonl(L.censuses), "census_id")
        c["written_by"] = WRITTEN_BY
        append_jsonl(L.censuses, c)
        print("census", c["census_id"], "%s ceiling strict %d of %d, leads %d" % (
            c["pool"], c["ceiling_strict"], c["pool_size"], c["ceiling_leads"]))
        return c
    return None


def cmd_forecast(a, L):
    rates = load_base_rates(L.base_rates)
    census = find_census(L, a)
    agent, _, model = a.planner.partition(":")
    spec = {"quantity": a.quantity, "kind": "binary" if a.event else "interval", "p10": a.p10, "p50": a.p50,
            "p90": a.p90, "event": a.event, "prob": a.prob, "reference_class": a.reference_class,
            "reason": a.reason, "deviation": a.deviation, "unlock_p90": a.unlock_p90}
    rec, flags = validate_forecast(spec, rates, census)
    for d in a.run_dir or []:
        if git("ls-files", "--", d):
            raise Refusal("run directory %s already holds committed files: forecasts must be registered before the run" % d)
    if census is None and QUANTITIES[a.quantity][1] and rec["kind"] == "interval":
        flags.append("NO_CENSUS_CAP")
    if flags and not a.accept_flag:
        print("FLAGS: " + ", ".join(flags) + (" | census %s: strict %d of %d, leads %d" % (
            census["census_id"], census["ceiling_strict"], census["pool_size"], census["ceiling_leads"]) if census else ""))
        print("not registered. Lower the forecast to the ceiling, or re-run with --accept-flag 'reason' to register it flagged.")
        return 3
    lines = read_jsonl(L.forecasts)
    rec.update({"schema": "llull.forecast/1", "forecast_id": new_id("L", lines, "forecast_id"), "rev": 1,
                "plan_id": a.plan_id, "planner": {"agent": agent, "model": model or "unknown"},
                "registered_at": now(), "registered_commit": head(), "written_by": WRITTEN_BY,
                "census_id": census.get("census_id") if census else None,
                "census_ceiling": ({k: census[k] for k in ("pool", "pool_size", "ceiling_strict", "ceiling_leads")}
                                   if census else None),
                "unlock_p90": a.unlock_p90 or 0.0, "flags": flags,
                "accepted_flag_reason": a.accept_flag if flags else None,
                "run_dirs": a.run_dir or [], "resolution": {"file": a.resolve_file, "field": a.resolve_field, "by": a.resolve_by}})
    msg = privacy_problem(json.dumps(rec))
    if msg:
        raise Refusal("privacy: " + msg, 3)
    append_jsonl(L.forecasts, rec)
    print("registered", rec["forecast_id"], "flags: %s" % (", ".join(flags) or "none"))
    if rec.get("shrunk_p50_from_all_misses") is not None:
        print("note: no measured class for this quantity; the measured median miss ratio (%.3f) would put p50 at %g"
              % (rates[CLASS_FALLBACK]["value"], rec["shrunk_p50_from_all_misses"]))
    return 0


def cmd_outcome(a, L):
    fc = latest(read_jsonl(L.forecasts), "forecast_id").get(a.forecast)
    if not fc:
        raise Refusal("unknown forecast %s" % a.forecast)
    if any(o["forecast_id"] == a.forecast for o in read_jsonl(L.outcomes)):
        raise Refusal("%s already has an outcome (outcomes are append-only, one per forecast)" % a.forecast)
    err = repo_path_ok(a.source)
    if err:
        raise Refusal(err)
    if fc["kind"] == "binary" and a.measured not in (0, 1):
        raise Refusal("a binary forecast resolves to 0 or 1")
    rec = {"schema": "llull.outcome/1", "outcome_id": new_id("O", read_jsonl(L.outcomes), "outcome_id"),
           "forecast_id": a.forecast, "rev": 1, "measured": a.measured, "source": a.source, "note": a.note or "",
           "recorded_at": now(), "recorded_commit": head(), "written_by": WRITTEN_BY}
    cap = fc.get("census_ceiling")
    kind = QUANTITIES[fc["quantity"]][1]
    if cap and kind:
        lim = cap["ceiling_strict"] / (cap["pool_size"] or 1) if kind == "share" else cap["ceiling_strict"]
        if a.measured > lim + fc.get("unlock_p90", 0) + 1e-12:
            rec["ceiling_violated"] = True
            print("WARNING: measured %g exceeds the census ceiling %g: a gate missed a route, review it" % (a.measured, lim))
    append_jsonl(L.outcomes, rec)
    print("recorded", rec["outcome_id"], "for", a.forecast)
    return 0


def first_commit(*args):
    return (git("log", "--reverse", "--format=%H", *args) or "").split("\n")[0]


def registration_status(f, L):
    """Can git prove the forecast was committed strictly before its run directories? Returns
    (status, reason): 'preregistered', 'not_preregistered' (committed together with, or after, the run) or
    'unchecked' (no run directory declared, or the lines are not committed yet)."""
    runs = f.get("run_dirs") or []
    try:
        rel = str(L.forecasts.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return "unchecked", "ledger is outside the repository"
    fc_commit = first_commit("-S", f["forecast_id"], "--", rel) if (runs or L.outcomes.exists()) else ""
    if fc_commit:
        # the file that resolves the forecast first appeared in the very commit that registered it
        for o in read_jsonl(L.outcomes):
            if o["forecast_id"] == f["forecast_id"] and first_commit("--", o.get("source", "")) == fc_commit:
                return "not_preregistered", "its outcome source %s was first committed together with the forecast (%s)" % (
                    o["source"], fc_commit[:9])
    if not runs:
        return "unchecked", "no run directory declared"
    if not fc_commit:
        return "unchecked", "forecast line not committed yet (cannot yet prove it precedes the run)"
    for d in runs:
        run_commit = first_commit("--", d)
        if run_commit and (run_commit == fc_commit or git("merge-base", "--is-ancestor", fc_commit, run_commit) is None):
            return "not_preregistered", "run artifacts in %s were committed %s the forecast (%s)" % (
                d, "together with" if run_commit == fc_commit else "before", fc_commit[:9])
    return "preregistered", "forecast committed at %s, before the run" % fc_commit[:9]


def not_preregistered_ids(L, fcs):
    """Forecast ids excluded from calibration: marked in registration.jsonl, or provably not first by git order."""
    out = {m["forecast_id"]: m.get("reason", "marked") for m in read_jsonl(L.registration)
           if m.get("status") == "not_preregistered"}
    for fid, f in fcs.items():
        if fid not in out:
            st, why = registration_status(f, L)
            if st == "not_preregistered":
                out[fid] = why
    return out


def score_all(L):
    fcs = latest(read_jsonl(L.forecasts), "forecast_id")
    outs = {o["forecast_id"]: o for o in read_jsonl(L.outcomes)}
    npr = not_preregistered_ids(L, {k: f for k, f in fcs.items() if k in outs})
    per = {}
    for fid, f in fcs.items():
        o = outs.get(fid)
        if not o or fid in npr:
            continue
        P = per.setdefault(planner_key(f["planner"]), {"intervals": [], "binary": []})
        if f["kind"] == "binary":
            P["binary"].append((f["prob"], o["measured"]))
        else:
            cat = QUANTITIES[f["quantity"]][0]
            y = o["measured"]
            item = {"id": fid, "score": norm_interval_score(f["p10"], f["p90"], y, cat),
                    "inside": f["p10"] <= y <= f["p90"], "log_ratio": log_ratio(y, f["p50"], cat)}
            ov = f.get("outside_view")
            if ov is not None and ov > 0:
                ref = norm_interval_score(0.1 * ov, 2 * ov, y, cat)
                item["skill_vs_outside"] = 1 - item["score"] / ref if ref > 0 else None
            P["intervals"].append(item)
    res = {"schema": "llull.calibration/1", "written_at": now(), "commit": head(), "planners": {},
           "n_forecasts": len(fcs), "n_resolved": len(outs), "n_scored": len(outs) - len(npr),
           "not_preregistered_excluded": npr}
    for pk, P in sorted(per.items()):
        e = {"n_interval": len(P["intervals"]), "n_binary": len(P["binary"])}
        if P["intervals"]:
            iv = P["intervals"]
            lr = sorted(i["log_ratio"] for i in iv)
            mid = len(lr) // 2
            e.update(mean_norm_interval_score=sum(i["score"] for i in iv) / len(iv),
                     coverage_p10_p90=sum(i["inside"] for i in iv) / len(iv),
                     median_log_ratio=lr[mid] if len(lr) % 2 else (lr[mid - 1] + lr[mid]) / 2)
            e["optimism_factor"] = round(math.exp(-e["median_log_ratio"]), 3)
            sk = [i["skill_vs_outside"] for i in iv if i.get("skill_vs_outside") is not None]
            if sk:
                e["mean_skill_vs_outside_view"] = sum(sk) / len(sk)
        if P["binary"]:
            ps, os_ = [p for p, _ in P["binary"]], [o for _, o in P["binary"]]
            e["brier"] = brier(ps, os_)
            e["brier_reference_base_rate"] = (sum(os_) / len(os_)) * (1 - sum(os_) / len(os_))
            if len(ps) >= 10:
                e["murphy"] = murphy(ps, os_)
        n = e["n_interval"] + e["n_binary"]
        # binaries must beat always saying 0.5 (Brier 0.25); before this check 5 wrong binaries read "calibrated"
        e["trust"] = "unproven" if n < 5 else ("calibrated" if e.get("coverage_p10_p90", 0.8) >= 0.6
                                              and abs(e.get("median_log_ratio", 0)) <= math.log(2)
                                              and e.get("brier", 0.0) < 0.25 else "miscalibrated")
        res["planners"][pk] = e
    return res


def cmd_score(a, L):
    res = score_all(L)
    L.out.mkdir(parents=True, exist_ok=True)
    (L.out / "CALIBRATION.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("forecasts %d, resolved %d, scored %d" % (res["n_forecasts"], res["n_resolved"], res["n_scored"]))
    for fid, why in sorted(res["not_preregistered_excluded"].items()):
        print("  excluded (not_preregistered) %s: %s" % (fid, why))
    for pk, e in res["planners"].items():
        bits = ["n=%d" % (e["n_interval"] + e["n_binary"]), "trust=%s" % e["trust"]]
        if "coverage_p10_p90" in e:
            bits += ["coverage=%.2f" % e["coverage_p10_p90"], "optimism x%.2f" % e["optimism_factor"]]
        if "brier" in e:
            bits.append("Brier=%.3f (base-rate ref %.3f)" % (e["brier"], e["brier_reference_base_rate"]))
        print(" ", pk, " ".join(bits))
    if not res["planners"]:
        print("  no resolved forecasts yet: Llull is unproven")
    return 0


FLAGS_PREDICTING_A_MISS = ("CEILING_EXCEEDED", "CEILING_EXCEEDED_EVEN_COUNTING_LEADS")


def is_miss(f, o):
    """Interval: measured outside [p10, p90]. Binary: the planner expected the event (p >= 0.5) and it did not happen."""
    if f["kind"] == "interval":
        return not (f["p10"] <= o["measured"] <= f["p90"])
    return f["prob"] >= 0.5 and o["measured"] == 0


def selfscore_all(L, rule_commit, is_after=None):
    """Juvenal (part): of the resolved misses, how many did Llull flag in advance? Only forecasts registered strictly
    after the rule's commit count; earlier ones were written knowing the outcome or the rule's own data (in-sample)."""
    if is_after is None:
        full = lambda c: git("rev-parse", "--verify", "--quiet", "%s^{commit}" % c) if c else None
        rc_full = full(rule_commit)
        # registered_commit is stored short and rule_commit full: compare resolved hashes, so a forecast registered AT
        # the rule commit is in-sample, not counted as a strict descendant
        is_after = lambda c: bool(rc_full) and bool(full(c)) and full(c) != rc_full and \
            git("merge-base", "--is-ancestor", rc_full, full(c)) is not None
    fcs = latest(read_jsonl(L.forecasts), "forecast_id")
    outs = {o["forecast_id"]: o for o in read_jsonl(L.outcomes)}
    npr = not_preregistered_ids(L, {k: f for k, f in fcs.items() if k in outs})
    res = {"schema": "llull.selfscore/1", "written_at": now(), "commit": head(), "rule_commit": rule_commit,
           "definition": "miss = measured outside the 80% interval (interval) or event expected at p >= 0.5 and not "
                         "happening (binary); flagged = CEILING_EXCEEDED at registration; out-of-sample = registered_commit "
                         "is a strict descendant of rule_commit and the forecast is not not_preregistered",
           "n_resolved": len(outs), "n_not_preregistered": len(npr), "n_in_sample": 0, "n_out_of_sample": 0,
           "misses_out_of_sample": [], "misses_in_sample": []}
    flagged_oos = flagged_hit = 0
    for fid, o in sorted(outs.items()):
        f = fcs.get(fid)
        if f is None or fid in npr:
            continue
        miss = is_miss(f, o)
        flagged = any(x in FLAGS_PREDICTING_A_MISS for x in f.get("flags", []))
        if not is_after(f.get("registered_commit")):
            res["n_in_sample"] += 1
            if miss:
                res["misses_in_sample"].append({"forecast_id": fid, "flagged": flagged})
            continue
        res["n_out_of_sample"] += 1
        flagged_oos += flagged
        flagged_hit += flagged and miss
        if miss:
            res["misses_out_of_sample"].append({"forecast_id": fid, "flagged": flagged})
    n = len(res["misses_out_of_sample"])
    k = sum(1 for m in res["misses_out_of_sample"] if m["flagged"])
    res.update(n_misses_out_of_sample=n, n_flagged_misses=k, share_flagged=(k / n if n else None),
               n_flagged_out_of_sample=flagged_oos, precision=(flagged_hit / flagged_oos if flagged_oos else None),
               trust="unproven" if n < 5 else "measured")
    return res


def cmd_selfscore(a, L):
    rc = a.rule_commit or first_commit("-S", "CEILING_EXCEEDED", "--", "jobs/llull/llull.py")
    if not rc:
        raise Refusal("cannot find the commit that introduced the flag rule (give --rule-commit)")
    res = selfscore_all(L, rc)
    L.out.mkdir(parents=True, exist_ok=True)
    (L.out / "SELFSCORE.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print("rule commit %s; resolved %d (not_preregistered %d, in-sample %d, out-of-sample %d)" % (
        rc[:9], res["n_resolved"], res["n_not_preregistered"], res["n_in_sample"], res["n_out_of_sample"]))
    n = res["n_misses_out_of_sample"]
    if n:
        print("out-of-sample misses %d, flagged in advance %d = %.0f%%; flags that were right %s (trust: %s)" % (
            n, res["n_flagged_misses"], 100 * res["share_flagged"],
            "-" if res["precision"] is None else "%.0f%%" % (100 * res["precision"]), res["trust"]))
    else:
        print("no resolved out-of-sample misses yet: Llull's flag recall is unproven (in-sample misses %d are not counted)"
              % len(res["misses_in_sample"]))
    return 0


def cmd_premortem(a, L):
    census = None
    if a.pool:
        census = run_census(a.pool, [x for x in a.requires.split(",") if x] if a.requires else None,
                            pools=get_pools(a, L))
    w = run_wheel(a.plan, census, a.max, load_base_rates(L.base_rates) if L.base_rates.exists() else {})
    print("Llull wheel for %s: %d steps x %d modes = %d cells; %d checks passed quietly; showing %d question(s) (auto_fail %d)" % (
        a.plan, w["steps"], len(load_modes()), w["cells"], w["quiet"], len(w["questions"]), w["auto_fail"]))
    if w["questions"]:
        print("Frame: it is two weeks later and this step returned 1/28 of its forecast. Why?")
    else:
        print("No mechanical check fired or was unable to run on this plan: no questions. That is not proof it will succeed.")
    for i, c in enumerate(w["questions"], 1):
        print("%2d. [%s] %s (%d of 12 past misses) / step: %s" % (i, c["state"], c["mode"], c["past_misses"], c["step"]))
        print("    %s" % c["question"])
        print("    evidence: %s" % c["evidence"])
    if census:
        print(census_table(census))
    if a.json:
        print(json.dumps(w, indent=1))
    return 0


def cmd_rank(a, L):
    spec = json.loads(Path(a.actions).read_text())
    rates = load_base_rates(L.base_rates)
    censuses = {}
    pools = get_pools(a, L)
    # census the action pools and the populations their rates were measured on (for the share ratio)
    need = {x.get("pool") for x in spec["actions"] if x.get("pool")}
    need |= {(rates.get(x.get("reference_class", "")) or {}).get("population") for x in spec["actions"]}
    for p in sorted(x for x in need if x):
        censuses[p] = run_census(p, pools=pools)
    ranked, unranked = rank_actions(spec, rates, censuses)
    unit = spec["planning"].get("cost_unit", "usd")
    print("Raiffa ranking (cost unit: %s; max cost per ready order %s is a PLANNING parameter, not measured)" % (
        unit, spec["planning"]["max_cost_per_ready"]))
    for r in ranked:
        g = lambda v: "-" if v is None else "%.3g" % v
        print("  %-10s %-34s cost %-8s E_ready %-7s EVSI %-7s rank %-7s %s" % (
            r["tier"], r["id"], g(r["cost"]), g(r["e_ready"]), g(r["evsi"]), g(r["rank"]), r.get("note", "")))
        if r.get("share_basis"):
            print("             share %s: %s" % (g(r.get("share")), r["share_basis"]))
    for u in unranked:
        print("  UNRANKED %-34s %s" % (u["id"], "; ".join(u["reasons"])))
    L.out.mkdir(parents=True, exist_ok=True)
    (L.out / "RANK.json").write_text(json.dumps({"written_at": now(), "commit": head(), "planning": spec["planning"],
                                                  "ranked": ranked, "unranked": unranked,
                                                  "censuses": {k: {x: v[x] for x in ("pool_size", "ceiling_strict", "ceiling_leads")}
                                                               for k, v in censuses.items()}}, indent=1) + "\n")
    return 0


OUTCOME_ID_RE = re.compile(r"^O-\d{8}-\d+$")


def outcome_rate_problems(k, r, L):
    """A base-rate row sourced from a Llull outcome must equal that outcome's measured value, for the same quantity."""
    o = next((x for x in read_jsonl(L.outcomes) if x["outcome_id"] == r["source"]), None)
    if o is None:
        return ["base rate %s: source outcome %s is not in outcomes.jsonl" % (k, r["source"])]
    out = []
    if abs(o["measured"] - r["value"]) > 0.0006:
        out.append("base rate %s: value %g but outcome %s measured %g" % (k, r["value"], o["outcome_id"], o["measured"]))
    fc = latest(read_jsonl(L.forecasts), "forecast_id").get(o["forecast_id"])
    if fc is None or fc["quantity"] != class_quantity(k):
        out.append("base rate %s: outcome %s measures %s, not %s" % (
            k, o["outcome_id"], fc and fc["quantity"], class_quantity(k)))
    return out


def run_check(L, marks=None):
    """Returns (errors, warnings). `marks`, if a list, receives one dict per forecast that git cannot prove was
    registered before its run (not_preregistered): these are excluded from scoring, not errors."""
    errs, warns = [], []
    pools_known = set(POOL_DEFS)
    try:
        pools_known |= set(load_pools(L.pools))
    except (Refusal, ValueError) as e:
        errs.append("pools file unreadable: %s" % e)
    # base rates: measured with sources, consistent with the postmortems
    try:
        rates = load_base_rates(L.base_rates)
    except Exception as e:
        return ["base_rates.json unreadable: %s" % e], warns
    pm_ids = set()
    if L.postmortems.exists():
        pm_ids = {p["id"] for p in json.loads(L.postmortems.read_text())["plans"]}
    for k, r in rates.items():
        why = measured_problem(r)
        if why:
            errs.append("base rate %s is unmeasured: %s" % (k, why))
            continue
        if r.get("population") and r["population"] not in pools_known:
            errs.append("base rate %s: population %r is not a known pool" % (k, r["population"]))
        if OUTCOME_ID_RE.match(str(r["source"])):
            errs += outcome_rate_problems(k, r, L)   # source = a Llull outcome id: no postmortem, no quoted file
            continue
        if repo_path_ok(r["source"]):
            errs.append("base rate %s: %s" % (k, repo_path_ok(r["source"])))
        for pid in str(r.get("postmortem_id", "")).split(","):
            if pm_ids and pid not in pm_ids:
                errs.append("base rate %s cites unknown postmortem %s" % (k, pid))
        errs += evidence_problems(k, r, L)
    fcs_all = read_jsonl(L.forecasts)
    ids = [f["forecast_id"] for f in fcs_all if f.get("rev", 1) == 1]
    if len(ids) != len(set(ids)):
        errs.append("duplicate forecast ids")
    fcs = latest(fcs_all, "forecast_id")
    for fid, f in fcs.items():
        q = f.get("quantity")
        if q not in QUANTITIES or any(w in str(q).lower() for w in PROXY_WORDS):
            errs.append("%s: quantity %r is not an allowed unit" % (fid, q))
        if f.get("kind") == "interval" and not (f["p10"] <= f["p50"] <= f["p90"]):
            errs.append("%s: interval not ordered" % fid)
        if f.get("kind") == "binary" and not 0 <= f.get("prob", -1) <= 1:
            errs.append("%s: probability out of range" % fid)
        rc = f.get("reference_class", "")
        if not rc.startswith("new:") and measured_problem(rates.get(rc)):
            errs.append("%s: reference class %r is not a measured base rate" % (fid, rc))
        if f.get("flags") and not f.get("accepted_flag_reason"):
            errs.append("%s: flags without an accepted reason" % fid)
        msg = privacy_problem(json.dumps(f))
        if msg:
            errs.append("%s: privacy: %s" % (fid, msg))
        # registered before any run artifact (git order). Failing the order marks the entry not_preregistered
        # (excluded from calibration scoring); it is not a ledger error, since the lines cannot be rewritten.
        st, why = registration_status(f, L)
        if st == "not_preregistered":
            if marks is not None:
                marks.append({"forecast_id": fid, "reason": why})
        elif st == "unchecked" and f.get("run_dirs") and "not committed" in why:
            warns.append("%s: %s" % (fid, why))
    seen = set()
    for o in read_jsonl(L.outcomes):
        if o["forecast_id"] not in fcs:
            errs.append("outcome %s resolves an unknown forecast" % o["outcome_id"])
        if o["forecast_id"] in seen:
            errs.append("two outcomes for %s" % o["forecast_id"])
        seen.add(o["forecast_id"])
        e = repo_path_ok(o.get("source", ""))
        if e:
            errs.append("outcome %s: %s" % (o["outcome_id"], e))
    # Llull writes only under its own directory: nothing else in the repo may carry its marks
    return errs, warns


def _squash(t):
    return re.sub(r"\s+", "", t)


def evidence_problems(k, r, L):
    """Traceability: every row quotes its measurement verbatim (whitespace ignored) from a repository file.
    The all-misses fallback is instead recomputed from postmortems.json."""
    if k == CLASS_FALLBACK:
        if not L.postmortems.exists():
            return ["base rate %s: postmortems.json missing, cannot recompute" % k]
        pm = {p["id"]: p for p in json.loads(L.postmortems.read_text())["plans"]}
        ratios = sorted(pm[p]["miss_ratio"] for p in str(r.get("postmortem_id", "")).split(",")
                        if p in pm and pm[p].get("miss_ratio") is not None)
        if not ratios:
            return ["base rate %s: no miss ratios to recompute" % k]
        m = len(ratios) // 2
        med = ratios[m] if len(ratios) % 2 else (ratios[m - 1] + ratios[m]) / 2
        return [] if abs(med - r["value"]) < 0.0006 else ["base rate %s: value %g but the postmortem median is %g"
                                                          % (k, r["value"], med)]
    ev = r.get("evidence") or []
    if not ev:
        return ["base rate %s has no evidence quote" % k]
    out = []
    for e in ev:
        if repo_path_ok(e.get("source", "")):
            out.append("base rate %s evidence: %s" % (k, repo_path_ok(e.get("source", ""))))
        elif _squash(e.get("quote", "")) not in _squash((REPO / e["source"]).read_text(errors="replace")):
            out.append("base rate %s: quote %r not found in %s" % (k, e.get("quote", "")[:60], e["source"]))
    return out


def cmd_check(a, L):
    marks = []
    errs, warns = run_check(L, marks)
    for w in warns:
        print("warn:", w)
    for e in errs:
        print("FAIL:", e)
    done = {m["forecast_id"] for m in read_jsonl(L.registration) if m.get("status") == "not_preregistered"}
    for m in marks:
        print("not_preregistered: %s: %s; excluded from calibration scoring%s" % (
            m["forecast_id"], m["reason"], "" if m["forecast_id"] not in done else " (marked)"))
        if a.mark and not errs and m["forecast_id"] not in done:
            append_jsonl(L.registration, {"schema": "llull.registration/1", "forecast_id": m["forecast_id"],
                                          "status": "not_preregistered", "reason": m["reason"],
                                          "marked_at": now(), "marked_commit": head(), "written_by": WRITTEN_BY})
            print("marked", m["forecast_id"], "in", L.registration.name)
    if errs:
        return 4
    print("llull check ok (%d warnings, %d not_preregistered)" % (len(warns), len(marks)))
    return 0


def cmd_baserate(a, L):
    o = next((x for x in read_jsonl(L.outcomes) if x["outcome_id"] == a.outcome), None)
    if o is None:
        raise Refusal("no outcome %s in %s" % (a.outcome, L.outcomes))
    fc = latest(read_jsonl(L.forecasts), "forecast_id")[o["forecast_id"]]
    q = class_quantity(a.key)
    if q not in QUANTITIES or q != fc["quantity"]:
        raise Refusal("key %r must start with the outcome's quantity %r" % (a.key, fc["quantity"]))
    if fc["kind"] == "binary":
        raise Refusal("%s is a binary forecast: its outcome is 0 or 1, not a rate. Resolve an interval forecast of the rate."
                      % fc["forecast_id"])
    cat, v = QUANTITIES[q][0], o["measured"]
    if cat == "rate" and not 0.0 <= v <= 1.0:
        raise Refusal("a rate must lie in [0, 1], outcome measured %g" % v)
    if (a.num is None) != (a.den is None) or (a.den is not None and (a.den <= 0 or abs(a.num / a.den - v) > 0.0006)):
        raise Refusal("--num/--den must be given together and equal the measured value %g" % v)
    if a.population not in POOL_DEFS and a.population not in get_pools(a, L):
        raise Refusal("population %r is not a known pool (Y1, Y2, X1 or the pools file)" % a.population)
    d = json.loads(L.base_rates.read_text())
    if any(r["key"] == a.key for r in d["rows"]):
        raise Refusal("base rate %s already exists (rows are measurements; add a new key for a new measurement)" % a.key)
    row = {"key": a.key, "pool": a.pool_desc, "unit": "share" if cat == "rate" else cat, "value": v,
           "source": o["outcome_id"], "population": a.population, "n_studies": a.n_studies,
           "derived_from": {"outcome_id": o["outcome_id"], "forecast_id": fc["forecast_id"], "outcome_source": o["source"]},
           "note": a.note}
    if a.den is not None:
        row.update(num=a.num, den=a.den)
    msg = privacy_problem(json.dumps(row))
    if msg:
        raise Refusal("privacy: " + msg, 3)
    d["rows"].append(row)
    L.base_rates.write_text(json.dumps(d, indent=1) + "\n")
    print("added base rate %s = %g (source %s, population %s)" % (a.key, v, o["outcome_id"], a.population))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="llull.py", description=__doc__.split("\n")[0])
    p.add_argument("--ledger", default=str(ROOT / "ledger"), help="ledger directory (default jobs/llull/ledger)")
    p.add_argument("--pools", help="pools file (default <ledger>/pools.json): custom census pools")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("forecast", help="register a forecast before the run")
    f.add_argument("--plan-id", required=True)
    f.add_argument("--planner", required=True, help="agent[:model], e.g. claude:claude-sonnet-5-5")
    f.add_argument("--quantity", required=True)
    f.add_argument("--p10", type=float); f.add_argument("--p50", type=float); f.add_argument("--p90", type=float)
    f.add_argument("--event"); f.add_argument("--prob", type=float)
    f.add_argument("--reference-class", required=True)
    f.add_argument("--reason"); f.add_argument("--deviation")
    f.add_argument("--pool", help="compute the Domesday census for this pool now and cap the forecast by it")
    f.add_argument("--requires"); f.add_argument("--census-id")
    f.add_argument("--unlock-p90", type=float, default=0.0, help="p90 of a registered step that creates the missing input")
    f.add_argument("--run-dir", action="append", help="directory the plan will write its run artifacts to")
    f.add_argument("--accept-flag", help="register a flagged forecast anyway; the reason stays on the record")
    f.add_argument("--resolve-file"); f.add_argument("--resolve-field"); f.add_argument("--resolve-by")
    o = sub.add_parser("outcome", help="record the measured value of a forecast")
    o.add_argument("--forecast", required=True); o.add_argument("--measured", type=float, required=True)
    o.add_argument("--source", required=True, help="repository-relative committed file holding the measurement")
    o.add_argument("--note")
    sub.add_parser("score", help="Brier / interval score / coverage per planner")
    c = sub.add_parser("census", help="Domesday prerequisite census for a pool")
    c.add_argument("--pool", help="Y1, Y2, X1 or a pool defined in the pools file"); c.add_argument("--requires")
    c.add_argument("--record", action="store_true"); c.add_argument("--json", action="store_true")
    c.add_argument("--list", action="store_true")
    m = sub.add_parser("premortem", help="question wheel for a plan file (.json spec, .md or .txt)")
    m.add_argument("plan"); m.add_argument("--pool"); m.add_argument("--requires")
    m.add_argument("--max", type=int, default=12); m.add_argument("--json", action="store_true")
    r = sub.add_parser("rank", help="value-of-information ranking of candidate actions")
    r.add_argument("--actions", required=True)
    b = sub.add_parser("baserate", help="make a base-rate row from a resolved Llull outcome (source = outcome id)")
    b.add_argument("--outcome", required=True); b.add_argument("--key", required=True)
    b.add_argument("--population", required=True, help="the pool the rate was measured on (random draws)")
    b.add_argument("--pool-desc", required=True); b.add_argument("--num", type=int); b.add_argument("--den", type=int)
    b.add_argument("--n-studies", type=int, default=1); b.add_argument("--note", default="")
    ss = sub.add_parser("selfscore", help="share of resolved misses flagged in advance (out-of-sample only)")
    ss.add_argument("--rule-commit", help="commit that introduced the flag rule (default: first commit with CEILING_EXCEEDED)")
    ck = sub.add_parser("check", help="validate the ledger")
    ck.add_argument("--mark", action="store_true", help="append not_preregistered marks to ledger/registration.jsonl")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    L = Ledger(a.ledger)
    try:
        if a.cmd == "census" and not a.list and not a.pool:
            raise Refusal("census needs --pool (or --list)")
        return {"forecast": cmd_forecast, "outcome": cmd_outcome, "score": cmd_score, "census": cmd_census,
                "premortem": cmd_premortem, "rank": cmd_rank, "check": cmd_check,
                "baserate": cmd_baserate, "selfscore": cmd_selfscore}[a.cmd](a, L)
    except Refusal as e:
        print("refused:", e, file=sys.stderr)
        return e.code
    except FileNotFoundError as e:
        print("refused: input data not found (%s)" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
