"""Reviewed, versioned status proposals and isolated claim-kit working dossiers.

This is an offline handoff, never a status publisher. One bounded reconstruction
freezes existing compiler records and held evidence. Editing a producer decision
then reuses that frozen dossier; it does not run ingestion or corpus excavation.
An accepted independent research review permits an experimental working status.
Only the owner can adopt a proposal through the project's authoritative process.
"""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

from assemble import assemble, blank_sheet, canonical_sha, check_claim
from build import package
from inputs import COMPILER_FILES, STATUSES, UNIVERSE

INPUT_SCHEMA = "eo-claim-kit-overlay-input/v1"
EVIDENCE_SCHEMA = "eo-status-overlay-evidence/v1"
REVIEW_SCHEMA = "eo-status-overlay-review/v1"
PROPOSAL_SCHEMA = "eo-status-promotion-proposal/v1"
CODE_FILES = COMPILER_FILES
COMPILED_STEMS = ("OVERLAY_INPUTS", "CLAUSES", "OWN_TERMS", "ACTING_PROVISIONS",
                  "CHAINS", "STATUS_LEADS", "TEXT_REPRESENTATIONS")
SHA = re.compile(r"[0-9a-f]{64}\Z")
CUTOFF = "2026-10-14"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _seal(value):
    value["fingerprint"] = canonical_sha({k: v for k, v in value.items() if k != "fingerprint"})
    return value


def _sealed(value, schema):
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError("wrong_schema:" + schema)
    expected = canonical_sha({k: v for k, v in value.items() if k != "fingerprint"})
    if value.get("fingerprint") != expected:
        raise ValueError("fingerprint_mismatch:" + schema)


def _child(repo, rel):
    if not isinstance(rel, str) or not rel:
        raise ValueError("missing_relative_path")
    root = Path(repo).resolve()
    path = (root / rel).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("unsafe_repository_path:" + rel)
    return path


def _json(path):
    return json.loads(Path(path).read_bytes())


def _history_module(repo):
    path = _child(repo, "jobs/status-history/history.py")
    spec = importlib.util.spec_from_file_location("claim_kit_overlay_history", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _authority(repo, iid):
    """Pin the existing identity/status tables; admit no identities or statuses."""
    rows = {}
    paths = {}
    for rel in (UNIVERSE, STATUSES):
        path = _child(repo, rel)
        raw = path.read_bytes()
        paths[rel] = _sha(raw)
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows[rel] = list(csv.DictReader(fh))
    identity = [r for r in rows[UNIVERSE]
                if (r.get("id") or r.get("instrument_id")) == iid
                and r.get("included_in_bibliography", "1") == "1"]
    if len(identity) != 1:
        raise ValueError("identity_not_unique_in_authoritative_census:" + str(iid))
    status = [r for r in rows[STATUSES]
              if (r.get("instrument_id") or r.get("id")) == iid
              and r.get("provisional_substantive_status") in {"yes", "no"}]
    if status:
        raise ValueError("already_has_authoritative_provisional_status:" + iid)
    return {"files": paths, "identity": identity[0], "provisional_status": None}


def _current_code(repo):
    return {name: _sha(_child(repo, "jobs/claim-kit/" + name).read_bytes()) for name in CODE_FILES}


def _manifest(repo, output):
    """Reject stale compiler formats, omitted shards and noncontiguous parts."""
    out = Path(output).resolve()
    root = Path(repo).resolve()
    if not out.is_relative_to(root) or out == root:
        raise ValueError("compiled_output_must_be_inside_repository")
    if (out / "FAILED.json").exists():
        raise ValueError("compiled_run_failed")
    if (out / "STATUS.json").exists() and _json(out / "STATUS.json").get("result") != "succeeded":
        raise ValueError("compiled_runner_did_not_succeed")
    summary = _json(out / "SUMMARY.json")
    if summary.get("overlay_input_schema") != INPUT_SCHEMA:
        raise ValueError("old_compiled_outputs:overlay_input_schema; run claim-kit build once")
    if summary.get("compiled_code_sha256") != _current_code(repo):
        raise ValueError("old_compiled_outputs:code_fingerprint; run claim-kit build once")
    names = summary.get("jsonl_shards")
    hashes = summary.get("jsonl_shard_sha256")
    if (not isinstance(names, list) or len(names) != len(set(names))
            or not isinstance(hashes, dict) or set(hashes) != set(names)):
        raise ValueError("compiled_shard_manifest_required")
    if any(not isinstance(n, str) or Path(n).name != n or not n.endswith(".jsonl") for n in names):
        raise ValueError("unsafe_compiled_shard_name")
    if set(names) != {p.name for p in out.glob("*.jsonl")}:
        raise ValueError("missing_or_unlisted_compiled_shards")
    for stem in COMPILED_STEMS:
        shards = sorted(n for n in names if n == stem + ".jsonl" or n.startswith(stem + ".part"))
        if not shards or shards[0] != stem + ".jsonl":
            raise ValueError("compiled_shard_missing:" + stem)
        expected = [stem + ".jsonl"] + [stem + f".part{n:04}.jsonl" for n in range(1, len(shards))]
        if shards != expected:
            raise ValueError("compiled_shard_sequence_invalid:" + stem)
    return out, summary


def _read_records(out, summary, stem, telemetry):
    names = sorted(n for n in summary["jsonl_shards"]
                   if n == stem + ".jsonl" or n.startswith(stem + ".part"))
    for name in names:
        path = (out / name).resolve()
        if not path.is_relative_to(out):
            raise ValueError("unsafe_compiled_shard_path")
        # Stream large shards. The hash is over their original bytes, not parsed JSON.
        digest = hashlib.sha256()
        telemetry["compiled_shards_read"] += 1
        with path.open("rb") as fh:
            for number, raw in enumerate(fh, 1):
                digest.update(raw)
                telemetry["compiled_bytes_read"] += len(raw)
                if not raw.strip():
                    continue
                try:
                    row = json.loads(raw)
                except ValueError as exc:
                    raise ValueError(f"invalid_compiled_record:{name}:{number}") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"nonobject_compiled_record:{name}:{number}")
                telemetry["compiled_records_read"] += 1
                yield row
        if digest.hexdigest() != summary["jsonl_shard_sha256"].get(name):
            raise ValueError("compiled_shard_hash_mismatch:" + name)


