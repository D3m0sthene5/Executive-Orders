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
        "max_unadjudicated_days", "max_plan_age_days", "max_lot_orders", "max_orders_per_week", "max_lots_per_day",
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


def committed(repo, rel):
    """True when rel is tracked by git and has no uncommitted change (an owner merge, not a working-tree edit)."""
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    log = git("log", "-1", "--format=%H", "--", rel)
    status = git("status", "--porcelain", "--", rel)
    return log.returncode == 0 and bool(log.stdout.strip()) and status.returncode == 0 and not status.stdout.strip()


def owner_decision(repo, token, records=None):
    """The recorded owner decision carrying token, with its owner-ruling file; None if absent.

    Both must carry the exact token: a Kean decision whose ruling text includes it, and a file under
    research/readiness/owner_rulings/ listed in that decision's sources whose text includes it. Both must be
    committed. No code can tell who wrote a file; the guard is that both reach main only by an owner merge.
    """
    for record in (records if records is not None else decisions(repo)[0].values()):
        if token not in str(record.get("ruling", "")):
            continue
        for source in record.get("sources") or []:
            if not isinstance(source, str) or not source.startswith(RULINGS):
                continue
            full = path_in(repo, source)
            if (full.is_file() and token in full.read_text(encoding="utf-8", errors="replace")
                    and committed(repo, source) and committed(repo, DECISIONS)):
                return {"decision": record.get("id"), "ruling": pin(repo, source)}
    return None


def authorization(repo):
    digest = rule_sha(repo)
    latest, _ = decisions(repo)
    suspended = owner_decision(repo, SUSPEND + digest, latest.values())
    if suspended:
        raise Refused(f"standing rule suspended by owner decision {suspended['decision']}")
    found = owner_decision(repo, APPROVE + digest, latest.values())
    if not found:
        raise Refused(f"no recorded owner decision approves RULE.md (sha256 {digest}); the rule is a draft "
                      f"(see the Respondendi owner ask in HANDOFF/KEAN_ASKS.md). Adopt nothing.")
    return dict(found, rule_sha256=digest)


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


def stratum_kind(stratum):
    """A stratum is '<process fingerprint>:<kind>:<text basis>:<tier>'."""
    parts = str(stratum).split(":")
    return parts[1] if len(parts) == 4 else None


def stratum_state(repo, stratum, params):
    params = effective(params, stratum_kind(stratum))
    rows = [f for f in findings(repo) if f.get("stratum") == stratum]
    decided = [f for f in rows if f["finding"] != "open"]
    errors = sum(f["finding"] == "confirmed_error" for f in decided)
    needed = audits_needed(errors, params["bound_target"])
    last = decided[-59:]
    stopped = None
    if sum(f["finding"] == "confirmed_error" for f in last) >= params["stop_confirmed_errors_in_59"]:
        stopped = f"{params['stop_confirmed_errors_in_59']} or more confirmed errors in the last 59 audits"
    elif len(decided) >= params["stop_bound_after_audits"] and upper_bound(errors, len(decided)) > params["stop_bound"]:
        stopped = f"audit-based upper bound above {params['stop_bound']:.0%}"
    if stopped and owner_decision(repo, RESUME + stratum):
        stopped = None
    return {"stratum": stratum, "audits": len(decided), "open": len(rows) - len(decided), "confirmed_errors": errors,
            "audits_needed": needed, "probation": len(decided) < needed,
            "upper_95": round(upper_bound(errors, len(decided)), 4) if decided else None, "stopped": stopped}


# ---------------------------------------------------------------------------------------------------- qualification

def _arm(name):
    match = re.fullmatch(r"(BLIND_REVIEW|AFTER_REVEAL)_([A-Za-z0-9]+)\.jsonl", name)
    return (match.group(1), match.group(2)) if match else (None, None)


