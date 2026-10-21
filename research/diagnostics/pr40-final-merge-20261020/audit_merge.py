"""Offline, reproducible evidence-preservation audit for the final PR #40 merge."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = '6d9cbc21c1b2e5adc567bd7d9abe729909124ef9'
INCOMING = '69372304ff28504997b20357dc2b6351992d8bcb'
GENERATIONS = [INCOMING, '603098f5cd5dc240c6a7fcb7176f2bbf0bec149b']
sys.path[:0] = [str(ROOT/'jobs/source-ladder'), str(ROOT/'jobs/_lib')]
import fetch_ladder as fl
import job
import ladder_queue
from prior_output import PriorOutput, UnionPriorOutput


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    spec = json.loads((ROOT/'research/repair-20261020/SOURCE_IMPORTS.json').read_bytes())
    assert all(ref in spec['commits'] for ref in GENERATIONS)
    priors = [PriorOutput.from_git_ref(ROOT, 'jobs/source-ladder/output', ref)
              for ref in [BASE] + spec['commits']]
    with tempfile.TemporaryDirectory() as temp:
        queue = Path(temp)/'FETCH_QUEUE.jsonl'
        queue.write_bytes(git('show', BASE+':research/readiness/FETCH_QUEUE.jsonl'))
        requests, problems = ladder_queue.read_fetch_queue(queue, {})
    by_id = {w.wanted_id:w for w in requests}
    # Shared/Opus records carry their exact question in their stable identifier
    # and source citation. Queue requests use the current normalized request.
    for prior in priors:
        for source in prior.jsonl('SOURCES.jsonl'):
            wid = source['wanted_id']
            if not wid.startswith('queue:'):
                by_id.setdefault(wid, fl.Wanted(wid, source.get('instrument_ids') or [],
                    urls=[source.get('requested_url') or source.get('url')],
                    citation=source.get('citation') or ''))
    union = UnionPriorOutput(priors, requests=by_id)
    found = job.previous_found(union)
    valid, stale, audit = job.revalidate_previous(found, by_id)
    baseline = {s['wanted_id']:s for s in priors[0].jsonl('SOURCES.jsonl')}
    incoming = {s['wanted_id']:s for p in priors[1:3] for s in p.jsonl('SOURCES.jsonl')}
    additions = []
    for wid, source in incoming.items():
        if wid in baseline:
            continue
        selected = valid.get(wid)
        additions.append({'wanted_id':wid, 'source_sha256':source.get('sha256'),
            'in_current_validated_union':selected is not None,
            'quarantine_or_revalidation_reason':stale.get(wid) or
                ('retained quarantine excludes this receipt' if wid not in found else None),
            'text_sha256':hashlib.sha256(selected[1]).hexdigest() if selected and selected[1] else None})
    full_order = next((wid for wid in valid if wid.startswith('queue:EO:11490:34 FR')), None)
    assert full_order, 'Repaired EO 11490 extraction was lost during source-generation reconciliation'
    body = valid[full_order][1].decode('utf-8')
    pages = []
    import re
    for match in re.finditer(r'^=== PDF page (\d+)', body, re.M):
        pages.append(int(match.group(1)))
    assert set(range(63,96)).issubset(pages), pages
    assert '3014' in body and '3015' in body
    rejected = union.jsonl('REJECTED_PRIOR_SOURCES.jsonl')
    assert any(r['wanted_id']==full_order for r in rejected)
    protected = ['research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv',
        'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',
        'research/stage12/METHODOLOGY_CODEBOOK_SUPPLEMENT_PROPOSED.md',
        'research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json',
        'research/readiness/SOURCE_AUDIT_HOLDS.jsonl']
    protected_proof = []
    for path in protected:
        old = git('rev-parse', BASE+':'+path).decode().strip()
        current = git('rev-parse', ':'+path).decode().strip()
        assert old == current, path
        protected_proof.append({'path':path, 'blob_sha':old, 'unchanged':True})
    changed = git('diff','--name-only','874f970f5564b81135e6ff939ff77b56f8972a5a',INCOMING).decode().splitlines()
    jobs = sorted({p.split('/')[1] for p in changed if p.startswith('jobs/') and '/output/' in p})
    history = [{'commit':ref, 'job_output_trees':{
        name:git('rev-parse',ref+':jobs/'+name+'/output').decode().strip()
        for name in jobs}} for ref in GENERATIONS]
    result = {'schema':'eo-final-pr40-merge-audit/v1','baseline':BASE,'incoming':INCOMING,
        'passed':True, 'network_source_acquisitions':0,
        'canonical_output_policy':'Keep the coherent main generation from successful run 39507868600; '
            'retain both incoming generated histories as merge ancestors, and import their exact '
            'source generations through the existing pinned source-ladder interface. '
            'The normal post-integration pipeline rebuilds derived outputs.',
        'source_import_commits':spec['commits'], 'union_candidates':len(found),
        'current_retrieval_checks_passed':len(valid), 'current_retrieval_checks_failed':len(stale),
        'incoming_receipts_absent_from_baseline':additions,
        'repaired_EO_11490':{'wanted_id':full_order,'pdf_pages':pages,
            'section_3014_present':True,'section_3015_present':True,'old_quarantine_retained':True},
        'retained_quarantine_records':len(rejected), 'protected_inputs':protected_proof,
        'historical_output_generations':history, 'request_warnings':problems,
        'does_not_establish':'Legal effect, source authentication, human certification, new owner rulings or savings'}
    target = Path(__file__).with_name('MERGE_AUDIT.json')
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'passed':True,'source_candidates':len(found),'retrieval_valid':len(valid),
        'retrieval_stale':len(stale),'new_valid_receipts':sum(r['in_current_validated_union'] for r in additions),
        'historical_generations':len(history),'EO_11490_pages':len(pages)}),flush=True)


if __name__ == '__main__':
    main()
