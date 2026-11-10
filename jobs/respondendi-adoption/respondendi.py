"""Respondendi: adopt undecided-route status proposals under one standing owner rule.

Named for the ius publice respondendi, by which Augustus let vetted jurists give opinions that carried standing
authority, so that each answer did not need the emperor. Here the owner approves one rule (RULE.md) once; a
proposal that meets every condition of that exact rule is adopted without a per-order owner decision.

What it replaces: the hand route of D-20261108-haloander-adopt and D-20261110-papinian-adopt (adoption rows, a
pinned accepted_additions entry in jobs/claim-kit/population_contract.json, the reviewed claims filed canonically,
byte-identical to the reviewed REPLACEMENT_PROPOSAL.jsonl lines).

Refusals, in order: no recorded owner decision cites the SHA-256 of RULE.md (an owner ruling file under
research/readiness/owner_rulings/ and a Kean decision must both carry `respondendi-rule-sha256:<sha>`); the rule is
suspended; adoption is stopped by an audit disagreement; audit debt; size limits; and, per order, any failed
condition. Nothing here certifies anything: AI review is never human certification.

    python -I jobs/respondendi-adoption/respondendi.py rule-sha
    python -I jobs/respondendi-adoption/respondendi.py check --completion DIR/complete-vN --admission PACKET/ADMISSION.json
    python -I jobs/respondendi-adoption/respondendi.py adopt --lot NAME --completion ... --admission ... [--write]
    python -I jobs/respondendi-adoption/respondendi.py audit-queue
    python -I jobs/respondendi-adoption/respondendi.py audit-record --lot NAME --order EO:N ... [--write]
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
import sys

HERE = Path(__file__).resolve().parent
TOOL = "jobs/respondendi-adoption"
RULE = TOOL + "/RULE.md"
REGISTER = TOOL + "/register"
LOTS = "research/respondendi/lots"
REPORT = "research/respondendi/REPORT.md"
CLAIMS = "research/readiness/claims"
LEDGER = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
CONTRACT = "jobs/claim-kit/population_contract.json"
DECISIONS = "jobs/kean/register/decisions.jsonl"
RULINGS = "research/readiness/owner_rulings/"
APPROVE = "respondendi-rule-sha256:"
SUSPEND = "respondendi-suspend-sha256:"
RESUME = "respondendi-resume:"
LOT_SCHEMA = "eo-respondendi-lot/v1"
LOT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{2,60}\Z")
ROW_FIELDS = [
    "instrument_id", "provisional_substantive_status", "decision_origin", "opus_any_effect_status",
    "opus_source_text_obtained", "opus_footprint_complete_claim", "opus_first_cause_status",
    "opus_original_images_in_supplied_zip", "stage16_structured_episode_count",
    "stage16_scoped_first_cause_proven_count", "stage17_provision_count", "stage17_transition_count",
    "stage17_scoped_first_sunset_count", "recorded_legal_event_count", "stage17_assessment",
    "stage16_v3_assessment", "whole_order_first_cessation_verified_by_this_audit",
    "human_certified_by_this_release", "audit_next_step"]


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
    need = {"rule_id", "allowed_actions", "statuses_allowed", "min_blind_arms", "min_controls",
            "claims_per_control", "probation_audits", "audit_rate_probation", "min_audits_probation",
            "audit_rate_steady", "min_audits_steady", "max_pending_audits", "max_audit_age_days",
            "max_lot_orders", "max_orders_per_week", "stop_on_disagreements"}
    missing = sorted(need - set(params))
    if missing:
        raise Refused("RULE.md parameters missing: " + ", ".join(missing))
    if not set(params["statuses_allowed"]) <= {"yes", "no"} or params["min_blind_arms"] < 2:
        raise Refused("RULE.md parameters out of range")
    return params


def decisions(repo):
    """Latest revision of each Kean decision, plus every revision (for history checks)."""
    latest, every = {}, []
    for record in read_jsonl(repo, DECISIONS):
        every.append(record)
        current = latest.get(record.get("id"))
        if current is None or record.get("rev", 0) >= current.get("rev", 0):
            latest[record.get("id")] = record
    return latest, every


def owner_decision(repo, token, records=None):
    """The recorded owner decision carrying token, with its owner-ruling file; None if absent.

    Both must carry the exact token: a Kean decision whose ruling text includes it, and a file under
    research/readiness/owner_rulings/ listed in that decision's sources whose text includes it. An agent can write
    neither into main on its own: both arrive only through a pull request the owner merges.
    """
    for record in (records if records is not None else decisions(repo)[0].values()):
        if token not in str(record.get("ruling", "")):
            continue
        for source in record.get("sources") or []:
            if not isinstance(source, str) or not source.startswith(RULINGS):
                continue
            full = path_in(repo, source)
            if full.is_file() and token in full.read_text(encoding="utf-8", errors="replace"):
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
    except ValueError as exc:
        raise Refused(f"population contract invalid: {exc}")


def census_ids(repo):
    contract = json.loads(path_in(repo, CONTRACT).read_text(encoding="utf-8"))
    census = contract["census"]
    rows = csv.DictReader(io.StringIO(path_in(repo, census["path"]).read_text(encoding="utf-8-sig"), newline=""))
    return {(r.get("id") or r.get("instrument_id")) for r in rows if r.get("included_in_bibliography", "1") == "1"}


# ---------------------------------------------------------------------------------------------------- register

def lots(repo):
    return read_jsonl(repo, REGISTER + "/LOTS.jsonl")


def audits(repo):
    return read_jsonl(repo, REGISTER + "/AUDITS.jsonl")


def reversals(repo):
    return read_jsonl(repo, REGISTER + "/REVERSALS.jsonl")


def stop_state(repo):
    """The open stop, if an audit disagreement stopped adoption and no owner resume decision cites it."""
    full = path_in(repo, REGISTER + "/STOP.json")
    if not full.is_file():
        return None
    stops = json.loads(full.read_text(encoding="utf-8"))
    for stop in stops.get("stops", []):
        if not owner_decision(repo, RESUME + stop["stop_id"]):
            return stop
    return None


def audit_streak(repo):
    """Agreeing audits since the last disagreement (probation counts these)."""
    streak = 0
    for record in audits(repo):
        streak = streak + 1 if record.get("verdict") == "agree" else 0
    return streak


def pending_audits(repo):
    done = {(a.get("lot"), a.get("instrument_id")) for a in audits(repo)}
    gone = {(r.get("lot"), r.get("instrument_id")) for r in reversals(repo)}
    pending = []
    for lot in lots(repo):
        for iid in lot.get("audit_sample", []):
            if (lot["lot"], iid) not in done and (lot["lot"], iid) not in gone:
                pending.append({"lot": lot["lot"], "instrument_id": iid, "since": lot["date"]})
    return pending


def upper_bound(errors, n, confidence=0.95):
    """One-sided Clopper-Pearson upper bound on an error rate from n audits with `errors` disagreements."""
    if n <= 0:
        return 1.0
    if errors >= n:
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


# ---------------------------------------------------------------------------------------------------- qualification

def _arm(name):
    match = re.fullmatch(r"(BLIND_REVIEW|AFTER_REVEAL)_([A-Za-z0-9]+)\.jsonl", name)
    return (match.group(1), match.group(2)) if match else (None, None)


def qualify(repo, completion, admission_paths, params, statuses, census, adopted_ok=frozenset()):
    """Check every proposal line of one kit completion against the rule.

    completion: repository path of a `kit.py complete --publish` output folder (…/completion/complete-vN).
    Returns (accepted members, refused [{instrument_id, reasons}], completion-level facts).
    A completion-level failure (tampered manifest, missed control, exceptions) refuses every member.
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

    # Review receipts: every file the manifest pins, verified, grouped by arm.
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
    families = sorted({str(r.get("model_family") or "unrecorded") for recs in blind.values() for r in recs.values()})

    # Controls: enough of them, and every arm rejected every planted version.
    controls = manifest.get("controls") or []
    set_size = len({k for k in next(iter(blind.values()))})
    needed = max(params["min_controls"], math.ceil(set_size / params["claims_per_control"]))
    if len(controls) < needed:
        raise Refused(f"{crel}: {len(controls)} planted controls for a review set of {set_size}; the rule needs {needed}")
    control_ids, control_pins = set(), []
    for control in controls:
        for arm, recs in blind.items():
            record = recs.get(control.get("planted_claim_sha256"))
            if not record or record.get("verdict") != "rejected":
                raise Refused(f"{crel}: arm {arm} did not reject planted control {control.get('instrument_id')}")
        control_ids.add(control.get("instrument_id"))
        for key in ("seed", "adjudication"):
            if control.get(key):
                pinned(repo, control[key])
                control_pins.append(control[key])
    if any(c.get("caught") is not True for c in tally.get("controls") or []):
        raise Refused(f"{crel}: the kit's tally records a missed control")

    members = {m.get("instrument_id"): m for m in manifest.get("members") or []}
    outcomes = {o.get("instrument_id"): o for o in tally.get("outcomes") or []}
    base_pins = [pin(repo, manifest_rel)] + [pin(repo, crel + "/" + n) for n in
                                            ("PUBLICATION.json", "TALLY.json", "TRACKER_CHECKER.json", "INPUTS.json")]
    accepted, refused = [], []
    lines = proposal_bytes.split(b"\n")
    for number_, raw in enumerate(lines, 1):
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
        if kind not in ("whole_case", "partial_research") or (status_only and not params.get("status_only")):
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
            end = claim.get("whole_order_end")
            if status == "no" and not (isinstance(end, dict) and end.get("date") and isinstance(end.get("source"), dict)):
                why.append("status-only NO needs a dated whole-order end with its source")
        for arm in sorted(blind):
            source, want = (after, "upheld_after_reveal") if iid in control_ids else (blind, "upheld")
            record = source.get(arm, {}).get(csha)
            if (not record or record.get("verdict") != want or record.get("instrument_id") != iid
                    or record.get("independent") is not True or record.get("separate_context") is not True
                    or record.get("scope", "whole_case") != kind):
                why.append(f"arm {arm} did not record verdict {want!r} on this exact claim as an independent, "
                           f"separate-context review in scope {kind}")
        bundle = member.get("overlay_bundle") or {}
        bundle_pins = []
        try:
            files = {key: json.loads(pinned(repo, bundle[key]).decode("utf-8"))
                     for key in ("evidence", "decision", "review", "proposal")}
            bundle_pins = [bundle[key] for key in ("evidence", "decision", "review", "proposal")]
        except (KeyError, Refused) as exc:
            files = None
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
            "proposal": {"path": pub["path"], "sha256": pub["sha256"], "line": number_},
            "claim_line": raw.decode("utf-8"), "producer": producer,
            "status_reviewer": files["review"].get("reviewer"), "arm_reviewers": sorted(arm_names),
            "review_families": families,
            "pins": base_pins + receipt_pins + control_pins + bundle_pins + [pin(repo, p) for p in admitted]})
    return accepted, refused, {"completion": crel, "review_set": set_size, "controls": sorted(control_ids)}


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


