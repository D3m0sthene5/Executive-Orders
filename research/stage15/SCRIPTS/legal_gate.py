#!/usr/bin/env python3
"""Conservative gate for proposing future instrument legal determinations.
A passing record is REVIEW_READY, never an automated final legal conclusion.
All evidence predicates require explicit analyst-supplied backed records.
"""
from dataclasses import dataclass, field

@dataclass
class LegalProposal:
    proposed_status: str
    identity_verified: bool=False
    original_scope_complete: bool=False
    whole_ending_endpoint_proven: bool=False
    amendment_host_traced: bool=False
    amendment_present: bool=False
    saved_rights_traced: bool=False
    residual_scopes_traced: bool=False
    effective_date_checked: bool=False
    later_events_checked_to_cutoff: bool=False
    currently_operative_predicate: bool=False
    material_unresolved_scopes: bool=True
    source_independent_review_done: bool=False
    ever_operated_proven: bool=False
    first_cause_asserted: bool=False
    first_cause_precedes_formal_revocation_checked: bool=False
    first_cause_date_evidenced: bool=False
    first_cause_event_evidenced: bool=False
    original_signed_instrument_hash: str | None=None
    evidence_ids: list[str]=field(default_factory=list)

def assess(p:LegalProposal):
    errors=[]
    if p.proposed_status not in ('yes','no','indeterminate'):errors.append('invalid proposed_status enum')
    if p.proposed_status!='indeterminate':
        for k in ['identity_verified','effective_date_checked','later_events_checked_to_cutoff','source_independent_review_done']:
            if not getattr(p,k):errors.append('missing '+k)
        if not p.evidence_ids:errors.append('missing source-specific evidence IDs')
        if p.proposed_status=='yes' and not p.currently_operative_predicate:errors.append('YES requires a source-attributable operative predicate')
        if p.proposed_status=='no':
            if not (p.original_scope_complete or p.whole_ending_endpoint_proven):errors.append('NO requires whole original footprint or qualified whole-scope dispositive endpoint')
            if p.amendment_present and not p.amendment_host_traced:errors.append('amender host footprint unresolved')
            if not p.saved_rights_traced:errors.append('saved rights not mapped')
            if not p.residual_scopes_traced:errors.append('remaining scope/residual effect not traced')
            if p.material_unresolved_scopes:errors.append('material unresolved original/successor scope')
    if p.first_cause_asserted:
        if not p.ever_operated_proven:errors.append('first cessation claimed without prior operative episode')
        if not p.first_cause_precedes_formal_revocation_checked:errors.append('first cause timeline not distinguished from later cleanup revocation')
        if not p.first_cause_date_evidenced:errors.append('first cause date lacks primary evidence')
        if not p.first_cause_event_evidenced:errors.append('first cause event lacks primary evidence')
    return {'state':'READY_FOR_FURTHER_LEGAL_REVIEW' if not errors else 'HOLD','errors':errors,'automatic_status_promotion':False}

if __name__=='__main__':
    from pprint import pprint
    pprint(assess(LegalProposal(proposed_status='no')))
