"""Preserve initial producer artifacts; correct the independently rejected cases."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent
ARM = PRODUCER.parent
REPO = HERE.parents[7]
spec = importlib.util.spec_from_file_location('existing_assembler', REPO/'jobs/claim-kit/assemble.py')
assembler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembler)


def dump(name, obj):
    p = HERE/name
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def overrides(d, spans):
    return [{'scope_id':d['instrument_id']+'#'+label,'source_id':d['original_source_id'],
             'char_start':start,'char_end':end,
             'reason':'Separate one-time legal effectiveness, congressional transmission and Federal Register publication from continuing authority; distinct commands require distinct supported first ends.'}
            for label,start,end in spans]


def blank_row(scope):
    return {'scope_id':scope,'state':None,'end_id':None,'effective_date':None,
            'effective_date_confirmed':False,'current_basis_id':None,'current_legal_basis':'',
            'checked_through':None,'later_event_ids':[],'later_events':[],
            'reason':'No exact first-end approval. The previously conflated dates are withdrawn; see correction rationale and shared research tasks.'}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if (HERE/'OUTCOMES.json').exists():
        raise RuntimeError('Preserve this correction attempt; do not overwrite it.')
    initial_files = [p for p in PRODUCER.rglob('*') if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts]
    manifest = {str(p.relative_to(PRODUCER)):hashlib.sha256(p.read_bytes()).hexdigest() for p in initial_files}
    review = json.loads((ARM/'review/OUTCOMES.json').read_text(encoding='utf-8'))
    review_by_id = {x['instrument_id']:x for x in review['members']}
    audit, outcomes, claims, tasks = [],[],[],[]
    for n in [12720,12813,12734,12817,12696,12722]:
        ident = f'EO:{n}'
        d = json.loads((ARM/'dossiers'/f'EO_{n}.json').read_text(encoding='utf-8'))
        s = json.loads((PRODUCER/'decisions'/f'EO_{n}.json').read_text(encoding='utf-8'))
        old = deepcopy(s)
        if n in [12813,12734,12817]:
            s['approved'] = False
            s['search_ids'] = []
            s['conflict_resolutions'] = {}
            s['correction_review_codes'] = review_by_id[ident]['required_correction_codes']
            s['source_review_method'] += ' Correction accepts the independent AI review objections; no missing fact is inferred from a publication issue or later revocation.'
            if n == 12813:
                s['clauses'] = [blank_row(c['scope_id']) for c in old['clauses']]
                s['unresolved_material_gaps'] = ['EO12815 substitutes December 31, 1992 into the original not-later-than clause; this proves an outer termination bound, not an exact first cessation for all eight functions. Actual cessation evidence is unheld.']
                s['research_rationale'] = 'Withdraw the exact December 31, 1992 first-end assignments. The independent review correctly distinguishes the not-later-than bound from an actual termination date. EO12815 changes only the date in EO12813 section 4(b), retaining the qualifier. EO12869 formally revokes effective September 30, 1993 but does not supply the earlier actual terminal date. All eight Commission-dependent scopes remain in the inventory; no later formal-revocation date replaces an unknown earlier first end. Accrued travel and procurement liabilities remain residual questions, not evidence of a new independent Commission mandate.'
                s['known_legal_bounds_and_events'] = [{'kind':'termination_outer_bound','date':'1992-12-31','evidence_id':'ACTOR_TEXT:EO:12815','exact_first_end':False}, {'kind':'later_formal_revocation','date':'1993-09-30','evidence_id':'ACTOR_TEXT:EO:12869','exact_first_end':False}]
                tasks.append({'task_id':'A-correction-12813-actual-cessation','instrument_id':ident,'type':'shared_legal_fact_and_acquisition','required_sources':['Commission charter and amendments','AID/State Commission termination notice, final activity record, meeting/closeout record or authoritative administrative determination','Federal Advisory Committee Act termination records'], 'required_fact':'Establish actual termination/first cessation of each Commission function at or before December 31, 1992, including any earlier termination; distinguish legal termination from merely finishing advisory work.','held_evidence':['ORIGINAL:EO:12813','ACTOR_TEXT:EO:12815','ACTOR_TEXT:EO:12869'],'prohibited_inference':'Do not convert not-later-than into an exact date or substitute the 1993 formal revocation as the first end.','exhaustion_asserted':False})
            elif n == 12734:
                t = d['evidence'][d['original_source_id']]['text']
                start = t.index('This order is effective immediately')
                trans = t.index('shall be transmitted',start)
                pub = t.index('published in the Federal Register',trans)
                stop = pub + len('published in the Federal Register.')
                s['inventory_overrides'] = overrides(d,[('construction-authority',707,start-1),('initial-effectiveness',start,trans),('congress-transmission',trans,pub),('register-publication',pub,stop)])
                inventory,_,errors = assembler.derive_inventory(d,s['inventory_overrides'])
                if errors:raise ValueError(errors)
                s['clauses'] = [blank_row(c['scope_id']) for c in inventory]
                s['inventory_confirmed'] = True
                s['unresolved_material_gaps'] = ['Congressional-transmission actual completion/first-end date is unheld. The Federal Register issue date November 19, 1990 establishes a completion bound, not independently the actual first publication/completion timing for an exact-date schema.','The prior whole scope incorrectly assigned later 2004 revocation as the first end of notice commands. Distinct scopes are now retained without guessed exact dates.']
                s['research_rationale'] = 'Withdraw the complete exact-date claim. Separate the construction invocation from immediate-effectiveness, congressional-transmission and publication commands. EO13350 expressly revokes prospective construction authority effective July 30, 2004 at 12:01 a.m. EDT. That act does not establish the original notice commands first ceased in 2004. The printed November 19, 1990 Federal Register representation supplies publication evidence and a latest-completion bound, while exact first completion and congressional transmittal remain unproved. Savings retain accrued actions and duties rather than authorizing a new construction program.'
                s['known_legal_bounds_and_events'] = [{'kind':'prospective_construction_authority_revocation','date':'2004-07-30','time':'00:01 EDT','evidence_id':'ACTOR_TEXT:EO:13350','all_original_commands_first_end':False},{'kind':'publication_completion_bound','not_later_than':'1990-11-19','evidence_id':d['original_source_id'],'exact_first_end':False}]
                tasks.append({'task_id':'A-correction-12734-notice-completion','instrument_id':ident,'type':'shared_legal_fact_and_acquisition','required_sources':['Congressional receipt/transmittal record for EO12734','Original Federal Register filing, public-inspection and publication chronology; assess actual completion of the commanded publication'], 'required_fact':'Establish actual first completion/end dates separately for congressional transmission and publication; distinguish original effectiveness from continued emergency-construction authority.','known_bound':'Federal Register issue November 19, 1990','prohibited_inference':'Do not assign July 30, 2004 to historical notice commands or invent transmittal from signing/publication.','exhaustion_asserted':False})
            else:
                t = d['evidence'][d['original_source_id']]['text']
                base = deepcopy(old['inventory_overrides'][:-1])
                a = t.index('(a) This order is effective immediately.',6309)
                b = t.index('(b) This order shall be transm',a)
                pub = t.index('published in the',b)
                stop = t.index('Federal Register.',pub)+len('Federal Register.')
                base += overrides(d,[('sec8-a',a,b-1),('sec8-b-congress-transmission',b,pub),('sec8-b-register-publication',pub,stop)])
                s['inventory_overrides'] = base
                inventory,_,errors = assembler.derive_inventory(d,base)
                if errors:raise ValueError(errors)
                s['clauses'] = [blank_row(c['scope_id']) for c in inventory]
                s['inventory_confirmed'] = True
                s['unresolved_material_gaps'] = ['Congressional-transmission actual completion date is unheld. The October 23, 1992 Federal Register issue establishes a publication-completion bound, not the entire exact first-end chronology.','Contrary research lead: UNSCR1483 paragraphs 10, 16-17 and 23, and OFAC 31 CFR 575.533 effective May 23, 2003 may affect the scope of EO12817 implementation, transfers and UN repayments. Full attributable sources and a clause-level legal analysis are required. Restoration of Resolution778 funds is expressly contemplated and does not prove automatic prior cessation or account exhaustion.']
                s['research_rationale'] = 'Withdraw the complete exact-date claim and split section 8(a) effectiveness from section 8(b) congressional transmission and publication. EO13350 expressly revokes EO12817 effective July 30, 2004 at 12:01 a.m. EDT, but that does not give first-end dates for historical notice duties or prove no earlier partial legal change. Preserve the unresolved contrary leads to UNSCR1483 and OFAC575.533 rather than infer a May23,2003 whole ending. Resolution778 fund restoration/repaid assets remain expressly contemplated. No completion of every Treasury determination, transfer, investment, repayment or account is asserted. Sections4/7 and EO13350 accrued savings remain separately relevant.'
                s['known_legal_bounds_and_events'] = [{'kind':'express_revocation','date':'2004-07-30','time':'00:01 EDT','evidence_id':'ACTOR_TEXT:EO:13350','all_original_commands_first_end':False},{'kind':'publication_completion_bound','not_later_than':'1992-10-23','evidence_id':d['original_source_id'],'exact_first_end':False}]
                tasks.append({'task_id':'A-correction-12817-notice-completion','instrument_id':ident,'type':'shared_legal_fact_and_acquisition','required_sources':['Congressional receipt/transmittal record for EO12817','Original Federal Register filing/public-inspection/publication chronology'], 'required_fact':'Establish actual first completion dates for the separately inventoried notice commands; do not merge original effectiveness with later revocation.','known_bound':'Federal Register issue October 23, 1992','prohibited_inference':'No 2004 first-end assignment for publication/transmittal and no invented congressional completion.','exhaustion_asserted':False})
                tasks.append({'task_id':'A-correction-12817-2003-partial-scope','instrument_id':ident,'type':'shared_contrary_evidence_acquisition_and_analysis','source_leads':['UN Security Council Resolution1483 paragraphs10,16-17,23','OFAC 31 CFR575.533 rule effective2003-05-23; full operative section, exceptions and source notice'], 'required_fact':'Determine clause-specific legal effect on EO12817 Treasury implementation, conditional financial-institution transfers, Federal Reserve holding/investment/transfers, UN repayments and good-faith/accrued protections. Preserve contemplated restoration of Resolution778 funds and analyze its effect.','prohibited_inference':'These are unverified research leads, not an automatic May23,2003 whole-order end, proof that all assets were exhausted, or a substitute for exact earlier first ends.','exhaustion_asserted':False})
            s['savings']['state'] = None
            s['earlier_endings_and_partial_scope'] = 'The initial exact-date approval is withdrawn. Preserve supported formal revocation or outer bounds only in auxiliary known_legal_bounds_and_events; exact first-end fields are blank until the listed tasks are resolved.'
        dump(f'decisions/EO_{n}.json',s)
        claim,errors = assembler.assemble(s,d,REPO)
        check_errors = assembler.check_claim(claim,REPO,d) if claim else None
        if n == 12720:
            assert not errors and not check_errors
            assert assembler.canonical_sha(claim) == review_by_id[ident]['claim_sha256']
            claims.append(claim)
        else:
            assert claim is None and s['approved'] is False
        audit.append({'instrument_id':ident,'sheet':s,'claim':claim,'errors':errors,'check_claim_errors':check_errors,'claim_sha256':assembler.canonical_sha(claim) if claim else None})
        outcomes.append({'instrument_id':ident,'outcome':'accepted_exact_proposal_retained' if claim else 'unable','approved':s['approved'],'assembler_pass':claim is not None,'assembler_errors':errors,'review_basis':review_by_id[ident]['decision'],'unresolved_material_gaps':s['unresolved_material_gaps']})
        print(ident,'retained' if claim else 'unable',len(errors))
    # Carry forward precise tasks for the two originally blocked controls.
    tasks.extend(json.loads((PRODUCER/'ACQUISITION_TASKS.json').read_text(encoding='utf-8')))
    dump('ACQUISITION_TASKS.json',tasks)
    dump('ASSEMBLER_AUDIT.json',audit)
    dump('OUTCOMES.json',{'schema':'matched-producer-correction/v1','arm':'A','phase':'correction-v1','all_six_retained':True,'counts':{'frozen_members':6,'retained_independently_accepted_exact_proposals':1,'unable':5,'withdrawn_initial_approvals':3,'assembler_attempts':6,'unexpected_assembly_failures':0},'members':outcomes,'canonical_writes':0,'human_certifications':0})
    (HERE/'assembled-proposals.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in claims),encoding='utf-8')
    assert all(hashlib.sha256((PRODUCER/name).read_bytes()).hexdigest()==sha for name,sha in manifest.items())
    dump('INITIAL_ARTIFACT_PRESERVATION.json',{'all_preserved':True,'initial_file_sha256':manifest})
    dump('CORRECTION_METRICS.json',{'start_utc':'2026-10-18T13:43:18.390Z','end_of_decision_correction_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds_decision_correction':(datetime.now(timezone.utc)-datetime.fromisoformat('2026-10-18T13:43:18.390+00:00')).total_seconds(),'active_seconds':None,'assembler_calls':6,'check_claim_calls':1,'initial_artifacts_preserved':True,'network_fetches':0,'note':'Actual rollout usage/tool-wrapper counts will be exported separately at the final telemetry snapshot.'})


if __name__=='__main__':
    main()
