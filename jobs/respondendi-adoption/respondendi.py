"""Respondendi: adopt undecided-route status proposals under one standing owner rule.

Named for the ius publice respondendi, by which Augustus let vetted jurists give opinions that carried standing
authority, so that each answer did not need the emperor. Here the owner approves one rule (RULE.md) once; a
proposal that meets every condition of that exact rule is adopted without a per-order owner decision.

What it replaces: the hand route of D-20261108-haloander-adopt and D-20261110-papinian-adopt (adoption rows, a
pinned accepted_additions entry in jobs/claim-kit/population_contract.json, the reviewed claims filed canonically,
byte-identical to the reviewed REPLACEMENT_PROPOSAL.jsonl lines).

The route is plan -> audit -> adopt. `plan` qualifies every proposal line of the named completions against the
rule, keeps only members of the rule's lot, fixes the process stratum and draws the audit sample (every member while
the stratum is on probation). Auditors of another model family, or people, record their findings; a disagreement
goes to adjudication and only a confirmed error counts. `adopt` writes nothing until every sampled member is
audited, and adopts only members whose audit agreed (or whose disagreement was adjudicated as the auditor's error).

Refusals: no recorded owner decision cites the SHA-256 of RULE.md (a committed owner-ruling file under
research/readiness/owner_rulings/ and a committed Kean decision must both carry `respondendi-rule-sha256:<sha>`);
the rule is suspended; the stratum is stopped by confirmed errors; audit debt; size and cadence limits; and, per
order, any failed condition. Nothing here certifies anything: AI review is never human certification.

    python -I jobs/respondendi-adoption/respondendi.py rule-sha
    python -I jobs/respondendi-adoption/respondendi.py check --completion WAVE/u01/completion/complete-v1 --admission WAVE/u01/packet/ADMISSION.json
    python -I jobs/respondendi-adoption/respondendi.py plan --lot NAME --completion ... --admission ... --prompt PROMPT.txt ... [--write]
    python -I jobs/respondendi-adoption/respondendi.py audit-queue
    python -I jobs/respondendi-adoption/respondendi.py audit-record --lot NAME --order EO:N ... [--write]
    python -I jobs/respondendi-adoption/respondendi.py adjudicate --lot NAME --order EO:N ... [--write]
    python -I jobs/respondendi-adoption/respondendi.py adopt --lot NAME [--write]
    python -I jobs/respondendi-adoption/respondendi.py reverse --lot NAME --order EO:N --reason TEXT [--write]
    python -I jobs/respondendi-adoption/respondendi.py status | report [--write] | verify
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TOOL = "jobs/respondendi-adoption"
RULE = TOOL + "/RULE.md"
CHECKLIST = TOOL + "/UNDECIDED_CHECKLIST.md"
REGISTER = TOOL + "/register"
LOTS = "research/respondendi/lots"
REPORT = "research/respondendi/REPORT.md"
CLAIMS = "research/readiness/claims"
LEDGER = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
CONTRACT = "jobs/claim-kit/population_contract.json"
DECISIONS = "jobs/kean/register/decisions.jsonl"
HOLDS = "research/readiness/SOURCE_AUDIT_HOLDS.jsonl"
RULINGS = "research/readiness/owner_rulings/"
KIT_PROCESS_FILES = ("jobs/claim-kit/status_overlay.py", "jobs/claim-kit/completion.py",
                     "jobs/claim-kit/assemble.py", "jobs/claim-kit/batch.py")
KIT_OVERLAY = "jobs/claim-kit/status_overlay.py"
MAIN = "refs/remotes/origin/main"
APPROVE = "respondendi-rule-sha256:"
SUSPEND = "respondendi-suspend-sha256:"
RESUME = "respondendi-resume:"
LOT_SCHEMA = "eo-respondendi-lot/v1"
PLAN_SCHEMA = "eo-respondendi-plan/v1"
LOT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{2,60}\Z")
ROW_FIELDS = [
    "instrument_id", "provisional_substantive_status", "decision_origin", "opus_any_effect_status",
    "opus_source_text_obtained", "opus_footprint_complete_claim", "opus_first_cause_status",
    "opus_original_images_in_supplied_zip", "stage16_structured_episode_count",
    "stage16_scoped_first_cause_proven_count", "stage17_provision_count", "stage17_transition_count",
    "stage17_scoped_first_sunset_count", "recorded_legal_event_count", "stage17_assessment",
    "stage16_v3_assessment", "whole_order_first_cessation_verified_by_this_audit",
    "human_certified_by_this_release", "audit_next_step"]
NEED = {"rule_id", "allowed_actions", "statuses_allowed", "min_blind_arms", "min_controls", "claims_per_control",
        "control_kinds", "status_control_kinds", "min_control_kinds", "kinds", "text_bases", "cutoff",
        "bound_target", "audit_rate_steady",
        "min_audits_steady", "stop_confirmed_errors_in_59", "stop_bound", "stop_bound_after_audits",
        "max_unadjudicated_days", "max_plan_age_days", "max_completion_age_days", "max_lot_orders",
        "max_orders_per_week", "max_lots_per_day",
        "status_only_allowed_gate_errors", "status_only_required_checker_steps"}


class Refused(Exception):
    """A rule condition is not met; nothing was written."""


# ---------------------------------------------------------------------------------------------------- basics

def sha(data):
    return hashlib.sha256(data).hexdigest()


def canon(value):
    """The claim kit's canonical claim hash (assemble.canonical_sha for non-dossier values)."""
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8"))


def path_in(repo, rel):
    if not isinstance(rel, str) or not rel or rel.startswith(("/", "\\")) or ":" in rel:
        raise Refused(f"unsafe or missing repository path: {rel!r}")
    root = Path(repo).resolve()
    full = (root / rel).resolve()
    if not full.is_relative_to(root) or full == root:
        raise Refused(f"path escapes repository: {rel}")
    return full


def rel_of(repo, path):
    return Path(path).resolve().relative_to(Path(repo).resolve()).as_posix()


def read_json(repo, rel):
    full = path_in(repo, rel)
    if not full.is_file():
        raise Refused(f"missing file: {rel}")
    try:
        return json.loads(full.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise Refused(f"unreadable JSON {rel}: {exc}")


def read_jsonl(repo, rel):
    full = path_in(repo, rel)
    if not full.is_file():
        return []
    return [json.loads(line) for line in full.read_text(encoding="utf-8").splitlines() if line.strip()]


def pin(repo, rel):
    return {"path": rel, "sha256": sha(path_in(repo, rel).read_bytes())}


def pinned(repo, ref):
    """Bytes of a {path, sha256} reference; Refused if missing or changed."""
    full = path_in(repo, ref.get("path"))
    if not full.is_file():
        raise Refused(f"pinned file missing: {ref.get('path')}")
    data = full.read_bytes()
    if sha(data) != ref.get("sha256"):
        raise Refused(f"pinned file changed: {ref.get('path')}")
    return data


def today():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


ALLOW_DATES = False                                             # set only by the test suite, in-process


def clock(date=None):
    """Dates come from the system clock. The command line takes no date; only the test suite may pass one."""
    if date and date != today() and not ALLOW_DATES:
        raise Refused("dates come from the clock")
    return date or today()


def number(iid):
    match = re.search(r"(\d+)", iid or "")
    return (int(match.group(1)) if match else 0, iid or "")


def days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


# ---------------------------------------------------------------------------------------------------- the rule

def rule_bytes(repo):
    full = path_in(repo, RULE)
    if not full.is_file():
        raise Refused(f"rule file missing: {RULE}")
    return full.read_bytes()


def rule_sha(repo):
    """Hash of RULE.md with line endings normalized, so a Windows checkout gives the same hash."""
    return sha(rule_bytes(repo).replace(b"\r\n", b"\n"))


def parameters(repo):
    text = rule_bytes(repo).decode("utf-8").replace("\r\n", "\n")
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.S)
    if len(blocks) != 1:
        raise Refused("RULE.md must hold exactly one ```json parameter block")
    params = json.loads(blocks[0])
    missing = sorted(NEED - set(params))
    if missing:
        raise Refused("RULE.md parameters missing: " + ", ".join(missing))
    if (not set(params["statuses_allowed"]) <= {"yes", "no"} or params["min_blind_arms"] < 2
            or not set(params["status_control_kinds"]) <= set(params["control_kinds"])):
        raise Refused("RULE.md parameters out of range")
    for kid, kind in params["kinds"].items():
        if kind.get("status") not in params["statuses_allowed"] or not set(kind.get("required_control_kinds", [])) <= set(params["control_kinds"]):
            raise Refused(f"RULE.md kind {kid}: status or control kinds out of range")
        if set(kind.get("overrides", {})) - OVERRIDABLE:
            raise Refused(f"RULE.md kind {kid}: only {sorted(OVERRIDABLE)} may be overridden per kind")
    return params


OVERRIDABLE = {"bound_target", "stop_confirmed_errors_in_59", "stop_bound", "stop_bound_after_audits",
               "audit_rate_steady", "min_audits_steady"}


def effective(params, kind_id):
    """The rule's parameters with one kind's stricter overrides applied."""
    return dict(params, **params["kinds"].get(kind_id, {}).get("overrides", {}))


def decisions(repo):
    """Latest revision of each Kean decision, plus every revision."""
    latest, every = {}, []
    for record in read_jsonl(repo, DECISIONS):
        every.append(record)
        current = latest.get(record.get("id"))
        if current is None or record.get("rev", 0) >= current.get("rev", 0):
            latest[record.get("id")] = record
    return latest, every


def git_main(repo, rel):
    """The bytes of rel on origin/main, or None. Approvals count only once they are on main (an owner merge)."""
    out = subprocess.run(["git", "-C", str(repo), "show", f"{MAIN}:{rel}"], capture_output=True)
    return out.stdout if out.returncode == 0 else None


VERBS = {APPROVE: "approves", SUSPEND: "suspends", RESUME: "resumes"}


def owner_decision(repo, token):
    """The owner decision carrying token on origin/main, with its owner-ruling file; None if absent.

    Polarity is anchored: the Kean decision's ruling must begin with "Owner <verb> <token>" and the owner-ruling file
    under research/readiness/owner_rulings/, listed in its sources, must hold that exact line. Both are read from
    origin/main, so an unmerged branch, a working-tree edit or a declining text that merely cites the hash counts
    for nothing. The working copy of the ruling must equal main's (it is pinned).
    """
    prefix = next(v for k, v in VERBS.items() if token.startswith(k))
    phrase = f"Owner {prefix} {token}"
    raw = git_main(repo, DECISIONS)
    if raw is None:
        return None
    latest = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("rev", 0) >= latest.get(record.get("id"), {}).get("rev", -1):
            latest[record.get("id")] = record
    for record in latest.values():
        ruling = str(record.get("ruling", "")).strip()
        # Approval and resume must be the exact phrase: a conditional or partial approval is not an approval (amend
        # the rule instead). A suspension counts on any mention of its token, so natural wording fails closed.
        if not (ruling == phrase or (prefix == "suspends" and token in ruling)):
            continue
        for source in record.get("sources") or []:
            if not isinstance(source, str) or not source.startswith(RULINGS):
                continue
            main = git_main(repo, source)
            full = path_in(repo, source)
            lines = [l.strip() for l in (main or b"").decode("utf-8", errors="replace").splitlines()]
            if (main is not None and (phrase in lines or (prefix == "suspends" and any(token in l for l in lines)))
                    and full.is_file() and full.read_bytes() == main):
                return {"decision": record.get("id"), "ruling": pin(repo, source)}
    return None