def _unique(records, label, required=True):
    if len(records) != 1 and (required or records):
        raise ValueError("compiled_record_not_unique:" + label)
    return records[0] if records else None


def _held(repo, record, sources, telemetry):
    record = deepcopy(record)
    source = record.get("source")
    if not isinstance(source, dict):
        raise ValueError("selected_source_missing")
    rel = record.get("text_path")
    if source.get("text_path") != rel:
        raise ValueError("selected_text_path_mismatch")
    path = _child(repo, rel)
    raw = path.read_bytes()
    telemetry["selected_text_opens"] += 1
    telemetry["selected_text_bytes"] += len(raw)
    if _sha(raw) != source.get("text_sha256"):
        raise ValueError("selected_text_hash_mismatch:" + rel)
    sources[rel] = _sha(raw)
    record["text"] = raw.decode("utf-8")
    if not record["text"].strip():
        raise ValueError("selected_text_empty:" + rel)
    return record


def _source_pins(repo, dossier, pins, telemetry=None):
    """Verify all exact spans and pin local originals without pretending to read pages."""
    cache = {}
    records = list(dossier.get("evidence", {}).values()) + dossier.get("clauses", [])
    for record in records:
        source = record.get("source")
        if not isinstance(source, dict) or not record.get("text"):
            continue
        rel = source.get("text_path")
        if rel:
            if rel not in cache:
                raw = _child(repo, rel).read_bytes()
                cache[rel] = (_sha(raw), raw.decode("utf-8"))
                if telemetry is not None:
                    telemetry["span_validation_file_opens"] += 1
                    telemetry["span_validation_file_bytes"] += len(raw)
            digest, text = cache[rel]
            if digest != source.get("text_sha256"):
                raise ValueError("frozen_source_text_hash_mismatch:" + rel)
            start, end = record.get("char_start"), record.get("char_end")
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                    or text[start:end] != record["text"]):
                raise ValueError("frozen_source_span_mismatch:" + str(record.get("id")))
            pins[rel] = digest
        for key in ("local_path", "local_file", "download_path"):
            if source.get(key):
                rel = source[key]
                if rel in pins:
                    digest = pins[rel]
                else:
                    raw = _child(repo, rel).read_bytes()
                    digest = _sha(raw)
                    if telemetry is not None:
                        telemetry["span_validation_file_opens"] += 1
                        telemetry["span_validation_file_bytes"] += len(raw)
                if digest != (source.get("sha256") or source.get("local_file_sha256")):
                    raise ValueError("frozen_original_hash_mismatch:" + rel)
                pins[rel] = digest


