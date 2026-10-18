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
    if not isinstance(ids,list) or not 1<=len(ids)<=50 or len(set(ids))!=len(ids):
        raise ValueError('source plan must contain 1..50 distinct wanted IDs')
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
