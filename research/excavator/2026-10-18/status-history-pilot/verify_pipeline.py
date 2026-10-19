"""Reproduce the real claim-kit build consumer on its small integration corpus.

This validates pointer propagation, blank-decision refusal and legal-state
isolation. It is not a legal experiment or a corpus-cost estimate.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
from test_build import BuildIntegrationTests,write_json,write_jsonl,read_jsonl

def main():
    start=time.monotonic();case=BuildIntegrationTests();case.setUp()
    try:
        fragments=[]
        for iid in ('EO:1','EO:4'):
            p=case.repo/'jobs/status-history/output/histories'/('EO_'+iid[3:]+'.json')
            write_json(p,{'schema':'eo-status-history/v1','instrument_id':iid,
                          'current_legal_status':None,'accepted_legal_intervals':[]})
            fragments.append({'instrument_id':iid,'kind':'status_history_candidates',
                'data':{'history_path':p.relative_to(case.repo).as_posix(),
                        'history_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                        'notice':'Synthetic lead only'}})
        write_jsonl(case.repo/'jobs/status-history/output/FRAGMENTS.jsonl',fragments)
        protected={p:p.read_bytes() for p in case.repo.rglob('*') if p.is_file()}
        summary=case.run_build()
        decided=case.dossier('EO:1')
        undecided=next(r for r in read_jsonl(case.out/'STATUS_LEADS.jsonl') if r['instrument_id']=='EO:4')
        assert decided['status_history']['machine_lead'] is True
        assert undecided['status_history']['machine_lead'] is True
        assert undecided['status'] is None
        assert summary['counts']['assembled_claims']==0
        assert {p:p.read_bytes() for p in protected}==protected
        case.test_blank_sheets_never_assemble_and_each_failure_reported()
        result={'schema':'eo-status-history-pipeline-integration/v1',
            'consumer':'actual claim-kit build on existing synthetic integration corpus',
            'decided_dossier_pointer_propagated':True,'undecided_status_lead_pointer_propagated':True,
            'machine_lead_preserved':True,'blank_lifecycle_decision_rejected':True,
            'provisional_statuses_changed':0,'claims_assembled_from_history':0,
            'protected_source_inputs_mutated':0,'wall_seconds':round(time.monotonic()-start,4)}
        dest=Path(__file__).with_name('PIPELINE_INTEGRATION.json')
        dest.write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
        print(json.dumps(result))
    finally:case.doCleanups()

if __name__=='__main__':main()