# ---------------------------------------------------------------------------------------------------- writing

def row_for(member, lot, decision):
    row = dict.fromkeys(ROW_FIELDS, "")
    row.update({
        "instrument_id": member["instrument_id"],
        "provisional_substantive_status": member["status"],
        "decision_origin": (f"respondendi:{lot}:reviewed_claim {member['claim_sha256'][:16]} (standing owner rule "
                            f"{decision}; status review + two-arm blind AI review"
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
                            "(reversible; sampled audit); independent human review")})
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


def gates(repo, params, size, date):
    """Run-level refusals: stop, audit debt, weekly cap, lot size."""
    stop = stop_state(repo)
    if stop:
        raise Refused(f"adoption stopped by {stop['stop_id']} ({stop['reason'][:200]}); the owner must record a "
                      f"decision citing '{RESUME}{stop['stop_id']}'")
    pending = pending_audits(repo)
    if len(pending) > params["max_pending_audits"]:
        raise Refused(f"audit debt: {len(pending)} sampled orders unaudited (limit {params['max_pending_audits']})")
    day = dt.date.fromisoformat(date)
    late = [p for p in pending if (day - dt.date.fromisoformat(p["since"])).days > params["max_audit_age_days"]]
    if late:
        raise Refused(f"audit debt: {len(late)} sampled orders older than {params['max_audit_age_days']} days, "
                      f"first {late[0]['lot']} {late[0]['instrument_id']}")
    if size > params["max_lot_orders"]:
        raise Refused(f"{size} qualifying orders; at most {params['max_lot_orders']} per lot (split the lot)")
    week = sum(lot["count"] for lot in lots(repo) if 0 <= (day - dt.date.fromisoformat(lot["date"])).days < 7)
    if week + size > params["max_orders_per_week"]:
        raise Refused(f"weekly limit: {week} adopted in the last 7 days; {size} more exceeds {params['max_orders_per_week']}")