def freeze_evidence(repo, output, packet, telemetry=None):
    """Reconstruct one undecided order from current compiler outputs, then freeze it.

    ``packet`` is the complete ``status-history.history.show`` result, never its
    compact startup preview. ``telemetry`` is an optional dict filled in place.
    No files are written. All corpus iteration occurs only in this first step.
    """
    started = time.perf_counter()
    stats = {"compiled_shards_read": 0, "compiled_bytes_read": 0, "compiled_records_read": 0,
             "selected_text_opens": 0, "selected_text_bytes": 0,
             "span_validation_file_opens": 0, "span_validation_file_bytes": 0,
             "history_pin_file_opens": 0, "history_pin_file_bytes": 0,
             "history_validator_source_opens": None, "corpus_rebuilds": 0,
             "billed_input_tokens": None, "billed_output_tokens": None}
    try:
        root = Path(repo).resolve()
        if not isinstance(packet, dict) or not isinstance(packet.get("history"), dict):
            raise ValueError("full_status_history_packet_required")
        iid = packet["history"].get("instrument_id")
        if not isinstance(iid, str):
            raise ValueError("instrument_id_required")
        authority = _authority(root, iid)
        history = _history_module(root)
        current = history.show(root / "jobs/status-history/output", iid)
        if canonical_sha(current) != canonical_sha(packet):
            raise ValueError("stale_or_incomplete_history_packet")
        if (packet["history"].get("legal_cutoff") != CUTOFF
                or packet["history"].get("provisional_status") is not None):
            raise ValueError("history_authority_status_or_cutoff_mismatch")
        errors = history.validate_packet(root, packet)
        if errors:
            raise ValueError("history_source_validation_failed:" + ";".join(errors))
        out, summary = _manifest(root, output)
        inputs = _unique([r for r in _read_records(out, summary, "OVERLAY_INPUTS", stats)
                          if r.get("instrument_id") == iid], "OVERLAY_INPUTS:" + iid)
        if inputs.get("schema") != INPUT_SCHEMA:
            raise ValueError("old_overlay_input_record")
        leads = _unique([r for r in _read_records(out, summary, "STATUS_LEADS", stats)
                         if r.get("instrument_id") == iid], "STATUS_LEADS:" + iid)
        if leads.get("status") is not None:
            raise ValueError("status_lead_must_be_undecided")
        clause = _unique([r for r in _read_records(out, summary, "CLAUSES", stats)
                          if r.get("instrument_id") == iid], "CLAUSES:" + iid, required=False)
        terms = [r for r in _read_records(out, summary, "OWN_TERMS", stats)
                 if r.get("instrument_id") == iid]
        acts = [r for r in _read_records(out, summary, "ACTING_PROVISIONS", stats)
                if r.get("target_id") == iid]
        chain = _unique([r for r in _read_records(out, summary, "CHAINS", stats)
                         if r.get("target_id") == iid], "CHAINS:" + iid)
        actor_ids = sorted(set(inputs.get("known_actor_ids", [])) | {a["actor_id"] for a in acts})
        if any(not isinstance(actor, str) for actor in actor_ids):
            raise ValueError("actor_identity_malformed")
        # A target's source is explicitly frozen by the compiler; select the same
        # sources for actors by their primary CLAUSES source, never by guessing.
        actor_clauses = {r["instrument_id"]: r for r in _read_records(out, summary, "CLAUSES", stats)
                         if r.get("instrument_id") in actor_ids}
        declared = [r for r in _read_records(out, summary, "TEXT_REPRESENTATIONS", stats)
                    if r.get("instrument_id") in set(actor_ids + [iid])]
        selected, pins = {}, {}
        target = inputs.get("selected")
        if target:
            if target.get("instrument_id") != iid:
                raise ValueError("selected_identity_mismatch")
            selected[iid] = _held(root, target, pins, stats)
            if clause and clause.get("source") != target.get("source"):
                raise ValueError("selected_clause_source_mismatch")
            if not any(r.get("instrument_id") == iid and r.get("text_path") == target.get("text_path")
                       for r in declared):
                raise ValueError("selected_text_representation_missing")
        elif clause:
            raise ValueError("selected_text_missing_for_compiled_clause")
        missing = list(leads.get("missing", []))
        for actor in actor_ids:
            source = actor_clauses.get(actor, {}).get("source")
            if source is None:
                missing.append("No compiled selected actor text located: " + actor)
                continue
            choices = [r for r in declared if r.get("instrument_id") == actor
                       and r.get("text_path") == source.get("text_path")]
            if not choices:
                raise ValueError("compiled_actor_representation_missing:" + actor)
            # Multiple page declarations can represent the same held artifact.
            # The normalized compiled source is authoritative for exact spans.
            actor_record = deepcopy(choices[0])
            actor_record["source"] = deepcopy(source)
            selected[actor] = _held(root, actor_record, pins, stats)
        corpus = {"drafts": {iid: deepcopy(inputs.get("draft", {}))}, "statuses": {},
                  "machine_searches": deepcopy(inputs.get("machine_searches", {})),
                  "current_law": {iid: deepcopy(leads.get("current_law_leads", []))},
                  "status_histories": {iid: deepcopy(leads.get("status_history"))}}
        dossier = package(iid, corpus, selected, clause, terms, acts, chain, missing, actor_ids)
        # package() uses paths relative to the canonical compiler output for
        # large actor contexts. Qualify those pointers before moving a dossier
        # into an isolated bundle, and pin the actual shared context record.
        for context in dossier["actor_contexts"]:
            if context.get("overflow"):
                old = context["overflow"]
                path = (out / old).resolve()
                if not path.is_relative_to(out):
                    raise ValueError("unsafe_actor_context_overflow")
                raw = path.read_bytes()
                record = json.loads(raw)
                actor = context["actor_id"]
                if (record.get("instrument_id") != actor or record.get("text") != selected[actor]["text"]
                        or record.get("source") != selected[actor]["source"]):
                    raise ValueError("compiled_actor_context_mismatch:" + actor)
                rel = path.relative_to(root).as_posix()
                pins[rel] = _sha(raw)
                context["overflow"] = rel
                context["held_text_path"] = selected[actor]["text_path"]
                dossier["missing"] = [m.replace("at " + old + " before", "at " + rel + " before")
                                      for m in dossier["missing"]]
                stats["span_validation_file_opens"] += 1
                stats["span_validation_file_bytes"] += len(raw)
        dossier["fingerprint"] = canonical_sha(dossier)
        _source_pins(root, dossier, pins, stats)
        # Pin the actual held history sources as well as their typed records.
        for observation in packet["observations"] + packet.get("supporting_observations", []):
            source = observation["source"]
            for key in ("compressed_path", "text_path", "path"):
                if source.get(key):
                    rel = source[key]
                    if rel not in pins:
                        raw = _child(root, rel).read_bytes()
                        pins[rel] = _sha(raw)
                        stats["history_pin_file_opens"] += 1
                        stats["history_pin_file_bytes"] += len(raw)
        rel_out = out.relative_to(root).as_posix()
        return _seal({"schema": EVIDENCE_SCHEMA, "instrument_id": iid, "legal_cutoff": CUTOFF,
                      "authority": authority, "history_packet": deepcopy(packet),
                      "history_sha256": packet["history"]["fingerprint"],
                      "source_fingerprints": dict(sorted(pins.items())),
                      "compiled": {"output": rel_out, "summary_sha256": _sha((out / "SUMMARY.json").read_bytes()),
                                   "code_sha256": summary["compiled_code_sha256"],
                                   "consumed_shard_sha256": {n: h for n, h in summary["jsonl_shard_sha256"].items()
                                      if any(n == s + ".jsonl" or n.startswith(s + ".part") for s in COMPILED_STEMS)}},
                      "base_dossier": dossier,
                      "notice": "Frozen machine evidence, not a provisional status or a lifecycle conclusion."})
    finally:
        stats["wall_seconds"] = round(time.perf_counter() - started, 6)
        if telemetry is not None:
            telemetry.update(stats)


