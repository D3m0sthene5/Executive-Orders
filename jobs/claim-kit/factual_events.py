"""Expose independently reviewed NORTON facts solely as explicit later events.

No registry record is authored or reviewed here. The existing NORTON source,
answer and per-clause application gates are repeated against current bytes and
registry records. A fact never supplies an original, ending or current basis.
"""
from copy import deepcopy
import base64
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("claim_kit_norton_model", HERE.parent / "norton/model.py")
MODEL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MODEL)
MARKER = "norton_factual_event"
ROLE = "reviewed_factual_event"


def _registered(repo, kind, record, keys):
    """Require the unique exact durable record, not a fragment's assertion."""
    matches = []
    for path in sorted((Path(repo) / "research/readiness/factual").glob("*/" + kind + ".jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if all(item.get(k) == record.get(k) for k in keys):
                    matches.append(item)
    return len(matches) == 1 and matches[0] == record


def reviewed_events(repo, iid, data):
    """Return (event evidence, errors); unreviewed applications stay context only."""
    app = data.get("application", {})
    if app.get("state") not in ("ai_reviewed", "human_accepted"):
        return [], []
    errors = []
    question = data.get("question", {})
    answer = data.get("reviewed_answer") or {}
    answer_review = answer.get("review", {})
    original_answer = {k: v for k, v in answer.items()
                       if k not in ("review", "reviewer_type", "factual_review_status")}
    app_review = data.get("application_review") or {}
    evidence = data.get("reviewed_evidence", [])
    if data.get("legal_effect") != "unresolved" or app.get("instrument_id") != iid:
        errors.append("factual_application_identity_or_effect")
    try:
        if question.get("schema") != "norton-question/v1":
            errors.append("wrong_question_schema")
        if question.get("question_key") != MODEL.question_key(question):
            errors.append("factual_question_key_mismatch")
        if question.get("origin") not in ("owner_seeded", "machine_extracted"):
            errors.append("factual_question_origin_required")
        if original_answer.get("schema") != "norton-factual-answer/v1":
            errors.append("wrong_answer_schema")
        if (not isinstance(original_answer.get("answer"), str) or
                len(original_answer["answer"].strip()) < 40 or not original_answer.get("producer")):
            errors.append("factual_answer_missing")
        if not original_answer.get("id") or not app.get("id"):
            errors.append("missing_factual_record_id")
        errors += MODEL.application_errors(repo, question, app)
        errors += MODEL.review_errors(repo, original_answer, answer_review, "answer")
        errors += MODEL.review_errors(repo, app, app_review, "application")
        for kind, record, keys in (
            ("questions", question, ("question_key",)),
            ("answers", original_answer, ("id",)),
            ("applications", app, ("id",)),
            ("reviews", answer_review, ("record_kind", "record_id")),
            ("reviews", app_review, ("record_kind", "record_id")),
        ):
            if not _registered(repo, kind, record, keys):
                errors.append("factual_registry_mismatch:" + kind)
        if (app.get("answer_id") != original_answer.get("id") or
                original_answer.get("question_key") != question.get("question_key")):
            errors.append("factual_answer_application_mismatch")
        if (not isinstance(evidence, list) or not evidence or
                sorted(e.get("id", "") for e in evidence) != sorted(original_answer.get("evidence_ids", [])) or
                len({e.get("id") for e in evidence}) != len(evidence)):
            errors.append("factual_evidence_set_mismatch")
            evidence = []
        for record in evidence:
            errors += MODEL.evidence_errors(repo, question, record)
            if not _registered(repo, "evidence", record, ("id",)):
                errors.append("factual_registry_mismatch:evidence")
        if (app.get("state") == "human_accepted" and
                (app_review.get("reviewer_type") != "independent_human" or
                 answer_review.get("reviewer_type") != "independent_human")):
            errors.append("factual_human_tier_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append("factual_validation_error:" + type(exc).__name__)
    if errors:
        return [], sorted(set(errors))
    result = []
    for record in evidence:
        ident = "FACT:" + app["id"] + ":" + record["id"]
        metadata = {
            "id": ident, "application_id": app["id"], "answer_id": original_answer["id"],
            "evidence_id": record["id"], "question_key": question["question_key"],
            "instrument_id": iid, "scope_id": app["scope_id"],
            "event_date": record["event_date"], "event_kind": record["event_kind"],
            "entity_id": question["entity_id"], "legal_effect": "unresolved",
            "answer_sha256": MODEL.fingerprint(original_answer),
            "application_sha256": MODEL.fingerprint(app),
            "evidence_sha256": MODEL.fingerprint(record),
            "answer_review_sha256": MODEL.fingerprint(answer_review),
            "application_review_sha256": MODEL.fingerprint(app_review),
        }
        source = deepcopy(record["source"])
        source["local_path"] = source["raw_path"]
        source[MARKER] = metadata
        result.append({
            "id": ident, "role": ROLE, "scope_id": app["scope_id"],
            "instrument_id": iid, "actor_id": question["entity_id"],
            "mechanism": "factual_" + record["event_kind"],
            "event_date": record["event_date"], "legal_effect": "unresolved",
            "source": source, "text": record["text"],
            "char_start": record["char_start"], "char_end": record["char_end"],
            "notice": "Reviewed factual event only. Select explicitly as a later event; no legal effect or ending inferred.",
        })
    return result, []


def usage_errors(claim, dossier=None):
    """The role restriction survives both assembly and independent claim checking."""
    errors = []
    known = (dossier or {}).get("evidence", {})
    def walk(value, path=()):
        if isinstance(value, dict):
            marker = value.get(MARKER)
            ident = value.get("evidence_id", "")
            if value.get("evidence_id_encoding") == "base64url-utf8" and isinstance(ident, str):
                try:
                    ident = base64.urlsafe_b64decode(ident + "=" * (-len(ident) % 4)).decode("utf-8")
                except (ValueError, UnicodeError):
                    ident = ""
            if isinstance(ident, str) and ident.startswith("FACT:") and marker is None:
                errors.append("factual_event_marker_missing")
            if marker is not None:
                if not isinstance(marker, dict):
                    errors.append("invalid_factual_event_marker")
                    return
                # Only an event's source may carry a factual citation.
                allowed = (len(path) == 5 and path[0] == "operative_clauses" and
                           type(path[1]) is int and path[2] == "later_events" and
                           type(path[3]) is int and path[4] == "source")
                if not allowed:
                    errors.append("factual_event_cannot_supply_legal_effect:" + ".".join(map(str, path)))
                    return
                clause = claim["operative_clauses"][path[1]]
                event = clause["later_events"][path[3]]
                if (marker.get("instrument_id") != claim.get("instrument_id") or
                        marker.get("scope_id") != clause.get("scope_id") or
                        marker.get("legal_effect") != "unresolved"):
                    errors.append("factual_event_application_mismatch")
                if (event.get("effective_date") != marker.get("event_date") or
                        event.get("actor") != marker.get("entity_id") or
                        event.get("mechanism") != "factual_" + str(marker.get("event_kind"))):
                    errors.append("factual_event_date_or_meaning_changed")
                if dossier is not None:
                    record = known.get(marker.get("id"), {})
                    if record.get("role") != ROLE or record.get("source", {}).get(MARKER) != marker:
                        errors.append("factual_event_not_dossier_evidence")
            for key, child in value.items():
                if key != MARKER:
                    walk(child, path + (key,))
        elif isinstance(value, list):
            for n, child in enumerate(value):
                walk(child, path + (n,))
    walk(claim)
    return sorted(set(errors))


def claim_errors(claim, repo, dossier=None):
    """Revalidate every cited fact, even when no compiled dossier is available."""
    errors = usage_errors(claim, dossier)
    citations = []
    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get(MARKER), dict):
                citations.append(value)
            for key, child in value.items():
                if key != MARKER:
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(claim)
    if not citations:
        return errors
    try:
        registry = {}
        for kind in ("questions", "applications", "answers", "evidence", "reviews"):
            registry[kind] = []
            for path in sorted((Path(repo) / "research/readiness/factual").glob("*/" + kind + ".jsonl")):
                registry[kind].extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        def one(kind, **keys):
            found = [r for r in registry[kind] if all(r.get(k) == v for k, v in keys.items())]
            if len(found) != 1:
                raise ValueError("missing_or_duplicate_factual_record:" + kind)
            return found[0]
        checked, applications = {}, {}
        for cited in citations:
            m = cited[MARKER]
            aid = m.get("application_id")
            if aid not in checked:
                app = one("applications", id=aid)
                answer = one("answers", id=app.get("answer_id"))
                answer_review = one("reviews", record_kind="answer", record_id=answer.get("id"))
                data = {"application": app, "question": one("questions", question_key=app.get("question_key")),
                        "reviewed_answer": dict(answer, review=answer_review),
                        "application_review": one("reviews", record_kind="application", record_id=aid),
                        "reviewed_evidence": [one("evidence", id=eid) for eid in answer.get("evidence_ids", [])],
                        "legal_effect": "unresolved"}
                records, failures = reviewed_events(repo, claim.get("instrument_id"), data)
                errors.extend(failures)
                checked[aid] = {r["id"]: r for r in records}
                applications[aid] = app
            record = checked[aid].get(m.get("id"))
            if not record:
                errors.append("factual_event_no_current_reviewed_record")
                continue
            expected = dict(record["source"], quote=record["text"],
                            char_start=record["char_start"], char_end=record["char_end"])
            if any(cited.get(key) != value for key, value in expected.items()):
                errors.append("factual_event_citation_changed")
            # A scope label alone cannot carry applicability across a changed
            # clause boundary or quotation. Re-segmentation needs a new review.
            clauses = [c for c in claim.get("operative_clauses", [])
                       if isinstance(c, dict) and c.get("scope_id") == m.get("scope_id")]
            reviewed_clause = applications[aid]["clause_evidence"]
            expected_clause_source = dict(reviewed_clause["source"], quote=reviewed_clause["text"],
                                          char_start=reviewed_clause["char_start"], char_end=reviewed_clause["char_end"])
            identity_keys = ("sha256", "local_file_sha256", "text_sha256", "text_path",
                             "char_start", "char_end", "quote")
            if (len(clauses) != 1 or clauses[0].get("original_operative_text") != reviewed_clause["text"] or
                    any(clauses[0].get("original_source", {}).get(k) != expected_clause_source.get(k)
                        for k in identity_keys)):
                errors.append("factual_event_clause_evidence_mismatch")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append("factual_claim_validation_error:" + type(exc).__name__)
    return sorted(set(errors))
