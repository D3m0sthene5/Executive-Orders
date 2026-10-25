"""Diagnose real production receipts, with explicit evidence/measurement limits.

This optional CLI reads ordinary research outputs. It never launches research,
acquisition, ledger writes or a tracker rebuild, and never updates legal records.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from production_receipts import (Reader, canonical, import_production, interval,
                                 number, require, tally, union_seconds, SHA)
from survey import PHASES, TOKEN_CATEGORIES


def effort(reader, references, selected_ids):
    events = {}
    for ref in references:
        value = reader.value(ref)
        require(value.get('schema') == 'neyman.production-effort/1', 'unsupported effort schema')
        for e in value['events']:
            require(isinstance(e.get('event_id'), str) and e['event_id'], 'effort event id required')
            key = e['event_id']
            if key in events:
                require(events[key] == e, 'conflicting shared effort event')
                continue
            require(e.get('phase') in PHASES and e.get('kind') in ('worker_elapsed', 'active', 'access_wait', 'machine'),
                    'invalid phase/measurement kind')
            require(isinstance(e.get('worker_id'), str) and e['worker_id'], 'worker id required')
            uses = e.get('instrument_ids')
            require(isinstance(uses, list) and uses and len(uses) == len(set(uses)) and set(uses) <= selected_ids,
                    'effort downstream membership mismatch')
            interval(e['started_utc'], e['finished_utc'])
            require(e.get('coverage') in ('partial', 'complete_interval'), 'measurement coverage required')
            require(isinstance(e.get('measurement_method'), str) and e['measurement_method'].strip(),
                    'measurement method required; elapsed is not active labor')
            tokens = e.get('tokens', {})
            require(isinstance(tokens, dict) and set(tokens) <= set(TOKEN_CATEGORIES), 'unknown token category')
            for k, v in tokens.items():
                if v is not None:
                    number(v, k)
                    require(type(v) is int, 'token count must be integer')
            # A usage record may not be attached to several overlapping phase events.
            require(not any(v is not None for v in tokens.values()) or isinstance(e.get('usage_id'), str)
                    and e['usage_id'], 'token observations need stable usage_id')
            events[key] = e
    groups = defaultdict(list); phase_groups = defaultdict(list); usage = {}
    for e in events.values():
        groups[(e['kind'], e['worker_id'])].append(interval(e['started_utc'], e['finished_utc']))
        phase_groups[(e['phase'], e['kind'], e['worker_id'])].append(interval(e['started_utc'], e['finished_utc']))
        if e.get('usage_id'):
            u = e['usage_id']; tokens = e.get('tokens', {})
            require(u not in usage or usage[u] == tokens, 'conflicting usage record')
            usage[u] = tokens
    totals = {kind: sum(union_seconds(spans) for (k, _), spans in groups.items() if k == kind)
              if any(k == kind for k, _ in groups) else None
              for kind in ('worker_elapsed', 'active', 'access_wait', 'machine')}
    return {'events': list(events.values()), 'observed_seconds_by_kind': totals,
            'observed_phase_seconds_by_kind': {phase: {kind:
                sum(union_seconds(spans) for (p, k, _), spans in phase_groups.items() if p == phase and k == kind)
                if any(p == phase and k == kind for p, k, _ in phase_groups) else None
                for kind in totals} for phase in PHASES},
            'observed_token_lower_bounds': {k: sum(t[k] for t in usage.values() if t.get(k) is not None)
                                            if any(t.get(k) is not None for t in usage.values()) else None
                                            for k in TOKEN_CATEGORIES},
            'token_usage_records': len(usage), 'complete_session_cost': None,
            'note': 'Intervals unioned per worker/kind; kinds overlap and must not be added. Reasoning may be included in output.'}


def repair_probe(reader, spec):
    iid = spec['instrument_id']
    before, after = (tally(reader, spec[k]) for k in ('before', 'after'))
    require(before['attempt_id'] != after['attempt_id'], 'repair needs distinct attempts')
    rows = [next((r for r in a['outcomes'] if r['instrument_id'] == iid), None) for a in (before, after)]
    require(all(rows), 'repair target absent from receipt')
    require(before['interval'][1] <= after['interval'][0], 'repair attempt chronology invalid')
    deps = [reader.value(spec[k]) for k in ('before_dependencies', 'after_dependencies')]
    require(all(isinstance(d, dict) and all(v is None or SHA.fullmatch(str(v))
                                          for v in d.values()) for d in deps), 'dependency hash maps required')
    changed = sorted(k for k in set(deps[0]) | set(deps[1]) if deps[0].get(k) != deps[1].get(k))
    transition = rows[0]['outcome'] != 'eligible' and rows[1]['outcome'] == 'eligible' and rows[1].get('source_review_upheld') is True
    return {'instrument_id': iid, 'before': spec['before'], 'after': spec['after'],
            'scope': 'completion eligibility only; not proof of whole lifecycle or source adequacy',
            'observed_transition': transition, 'changed_declared_dependencies': changed,
            'result': ('inconclusive_multiple_changes' if len(changed) != 1 else
                       'single_declared_change_with_transition' if transition else 'no_eligibility_rescue'),
            'causal_attribution': 'unverified; supplied dependency maps may omit changes',
            'hours_saved': None, 'tokens_saved': None}


def questions(reader, references, selected_ids):
    result = []
    for ref in references:
        q = reader.value(ref)
        require(q.get('schema') == 'neyman.discriminating-question/1' and q.get('instrument_id') in selected_ids,
                'question schema/target mismatch')
        require(all(isinstance(q.get(k), str) and q[k].strip() for k in
                    ('assessor', 'question', 'needed_observation', 'suggested_existing_route')), 'incomplete question')
        alternatives = q.get('alternatives')
        require(isinstance(alternatives, list) and len(alternatives) >= 2 and
                all(isinstance(a, str) and a.strip() for a in alternatives) and
                len(set(alternatives)) == len(alternatives), 'distinct explanations required')
        require(q.get('basis'), 'question basis required')
        for basis in q['basis']:
            reader.value(basis)
        result.append(dict(q, ref=ref, status='research_recommendation_not_legal_finding'))
    return result


def diagnose(reader, manifest):
    imported = import_production(reader, manifest)
    ids = {c['instrument_id'] for c in imported['observations']}
    costs = effort(reader, manifest.get('effort_receipts', []), ids)
    checkpoints = defaultdict(list)
    for c in imported['checkpoints']:
        checkpoints[c['instrument_id']].append(c)
    qs = questions(reader, manifest.get('questions', []), ids)
    for c in imported['observations']:
        iid = c['instrument_id']; cp = checkpoints[iid]
        c['execution_exceptions'] = [dict(receipt=a['receipt'], error=r.get('error'),
                                         scope='reported completion failure; substantive cause not inferred')
                                     for a in imported['attempts'] for r in a['outcomes']
                                     if r['instrument_id'] == iid and r['outcome'] == 'exception']
        c['source_checkpoints'] = cp
        for checkpoint in cp:
            checkpoint['binds_selected_claim'] = c['claim_sha256'] is not None and any(
                v['claim_sha256'] == c['claim_sha256'] for v in checkpoint['referenced_claim_versions'])
        c['next_questions'] = [q for q in qs if q['instrument_id'] == iid]
        if c.get('right_censored'):
            c['diagnosis'] = 'censored_research_attempt'
            c['next_action'] = 'Retain the actual attempted question and evidence; no completion or exhaustion inferred.'
        elif not c['whole_case_gate_pass'] and any(p['binds_selected_claim'] for p in cp):
            c['diagnosis'] = 'documented_unresolved_evidence_or_application'
            c['next_action'] = 'Use the pinned event/record requests and question; resolve routing or locate primary evidence before resuming the held conclusion.'
        elif c['whole_case_gate_pass'] and c['tracker_blockers'] == ['NO_PROVISIONAL_STATUS']:
            c['diagnosis'] = 'reviewed_proposal_awaits_status_adoption'
            c['next_action'] = 'Route the existing exact proposal through owner adoption; no fresh research inferred from this blocker.'
        elif c['ready_in_isolated_replay']:
            c['diagnosis'] = 'ready_in_isolated_replay'
            c['next_action'] = 'Retain exact reviewed claim and receipts for authorized integration.'
        else:
            c['diagnosis'] = 'requires_scoped_assessment'
            c['next_action'] = 'Inspect exact remaining gates; no root cause inferred from an open step alone.'
    attempts = imported['attempts']
    known = [a['machine_seconds'] for a in attempts if a['machine_seconds'] is not None]
    imported['effort'] = costs
    imported['repair_probes'] = [repair_probe(reader, p) for p in manifest.get('repair_probes', [])]
    imported['summary'] = {
        'observed_orders': len(ids), 'unique_completion_invocations': len(attempts),
        'failed_completion_invocations': sum(any(r['outcome'] == 'exception' for r in a['outcomes']) for a in attempts),
        'research_attempts': len(imported['research_attempts']),
        'censored_orders': sum(bool(c.get('right_censored')) for c in imported['observations']),
        'reviewed_whole_case_proposals': sum(c['whole_case_gate_pass'] for c in imported['observations']),
        'reviewed_partials': sum(c['reviewed_output'] == 'partial_research' for c in imported['observations']),
        'ready_in_isolated_replay': sum(c['ready_in_isolated_replay'] for c in imported['observations']),
        'diagnoses': dict(Counter(c['diagnosis'] for c in imported['observations'])),
        'completion_machine_seconds_lower_bound': sum(known),
        'completion_machine_seconds_total': sum(known) if attempts and len(known) == len(attempts) else None,
        'completion_occupied_wall_seconds': union_seconds([a['interval'] for a in attempts]) if attempts else None,
        'worker_effort_coverage': 'none' if not costs['events'] else 'partial_observed_intervals',
        'total_agent_hours': None, 'net_hours_saved': None, 'verified_savings': False,
        'population_inference_supported': False, 'primary_cost_bottleneck': 'not_identified_with_available_effort_coverage'}
    imported['measurement_gaps'] = [
        'Completion timers measure machine invocation, not producer/reviewer effort.',
        'No population cost or savings extrapolation from a convenience cohort.',
        'Checkpoints and question explanations remain attributed hypotheses; no automatic legal findings.',
        'Missing effort intervals and incomplete task attempts are not zero-cost work.']
    imported['input_pins'] = dict(sorted(reader.pins.items()))
    imported['implementation_pins'] = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                                       for name in ('diagnose.py', 'production_receipts.py', 'survey.py')}
    return imported


def render(data):
    s = data['summary']
    out = ['# NEYMAN production diagnosis', '',
           f"Cohort: {data['cohort_kind']}. {s['observed_orders']} orders; {s['unique_completion_invocations']} unique completion invocations.",
           f"{s['reviewed_whole_case_proposals']} reviewed whole-case proposals; {s['reviewed_partials']} reviewed partials; {s['ready_in_isolated_replay']} ready in isolated replay.",
           f"Observed completion machine seconds: {s['completion_machine_seconds_lower_bound']:.6f}. Total agent hours and savings remain unknown.",
           '', '| Order | Observed state | Next action |', '| --- | --- | --- |']
    for c in data['observations']:
        for failure in c['execution_exceptions']:
            out += ['', c['instrument_id']+' retained completion failure: '+str(failure['error'])]
        out.append(f"| {c['instrument_id']} | {c['diagnosis']} | {c['next_action']} |")
    for c in data['observations']:
        for cp in c['source_checkpoints']:
            out += ['', '## '+c['instrument_id']+' recorded checkpoint context', '', cp['reason'],
                    'Binds selected claim: '+str(cp['binds_selected_claim'])+'. Historical context does not override the selected result.',
                    '', 'Attribution: '+cp['attribution']+'. No exhaustion inferred.']
            for r in cp['requests']:
                out += ['', '- Needed record: '+str(r['citation']), '  Purpose: '+str(r['needed_evidence'])]
        for q in c['next_questions']:
            out += ['', 'Next discriminating question: '+q['question'],
                    'Observation sought: '+q['needed_observation']]
    out += ['', '## Limits', ''] + ['- '+g for g in data['measurement_gaps']]
    return '\n'.join(out)+'\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--manifest', required=True, help='repository-relative production import manifest')
    p.add_argument('--out', type=Path, required=True, help='new isolated output directory')
    a = p.parse_args(argv)
    try:
        reader = Reader(a.repo)
        manifest_ref = reader.ref(a.manifest)
        data = diagnose(reader, reader.value(manifest_ref))
        # Refuse races/edited inputs between parsing and publication.
        for path, sha in data['input_pins'].items():
            if sha is None:
                require(not reader.path(path).exists(), 'previously absent input appeared: '+path)
            else:
                reader.raw({'path': path, 'sha256': sha})
        dest = a.out if a.out.is_absolute() else reader.root/a.out
        dest = dest.resolve()
        if dest.is_relative_to(reader.root):
            allowed = [reader.root/'research/neyman/production-diagnostics',
                       reader.root/'jobs/neyman/output/diagnostics']
            require(any(dest.is_relative_to(d) and dest != d for d in allowed),
                    'repository output must be a new NEYMAN diagnostic run directory')
        require(not dest.exists(), 'output already exists; choose a new directory')
        dest.mkdir(parents=True, exist_ok=False)
        (dest/'DIAGNOSIS.json').write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')
        (dest/'OBSERVATIONS.jsonl').write_text(''.join(json.dumps(c, sort_keys=True, allow_nan=False)+'\n' for c in data['observations']))
        (dest/'REPORT.md').write_text(render(data))
        print(json.dumps(data['summary'], sort_keys=True))
        return 0
    except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        print('production diagnosis refused: '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