def prepare_evidence(repo, output, iid, telemetry=None):
    """Ordinary preparation uses the existing full, unset-status dossier."""
    root = Path(repo).resolve()
    packet = _history_module(root).show(root / "jobs/status-history/output", iid)
    return freeze_evidence(root, output, packet, telemetry)


def validate_evidence(repo, evidence):
    """Recheck bounded held sources/current history and authority; do not excavate."""
    _sealed(evidence, EVIDENCE_SCHEMA)
    iid = evidence["instrument_id"]
    if _authority(repo, iid) != evidence.get("authority"):
        raise ValueError("stale_authority_snapshot")
    compiled = evidence["compiled"]
    if _current_code(repo) != compiled["code_sha256"]:
        raise ValueError("stale_compiler_code")
    out, summary = _manifest(repo, _child(repo, compiled["output"]))
    # Keep the exact original SUMMARY hash as a receipt. A runner may update its
    # input commit/timing without changing any consumed compiler record; that
    # alone must not force a new extraction and independent legal review.
    current_shards = {n: h for n, h in summary["jsonl_shard_sha256"].items()
                      if any(n == s + ".jsonl" or n.startswith(s + ".part") for s in COMPILED_STEMS)}
    if current_shards != compiled["consumed_shard_sha256"]:
        raise ValueError("stale_compiled_generation")
    if (out / "FAILED.json").exists():
        raise ValueError("compiled_run_failed")
    if (out / "STATUS.json").exists() and _json(out / "STATUS.json").get("result") != "succeeded":
        raise ValueError("compiled_runner_did_not_succeed")
    for rel, digest in evidence["source_fingerprints"].items():
        if _sha(_child(repo, rel).read_bytes()) != digest:
            raise ValueError("stale_held_source:" + rel)
    mod = _history_module(repo)
    current = mod.show(Path(repo).resolve() / "jobs/status-history/output", iid)
    if canonical_sha(current) != canonical_sha(evidence["history_packet"]):
        raise ValueError("stale_status_history")
    dossier = evidence["base_dossier"]
    if (dossier.get("instrument_id") != iid or dossier.get("whole_order_status") is not None
            or dossier.get("fingerprint") != canonical_sha(dossier)):
        raise ValueError("invalid_frozen_base_dossier")
    _source_pins(repo, dossier, {})
    return True


