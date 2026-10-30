"""Deterministic claim-kit/checker/tracker boundary probe; never writes production records."""
import copy
import datetime
import json
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
os.environ['CLAIM_CHECKER_VERIFY_DOWNLOADS'] = '0'
sys.path.insert(0, str(ROOT/'jobs/claim-checker'))
sys.path.insert(0, str(ROOT/'jobs/readiness-tracker'))
sys.path.insert(0, str(ROOT/'jobs/claim-kit'))
sys.path.insert(0, str(ROOT/'jobs/claim-checker'))
import checker as C
import tracker as T
import test_checker as TC
import test_tracker as TT

spec_a = importlib.util.spec_from_file_location('assemble_probe', ROOT/'jobs/claim-kit/assemble.py')
A = importlib.util.module_from_spec(spec_a); spec_a.loader.exec_module(A)
spec_ta = importlib.util.spec_from_file_location('test_assemble_probe', ROOT/'jobs/claim-kit/test_assemble.py')
TA = importlib.util.module_from_spec(spec_ta); spec_ta.loader.exec_module(TA)


def run_assembler_only():
    out = {}
    # Actual claim-kit assembler + Stage 19 gate, isolated in test_assemble's temp repo.
    test = TA.AssemblyTests(methodName='test_complete_claim_passes_real_gate_and_strict_check')
    test.setUp()
    try:
        text = (test.repo/'held.txt').read_text(encoding='utf-8')
        insertion = 'The Secretary shall maintain a separate records program annually.\n'
        text = text.replace('Executive Order 2.', insertion+'Executive Order 2.', 1)
        (test.repo/'held.txt').write_text(text, encoding='utf-8')
        prefix = text.split('Executive Order 2.', 1)[0]
        source_sha = hashlib.sha256(text.encode()).hexdigest()
        original = test.dossier['evidence']['ORIGINAL:EO:1']
        original.update(text=prefix, char_start=0, char_end=len(prefix))
        for record in list(test.dossier['evidence'].values()) + test.dossier['clauses']:
            quote = record.get('text', '')
            if quote and quote in text:
                record['char_start'] = text.index(quote)
                record['char_end'] = record['char_start'] + len(quote)
            src = record.get('source')
            if isinstance(src, dict):
                src.update(sha256=source_sha, text_sha256=source_sha, local_path='held.txt', text_path='held.txt')
        test.refresh(); test.sheet['dossier_sha256'] = test.dossier['fingerprint']
        claim, errors = test.assemble()
        out['incomplete_inventory'] = {'assembled':claim is not None,'errors':errors,
            'claim_clause_count':len(claim['operative_clauses']) if claim else None,
            'original_contains_omitted_command':bool(claim and insertion.strip() in claim['original_representation']['quote'])}
    finally:
        test.tearDown()
    for kind,label in [('report_deadline','report_deadline_rejected'), ('actual_performance','other_kind_control')]:
        test = TA.AssemblyTests(methodName='test_complete_claim_passes_real_gate_and_strict_check')
        test.setUp()
        try:
            test.dossier['evidence']['ACT:EO:1>EO:2']['kind'] = kind
            test.refresh(); test.sheet['dossier_sha256'] = test.dossier['fingerprint']
            claim, errors = test.assemble()
            out[label] = {'assembled':claim is not None,'errors':errors}
        finally:
            test.tearDown()
    return out


def run():
    output = {'fixture':'synthetic source text from jobs/claim-checker/test_checker.py; no historical/legal claim',
              'network':'disabled', 'models':'not used',
              'assembler_only':run_assembler_only()}
    # Claim-checker fixture provides a preserved original, exact text quotes,
    # captured end bytes, and the actual Stage 19 gate via its fixture shim.
    with tempfile.TemporaryDirectory(prefix='lifecycle-checker-') as td:
        root = Path(td)
        job_dir = root/'jobdir'; cache_dir = root/'cache'
        TC.build_repo(root)
        claim = copy.deepcopy(TC.good_claim())
        claim['operative_clauses'] = claim['operative_clauses'][:1]
        ctx = C.Context(root, job_dir, cache_dir, today=datetime.date(2026, 10, 30))
        rows, errors, status = C.check_claim(claim, ctx)
        summary = C.summarise_claim('probe:EO:90001', 'synthetic.jsonl', 1,
                                     claim, rows, errors, status, ctx)
        output['claim_checker'] = {
            'instrument_id': claim['instrument_id'],
            'errors': errors,
            'status': status,
            'mechanical_result': summary['mechanical_result'],
            'gate_passed': summary['gate_passed'],
            'all_checks_passed': summary['all_checks_passed'],
            'step_checker_passed': {k:v['checker_passed'] for k,v in summary['steps'].items()},
            'checker_failure_total': summary['failures_total'],
            'omitted_source_clause_count': 1,
            'claim_clause_count': len(claim['operative_clauses']),
        }
        claim_sha = ctx.gate.claim_sha(claim)
        step_receipt = {k:v['checker_passed'] for k,v in summary['steps'].items()}

        # Reuse the readiness tracker test fixture, replacing only its tiny
        # universe/decision rows and feeding the exact claim + checker receipt.
        tt = TT.TrackerTest(methodName='test_complete_claim_makes_an_order_ready')
        tt.setUp()
        try:
            r = tt.root
            TT.write_csv(r/T.P['universe'], [{'id':'EO:90001','included_in_bibliography':'1'}])
            TT.write_csv(r/T.P['decided'], [{'instrument_id':'EO:90001','provisional_substantive_status':'no','decision_origin':'probe'}])
            TT.write_csv(r/T.P['causal'], [{'instrument_id':'EO:90001','locally_preserved_primary_representation':'1','quarantined_relationship_count':'0'}])
            TT.write_csv(r/T.P['crosswalk'], [{'instrument_id':'EO:90001','selected_literal_URL':'https://www.govinfo.gov/x/EO_90001.pdf'}])
            TT.write_csv(r/T.P['custody'], [{'instrument_id':'EO:90001','custody_state':'not_attempted'}])
            (r/'research/readiness/claims/probe.jsonl').write_text(json.dumps(claim)+'\n')
            (r/T.P['exhausted']).parent.mkdir(parents=True, exist_ok=True)
            (r/T.P['exhausted']).write_text('', encoding='utf-8')
            checker_payload = {'by_instrument': {'EO:90001': {
                'claim_sha256': claim_sha, 'steps_checker_passed': step_receipt}}}
            tt.write(T.J['checker'], json.dumps(checker_payload))
            orders, problems = T.build(str(r))
            summary = T.summarise(orders, problems)
            order = next(x for x in orders if x['instrument_id']=='EO:90001')
            output['tracker'] = {
                'ready_for_human_review': order['ready_for_human_review'],
                'ready_tier': order.get('ready_tier'),
                'step_clause_inventory': order['step_clause_inventory'],
                'step_ending_or_current_basis': order['step_ending_or_current_basis'],
                'tracker_summary_ready_count': summary['ready_for_human_review'],
                'problems': problems,
            }
        finally:
            tt.tearDown()

    # The isolated assembler checks use the same synthetic source narrative.
    # (The fuller end-to-end observation above is the authoritative integration result.)
    return output


if __name__ == '__main__':
    result = run()
    dest = Path(__file__).with_name('EXECUTION.json')
    dest.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
