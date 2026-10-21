"""Reconcile research stages against pinned current claims, checker and tracker.

This reads existing outputs; it never implements readiness or turns evidence
records into whole-order conclusions. Historical attempts remain historical.
"""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


class Inputs:
    def __init__(self, repo):
        self.repo, self.pins = Path(repo).resolve(), {}

    def read(self, path):
        p = self.repo / path
        raw = p.read_bytes()
        self.pins[p.relative_to(self.repo).as_posix()] = hashlib.sha256(raw).hexdigest()
        return raw.decode('utf-8')

    def obj(self, path):
        return json.loads(self.read(path))

    def lines(self, path):
        return [json.loads(line) for line in self.read(path).splitlines() if line.strip()]


def review_records(value):
    for key in ('verdicts', 'orders', 'records'):
        rows = value.get(key)
        if isinstance(rows, list):
            return rows
        if isinstance(rows, dict):
            return [{'instrument_id':iid, 'verdict':v} for iid,v in rows.items()]
    raise ValueError('review file has no per-order verdicts')


def claim_stages(selected, effective, checker, tracker):
    """Exact claim hashes prevent stale checks or another owner's claim gaining credit."""
    current = {iid:sha for iid,sha in selected.items() if effective.get(iid) == sha}
    passed = {iid for iid,sha in current.items() if any(
        row.get('claim_sha256') == sha and row.get('all_checks_passed') is True
        and row.get('gate_passed') is True for row in checker.get(iid, []))}
    ready = {iid for iid in passed if tracker.get(iid, {}).get('ready_for_human_review') == 'yes'}
    return {'canonical_claims_in_campaign':len(selected), 'currently_effective_claims':len(current),
            'local_checker_passes':len(passed), 'integrated_ready_orders':len(ready),
            'checker_unverified_or_failed':sorted(set(current)-passed),
            'checker_passed_but_not_integrated_ready':[
                {'instrument_id':iid,'blockers':tracker.get(iid, {}).get('blockers')}
                for iid in sorted(passed-ready)],
            'independently_human_certified_added':0}