def extend_decision(packet, evidence, agent=""):
    """Produce a blank existing status-history sheet with explicit source judgments."""
    _sealed(evidence, EVIDENCE_SCHEMA)
    if canonical_sha(packet) != canonical_sha(evidence["history_packet"]):
        raise ValueError("decision_history_evidence_mismatch")
    h = packet["history"]
    return {"schema": "eo-status-history-decision/v1", "instrument_id": evidence["instrument_id"],
            "history_sha256": h["fingerprint"], "evidence_sha256": evidence["fingerprint"],
            "agent": agent, "approved": False, "identity_confirmed": False,
            "observations_reviewed": [], "proposed_intervals": [], "conflict_resolutions": {},
            "recommended_provisional_status": None, "rationale": "", "material_gaps": list(h.get("flags", [])),
            "basis_evidence_ids": [], "basis_review_confirmed": False,
            "earlier_endings_checked": False, "partial_scope_checked": False, "savings_checked": False,
            "current_predicate_checked_through": None, "original_pages_confirmed": False,
            "notice": "Producer research decision only. Independent review and owner adoption remain separate."}


def blank_review(decision, evidence, reviewer=""):
    """Pin this exact producer sheet and evidence; leave every review judgment blank."""
    _sealed(evidence, EVIDENCE_SCHEMA)
    return {"schema": REVIEW_SCHEMA, "instrument_id": evidence["instrument_id"],
            "decision_sha256": canonical_sha(decision), "evidence_sha256": evidence["fingerprint"],
            "history_sha256": evidence["history_sha256"], "reviewer": reviewer,
            "reviewer_role": "independent_ai", "independence_confirmed": False,
            "decision": None, "source_checks_confirmed": False,
            "checked_evidence_ids": [], "rationale": "",
            "notice": "Independent research review only; never an eo-lifecycle-review/v1 certification."}


def _reason(value):
    return isinstance(value, str) and len(value.strip()) >= 30 and not re.search(
        r"\b(?:TODO|PLACEHOLDER|TBD)\b", value, re.I)