def resume_points(repo, key, limit):
    """Audit counts at which the owner resumed a stopped kind key (tokens respondendi-resume:<key>@<n>); a count
    beyond the findings that existed cannot be honoured, so an inflated token resumes nothing."""
    raw = git_main(repo, DECISIONS) or b""
    points = set()
    for match in re.finditer(r"Owner resumes " + re.escape(RESUME + key) + r"@(\d+)", raw.decode("utf-8", errors="replace")):
        n = int(match.group(1))
        if n <= limit and owner_decision(repo, f"{RESUME}{key}@{n}"):
            points.add(n)
    return sorted(points)


def main_commit(repo):
    """origin/main as fetched, and only if it equals GitHub's main now (a hand-moved ref or a stale fetch refuses)."""
    local = subprocess.run(["git", "-C", str(repo), "rev-parse", MAIN], capture_output=True, text=True)
    remote = subprocess.run(["git", "-C", str(repo), "ls-remote", "origin", "refs/heads/main"], capture_output=True, text=True)
    here = local.stdout.strip() if local.returncode == 0 else None
    there = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout.split() else None
    if not here or here != there:
        raise Refused("origin/main here is not GitHub's main now (fetch, or the ref was moved by hand); adopt nothing")
    return here


def authorization(repo):
    digest = rule_sha(repo)
    commit = main_commit(repo)
    suspended = owner_decision(repo, SUSPEND + digest)
    if suspended:
        raise Refused(f"standing rule suspended by owner decision {suspended['decision']}")
    found = owner_decision(repo, APPROVE + digest)
    if not found:
        raise Refused(f"no owner decision on origin/main approves RULE.md (sha256 {digest}); the rule is a draft "
                      f"(see the Respondendi owner ask in HANDOFF/KEAN_ASKS.md). Adopt nothing.")
    return dict(found, rule_sha256=digest, main_commit=commit)


def ulpian_state(repo, kind):
    """The owner-approved Ulpian bound rule on GitHub's main, and its class table; (row index, reason or None)."""
    rule = kind["owner_rule"]
    token = rule["token"] + rule["sha256"]
    body = git_main(repo, rule["path"])
    if body is None or sha(body.replace(b"\r\n", b"\n")) != rule["sha256"]:
        return {}, f"{rule['path']} on main is not the approved text (sha256 {rule['sha256'][:12]}...)"
    raw = git_main(repo, DECISIONS) or b""
    latest = {}
    for line in raw.decode("utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("id") == rule["decision"] and record.get("rev", 0) >= latest.get("rev", -1):
            latest = record
    ruling = str(latest.get("ruling", "")).strip()
    sources = [x for x in latest.get("sources") or [] if isinstance(x, str) and x.startswith(RULINGS)]
    if not (ruling.startswith("Approve") and token in ruling and any(token in (git_main(repo, x) or b"").decode("utf-8", errors="replace")
                                                                     for x in sources)):
        return {}, f"no owner approval on main: {rule['decision']} citing {rule['token']}{rule['sha256'][:12]}..."
    table = git_main(repo, rule["class"])
    if table is None:
        return {}, f"{rule['class']} is not on main"
    rows = {r.get("instrument_id"): r for r in csv.DictReader(io.StringIO(table.decode("utf-8-sig"), newline=""))}
    return rows, None


def routes_on_main(repo):
    """Routes the merged claim kit declares live: UNDECIDED_ROUTES in status_overlay.py on origin/main."""
    raw = git_main(repo, KIT_OVERLAY)
    match = re.search(r"^UNDECIDED_ROUTES\s*=\s*frozenset\(\s*(\{[^}]*\})\s*\)", (raw or b"").decode("utf-8", errors="replace"), re.M)
    if not match:
        return frozenset()
    import ast
    try:
        return frozenset(ast.literal_eval(match.group(1)))
    except (ValueError, SyntaxError):
        return frozenset()


_KIT = {}


def kit_matches_main(repo):
    """The claim-kit files whose gates Respondendi relies on must be byte-identical to origin/main's."""
    for rel in (KIT_OVERLAY,) + KIT_PROCESS_FILES:
        full = path_in(repo, rel)
        main = git_main(repo, rel)
        if (main is None) != (not full.is_file()) or (main is not None and full.read_bytes() != main):
            raise Refused(f"{rel} differs from origin/main; run Respondendi on main's claim kit")


def kit_checks(repo, decision, review, evidence):
    """The claim kit's own gates on the pinned bundle: evidence seal, producer decision, independent review."""
    if "module" not in _KIT:
        kit = str(HERE.parent / "claim-kit")
        sys.path.insert(0, kit)
        try:
            spec = importlib.util.spec_from_file_location("respondendi_status_overlay", HERE.parent / "claim-kit" / "status_overlay.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:                                    # noqa: BLE001 - any import failure refuses
            raise Refused(f"claim-kit validation unavailable in this checkout: {exc}")
        finally:
            sys.path.remove(kit)
        _KIT["module"] = module
    so = _KIT["module"]
    errors = []
    try:
        so._sealed(evidence, so.EVIDENCE_SCHEMA)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    errors += so._decision_errors(decision, evidence)
    errors += so._review_errors(review, decision, evidence)
    return errors


# ---------------------------------------------------------------------------------------------------- population

def kit_population():
    path = HERE.parent / "claim-kit" / "population.py"
    spec = importlib.util.spec_from_file_location("respondendi_population", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def population(repo, contract_text=None):
    contract = json.loads(contract_text if contract_text is not None
                          else path_in(repo, CONTRACT).read_text(encoding="utf-8"))
    try:
        return kit_population().validate_inputs(repo, contract=contract)
    except (ValueError, OSError) as exc:
        raise Refused(f"population contract invalid: {exc}")


def census_ids(repo):
    contract = json.loads(path_in(repo, CONTRACT).read_text(encoding="utf-8"))
    census = contract["census"]
    rows = csv.DictReader(io.StringIO(path_in(repo, census["path"]).read_text(encoding="utf-8-sig"), newline=""))
    return {(r.get("id") or r.get("instrument_id")) for r in rows if r.get("included_in_bibliography", "1") == "1"}


# ---------------------------------------------------------------------------------------------------- register

def register(repo, name):
    return read_jsonl(repo, f"{REGISTER}/{name}.jsonl")


def plans(repo):
    root = path_in(repo, LOTS)
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("*/PLAN.json"))] if root.is_dir() else []


def lots(repo):
    return register(repo, "LOTS")


def upper_bound(errors, n, confidence=0.95):
    """One-sided Clopper-Pearson upper bound on an error rate from n audits with `errors` confirmed errors."""
    if n <= 0 or errors >= n:
        return 1.0
    alpha = 1 - confidence

    def cdf(p):
        return sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(errors + 1))
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def audits_needed(errors, target):
    """Audits that bring the 95% upper bound to target with this many confirmed errors (59 for 0 at 5%)."""
    n = errors + 1
    while upper_bound(errors, n) > target:
        n += 1
    return n


def findings(repo):
    """Every audit with its adjudication folded in: finding is agree, confirmed_error, auditor_wrong or open."""
    adj = {(a["lot"], a["instrument_id"]): a for a in register(repo, "ADJUDICATIONS")}
    out = []
    for audit in register(repo, "AUDITS"):
        key = (audit["lot"], audit["instrument_id"])
        if audit["verdict"] == "agree":
            finding = "agree"
        elif key in adj:
            finding = adj[key]["finding"]
        else:
            finding = "open"
        out.append(dict(audit, finding=finding, adjudication=adj.get(key)))
    return out


def counted(repo):
    """Findings that count toward a bound: a confirmed error always (and every reversal); an agreeing audit only when
    it was in its plan's sample and its lot was adopted. Audits of abandoned plans add no clean record."""
    adopted = {l["lot"] for l in lots(repo)}
    out = [f for f in findings(repo) if f["finding"] == "confirmed_error"
           or (f["finding"] in ("agree", "auditor_wrong") and f.get("in_sample") and f["lot"] in adopted)]
    for r in register(repo, "REVERSALS"):
        if r.get("stratum"):
            out.append({"lot": r["lot"], "instrument_id": r["instrument_id"], "stratum": r["stratum"],
                        "finding": "confirmed_error", "reversal": True, "date": r.get("date")})
    return [f for _, f in sorted(enumerate(out), key=lambda x: (str(x[1].get("date") or ""), x[0]))]


def on_record_errors(repo):
    """Orders with a confirmed error or a reversal on record: never again by the standing rule."""
    return ({f["instrument_id"] for f in findings(repo) if f["finding"] == "confirmed_error"}
            | {r["instrument_id"] for r in register(repo, "REVERSALS")})


def stratum_kind(stratum):
    """A stratum is '<process fingerprint>:<kind>:<text basis>:<tier>'."""
    parts = str(stratum).split(":")
    return parts[1] if len(parts) == 4 else None


def kind_key(stratum):
    parts = str(stratum).split(":")
    return ":".join(parts[1:]) if len(parts) == 4 else str(stratum)


def stratum_state(repo, stratum, params):
    """Probation is per stratum (a new process starts a fresh audit plan); the stop rule is per kind key (kind, text
    basis, tier) across processes, so changing a prompt cannot escape a stop, and it counts only errors after the
    owner's latest resume point."""
    params = effective(params, stratum_kind(stratum))
    rows = counted(repo)
    mine = [f for f in rows if f.get("stratum") == stratum]
    errors = sum(f["finding"] == "confirmed_error" for f in mine)
    needed = audits_needed(errors, params["bound_target"])
    key = kind_key(stratum)
    same = [f for f in rows if kind_key(f.get("stratum")) == key]
    points = resume_points(repo, key, len(same))
    after = same[points[-1]:] if points else same
    errs = sum(f["finding"] == "confirmed_error" for f in after)
    stopped = None
    if sum(f["finding"] == "confirmed_error" for f in after[-59:]) >= params["stop_confirmed_errors_in_59"]:
        stopped = f"{params['stop_confirmed_errors_in_59']} or more confirmed errors in the last 59 audits of {key}"
    elif len(after) >= params["stop_bound_after_audits"] and upper_bound(errs, len(after)) > params["stop_bound"]:
        stopped = f"audit-based upper bound above {params['stop_bound']:.0%} for {key}"
    open_ = sum(1 for f in findings(repo) if f.get("stratum") == stratum and f["finding"] == "open")
    return {"stratum": stratum, "audits": len(mine), "open": open_, "confirmed_errors": errors,
            "audits_needed": needed, "probation": len(mine) < needed or params.get("audit_rate_steady", 0) >= 1,
            "upper_95": round(upper_bound(errors, len(mine)), 4) if mine else None, "stopped": stopped,
            "resume_token": f"{RESUME}{key}@{len(same)}" if stopped else None}


# ---------------------------------------------------------------------------------------------------- qualification

def _arm(name):
    match = re.fullmatch(r"(BLIND_REVIEW|AFTER_REVEAL)_([A-Za-z0-9]+)\.jsonl", name)
    return (match.group(1), match.group(2)) if match else (None, None)


ABBREV = re.compile(r"\b(nos?|secs?|f\.\s?r|u\.\s?s\.\s?c|stat|ex|ord|proc|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec|e\.\s?o|p\.\s?r)\.")
LABELS = re.compile(r"^\s*([a-z ]+?)\s*(?:by)?\s*:", re.I)
YEAR = re.compile(r"\b(1[789]\d\d|20\d\d)\b")