def express_check(claim, kind, cutoff, target_id=None):
    """Zero-token check on a located ending quote: an express, named, unqualified end by a later instrument.

    The quote names target_id (default: the order itself) by number within the clause that carries an ending verb,
    with no qualifier and no section heading in between; the actor is another order or proclamation; the end falls on
    or after the actor's signing date and before the cutoff.
    """
    iid = target_id or claim.get("instrument_id") or ""
    end = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else {}
    src = end.get("source") if isinstance(end.get("source"), dict) else {}
    why = []
    actor = str(end.get("actor") or "")
    if not actor.startswith(tuple(kind["actor_prefixes"])) or actor in (iid, claim.get("instrument_id")):
        why.append(f"ending actor {actor!r} is not a later presidential instrument")
    if not src.get("text_path") or not src.get("sha256"):
        why.append("ending source has no held text path and hash")
    signed, date = str(src.get("signing_date") or ""), str(end.get("date") or "")
    if not (re.fullmatch(r"\d{4}-\d{2}-\d{2}", signed) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
            and signed <= date <= cutoff):
        why.append("end date is not on or after the actor's signing date and before the cutoff")
    target = re.sub(r"\D", "", iid)
    text = re.sub(r"[\u00ad\ufffd]\s*", "", str(src.get("quote") or ""))
    text = re.sub(r"\s+", " ", text).lower()
    hits = [m.start() for m in re.finditer(r"(?<!\d)" + re.escape(target) + r"(?!\d)", text)] if target else []
    if not hits:
        why.append(f"the ending quote never names {iid} by number")
    elif not any(_named_end(text, at, len(target), kind) for at in hits):
        why.append(f"no clause naming {iid} carries an unqualified ending verb")
    return why


def _named_end(text, at, width, kind):
    """An ending verb within the clause around the number: up to 150 characters before it or 400 after, with no
    section heading and no qualifier between the number and the verb (or in the 60 characters after the verb)."""
    verbs = "|".join(re.escape(v) for v in kind["ending_verbs"])
    for m in re.finditer(r"\b(?:" + verbs + r")\b", text[max(0, at - 150):at + width + 400]):
        start = max(0, at - 150) + m.start()
        lo, hi = min(start, at), max(start + len(m.group(0)), at + width)
        span = text[lo:hi]
        tail = re.split(r"[.;]", text[hi:hi + 60])[0]          # "revoked in part", "revoked so far as ..."
        if (re.search(r"\bsec(?:tion)?\.? ?\d", span[1:])
                or any(q in span + " " + tail for q in kind["qualifiers"])):
            continue
        return True
    return False


def lot_check(claim, params):
    """The express-named-revocation check alone (kept for callers of version 1)."""
    return express_check(claim, params["kinds"]["express_named_revocation"], params["cutoff"])


def _records(evidence):
    dossier = (evidence or {}).get("base_dossier") or {}
    records = dossier.get("evidence")
    return dossier, (records if isinstance(records, dict) else {})


def text_basis(evidence, params):
    """'original' when the frozen ORIGINAL is acceptable as an original; 'working' when it is a working text the
    rule allows (needs F6: the record names its working_text_basis); None otherwise."""
    dossier, records = _records(evidence)
    original = records.get(dossier.get("original_source_id")) or {}
    if original.get("acceptable_as_original") is True:
        return "original"
    working = params["text_bases"]["working"]
    if (original.get("working_text_basis") in working["working_text_basis"]
            and original.get("grade") in working["grades"]):
        return "working"
    return None