def _decision_errors(decision, evidence):
    errors = []
    if not isinstance(decision, dict) or decision.get("schema") != "eo-status-history-decision/v1":
        return ["producer_status_decision_required"]
    if decision.get("instrument_id") != evidence["instrument_id"]:
        errors.append("decision_identity_mismatch")
    if decision.get("history_sha256") != evidence["history_sha256"]:
        errors.append("stale_decision_history")
    if decision.get("evidence_sha256") != evidence["fingerprint"]:
        errors.append("stale_decision_evidence")
    if not isinstance(decision.get("agent"), str) or not decision["agent"].strip():
        errors.append("producer_agent_required")
    for flag in ("approved", "identity_confirmed", "basis_review_confirmed", "earlier_endings_checked",
                 "partial_scope_checked", "savings_checked"):
        if decision.get(flag) is not True:
            errors.append("producer_" + flag + "_required")
    status = decision.get("recommended_provisional_status")
    if status not in {"yes", "no"}:
        errors.append("explicit_producer_yes_no_required")
    if not _reason(decision.get("rationale")):
        errors.append("producer_substantive_rationale_required")
    if decision.get("material_gaps") != []:
        errors.append("unresolved_status_material_gaps")
    h = evidence["history_packet"]["history"]
    reviewed = decision.get("observations_reviewed")
    if (not isinstance(reviewed, list) or any(not isinstance(v, str) for v in reviewed)
            or set(reviewed) != set(h.get("observation_ids", []))):
        errors.append("all_history_observations_must_be_reviewed")
    resolutions = decision.get("conflict_resolutions")
    if (not isinstance(resolutions, dict)
            or any(not _reason(resolutions.get(flag)) for flag in h.get("flags", []))):
        errors.append("history_conflicts_require_explicit_resolution")
    records = evidence["base_dossier"].get("evidence", {})
    basis = decision.get("basis_evidence_ids")
    if (not isinstance(basis, list) or not basis or any(not isinstance(v, str) for v in basis)
            or len(basis) != len(set(basis))):
        errors.append("noneditorial_status_basis_required")
        basis = []
    for ident in basis:
        record = records.get(ident)
        if (not isinstance(record, dict) or not isinstance(record.get("source"), dict)
                or not record.get("text") or not record["source"].get("text_path")):
            errors.append("status_basis_not_exact_held_evidence:" + ident)
        elif record.get("kind") == "report_deadline":
            errors.append("report_deadline_cannot_establish_status:" + ident)
        elif (record.get("basis_code") == "ofr_codification_1989_in_force"
              or isinstance(record.get("meta"), dict)
              and record["meta"].get("basis_code") == "ofr_codification_1989_in_force"):
            errors.append("historical_editorial_snapshot_cannot_establish_status:" + ident)
    if status == "no" and not any(ident.startswith(("ACT:", "TERM:", "ACTOR_TEXT:")) and ident in records for ident in basis):
        errors.append("snapshot_only_or_missing_ending_basis")
    if status == "yes":
        if not any(ident.startswith("CURRENT:") and ident in records for ident in basis):
            errors.append("snapshot_only_or_missing_current_predicate")
        if decision.get("current_predicate_checked_through") != CUTOFF:
            errors.append("current_predicate_cutoff_confirmation_required")
    original = records.get(evidence["base_dossier"].get("original_source_id"), {})
    if not original.get("acceptable_as_original"):
        errors.append("acceptable_original_required_for_status_proposal")
    if original.get("requires_page_check") and decision.get("original_pages_confirmed") is not True:
        errors.append("original_page_confirmation_required")
    return errors


def _review_errors(review, decision, evidence):
    if not isinstance(review, dict) or review.get("schema") != REVIEW_SCHEMA:
        return ["independently_pinned_review_required"]
    errors = []
    if review.get("instrument_id") != evidence["instrument_id"]:
        errors.append("review_identity_mismatch")
    if review.get("decision_sha256") != canonical_sha(decision):
        errors.append("stale_review_decision")
    if review.get("evidence_sha256") != evidence["fingerprint"]:
        errors.append("stale_review_evidence")
    if review.get("history_sha256") != evidence["history_sha256"]:
        errors.append("stale_review_history")
    producer, reviewer = decision.get("agent"), review.get("reviewer")
    if (not isinstance(reviewer, str) or not reviewer.strip()
            or not isinstance(producer, str) or reviewer.strip().casefold() == producer.strip().casefold()):
        errors.append("different_independent_reviewer_required")
    if review.get("reviewer_role") not in {"independent_ai", "independent_human"}:
        errors.append("independent_research_reviewer_role_required")
    for flag in ("independence_confirmed", "source_checks_confirmed"):
        if review.get(flag) is not True:
            errors.append("review_" + flag + "_required")
    if review.get("decision") != "accept":
        errors.append("independent_review_accept_required")
    if not _reason(review.get("rationale")):
        errors.append("review_substantive_rationale_required")
    checked = review.get("checked_evidence_ids")
    needed = set(decision.get("basis_evidence_ids", []))
    needed.add(evidence["base_dossier"].get("original_source_id"))
    if (not isinstance(checked, list) or any(not isinstance(v, str) for v in checked)
            or not needed.issubset(set(checked))):
        errors.append("review_must_check_original_and_selected_basis")
    elif any(ident not in evidence["base_dossier"].get("evidence", {}) for ident in checked):
        errors.append("review_unknown_checked_evidence")
    return errors


