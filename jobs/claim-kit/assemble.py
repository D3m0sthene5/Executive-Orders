"""Model-neutral, fail-closed decision-sheet -> Stage 19 claim assembly.

This module copies evidence; it supplies no legal decisions and writes no reviews.
An empty error list proves only the checks documented here. The independent
claim-checker must additionally establish custody of the original source bytes.
"""

from copy import deepcopy
import base64
import binascii
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import working_text as W
import factual_events as F


DOSSIER_SCHEMA = "eo-claim-kit-dossier/v1"
DECISION_SCHEMA = "eo-claim-kit-decision/v1"
CUTOFF = "2026-10-14"
SHA = re.compile(r"[0-9a-f]{64}\Z")


def canonical_sha(value):
    """Hash canonical JSON. For dossiers, omit their self-referential fingerprint."""
    if isinstance(value, dict) and value.get("schema") == DOSSIER_SCHEMA:
        value = {k: v for k, v in value.items() if k != "fingerprint"}
    data = json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _records(dossier):
    """The evidence map includes clause records, keyed by stable dossier ids."""
    evidence = dossier.get("evidence", {})
    result = dict(evidence) if isinstance(evidence, dict) else {}
    for clause in dossier.get("clauses", []) if isinstance(dossier.get("clauses"), list) else []:
        if isinstance(clause, dict):
            ident = clause.get("id") or "CLAUSES:" + str(clause.get("scope_id", ""))
            if isinstance(ident, str):
                result.setdefault(ident, clause)
    return result


def derive_inventory(dossier, overrides):
    """Derive exact clause records from producer-selected original-source spans.

    Return (clauses, evidence_by_id, errors). Offsets are absolute code-point
    offsets in the cited held text file. Only the dossier's original evidence id
    is permitted; the source and quote cannot be supplied or edited by a sheet.
    The caller retains the ORIGINAL dossier fingerprint, and pins the override
    list in claim_kit metadata so checking reconstructs these same records.
    """
    errors, clauses, evidence = [], [], {}
    if not isinstance(dossier, dict) or not isinstance(overrides, list) or not overrides:
        return [], {}, ["inventory_overrides_nonempty_list_required"]
    original_id = dossier.get("original_source_id")
    parent = _records(dossier).get(original_id) if isinstance(original_id, str) else None
    if not isinstance(parent, dict):
        return [], {}, ["inventory_override_original_missing"]
    parent_start, parent_end, text = parent.get("char_start"), parent.get("char_end"), parent.get("text")
    if (type(parent_start) is not int or type(parent_end) is not int or
            not isinstance(text, str) or parent_start < 0 or
            parent_end <= parent_start or len(text) != parent_end - parent_start or
            not isinstance(parent.get("source"), dict)):
        return [], {}, ["inventory_override_original_span_malformed"]
    seen, ranges = set(), []
    required = {"scope_id", "source_id", "char_start", "char_end", "reason"}
    for index, override in enumerate(overrides):
        label = f"inventory_override_{index}"
        if not isinstance(override, dict) or set(override) != required:
            errors.append(label + ":fields")
            continue
        scope, source_id = override.get("scope_id"), override.get("source_id")
        start, end = override.get("char_start"), override.get("char_end")
        if (not isinstance(scope, str) or
                not scope.startswith(str(dossier.get("instrument_id")) + "#") or
                not scope.partition("#")[2].strip()):
            errors.append(label + ":scope_id")
            continue
        if scope in seen:
            errors.append(label + ":duplicate_scope")
        seen.add(scope)
        if source_id != original_id:
            errors.append(label + ":source_must_be_dossier_original")
        if not _nonempty(override.get("reason")):
            errors.append(label + ":reason_required")
        if (type(start) is not int or type(end) is not int or
                not parent_start <= start < end <= parent_end):
            errors.append(label + ":outside_original_span")
            continue
        if any(start < other_end and end > other_start for other_start, other_end in ranges):
            errors.append(label + ":overlapping_spans")
        ranges.append((start, end))
        quote = text[start - parent_start:end - parent_start]
        if not quote.strip():
            errors.append(label + ":empty_text")
        ident = f"OVERRIDE:{original_id}#{start}-{end}"
        record = {"id": ident, "scope_id": scope, "source": deepcopy(parent["source"]),
                  "text": quote, "char_start": start, "char_end": end,
                  "parent_source_id": original_id, "inventory_reason": override.get("reason")}
        clauses.append(record)
        evidence[ident] = record
    return clauses, evidence, list(dict.fromkeys(errors))