def sample_for(core_sha, ids, params, probation):
    rate, least = ((params["audit_rate_probation"], params["min_audits_probation"]) if probation
                   else (params["audit_rate_steady"], params["min_audits_steady"]))
    k = min(len(ids), max(least, math.ceil(rate * len(ids))))
    return sorted(random.Random(core_sha).sample(sorted(ids), k), key=number)


def adopt(repo, lot, completions, admission_paths, date=None, write=False):
    repo = Path(repo).resolve()
    date = date or today()
    if not LOT_NAME.fullmatch(lot or ""):
        raise Refused("lot name: lowercase letters, digits and hyphens, 3-61 characters")
    if path_in(repo, f"{LOTS}/{lot}").exists() or any(l["lot"] == lot for l in lots(repo)):
        raise Refused(f"lot {lot} already exists")
    params = parameters(repo)
    auth = authorization(repo) if write else None
    accepted, refused, facts, state = gather(repo, completions, admission_paths, params)
    result = {"lot": lot, "rule_sha256": rule_sha(repo), "qualifying": [m["instrument_id"] for m in accepted],
              "refused": refused, "completions": facts, "written": False}
    if not write:
        try:
            result["authorization"] = authorization(repo)
        except Refused as exc:
            result["authorization"] = str(exc)
        return result
    if not accepted:
        raise Refused("no proposal meets the rule; nothing adopted")
    gates(repo, params, len(accepted), date)
    probation = audit_streak(repo) < params["probation_audits"]
    decision = auth["decision"]
    rows = [row_for(m, lot, decision) for m in accepted]
    rows_rel, lot_rel = f"{LOTS}/{lot}/ADOPTION_ROWS.csv", f"{LOTS}/{lot}/LOT.json"
    claims_rel = f"{CLAIMS}/respondendi-{lot}.jsonl"
    core = {"schema": LOT_SCHEMA, "lot": lot, "date": date, "rule_id": params["rule_id"],
            "rule_sha256": auth["rule_sha256"], "owner_decision": decision, "owner_ruling": auth["ruling"],
            "completions": completions, "admissions": list(admission_paths),
            "members": [{k: v for k, v in m.items() if k != "claim_line"} for m in accepted],
            "refused": refused, "rows_file": rows_rel,
            "claims_file": claims_rel if any(m["kind"] == "whole_case" for m in accepted) else None,
            "independent_human_certifications": 0,
            "notice": "Provisional statuses adopted from AI review under a standing owner rule; never a human certification."}
    core_sha = canon(core)
    sample = sample_for(core_sha, [m["instrument_id"] for m in accepted], params, probation)
    receipt = dict(core, core_sha256=core_sha, probation=probation, audit_sample=sample)

    tx = Transaction(repo)
    rows_bytes = csv_text(rows).encode("utf-8")
    tx.put(rows_rel, rows_bytes)
    tx.put(lot_rel, (json.dumps(receipt, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    filed = [m for m in accepted if m.get("kind", "whole_case") == "whole_case"]
    if filed:
        tx.put(claims_rel, "".join(m["claim_line"] + "\n" for m in filed).encode("utf-8"))
    tx.append(LEDGER, csv_text(rows, header=False).encode("utf-8"))
    # Pin the rule text as it stood at adoption (a later amended RULE.md must not break this lot's pins).
    rule_rel = f"{LOTS}/{lot}/RULE_AT_ADOPTION.md"
    tx.put(rule_rel, rule_bytes(repo).replace(b"\r\n", b"\n"))
    pins = [{"path": rule_rel, "sha256": sha(tx.writes[rule_rel])}, auth["ruling"],
            {"path": lot_rel, "sha256": sha(tx.writes[lot_rel])}]
    seen = set()
    for member in accepted:
        for ref in member["pins"]:
            if ref["path"] not in seen and ref["path"] not in {p["path"] for p in pins}:
                seen.add(ref["path"])
                pins.append({"path": ref["path"], "sha256": ref["sha256"]})
    entry = {"name": f"Respondendi lot {lot} (standing owner rule {decision})", "count": len(accepted),
             "accepted_in_main": f"standing owner rule {decision} (respondendi lot {lot}; in main when this commit merges)",
             "standing_rule": {"decision": decision, "rule_sha256": auth["rule_sha256"], "lot_receipt": lot_rel},
             "rows": {"path": rows_rel, "sha256": sha(rows_bytes)}, "authorization_pins": pins}
    tx.put(CONTRACT, insert_entry(tx.text(CONTRACT), entry).encode("utf-8"))
    tx.append(REGISTER + "/LOTS.jsonl", (json.dumps(
        {"lot": lot, "date": date, "count": len(accepted), "core_sha256": core_sha, "probation": probation,
         "audit_sample": sample, "rule_sha256": auth["rule_sha256"], "owner_decision": decision},
        ensure_ascii=False) + "\n").encode("utf-8"))
    before = len(state["statuses"])

    def check():
        after = population(repo)
        if len(after["statuses"]) != before + len(accepted):
            raise Refused("population did not grow by exactly the adopted orders")
    tx.commit(check)
    write_report(repo)
    result.update(written=True, adopted=len(accepted), audit_sample=sample, probation=probation,
                  decided_before=before, decided_after=before + len(accepted), owner_decision=decision)
    return result


# ---------------------------------------------------------------------------------------------------- audits and reversal

def lot_receipt(repo, lot):
    return read_json(repo, f"{LOTS}/{lot}/LOT.json")


def audit_record(repo, lot, iid, auditor, role, family, verdict, status_found, basis, evidence=None,
                 date=None, write=False):
    repo = Path(repo).resolve()
    receipt = lot_receipt(repo, lot)
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
    if any(a["lot"] == lot and a["instrument_id"] == iid for a in audits(repo)):
        raise Refused(f"{iid} in lot {lot} is already audited")
    record = {"schema": "eo-respondendi-audit/v1", "lot": lot, "instrument_id": iid, "claim_sha256": member["claim_sha256"],
              "adopted_status": member["status"], "auditor": auditor, "role": role, "model_family": family,
              "verdict": verdict, "status_found": status_found, "basis": basis, "date": date or today(),
              "in_sample": iid in receipt.get("audit_sample", []),
              "notice": "An audit of a provisional status; never a human certification of the lifecycle."}
    if evidence:
        record["evidence"] = pin(repo, evidence)
    result = {"audit": record, "written": False}
    if not write:
        return result
    tx = Transaction(repo)
    tx.append(REGISTER + "/AUDITS.jsonl", (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
    if verdict == "disagree":
        stop_rel = REGISTER + "/STOP.json"
        full = path_in(repo, stop_rel)
        stops = json.loads(full.read_text(encoding="utf-8")) if full.is_file() else {"stops": []}
        stop_id = f"stop-{lot}-{iid.replace(':', '-').lower()}"
        stops["stops"].append({"stop_id": stop_id, "lot": lot, "instrument_id": iid, "date": record["date"],
                               "reason": f"audit by {auditor} ({role}, {family}) found {status_found}: {basis}"})
        tx.put(stop_rel, (json.dumps(stops, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
        result["stop_id"] = stop_id
        result["next"] = f"reverse {iid}: respondendi.py reverse --lot {lot} --order {iid} --reason ... --write"
    tx.commit(lambda: None)
    write_report(repo)
    result["written"] = True
    return result


def reverse(repo, lot, iid, reason, date=None, write=False):
    repo = Path(repo).resolve()
    if not reason or len(reason) < 20:
        raise Refused("give the reason for the reversal (at least 20 characters)")
    receipt = lot_receipt(repo, lot)
    if any(r["lot"] == lot and r["instrument_id"] == iid for r in reversals(repo)):
        raise Refused(f"{iid} in lot {lot} is already reversed")
    contract_text = path_in(repo, CONTRACT).read_text(encoding="utf-8")
    entry = next((e for e in json.loads(contract_text)["accepted_additions"]
                  if (e.get("standing_rule") or {}).get("lot_receipt") == f"{LOTS}/{lot}/LOT.json"), None)
    if entry is None:
        raise Refused(f"lot {lot} has no population contract entry")
    rows_rel, claims_rel = receipt["rows_file"], receipt["claims_file"]
    rows_text = path_in(repo, rows_rel).read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(rows_text, newline="")))
    row = next((r for r in rows if r["instrument_id"] == iid), None)
    if row is None:
        raise Refused(f"{iid} is not adopted in lot {lot}")
    line = csv_text([row], header=False)
    ledger = path_in(repo, LEDGER).read_text(encoding="utf-8")
    if ledger.count(line) != 1:
        raise Refused(f"{iid}: its adoption row is not in the ledger exactly once")
    claims_path = path_in(repo, claims_rel) if claims_rel else None
    claim_lines = (claims_path.read_text(encoding="utf-8").splitlines(keepends=True)
                   if claims_path and claims_path.is_file() else [])
    keep = [c for c in claim_lines if c.strip() and json.loads(c).get("instrument_id") != iid]
    removed = [c for c in claim_lines if c.strip() and json.loads(c).get("instrument_id") == iid]
    record = {"schema": "eo-respondendi-reversal/v1", "lot": lot, "instrument_id": iid, "reason": reason,
              "date": date or today(), "removed_row": row,
              "removed_claim_sha256": [canon(json.loads(c)) for c in removed],
              "effect": "status undecided again; the canonical claim is withdrawn; the lot receipt is unchanged"}
    result = {"reversal": record, "written": False}
    if not write:
        return result
    tx = Transaction(repo)
    new_rows = csv_text([r for r in rows if r["instrument_id"] != iid]).encode("utf-8")
    tx.put(rows_rel, new_rows)
    tx.put(LEDGER, ledger.replace(line, "").encode("utf-8"))
    if removed:
        tx.put(claims_rel, "".join(keep).encode("utf-8"))
    rev_rel = f"{LOTS}/{lot}/REVERSAL_{iid.replace(':', '_')}.json"
    tx.put(rev_rel, (json.dumps(record, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    new_entry = json.loads(json.dumps(entry))
    new_entry["count"] = entry["count"] - 1
    new_entry["rows"]["sha256"] = sha(new_rows)
    new_entry["authorization_pins"].append({"path": rev_rel, "sha256": sha(tx.writes[rev_rel])})
    tx.put(CONTRACT, replace_entry(contract_text, entry, new_entry).encode("utf-8"))
    tx.append(REGISTER + "/REVERSALS.jsonl", (json.dumps(
        {"lot": lot, "instrument_id": iid, "date": record["date"], "record": rev_rel}, ensure_ascii=False) + "\n").encode("utf-8"))
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
    done = audits(repo)
    errors = sum(a["verdict"] == "disagree" for a in done)
    streak = audit_streak(repo)
    adopted = sum(l["count"] for l in lots(repo)) - len(reversals(repo))
    return {"rule_sha256": rule_sha(repo), "authorization": auth, "stop": stop_state(repo),
            "lots": len(lots(repo)), "adopted_net": adopted, "reversed": len(reversals(repo)),
            "audits": len(done), "disagreements": errors, "agree_streak": streak,
            "probation": streak < params["probation_audits"], "pending_audits": pending_audits(repo),
            "error_upper_95": round(upper_bound(errors, len(done)), 4) if done else None,
            "independent_human_certifications": 0}


def report_text(repo):
    s = status(repo)
    lines = ["# Respondendi report", "",
             "Generated by `python -I jobs/respondendi-adoption/respondendi.py report --write`; do not edit by hand.", "",
             f"- Rule: `{RULE}` sha256 `{s['rule_sha256']}`",
             f"- Authorization: {s['authorization'] if isinstance(s['authorization'], str) else s['authorization']['decision']}",
             f"- Stopped: {('yes, ' + s['stop']['stop_id']) if s['stop'] else 'no'}",
             f"- Lots: {s['lots']}; adopted (net of reversals): {s['adopted_net']}; reversed: {s['reversed']}",
             f"- Audits: {s['audits']}, disagreements {s['disagreements']}, agreeing streak {s['agree_streak']}, "
             f"probation {'on' if s['probation'] else 'off'}",
             f"- Audit-based 95% upper bound on the adopted-status error rate: "
             f"{'none yet' if s['error_upper_95'] is None else format(s['error_upper_95'], '.1%')}",
             f"- Pending sampled audits: {len(s['pending_audits'])}",
             "- Human-certified whole lifecycles: 0 (AI review and status audits are never human certification).", "",
             "| Lot | Date | Adopted | Sample | Probation |", "|---|---|---:|---|---|"]
    for lot in lots(repo):
        lines.append(f"| {lot['lot']} | {lot['date']} | {lot['count']} | {', '.join(lot['audit_sample'])} | "
                     f"{'yes' if lot['probation'] else 'no'} |")
    if s["pending_audits"]:
        lines += ["", "## Pending audits", ""] + [f"- {p['lot']} {p['instrument_id']} (since {p['since']})"
                                                for p in s["pending_audits"]]
    return "\n".join(lines) + "\n"


def write_report(repo):
    """Regenerate the owner report after every write, so it is never stale."""
    full = path_in(repo, REPORT)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(report_text(repo).encode("utf-8"))


def verify(repo):
    """Every standing-rule contract entry still matches its lot, rows, claims, ledger and owner decision."""
    repo = Path(repo).resolve()
    contract = json.loads(path_in(repo, CONTRACT).read_text(encoding="utf-8"))
    _, every = decisions(repo)
    ledger = path_in(repo, LEDGER).read_text(encoding="utf-8")
    problems, checked = [], 0
    reversed_ids = {(r["lot"], r["instrument_id"]) for r in reversals(repo)}
    for entry in contract.get("accepted_additions", []):
        rule = entry.get("standing_rule")
        if not rule:
            continue
        checked += 1
        try:
            receipt = read_json(repo, rule["lot_receipt"])
            if not owner_decision(repo, APPROVE + rule["rule_sha256"], every):
                problems.append(f"{receipt['lot']}: no owner decision cites rule sha {rule['rule_sha256']}")
            copy = path_in(repo, f"{LOTS}/{receipt['lot']}/RULE_AT_ADOPTION.md")
            if not copy.is_file() or sha(copy.read_bytes()) != rule["rule_sha256"]:
                problems.append(f"{receipt['lot']}: the rule text pinned at adoption is missing or changed")
            if rule["rule_sha256"] != receipt["rule_sha256"] or rule["decision"] != receipt["owner_decision"]:
                problems.append(f"{receipt['lot']}: contract entry and lot receipt disagree on the rule")
            if receipt.get("core_sha256") != canon({k: v for k, v in receipt.items()
                                                    if k not in {"core_sha256", "probation", "audit_sample"}}):
                problems.append(f"{receipt['lot']}: lot receipt altered after adoption")
            live = [m for m in receipt["members"] if (receipt["lot"], m["instrument_id"]) not in reversed_ids]
            rows = list(csv.DictReader(io.StringIO(pinned(repo, entry["rows"]).decode("utf-8"), newline="")))
            if [r["instrument_id"] for r in rows] != [m["instrument_id"] for m in live]:
                problems.append(f"{receipt['lot']}: rows differ from the lot's members net of reversals")
            for row in rows:
                if ledger.count(csv_text([row], header=False)) != 1:
                    problems.append(f"{receipt['lot']}: {row['instrument_id']} row not in the ledger exactly once")
            claims_file = receipt.get("claims_file")
            claims = ([json.loads(c) for c in path_in(repo, claims_file).read_text(encoding="utf-8").splitlines() if c.strip()]
                      if claims_file else [])
            if [canon(c) for c in claims] != [m["claim_sha256"] for m in live if m.get("kind", "whole_case") == "whole_case"]:
                problems.append(f"{receipt['lot']}: canonical claims differ from the adopted claim hashes")
            for member in live:
                line = member["proposal"]["line"]
                data = pinned(repo, {"path": member["proposal"]["path"], "sha256": member["proposal"]["sha256"]})
                if canon(json.loads(data.split(b"\n")[line - 1])) != member["claim_sha256"]:
                    problems.append(f"{receipt['lot']}: {member['instrument_id']} differs from its reviewed proposal line")
        except (Refused, KeyError, ValueError) as exc:
            problems.append(f"{entry.get('name')}: {exc}")
    try:
        population(repo)
    except Refused as exc:
        problems.append(str(exc))
    return {"standing_rule_entries": checked, "problems": problems, "ok": not problems}


def audit_queue(repo):
    repo = Path(repo).resolve()
    out = []
    for p in pending_audits(repo):
        receipt = lot_receipt(repo, p["lot"])
        member = next(m for m in receipt["members"] if m["instrument_id"] == p["instrument_id"])
        out.append(dict(p, status=member["status"], claim=member["proposal"], families_excluded=member["review_families"],
                        reviewers_excluded=[member["producer"], member["status_reviewer"], *member["arm_reviewers"]]))
    return out


# ---------------------------------------------------------------------------------------------------- CLI

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rule-sha")
    for name in ("check", "adopt"):
        p = sub.add_parser(name)
        p.add_argument("--completion", action="append", required=True, help="…/completion/complete-vN (repeatable)")
        p.add_argument("--admission", action="append", default=[], help="packet ADMISSION.json (repeatable)")
        if name == "adopt":
            p.add_argument("--lot", required=True)
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
    p = sub.add_parser("reverse")
    p.add_argument("--lot", required=True)
    p.add_argument("--order", required=True)
    p.add_argument("--reason", required=True)
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
        elif args.cmd == "adopt":
            out = adopt(repo, args.lot, args.completion, args.admission, args.date, args.write)
        elif args.cmd == "audit-queue":
            out = audit_queue(repo)
        elif args.cmd == "audit-record":
            out = audit_record(repo, args.lot, args.order, args.auditor, args.role, args.family, args.verdict,
                               args.status_found, args.basis, args.evidence, args.date, args.write)
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