def propose(repo, decision, review, evidence):
    """Create an approval-ready proposal; owner acceptance always starts false."""
    validate_evidence(repo, evidence)
    errors = _decision_errors(decision, evidence)
    if not errors:
        errors.extend(_review_errors(review, decision, evidence))
    if errors:
        raise ValueError("status_proposal_rejected:" + ";".join(errors))
    proposal = {"schema": PROPOSAL_SCHEMA, "instrument_id": evidence["instrument_id"],
                "legal_cutoff": CUTOFF, "authoritative_status_before": None,
                "recommended_provisional_status": decision["recommended_provisional_status"],
                "producer": decision["agent"], "decision_sha256": canonical_sha(decision),
                "reviewer": review["reviewer"], "review_sha256": canonical_sha(review),
                "history_sha256": evidence["history_sha256"], "evidence_sha256": evidence["fingerprint"],
                "authority": deepcopy(evidence["authority"]),
                "source_fingerprints": deepcopy(evidence["source_fingerprints"]),
                "owner_acceptance": {"accepted": False, "accepted_by": None, "accepted_on": None},
                "ready_for_owner_acceptance": True, "canonical_status_written": False,
                "promotion_target": STATUSES,
                "notice": "Reviewed proposal only. Owner adoption through the authoritative process is still required; no automatic publication exists."}
    proposal["proposal_id"] = "status-overlay:" + evidence["instrument_id"] + ":" + canonical_sha(proposal)[:20]
    return _seal(proposal)


def experimental_dossier(repo, proposal, decision, review, evidence):
    """Use a reviewed proposed status in an explicitly isolated, unaccepted dossier."""
    _sealed(proposal, PROPOSAL_SCHEMA)
    if proposal != propose(repo, decision, review, evidence):
        raise ValueError("proposal_does_not_match_frozen_decision_review_evidence")
    dossier = deepcopy(evidence["base_dossier"])
    dossier["whole_order_status"] = proposal["recommended_provisional_status"]
    dossier["status_overlay"] = {
        "schema": "eo-claim-kit-working-status/v1", "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal["fingerprint"], "evidence_sha256": evidence["fingerprint"],
        "decision_sha256": proposal["decision_sha256"], "review_sha256": proposal["review_sha256"],
        "authoritative_status": None, "owner_accepted": False, "experimental_only": True}
    if dossier["whole_order_status"] == "yes":
        dossier["missing"] = sorted(set(dossier["missing"] + [
            "Current legal predicate and coverage through 2026-10-14 require judgment; a citation or 1989 snapshot cannot prove continuation."]))
    dossier["notice"] = "EXPERIMENTAL STATUS OVERLAY; OWNER HAS NOT ADOPTED THIS STATUS. " + dossier["notice"]
    dossier["fingerprint"] = canonical_sha(dossier)
    return dossier


def assemble_working(repo, sheet, proposal, decision, review, evidence):
    """Run the existing assembler and retain the experimental status label.

    Returns the existing ``(claim, errors)`` pair. No canonical claim is written;
    changing the status proposal or review requires a newly pinned lifecycle sheet.
    """
    dossier = experimental_dossier(repo, proposal, decision, review, evidence)
    claim, errors = assemble(sheet, dossier, repo)
    if claim is not None and not errors:
        claim["claim_kit"]["status_overlay"] = deepcopy(dossier["status_overlay"])
    return claim, errors


def check_working_claim(repo, claim, proposal, decision, review, evidence):
    """Recheck both the frozen status handoff and the existing lifecycle gate."""
    dossier = experimental_dossier(repo, proposal, decision, review, evidence)
    if (not isinstance(claim, dict) or not isinstance(claim.get("claim_kit"), dict)
            or claim["claim_kit"].get("status_overlay") != dossier["status_overlay"]):
        return ["working_claim_status_overlay_label_required"]
    return check_claim(claim, repo, dossier)