def blank_sheet(dossier, agent=""):
    """Produce an unapproved sheet, with every legal judgment left blank."""
    sheet = {
        "schema": DECISION_SCHEMA,
        "instrument_id": dossier.get("instrument_id"),
        "dossier_sha256": canonical_sha(dossier), "agent": agent,
        "original_confirmed": False, "original_pages_confirmed": False, "inventory_confirmed": False,
        "inventory_overrides": [],
        "clauses": [{"scope_id": c.get("scope_id"),
                     "clause_id": c.get("id") or "CLAUSES:" + str(c.get("scope_id", "")),
                     "state": None, "end_id": None, "effective_date": None,
                     "effective_date_confirmed": False, "current_basis_id": None,
                     "current_legal_basis": "", "checked_through": None,
                     "later_event_ids": [], "later_events": [], "reason": ""}
                    for c in dossier.get("clauses", [])],
        "savings": {"state": None, "source_id": None, "reason": ""},
        "search_ids": [], "conflict_resolutions": {}, "research_rationale": "",
        "unresolved_material_gaps": deepcopy(dossier.get("missing", [])),
        "approved": False,
    }
    refs = [r.get("source", {}) for r in _records(dossier).values()
            if isinstance(r, dict) and r.get("source", {}).get("acceptable_as_original") is False]
    if refs:
        sheet["working_text"] = W.blank(refs)
    return sheet