def classify(repo, claim, decision, evidence, params):
    """(kind id, text basis, reasons). Every predicate reads only the claim and its pinned frozen evidence.

    A kind whose route is not on main cannot be met: its predicate needs record types (CURRENT:, OWN_TEXT:,
    PARENT_END:, a working_text_basis) that only the fixed kit emits, and the outer-bound kind also needs a
    committed owner decision citing its token.
    """
    status = claim.get("whole_order_status")
    end = claim.get("whole_order_end") if isinstance(claim.get("whole_order_end"), dict) else {}
    mechanism = end.get("mechanism")
    matches = [kid for kid, kind in params["kinds"].items()
               if kind["status"] == status and (status == "yes" or mechanism in kind.get("mechanisms", []))]
    if len(matches) != 1:
        return None, None, [f"no single lot kind covers status {status!r} with end mechanism {mechanism!r}"]
    kid = matches[0]
    kind = params["kinds"][kid]
    why = []
    if kind.get("owner_token") and not owner_decision(repo, kind["owner_token"]):
        why.append(f"lot kind {kid} is inactive: {kind['prerequisite']}")
    _, records = _records(evidence)
    basis = [b for b in (decision or {}).get("basis_evidence_ids") or [] if b in records]
    prefixes = tuple(kind.get("basis_prefixes", []))
    if prefixes and not any(b.startswith(prefixes) for b in basis):
        why.append(f"lot kind {kid} needs a status basis of {list(prefixes)} in the frozen evidence"
                   + (f" (inactive until: {kind['prerequisite']})" if kind.get("prerequisite") else ""))
    cutoff = params["cutoff"]
    if kid == "express_named_revocation":
        why += express_check(claim, kind, cutoff)
        target = re.sub(r"\D", "", claim.get("instrument_id") or "")
        for b in basis:
            r = records[b]
            if not b.startswith("ACT:"):
                continue
            if r.get("scope") == "partial":
                why.append(f"the basis record {b} is a partial provision")
            # The machine savings detector also catches budget "savings"; a phrase counts when it sits in the
            # revoking provision itself or names this order.
            provision = re.sub(r"\s+", " ", str(r.get("provision_text") or r.get("text") or "")).lower()
            for phrase in r.get("savings_phrases") or []:
                flat = re.sub(r"\s+", " ", str(phrase)).lower()
                if flat and (flat[:80] in provision or provision[:80] in flat
                             or re.search(r"(?<!\d)" + re.escape(target) + r"(?!\d)", re.sub(r"(?<=\d)[ ,](?=\d)", "", flat))):
                    why.append(f"the basis record {b} carries a savings phrase in its revoking provision")
                    break
    elif kid == "own_terms":
        date = str(end.get("date") or "")
        terms = [records[b] for b in basis if b.startswith("TERM:")]
        if not any(t.get("kind") in kind["term_kinds"] and (t.get("stated_end_date") or t.get("computed_end_candidate")) == date
                   for t in terms):
            why.append("no TERM basis of a dated kind states the claimed end date")
        if end.get("actor") != claim.get("instrument_id") or not date or date > cutoff:
            why.append("an own-terms end must be the order's own, dated on or before the cutoff")
    elif kid == "spent_on_issue":
        own = [records[b] for b in basis if b.startswith("OWN_TEXT:")]
        if not any(o.get("own_text_kind") == mechanism for o in own):
            why.append("no OWN_TEXT basis of the claimed kind")
        if end.get("actor") != claim.get("instrument_id"):
            why.append("a spent-on-issue end must be the order's own")
    elif kid == "follows_parent":
        parent = str(end.get("parent") or "")
        if not parent.startswith("EO:") or parent == claim.get("instrument_id"):
            why.append("a follows-parent end must name the parent order")
        else:
            why += express_check(claim, kind, cutoff, target_id=parent)
    elif kid == "yes_current":
        if claim.get("whole_order_end"):
            why.append("a YES claim must not assert a whole-order end")
        if decision.get("current_predicate_checked_through") != cutoff:
            why.append("the current predicate must be checked through the cutoff")
        for b, r in records.items():
            if b.startswith("ACT:") and r.get("scope") in ("whole", "whole_via_parent") and r.get("verb") in kind["ending_verbs"]:
                why.append(f"held whole-scope ending lead {b} contradicts YES; outside the lot")
                break
    elif kid == "outer_bound":
        if end.get("bound_rule") != kind.get("bound_rule_id"):
            why.append("an outer-bound end must cite the owner's bound rule")
    basis_text = text_basis(evidence, params)
    if basis_text is None:
        why.append("the frozen original is neither acceptable as an original nor an allowed working text"
                   f" (working texts inactive until: {params['text_bases']['working']['prerequisite']})")
    elif basis_text not in kind.get("text_bases", ["original"]):
        why.append(f"lot kind {kid} does not accept a {basis_text} text")
    return kid, basis_text, why