def _destination(repo, destination):
    root = Path(repo).resolve()
    path = Path(destination).resolve()
    allowed = (root / "jobs/claim-kit/output/overlays", root / "research/excavator")
    if not any(path.is_relative_to(base.resolve()) and path != base.resolve() for base in allowed):
        raise ValueError("overlay_destination_must_be_isolated_from_authoritative_inputs")
    if path.is_relative_to((root / "research/excavator").resolve()):
        rel = path.relative_to(root / "research/excavator")
        if not {"overlay", "overlays"}.intersection(rel.parts):
            raise ValueError("research_overlay_destination_requires_overlay_directory")
    return path


def write_bundle(repo, destination, proposal, decision, review, evidence, telemetry=None,
                 lifecycle_sheet=None):
    """Write a new versioned isolated bundle; refuse any preexisting destination."""
    started = time.perf_counter()
    destination = _destination(repo, destination)
    dossier = experimental_dossier(repo, proposal, decision, review, evidence)
    sheet = blank_sheet(dossier, decision["agent"])
    if lifecycle_sheet is not None:
        # Retain the producer's investigation across the status boundary. Only
        # the reviewed working-status envelope changes; this grants no review.
        if (not isinstance(lifecycle_sheet, dict)
                or lifecycle_sheet.get("schema") != sheet["schema"]
                or lifecycle_sheet.get("instrument_id") != evidence["instrument_id"]
                or lifecycle_sheet.get("dossier_sha256") != evidence["base_dossier"]["fingerprint"]
                or lifecycle_sheet.get("whole_order_status") not in (None, dossier["whole_order_status"])):
            raise ValueError("lifecycle_sheet_must_match_frozen_base_dossier")
        sheet = deepcopy(lifecycle_sheet)
        sheet["dossier_sha256"] = dossier["fingerprint"]
        # The new working status changes the exact decision version. Preserve
        # its analysis, but require producer confirmation against that version.
        sheet["approved"] = False
        if "whole_order_status" in sheet:
            sheet["whole_order_status"] = dossier["whole_order_status"]
    if destination.exists():
        raise ValueError("overlay_bundle_exists; use a new versioned destination")
    before = _authority(repo, evidence["instrument_id"])
    payloads = {"EVIDENCE.json": evidence, "STATUS_DECISION.json": decision,
                "STATUS_REVIEW.json": review, "PROMOTION_PROPOSAL.json": proposal,
                "DOSSIER.json": dossier, "LIFECYCLE_DECISION.json": sheet}
    if lifecycle_sheet is not None:
        payloads["LIFECYCLE_SOURCE_DECISION.json"] = deepcopy(lifecycle_sheet)
        payloads["LIFECYCLE_CONTINUITY.json"] = {
            "instrument_id": evidence["instrument_id"],
            "source_sheet_path": "LIFECYCLE_SOURCE_DECISION.json",
            "source_sheet_sha256": canonical_sha(lifecycle_sheet),
            "source_dossier_sha256": evidence["base_dossier"]["fingerprint"],
            "working_sheet_sha256": canonical_sha(sheet),
            "working_dossier_sha256": dossier["fingerprint"],
            "producer_reconfirmation_required": True,
            "independent_lifecycle_review_required": True}
    destination.mkdir(parents=True, exist_ok=False)
    for filename, value in payloads.items():
        (destination / filename).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    stats = {"schema": "eo-status-overlay-telemetry/v1", "wall_seconds": round(time.perf_counter() - started, 6),
             "corpus_rebuilds": 0, "billed_input_tokens": None, "billed_output_tokens": None,
             "authoritative_files_unchanged": before == _authority(repo, evidence["instrument_id"])}
    if telemetry is not None:
        stats["evidence_freeze"] = deepcopy(telemetry)
    (destination / "TELEMETRY.json").write_text(json.dumps(stats, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if not stats["authoritative_files_unchanged"]:
        raise ValueError("authority_changed_during_overlay_write")
    return {"directory": str(destination), "proposal_id": proposal["proposal_id"],
            "dossier_sha256": dossier["fingerprint"], "owner_accepted": False,
            "authoritative_files_unchanged": True}
