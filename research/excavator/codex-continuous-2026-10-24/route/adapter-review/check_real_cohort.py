"""Independent bounded discovery/binding audit; no legal review or adoption."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--write', type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    repo = args.repo.resolve()
    sys.path[:0] = [str(args.stage), str(repo/'jobs/claim-kit')]
    import prior_research as prior
    folder = repo/'research/excavator/sinclair-2026-10-20/lean-review-2026-10-22'
    review_path = folder/'CROSS_FAMILY_REVIEW.json'
    hold_path = folder/'HELD_PROPOSALS.json'
    adoption_path = repo/'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
    protected_before = {str(p.relative_to(repo)): digest(p) for p in (review_path,hold_path,adoption_path)}
    review = json.loads(review_path.read_bytes())
    holds = json.loads(hold_path.read_bytes())
    with (folder/'CROSS_FAMILY_ADOPTION_ROWS.csv').open() as handle:
        cohort = [r['instrument_id'] for r in csv.DictReader(handle)]
    extra = ['EO:9380','EO:9593'] + [r['instrument_id'] for r in holds['proposals']]
    dossiers = {iid: json.loads((repo/'jobs/claim-kit/output/dossiers'/
        (iid.replace(':','_')+'.json')).read_bytes()) for iid in cohort}
    for iid in extra:
        candidates = list((repo/'research/excavator/sinclair-2026-10-20').rglob(
            iid.replace(':','_')+'/proposal-v1/EVIDENCE.json'))
        assert len(candidates) == 1, (iid, candidates)
        dossiers[iid] = json.loads(candidates[0].read_bytes())['base_dossier']
    assert len(cohort) == 29 and len(dossiers) == 37
    context = prior.collect(repo,dossiers,exclude=repo/'research/excavator/codex-continuous-2026-10-24')
    cases = []
    for n,row in enumerate(review['verdicts']):
        iid = row['instrument_id']
        decision_file = next(p for p in row['input_files'] if p['path'].endswith('/STATUS_DECISION.json'))
        evidence_file = next(p for p in row['input_files'] if p['path'].endswith('/EVIDENCE.json'))
        decision = json.loads((repo/decision_file['path']).read_bytes())
        evidence = json.loads((repo/evidence_file['path']).read_bytes())
        assert decision['instrument_id'] == evidence['instrument_id'] == evidence['base_dossier']['instrument_id'] == iid
        assert digest(repo/decision_file['path']) == decision_file['sha256']
        assert digest(repo/evidence_file['path']) == evidence_file['sha256']
        assert evidence['fingerprint'] == row['evidence_canonical_fingerprint'] == decision['evidence_sha256']
        item = next(r for r in context['orders'][iid]['status_research'] if r['path'] == decision_file['path'])
        found = next(r for r in item['reviews'] if r['path'] == str(review_path.relative_to(repo)))
        assert found['pointer'] == '/verdicts/'+str(n)
        assert found['version_binding'] == 'exact' and found['verdict'] == row['verdict']
        assert found['scope'] == row['scope']
        assert found['d6'] == {k:row['d6'][k] for k in ('assessment','coverage')}
        assert not item['automatic_approval'] and not found['full_lifecycle_approved']
        if iid in cohort:
            assert item['adoption']['state'] == 'recorded_provisional_status_for_review'
        else:
            assert row['verdict'] == 'needs_research'
            assert item['adoption']['state'] == 'not_recorded_in_current_authority'
        text = json.dumps(prior.brief(context,iid))
        if iid == 'EO:13975':
            assert '14005' in text and '14006' in text
        if iid == 'EO:10704':
            assert 'Do not adopt the producer earlier-displacement theory' in text
        cases.append({'instrument_id':iid,'producer_version_file':decision_file,
            'review_pointer':found['pointer'],'version_binding':found['version_binding'],
            'adoption_state':item['adoption']['state'],'verdict':found['verdict'],
            'source_pin_states':dict(Counter(p['state'] for p in item['source_pins'])),
            'reconciliation_tasks':item['reconciliation_tasks']})
    hold_results = []
    for row in holds['proposals']:
        iid = row['instrument_id'];items = context['orders'][iid]['status_holds']
        assert len(items) == 1
        item = items[0]
        assert item['record'] == row and item['state'] == 'held_out_of_pending_adoption'
        assert item['historical_review']['binding'] == 'exact'
        assert item['historical_review']['record']['instrument_id'] == iid
        assert item['historical_review']['producer_version_binding'] == 'not_established_by_procedural_hold'
        assert not item['automatic_approval'] and not item['full_lifecycle_approved']
        assert all(r['adoption']['state'] == 'not_recorded_in_current_authority'
            for r in context['orders'][iid]['status_research'])
        hold_results.append({'instrument_id':iid,'state':item['state'],
            'historical_review':{k:item['historical_review'][k] for k in ('file','pointer','binding','producer_version_binding')}})
    assert context['automatic_approvals'] == 0
    assert protected_before == {p:digest(repo/p) for p in protected_before}
    output={'scope':'Independent engineering checks only, no legal/source adequacy review.',
        'reviewed_module_sha256':digest(Path(prior.__file__)),
        'cohort_count':len(cohort),'dossiers_checked':len(dossiers),
        'dossier_caveat':'29 published decided dossiers; eight historical frozen dossiers are audit carriers only, not current production freezes.',
        'cross_family_cases':cases,'parent_holds':hold_results,
        'protected_before_after_sha256':protected_before,
        'automatic_approvals':context['automatic_approvals'],
        'elapsed_seconds':round(time.perf_counter()-started,6),'tokens':None,'cache_tokens':None}
    args.write.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ('cohort_count','dossiers_checked','automatic_approvals','elapsed_seconds')},indent=2))


if __name__ == '__main__':
    main()