def _gate(repo):
    path = Path(repo) / "research/stage19/code/claim_gate.py"
    spec = importlib.util.spec_from_file_location("claim_kit_stage19_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _child(repo, name):
    if not isinstance(name, str) or not name:
        raise ValueError("missing path")
    root = Path(repo).resolve()
    path = (root / name).resolve()
    path.relative_to(root)  # Reject absolute outside paths and symlink escapes.
    return path


def _source_errors(source, quote, repo, label):
    errors = []
    if not isinstance(source, dict):
        return [label + ":missing_source"]
    original_sha = source.get("sha256")
    if not original_sha and source.get("archival_id"):
        original_sha = source.get("local_file_sha256")
    if not isinstance(original_sha, str) or not SHA.fullmatch(original_sha):
        errors.append(label + ":source_sha256")
    if not isinstance(source.get("text_sha256"), str) or not SHA.fullmatch(source["text_sha256"]):
        errors.append(label + ":text_sha256")
    try:
        raw = _child(repo, source.get("text_path")).read_bytes()
        # Decode without newline conversion: offsets refer to exact stored text.
        text = raw.decode("utf-8")
        if hashlib.sha256(raw).hexdigest() != source.get("text_sha256"):
            errors.append(label + ":text_hash_mismatch")
        start, end = source.get("char_start"), source.get("char_end")
        if (type(start) is not int or type(end) is not int or
                not 0 <= start < end <= len(text)):
            errors.append(label + ":quote_offsets")
        elif not isinstance(quote, str) or not quote or text[start:end] != quote:
            errors.append(label + ":quote_not_exact_slice")
    except (OSError, ValueError, UnicodeError, TypeError):
        errors.append(label + ":text_unavailable_or_unsafe")
    # A declared local original must hash correctly; undeclared custody is checked
    # independently by jobs/claim-checker, not inferred from extracted text.
    for key in ("local_path", "local_file", "download_path"):
        if source.get(key):
            try:
                if hashlib.sha256(_child(repo, source[key]).read_bytes()).hexdigest() != original_sha:
                    errors.append(label + ":original_hash_mismatch")
            except (OSError, ValueError, TypeError):
                errors.append(label + ":original_unavailable_or_unsafe")
    return errors


def _reference(ident, evidence, errors):
    record = evidence.get(ident) if isinstance(ident, str) else None
    if not isinstance(record, dict):
        errors.append("unknown_evidence_id:" + str(ident))
        return {}
    source = deepcopy(record.get("source", {}))
    if not isinstance(source, dict):
        errors.append("malformed_source:" + str(ident))
        return {}
    source.update({"evidence_id": encode_evidence_id(ident),
                   "evidence_id_encoding": "base64url-utf8", "quote": record.get("text"),
                   "char_start": record.get("char_start"),
                   "char_end": record.get("char_end")})
    return source


def encode_evidence_id(ident):
    """Serialize an internal record id without suggesting it is a legal citation."""
    if not isinstance(ident, str) or not ident:
        raise ValueError("evidence id must be a nonempty string")
    return base64.urlsafe_b64encode(ident.encode("utf-8")).decode("ascii").rstrip("=")


def decode_evidence_id(source):
    """Decode only the explicitly marked, canonical claim-provenance encoding."""
    if not isinstance(source, dict) or source.get("evidence_id_encoding") != "base64url-utf8":
        raise ValueError("missing or unsupported evidence id encoding")
    value = source.get("evidence_id")
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("malformed encoded evidence id")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        ident = raw.decode("utf-8")
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise ValueError("malformed encoded evidence id") from exc
    if not ident or encode_evidence_id(ident) != value:
        raise ValueError("noncanonical encoded evidence id")
    return ident


def _reference_id(source):
    try:
        return decode_evidence_id(source)
    except ValueError:
        return None


def _conflict_id(conflict):
    if isinstance(conflict, str):
        return conflict
    if isinstance(conflict, dict):
        value = conflict.get("id") or conflict.get("code")
        return value if isinstance(value, str) else canonical_sha(conflict)
    return str(conflict)


def _placeholder(value):
    if isinstance(value, str):
        return "PLACEHOLDER" in value.upper()
    if isinstance(value, dict):
        return any(_placeholder(k) or _placeholder(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_placeholder(v) for v in value)
    return False


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _check_claim(claim, repo, dossier=None):
    """Run Stage 19 plus strict exact-slice checks; no custody/review assertion.

    If a dossier is supplied, every source must also match a named immutable
    evidence record. This prevents edited claims from substituting free sources.
    """
    if not isinstance(claim, dict):
        return ["claim_not_object"]
    errors = []
    if _placeholder(claim):
        errors.append("placeholder")
    if not claim.get("operative_clauses"):
        errors.append("operative_clauses_empty")
    gaps = claim.get("unresolved_material_gaps", [])
    if claim.get("later_source_search") and isinstance(gaps, list) and any(
            isinstance(g, str) and "CONFLICT" in g.upper() for g in gaps):
        errors.append("conflicts_with_later_source_search")
    try:
        errors.extend(_gate(repo).validate_claim(claim, expected_status=(
            dossier.get("whole_order_status") if isinstance(dossier, dict) else None)))
    except (OSError, AttributeError, TypeError, ValueError, KeyError) as exc:
        errors.append("stage19_gate_failure:" + type(exc).__name__)

    evidence = _records(dossier) if isinstance(dossier, dict) else None
    if dossier is not None:
        if not isinstance(dossier, dict):
            errors.append("dossier_not_object")
        else:
            fingerprint = canonical_sha(dossier)
            if dossier.get("fingerprint") != fingerprint:
                errors.append("dossier_fingerprint_mismatch")
            if claim.get("instrument_id") != dossier.get("instrument_id"):
                errors.append("instrument_id_mismatch")
            metadata = claim.get("claim_kit")
            if not isinstance(metadata, dict):
                metadata = {}
            if metadata.get("dossier_sha256") != fingerprint:
                errors.append("stale_dossier_fingerprint")
            if metadata.get("producer_approved") is not True or not _nonempty(metadata.get("agent")):
                errors.append("producer_approval_required")
            overrides = metadata.get("inventory_overrides", [])
            if not isinstance(overrides, list):
                errors.append("inventory_overrides_not_list")
            elif overrides:
                corrected, derived, override_errors = derive_inventory(dossier, overrides)
                errors.extend(override_errors)
                evidence.update(derived)
                expected_inventory = {c["scope_id"]: c["id"] for c in corrected}
                actual = claim.get("operative_clauses")
                if not isinstance(actual, list) or len(actual) != len(corrected):
                    errors.append("corrected_inventory_mismatch")
                elif any(not isinstance(c, dict) or not isinstance(c.get("original_source"), dict) or
                         expected_inventory.get(c.get("scope_id")) != _reference_id(c["original_source"])
                         for c in actual):
                    errors.append("corrected_inventory_mismatch")
                elif len({c.get("scope_id") for c in actual}) != len(corrected):
                    errors.append("corrected_inventory_mismatch")
            original_record = evidence.get(dossier.get("original_source_id"), {})
            if (original_record.get("requires_page_check") and original_record.get("acceptable_as_original") is not False
                    and metadata.get("original_pages_confirmed") is not True):
                errors.append("original_page_check_confirmation_required")
            representation = claim.get("original_representation")
            if not isinstance(representation, dict) or _reference_id(representation) != dossier.get("original_source_id"):
                errors.append("original_source_id_mismatch")

    clauses = claim.get("operative_clauses", [])
    if isinstance(clauses, list):
        for index, clause in enumerate(clauses):
            if not isinstance(clause, dict):
                continue
            source = clause.get("original_source")
            if isinstance(source, dict) and clause.get("original_operative_text") != source.get("quote"):
                errors.append(f"clause_{index}_original_text_not_source_quote")

    def walk(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                label = path + "." + key if path else key
                if key in ("original_representation", "original_source", "source"):
                    quote = child.get("quote") if isinstance(child, dict) else None
                    errors.extend(_source_errors(child, quote, repo, label))
                    if evidence is not None:
                        ident = _reference_id(child)
                        if ident is None:
                            errors.append(label + ":invalid_evidence_id_encoding")
                        comparison_errors = []
                        expected = _reference(ident, evidence, comparison_errors)
                        if comparison_errors or child != expected:
                            errors.append(label + ":not_dossier_evidence")
                else:
                    walk(child, label)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
    walk(claim)
    policy_errors, _ = W.policy(claim, repo)
    errors.extend(policy_errors)
    errors.extend(F.claim_errors(claim, repo, dossier))
    return list(dict.fromkeys(errors))


def _assemble(sheet, dossier, repo):
    """Return (claim, []) or (None, explicit_errors); never mutate inputs."""
    if not isinstance(sheet, dict) or not isinstance(dossier, dict):
        return None, ["sheet_or_dossier_not_object"]
    errors = []
    if sheet.get("schema") != DECISION_SCHEMA:
        errors.append("decision_schema")
    if dossier.get("schema") != DOSSIER_SCHEMA:
        errors.append("dossier_schema")
    fingerprint = canonical_sha(dossier)
    if dossier.get("fingerprint") != fingerprint:
        errors.append("dossier_fingerprint_mismatch")
    if sheet.get("dossier_sha256") != fingerprint:
        errors.append("stale_dossier_fingerprint")
    if sheet.get("instrument_id") != dossier.get("instrument_id"):
        errors.append("instrument_id_mismatch")
    if "whole_order_status" in sheet and sheet["whole_order_status"] != dossier.get("whole_order_status"):
        errors.append("whole_order_status_mismatch")
    if dossier.get("whole_order_status") not in ("yes", "no"):
        errors.append("missing_provisional_status")
    for field in ("approved", "inventory_confirmed"):
        if sheet.get(field) is not True:
            errors.append(field + "_required")
    if not _nonempty(sheet.get("agent")):
        errors.append("agent_required")
    if _placeholder(sheet) or _placeholder(dossier.get("clauses", [])):
        errors.append("placeholder")
    if sheet.get("unresolved_material_gaps") != []:
        errors.append("unresolved_material_gaps")
    resolutions = sheet.get("conflict_resolutions")
    if not isinstance(resolutions, dict):
        resolutions = {}
        errors.append("conflict_resolutions_not_object")
    conflicts = dossier.get("conflicts", [])
    if not isinstance(conflicts, list):
        errors.append("conflicts_not_list")
        conflicts = []
    unresolved = [c for c in conflicts if not _nonempty(resolutions.get(_conflict_id(c)))]
    if unresolved:
        errors.append("unresolved_conflicts")
        if sheet.get("search_ids"):
            errors.append("conflicts_with_later_source_search")
    evidence = _records(dossier)
    overrides = sheet.get("inventory_overrides", [])
    corrected = None
    if not isinstance(overrides, list):
        errors.append("inventory_overrides_not_list")
    elif overrides:
        corrected, derived, override_errors = derive_inventory(dossier, overrides)
        errors.extend(override_errors)
        evidence.update(derived)
    original_id = dossier.get("original_source_id")
    original_record = evidence.get(original_id, {}) if isinstance(original_id, str) else {}
    if not isinstance(original_record, dict):
        original_record = {}
    original = _reference(original_id, evidence, errors)
    if (original_record.get("requires_page_check") and original_record.get("acceptable_as_original") is not False
            and sheet.get("original_pages_confirmed") is not True):
        errors.append("original_page_check_confirmation_required")
    grade = " ".join(str(original_record.get(k, "")) for k in
                     ("source_grade", "kind", "role", "type", "origin"))
    grade += " " + str(original.get("url", ""))
    grade += " " + " ".join(str(original.get(k, "")) for k in
                              ("source_grade", "kind", "role", "type", "origin"))
    provisional = original_record.get("acceptable_as_original") is False or original.get("acceptable_as_original") is False
    if provisional:
        if original.get("grade") not in W.GRADES or original.get("acceptable_as_original") is not False:
            errors.append("lead_is_not_original:working_text_grade_required")
        if not isinstance(sheet.get("working_text"), dict):
            errors.append("working_text:disclosure_required")
    elif "richardson" in grade.lower() or "compiled_transcription_lead" in grade.lower():
        errors.append("lead_is_not_original")
    elif sheet.get("original_confirmed") is not True:
        errors.append("original_confirmed_required")

    claim = {"schema": "eo-lifecycle-claim/v1", "instrument_id": dossier.get("instrument_id"),
             "whole_order_status": dossier.get("whole_order_status"),
             "original_representation": original, "operative_clauses": [],
             "whole_order_end": None, "savings_residuals": {}, "later_source_search": [],
             "research_rationale": sheet.get("research_rationale"),
             "unresolved_material_gaps": deepcopy(sheet.get("unresolved_material_gaps")),
             "claim_kit": {"dossier_sha256": fingerprint, "agent": sheet.get("agent"),
                           "producer_approved": sheet.get("approved") is True,
                           "original_pages_confirmed":sheet.get("original_pages_confirmed") is True,
                           "inventory_overrides": deepcopy(overrides)}}
    if isinstance(sheet.get("working_text"), dict):
        claim["working_text"] = deepcopy(sheet["working_text"])
    clauses = sheet.get("clauses")
    expected = corrected if corrected is not None else dossier.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append("operative_clauses_empty")
        clauses = []
    if not isinstance(expected, list) or not expected:
        errors.append("dossier_clause_inventory_empty")
        expected = []
    scopes = [c.get("scope_id") for c in clauses if isinstance(c, dict)]
    expected_scopes = [c.get("scope_id") for c in expected if isinstance(c, dict)]
    valid_scopes = all(isinstance(s, str) and s.strip() for s in scopes + expected_scopes)
    if (not valid_scopes or len(scopes) != len(clauses) or
            (valid_scopes and (len(set(scopes)) != len(scopes) or set(scopes) != set(expected_scopes)))):
        errors.append("clause_inventory_mismatch")
    original_ids = {c.get("scope_id"): c.get("id") or "CLAUSES:" + str(c.get("scope_id", ""))
                    for c in expected if isinstance(c, dict) and isinstance(c.get("scope_id"), str)}

    def event(ident, decision, date_key):
        rec = evidence.get(ident, {}) if isinstance(ident, str) else {}
        if not isinstance(rec, dict):
            rec = {}
        ref = _reference(ident, evidence, errors)
        date_value = decision.get("effective_date")
        if decision.get("effective_date_confirmed") is not True:
            errors.append("effective_date_confirmation_required:" + str(ident))
        return {date_key: date_value, "actor": rec.get("actor_id") or rec.get("instrument_id"),
                "mechanism": decision.get("mechanism") or rec.get("mechanism") or rec.get("verb") or rec.get("kind"),
                "source": ref}

    for index, decision in enumerate(clauses):
        if not isinstance(decision, dict):
            errors.append(f"clause_{index}_not_object")
            continue
        scope = decision.get("scope_id")
        ident = decision.get("clause_id") or (original_ids.get(scope) if isinstance(scope, str) else None)
        if corrected is not None and ident != (original_ids.get(scope) if isinstance(scope, str) else None):
            errors.append(f"clause_{index}_corrected_evidence_id_mismatch")
        rec = evidence.get(ident, {}) if isinstance(ident, str) else {}
        if not isinstance(rec, dict):
            rec = {}
        if rec.get("scope_id") != scope:
            errors.append(f"clause_{index}_evidence_scope_mismatch")
        item = {"scope_id": scope, "original_operative_text": rec.get("text"),
                "original_source": _reference(ident, evidence, errors),
                "state_at_cutoff": decision.get("state"), "later_events": [],
                "judgment_reason": decision.get("reason")}
        if not _nonempty(decision.get("reason")):
            errors.append(f"clause_{index}_reason_required")
        if decision.get("state") in ("terminated", "never_activated"):
            end_rec = evidence.get(decision.get("end_id"), {}) if isinstance(decision.get("end_id"), str) else {}
            if isinstance(end_rec, dict) and end_rec.get("kind") == "report_deadline":
                errors.append(f"clause_{index}_report_deadline_is_not_end")
            item["first_end"] = event(decision.get("end_id"), decision, "date")
        elif decision.get("state") == "operative":
            basis_rec = evidence.get(decision.get("current_basis_id"), {}) if isinstance(decision.get("current_basis_id"), str) else {}
            if isinstance(basis_rec, dict):
                basis_meta = basis_rec.get("meta", {})
                if not isinstance(basis_meta, dict):
                    basis_meta = {}
                basis_code = basis_rec.get("basis_code") or basis_meta.get("basis_code")
                if basis_code == "ofr_codification_1989_in_force":
                    errors.append(f"clause_{index}_historical_editorial_is_not_current_basis")
            item["current_predicate"] = {
                "legal_basis": decision.get("current_legal_basis"),
                "source": _reference(decision.get("current_basis_id"), evidence, errors),
                "checked_through": decision.get("checked_through")}
        later = decision.get("later_events", [])
        ids = decision.get("later_event_ids", [])
        if not isinstance(later, list) or not isinstance(ids, list):
            errors.append(f"clause_{index}_later_events_not_list")
            later, ids = [], []
        # The explicit records are authoritative. Bare ids still require a
        # separately recorded confirmation and date; a machine candidate is not
        # a producer's effective-date judgment.
        seen = set()
        for later_decision in later:
            if not isinstance(later_decision, dict):
                errors.append(f"clause_{index}_later_event_not_object")
                continue
            later_id = later_decision.get("id")
            if not isinstance(later_id, str):
                errors.append(f"clause_{index}_malformed_later_event_id")
                continue
            if later_id in seen:
                errors.append(f"clause_{index}_duplicate_later_event")
            seen.add(later_id)
            item["later_events"].append(event(later_id, later_decision, "effective_date"))
        if any(not isinstance(ident, str) or ident not in seen for ident in ids):
            errors.append(f"clause_{index}_later_event_confirmation_required")
        claim["operative_clauses"].append(item)
    if claim["whole_order_status"] == "no":
        ends = [c.get("first_end") for c in claim["operative_clauses"]]
        dated = [e for e in ends if isinstance(e, dict) and isinstance(e.get("date"), str)]
        if dated:
            claim["whole_order_end"] = deepcopy(max(dated, key=lambda e: e["date"]))
    savings = sheet.get("savings")
    if isinstance(savings, dict):
        claim["savings_residuals"] = {"state": savings.get("state"), "reason": savings.get("reason"),
                                     "source": _reference(savings.get("source_id"), evidence, errors)}
    searches = dossier.get("machine_searches", [])
    by_search = {s.get("search_id"): s for s in searches
                 if isinstance(s, dict) and isinstance(s.get("search_id"), str)} if isinstance(searches, list) else {}
    chosen = sheet.get("search_ids", [])
    if not isinstance(chosen, list):
        errors.append("search_ids_not_list")
        chosen = []
    if len(set(x for x in chosen if isinstance(x, str))) != len(chosen):
        errors.append("duplicate_or_malformed_search_ids")
    for ident in chosen:
        record = by_search.get(ident) if isinstance(ident, str) else None
        entry = record.get("entry", record) if isinstance(record, dict) else None
        if not isinstance(entry, dict):
            errors.append("unknown_search_id:" + str(ident))
            continue
        claim["later_source_search"].append(deepcopy(entry))
    if chosen and all(isinstance(by_search.get(ident), dict) and
                      (by_search[ident].get("coverage_warning") or
                       (isinstance(by_search[ident].get("entry"), dict) and
                        by_search[ident]["entry"].get("coverage_warning")))
                      for ident in chosen if isinstance(ident, str)):
        errors.append("search_coverage_incomplete")
    if isinstance(claim.get("working_text"), dict):
        used = {W.key(ref) for _, ref in W.references(claim) if ref.get("acceptable_as_original") is False}
        if not used:
            claim.pop("working_text")
        elif isinstance(claim["working_text"].get("confirmations"), list):
            claim["working_text"]["confirmations"] = [c for c in claim["working_text"]["confirmations"]
                if isinstance(c, dict) and W.key(c) in used]
    errors.extend(check_claim(claim, repo, dossier))
    errors = list(dict.fromkeys(errors))
    return (None, errors) if errors else (claim, [])


def check_claim(claim, repo, dossier=None):
    """Fail closed for malformed JSON shapes as well as incomplete claims."""
    try:
        return _check_claim(claim, repo, dossier)
    except (TypeError, ValueError, KeyError, AttributeError, RecursionError) as exc:
        return ["malformed_claim_or_dossier:" + type(exc).__name__]


def assemble(sheet, dossier, repo):
    """Public fail-closed assembler; errors never produce a claim to commit."""
    try:
        return _assemble(sheet, dossier, repo)
    except (TypeError, ValueError, KeyError, AttributeError, RecursionError) as exc:
        return None, ["malformed_sheet_or_dossier:" + type(exc).__name__]
