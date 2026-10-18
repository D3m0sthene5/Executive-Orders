"""Optional fingerprinted source plans. No routes, validators or judgments here."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path


def queue_inputs(repo):
    import ladder_queue as q
    import ofr_index
    repo=Path(repo)
    universe={r['id'] for r in q.read_csv(repo/'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv')}
    try:
        index=ofr_index.load_index(repo_root=repo,universe_ids=universe)
    except FileNotFoundError:
        index={}
    queued, problems=q.read_fetch_queue(repo/q.FETCH_QUEUE,index)
    shared=q.shared_source_wanted(repo,index,q.load_hints(repo)) if (repo/q.SHARED).exists() else []
    opus, more=q.opus_refetch_wanted(repo)
    return queued+shared+opus, problems+more


def queue_fingerprint(items):
    # The execution signature includes routes, expected hashes, membership,
    # metadata and order, so changed sources invalidate an old plan.
    raw=json.dumps([asdict(w) for w in items],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()


def select_plan(items, plan):
    if plan.get('schema')!='eo-source-plan/v1' or plan.get('queue_fingerprint')!=queue_fingerprint(items):
        raise ValueError('source plan is stale or has an invalid schema; rebuild the excavator')
    ids=plan.get('wanted_ids')
    if not isinstance(ids,list) or not 0<=len(ids)<=50 or len(set(ids))!=len(ids):
        raise ValueError('source plan must contain 0..50 distinct wanted IDs')
    by={}
    for w in items:
        if w.wanted_id in by:
            raise ValueError('ambiguous duplicate queue ID: '+w.wanted_id)
        by[w.wanted_id]=w
    if any(i not in by for i in ids):
        raise ValueError('source plan contains an unknown queue ID')
    budget=plan.get('max_requests')
    if type(budget) is not int or not 1<=budget<=300:
        raise ValueError('source plan request budget must be 1..300')
    return [by[i] for i in ids]


def retain_unselected(prior, carried, selected, out):
    """Carry held evidence outside a bounded pass, preserving its actual bytes."""
    from fetch_ladder import unique_file_name
    sources, results = [], []
    if prior is None:
        return sources, results
    previous = {r['wanted_id']: r for r in prior.csv_rows('RESULTS.csv')}
    for wid, (source, text) in sorted(carried.items()):
        if wid in selected:
            continue
        src = dict(source, carried_forward_from=prior.label)
        if text is not None:
            rel = 'texts/'+unique_file_name(wid)
            (out/rel).parent.mkdir(parents=True,exist_ok=True)
            (out/rel).write_bytes(text)
            src['text_path'] = rel
        else:
            src['text_path'] = None
        sources.append(src)
        row = dict(previous[wid], attempts=0, carried_forward_from=prior.label,
                   text_path=src['text_path'] or '')
        results.append(row)
    return sources, results


def open_steps(row):
    steps=("provisional_status","original_text","clause_inventory","ending_or_current_basis","savings_residuals","counterevidence","shared_sources","opus_media")
    return [step for step in steps if row.get("step_"+step)=="open"]


def opportunity(wanted, rows, found):
    """A source can complete only its declared machine step, never legal judgment.

    Ceiling means *all* the order's missing steps are this step and every blocker
    is explicitly addressed. Multiple missing media are checked separately below.
    """
    step = wanted.step
    affected = sorted({i for i in wanted.instrument_ids if i in rows and
                       rows[i].get('step_'+step) == 'open'})
    is_media = wanted.wanted_id.startswith('opus-refetch:')
    if wanted.wanted_id in found:
        affected = []
    # Other blockers remain; completing a source is not completing its clauses.
    addressed = ('OPUS_MEDIA_REFETCH_NEEDED',) if is_media else (
        ('SHARED_SOURCE_NOT_RETRIEVED',) if step == 'shared_sources' else ())
    near = [i for i in affected if open_steps(rows[i]) == [step] and
            all(b.startswith(addressed) for b in rows[i].get('blockers', '').split('|') if b)] if addressed else []
    return {'wanted_id': wanted.wanted_id, 'step': step, 'citation': wanted.citation,
            'urls': wanted.urls, 'expected_sha256': wanted.extra.get('expected_sha256'),
            'affected_order_ids': affected, 'potential_step_completions': len(affected),
            'near_ready_order_ids': near, 'ready_lower_bound': 0,
            'remaining_step_tasks': sum(max(0, len(open_steps(rows[i]))-1) for i in affected),
            'undecided_affected': sum(rows[i].get('step_provisional_status') == 'open' for i in affected),
            'next_action': 'source-ladder plan; verify source acceptance, then rerun checker/tracker',
            'confidence': 'mechanical workload estimate; no legal inference'}


def rank_actions(actions):
    # No invented billing coefficients: first readiness proximity, then verified
    # machine step opportunity, then lower downstream work, stable ID tie break.
    return sorted(actions, key=lambda a: (-len(a['near_ready_order_ids']),
                  -a['potential_step_completions'], a['remaining_step_tasks'], a['wanted_id']))



def make_readiness_plan(items, found, tracker_path, limit=12, budget=80):
    import csv
    raw=Path(tracker_path).read_bytes()
    rows={r['instrument_id']:r for r in csv.DictReader(raw.decode('utf-8-sig').splitlines())}
    if not 1<=limit<=50 or not 1<=budget<=300:
        raise ValueError('readiness plan limit must be 1..50 and budget 1..300')
    actions=rank_actions([opportunity(w,rows,found) for w in items])
    chosen=[a['wanted_id'] for a in actions if a['potential_step_completions']][:limit]
    return {'schema':'eo-source-plan/v1','queue_fingerprint':queue_fingerprint(items),
            'tracker_sha256':hashlib.sha256(raw).hexdigest(),'wanted_ids':chosen,
            'max_requests':budget,'legal_cutoff':'2026-10-14','method':'readiness proximity, step opportunity, downstream work, stable ID'}