def _norm(text):
    t = re.sub(r"[\u00ad\ufffd]", "", str(text or ""))
    t = re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1\2", t)            # rejoin words broken at line ends
    t = re.sub(r"\s+", " ", t).lower()
    return ABBREV.sub(lambda m: m.group(1).replace(".", "").replace(" ", "") + " ", t)


def _id_pattern(iid):
    """The order's full printed number: EO:341A matches 341A or 341-A, never 341 or '341 a'; EO:341 never matches 341A."""
    match = re.fullmatch(r"EO:(\d+)([A-Za-z]?)", iid or "")
    if not match:
        return None
    num, suffix = match.group(1), match.group(2).lower()
    tail = (r"-?" + suffix + r"(?![a-z\d])") if suffix else r"(?!\d)(?!-?[a-z]\b)"
    return r"(?<![\d])" + num + tail


def named_end_in(text, iid, kind):
    """Zero-token: a sentence of text introduces iid as 'Executive Order (No.) N', carries an ending verb, no
    qualifier, no partial or relational phrase in the 80 characters before the number, and no 'is amended' between
    the number and the verb; and no sentence naming the order carries a qualifier."""
    pattern = _id_pattern(iid)
    if not pattern:
        return False
    verbs = r"\b(?:" + "|".join(re.escape(v) for v in kind["ending_verbs"]) + r")\b"
    passed = False
    for sentence in re.split(r"(?<=[.;])\s+", _norm(text)):
        hits = list(re.finditer(pattern, sentence))
        if not hits:
            continue
        if any(q in sentence for q in kind["qualifiers"]):
            return False
        for m in hits:
            pre = sentence[max(0, m.start() - 120):m.start()]
            if not re.search(r"(executive orders?|ex ord|e o)\b[^;]{0,120}$", pre):
                continue
            if any(q in pre[-80:] for q in kind["pre_qualifiers"]):
                return False
            verb = re.search(verbs, sentence)
            if not verb:
                continue
            between = sentence[m.end():verb.start()] if verb.start() > m.end() else ""
            if re.search(r"\b(is|are) (hereby )?(further )?amended\b", between):
                return False
            passed = True
    return passed


def lot_check(claim, params):
    """Kept for version-1 callers: the sentence check on the claim's own ending quote."""
    kind = params["kinds"]["express_named_revocation"]
    end = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else {}
    src = end.get("source") if isinstance(end.get("source"), dict) else {}
    return [] if named_end_in(src.get("quote"), claim.get("instrument_id"), kind) else ["no unqualified named end"]


def _records(evidence):
    dossier = (evidence or {}).get("base_dossier") or {}
    records = dossier.get("evidence")
    return dossier, (records if isinstance(records, dict) else {})


def _history_texts(evidence):
    packet = (evidence or {}).get("history_packet") or {}
    return [_norm(o.get("text")) for o in packet.get("observations") or [] if isinstance(o, dict) and o.get("text")]


def _segments(history):
    """Catalog note entries ('Revoked by: EO 13241, December 18, 2001'), one per label."""
    return [seg.strip() for h in history for seg in re.split(r"\||\n|(?<=\d{4}) (?=[a-z ]+ by:)", h) if seg.strip()]


def _later_acts(history, end_date, skip=None):
    """Catalog entries that act on the order after its claimed end (an amendment, continuation, reinstatement,
    suspension or second ending after the end means the claimed end is not the whole story)."""
    year = int(end_date[:4]) if end_date else 9999
    out = []
    for seg in _segments(history):
        if seg == skip or not re.match(r"(amended|continued|reinstated|suspended|superseded|revoked|extended|nullified|rescinded|terminated|modified) by", seg):
            continue
        years = [int(y) for y in YEAR.findall(seg)]
        if years and max(years) > year:
            out.append(seg)
    return out


def text_basis(evidence, params, routes):
    """'original' when the frozen ORIGINAL is acceptable as an original; 'working' when it is a working text the rule
    allows and the merged kit declares the working_text route live (F6); None otherwise."""
    dossier, records = _records(evidence)
    original = records.get(dossier.get("original_source_id")) or {}
    if original.get("acceptable_as_original") is True:
        return "original"
    working = params["text_bases"]["working"]
    if (working["route"] in routes and original.get("working_text_basis") in working["working_text_basis"]
            and original.get("grade") in working["grades"]):
        return "working"
    return None


def _date(value):
    value = str(value or "")
    return value if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else None


def classify(repo, claim, decision, evidence, params, routes=None):
    """(kind id, text basis, reasons). The kind is fixed by the kit-emitted basis records, never by the producer's
    free-text mechanism. A kind whose route the merged kit does not declare live (UNDECIDED_ROUTES on origin/main)
    is inactive. Every predicate reads only the claim and its pinned frozen evidence."""
    routes = routes_on_main(repo) if routes is None else routes
    iid = claim.get("instrument_id") or ""
    status = claim.get("whole_order_status")
    end = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else {}
    dossier, records = _records(evidence)
    basis = [b for b in (decision or {}).get("basis_evidence_ids") or [] if b in records]
    target_signed = _date((records.get(dossier.get("original_source_id")) or {}).get("signing_date"))
    cutoff = params["cutoff"]
    history = _history_texts(evidence)
    segments = _segments(history)
    acts = {b: r for b, r in records.items() if b.startswith("ACT:")}
    actor_texts = [b for b in records if b.startswith("ACTOR_TEXT:")]
    life = params["kinds"].get("ulpian_life_bound") or {}
    if status == "yes":
        kid = "yes_current"
    elif life and end.get("mechanism") in life.get("mechanisms", []):
        kid = "ulpian_life_bound"
    elif any(b.startswith("OWN_TEXT:") for b in basis):
        kid = "spent_on_issue"
    elif any(b.startswith("TERM:") for b in basis) and end.get("actor") == iid:
        kid = "own_terms"
    elif any(b.startswith("ACT:") for b in basis):
        kid = "express_named_revocation"
    else:
        return None, None, ["no lot kind: the status basis is not an ACT, TERM, OWN_TEXT or CURRENT record"]
    kind = params["kinds"][kid]
    why = []
    if kind.get("route") and kind["route"] not in routes:
        why.append(f"lot kind {kid} is inactive until: {kind['prerequisite']}")
    date = _date(end.get("date"))
    if status == "no" and not (date and date < cutoff and target_signed and target_signed <= date):
        why.append("a NO needs a whole-order end on or after the order's signing and before the cutoff")
    if kid == "express_named_revocation":
        actor = str(end.get("actor") or "")
        good = [b for b in basis if b.startswith("ACT:") and acts[b].get("actor_id") == actor
                and acts[b].get("scope") == "whole" and acts[b].get("names_target") is True
                and not acts[b].get("reaches_target_via") and acts[b].get("verb") in kind["act_verbs"]]
        if not good:
            why.append("no whole-scope, directly naming ACT basis record from the claimed actor")
        quote = _norm((end.get("source") or {}).get("quote"))
        target = re.sub(r"\D", "", iid)
        for b in good:
            r = acts[b]
            provision = str(r.get("provision_text") or r.get("text") or "")
            if len(provision) > kind["max_provision_chars"] or not named_end_in(provision, iid, kind):
                why.append(f"the basis provision {b} is not one sentence naming the order with an unqualified end")
            if not quote or not _norm(provision) or _norm(provision)[:200] not in quote:
                why.append("the claim's ending quote must contain the basis record's provision")
            signed = _date(r.get("signing_date"))
            if not (signed and target_signed and target_signed < signed and date and signed <= date):
                why.append("the actor must be signed after the order, and the end on or after the actor's signing")
            if _date(r.get("effective_date")) and _date(r.get("effective_date")) != date:
                why.append(f"the claimed end differs from the basis record's effective date {r.get('effective_date')}")
            if r.get("exceptions_text"):
                why.append(f"the basis provision {b} carries an exception")
            flat_prov = _norm(provision)
            for phrase in r.get("savings_phrases") or []:
                flat = _norm(phrase)
                if flat and (flat[:80] in flat_prov or re.search(r"(?<!\d)" + re.escape(target) + r"(?!\d)", flat)):
                    why.append(f"the basis provision {b} carries a savings phrase")
                    break
        for b, r in acts.items():
            if r.get("actor_id") == actor and r.get("scope") == "partial":
                why.append(f"the same actor also acts on part of the order ({b})")
            if r.get("verb") in ("reinstate", "continue"):
                why.append(f"a reinstatement or continuation lead is held ({b})")
        num = re.sub(r"\D", "", actor)
        word = r"(eo|executive order)" if actor.startswith("EO:") else r"(proc|proclamation)"
        witness = re.compile(r"^(revoked|superseded|rescinded|terminated) by: ?" + word + r" ?(no )?" + num + r"\b")
        hits = [seg for seg in segments if witness.match(seg) and not re.search(r"\(|\bpart|\bsec|\bsection|in part", seg)]
        if not hits:
            why.append("no second witness: no catalog note entry names the same actor as ending the order")
        later = _later_acts(history, date, skip=hits[0] if hits else None)
        if later:
            why.append(f"a catalog entry acts on the order after the claimed end: {later[0][:120]}")
        if any(("reinstat" in h or "revived" in h) for h in history):
            why.append("a catalog note records a reinstatement")
    elif kid == "own_terms":
        terms = [records[b] for b in basis if b.startswith("TERM:")]
        whole = {iid, iid + "#whole"}
        if not any(t.get("kind") in kind["term_kinds"] and t.get("stated_end_date") == date and t.get("scope_id") in whole
                   for t in terms):
            why.append("no whole-order TERM basis of a stated, dated kind gives the claimed end date")
        if not any(re.search(kind["term_text_pattern"], _norm(t.get("text"))) for t in terms):
            why.append("the term's text does not set an expiry for this order")
        if any(any(w in _norm(t.get("text")) for w in kind["extension_words"]) for t in terms):
            why.append("the term's text speaks of extension, renewal or a further order")
        if acts or actor_texts:
            why.append("a later instrument acts on the order; an own-terms end is outside the lot")
        if any(re.search(r"\b(eo|proc|plo):", str(m).lower()) for m in dossier.get("missing") or []):
            why.append("the dossier names a missing later instrument")
        if any(re.match(r"(amended|continued|revoked|superseded|extended|modified|suspended) by", seg) for seg in segments):
            why.append("a catalog note records a later act on the order")
        if end.get("actor") != iid:
            why.append("an own-terms end must be the order's own")
    elif kid == "spent_on_issue":
        own = [records[b] for b in basis if b.startswith("OWN_TEXT:")]
        if not any(o.get("own_text_kind") in kind["own_text_kinds"] and o.get("mechanism") == "spent_on_issue"
                   and o.get("actor_id") == iid and o.get("scope") == "whole" and str(o.get("text") or "").strip()
                   and (o.get("whole_order_test") or {}).get("continuing_sentences") == 0 for o in own):
            why.append("no whole-order OWN_TEXT basis of an allowed kind, by the order itself, with its operative text")
        if end.get("actor") != iid or end.get("mechanism") != "spent_on_issue" or not (date and date == target_signed):
            why.append("a spent-on-issue end is the order's own, on its signing date")
        if any(re.match(r"(amended|continued|revoked|superseded|extended|modified|suspended|reinstated) by", seg) for seg in segments):
            why.append("a catalog note records a later act on the order; outside the lot")
        if any(o.get("own_text_kind") == "amends_parent" for o in own):
            parents = {b for b in records if b.startswith("PARENT_END:")}
            cited = set()
            for item in claim.get("savings_residuals") or []:
                if isinstance(item, dict):
                    cited.add(str(((item.get("source") or {}) if isinstance(item.get("source"), dict) else {}).get("evidence_id")))
            if parents and not parents & cited:
                why.append("an amending order's surviving text must cite the held PARENT_END record as its source")
    elif kid == "ulpian_life_bound":
        rows, reason = ulpian_state(repo, kind)
        if reason:
            why.append(f"lot kind {kid} is inactive until: {kind['prerequisite']} ({reason})")
        row = rows.get(iid) or {}
        if not reason and not (row.get("tier") == "quoted_fact" and row.get("status") == "undecided"
                               and _date(row.get("bound")) and row["bound"] < cutoff):
            why.append("not a quoted-fact member of the approved Ulpian class with a bound before the cutoff")
        if row:
            if end.get("date_kind") != "not_later_than" or end.get("first_cause") != "unresolved" or date != row.get("bound"):
                why.append("the end must be not_later_than the Ulpian bound, with the first cause unresolved")
            src = end.get("source") if isinstance(end.get("source"), dict) else {}
            if src.get("text_path") != row.get("text_path"):
                why.append("the end must cite the held text the Ulpian class read")
            flat = json.dumps(claim, ensure_ascii=False).lower()
            if str(row.get("born_by")) not in flat or "unknown" not in flat:
                why.append("the claim must state the birth bound it rests on and that use of the permission is unknown")
    elif kid == "yes_current":
        signals = kind["ending_signals"]
        if claim.get("whole_order_end"):
            why.append("a YES claim must not assert a whole-order end")
        current = [records[b] for b in basis if b.startswith("CURRENT:")]
        if not current:
            why.append("a YES needs a CURRENT basis record")
        if (decision or {}).get("current_predicate_checked_through") != cutoff:
            why.append("the current predicate must be checked through the cutoff")
        if any(any(w in _norm(r.get("text")) for w in signals) for r in current):
            why.append("the current-status text itself carries an ending signal")
        if acts or actor_texts:
            why.append("a later instrument acts on the order; a YES is outside the lot")
        if any(b.startswith("TERM:") and r.get("kind") in kind["ending_term_kinds"] for b, r in records.items()):
            why.append("an own-terms record of an ending kind is held")
        bad = [seg for seg in segments if (LABELS.match(seg) or [None, ""])[1].strip() not in kind["allowed_labels"]]
        if bad:
            why.append(f"a catalog note entry outside the YES allow-list: {bad[0][:80]}")
        packet = (evidence or {}).get("history_packet") or {}
        dumped = _norm(json.dumps([packet.get("observations"), packet.get("events"), dossier.get("current_law_leads")],
                                  ensure_ascii=False)).replace("revokes:", "").replace("supersedes:", "")
        if any(w in dumped for w in signals):
            why.append("an observation, event or current-law lead carries an ending signal")
        if dossier.get("missing"):
            why.append("the dossier lists missing sources")
        searches = {x.get("search_id"): x for x in dossier.get("machine_searches") or [] if isinstance(x, dict)}
        for sid in kind["complete_searches"]:
            if not (searches.get(sid) or {}).get("complete"):
                why.append(f"search {sid} is not complete")
    basis_text = text_basis(evidence, params, routes)
    if basis_text is None:
        why.append("the frozen original is neither acceptable as an original nor an allowed working text"
                   f" (working texts inactive until: {params['text_bases']['working']['prerequisite']})")
    elif basis_text not in kind.get("text_bases", ["original"]):
        why.append(f"lot kind {kid} does not accept a {basis_text} text")
    return kid, basis_text, why


