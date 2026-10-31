"""Versioned research worksheets. Validation grants no evidentiary/legal approval."""
import copy
import hashlib
import json
from pathlib import Path

SCHEMA = "eo-early-source-worksheet/v2"
STATE = "research_only_never_certification"
BINDING = "eo-early-case-sources/v1"


def read_worksheet(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate worksheet key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def artifact(root, path, role, expected=None, **identity):
    """Hash actual bytes, retaining absent/conflicting declared custody separately."""
    root = Path(root).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Source path escapes repository")
    actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    return dict(role=role, path=path, expected_sha256=expected or None,
                sha256=actual, present=actual is not None, **identity)


def bind_case(case, metadata, sources):
    sources = sorted(sources, key=lambda x: json.dumps(x, sort_keys=True))
    body = dict(schema=BINDING, item_id=case["id"], candidate_id="LOC:" + case["id"],
                item_url=case["url"], candidate_version=digest({"metadata":metadata,"prior_candidate":case.get("prior_stage22_research_candidate",{})}), sources=sources)
    case["source_binding"] = dict(body, fingerprint=digest(body))
    return case


def health(binding):
    if not isinstance(binding, dict) or binding.get("schema") != BINDING:
        return "unknown_version"
    body = {k: v for k, v in binding.items() if k != "fingerprint"}
    if binding.get("fingerprint") != digest(body):
        return "conflicting_representation"
    sources = binding.get("sources")
    if not isinstance(sources, list):
        return "unknown_version"
    seen = {}
    for source in sources:
        if not isinstance(source, dict):
            return "unknown_version"
        key = (source.get("role"), source.get("path"))
        if key in seen and seen[key] != source:
            return "conflicting_representation"
        seen[key] = source
        if source.get("expected_sha256") and source.get("sha256") and source["expected_sha256"] != source["sha256"]:
            return "conflicting_representation"
    if any(not s.get("present") for s in sources):
        return "missing_source"
    if not binding.get("candidate_version") or not sources:
        return "unknown_version"
    return "unchanged_source"


def classify(item_id, entry, case):
    if not isinstance(entry, dict) or case is None:
        return "conflicting_representation"
    old = entry.get("source_binding")
    new = case.get("source_binding")
    if entry.get("candidate_id") != "LOC:" + item_id:
        return "conflicting_representation"
    if not isinstance(old, dict) or not isinstance(new, dict):
        return "unknown_version"
    for binding in (old, new):
        if binding.get("item_id") != item_id or binding.get("candidate_id") != "LOC:" + item_id or binding.get("item_url") != case["url"]:
            return "conflicting_representation"
    for binding in (old, new):
        status = health(binding)
        if status != "unchanged_source":
            return status
    return "unchanged_source" if old == new else "changed_source"


def export_worksheet(cases, notes, unverified_notes=()):
    by = {c["id"]: c for c in cases}
    if len(by) != len(cases) or set(notes) - set(by):
        raise ValueError("Duplicate or unknown catalog item")
    return dict(schema=SCHEMA, review_state=STATE,
                per_case={k: dict(candidate_id="LOC:" + k,
                                  source_binding=copy.deepcopy(by[k]["source_binding"]),
                                  notes=copy.deepcopy(v)) for k, v in notes.items()},
                unverified_notes=copy.deepcopy(list(unverified_notes)))


def validate_worksheet(document, cases):
    if not isinstance(document, dict) or document.get("review_state") != STATE or document.get("schema") not in (SCHEMA, "eo-early-source-worksheet/v1"):
        raise ValueError("Unrecognized research worksheet")
    entries = document.get("per_case")
    if not isinstance(entries, dict):
        raise ValueError("per_case must be an object")
    by = {c["id"]: c for c in cases}
    if len(by) != len(cases):
        raise ValueError("Duplicate current catalog item")
    result = []
    for item_id, entry in entries.items():
        legacy = document["schema"].endswith("/v1")
        status = "legacy_unverified" if legacy and item_id in by else classify(item_id, entry, by.get(item_id))
        notes = entry if legacy else entry.get("notes") if isinstance(entry, dict) else None
        if not isinstance(notes, dict):
            status = "conflicting_representation"
        result.append(dict(item_id=item_id, validation=status, entry=copy.deepcopy(entry),
                           notes=copy.deepcopy(notes), research_only=True))
    # Historical notes are never silently re-attached or upgraded on re-export.
    for old in document.get("unverified_notes", []):
        result.append(dict(item_id=old.get("item_id"), validation="legacy_unverified",
                           entry=copy.deepcopy(old), notes=None, research_only=True))
    return result


def validated_proposal(record):
    """Attribution is required; validation proves the binding, never the finding."""
    if record["validation"] != "unchanged_source":
        return None
    notes = record.get("notes") or {}
    proposal = notes.get("proposal")
    if not isinstance(proposal, dict) or proposal.get("disposition") not in (
            "recommend_inclusion", "recommend_exclusion", "possible_duplicate", "hold"):
        return None
    if not notes.get("reviewer") or not proposal.get("reason") or proposal.get("attribution") != "AI_research":
        return None
    return copy.deepcopy(proposal)
