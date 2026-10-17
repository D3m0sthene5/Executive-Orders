"""Stage 16 legal and evidence policy, executed by build.py, not an advisory file.

The legacy v2.0.0 statuses are frozen in a separate ledger column. A v3.0.0
adjudication is a separate, sourced legal decision. A report may display old
results descriptively but never silently equate them to validated v3.0.0 results.
"""
from dataclasses import dataclass
from typing import Optional

CUTOFF='2026-10-14'
V3='3.0.0-research'
STATE={'never_operative','operative','partially_operative','dormant','terminated','revived','indeterminate'}
ATTR={'original_EO_direct','host_incorporated_from_EO','independent_successor','later_saving_clause','historic_disposition','unresolved'}
CAUSE={'original_term','subsequent_presidential','later_amendment_condition','legislative','judicial','regulatory','performance_complete','unknown','never_operated'}

@dataclass
class Review:
    document_verified: bool=False
    whole_original_scope_verified: bool=False
    later_events_checked: bool=False
    saved_rights_checked: bool=False
    host_amendment_checked: bool=False
    residual_checked: bool=False
    unresolved_material_scope: bool=True
    current_predicate_verified: bool=False
    original_evidence_ref: Optional[str]=None
    independent_review: bool=False
    endorsement: str='first_pass'

class DecisionRejected(Exception): pass

def authorize_status(status: str, p:Review, *, certified=False):
    """No persisted research classification without the required scoped evidence.

    certified=True additionally requires independent review. Routine source-based
    research is retained as a first-pass finding and never claimed as certified.
    """
    if status not in {'yes','no','indeterminate'}:raise DecisionRejected('invalid status')
    if status=='indeterminate':return 'held'
    checks=[('document_verified',p.document_verified),('original_evidence_ref',bool(p.original_evidence_ref)),('later_events_checked',p.later_events_checked)]
    if status=='yes': checks.extend([('current_predicate_verified',p.current_predicate_verified),('host_amendment_checked',p.host_amendment_checked)])
    else:checks.extend([('whole_original_scope_verified',p.whole_original_scope_verified),('saved_rights_checked',p.saved_rights_checked),('residual_checked',p.residual_checked),('host_amendment_checked',p.host_amendment_checked),('no_unresolved_material_scope',not p.unresolved_material_scope)])
    if certified:checks.append(('independent_review',p.independent_review))
    failed=[x for x,v in checks if not v]
    if failed:raise DecisionRejected('MISSING:'+','.join(failed))
    return 'certified' if certified else 'source_reviewed_not_independently_certified'

def authorize_first_cause(*,ever_operative,source_for_episode,source_for_cause,first_date_type,alternative_earlier_end_excluded,successor_not_only_latest_bound):
    checks={'ever_operative':ever_operative,'source_for_episode':bool(source_for_episode),'source_for_cause':bool(source_for_cause),'first_date_type':first_date_type=='exact','earlier_end_excluded':alternative_earlier_end_excluded,'not_a_cleanup_bound':successor_not_only_latest_bound}
    failed=[x for x,v in checks.items() if not v]
    if failed:raise DecisionRejected('CAUSE_MISSING:'+','.join(failed))
    return True

@dataclass
class SharedSourceInference:
    """A candidate for family expansion, NOT a legal determination.

    Root inference gates address the seven Stage15 shared-error families.
    """
    original_all_clauses_known: bool=False
    surviving_independent_clause_excluded: bool=False
    savings_and_rights_checked: bool=False
    exact_successor_scope_proved: bool=False
    host_amendments_traced: bool=False
    grant_exercise_proved_if_relied_on: bool=False
    residual_institutional_authority_traced: bool=False
    continuing_duties_traced: bool=False
    primary_text_available: bool=False
    evidence_of_actual_cessation: bool=False
    first_cause_separately_evidenced: bool=False
    first_cause_claimed: bool=False
    source_is_only_editorial_silence: bool=False


def assess_mass_inference(x:SharedSourceInference):
    missing=[]
    for flag in ('original_all_clauses_known','surviving_independent_clause_excluded','savings_and_rights_checked',
                 'exact_successor_scope_proved','host_amendments_traced',
                 'grant_exercise_proved_if_relied_on','residual_institutional_authority_traced',
                 'continuing_duties_traced','primary_text_available','evidence_of_actual_cessation'):
        if not getattr(x,flag):missing.append(flag)
    if x.source_is_only_editorial_silence:missing.append('editorial_silence_is_not_evidence')
    if x.first_cause_claimed and not x.first_cause_separately_evidenced:missing.append('first_cause_separate_from_successor_revocation')
    return {'family_rule_usable_for_source_based_review':not missing,'missing':missing,'automatically_classify_predecessors':False}
