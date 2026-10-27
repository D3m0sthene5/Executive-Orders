"""Structural gate for complete whole-lifecycle claims and independent reviews.

Passing this gate means a dossier has the required evidence fields and a
recorded independent review assertion. It does not prove the legal judgment;
source-check quality remains a human responsibility.
"""

import hashlib
import json
from datetime import date
from urllib.parse import urlparse

LEGAL_CUTOFF="2026-10-14"

def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))


def claim_sha(claim):
    return hashlib.sha256(canonical(claim).encode("utf-8")).hexdigest()


def source_ok(ref):
    if not isinstance(ref,dict):
        return False
    url=ref.get("url")
    parsed=urlparse(url) if isinstance(url,str) else None
    online=bool(parsed and parsed.scheme=="https" and parsed.netloc)
    offline=bool(ref.get("archival_id") and isinstance(ref.get("local_file_sha256"),str) and len(ref["local_file_sha256"])==64 and all(c in "0123456789abcdef" for c in ref["local_file_sha256"].lower()))
    return bool(ref.get("page_or_item") and (online or offline) and (ref.get("sha256") or ref.get("archival_id") or offline))


def exact_date(value):
    if not isinstance(value,str):
        return False
    try:
        return date.fromisoformat(value).isoformat()==value
    except ValueError:
        return False


def validate_claim(claim, expected_status=None):
    errors=[]
    if claim.get("schema")!="eo-lifecycle-claim/v1":
        errors.append("schema")
    if not isinstance(claim.get("instrument_id"),str) or not claim["instrument_id"].startswith("EO:"):
        errors.append("instrument_id")
    status=claim.get("whole_order_status")
    if status not in ("yes","no") or (expected_status and status!=expected_status):
        errors.append("whole_order_status_mismatch")
    if not source_ok(claim.get("original_representation")):
        errors.append("original_representation_provenance")
    clauses=claim.get("operative_clauses")
    if not isinstance(clauses,list) or not clauses:
        return errors+["operative_clauses_empty"]
    scope_ids=set()
    continuing=0
    end_dates=[]
    for n,clause in enumerate(clauses):
        if not isinstance(clause,dict):
            errors.append(f"clause_{n}_not_object")
            continue
        scope=clause.get("scope_id")
        if not isinstance(scope,str) or not scope.strip() or scope in scope_ids:
            errors.append(f"clause_{n}_scope_id")
        scope_ids.add(scope)
        if not clause.get("original_operative_text") or not source_ok(clause.get("original_source")):
            errors.append(f"clause_{n}_original_text_or_source")
        state=clause.get("state_at_cutoff")
        if state=="operative":
            continuing+=1
            pred=clause.get("current_predicate")
            if not isinstance(pred,dict) or not pred.get("legal_basis") or not source_ok(pred.get("source")) or pred.get("checked_through")!=LEGAL_CUTOFF:
                errors.append(f"clause_{n}_current_predicate")
        elif state in ("terminated","never_activated"):
            end=clause.get("first_end")
            if not isinstance(end,dict) or not exact_date(end.get("date")) or end.get("date", "9999")>LEGAL_CUTOFF or not end.get("actor") or not end.get("mechanism") or not source_ok(end.get("source")):
                errors.append(f"clause_{n}_first_end")
            else:
                end_dates.append(end["date"])
        else:
            errors.append(f"clause_{n}_state")
        events=clause.get("later_events")
        if not isinstance(events,list):
            errors.append(f"clause_{n}_later_events_list")
        elif any(not isinstance(event,dict) or not exact_date(event.get("effective_date")) or event.get("effective_date", "9999")>LEGAL_CUTOFF or not event.get("actor") or not event.get("mechanism") or not source_ok(event.get("source")) for event in events):
            errors.append(f"clause_{n}_later_event_evidence")
    if status=="no":
        if continuing:
            errors.append("no_with_continuing_clause")
        whole=claim.get("whole_order_end")
        if not isinstance(whole,dict) or not exact_date(whole.get("date")) or whole.get("date", "9999")>LEGAL_CUTOFF or not whole.get("mechanism") or not whole.get("actor") or not source_ok(whole.get("source")):
            errors.append("whole_order_end_evidence")
        elif end_dates and whole["date"] != max(end_dates):
            errors.append("whole_order_end_not_last_clause_end")
    elif status=="yes":
        if not continuing:
            errors.append("yes_without_continuing_clause")
        if claim.get("whole_order_end") is not None:
            errors.append("yes_must_not_assert_whole_end")
    residual=claim.get("savings_residuals")
    if not isinstance(residual,dict) or residual.get("state") not in ("none_after_bounded_search","continuing_independent","transferred_or_accrued") or not residual.get("reason") or not source_ok(residual.get("source")):
        errors.append("savings_residuals_evidence")
    search=claim.get("later_source_search")
    if not isinstance(search,list) or not search or any(not isinstance(x,dict) or not x.get("repository") or not x.get("query_or_scope") or not exact_date(x.get("checked_on")) for x in search):
        errors.append("bounded_later_search")
    if claim.get("unresolved_material_gaps") not in ([],):
        errors.append("unresolved_material_gaps")
    if not isinstance(claim.get("research_rationale"),str) or len(claim["research_rationale"].strip())<40:
        errors.append("research_rationale")
    return errors


def validate_review(review,claim):
    errors=[]
    if review.get("schema")!="eo-lifecycle-review/v1":
        errors.append("schema")
    if review.get("claim_sha256")!=claim_sha(claim):
        errors.append("stale_claim_fingerprint")
    if review.get("instrument_id")!=claim.get("instrument_id"):
        errors.append("instrument_id")
    if review.get("decision")!="uphold":
        errors.append("review_not_upheld")
    if not isinstance(review.get("reviewer"),str) or len(review["reviewer"].strip())<3 or review.get("reviewer_role")!="independent_human":
        errors.append("independent_human_reviewer")
    if not isinstance(review.get("rationale"),str) or len(review["rationale"].strip())<40:
        errors.append("review_rationale")
    checked=review.get("checked_source_urls")
    archived=review.get("checked_archival_items",[])
    if not isinstance(checked,list) or not all(isinstance(u,str) and u.startswith("https://") for u in checked) or not isinstance(archived,list) or not all(isinstance(x,str) and x.strip() for x in archived) or not (checked or archived):
        errors.append("checked_sources")
    else:
        cited=[claim.get("original_representation"),claim.get("savings_residuals",{}).get("source")]
        whole=claim.get("whole_order_end")
        if isinstance(whole,dict):
            cited.append(whole.get("source"))
        for note in claim.get("source_notes",[]):
            if isinstance(note,dict):
                cited.append(note.get("source"))
        for clause in claim.get("operative_clauses",[]):
            if not isinstance(clause,dict):
                continue
            cited.append(clause.get("original_source"))
            for field in ("first_end","current_predicate"):
                item=clause.get(field)
                if isinstance(item,dict):
                    cited.append(item.get("source"))
            for item in clause.get("later_events",[]):
                if isinstance(item,dict):
                    cited.append(item.get("source"))
        if any(isinstance(source,dict) and not ((source.get("url") in checked) or (source.get("archival_id") in archived)) for source in cited):
            errors.append("unchecked_cited_source")
    if not exact_date(review.get("reviewed_on")):
        errors.append("review_date")
    return errors