def qualify(repo, completion, admission_paths, params, statuses, census, adopted_ok=frozenset(), plan_date=None):
    """Check every proposal line of one kit completion against the rule.

    completion: repository path of a `kit.py complete --publish` output folder (…/completion/complete-vN).
    Returns (accepted members, refused [{instrument_id, reasons}], completion-level facts).
    A completion-level failure (tampered manifest, missed or untyped controls, exceptions) refuses every member.
    """
    comp = path_in(repo, completion)
    if not comp.is_dir():
        raise Refused(f"completion folder missing: {completion}")
    crel = rel_of(repo, comp)
    inputs = read_json(repo, crel + "/INPUTS.json")
    receipts_in = inputs.get("preserved_receipts") or {}
    # The manifest is the COMPLETION.json the completion itself pinned: beside it (claim-kit and Papinian layout) or
    # in the packet's completion/ folder (Maudslay conveyor layout). Exactly one candidate may exist.
    candidates = [k for k in receipts_in if k.endswith("/COMPLETION.json")
                  and k in (rel_of(repo, comp.parent / "COMPLETION.json"), rel_of(repo, comp.parent / "completion" / "COMPLETION.json"))]
    if len(candidates) != 1:
        raise Refused(f"{crel}: cannot tell which COMPLETION.json the completion ran with")
    manifest_rel = candidates[0]
    manifest = read_json(repo, manifest_rel)
    if receipts_in[manifest_rel] != sha(path_in(repo, manifest_rel).read_bytes()):
        raise Refused(f"{manifest_rel} differs from the manifest the completion ran with")
    pub = read_json(repo, crel + "/PUBLICATION.json")
    if pub.get("mode") != "replacement_proposal" or pub.get("written") is not True:
        raise Refused(f"{crel}: not a written replacement-proposal publication")
    if pub.get("independent_human_certifications", 0) != 0:
        raise Refused(f"{crel}: claims a human certification; Respondendi adopts AI-reviewed statuses only")
    proposal_bytes = pinned(repo, {"path": pub.get("path"), "sha256": pub.get("sha256")})
    if read_json(repo, crel + "/EXCEPTIONS.json"):
        raise Refused(f"{crel}: completion recorded exceptions")
    tally = read_json(repo, crel + "/TALLY.json")
    finished = _date(str(tally.get("finished_utc") or "")[:10])
    if not finished or days(finished, plan_date or today()) > params["max_completion_age_days"]:
        raise Refused(f"{crel}: completion older than {params['max_completion_age_days']} days or undated; complete again")
    checker = read_json(repo, crel + "/TRACKER_CHECKER.json").get("by_instrument", {})
    routes = routes_on_main(repo)
    kit_matches_main(repo)
    adm = []
    for path in admission_paths:
        record = read_json(repo, path)
        if record.get("schema") == "eo-claim-kit-admission/v1" and record.get("bentham_action") in params["allowed_actions"]:
            adm.append((path, set(record.get("instrument_ids") or [])))

    blind, after, receipt_pins = {}, {}, []
    for ref in manifest.get("receipts") or []:
        pinned(repo, ref)
        receipt_pins.append({"path": ref["path"], "sha256": ref["sha256"]})
        kind, arm = _arm(Path(ref["path"]).name)
        if kind is None:
            continue
        target = blind if kind == "BLIND_REVIEW" else after
        target.setdefault(arm, {})
        for record in read_jsonl(repo, ref["path"]):
            target[arm][record.get("claim_sha256")] = record
    if len(blind) < params["min_blind_arms"]:
        raise Refused(f"{crel}: {len(blind)} blind arms; the rule needs {params['min_blind_arms']}")
    reviewers = {arm: {r.get("reviewer") for r in recs.values()} for arm, recs in blind.items()}
    names = [n for group in reviewers.values() for n in group]
    if len(names) != len(set(names)) or None in names or any(len(g) != 1 for g in reviewers.values()):
        raise Refused(f"{crel}: each arm must be one named reviewer, different from every other arm")
    arm_names = set(names)
    families = sorted({str(r.get("model_family") or "unrecorded") for recs in blind.values() for r in recs.values()}
                      | {str(manifest.get("producer_model_family") or "unrecorded")})

    controls = manifest.get("controls") or []
    set_size = len(next(iter(blind.values())))
    needed = max(params["min_controls"], math.ceil(set_size / params["claims_per_control"]))
    if len(controls) < needed:
        raise Refused(f"{crel}: {len(controls)} planted controls for a review set of {set_size}; the rule needs {needed}")
    control_ids, control_pins, kinds, control_kind_of = set(), [], set(), {}
    for control in controls:
        for arm, recs in blind.items():
            record = recs.get(control.get("planted_claim_sha256"))
            if not record or record.get("verdict") != "rejected":
                raise Refused(f"{crel}: arm {arm} did not reject planted control {control.get('instrument_id')}")
        control_ids.add(control.get("instrument_id"))
        adjudication = None
        for key in ("seed", "adjudication"):
            if control.get(key):
                data = pinned(repo, control[key])
                control_pins.append(control[key])
                if key == "adjudication":
                    adjudication = json.loads(data.decode("utf-8"))
        kind = (adjudication or {}).get("control_kind")
        control_kind_of[control.get("instrument_id")] = kind
        if kind not in params["control_kinds"]:
            raise Refused(f"{crel}: control {control.get('instrument_id')} has no control_kind from the rule's catalogue")
        kinds.add(kind)
    if len(kinds) < params["min_control_kinds"] or not kinds & set(params["status_control_kinds"]):
        raise Refused(f"{crel}: controls must be of at least {params['min_control_kinds']} kinds, one of them "
                      f"status-determining ({params['status_control_kinds']}); found {sorted(kinds)}")
    if any(c.get("caught") is not True for c in tally.get("controls") or []):
        raise Refused(f"{crel}: the kit's tally records a missed control")

    members = {m.get("instrument_id"): m for m in manifest.get("members") or []}
    outcomes = {o.get("instrument_id"): o for o in tally.get("outcomes") or []}
    control_kinds_by_lot = {}
    for line in proposal_bytes.split(b"\n"):
        if not line.strip():
            continue
        genuine = json.loads(line.decode("utf-8"))
        cid = genuine.get("instrument_id")
        if cid not in control_ids:
            continue
        try:
            bundle_c = (members.get(cid) or {}).get("overlay_bundle") or {}
            lk, _, _ = classify(repo, genuine, json.loads(pinned(repo, bundle_c["decision"]).decode("utf-8")),
                                json.loads(pinned(repo, bundle_c["evidence"]).decode("utf-8")), params, routes)
        except (KeyError, Refused, ValueError):
            continue
        control_kinds_by_lot.setdefault(lk, set()).add(control_kind_of[cid])
    base_pins = [pin(repo, manifest_rel)] + [pin(repo, crel + "/" + n) for n in
                                            ("PUBLICATION.json", "TALLY.json", "TRACKER_CHECKER.json", "INPUTS.json")]
    accepted, refused = [], []
    for number_, raw in enumerate(proposal_bytes.split(b"\n"), 1):
        if not raw.strip():
            continue
        claim = json.loads(raw.decode("utf-8"))
        iid, csha, why = claim.get("instrument_id"), canon(claim), []
        status = claim.get("whole_order_status")
        member = members.get(iid) or {}
        outcome = outcomes.get(iid) or {}
        overlay = ((claim.get("claim_kit") or {}).get("status_overlay")) or {}
        producer = (claim.get("claim_kit") or {}).get("agent")
        kind = member.get("publication_kind") or "whole_case"
        status_only = kind == "partial_research"
        if kind not in ("whole_case", "partial_research"):
            why.append(f"publication kind {kind!r} is not one the rule adopts")
        if status not in params["statuses_allowed"]:
            why.append(f"status {status!r} is not one the rule allows ({params['statuses_allowed']})")
        if member.get("outcome") != "submit" or member.get("claim_sha256") != csha:
            why.append("not a submitted member of the completion manifest with this exact claim hash")
        if (outcome.get("outcome") != "eligible" or outcome.get("claim_sha256") != csha
                or outcome.get("source_review_upheld") is not True or (outcome.get("publication_kind") or kind) != kind):
            why.append("the kit's tally does not record this exact claim as eligible and source-upheld")
        gaps = outcome.get("gate_errors") or []
        if not status_only and gaps:
            why.append("whole-case claim with gate errors: " + ", ".join(map(str, gaps))[:300])
        if status_only:
            allowed = tuple(params.get("status_only_allowed_gate_errors") or ())
            off = [g for g in gaps if not str(g).startswith(allowed)]
            if not gaps or off:
                why.append("status-only claim: its open gaps must be clause-level only "
                           f"({list(allowed)}); found {off or 'none'}")
        for arm in sorted(blind):
            source, want = (after, "upheld_after_reveal") if iid in control_ids else (blind, "upheld")
            record = source.get(arm, {}).get(csha)
            if (not record or record.get("verdict") != want or record.get("instrument_id") != iid
                    or record.get("independent") is not True or record.get("separate_context") is not True
                    or record.get("scope", "whole_case") != kind):
                why.append(f"arm {arm} did not record verdict {want!r} on this exact claim as an independent, "
                           f"separate-context review in scope {kind}")
        bundle = member.get("overlay_bundle") or {}
        bundle_pins, files = [], None
        try:
            files = {key: json.loads(pinned(repo, bundle[key]).decode("utf-8"))
                     for key in ("evidence", "decision", "review", "proposal")}
            bundle_pins = [bundle[key] for key in ("evidence", "decision", "review", "proposal")]
        except (KeyError, Refused) as exc:
            why.append(f"overlay bundle not pinned or changed: {exc}")
        if files:
            review, decision, proposal = files["review"], files["decision"], files["proposal"]
            if (review.get("schema") != "eo-status-overlay-review/v1" or review.get("decision") != "accept"
                    or review.get("independence_confirmed") is not True or review.get("source_checks_confirmed") is not True
                    or review.get("instrument_id") != iid):
                why.append("no accepted independent status review with source checks confirmed")
            if review.get("reviewer") in arm_names or review.get("reviewer") in (None, producer):
                why.append("the status reviewer is not distinct from the producer and both lifecycle arms")
            if (decision.get("instrument_id") != iid or decision.get("approved") is not True
                    or decision.get("recommended_provisional_status") != status):
                why.append("the producer's status decision does not recommend the claimed status")
            if (proposal.get("recommended_provisional_status") != status
                    or proposal.get("decision_sha256") != overlay.get("decision_sha256")
                    or proposal.get("review_sha256") != overlay.get("review_sha256")
                    or overlay.get("decision_sha256") != canon(decision) or review.get("decision_sha256") != canon(decision)):
                why.append("the promotion proposal does not bind this claim's decision and review")
        kid, basis_text, kind_why = classify(repo, claim, (files or {}).get("decision") or {},
                                              (files or {}).get("evidence") or {}, params, routes)
        why.extend(kind_why)
        if files and not kind_why:
            why.extend("claim-kit gate: " + str(e) for e in kit_checks(repo, files["decision"], files["review"], files["evidence"]))
        kind_rule = params["kinds"].get(kid) or {}
        if status_only and not kind_rule.get("status_only", False):
            why.append(f"lot kind {kid} has no status-only tier")
        lacking = sorted(set(kind_rule.get("required_control_kinds", [])) - control_kinds_by_lot.get(kid, set()))
        anyof = set(kind_rule.get("required_control_any", []))
        if anyof and not anyof & control_kinds_by_lot.get(kid, set()):
            lacking = lacking + [" or ".join(sorted(anyof))]
        if lacking:
            why.append(f"lot kind {kid} needs controls of kind {lacking} planted on claims of that kind in the review set")
        if status_only and any(re.search(params["status_only_forbidden_gap_pattern"], _norm(g)) for g in gaps):
            why.append("a status-only gap may not concern another instrument or the status itself")
        check = checker.get(iid) or {}
        if status_only:
            steps = check.get("steps_checker_passed") or {}
            failed = [s for s in params.get("status_only_required_checker_steps") or [] if steps.get(s) is not True]
            if check.get("claim_sha256") != csha or failed:
                why.append("the claim checker did not pass the status steps of this exact claim: " + ", ".join(failed))
        elif (check.get("claim_sha256") != csha or check.get("all_checks_passed") is not True
                or check.get("gate_passed") is not True or check.get("mechanical_result") != "pass"):
            why.append("the claim checker did not pass this exact claim in the completion receipt")
        if iid not in census:
            why.append("not in the census")
        if iid in statuses and iid not in adopted_ok:
            why.append("already has a provisional status; Respondendi never changes a decided status")
        admitted = [path for path, ids in adm if iid in ids]
        if not admitted:
            why.append(f"no admission receipt places it in a Bentham action of {params['allowed_actions']}")
        if why:
            refused.append({"instrument_id": iid, "claim_sha256": csha, "reasons": why})
            continue
        accepted.append({
            "instrument_id": iid, "status": status, "claim_sha256": csha,
            "kind": "status_only" if status_only else "whole_case", "open_gaps": list(gaps),
            "lot_kind": kid, "text_basis": basis_text,
            "proposal": {"path": pub["path"], "sha256": pub["sha256"], "line": number_},
            "claim_line": raw.decode("utf-8"), "producer": producer,
            "status_reviewer": files["review"].get("reviewer"), "arm_reviewers": sorted(arm_names),
            "review_families": families,
            "pins": base_pins + receipt_pins + control_pins + bundle_pins + [pin(repo, p) for p in admitted]})
    return accepted, refused, {"completion": crel, "review_set": set_size, "controls": sorted(control_ids),
                               "control_kinds": sorted(kinds), "families": families}