def reconcile(repo, tracker_path='jobs/readiness-tracker/output/READINESS_BY_ORDER.csv'):
    data = Inputs(repo)
    gate_path = data.repo/'research/stage19/code/claim_gate.py'
    spec = importlib.util.spec_from_file_location('progress_claim_gate', gate_path)
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    data.read(gate_path)
    groups = {'lambertini_III':{}, 'rastell':{}, 'lamm_II':{}, 'lamm_III':{}}
    effective = {}
    for path in sorted((data.repo/'research/readiness/claims').glob('*.jsonl')):
        for claim in data.lines(path):
            iid, sha = claim['instrument_id'], gate.claim_sha(claim)
            effective[iid] = sha
            for group,prefix in [('lambertini_III','claude-lambertini-i'),('rastell','claude-rastell-c'),
                                 ('lamm_II','claude-lamm-s'),('lamm_III','claude-lamm-t')]:
                if path.name.startswith(prefix): groups[group][iid] = sha
    check_data = data.obj('jobs/claim-checker/output/PER_CLAIM.json')
    checker = {}
    for row in check_data['claims']:
        checker.setdefault(row['instrument_id'], []).append(row)
    tracker = {r['instrument_id']:r for r in csv.DictReader(data.read(tracker_path).splitlines())}
    stages = {name:claim_stages(rows, effective, checker, tracker) for name,rows in groups.items()}

    batches = []
    base = data.repo/'research/excavator/lambertini-2026-10-20/instruments'
    for directory in sorted(base.iterdir()):
        if not directory.is_dir() or not directory.name.isdigit(): continue
        log = data.lines(directory/'ORDER_LOG.jsonl')
        attempts = {r['instrument_id'] for r in log}
        review = directory/'reviews/VERDICTS.json'
        rows = review_records(data.obj(review)) if review.exists() else []
        reviewed = {r['instrument_id'] for r in rows}
        if not reviewed <= attempts: raise ValueError('review includes an order outside batch log')
        upheld = {r['instrument_id'] for r in rows if r.get('verdict',r.get('decision')) in ('uphold','upheld')}
        batches.append({'batch':directory.name,'attempts':len(attempts),'reviewed_cases':len(reviewed),
                        'AI_upheld_cases':len(upheld),'unreviewed_cases':sorted(attempts-reviewed)})
    stages['lambertini_III'].update(attempts=sum(b['attempts'] for b in batches),
        reviewed_cases=sum(b['reviewed_cases'] for b in batches),
        AI_upheld_cases=sum(b['AI_upheld_cases'] for b in batches), batches=batches)

    submitted = data.lines('research/readiness/act_overrides/rastell-2026-10-20.jsonl')
    ingested = {}
    for path in sorted((data.repo/'jobs/claim-kit/output').glob('ACTING_PROVISIONS*.jsonl')):
        for row in data.lines(path):
            if row.get('override_id','').endswith('@rastell'): ingested[row['override_id']] = row
    review_rows = []
    for path in sorted((data.repo/'research/excavator/rastell-2026-10-20').glob('batch_*/review/REVIEW.jsonl')):
        review_rows.extend(data.lines(path))
    opportunities = {r['target_id'] for r in review_rows if r.get('claims_enabled') == 'yes'
                     and r.get('verdict') == 'upheld'}
    stages['rastell'].update(located_evidence_submitted=len(submitted),
        ingested_evidence_records=len(ingested),
        submitted_not_ingested=sorted({r['id'] for r in submitted}-set(ingested)),
        distinct_targets_with_ingested_evidence=len({r['target_id'] for r in ingested.values()}),
        reviewer_suggested_research_opportunities=len(opportunities),
        research_opportunity_ids=sorted(opportunities),
        remaining_obligation='Investigate earlier cessation, original clauses, scope, savings, and later counterevidence; none of these counts is a completed lifecycle.')

    for group, pattern in [('lamm_II','sunsets/batch_*/OWN_TERM_END_RECORDS.jsonl'),
                           ('lamm_III','sunsets3/batch_*/OWN_TERM_END_RECORDS.jsonl')]:
        records = [r for p in sorted((data.repo/'research/excavator/lamm-2026-10-20').glob(pattern)) for r in data.lines(p)]
        stages[group]['attempted_ending_records'] = len(records)
        stages[group]['producer_verdicts'] = dict(Counter(r.get('verdict') or 'unrecorded' for r in records))
        stages[group]['note'] = 'Ending facts and producer findings are not whole-order claims; partial endings stay separate.'
    lamm3_reviews = [r for p in sorted((data.repo/'research/excavator/lamm-2026-10-20').glob('sunsets3/batch_*/review/REVIEW.jsonl')) for r in data.lines(p)]
    producers = {r['instrument_id']:r for p in sorted((data.repo/'research/excavator/lamm-2026-10-20').glob('sunsets3/batch_*/OWN_TERM_END_RECORDS.jsonl')) for r in data.lines(p)}
    verdict = lambda r: r.get('review_verdict') or r.get('verdict')
    stages['lamm_III'].update(AI_upheld_ending_records=sum(verdict(r)=='upheld' for r in lamm3_reviews),
        confirmed_negative_reasons=dict(Counter(r.get('producer_verdict') or r.get('record_verdict') or
            producers[r['instrument_id']].get('verdict') or 'unrecorded'
            for r in lamm3_reviews if verdict(r)=='negative_confirmed')))
    lamm_history=data.obj('research/excavator/lamm-2026-10-20/OUTCOME.json')
    stages['lamm_II']['AI_upheld_ending_records_reported_in_historical_summary']=sum(
        lamm_history[k]['upheld'] for k in ('batch_03','batch_04','batch_05'))
    stages['lamm_II']['review_count_basis']='Historical per-batch summary; per-record independent review files are not present for these batches.'
    data.read(Path(__file__).resolve())
    return {'schema':'eo-research-progress/v1', 'repo_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=data.repo,text=True).strip(),
            'stages':stages,'tracker_orders':len(tracker),
            'integrated_ready_total':sum(r.get('ready_for_human_review')=='yes' for r in tracker.values()),
            'input_sha256':dict(sorted(data.pins.items())),
            'note':'Exact input hashes identify this observation. Stages overlap and must not be added. No legal status, ownership or human certification changed.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',default=str(Path(__file__).resolve().parents[2]))
    p.add_argument('--tracker',default='jobs/readiness-tracker/output/READINESS_BY_ORDER.csv')
    p.add_argument('--out',required=True)
    a=p.parse_args(); result=reconcile(a.repo,a.tracker)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['stages'],indent=2,sort_keys=True))
