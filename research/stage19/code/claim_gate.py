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
SCHEMA_V1="eo-lifecycle-claim/v1"
# Schema v2 (owner ruling R2, 2026-11-06; Kean D-20261106-justinian-r2) adopts the legal first-ending
# interval contract alongside immutable v1. Vocabularies come from the immutable Stage 15 codebook
# (research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json): first_cause_type verbatim, and
# date_kind is the codebook's historical_evidence_dates restricted to the kinds a first end can take.
SCHEMA_V2="eo-lifecycle-claim/v2"
DATE_KINDS=("exact","not_later_than","interval")
FIRST_CAUSES=("under_original_terms","later_amendment_imposed_condition","later_presidential","legislative",
              "regulatory","judicial","completion_of_task","never_activated","unresolved")
MECHANISMS=("express_revocation","express_supersession","implied_supersession","amendment",
            "expiration_by_own_terms","condition_or_event_occurred","task_completed","body_abolished",
            "statutory_termination","authority_repealed_or_lapsed","judicial_invalidation","regulatory_action",
            "never_activated","other")
DERIVED_FIELDS=("formal_revocation_after_earlier_cessation",)

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


def status_contested(claim, expected_status=None):
    """Owner ruling R5 (2026-11-06): a claim may assert a status that disagrees with the provisional ledger.

    This is a contest, not a gate failure: the tracker records blocker STATUS_CONTESTED and lists the
    claim in CONTESTED.csv; the ledger changes only through an owner-merged pull request.
    """
    status=claim.get("whole_order_status") if isinstance(claim,dict) else None
    return bool(expected_status in ("yes","no") and status in ("yes","no") and status!=expected_status)


def end_window(end, v2):
    """(earliest, latest, established) of a first or whole-order end that passed its checks."""
    if not v2 or end.get("date_kind")=="exact":
        return end["date"], end["date"], True
    if end["date_kind"]=="interval":
        return end["earliest"], end["latest"], True
    return None, end["date"], False


def v2_end_errors(end, label):
    """Schema v2 timing, cause and mechanism of one first end (or of the whole-order end)."""
    errors=[]
    kind=end.get("date_kind")
    cause=end.get("first_cause")
    if kind not in DATE_KINDS:
        return [f"{label}_date_kind"]
    if cause not in FIRST_CAUSES:
        errors.append(f"{label}_first_cause")
    if kind=="exact":
        if not exact_date(end.get("date")) or end["date"]>LEGAL_CUTOFF:
            errors.append(f"{label}_date")
    elif kind=="interval":
        lo,hi=end.get("earliest"),end.get("latest")
        if "date" in end or not exact_date(lo) or not exact_date(hi) or not lo<hi or hi>LEGAL_CUTOFF:
            # A one-day interval must be written as exact (contract proposal); never a midpoint in "date".
            errors.append(f"{label}_interval")
    elif not exact_date(end.get("date")) or end["date"]>LEGAL_CUTOFF:
        errors.append(f"{label}_date")
    # A latest-possible end without affirmative evidence of the ending event is not a first end:
    # not_later_than is accepted only while the first cause is unresolved, and only then.
    if (kind=="not_later_than")!=(cause=="unresolved"):
        errors.append(f"{label}_not_later_than_requires_unresolved_cause")
    if end.get("mechanism") not in MECHANISMS:
        errors.append(f"{label}_mechanism")
    note=end.get("mechanism_note")
    if note is not None and not isinstance(note,str) or (end.get("mechanism")=="other" and not (note or "").strip()):
        errors.append(f"{label}_mechanism_note")
    if not end.get("actor") or not source_ok(end.get("source")):
        errors.append(f"{label}_actor_or_source")
    return errors