def gather(repo, completions, admission_paths, params, adopted_ok=frozenset(), plan_date=None):
    state = population(repo)
    census = census_ids(repo)
    accepted, refused, facts = [], [], []
    for completion in completions:
        ok, bad, fact = qualify(repo, completion, admission_paths, params, state["statuses"], census, adopted_ok, plan_date)
        accepted.extend(ok)
        refused.extend(bad)
        facts.append(fact)
    ids = [m["instrument_id"] for m in accepted]
    if len(ids) != len(set(ids)):
        raise Refused("the same order qualifies in two completions; adopt each order once")
    accepted.sort(key=lambda m: number(m["instrument_id"]))
    return accepted, refused, facts, state


def stratum_of(repo, params, prompts, families):
    """Process fingerprint: a change of prompt, checklist, kit code, rule or model family is a new process; each
    member's stratum adds its lot kind, text basis and tier (see member_stratum)."""
    if not prompts:
        raise Refused("name the producer and reviewer prompt files (--prompt); they define the process stratum")
    return canon({"rule_id": params["rule_id"], "families": sorted(families),
                  "prompts": sorted(sha(path_in(repo, p).read_bytes()) for p in prompts),
                  "checklist": sha(path_in(repo, CHECKLIST).read_bytes()) if path_in(repo, CHECKLIST).is_file() else None,
                  "kit": {p: sha(path_in(repo, p).read_bytes()) for p in KIT_PROCESS_FILES if path_in(repo, p).is_file()}})[:16]


def member_stratum(process, member):
    return f"{process}:{member['lot_kind']}:{member['text_basis']}:{member['kind']}"


# ---------------------------------------------------------------------------------------------------- writing

def row_for(member, lot, decision):
    row = dict.fromkeys(ROW_FIELDS, "")
    row.update({
        "instrument_id": member["instrument_id"],
        "provisional_substantive_status": member["status"],
        "decision_origin": (f"respondendi:{lot}:reviewed_claim {member['claim_sha256'][:16]} (standing owner rule "
                            f"{decision}; status review + two-arm blind AI review + "
                            + ("cross-family audit" if member.get("audited") else "sampled cross-family audit")
                            + ("; status only, lifecycle claim not filed" if member.get("kind") == "status_only" else "")
                            + f"; {LOTS}/{lot}/LOT.json)"),
        "opus_any_effect_status": "not_recorded_in_opus_overlay",
        "opus_source_text_obtained": "not_applicable", "opus_footprint_complete_claim": "not_applicable",
        "opus_first_cause_status": "not_applicable", "opus_original_images_in_supplied_zip": "not_applicable",
        "stage16_structured_episode_count": "0", "stage16_scoped_first_cause_proven_count": "0",
        "stage17_provision_count": "0", "stage17_transition_count": "0", "stage17_scoped_first_sunset_count": "0",
        "recorded_legal_event_count": "0",
        "whole_order_first_cessation_verified_by_this_audit": "no", "human_certified_by_this_release": "no",
        "audit_next_step": (f"AI-reviewed claim status adopted as provisional under standing owner rule {decision} "
                            "(reversible); independent human review")})
    return row


def csv_text(rows, header=True):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=ROW_FIELDS, lineterminator="\n")
    if header:
        writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def entry_text(entry):
    return "\n".join("    " + line for line in json.dumps(entry, indent=2, ensure_ascii=False).splitlines())


def insert_entry(contract_text, entry):
    marker, empty = "\n  ]\n}", '"accepted_additions": []'
    at = contract_text.rstrip().rfind(marker)
    if not json.loads(contract_text)["accepted_additions"] and contract_text.count(empty) == 1:
        text = contract_text.replace(empty, '"accepted_additions": [\n' + entry_text(entry) + "\n  ]")
    elif at < 0:
        raise Refused("population_contract.json layout not recognized; add the entry by hand")
    else:
        text = contract_text[:at] + ",\n" + entry_text(entry) + contract_text[at:]
    if json.loads(text)["accepted_additions"][-1] != entry:
        raise Refused("population_contract.json: the new entry did not land in accepted_additions")
    return text


def replace_entry(contract_text, old, new):
    before = entry_text(old)
    if contract_text.count(before) != 1:
        raise Refused("population_contract.json: the lot's entry was reformatted; reverse by hand")
    text = contract_text.replace(before, entry_text(new))
    if new not in json.loads(text)["accepted_additions"]:
        raise Refused("population_contract.json: replacement failed")
    return text


class Transaction:
    """Write files together; restore every original byte if validation fails."""

    def __init__(self, repo):
        self.repo, self.saved, self.writes = Path(repo), {}, {}

    def put(self, rel, data):
        full = path_in(self.repo, rel)
        if rel not in self.saved:
            self.saved[rel] = full.read_bytes() if full.exists() else None
        self.writes[rel] = data

    def append(self, rel, data):
        full = path_in(self.repo, rel)
        current = self.writes.get(rel, full.read_bytes() if full.exists() else b"")
        if current and not current.endswith(b"\n"):
            current += b"\n"
        self.put(rel, current + data)

    def text(self, rel):
        if rel in self.writes:
            return self.writes[rel].decode("utf-8")
        return path_in(self.repo, rel).read_text(encoding="utf-8")

    def commit(self, check):
        for rel, data in self.writes.items():
            full = path_in(self.repo, rel)
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(data)
        try:
            check()
        except Exception:
            self.rollback()
            raise

    def rollback(self):
        for rel, data in self.saved.items():
            full = path_in(self.repo, rel)
            if data is None:
                if full.exists():
                    full.unlink()
            else:
                full.write_bytes(data)