def qualify(repo, completion, admission_paths, params, statuses, census, adopted_ok=frozenset()):
    """Check every proposal line of one kit completion against the rule.

    completion: repository path of a `kit.py complete --publish` output folder (…/completion/complete-vN).
    Returns (accepted members, refused [{instrument_id, reasons}], completion-level facts).
    A completion-level failure (tampered manifest, missed or untyped controls, exceptions) refuses every member.
    """
    comp = path_in(repo, completion)
    if not comp.is_dir():
        raise Refused(f"completion folder missing: {completion}")
    crel = rel_of(repo, comp)
    manifest_rel = rel_of(repo, comp.parent / "COMPLETION.json")
    manifest = read_json(repo, manifest_rel)
    inputs = read_json(repo, crel + "/INPUTS.json")
    preserved = (inputs.get("preserved_receipts") or {}).get(manifest_rel)
    if preserved != sha(path_in(repo, manifest_rel).read_bytes()):
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
    checker = read_json(repo, crel + "/TRACKER_CHECKER.json").get("by_instrument", {})
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
    control_ids, control_pins, kinds = set(), [], set()
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
                    or proposal.get("review_sha256") != overlay.get("review_sha256")):
                why.append("the promotion proposal does not bind this claim's decision and review")
        kid, basis_text, kind_why = classify(repo, claim, (files or {}).get("decision") or {},
                                              (files or {}).get("evidence") or {}, params)
        why.extend(kind_why)
        kind_rule = params["kinds"].get(kid) or {}
        if status_only and not kind_rule.get("status_only", False):
            why.append(f"lot kind {kid} has no status-only tier")
        lacking = sorted(set(kind_rule.get("required_control_kinds", [])) - kinds)
        if lacking:
            why.append(f"lot kind {kid} needs controls of kind {lacking} in the review set")
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


def gather(repo, completions, admission_paths, params, adopted_ok=frozenset()):
    state = population(repo)
    census = census_ids(repo)
    accepted, refused, facts = [], [], []
    for completion in completions:
        ok, bad, fact = qualify(repo, completion, admission_paths, params, state["statuses"], census, adopted_ok)
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
    date = date or today()
    if not LOT_NAME.fullmatch(lot or ""):
        raise Refused("lot name: lowercase letters, digits and hyphens, 3-61 characters")
    if path_in(repo, f"{LOTS}/{lot}").exists():
        raise Refused(f"lot {lot} already exists")
    params = parameters(repo)
    auth = authorization(repo) if write else None
    accepted, refused, facts, _ = gather(repo, completions, admission_paths, params)
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
                                    f"record a decision citing '{RESUME}{m['stratum']}'"]})
    accepted = [m for m in accepted if not states[m["stratum"]]["stopped"]]
    planned = {f["instrument_id"] for p in plans(repo) if not p.get("adopted") for f in p["members"]}
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
            k = min(len(group), max(eff["min_audits_steady"], math.ceil(eff["audit_rate_steady"] * len(group))))
            sample += random.Random(core_sha + stratum).sample(group, k)
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
    tx.put(f"{LOTS}/{lot}/PLAN.json", jfile(dict(receipt, owner_decision=auth["decision"])))
    tx.commit(lambda: None)
    write_report(repo)
    result["written"] = True
    return result


def plan_of(repo, lot):
    return read_json(repo, f"{LOTS}/{lot}/PLAN.json")


# ---------------------------------------------------------------------------------------------------- audits

def audit_record(repo, lot, iid, auditor, role, family, verdict, status_found, basis, evidence=None,
                 date=None, write=False):
    repo = Path(repo).resolve()
    receipt = plan_of(repo, lot)
    member = next((m for m in receipt["members"] if m["instrument_id"] == iid), None)
    if member is None:
        raise Refused(f"{iid} is not a member of lot {lot}")
    if role not in {"human", "independent_ai"}:
        raise Refused("role: human or independent_ai")
    if role == "independent_ai" and (not family or family in set(member.get("review_families") or []) | {"unrecorded"}):
        raise Refused(f"an AI auditor must name a model family different from the reviewers' {member.get('review_families')}")
    if auditor in {member.get("producer"), member.get("status_reviewer"), *member.get("arm_reviewers", [])}:
        raise Refused("the auditor must not be the producer or a reviewer of this order")
    if verdict not in {"agree", "disagree"} or status_found not in {"yes", "no", "unknown"}:
        raise Refused("verdict agree|disagree; status-found yes|no|unknown")
    if verdict == "agree" and status_found != member["status"]:
        raise Refused("an agreeing audit must find the adopted status")
    if not basis or len(basis) < 40:
        raise Refused("give the audit's dated basis (at least 40 characters)")
    if any(a["lot"] == lot and a["instrument_id"] == iid for a in register(repo, "AUDITS")):
        raise Refused(f"{iid} in lot {lot} is already audited")
    record = {"schema": "eo-respondendi-audit/v1", "lot": lot, "stratum": member["stratum"], "instrument_id": iid,
              "claim_sha256": member["claim_sha256"], "planned_status": member["status"], "auditor": auditor,
              "role": role, "model_family": family, "verdict": verdict, "status_found": status_found, "basis": basis,
              "date": date or today(), "in_sample": iid in receipt.get("audit_sample", []),
              "notice": "An audit of a provisional status; never a human certification of the lifecycle."}
    if evidence:
        record["evidence"] = pin(repo, evidence)
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