def derived(claim):
    """Fields the gate computes and a producer never fills (schema v2).

    formal_revocation_after_earlier_cessation: True when the order's formal disposition (for example a
    later cleanup revocation) is dated after an established whole-order end; False when it is not; None
    when there is no formal disposition or the whole-order end is only bounded (not_later_than).
    """
    out={"formal_revocation_after_earlier_cessation":None}
    if not isinstance(claim,dict) or claim.get("schema")!=SCHEMA_V2:
        return out
    disposition,whole=claim.get("formal_disposition"),claim.get("whole_order_end")
    if not isinstance(disposition,dict) or not exact_date(disposition.get("date")) or not isinstance(whole,dict):
        return out
    if whole.get("date_kind")=="exact" and exact_date(whole.get("date")):
        out["formal_revocation_after_earlier_cessation"]=whole["date"]<disposition["date"]
    elif whole.get("date_kind")=="interval" and exact_date(whole.get("latest")):
        out["formal_revocation_after_earlier_cessation"]=whole["latest"]<disposition["date"]
    return out


def validate_claim(claim, expected_status=None):
    errors=[]
    v2=claim.get("schema")==SCHEMA_V2
    if claim.get("schema") not in (SCHEMA_V1,SCHEMA_V2):
        errors.append("schema")
    if not isinstance(claim.get("instrument_id"),str) or not claim["instrument_id"].startswith("EO:"):
        errors.append("instrument_id")
    status=claim.get("whole_order_status")
    # R5: disagreement with the ledger is a contest (status_contested), not a structural error.
    if status not in ("yes","no"):
        errors.append("whole_order_status_mismatch")
    if not source_ok(claim.get("original_representation")):
        errors.append("original_representation_provenance")
    clauses=claim.get("operative_clauses")
    if not isinstance(clauses,list) or not clauses:
        return errors+["operative_clauses_empty"]
    scope_ids=set()
    continuing=0
    end_dates=[]
    windows=[]
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
            if v2:
                problems=v2_end_errors(end,f"clause_{n}_first_end") if isinstance(end,dict) else [f"clause_{n}_first_end"]
                errors+=problems
                if not problems:
                    windows.append(end_window(end,True))
            elif not isinstance(end,dict) or not exact_date(end.get("date")) or end.get("date", "9999")>LEGAL_CUTOFF or not end.get("actor") or not end.get("mechanism") or not source_ok(end.get("source")):
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
    if status=="no" and v2:
        if continuing:
            errors.append("no_with_continuing_clause")
        whole=claim.get("whole_order_end")
        problems=v2_end_errors(whole,"whole_order_end") if isinstance(whole,dict) else ["whole_order_end_evidence"]
        errors+=problems
        if not problems and windows:
            # whole_order_end is the LATEST clause first end (not the first moment the order lost force):
            # [max(clause earliest), max(clause latest)], bounded only if any clause is bounded.
            lo,hi,est=end_window(whole,True)
            latest=max(w[1] for w in windows)
            if any(not w[2] for w in windows):
                want=("not_later_than",None,latest)
            elif all(w[0]==w[1] for w in windows):
                want=("exact",latest,latest)
            else:
                want=("interval",max(w[0] for w in windows),latest)
            if (whole.get("date_kind"),lo if whole.get("date_kind")!="not_later_than" else None,hi)!=want:
                errors.append("whole_order_end_not_last_clause_end")
    elif status=="no":
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
    if v2:
        errors+=v2_order_errors(claim, windows)
    return errors


def v2_order_errors(claim, windows):
    """Order-level formal disposition and the derived fields (schema v2)."""
    errors=[]
    disposition=claim.get("formal_disposition")
    if disposition is not None:
        if (not isinstance(disposition,dict) or not isinstance(disposition.get("instrument"),str)
                or not disposition["instrument"].strip() or not exact_date(disposition.get("date"))
                or disposition["date"]>LEGAL_CUTOFF
                or ("source" in disposition and not source_ok(disposition["source"]))):
            errors.append("formal_disposition")
    bounded=[w for w in windows if not w[2]]
    if bounded:
        # A not_later_than bound needs the instrument that formally disposed of the order no later than it.
        if not isinstance(disposition,dict) or not exact_date(disposition.get("date")):
            errors.append("not_later_than_without_formal_disposition")
        elif any(w[1]>disposition["date"] for w in bounded):
            errors.append("not_later_than_after_formal_disposition")
    for field in DERIVED_FIELDS:
        if field in claim:
            errors.append(f"derived_field_hand_filled:{field}")
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
        disposition=claim.get("formal_disposition")
        if isinstance(disposition,dict) and "source" in disposition:
            cited.append(disposition.get("source"))
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