def jline(value):
    return (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")


def jfile(value):
    return (json.dumps(value, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------------------- plan

def plan(repo, lot, completions, admission_paths, prompts, date=None, write=False):
    repo = Path(repo).resolve()
    date = clock(date)
    if not LOT_NAME.fullmatch(lot or ""):
        raise Refused("lot name: lowercase letters, digits and hyphens, 3-61 characters")
    if path_in(repo, f"{LOTS}/{lot}").exists():
        raise Refused(f"lot {lot} already exists")
    params = parameters(repo)
    auth = authorization(repo) if write else None
    accepted, refused, facts, _ = gather(repo, completions, admission_paths, params, plan_date=date)
    families = sorted({f for fact in facts for f in fact["families"]})
    process = stratum_of(repo, params, prompts, families)
    states = {}
    for m in accepted:
        m["stratum"] = member_stratum(process, m)
        states.setdefault(m["stratum"], stratum_state(repo, m["stratum"], params))
    stopped = [m for m in accepted if states[m["stratum"]]["stopped"]]
    for m in stopped:
        refused.append({"instrument_id": m["instrument_id"], "claim_sha256": m["claim_sha256"],
                        "reasons": [f"stratum {m['stratum']} stopped: {states[m['stratum']]['stopped']}; the owner must "
                                    f"record 'Owner resumes {states[m['stratum']]['resume_token']}'"]})
    accepted = [m for m in accepted if not states[m["stratum"]]["stopped"]]
    errors_on_record = on_record_errors(repo)
    for m in [m for m in accepted if m["instrument_id"] in errors_on_record]:
        refused.append({"instrument_id": m["instrument_id"], "claim_sha256": m["claim_sha256"],
                        "reasons": ["a confirmed error or a reversal is on record for this order; a named owner decision only"]})
    accepted = [m for m in accepted if m["instrument_id"] not in errors_on_record]
    adopted_lots = {l["lot"] for l in lots(repo)}
    live = [p for p in plans(repo) if p["lot"] not in adopted_lots and p.get("rule_sha256") == rule_sha(repo)
            and days(p["date"], date) <= params["max_plan_age_days"]]
    planned = {f["instrument_id"] for p in live for f in p["members"]}
    clash = sorted(planned & {m["instrument_id"] for m in accepted})
    if clash:
        raise Refused(f"already planned in another open lot: {', '.join(clash[:10])}")
    ids = [m["instrument_id"] for m in accepted]
    core = {"schema": PLAN_SCHEMA, "lot": lot, "date": date, "rule_sha256": rule_sha(repo), "process": process,
            "completions": completions, "admissions": list(admission_paths),
            "prompts": [pin(repo, p) for p in prompts],
            "members": [{k: v for k, v in m.items() if k != "claim_line"} for m in accepted], "refused": refused}
    core_sha = canon(core)
    sample = []
    for stratum in sorted(states):
        group = sorted((m["instrument_id"] for m in accepted if m["stratum"] == stratum), key=number)
        if not group:
            continue
        if states[stratum]["probation"]:
            sample += group
        else:
            eff = effective(params, stratum_kind(stratum))
            # Each member is drawn by its own claim hash against the rate, so lot composition cannot steer it.
            score = {m["instrument_id"]: int(sha((m["claim_sha256"] + rule_sha(repo)).encode())[:12], 16) / 16 ** 12
                     for m in accepted if m["stratum"] == stratum}
            chosen = [i for i in group if score[i] < eff["audit_rate_steady"]]
            for i in sorted(group, key=lambda i: score[i]):
                if len(chosen) >= min(len(group), eff["min_audits_steady"]):
                    break
                if i not in chosen:
                    chosen.append(i)
            sample += chosen
    sample = sorted(sample, key=number)
    receipt = dict(core, core_sha256=core_sha, strata=states, audit_sample=sample)
    result = {"lot": lot, "process": process, "strata": states, "qualifying": ids, "refused": refused,
              "audit_sample": sample, "completions": facts, "written": False}
    if not write:
        try:
            result["authorization"] = authorization(repo)
        except Refused as exc:
            result["authorization"] = str(exc)
        return result
    if not accepted:
        raise Refused("no proposal meets the rule; nothing planned")
    if len(accepted) > params["max_lot_orders"]:
        raise Refused(f"{len(accepted)} qualifying orders; at most {params['max_lot_orders']} per lot (split the lot)")
    tx = Transaction(repo)
    tx.put(f"{LOTS}/{lot}/PLAN.json", jfile(dict(receipt, owner_decision=auth["decision"], main_commit=auth["main_commit"])))
    tx.commit(lambda: None)
    write_report(repo)
    result["written"] = True
    return result


def plan_of(repo, lot):
    return read_json(repo, f"{LOTS}/{lot}/PLAN.json")


# ---------------------------------------------------------------------------------------------------- audits

def _families(member):
    return {str(f).casefold() for f in member.get("review_families") or []} | {"unrecorded", "unknown", ""}


FAMILY_OF = (("claude", "anthropic"), ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"), ("o4", "openai"),
             ("codex", "openai"), ("gemini", "google"), ("grok", "xai"), ("llama", "meta"), ("mistral", "mistral"),
             ("deepseek", "deepseek"), ("qwen", "alibaba"))


def check_evidence(repo, lot, member, evidence, role, who, family, params):
    """An audit or adjudication's evidence: its own file in the lot's audit-evidence folder, never reused, naming
    the order and the exact claim; an AI's is a JSON run receipt whose model id gives the family; a person must be on
    the rule's list."""
    folder = f"{LOTS}/{lot}/audit-evidence/"
    if not evidence or not str(evidence).replace("\\", "/").startswith(folder):
        raise Refused(f"evidence must be a file under {folder}")
    data = path_in(repo, evidence).read_bytes()
    text = data.decode("utf-8", errors="replace")
    if member["instrument_id"] not in text or member["claim_sha256"] not in text:
        raise Refused("the evidence must name the order and its exact claim hash")
    digest = sha(data)
    used = {a.get("evidence", {}).get("sha256") for name in ("AUDITS", "ADJUDICATIONS") for a in register(repo, name)}
    if digest in used:
        raise Refused("this evidence file already backs another audit or adjudication")
    if role == "human":
        if who not in params["human_auditors"]:
            raise Refused(f"a person auditing must be one the rule names ({params['human_auditors']})")
        return
    try:
        model = str(json.loads(text).get("model") or "").lower()
    except ValueError:
        raise Refused("an AI audit's evidence must be a JSON run receipt with its model id")
    derived = next((fam for prefix, fam in FAMILY_OF if model.startswith(prefix)), None)
    if not derived or derived != str(family or "").casefold():
        raise Refused(f"the run receipt's model {model!r} does not show family {family!r}")


def audit_record(repo, lot, iid, auditor, role, family, verdict, status_found, basis, evidence=None,
                 date=None, write=False):
    repo = Path(repo).resolve()
    date = clock(date)
    if not evidence:
        raise Refused("pin the audit's transcript or run receipt (--evidence); an audit without evidence counts for nothing")
    receipt = plan_of(repo, lot)
    member = next((m for m in receipt["members"] if m["instrument_id"] == iid), None)
    if member is None:
        raise Refused(f"{iid} is not a member of lot {lot}")
    if role not in {"human", "independent_ai"}:
        raise Refused("role: human or independent_ai")
    if role == "independent_ai" and str(family or "").casefold() in _families(member):
        raise Refused(f"an AI auditor must name a model family different from the reviewers' {member.get('review_families')}")
    if auditor in {member.get("producer"), member.get("status_reviewer"), *member.get("arm_reviewers", [])}:
        raise Refused("the auditor must not be the producer or a reviewer of this order")
    if verdict not in {"agree", "disagree"} or status_found not in {"yes", "no", "unknown"}:
        raise Refused("verdict agree|disagree; status-found yes|no|unknown")
    if verdict == "agree" and status_found != member["status"]:
        raise Refused("an agreeing audit must find the adopted status")
    check_evidence(repo, lot, member, evidence, role, auditor, family, parameters(repo))
    if not basis or len(basis) < 40:
        raise Refused("give the audit's dated basis (at least 40 characters)")
    if any(a["lot"] == lot and a["instrument_id"] == iid for a in register(repo, "AUDITS")):
        raise Refused(f"{iid} in lot {lot} is already audited")
    record = {"schema": "eo-respondendi-audit/v1", "lot": lot, "stratum": member["stratum"], "instrument_id": iid,
              "claim_sha256": member["claim_sha256"], "planned_status": member["status"], "auditor": auditor,
              "role": role, "model_family": family, "verdict": verdict, "status_found": status_found, "basis": basis,
              "date": date, "in_sample": iid in receipt.get("audit_sample", []),
              "evidence": pin(repo, evidence),
              "notice": "An audit of a provisional status; never a human certification of the lifecycle."}
    result = {"audit": record, "written": False}
    if not write:
        return result
    tx = Transaction(repo)
    tx.append(REGISTER + "/AUDITS.jsonl", jline(record))
    tx.commit(lambda: None)
    write_report(repo)
    result["written"] = True
    if verdict == "disagree":
        result["next"] = (f"adjudicate: respondendi.py adjudicate --lot {lot} --order {iid} --adjudicator NAME "
                          "--role human|independent_ai --family F --finding confirmed_error|auditor_wrong --basis ... --write")
    return result


def adjudicate(repo, lot, iid, adjudicator, role, family, finding, basis, date=None, write=False, evidence=None):
    """Settle a disagreeing audit: a third reviewer (a person, or an AI of a family other than the auditor's)."""
    repo = Path(repo).resolve()
    date = clock(date)
    if not evidence:
        raise Refused("pin the adjudication's transcript or run receipt (--evidence)")
    audit = next((a for a in register(repo, "AUDITS") if a["lot"] == lot and a["instrument_id"] == iid), None)
    if audit is None or audit["verdict"] != "disagree":
        raise Refused(f"{iid} in lot {lot} has no disagreeing audit to adjudicate")
    if any(a["lot"] == lot and a["instrument_id"] == iid for a in register(repo, "ADJUDICATIONS")):
        raise Refused(f"{iid} in lot {lot} is already adjudicated")
    member = next(m for m in plan_of(repo, lot)["members"] if m["instrument_id"] == iid)
    if role not in {"human", "independent_ai"} or finding not in {"confirmed_error", "auditor_wrong"}:
        raise Refused("role human|independent_ai; finding confirmed_error|auditor_wrong")
    excluded = {audit["auditor"], member.get("producer"), member.get("status_reviewer"), *member.get("arm_reviewers", [])}
    if adjudicator in excluded:
        raise Refused("the adjudicator must not be the auditor, the producer or a reviewer of this order")
    if role == "independent_ai" and (str(family or "").casefold() == str(audit.get("model_family")).casefold()
                                     or str(family or "").casefold() in _families(member)):
        raise Refused("an AI adjudicator must be of a family other than the auditor's and the reviewers'")
    if not basis or len(basis) < 40:
        raise Refused("give the adjudication's basis (at least 40 characters)")
    check_evidence(repo, lot, member, evidence, role, adjudicator, family, parameters(repo))
    record = {"schema": "eo-respondendi-adjudication/v1", "lot": lot, "stratum": audit["stratum"], "instrument_id": iid,
              "adjudicator": adjudicator, "role": role, "model_family": family, "finding": finding, "basis": basis,
              "date": date, "evidence": pin(repo, evidence)}
    if not write:
        return {"adjudication": record, "written": False}
    tx = Transaction(repo)
    tx.append(REGISTER + "/ADJUDICATIONS.jsonl", jline(record))
    tx.commit(lambda: None)
    write_report(repo)
    return {"adjudication": record, "written": True}


# ---------------------------------------------------------------------------------------------------- adopt

def adopt(repo, lot, date=None, write=False):
    repo = Path(repo).resolve()
    date = clock(date)
    params = parameters(repo)
    receipt = plan_of(repo, lot)
    if any(l["lot"] == lot for l in lots(repo)):
        raise Refused(f"lot {lot} is already adopted")
    if receipt["rule_sha256"] != rule_sha(repo):
        raise Refused("RULE.md changed since the plan; plan the lot again under the current rule")
    auth = authorization(repo) if write else None
    states = {m["stratum"]: stratum_state(repo, m["stratum"], params) for m in receipt["members"]}
    by_order = {f["instrument_id"]: f for f in findings(repo) if f["lot"] == lot}
    confirmed = [i for i, f in by_order.items() if f["finding"] == "confirmed_error"]
    must = set(receipt["audit_sample"]) | ({m["instrument_id"] for m in receipt["members"]} if confirmed else set())
    missing = sorted((i for i in must if i not in by_order), key=number)
    open_ = sorted((i for i, f in by_order.items() if f["finding"] == "open"), key=number)
    ok_ids = [m["instrument_id"] for m in receipt["members"] if not states[m["stratum"]]["stopped"] and (
              m["instrument_id"] in by_order and by_order[m["instrument_id"]]["finding"] in ("agree", "auditor_wrong")
              or (m["instrument_id"] not in must and m["instrument_id"] not in by_order))]
    stopped = {s: st["stopped"] for s, st in states.items() if st["stopped"]}
    result = {"lot": lot, "strata": states, "audits_missing": missing, "open_disagreements": open_,
              "confirmed_errors": confirmed, "adoptable": ok_ids, "stopped_strata": stopped, "written": False}
    if not write:
        return result
    if missing:
        raise Refused(f"audits missing for {len(missing)} orders of lot {lot}: {', '.join(missing[:10])}")
    if open_:
        raise Refused(f"adjudicate the disagreeing audits of lot {lot} first: {', '.join(open_[:10])}")
    stale = [f for f in findings(repo) if f["finding"] == "open" and days(f["date"], date) > params["max_unadjudicated_days"]]
    if stale:
        raise Refused(f"audit debt: {len(stale)} disagreements unadjudicated for more than "
                      f"{params['max_unadjudicated_days']} days, first {stale[0]['lot']} {stale[0]['instrument_id']}")
    if days(receipt["date"], date) > params["max_plan_age_days"]:
        raise Refused(f"plan of {receipt['date']} is older than {params['max_plan_age_days']} days; plan again")
    done = lots(repo)
    if sum(1 for l in done if l["date"] == date) >= params["max_lots_per_day"]:
        raise Refused(f"cadence: {params['max_lots_per_day']} lot(s) a day; frozen evidence of packets in flight pins "
                      "the whole status ledger, so adopt once, after the day's batches complete")
    if not ok_ids:
        raise Refused("no member of the lot is adoptable" + (f"; stopped strata: {stopped}" if stopped else ""))
    week = sum(l["count"] for l in done if 0 <= days(l["date"], date) < 7)
    if week + len(ok_ids) > params["max_orders_per_week"]:
        raise Refused(f"weekly limit: {week} adopted in the last 7 days; {len(ok_ids)} more exceeds {params['max_orders_per_week']}")
    # Re-qualify from the pinned receipts: nothing the plan relied on may have changed.
    accepted, _, _, state_pop = gather(repo, receipt["completions"], receipt["admissions"], params, plan_date=receipt["date"])
    current = {m["instrument_id"]: m for m in accepted}
    members = []
    for iid in ok_ids:
        planned = next(m for m in receipt["members"] if m["instrument_id"] == iid)
        now = current.get(iid)
        if now is None or now["claim_sha256"] != planned["claim_sha256"]:
            raise Refused(f"{iid} no longer qualifies with its planned claim; plan the lot again")
        members.append(dict(now, audited=iid in by_order, stratum=planned["stratum"]))
    decision = auth["decision"]
    rows = [row_for(m, lot, decision) for m in members]
    rows_rel, lot_rel = f"{LOTS}/{lot}/ADOPTION_ROWS.csv", f"{LOTS}/{lot}/LOT.json"
    rule_rel, claims_rel = f"{LOTS}/{lot}/RULE_AT_ADOPTION.md", f"{CLAIMS}/respondendi-{lot}.jsonl"
    filed = [m for m in members if m["kind"] == "whole_case"]
    # The register files keep growing; the lot pins a frozen copy of its own audits and adjudications.
    tx = Transaction(repo)
    audits_rel = f"{LOTS}/{lot}/AUDITS.jsonl"
    own = [a for name in ("AUDITS", "ADJUDICATIONS") for a in register(repo, name) if a.get("lot") == lot]
    tx.put(audits_rel, b"".join(jline(a) for a in own))
    audit_pins = [{"path": audits_rel, "sha256": sha(tx.writes[audits_rel])}]
    core = {"schema": LOT_SCHEMA, "lot": lot, "date": date, "rule_id": params["rule_id"],
            "rule_sha256": auth["rule_sha256"], "owner_decision": decision, "owner_ruling": auth["ruling"],
            "main_commit": auth["main_commit"],
            "process": receipt["process"], "plan": pin(repo, f"{LOTS}/{lot}/PLAN.json"),
            "members": [{k: v for k, v in m.items() if k != "claim_line"} for m in members],
            "excluded": [{"instrument_id": i, "finding": by_order[i]["finding"]} for i in sorted(
                {m["instrument_id"] for m in receipt["members"]} - set(ok_ids), key=number)],
            "audits": audit_pins, "claims_file": claims_rel if filed else None, "rows_file": rows_rel,
            "independent_human_certifications": 0,
            "notice": "Provisional statuses adopted from AI review under a standing owner rule; never a human certification."}
    receipt_out = dict(core, core_sha256=canon(core))
    rows_bytes = csv_text(rows).encode("utf-8")
    tx.put(rows_rel, rows_bytes)
    tx.put(lot_rel, jfile(receipt_out))
    tx.put(rule_rel, rule_bytes(repo).replace(b"\r\n", b"\n"))
    if filed:
        tx.put(claims_rel, "".join(m["claim_line"] + "\n" for m in filed).encode("utf-8"))
    tx.append(LEDGER, csv_text(rows, header=False).encode("utf-8"))
    pins = [{"path": rule_rel, "sha256": sha(tx.writes[rule_rel])}, auth["ruling"],
            {"path": lot_rel, "sha256": sha(tx.writes[lot_rel])}, pin(repo, f"{LOTS}/{lot}/PLAN.json")] + audit_pins
    for member in members:
        for ref in member["pins"]:
            if ref["path"] not in {p["path"] for p in pins}:
                pins.append({"path": ref["path"], "sha256": ref["sha256"]})
    entry = {"name": f"Respondendi lot {lot} (standing owner rule {decision})", "count": len(members),
             "accepted_in_main": f"standing owner rule {decision} (respondendi lot {lot}; in main when this commit merges)",
             "standing_rule": {"decision": decision, "rule_sha256": auth["rule_sha256"], "lot_receipt": lot_rel},
             "rows": {"path": rows_rel, "sha256": sha(rows_bytes)}, "authorization_pins": pins}
    tx.put(CONTRACT, insert_entry(tx.text(CONTRACT), entry).encode("utf-8"))
    tx.append(REGISTER + "/LOTS.jsonl", jline(
        {"lot": lot, "date": date, "count": len(members), "process": receipt["process"],
         "kinds": dict(sorted(__import__("collections").Counter(m["lot_kind"] for m in members).items())),
         "core_sha256": receipt_out["core_sha256"],
         "rule_sha256": auth["rule_sha256"], "owner_decision": decision}))
    before = len(state_pop["statuses"])

    def check():
        if len(population(repo)["statuses"]) != before + len(members):
            raise Refused("population did not grow by exactly the adopted orders")
    tx.commit(check)
    write_report(repo)
    result.update(written=True, adopted=len(members), decided_before=before, decided_after=before + len(members),
                  owner_decision=decision)
    return result


# ---------------------------------------------------------------------------------------------------- reversal

def reverse(repo, lot, iid, reason, date=None, write=False):
    """Withdraw one adopted status: the row leaves the ledger and the lot's rows; a canonical claim stays (claim
    files are append-only) and gets an unresolved source-audit hold, so the tracker blocks it. A reversal counts as a
    confirmed error of its stratum."""
    repo = Path(repo).resolve()
    date = clock(date)
    if not reason or len(reason) < 20:
        raise Refused("give the reason for the reversal (at least 20 characters)")
    receipt = read_json(repo, f"{LOTS}/{lot}/LOT.json")
    if any(r["lot"] == lot and r["instrument_id"] == iid for r in register(repo, "REVERSALS")):
        raise Refused(f"{iid} in lot {lot} is already reversed")
    contract_text = path_in(repo, CONTRACT).read_text(encoding="utf-8")
    entry = next((e for e in json.loads(contract_text)["accepted_additions"]
                  if (e.get("standing_rule") or {}).get("lot_receipt") == f"{LOTS}/{lot}/LOT.json"), None)
    if entry is None:
        raise Refused(f"lot {lot} has no population contract entry")
    rows = list(csv.DictReader(io.StringIO(path_in(repo, entry["rows"]["path"]).read_text(encoding="utf-8"), newline="")))
    row = next((r for r in rows if r["instrument_id"] == iid), None)
    if row is None:
        raise Refused(f"{iid} is not adopted in lot {lot}")
    line = csv_text([row], header=False)
    ledger = path_in(repo, LEDGER).read_text(encoding="utf-8")
    if ledger.count(line) != 1:
        raise Refused(f"{iid}: its adoption row is not in the ledger exactly once")
    member = next(m for m in receipt["members"] if m["instrument_id"] == iid)
    n = 1
    while path_in(repo, f"{LOTS}/{lot}/ADOPTION_ROWS.r{n}.csv").exists():
        n += 1
    rows_rel = f"{LOTS}/{lot}/ADOPTION_ROWS.r{n}.csv"
    rev_rel = f"{LOTS}/{lot}/REVERSAL_{iid.replace(':', '_')}.json"
    record = {"schema": "eo-respondendi-reversal/v1", "lot": lot, "instrument_id": iid, "reason": reason,
              "date": date or today(), "removed_row": row, "claim_sha256": member["claim_sha256"],
              "kind": member["kind"], "rows_file": rows_rel,
              "effect": "status undecided again; a filed claim stays with an unresolved source-audit hold"}
    result = {"reversal": record, "written": False}
    if not write:
        return result
    tx = Transaction(repo)
    new_rows = csv_text([r for r in rows if r["instrument_id"] != iid]).encode("utf-8")
    tx.put(rows_rel, new_rows)
    tx.put(LEDGER, ledger.replace(line, "").encode("utf-8"))
    tx.put(rev_rel, jfile(record))
    if member["kind"] == "whole_case":
        tx.append(HOLDS, jline({"claim_sha256": member["claim_sha256"], "instrument_id": iid,
                                "reason": "Respondendi reversal: " + reason, "review_kind": "respondendi_reversal",
                                "review_path": rev_rel, "review_sha256": sha(tx.writes[rev_rel]),
                                "schema": "eo-source-audit-hold/v1", "state": "unresolved"}))
    new_entry = json.loads(json.dumps(entry))
    new_entry["count"] = entry["count"] - 1
    new_entry["rows"] = {"path": rows_rel, "sha256": sha(new_rows)}
    new_entry["authorization_pins"] += [entry["rows"], {"path": rev_rel, "sha256": sha(tx.writes[rev_rel])}]
    tx.put(CONTRACT, replace_entry(contract_text, entry, new_entry).encode("utf-8"))
    tx.append(REGISTER + "/REVERSALS.jsonl", jline({"lot": lot, "instrument_id": iid, "date": record["date"], "record": rev_rel,
                                                    "stratum": member.get("stratum"), "counts_as": "confirmed_error"}))
    before = len(population(repo)["statuses"])

    def check():
        if len(population(repo)["statuses"]) != before - 1:
            raise Refused("population did not shrink by exactly the reversed order")
    tx.commit(check)
    write_report(repo)
    result["written"] = True
    return result


# ---------------------------------------------------------------------------------------------------- reading

def status(repo):
    repo = Path(repo).resolve()
    params = parameters(repo)
    try:
        auth = authorization(repo)
    except Refused as exc:
        auth = str(exc)
    strata = sorted({m["stratum"] for p in plans(repo) for m in p["members"]})
    done = lots(repo)
    return {"rule_sha256": rule_sha(repo), "authorization": auth,
            "strata": [stratum_state(repo, s, params) for s in strata],
            "plans_open": [p["lot"] for p in plans(repo) if p["lot"] not in {l["lot"] for l in done}],
            "lots": len(done), "adopted_net": sum(l["count"] for l in done) - len(register(repo, "REVERSALS")),
            "reversed": len(register(repo, "REVERSALS")), "audit_queue": len(audit_queue(repo)),
            "independent_human_certifications": 0}


def report_text(repo):
    s = status(repo)
    auth = s["authorization"] if isinstance(s["authorization"], str) else s["authorization"]["decision"]
    lines = ["# Respondendi report", "",
             "Generated by `jobs/respondendi-adoption/respondendi.py` after every write; do not edit by hand.", "",
             f"- Rule: `{RULE}` sha256 `{s['rule_sha256']}`", f"- Authorization: {auth}",
             f"- Lots adopted: {s['lots']}; statuses adopted (net of reversals): {s['adopted_net']}; reversed: {s['reversed']}",
             f"- Open plans: {', '.join(s['plans_open']) or 'none'}; orders waiting for audit: {s['audit_queue']}",
             "- Human-certified whole lifecycles: 0 (AI review and status audits are never human certification).", "",
             "| Stratum | Audits | Confirmed errors | 95% upper bound | Audits needed for the bound | Probation | Stopped |",
             "|---|---:|---:|---:|---:|---|---|"]
    for st in s["strata"]:
        bound = "none yet" if st["upper_95"] is None else format(st["upper_95"], ".1%")
        lines.append(f"| `{st['stratum']}` | {st['audits']} | {st['confirmed_errors']} | {bound} | {st['audits_needed']} | "
                     f"{'yes' if st['probation'] else 'no'} | {st['stopped'] or 'no'} |")
    lines += ["", "| Lot | Date | Adopted | By kind |", "|---|---|---:|---|"]
    for lot in lots(repo):
        kinds = ", ".join(f"{k} {n}" for k, n in (lot.get("kinds") or {}).items())
        lines.append(f"| {lot['lot']} | {lot['date']} | {lot['count']} | {kinds} |")
    return "\n".join(lines) + "\n"


def write_report(repo):
    """Regenerate the owner report after every write, so it is never stale."""
    full = path_in(repo, REPORT)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(report_text(repo).encode("utf-8"))


def audit_queue(repo):
    repo = Path(repo).resolve()
    audited = {(a["lot"], a["instrument_id"]) for a in register(repo, "AUDITS")}
    adopted = {l["lot"] for l in lots(repo)}
    out = []
    for p in plans(repo):
        if p["lot"] in adopted:
            continue
        for iid in p["audit_sample"]:
            if (p["lot"], iid) in audited:
                continue
            member = next(m for m in p["members"] if m["instrument_id"] == iid)
            out.append({"lot": p["lot"], "instrument_id": iid, "since": p["date"], "status": member["status"],
                        "claim": member["proposal"], "families_excluded": member["review_families"],
                        "reviewers_excluded": [member["producer"], member["status_reviewer"], *member["arm_reviewers"]]})
    return out


def verify(repo):
    """Every standing-rule contract entry still matches its lot, rows, claims, holds, ledger and owner decision."""
    repo = Path(repo).resolve()
    contract = json.loads(path_in(repo, CONTRACT).read_text(encoding="utf-8"))
    _, every = decisions(repo)
    ledger = path_in(repo, LEDGER).read_text(encoding="utf-8")
    holds = {h.get("claim_sha256") for h in read_jsonl(repo, HOLDS) if h.get("state") == "unresolved"}
    problems, checked = [], 0
    reversed_ids = {(r["lot"], r["instrument_id"]) for r in register(repo, "REVERSALS")}
    for entry in contract.get("accepted_additions", []):
        rule = entry.get("standing_rule")
        if not rule:
            continue
        checked += 1
        try:
            receipt = read_json(repo, rule["lot_receipt"])
            lot = receipt["lot"]
            copy = path_in(repo, f"{LOTS}/{lot}/RULE_AT_ADOPTION.md")
            if not copy.is_file() or sha(copy.read_bytes()) != rule["rule_sha256"]:
                problems.append(f"{lot}: the rule text pinned at adoption is missing or changed")
            if not owner_decision(repo, APPROVE + rule["rule_sha256"]):
                problems.append(f"{lot}: no committed owner decision cites rule sha {rule['rule_sha256']}")
            if rule["rule_sha256"] != receipt["rule_sha256"] or rule["decision"] != receipt["owner_decision"]:
                problems.append(f"{lot}: contract entry and lot receipt disagree on the rule")
            if receipt.get("core_sha256") != canon({k: v for k, v in receipt.items() if k != "core_sha256"}):
                problems.append(f"{lot}: lot receipt altered after adoption")
            live = [m for m in receipt["members"] if (lot, m["instrument_id"]) not in reversed_ids]
            rows = list(csv.DictReader(io.StringIO(pinned(repo, entry["rows"]).decode("utf-8"), newline="")))
            if [r["instrument_id"] for r in rows] != [m["instrument_id"] for m in live]:
                problems.append(f"{lot}: rows differ from the lot's members net of reversals")
            for row in rows:
                if ledger.count(csv_text([row], header=False)) != 1:
                    problems.append(f"{lot}: {row['instrument_id']} row not in the ledger exactly once")
            claims_file = receipt.get("claims_file")
            claims = ([json.loads(c) for c in path_in(repo, claims_file).read_text(encoding="utf-8").splitlines() if c.strip()]
                      if claims_file else [])
            filed = [m for m in receipt["members"] if m["kind"] == "whole_case"]
            if [canon(c) for c in claims] != [m["claim_sha256"] for m in filed]:
                problems.append(f"{lot}: canonical claims differ from the adopted claim hashes")
            for m in filed:
                if (lot, m["instrument_id"]) in reversed_ids and m["claim_sha256"] not in holds:
                    problems.append(f"{lot}: reversed {m['instrument_id']} has no unresolved source-audit hold")
            audited = {a["instrument_id"]: a for a in read_jsonl(repo, f"{LOTS}/{lot}/AUDITS.jsonl") if a.get("schema") == "eo-respondendi-audit/v1"}
            plan_receipt = read_json(repo, f"{LOTS}/{lot}/PLAN.json")
            for iid in plan_receipt.get("audit_sample", []):
                if iid in {m["instrument_id"] for m in receipt["members"]} and iid not in audited:
                    problems.append(f"{lot}: adopted {iid} was in the audit sample but has no audit")
            for a in audited.values():
                try:
                    pinned(repo, a["evidence"])
                except (KeyError, Refused) as exc:
                    problems.append(f"{lot}: audit of {a['instrument_id']} has no intact evidence ({exc})")
            for member in receipt["members"]:
                data = pinned(repo, {"path": member["proposal"]["path"], "sha256": member["proposal"]["sha256"]})
                if canon(json.loads(data.split(b"\n")[member["proposal"]["line"] - 1])) != member["claim_sha256"]:
                    problems.append(f"{lot}: {member['instrument_id']} differs from its reviewed proposal line")
        except (Refused, KeyError, ValueError, StopIteration) as exc:
            problems.append(f"{entry.get('name')}: {exc}")
    try:
        population(repo)
    except Refused as exc:
        problems.append(str(exc))
    return {"standing_rule_entries": checked, "problems": problems, "ok": not problems}


# ---------------------------------------------------------------------------------------------------- CLI

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rule-sha")
    for name in ("check", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--completion", action="append", required=True, help="…/completion/complete-vN (repeatable)")
        p.add_argument("--admission", action="append", default=[], help="packet ADMISSION.json (repeatable)")
        if name == "plan":
            p.add_argument("--lot", required=True)
            p.add_argument("--prompt", action="append", default=[], help="producer/reviewer prompt file (repeatable)")
            p.add_argument("--write", action="store_true")
    sub.add_parser("audit-queue")
    p = sub.add_parser("audit-record")
    for flag in ("--lot", "--order", "--auditor", "--role", "--verdict", "--status-found", "--basis"):
        p.add_argument(flag, required=True)
    p.add_argument("--family", default="")
    p.add_argument("--evidence")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("adjudicate")
    for flag in ("--lot", "--order", "--adjudicator", "--role", "--finding", "--basis", "--evidence"):
        p.add_argument(flag, required=True)
    p.add_argument("--family", default="")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("adopt")
    p.add_argument("--lot", required=True)
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("reverse")
    for flag in ("--lot", "--order", "--reason"):
        p.add_argument(flag, required=True)
    p.add_argument("--write", action="store_true")
    sub.add_parser("status")
    sub.add_parser("kinds")
    p = sub.add_parser("report")
    p.add_argument("--write", action="store_true")
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    try:
        if args.cmd == "rule-sha":
            print(rule_sha(repo))
            return 0
        if args.cmd == "check":
            params = parameters(repo)
            accepted, refused, facts, _ = gather(repo, args.completion, args.admission, params)
            out = {"qualifying": [m["instrument_id"] for m in accepted], "refused": refused, "completions": facts}
        elif args.cmd == "plan":
            out = plan(repo, args.lot, args.completion, args.admission, args.prompt, None, args.write)
        elif args.cmd == "audit-queue":
            out = audit_queue(repo)
        elif args.cmd == "audit-record":
            out = audit_record(repo, args.lot, args.order, args.auditor, args.role, args.family, args.verdict,
                               args.status_found, args.basis, args.evidence, None, args.write)
        elif args.cmd == "adjudicate":
            out = adjudicate(repo, args.lot, args.order, args.adjudicator, args.role, args.family, args.finding,
                             args.basis, None, args.write, args.evidence)
        elif args.cmd == "adopt":
            out = adopt(repo, args.lot, None, args.write)
        elif args.cmd == "reverse":
            out = reverse(repo, args.lot, args.order, args.reason, None, args.write)
        elif args.cmd == "status":
            out = status(repo)
        elif args.cmd == "kinds":
            params, routes = parameters(repo), routes_on_main(repo)
            out = {k: {"status": v["status"], "route": v.get("route"),
                       "active": (ulpian_state(repo, v)[1] is None) if v.get("owner_rule") else (not v.get("route") or v["route"] in routes),
                       "prerequisite": v.get("prerequisite")}
                   for k, v in params["kinds"].items()}
            out["working_text_basis_active"] = params["text_bases"]["working"]["route"] in routes
        elif args.cmd == "report":
            if args.write:
                write_report(repo)
            print(report_text(repo))
            return 0
        else:
            out = verify(repo)
            print(json.dumps(out, indent=1, ensure_ascii=False))
            return 0 if out["ok"] else 1
    except Refused as exc:
        print("REFUSED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