def adjudicate(repo, lot, iid, adjudicator, role, family, finding, basis, date=None, write=False):
    """Settle a disagreeing audit: a third reviewer (a person, or an AI of a family other than the auditor's)."""
    repo = Path(repo).resolve()
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
    if role == "independent_ai" and (not family or family == audit.get("model_family")
                                     or family in set(member.get("review_families") or [])):
        raise Refused("an AI adjudicator must be of a family other than the auditor's and the reviewers'")
    if not basis or len(basis) < 40:
        raise Refused("give the adjudication's basis (at least 40 characters)")
    record = {"schema": "eo-respondendi-adjudication/v1", "lot": lot, "stratum": audit["stratum"], "instrument_id": iid,
              "adjudicator": adjudicator, "role": role, "model_family": family, "finding": finding, "basis": basis,
              "date": date or today()}
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
    date = date or today()
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
    accepted, _, _, state_pop = gather(repo, receipt["completions"], receipt["admissions"], params)
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
    files are append-only) and gets an unresolved source-audit hold, so the tracker blocks it."""
    repo = Path(repo).resolve()
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
    rows = list(csv.DictReader(io.StringIO(path_in(repo, receipt["rows_file"]).read_text(encoding="utf-8"), newline="")))
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
    tx.append(REGISTER + "/REVERSALS.jsonl", jline({"lot": lot, "instrument_id": iid, "date": record["date"], "record": rev_rel}))
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
            if not owner_decision(repo, APPROVE + rule["rule_sha256"], every):
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
            p.add_argument("--date")
            p.add_argument("--write", action="store_true")
    sub.add_parser("audit-queue")
    p = sub.add_parser("audit-record")
    for flag in ("--lot", "--order", "--auditor", "--role", "--verdict", "--status-found", "--basis"):
        p.add_argument(flag, required=True)
    p.add_argument("--family", default="")
    p.add_argument("--evidence")
    p.add_argument("--date")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("adjudicate")
    for flag in ("--lot", "--order", "--adjudicator", "--role", "--finding", "--basis"):
        p.add_argument(flag, required=True)
    p.add_argument("--family", default="")
    p.add_argument("--date")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("adopt")
    p.add_argument("--lot", required=True)
    p.add_argument("--date")
    p.add_argument("--write", action="store_true")
    p = sub.add_parser("reverse")
    for flag in ("--lot", "--order", "--reason"):
        p.add_argument(flag, required=True)
    p.add_argument("--date")
    p.add_argument("--write", action="store_true")
    sub.add_parser("status")
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
            out = plan(repo, args.lot, args.completion, args.admission, args.prompt, args.date, args.write)
        elif args.cmd == "audit-queue":
            out = audit_queue(repo)
        elif args.cmd == "audit-record":
            out = audit_record(repo, args.lot, args.order, args.auditor, args.role, args.family, args.verdict,
                               args.status_found, args.basis, args.evidence, args.date, args.write)
        elif args.cmd == "adjudicate":
            out = adjudicate(repo, args.lot, args.order, args.adjudicator, args.role, args.family, args.finding,
                             args.basis, args.date, args.write)
        elif args.cmd == "adopt":
            out = adopt(repo, args.lot, args.date, args.write)
        elif args.cmd == "reverse":
            out = reverse(repo, args.lot, args.order, args.reason, args.date, args.write)
        elif args.cmd == "status":
            out = status(repo)
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
